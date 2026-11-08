package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.border
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

data class SkinStyle(val bg: List<Color>, val text: Color, val sub: Color, val btn: Color, val border: Color,
                     val radius: Dp?, val gloss: Boolean = false, val waves: Boolean = true)

fun skinStyle(): SkinStyle = when (Prefs.skin.value) {
    "xp" -> when (Prefs.xpColour.value) {
        "silver" -> SkinStyle(listOf(Color(0xFFF6F6FA), Color(0xFFDADBE5), Color(0xFFB4B6C6)), Color(0xFF1E2333), Color(0xFF4A5068), Color(0xFF2B3550), Color(0xFF8D90A6), 18.dp, true)
        "olive" -> SkinStyle(listOf(Color(0xFFC9D8A0), Color(0xFF93A867), Color(0xFF5B7638)), Color.White, Color(0xFFF1F6E2), Color.White, Color(0xFF3F5424), 18.dp, true)
        else -> SkinStyle(listOf(Color(0xFF4A8BF0), Color(0xFF2159CC), Color(0xFF0F3C9E)), Color.White, Color(0xFFDCE8FF), Color.White, Color(0xFF0B2F7A), 18.dp, true)
    }
    "metal" -> SkinStyle(listOf(Color(0xFFA5ADB7), Color(0xFF656D78), Color(0xFF3A4048), Color(0xFF727A85)), Color.White, Color(0xFFE6EAEE), Color.White, Color(0xFF2A2F35), 14.dp)
    "wood" -> SkinStyle(listOf(Color(0xFF8B5A2B), Color(0xFF5C3A1A), Color(0xFF3E2612)), Color(0xFFFCE9C8), Color(0xFFE2C79A), Color(0xFFFCE9C8), Color(0xFF2A190B), 16.dp)
    "glass" -> SkinStyle(listOf(Color(0x33FFFFFF), Color(0x1AFFFFFF)), Color.White, Color(0xFFE6F2F7), Color.White, Color(0x66FFFFFF), null)
    "ipod" -> SkinStyle(listOf(Color(0xFFFAFAFA), Color(0xFFE1E3E7)), Color(0xFF111111), Color(0xFF555555), Color(0xFF222222), Color(0xFFB8BCC2), 22.dp, waves = false)
    else -> SkinStyle(listOf(Color(0xFF3A3330), Color(0xFF1F1B19)), Color.White, Color(0xFFE8DCD0), Color.White, Color(0x30FFFFFF), null)
}

