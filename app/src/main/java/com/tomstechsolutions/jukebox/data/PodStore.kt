package com.tomstechsolutions.jukebox.data

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.t
import com.tomstechsolutions.jukebox.ui.MainActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

/** Podcast settings per channel, downloads, "new episode" alerts and resume positions. */
object PodStore {
    // ---- channel lists: one "feed\ttitle\timage" per line ----
    private fun lines(s: String) = s.split('\n').filter { it.isNotBlank() }
    private fun line(p: Podcast) = listOf(p.feed, p.title, p.image).joinToString("\t") { it.replace('\t', ' ').replace('\n', ' ') }
    private fun has(s: String, p: Podcast) = lines(s).any { it.substringBefore('\t') == p.feed || (p.feed.isBlank() && it.split('\t').getOrNull(1) == p.title) }
    private fun toggle(s: String, p: Podcast): String = if (has(s, p)) lines(s).filter { it.substringBefore('\t') != p.feed }.joinToString("\n") else (lines(s) + line(p)).joinToString("\n")
    fun parse(s: String) = lines(s).map { val a = it.split('\t'); Podcast(a.getOrElse(1) { "" }, "", a[0], a.getOrElse(2) { "" }) }

    fun notifyOn(p: Podcast) = has(Prefs.podNotify.value, p)
    fun toggleNotify(ctx: Context, p: Podcast) { Prefs.podNotify.value = toggle(Prefs.podNotify.value, p); schedule(ctx) }
    fun autoDlOn(p: Podcast) = has(Prefs.podAutoDl.value, p)
    fun toggleAutoDl(ctx: Context, p: Podcast) { Prefs.podAutoDl.value = toggle(Prefs.podAutoDl.value, p); schedule(ctx) }
    fun hidden(p: Podcast) = lines(Prefs.podHidden.value).any { it.substringBefore('\t') == p.feed && p.feed.isNotBlank() || it.split('\t').getOrNull(1) == p.title }
    fun hide(p: Podcast) { if (!hidden(p)) Prefs.podHidden.value = (lines(Prefs.podHidden.value) + line(p)).joinToString("\n") }
    fun unhide(title: String) { Prefs.podHidden.value = lines(Prefs.podHidden.value).filter { it.split('\t').getOrNull(1) != title }.joinToString("\n") }
    fun hiddenList() = parse(Prefs.podHidden.value)

    // ---- per-channel speed and intro skip (keyed by podcast name, which every episode carries) ----
    private fun map(s: String) = try { JSONObject(s) } catch (_: Exception) { JSONObject() }
    fun speed(podcast: String): Float = map(Prefs.podSpeed.value).optDouble(podcast, 1.0).toFloat()
    fun setSpeed(podcast: String, v: Float) { Prefs.podSpeed.value = map(Prefs.podSpeed.value).put(podcast, v.toDouble()).toString() }
    fun skip(podcast: String): Int = map(Prefs.podSkip.value).optInt(podcast, 0)
    fun setSkip(podcast: String, s: Int) { Prefs.podSkip.value = map(Prefs.podSkip.value).put(podcast, s).toString() }

    // ---- played / resume ----
    fun played(url: String) = url in lines(Prefs.podPlayed.value)
    fun setPlayed(url: String, on: Boolean) {
        val l = lines(Prefs.podPlayed.value).filter { it != url }
        Prefs.podPlayed.value = (if (on) l + url else l).takeLast(2000).joinToString("\n")
    }
    private val posPrefs by lazy { com.tomstechsolutions.jukebox.App.ctx.getSharedPreferences("pod_pos", Context.MODE_PRIVATE) }
    fun pos(url: String): Long = posPrefs.getLong(url, 0L)
    fun setPos(url: String, ms: Long, dur: Long) {
        if (dur > 0 && ms > dur - 30_000) { posPrefs.edit().remove(url).apply(); setPlayed(url, true) }
        else if (ms > 5_000) posPrefs.edit().putLong(url, ms).apply()
    }

    // ---- downloads ----
    fun dir(ctx: Context, podcast: String): File = File(ctx.getExternalFilesDir("Podcasts") ?: ctx.filesDir, podcast.replace(Regex("[^\\p{L}\\p{N} _.-]"), "_").take(60)).apply { mkdirs() }
    private fun fileFor(ctx: Context, e: Episode) = File(dir(ctx, e.podcast), (e.url.hashCode().toUInt().toString(16)) + "." + (e.url.substringBefore('?').substringAfterLast('.', "mp3").take(4)))
    fun localFile(ctx: Context, e: Episode): File? = fileFor(ctx, e).takeIf { it.exists() && it.length() > 10_000 }

