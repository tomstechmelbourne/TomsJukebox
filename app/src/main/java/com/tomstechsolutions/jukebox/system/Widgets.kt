package com.tomstechsolutions.jukebox.system

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.KeyEvent
import android.view.View
import android.widget.RemoteViews
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.RoundRect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.graphics.drawscope.CanvasDrawScope
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.media3.common.Player
import androidx.media3.session.MediaButtonReceiver
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.data.Art
import com.tomstechsolutions.jukebox.data.Net
import com.tomstechsolutions.jukebox.data.Podcast
import com.tomstechsolutions.jukebox.data.Podcasts
import com.tomstechsolutions.jukebox.data.Stations
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.playback.SleepTimer
import com.tomstechsolutions.jukebox.t
import com.tomstechsolutions.jukebox.ui.BarColours
import com.tomstechsolutions.jukebox.ui.ButtonArt
import com.tomstechsolutions.jukebox.ui.MainActivity
import com.tomstechsolutions.jukebox.ui.buttonColour
import com.tomstechsolutions.jukebox.ui.darken
import com.tomstechsolutions.jukebox.ui.paintSkin
import com.tomstechsolutions.jukebox.ui.skinStyle
import com.tomstechsolutions.jukebox.ui.waves
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.io.File

/** Viên Thuốc widget: the layout follows the size you stretch it to (2×1 buttons … 4×4 big cover). */
open class PillWidget : AppWidgetProvider() {
    override fun onUpdate(ctx: Context, mgr: AppWidgetManager, ids: IntArray) { Widgets.refresh(ctx) }
    override fun onAppWidgetOptionsChanged(ctx: Context, mgr: AppWidgetManager, id: Int, o: Bundle) { Widgets.refresh(ctx) }
}
class WidgetSmall : PillWidget()
class WidgetMedium : PillWidget()
class WidgetLarge : PillWidget()
class WidgetRadio : PillWidget()
class WidgetPodcast : PillWidget()
class WidgetSleep : PillWidget()
class WidgetCover : PillWidget()

/** What the widgets show; the playback service fills it in. */
data class WState(
    val title: String = "", val artist: String = "", val playing: Boolean = false, val art: ByteArray? = null,
    val pos: Long = 0, val dur: Long = 0, val next: List<String> = emptyList(), val uri: String = "",
    val shuffle: Boolean = false, val repeat: Int = Player.REPEAT_MODE_OFF, val kind: String = "",
)

object Widgets {
    @Volatile var state = WState()
    private val io = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var artBmp: Bitmap? = null
    private var artKey = 0
    private var palette: IntArray = Art.BRAND

    fun update(ctx: Context, s: WState) {
        val old = state
        state = s
        val k = s.art?.size ?: 0
        if (k != artKey) {
            artKey = k
            artBmp = s.art?.let { try { BitmapFactory.decodeByteArray(it, 0, it.size, BitmapFactory.Options().apply { inSampleSize = 2 }) } catch (_: Exception) { null } }
            palette = if (artBmp != null) Art.palette(artBmp) else Core.palette.value
        }
        if (old.copy(pos = 0) == s.copy(pos = 0) && kotlin.math.abs(old.pos - s.pos) < 15_000) return
        refresh(ctx)
    }

    fun refresh(ctx: Context) {
        val mgr = AppWidgetManager.getInstance(ctx)
        fun ids(c: Class<*>) = try { mgr.getAppWidgetIds(ComponentName(ctx, c)) } catch (_: Exception) { IntArray(0) }
        for (c in listOf(WidgetSmall::class.java, WidgetMedium::class.java, WidgetLarge::class.java)) for (id in ids(c)) safe { pill(ctx, mgr, id) }
        for (id in ids(WidgetRadio::class.java)) safe { radio(ctx, mgr, id) }
        for (id in ids(WidgetPodcast::class.java)) safe { podcast(ctx, mgr, id) }
        for (id in ids(WidgetSleep::class.java)) safe { sleep(ctx, mgr, id) }
        for (id in ids(WidgetCover::class.java)) safe { cover(ctx, mgr, id) }
    }

    private inline fun safe(f: () -> Unit) { try { f() } catch (_: Exception) { } }

