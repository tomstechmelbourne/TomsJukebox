package com.tomstechsolutions.jukebox.ui

import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioManager
import android.os.Build
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.media3.common.Player
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.sin

/** "This phone" – or the Bluetooth / USB device the sound is going to. */
fun outputName(ctx: Context): String {
    val am = ctx.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    if (Build.VERSION.SDK_INT >= 23) {
        val outs = am.getDevices(AudioManager.GET_DEVICES_OUTPUTS)
        val pref = listOf(AudioDeviceInfo.TYPE_BLUETOOTH_A2DP, AudioDeviceInfo.TYPE_USB_HEADSET, AudioDeviceInfo.TYPE_WIRED_HEADPHONES, AudioDeviceInfo.TYPE_WIRED_HEADSET)
        for (ty in pref) outs.firstOrNull { it.type == ty }?.let { d -> val n = d.productName?.toString()?.trim().orEmpty(); return n.ifBlank { t("Headphones", "Tai nghe") } }
    }
    return t("This phone", "Điện thoại này")
}

/**
 * Thanh thời gian có sóng nhạc nhiều màu nằm trên phần đã nghe, nút kéo tròn phát sáng theo màu ảnh bìa.
 * Chạm hoặc kéo để tua.
 */
@Composable
fun WaveSeekBar(modifier: Modifier = Modifier, height: Dp = 44.dp) {
    val clock by rememberClock()
    val dur = Core.duration.longValue
    var dragFrac by remember { mutableStateOf<Float?>(null) }
    val frac = dragFrac ?: if (dur > 0) (Core.position.longValue.toFloat() / dur).coerceIn(0f, 1f) else 0f
    val glow = Color(Core.palette.value[0]).let { if (it.lum() < 0.12f) Color(0xFFFF3B3B) else it }
    Canvas(modifier.fillMaxWidth().height(height)
        .pointerInput(dur) { detectTapGestures { o -> if (dur > 0) Core.seekTo((o.x / size.width * dur).toLong()) } }
        .pointerInput(dur) {
            detectHorizontalDragGestures(onDragStart = { o -> dragFrac = (o.x / size.width).coerceIn(0f, 1f) },
                onDragEnd = { dragFrac?.let { if (dur > 0) Core.seekTo((it * dur).toLong()) }; dragFrac = null }, onDragCancel = { dragFrac = null }
            ) { ch, dx -> ch.consume(); dragFrac = ((dragFrac ?: frac) + dx / size.width).coerceIn(0f, 1f) }
        }) {
        val kr = 9.dp.toPx(); val left = kr; val w = size.width - 2 * kr
        val y = size.height - kr - 2.dp.toPx(); val th = 4.dp.toPx(); val x = left + w * frac
        // waves over the played part
        val lv = levelsAt(clock)
        val live = Core.playing.value && !Anim.lowPower.value
        val layers = listOf(Color(0xFFFF3B5C), Color(0xFFE040FB), Color(0xFF7C4DFF), Color(0xFF448AFF))
        if (x - left > 4f) layers.forEachIndexed { li, c ->
            val p = Path().apply { moveTo(left, y) }
            val steps = 40
            for (k in 0..steps) {
                val fx = k / steps.toFloat(); val px = left + (x - left) * fx
                var a = 0f
                for (b in 0 until 3) { val centre = ((b * 0.33f + li * 0.13f + if (live) clock * (0.04f + li * 0.01f) else 0f) % 1f); val lvl = lv[(b * 5 + li * 3) % lv.size]
                    a += lvl * exp(-((fx - centre) / 0.12f).let { it * it }) }
                val taper = sin(fx * Math.PI.toFloat()).coerceAtLeast(0f)
                p.lineTo(px, y - th / 2 - (size.height - 2 * kr - 6f) * (a * 0.75f).coerceAtMost(1f) * taper * if (live) 1f else 0.35f)
            }
            p.lineTo(x, y); p.close()
            drawPath(p, c.copy(alpha = 0.55f))
        }
        drawRoundRect(Color(0x66FFFFFF), Offset(x, y - th / 2), Size((left + w - x).coerceAtLeast(0f), th), CornerRadius(th / 2))
        drawRoundRect(Brush.horizontalGradient(listOf(Color.White.copy(alpha = 0.6f), Color.White), left, x), Offset(left, y - th / 2), Size(x - left, th), CornerRadius(th / 2))
        drawCircle(Brush.radialGradient(listOf(glow.copy(alpha = 0.7f), Color.Transparent), Offset(x, y), kr * 2.6f), kr * 2.6f, Offset(x, y))
        drawCircle(Color.White, kr, Offset(x, y))
        drawCircle(glow, kr * 0.72f, Offset(x, y))
    }
}