    suspend fun download(ctx: Context, e: Episode): Boolean = withContext(Dispatchers.IO) {
        val f = fileFor(ctx, e); if (f.exists() && f.length() > 10_000) return@withContext true
        val tmp = File(f.path + ".part")
        try {
            var url = e.best()
            var c: HttpURLConnection? = null
            for (hop in 0 until 6) {
                val cc = URL(url).openConnection() as HttpURLConnection
                cc.connectTimeout = 15000; cc.readTimeout = 30000; cc.instanceFollowRedirects = true
                cc.setRequestProperty("User-Agent", Net.UA)
                val code = cc.responseCode
                val loc = cc.getHeaderField("Location")
                if (code in 300..399 && loc != null) { url = URL(URL(url), loc).toString(); cc.disconnect(); continue }
                if (code >= 400) { cc.disconnect(); return@withContext false }
                c = cc; break
            }
            val conn = c ?: return@withContext false
            conn.inputStream.use { inp -> tmp.outputStream().use { inp.copyTo(it, 64 * 1024) } }
            conn.disconnect()
            tmp.renameTo(f)
        } catch (_: Exception) { tmp.delete(); false }
    }

    /** Keep only the newest [keep] downloaded files for a channel. */
    fun trim(ctx: Context, podcast: String, keepUrls: List<String>) {
        val keepNames = keepUrls.map { it.hashCode().toUInt().toString(16) }.toSet()
        dir(ctx, podcast).listFiles()?.forEach { if (it.nameWithoutExtension !in keepNames) it.delete() }
    }

    // ---- background check every 6 hours ----
    fun schedule(ctx: Context) {
        val wm = WorkManager.getInstance(ctx)
        if (Prefs.podNotify.value.isBlank() && Prefs.podAutoDl.value.isBlank() && Prefs.podAutoSave.value.isBlank()) { wm.cancelUniqueWork("pod_check"); return }
        wm.enqueueUniquePeriodicWork("pod_check", ExistingPeriodicWorkPolicy.KEEP, PeriodicWorkRequestBuilder<PodWorker>(6, TimeUnit.HOURS).build())
    }

    fun unmetered(ctx: Context): Boolean {
        val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return cm.activeNetwork != null && !cm.isActiveNetworkMetered
    }

    fun notifyNew(ctx: Context, p: Podcast, e: Episode) {
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= 26) nm.createNotificationChannel(NotificationChannel("pod_new", t("New Podcast Episodes", "Tập Podcast Mới"), NotificationManager.IMPORTANCE_DEFAULT))
        val open = PendingIntent.getActivity(ctx, p.feed.hashCode(), Intent(ctx, MainActivity::class.java).putExtra("open_podcast", p.feed).putExtra("open_podcast_title", p.title)
            .putExtra("open_podcast_image", p.image).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val n = NotificationCompat.Builder(ctx, "pod_new").setSmallIcon(R.drawable.g_podcast).setContentTitle(p.title.ifBlank { e.podcast })
            .setContentText(t("New episode: ", "Tập mới: ") + e.title).setAutoCancel(true).setContentIntent(open).build()
        try { nm.notify(p.feed.hashCode(), n) } catch (_: SecurityException) { }
    }
}

class PodWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val ctx = applicationContext
        val seen = try { JSONObject(Prefs.podSeen.value) } catch (_: Exception) { JSONObject() }
        for (p in PodStore.parse(Prefs.podNotify.value)) {
            val eps = try { Podcasts.episodes(p) } catch (_: Exception) { continue }
            val newest = eps.firstOrNull() ?: continue
            val was = seen.optString(p.feed, "")
            if (was.isNotBlank() && was != newest.url) {
                PodStore.notifyNew(ctx, p, newest)
                Prefs.podNew.value = (Prefs.podNew.value.split('\n').filter { it.isNotBlank() && it != p.feed } + p.feed).joinToString("\n")
            }
            seen.put(p.feed, newest.url)
        }
        Prefs.podSeen.value = seen.toString()
        try { com.tomstechsolutions.jukebox.system.Widgets.refresh(ctx) } catch (_: Exception) { }
        if (PodStore.unmetered(ctx)) for (p in PodStore.parse(Prefs.podAutoDl.value)) {
            val eps = try { Podcasts.episodes(p) } catch (_: Exception) { continue }
            val keep = eps.take(Prefs.podKeep.value.coerceIn(1, 20))
            keep.forEach { PodStore.download(ctx, it) }
            if (keep.isNotEmpty()) PodStore.trim(ctx, keep.first().podcast, keep.map { it.url })
        }
        // ⏰ Hẹn Giờ Thâu: lưu tập mới của các kênh đã chọn vào Bản Thâu Âm (chỉ khi có Wi-Fi)
        if (PodStore.unmetered(ctx)) for (p in PodStore.parse(Prefs.podAutoSave.value)) {
            val newest = try { Podcasts.episodes(p).firstOrNull() } catch (_: Exception) { null } ?: continue
            if (!PodSave.alreadySaved(newest.url) && PodSave.saveWhole(ctx, newest)) PodSave.markSaved(newest.url)
        }
        return Result.success()
    }
}