    // ---------- helpers ----------
    private fun size(mgr: AppWidgetManager, id: Int): Pair<Int, Int> {
        val o = mgr.getAppWidgetOptions(id)
        val w = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, 250).coerceAtLeast(40)
        val h = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, 110).coerceAtLeast(40)
        return w to h
    }

    private fun cornerDp(ctx: Context): Float = if (Build.VERSION.SDK_INT >= 31)
        try { ctx.resources.getDimension(android.R.dimen.system_app_widget_background_radius) / ctx.resources.displayMetrics.density } catch (_: Exception) { 24f } else 24f

    /** The widget's background: the chosen skin, the cover colours, see-through, frosted or the wallpaper colours. */
    private fun background(ctx: Context, wDp: Int, hDp: Int, pill: Boolean): Bitmap {
        val d = ctx.resources.displayMetrics.density
        var w = wDp * d; var h = hDp * d
        val sc = minOf(1f, 720f / maxOf(w, h)); w *= sc; h *= sc
        val img = ImageBitmap(w.toInt().coerceAtLeast(8), h.toInt().coerceAtLeast(8))
        val r = cornerDp(ctx) * d * sc
        val cols = palette.map { Color(it) }
        CanvasDrawScope().draw(Density(d * sc), LayoutDirection.Ltr, Canvas(img), Size(img.width.toFloat(), img.height.toFloat())) {
            val path = Path().apply { addRoundRect(RoundRect(0f, 0f, size.width, size.height, CornerRadius(r))) }
            clipPath(path) {
                when (Prefs.widgetBg.value) {
                    "skin" -> if (pill) { paintSkin(0f, 0f); if (skinStyle().waves) waves(3f, FloatArray(24) { 0.3f + 0.4f * kotlin.math.abs(kotlin.math.sin(it * 0.8f)) }, cols, 0.35f, 0.6f) }
                              else drawRect(Brush.linearGradient(listOf(cols[0].darken(0.45f), cols.getOrElse(1) { cols[0] }.darken(0.25f)), Offset.Zero, Offset(size.width, size.height)))
                    "cover" -> drawRect(Brush.linearGradient(listOf(cols[0].darken(0.5f), cols.getOrElse(1) { cols[0] }.darken(0.3f)), Offset.Zero, Offset(size.width, size.height)))
                    "clear" -> drawRect(Color.Black.copy(alpha = 0.18f))
                    "frost" -> { drawRect(Color.White.copy(alpha = 0.18f)); drawRect(Brush.verticalGradient(listOf(Color.White.copy(alpha = 0.18f), Color.Transparent))) }
                    else -> { val (a, b) = you(ctx); drawRect(Brush.verticalGradient(listOf(a, b))) }
                }
            }
        }
        return img.asAndroidBitmap()
    }

    private fun you(ctx: Context): Pair<Color, Color> = if (Build.VERSION.SDK_INT >= 31)
        Color(ctx.getColor(android.R.color.system_accent1_700)) to Color(ctx.getColor(android.R.color.system_accent1_900))
    else Color(0xFF1E4A63) to Color(0xFF0D2C40)

    private fun usesSkinText() = Prefs.widgetBg.value == "skin"
    private fun textCol() = if (usesSkinText()) skinStyle().text.toArgb() else android.graphics.Color.WHITE
    private fun subCol() = if (usesSkinText()) skinStyle().sub.toArgb() else 0xFFE8DCD0.toInt()
    private fun btnCol() = buttonColour(if (usesSkinText()) skinStyle().btn else Color.White).toArgb()

    private fun bar(ctx: Context, wDp: Int, frac: Float): Bitmap {
        val d = ctx.resources.displayMetrics.density
        val w = (wDp * d).toInt().coerceIn(40, 900); val h = (10 * d).toInt()
        val img = ImageBitmap(w, h)
        val cols = BarColours.colours(Prefs.barColour.value, palette)
        CanvasDrawScope().draw(Density(d), LayoutDirection.Ltr, Canvas(img), Size(w.toFloat(), h.toFloat())) {
            val th = h * 0.45f; val y = h / 2f
            drawRoundRect(Color(0x66000000), Offset(0f, y - th / 2), Size(size.width, th), CornerRadius(th))
            val fill = if (cols.size > 1) Brush.horizontalGradient(cols) else Brush.horizontalGradient(listOf(cols[0], cols[0]))
            if (frac > 0f) drawRoundRect(fill, Offset(0f, y - th / 2), Size(size.width * frac, th), CornerRadius(th / 2))
            drawCircle(Color.White, h * 0.42f, Offset((size.width * frac).coerceIn(h * 0.42f, size.width - h * 0.42f), y))
        }
        return img.asAndroidBitmap()
    }

    fun mediaButton(ctx: Context, code: Int): PendingIntent {
        val i = Intent(Intent.ACTION_MEDIA_BUTTON).setClass(ctx, MediaButtonReceiver::class.java)
            .setData(Uri.parse("tomsjukebox://key/$code")).putExtra(Intent.EXTRA_KEY_EVENT, KeyEvent(KeyEvent.ACTION_DOWN, code))
        return PendingIntent.getBroadcast(ctx, code, i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    fun action(ctx: Context, what: String): PendingIntent {
        val i = Intent(ctx, WidgetActions::class.java).setAction("tj.$what").setData(Uri.parse("tomsjukebox://w/" + Uri.encode(what)))
        return PendingIntent.getBroadcast(ctx, what.hashCode(), i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    private fun openApp(ctx: Context, extra: (Intent) -> Unit = {}): PendingIntent {
        val i = Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP).putExtra("open_now", true).also(extra)
        return PendingIntent.getActivity(ctx, 7 + i.extras.hashCode(), i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    private fun setBtn(v: RemoteViews, id: Int, kind: Int, px: Int, pi: PendingIntent) {
        try { v.setImageViewBitmap(id, ButtonArt.bitmap(kind, Prefs.btnStyle.value, px, btnCol())) } catch (_: Exception) { }
        v.setOnClickPendingIntent(id, pi)
    }

    private fun glyph(ctx: Context, v: RemoteViews, id: Int, res: Int, on: Boolean, pi: PendingIntent) {
        v.setImageViewResource(id, res)
        v.setInt(id, "setColorFilter", if (on) 0xFFFBB040.toInt() else textCol())
        v.setInt(id, "setImageAlpha", if (on) 255 else 170)
        v.setOnClickPendingIntent(id, pi)
    }

    // ---------- Viên Thuốc ----------
    private fun pill(ctx: Context, mgr: AppWidgetManager, id: Int) {
        val (w, h) = size(mgr, id)
        val layout = when { h < 100 && w < 180 -> R.layout.widget_pill_tiny; h < 100 -> R.layout.widget_pill_wide; h < 230 -> R.layout.widget_pill_mid; else -> R.layout.widget_pill_big }
        val s = state
        val v = RemoteViews(ctx.packageName, layout)
        v.setImageViewBitmap(R.id.w_bg, background(ctx, w, h, true))
        v.setInt(R.id.w_bg, "setImageAlpha", (Prefs.widgetAlpha.value * 255).toInt())
        v.setOnClickPendingIntent(R.id.w_root, openApp(ctx))
        val radio = s.kind == "radio"
        setBtn(v, R.id.w_play, if (s.playing) ButtonArt.PAUSE else ButtonArt.PLAY, 128, mediaButton(ctx, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
        setBtn(v, R.id.w_next, ButtonArt.NEXT, 104, if (radio) action(ctx, "nextstation") else mediaButton(ctx, KeyEvent.KEYCODE_MEDIA_NEXT))
        if (layout != R.layout.widget_pill_wide) setBtn(v, R.id.w_prev, if (radio) (if (Core.recording.value) ButtonArt.REC_STOP else ButtonArt.REC) else ButtonArt.PREV, 104,
            if (radio) action(ctx, "rec") else mediaButton(ctx, KeyEvent.KEYCODE_MEDIA_PREVIOUS))
        if (layout == R.layout.widget_pill_tiny) { mgr.updateAppWidget(id, v); return }
        v.setTextViewText(R.id.w_title, s.title.ifBlank { "Tom's Jukebox" }); v.setTextColor(R.id.w_title, textCol())
        v.setTextViewText(R.id.w_artist, s.artist); v.setTextColor(R.id.w_artist, subCol())
        val art = artBmp
        if (art != null) v.setImageViewBitmap(R.id.w_art, if (layout == R.layout.widget_pill_wide) round(art, true) else round(art, false)) else v.setImageViewResource(R.id.w_art, R.drawable.app_logo)
        if (layout == R.layout.widget_pill_wide) { mgr.updateAppWidget(id, v); return }
        v.setImageViewBitmap(R.id.w_bar, bar(ctx, w - 24, if (s.dur > 0) (s.pos.toFloat() / s.dur).coerceIn(0f, 1f) else 0f))
        glyph(ctx, v, R.id.w_fav, if (s.uri in Prefs.favSet()) R.drawable.g_star_full else R.drawable.g_star, s.uri in Prefs.favSet(), action(ctx, "fav"))
        glyph(ctx, v, R.id.w_shuffle, R.drawable.g_shuffle, s.shuffle, action(ctx, "shuffle"))
        glyph(ctx, v, R.id.w_repeat, if (s.repeat == Player.REPEAT_MODE_ONE) R.drawable.g_repeat_one else R.drawable.g_repeat, s.repeat != Player.REPEAT_MODE_OFF, action(ctx, "repeat"))
        if (layout == R.layout.widget_pill_big) {
            listOf(R.id.w_next1, R.id.w_next2, R.id.w_next3).forEachIndexed { i, tid ->
                val n = s.next.getOrNull(i); v.setTextViewText(tid, if (n != null) (if (i == 0) t("Up next: ", "Tiếp theo: ") else "· ") + n else "")
                v.setViewVisibility(tid, if (n != null) View.VISIBLE else View.GONE)
            }
        }
        mgr.updateAppWidget(id, v)
    }

    private fun round(b: Bitmap, circle: Boolean): Bitmap {
        val s = minOf(b.width, b.height)
        val out = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888)
        val c = android.graphics.Canvas(out)
        val p = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)
        p.shader = android.graphics.BitmapShader(b, android.graphics.Shader.TileMode.CLAMP, android.graphics.Shader.TileMode.CLAMP).apply {
            setLocalMatrix(android.graphics.Matrix().apply { setTranslate(-(b.width - s) / 2f, -(b.height - s) / 2f) }) }
        if (circle) c.drawCircle(s / 2f, s / 2f, s / 2f, p) else c.drawRoundRect(0f, 0f, s.toFloat(), s.toFloat(), s * 0.12f, s * 0.12f, p)
        return out
    }

    // ---------- Radio ----------
    fun radioStations() = Stations.all.filter { it.name in Prefs.radioFavs.value.split('\n') }.ifEmpty {
        Stations.all.filter { it.group == Prefs.radioState.value || it.group == "NAT" || it.group == "AUVN" }
    }.take(8)

    private fun radio(ctx: Context, mgr: AppWidgetManager, id: Int) {
        val (w, h) = size(mgr, id)
        val v = RemoteViews(ctx.packageName, R.layout.widget_radio)
        v.setImageViewBitmap(R.id.w_bg, background(ctx, w, h, false))
        v.setInt(R.id.w_bg, "setImageAlpha", (Prefs.widgetAlpha.value * 255).toInt())
        val list = radioStations()
        val playingName = if (state.kind == "radio") state.title else ""
        v.setTextViewText(R.id.w_title, if (Prefs.radioFavs.value.isBlank()) "Radio · " + t("Near Me", "Gần Tôi") else "Radio · ★ " + t("Favourites", "Yêu Thích"))
        v.setOnClickPendingIntent(R.id.w_title, openApp(ctx) { it.putExtra("open_now", false).putExtra("open_tab", "1") })
        val ids = listOf(R.id.s1, R.id.s2, R.id.s3, R.id.s4, R.id.s5, R.id.s6, R.id.s7, R.id.s8)
        ids.forEachIndexed { i, sid ->
            val st = list.getOrNull(i)
            if (st == null) { v.setViewVisibility(sid, View.INVISIBLE); return@forEachIndexed }
            v.setViewVisibility(sid, View.VISIBLE)
            val on = st.name == playingName
            v.setTextViewText(sid, (if (on) "▶ " else "") + st.name.substringBefore(" (").take(26))
            v.setTextColor(sid, if (on) 0xFFFBB040.toInt() else android.graphics.Color.WHITE)
            v.setOnClickPendingIntent(sid, action(ctx, "station:$i"))
        }
        v.setTextViewText(R.id.w_rec, if (Core.recording.value) "■ " + t("Stop", "Dừng") else "● " + t("Record", "Thâu"))
        v.setOnClickPendingIntent(R.id.w_rec, action(ctx, "rec"))
        setBtn(v, R.id.w_play, if (state.playing) ButtonArt.PAUSE else ButtonArt.PLAY, 104, mediaButton(ctx, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
        mgr.updateAppWidget(id, v)
    }

    // ---------- Podcast ----------
    private fun coverFile(ctx: Context, url: String) = File(File(ctx.cacheDir, "wcovers").apply { mkdirs() }, url.hashCode().toUInt().toString(16) + ".png")

    private fun podcast(ctx: Context, mgr: AppWidgetManager, id: Int) {
        val (w, h) = size(mgr, id)
        val v = RemoteViews(ctx.packageName, R.layout.widget_podcast)
        v.setImageViewBitmap(R.id.w_bg, background(ctx, w, h, false))
        v.setInt(R.id.w_bg, "setImageAlpha", (Prefs.widgetAlpha.value * 255).toInt())
        v.setTextViewText(R.id.w_title, "Podcast · " + t("Following", "Đang Theo Dõi"))
        v.setOnClickPendingIntent(R.id.w_title, openApp(ctx) { it.putExtra("open_now", false).putExtra("open_tab", "2") })
        val subs = Podcasts.subscribed().take(4)
        val newSet = Prefs.podNew.value.split('\n').toSet()
        val cells = listOf(Triple(R.id.p1, R.id.p1_img, R.id.p1_t) to R.id.p1_dot, Triple(R.id.p2, R.id.p2_img, R.id.p2_t) to R.id.p2_dot,
            Triple(R.id.p3, R.id.p3_img, R.id.p3_t) to R.id.p3_dot, Triple(R.id.p4, R.id.p4_img, R.id.p4_t) to R.id.p4_dot)
        var missing = false
        cells.forEachIndexed { i, (c, dot) ->
            val p = subs.getOrNull(i)
            if (p == null) { v.setViewVisibility(c.first, View.INVISIBLE); return@forEachIndexed }
            v.setViewVisibility(c.first, View.VISIBLE)
            v.setTextViewText(c.third, p.title)
            val f = coverFile(ctx, p.image)
            val bmp = if (f.exists()) BitmapFactory.decodeFile(f.path) else null
            if (bmp != null) v.setImageViewBitmap(c.second, round(bmp, false)) else { v.setImageViewResource(c.second, R.drawable.app_logo); if (p.image.isNotBlank()) missing = true }
            v.setViewVisibility(dot, if (p.feed in newSet) View.VISIBLE else View.GONE)
            v.setOnClickPendingIntent(c.first, action(ctx, "pod:${p.feed}"))
        }
        if (subs.isEmpty()) v.setTextViewText(R.id.w_title, t("Follow a podcast in the app to see it here", "Theo dõi podcast trong app để hiện ở đây"))
        mgr.updateAppWidget(id, v)
        if (missing) io.launch {
            for (p in subs) { val f = coverFile(ctx, p.image); if (!f.exists() && p.image.isNotBlank()) try {
                val c = java.net.URL(p.image).openConnection() as java.net.HttpURLConnection
                c.setRequestProperty("User-Agent", Net.UA); c.connectTimeout = 8000; c.readTimeout = 8000
                val b = c.inputStream.use { BitmapFactory.decodeStream(it) }; c.disconnect()
                if (b != null) f.outputStream().use { Bitmap.createScaledBitmap(b, 160, 160, true).compress(Bitmap.CompressFormat.PNG, 100, it) }
            } catch (_: Exception) { } }
            Handler(Looper.getMainLooper()).post { refresh(ctx) }
        }
    }

    // ---------- Hẹn Giờ ----------
    private fun sleep(ctx: Context, mgr: AppWidgetManager, id: Int) {
        val (w, h) = size(mgr, id)
        val v = RemoteViews(ctx.packageName, R.layout.widget_sleep)
        v.setImageViewBitmap(R.id.w_bg, background(ctx, w, h, false))
        v.setInt(R.id.w_bg, "setImageAlpha", (Prefs.widgetAlpha.value * 255).toInt())
        val mode = Core.sleepMode.value
        v.setTextViewText(R.id.w_status, when (mode) {
            "NONE" -> t("Sleep Timer", "Hẹn Giờ Tắt Nhạc")
            "END_TRACK" -> t("Stops at the end of this song", "Tắt khi hết bài này")
            "END_QUEUE" -> t("Stops at the end of the list", "Tắt khi hết danh sách")
            else -> t("Stops at ", "Tắt lúc ") + java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault()).format(java.util.Date(System.currentTimeMillis() + Core.sleepRemaining.longValue.coerceAtLeast(0)))
        })
        v.setTextViewText(R.id.tend, "♪ " + t("End Of Song", "Hết Bài"))
        v.setOnClickPendingIntent(R.id.t15, action(ctx, "sleep:15")); v.setOnClickPendingIntent(R.id.t30, action(ctx, "sleep:30"))
        v.setOnClickPendingIntent(R.id.t60, action(ctx, "sleep:60")); v.setOnClickPendingIntent(R.id.tend, action(ctx, "sleep:end"))
        v.setOnClickPendingIntent(R.id.toff, action(ctx, "sleep:off"))
        v.setViewVisibility(R.id.toff, if (mode == "NONE") View.GONE else View.VISIBLE)
        mgr.updateAppWidget(id, v)
    }

    // ---------- Ảnh Bìa ----------
    private fun cover(ctx: Context, mgr: AppWidgetManager, id: Int) {
        val s = state
        val v = RemoteViews(ctx.packageName, R.layout.widget_cover)
        val art = artBmp
        if (art != null) v.setImageViewBitmap(R.id.w_art, round(art, false)) else v.setImageViewResource(R.id.w_art, R.drawable.app_logo)
        v.setOnClickPendingIntent(R.id.w_art, action(ctx, "covertap"))
        try { v.setImageViewBitmap(R.id.w_play, ButtonArt.bitmap(if (s.playing) ButtonArt.PAUSE else ButtonArt.PLAY, 2, 104, android.graphics.Color.WHITE)) } catch (_: Exception) { }
        v.setOnClickPendingIntent(R.id.w_play, mediaButton(ctx, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
        val fav = s.uri in Prefs.favSet()
        v.setImageViewResource(R.id.w_fav, if (fav) R.drawable.g_star_full else R.drawable.g_star)
        v.setInt(R.id.w_fav, "setColorFilter", if (fav) 0xFFFFD54F.toInt() else android.graphics.Color.WHITE)
        v.setOnClickPendingIntent(R.id.w_fav, action(ctx, "fav"))
        mgr.updateAppWidget(id, v)
    }
}

/** Taps on widget buttons that aren't plain media keys. */
class WidgetActions : BroadcastReceiver() {
    override fun onReceive(ctx: Context, i: Intent) {
        val what = i.action?.removePrefix("tj.") ?: return
        val app = ctx.applicationContext
        val done = goAsync()
        fun finish() { try { Widgets.refresh(app) } catch (_: Exception) { }; try { done.finish() } catch (_: Exception) { } }
        when {
            what == "fav" -> { if (Widgets.state.uri.isNotBlank()) Prefs.toggleFav(Widgets.state.uri); finish() }
            what == "covertap" -> {          // one tap = play / pause, two quick taps = ★
                val now = System.currentTimeMillis()
                if (now - lastCoverTap < 450) { main.removeCallbacks(coverToggle); lastCoverTap = 0; if (Widgets.state.uri.isNotBlank()) Prefs.toggleFav(Widgets.state.uri); finish() }
                else { lastCoverTap = now; coverToggle = Runnable { Core.whenReady(app) { Core.toggle() } }; main.postDelayed(coverToggle, 460); finish() }
            }
            what.startsWith("sleep:") -> {
                val sl = Core.service?.sleep
                when (val v = what.removePrefix("sleep:")) {
                    "off" -> sl?.cancel(); "end" -> sl?.start(SleepTimer.Mode.END_TRACK)
                    else -> v.toIntOrNull()?.let { sl?.start(SleepTimer.Mode.MINUTES, it) }
                }
                finish()
            }
            else -> Core.whenReady(app) {
                when {
                    what == "shuffle" -> Core.toggleShuffle()
                    what == "repeat" -> Core.cycleRepeat()
                    what == "nextstation" -> Core.nextStation()
                    what == "rec" -> if (Core.recording.value) Core.stopRecording() else Core.startRecording()
                    what.startsWith("station:") -> Widgets.radioStations().getOrNull(what.removePrefix("station:").toIntOrNull() ?: -1)?.let { Core.radioList = Widgets.radioStations(); Core.playStation(it) }
                    what.startsWith("pod:") -> {
                        val feed = what.removePrefix("pod:")
                        Prefs.podNew.value = Prefs.podNew.value.split('\n').filter { it != feed && it.isNotBlank() }.joinToString("\n")
                        Core.scope.launch {
                            val p = Podcasts.subscribed().firstOrNull { it.feed == feed } ?: Podcast("", "", feed, "")
                            val e = try { Podcasts.episodes(p).firstOrNull() } catch (_: Exception) { null }
                            if (e != null) Core.playEpisode(e)
                        }
                    }
                }
                finish()
            }
        }
    }

    companion object {
        private val main = Handler(Looper.getMainLooper())
        private var lastCoverTap = 0L
        private var coverToggle = Runnable { }
    }
}