@Composable
private fun GlassBtn(kind: Int, size: Dp, onClick: () -> Unit, seekDir: Int = 0) {
    Box(Modifier.size(size).clip(CircleShape).background(Color(0x33FFFFFF)), contentAlignment = Alignment.Center) {
        CtlBtn(kind, size * 0.5f, Color.White, seekDir) { onClick() }
    }
}

/** Hàng nút: Xáo Trộn (hoặc Lặp Lại) · ⏮ ▶ ⏭ trong vòng kính mờ · ⊕ (Yêu Thích) hoặc ● Thâu khi nghe radio / podcast. */
@Composable
private fun CardButtons(leftRepeat: Boolean, big: Dp) {
    val radio = Core.kind.value == "radio"; val rec = radio || Core.kind.value == "podcast"
    val fav = Core.uri.value.isNotBlank() && Core.uri.value in Prefs.favSet()
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
        if (leftRepeat) IconBtn(if (Core.repeat.value == Player.REPEAT_MODE_ONE) Gl.repeatOne else Gl.repeat, if (Core.repeat.value != Player.REPEAT_MODE_OFF) ORANGE else Color.White, 24.dp) { Core.cycleRepeat() }
        else IconBtn(Gl.shuffle, if (Core.shuffle.value) ORANGE else Color.White, 24.dp) { Core.toggleShuffle() }
        GlassBtn(ButtonArt.PREV, big * 0.85f, { Core.prev() }, -1)
        GlassBtn(if (Core.playing.value) ButtonArt.PAUSE else ButtonArt.PLAY, big, { Core.toggle() })
        GlassBtn(ButtonArt.NEXT, big * 0.85f, { if (radio) Core.nextStation() else Core.next() }, if (radio) 0 else 1)
        if (rec) CtlBtn(if (Core.recording.value) ButtonArt.REC_STOP else ButtonArt.REC, 26.dp, Color.White) { if (Core.recording.value) Core.stopRecording() else Core.startRecording() }
        else Box(Modifier.size(34.dp).clip(CircleShape).border(2.dp, if (fav) ORANGE else Color.White, CircleShape).clickable { if (Core.uri.value.isNotBlank()) Prefs.toggleFav(Core.uri.value) }, contentAlignment = Alignment.Center) {
            Text(if (fav) "✓" else "+", color = if (fav) ORANGE else Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        }
    }
}


@Composable
private fun TimesRow() {
    Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp)) {
        Text(fmtTime(Core.position.longValue), color = Color(0xFFBDBDBD), fontSize = 13.sp, modifier = Modifier.weight(1f))
        Text(if (Core.kind.value == "radio") "LIVE" else fmtTime(Core.duration.longValue), color = Color(0xFFBDBDBD), fontSize = 13.sp)
    }
}

@Composable
private fun CoverBackground(blurIt: Boolean) {
    val art = Core.art.value
    if (art != null) Image(art.asImageBitmap(), null, Modifier.fillMaxSize().then(if (blurIt && Build.VERSION.SDK_INT >= 31) Modifier.blur(6.dp) else Modifier), contentScale = ContentScale.Crop)
    else Box(Modifier.fillMaxSize().background(Brush.linearGradient(Core.palette.value.map { Color(it).darken(0.5f) })))
    Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0x99000000), Color(0x77000000), Color(0xCC000000)))))
}

/**
 * Thẻ Ảnh Bìa (trong app): thẻ bo góc lớn, ảnh bìa làm nền tối, "Điện thoại này" + nút chọn loa, tên bài ở giữa,
 * sóng nhạc trên thanh thời gian, hàng nút trong vòng kính mờ. Vuốt lên để mở Đang Phát (thẻ dưới).
 */