/** The spinning cover disc. */
@Composable
fun Disc(size: Dp, clock: Float) {
    val art = Core.art.value
    val spin = remember { mutableFloatStateOf(0f) }
    val last = remember { mutableFloatStateOf(clock) }
    val dt = (clock - last.floatValue).coerceIn(0f, 0.2f); last.floatValue = clock
    if (Core.playing.value) {
        var sp = 40f
        if (Prefs.spinBeat.value) { val since = System.currentTimeMillis() - Core.beat.longValue; if (since < 250) sp += 160f * (1 - since / 250f) else sp += levelsAt(clock).take(3).average().toFloat() * 60f }
        spin.floatValue = (spin.floatValue + sp * dt) % 360f
    }
    Box(Modifier.size(size).graphicsLayer { rotationZ = spin.floatValue }.clip(CircleShape).background(Color(0xFF222222)), contentAlignment = Alignment.Center) {
        if (art != null) Image(art.asImageBitmap(), null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        else Canvas(Modifier.fillMaxSize()) {
            for (k in 1..6) drawCircle(Color(0x22FFFFFF), this.size.minDimension / 2 * k / 6.5f, style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
            drawCircle(ORANGE, this.size.minDimension * 0.18f)
        }
        Box(Modifier.size(size * 0.14f).clip(CircleShape).background(Color(0xFF1A1A1A)).border(1.dp, Color(0x8CFFFFFF), CircleShape))
    }
}

@Composable
fun TimeBar(modifier: Modifier, thick: Dp, knob: Dp) {
    val cols = BarColours.colours(Prefs.barColour.value, Core.palette.value)
    val dur = Core.duration.longValue
    val pos = Core.position.longValue
    var dragFrac by remember { mutableStateOf<Float?>(null) }
    val frac = dragFrac ?: if (dur > 0) (pos.toFloat() / dur).coerceIn(0f, 1f) else 0f
    Canvas(
        modifier.height(knob * 2 + 4.dp)
            .pointerInput(dur) { detectTapGestures { o -> if (dur > 0) Core.seekTo((o.x / size.width * dur).toLong()) } }
            .pointerInput(dur) {
                detectHorizontalDragGestures(
                    onDragStart = { o -> dragFrac = (o.x / size.width).coerceIn(0f, 1f) },
                    onDragEnd = { dragFrac?.let { if (dur > 0) Core.seekTo((it * dur).toLong()) }; dragFrac = null },
                    onDragCancel = { dragFrac = null },
                ) { ch, dx -> ch.consume(); dragFrac = ((dragFrac ?: frac) + dx / size.width).coerceIn(0f, 1f) }
            },
    ) {
        val th = thick.toPx(); val kr = knob.toPx(); val y = size.height / 2
        val left = kr; val w = size.width - 2 * kr
        drawRoundRect(Color(0xB0000000), Offset(left - 1, y - th / 2 - 1), Size(w + 2, th + 2), CornerRadius(th))
        val fill = if (cols.size > 1) Brush.horizontalGradient(cols, left, left + w) else Brush.horizontalGradient(listOf(cols[0], cols[0]))
        if (frac > 0) drawRoundRect(fill, Offset(left, y - th / 2), Size(w * frac, th), CornerRadius(th / 2))
        drawCircle(Color(0x55000000), kr + 1.5f, Offset(left + w * frac, y + 1))
        drawCircle(Color.White, kr, Offset(left + w * frac, y))
    }
}

/** Prev/next: tap = change song, hold = fast seek. */
@Composable
fun SeekBtn(id: Int, dir: Int, tint: Color, size: Dp, onTap: () -> Unit) {
    val scope = rememberCoroutineScope()
    val hp = haptic()
    Box(Modifier.clip(CircleShape).pointerInput(Unit) {
        detectTapGestures(onPress = {
            var held = false
            val job = scope.launch { delay(450); held = true; hp(); while (true) { Core.seekBy(dir * 10_000L); delay(250) } }
            tryAwaitRelease()
            job.cancel()
            if (!held) { hp(); onTap() }
        })
    }.padding(8.dp)) { G(id, tint, size) }
}

/** The Tom's Dock pill: two rows when big (Now Playing / lock screen), one row at the bottom of the app. */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun Pill(modifier: Modifier = Modifier, big: Boolean, onOpen: () -> Unit = {}, onLong: () -> Unit = {}) {
    val clock by rememberClock()
    val st = skinStyle()
    val slim = Prefs.skin.value == "slim"
    val h = when { big && slim -> 104.dp; big -> 150.dp; slim -> 56.dp; else -> 72.dp }
    val shape = RoundedCornerShape(st.radius ?: (h / 2))
    var dragX by remember { mutableFloatStateOf(0f) }
    val edgeHere = Prefs.edgeOn.value && Prefs.edgeWhere.value != "window"
    Box(modifier.fillMaxWidth().height(h)) {
        Box(
            Modifier.fillMaxSize().clip(shape)
                .drawBehind {
                    drawRect(Brush.verticalGradient(st.bg))
                    if (st.gloss) drawRoundRect(Brush.verticalGradient(listOf(Color(0x66FFFFFF), Color(0x10FFFFFF)), 0f, size.height / 2),
                        Offset(6f, 3f), Size(size.width - 12f, size.height / 2 - 3f), CornerRadius(size.height / 3))
                    if (Prefs.skin.value == "metal") for (yy in 0 until size.height.toInt() step 3) drawLine(Color(0x0FFFFFFF), Offset(0f, yy.toFloat()), Offset(size.width, yy.toFloat()))
                    if (st.waves && !Anim.lowPower.value) waves(clock, levelsAt(clock), Core.palette.value.map { Color(it) }, 0.42f)
                }
                .border(1.dp, st.border, shape)
                .pointerInput(Unit) {
                    detectHorizontalDragGestures(onDragEnd = {
                        if (Prefs.swipePill.value) { if (dragX < -80) Core.next() else if (dragX > 80) Core.prev() }
                        dragX = 0f
                    }) { _, dx -> dragX += dx }
                }
                .combinedClickable(onClick = onOpen, onLongClick = onLong),
        ) {
            val title = Core.title.value.ifBlank { "Tom's Jukebox" }
            val sub = listOf(Core.artist.value, Core.album.value).filter { it.isNotBlank() }.joinToString(" · ")
            val playId = if (Core.playing.value) Gl.pause else Gl.play
            if (big) {
                Row(Modifier.fillMaxSize().padding(if (slim) 8.dp else 11.dp), verticalAlignment = Alignment.CenterVertically) {
                    Disc(h - if (slim) 16.dp else 22.dp, clock)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(title, color = st.text, fontSize = 17.sp, fontWeight = FontWeight.Bold, maxLines = 1, modifier = Modifier.weight(1f).basicMarquee())
                            SleepBadge(st.text)
                        }
                        Text(listOf(sub, Core.format.value).filter { it.isNotBlank() }.joinToString("  ·  "), color = st.sub, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        if (!slim) Row(Modifier.fillMaxWidth(), horizontalArrangement = androidx.compose.foundation.layout.Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                            SeekBtn(Gl.prev, -1, st.btn, 26.dp) { Core.prev() }
                            Spacer(Modifier.width(12.dp))
                            IconBtn(playId, st.btn, 36.dp, pad = 4.dp) { Core.toggle() }
                            Spacer(Modifier.width(12.dp))
                            SeekBtn(Gl.next, 1, st.btn, 26.dp) { Core.next() }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(fmtTime(Core.position.longValue), color = st.sub, fontSize = 11.sp)
                            TimeBar(Modifier.weight(1f).padding(horizontal = 4.dp), 6.dp, 8.dp)
                            Text(if (Core.kind.value == "radio") "LIVE" else fmtTime(Core.duration.longValue), color = st.sub, fontSize = 11.sp)
                            if (slim) { IconBtn(playId, st.btn, 26.dp, pad = 4.dp) { Core.toggle() } }
                        }
                    }
                }
            } else {
                Row(Modifier.fillMaxSize().padding(if (slim) 5.dp else 7.dp), verticalAlignment = Alignment.CenterVertically) {
                    Disc(h - if (slim) 10.dp else 14.dp, clock)
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text(title, color = st.text, fontSize = 14.sp, fontWeight = FontWeight.Bold, maxLines = 1, modifier = Modifier.basicMarquee())
                        if (!slim) Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(sub, color = st.sub, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f, fill = false))
                            SleepBadge(st.sub)
                        }
                        TimeBar(Modifier.fillMaxWidth(), 4.dp, 5.dp)
                    }
                    IconBtn(playId, st.btn, if (slim) 26.dp else 30.dp, pad = 6.dp) { Core.toggle() }
                    SeekBtn(Gl.next, 1, st.btn, 24.dp) { Core.next() }
                }
            }
        }
        if (edgeHere) EdgeLight(Modifier.fillMaxSize(), st.radius ?: (h / 2))
    }
}

@Composable
fun SleepBadge(c: Color) {
    val rem = Core.sleepRemaining.longValue
    if (rem >= 0 && Core.sleepMode.value != "NONE") Text("  ⏾ " + fmtTime(rem), color = c, fontSize = 11.sp, fontWeight = FontWeight.Bold)
    else if (Core.sleepMode.value == "END_TRACK" || Core.sleepMode.value == "END_QUEUE") Text("  ⏾", color = c, fontSize = 11.sp)
    if (Core.recording.value) Text("  ● REC", color = Color(0xFFFF5252), fontSize = 11.sp, fontWeight = FontWeight.Bold)
}

