package com.tomstechsolutions.jukebox.data

import android.content.ContentValues
import android.content.Context
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Thâu podcast vào Bản Thâu Âm (Music/Tom's Jukebox/Recordings/Podcast):
 * cả tập (bản gốc, chất lượng cao nhất kênh có) hoặc một đoạn A–B cắt thẳng từ file gốc, không nén lại.
 */
object PodSave {
    private fun clean(s: String) = s.replace(Regex("[\\\\/:*?\"<>|\\n\\r\\t]"), "_").trim().take(80)
    private fun stamp() = SimpleDateFormat("yyyy-MM-dd HH.mm", Locale.US).format(Date())
    private fun mimeOf(ext: String) = when (ext) { "mp3" -> "audio/mpeg"; "m4a", "mp4" -> "audio/mp4"; "aac" -> "audio/aac"; "ogg", "opus" -> "audio/ogg"; else -> "audio/$ext" }

    /** Copies [src] into the Recordings/Podcast folder under [name]. */
    private fun publish(ctx: Context, src: InputStream, name: String): Boolean {
        val ext = name.substringAfterLast('.', "mp3").lowercase()
        return if (Build.VERSION.SDK_INT >= 29) {
            val cv = ContentValues().apply {
                put(MediaStore.Audio.Media.DISPLAY_NAME, name)
                put(MediaStore.Audio.Media.MIME_TYPE, mimeOf(ext))
                put(MediaStore.Audio.Media.RELATIVE_PATH, Environment.DIRECTORY_MUSIC + "/Tom's Jukebox/Recordings/Podcast")
                put(MediaStore.Audio.Media.IS_PENDING, 1)
            }
            val uri = ctx.contentResolver.insert(MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY), cv) ?: return false
            try {
                ctx.contentResolver.openOutputStream(uri)?.use { o -> src.copyTo(o, 64 * 1024) } ?: return false
                ctx.contentResolver.update(uri, ContentValues().apply { put(MediaStore.Audio.Media.IS_PENDING, 0) }, null, null)
                true
            } catch (e: Exception) { try { ctx.contentResolver.delete(uri, null, null) } catch (_: Exception) { }; false }
        } else {
            @Suppress("DEPRECATION")
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC), "Tom's Jukebox/Recordings/Podcast").apply { mkdirs() }
            val f = File(dir, name)
            try { f.outputStream().use { src.copyTo(it, 64 * 1024) }; android.media.MediaScannerConnection.scanFile(ctx, arrayOf(f.path), null, null); true } catch (_: Exception) { false }
        }
    }

    private fun open(url: String): Pair<InputStream, HttpURLConnection> {
        var u = url
        repeat(6) {
            val c = URL(u).openConnection() as HttpURLConnection
            c.connectTimeout = 15000; c.readTimeout = 30000; c.instanceFollowRedirects = true
            c.setRequestProperty("User-Agent", Net.UA)
            val code = c.responseCode; val loc = c.getHeaderField("Location")
            if (code in 300..399 && loc != null) { u = URL(URL(u), loc).toString(); c.disconnect(); return@repeat }
            if (code >= 400) { c.disconnect(); throw java.io.IOException("HTTP $code") }
            return c.inputStream to c
        }
        throw java.io.IOException("too many redirects")
    }

    private fun extOf(url: String) = url.substringBefore('?').substringAfterLast('.', "mp3").lowercase().takeIf { it.length in 2..4 && it.all { c -> c.isLetterOrDigit() } } ?: "mp3"

    /** ⬇ Lưu Cả Tập: the episode's original file (highest quality the channel offers). */
    suspend fun saveWhole(ctx: Context, e: Episode): Boolean = withContext(Dispatchers.IO) {
        val local = PodStore.localFile(ctx, e)
        val url = e.best()
        val name = "${clean(e.podcast)} - ${clean(e.title)} (${e.date.ifBlank { stamp() }.replace(",", "")}).${local?.extension ?: extOf(url)}"
        val ok = try {
            if (local != null) local.inputStream().use { publish(ctx, it, name) }
            else { val (inp, c) = open(url); try { inp.use { publish(ctx, it, name) } } finally { c.disconnect() } }
        } catch (_: Exception) { false }
        Messages.add(if (ok) t("Saved to Recordings › Podcast: $name", "Đã lưu vào Bản Thâu Âm › Podcast: $name") else t("Couldn't save: ", "Không lưu được: ") + e.title)
        ok
    }

    /** ✂ Cắt đoạn A–B (and ● Thâu while listening): copies the compressed audio between [aMs] and [bMs] without re-encoding. */
    suspend fun saveClip(ctx: Context, src: String, title: String, podcast: String, aMs: Long, bMs: Long): Boolean = withContext(Dispatchers.IO) {
        val a = minOf(aMs, bMs).coerceAtLeast(0); val b = maxOf(aMs, bMs)
        if (b - a < 1000) { Messages.add(t("The clip is too short.", "Đoạn cắt ngắn quá.")); return@withContext false }
        val ex = MediaExtractor()
        var tmp: File? = null
        val ok = try {
            if (src.startsWith("http")) ex.setDataSource(src, mapOf("User-Agent" to Net.UA)) else if (src.startsWith("content:") || src.startsWith("file:")) ex.setDataSource(ctx, android.net.Uri.parse(src), null) else ex.setDataSource(src)
            val track = (0 until ex.trackCount).firstOrNull { ex.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true } ?: throw java.io.IOException("no audio")
            ex.selectTrack(track)
            val fmt = ex.getTrackFormat(track); val mime = fmt.getString(MediaFormat.KEY_MIME) ?: ""
            ex.seekTo(a * 1000, MediaExtractor.SEEK_TO_PREVIOUS_SYNC)
            val buf = ByteBuffer.allocate(1 shl 20)
            val label = "${clean(podcast)} - ${clean(title)} [${fmtT(a)}–${fmtT(b)}]"
            when {
                mime == "audio/mpeg" -> {                      // MP3: frames carry their own headers, so they can simply be joined
                    tmp = File.createTempFile("clip", ".mp3", ctx.cacheDir)
                    tmp.outputStream().use { o ->
                        while (true) { val n = ex.readSampleData(buf, 0); if (n < 0 || ex.sampleTime > b * 1000) break
                            val arr = ByteArray(n); buf.get(arr, 0, n); buf.clear(); o.write(arr); ex.advance() }
                    }
                    tmp.inputStream().use { publish(ctx, it, "$label.mp3") }
                }
                mime == "audio/mp4a-latm" || (mime == "audio/opus" && Build.VERSION.SDK_INT >= 29) -> {
                    val isOpus = mime == "audio/opus"
                    tmp = File.createTempFile("clip", if (isOpus) ".ogg" else ".m4a", ctx.cacheDir)
                    val mx = MediaMuxer(tmp.path, if (isOpus) MediaMuxer.OutputFormat.MUXER_OUTPUT_OGG else MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
                    val out = mx.addTrack(fmt); mx.start()
                    val info = MediaCodec.BufferInfo(); var t0 = -1L
                    while (true) { val n = ex.readSampleData(buf, 0); val ts = ex.sampleTime; if (n < 0 || ts > b * 1000) break
                        if (t0 < 0) t0 = ts
                        info.set(0, n, ts - t0, if (ex.sampleFlags and MediaExtractor.SAMPLE_FLAG_SYNC != 0) MediaCodec.BUFFER_FLAG_KEY_FRAME else 0)
                        mx.writeSampleData(out, buf, info); buf.clear(); ex.advance() }
                    mx.stop(); mx.release()
                    tmp.inputStream().use { publish(ctx, it, label + if (isOpus) ".ogg" else ".m4a") }
                }
                else -> throw java.io.IOException(mime)
            }
        } catch (e: Exception) {
            Messages.add(t("Couldn't cut this episode (", "Không cắt được tập này (") + (e.message ?: "") + t("). Try \"Save Whole Episode\".", "). Thử \"Lưu Cả Tập\"."))
            false
        } finally { ex.release(); tmp?.delete() }
        if (ok) Messages.add(t("Clip saved to Recordings › Podcast.", "Đã lưu đoạn cắt vào Bản Thâu Âm › Podcast."))
        ok
    }

    private fun fmtT(ms: Long): String { val s = ms / 1000; return if (s >= 3600) "%d.%02d.%02d".format(s / 3600, s / 60 % 60, s % 60) else "%d.%02d".format(s / 60, s % 60) }

    // ---- ⏰ Hẹn Giờ Thâu: save each new episode of chosen channels ----
    fun autoSaveOn(p: Podcast) = Prefs.podAutoSave.value.split('\n').any { it.substringBefore('\t') == p.feed && p.feed.isNotBlank() }
    fun toggleAutoSave(ctx: Context, p: Podcast) {
        val l = Prefs.podAutoSave.value.split('\n').filter { it.isNotBlank() }
        Prefs.podAutoSave.value = (if (autoSaveOn(p)) l.filter { it.substringBefore('\t') != p.feed } else l + listOf(p.feed, p.title, p.image).joinToString("\t")).joinToString("\n")
        PodStore.schedule(ctx)
    }
    fun alreadySaved(url: String) = url in Prefs.podSavedUrls.value.split('\n')
    fun markSaved(url: String) { Prefs.podSavedUrls.value = (Prefs.podSavedUrls.value.split('\n').filter { it.isNotBlank() } + url).takeLast(500).joinToString("\n") }
}