@Composable
fun CardPlayer(modifier: Modifier = Modifier, compact: Boolean, onOpen: () -> Unit = {}, onLong: () -> Unit = {}) {
    val ctx = LocalContext.current
    var dragY by remember { mutableFloatStateOf(0f) }
    val shape = RoundedCornerShape(if (compact) 34.dp else 40.dp)
    Box(modifier.fillMaxWidth().height(if (compact) 196.dp else 232.dp).clip(shape)
        .pointerInput(compact) {
            detectDragGestures(onDragEnd = { if (compact && dragY < -50) onOpen(); dragY = 0f }, onDragCancel = { dragY = 0f }) { ch, d -> if (abs(d.y) > abs(d.x)) { ch.consume(); dragY += d.y } }
        }
        .pointerInput(Unit) { detectTapGestures(onTap = { if (compact) onOpen() }, onLongPress = { onLong() }) }) {
        CoverBackground(blurIt = false)
        Column(Modifier.fillMaxSize().padding(horizontal = 22.dp, vertical = if (compact) 12.dp else 16.dp), verticalArrangement = Arrangement.SpaceBetween) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(outputName(ctx), color = Color(0xFFE0E0E0), fontSize = 15.sp, fontWeight = FontWeight.Medium, modifier = Modifier.weight(1f), maxLines = 1)
                IconBtn(Gl.cast, Color.White, 22.dp) { openOutputSwitcher(ctx) }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                Image(painterResource(R.drawable.app_logo), null, Modifier.size(22.dp).clip(CircleShape))
                Spacer(Modifier.width(8.dp))
                Text(Core.title.value.ifBlank { "Tom's Jukebox" }, color = Color.White, fontSize = if (compact) 18.sp else 20.sp, fontWeight = FontWeight.SemiBold,
                    maxLines = 1, modifier = Modifier.weight(1f, fill = false).basicMarquee())
            }
            Column {
                WaveSeekBar(height = if (compact) 34.dp else 44.dp)
                TimesRow()
            }
            CardButtons(leftRepeat = false, big = if (compact) 46.dp else 56.dp)
        }
    }
}

/**
 * Màn hình khoá (hình 1): ảnh bìa lớn bo góc với tên bài ở dưới ảnh, rồi "Điện thoại này",
 * sóng nhạc trên thanh thời gian, giờ hai đầu và hàng nút.
 */
@Composable
fun LockCard(modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    Column(modifier.fillMaxWidth().clip(RoundedCornerShape(30.dp)).background(Color(0x55000000)).padding(10.dp)) {
        Box(Modifier.fillMaxWidth().aspectRatio(1.25f).clip(RoundedCornerShape(24.dp))) {
            val art = Core.art.value
            if (art != null) Image(art.asImageBitmap(), null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            else Box(Modifier.fillMaxSize().background(Brush.linearGradient(Core.palette.value.map { Color(it) })), contentAlignment = Alignment.Center) {
                Image(painterResource(R.drawable.app_logo), null, Modifier.size(96.dp)) }
            Box(Modifier.fillMaxWidth().height(80.dp).align(Alignment.BottomCenter).background(Brush.verticalGradient(listOf(Color.Transparent, Color(0xCC000000)))))
            Column(Modifier.align(Alignment.BottomStart).padding(horizontal = 14.dp, vertical = 10.dp)) {
                Text(Core.title.value.ifBlank { "Tom's Jukebox" }, color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold, maxLines = 1, modifier = Modifier.basicMarquee())
                if (Core.artist.value.isNotBlank()) Text(Core.artist.value, color = Color(0xFFE0E0E0), fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        }
        Row(Modifier.padding(start = 8.dp, top = 10.dp, end = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(outputName(ctx), color = Color(0xFFE0E0E0), fontSize = 14.sp, modifier = Modifier.weight(1f), textAlign = TextAlign.Start, maxLines = 1)
            IconBtn(Gl.cast, Color.White, 20.dp) { openOutputSwitcher(ctx) }
        }
        WaveSeekBar(Modifier.padding(horizontal = 4.dp), 40.dp)
        Box(Modifier.padding(horizontal = 6.dp)) { TimesRow() }
        Spacer(Modifier.height(4.dp))
        CardButtons(leftRepeat = true, big = 50.dp)
    }
}
