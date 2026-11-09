package com.tomstechsolutions.jukebox.ui

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.border
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
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
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

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

/** Colour the buttons are painted in (Trắng / Theo Ảnh Bìa / Màu Giao Diện / Tự Chọn). */
fun buttonColour(skinBtn: Color, accent: Color = ORANGE): Color = Motifs.of(Prefs.btnColour.value)?.let { Motifs.list[it].accent } ?: when (Prefs.btnColour.value) {
    "cover" -> Color(Core.palette.value[0])
    "theme" -> accent
    "custom" -> Color(Prefs.btnCustom.value)
    else -> skinBtn
}

/** One play/pause/prev/next/record button in the chosen button set. Hold prev/next to fast-seek. */
@Composable
fun CtlBtn(kind: Int, size: Dp, colour: Color, seekDir: Int = 0, onClick: () -> Unit) {
    val scope = rememberCoroutineScope()
    val hp = haptic()
    var pressed by remember { mutableStateOf(false) }
    val s = size * Prefs.btnScale.value
    val glow = if (Motifs.buttonStyle().first == 6) levelsAt(System.nanoTime() / 1e9f).take(4).average().toFloat() else 0f
    Box(Modifier.size(s + 8.dp).clip(CircleShape).pointerInput(seekDir) {
        detectTapGestures(onPress = {
            pressed = true
            var held = false
            val job = if (seekDir != 0) scope.launch { delay(450); held = true; hp(); while (true) { Core.seekBy(seekDir * 10_000L); delay(250) } } else null
            tryAwaitRelease()
            job?.cancel(); pressed = false
            if (!held) { hp(); onClick() }
        })
    }, contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(s)) {
            drawIntoCanvas { ButtonArt.draw(it.nativeCanvas, kind, Prefs.btnStyle.value, size.toPx() * Prefs.btnScale.value, colour.toArgb(), pressed, glow) }
        }
    }
}

/** Phone tilt for the Liquid Glass shimmer (-1..1). */
@Composable
fun rememberTilt(active: Boolean): Float {
    val ctx = LocalContext.current
    var tilt by remember { mutableFloatStateOf(0f) }
    DisposableEffect(active) {
        val sm = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val l = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) { tilt = tilt * 0.85f + (-e.values[0] / 9.8f).coerceIn(-1f, 1f) * 0.15f }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        if (active) sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.let { sm.registerListener(l, it, SensorManager.SENSOR_DELAY_UI) }
        onDispose { sm.unregisterListener(l) }
    }
    return tilt
}

/** Double-tap: next colour (or next wood / marble / XP variant). Returns the name to show. */
fun cycleSkinColour(): String = when (Prefs.skin.value) {
    "grain" -> { Prefs.woodType.value = (Prefs.woodType.value + 1) % 3; SkinList.woodTypes[Prefs.woodType.value].let { t(it.first, it.second) } }
    "marble" -> { Prefs.marbleType.value = (Prefs.marbleType.value + 1) % 3; SkinList.marbleTypes[Prefs.marbleType.value].let { t(it.first, it.second) } }
    "xp" -> { val l = listOf("blue", "silver", "olive"); val i = (l.indexOf(Prefs.xpColour.value) + 1) % 3; Prefs.xpColour.value = l[i]; Skins.xpColours[i].second }
    "pill", "slim" -> { Prefs.pillColour.value = (Prefs.pillColour.value + 1) % PillColours.list.size; PillColours.name(Prefs.pillColour.value) }
    else -> t("This skin has one colour – try Pill, Wood Grain or Marble", "Skin này chỉ có một màu – thử Viên Thuốc, Vân Gỗ hoặc Cẩm Thạch")
}

/** The Tom's Dock pill: two rows when big (Now Playing / lock screen), one row at the bottom of the app. */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun Pill(modifier: Modifier = Modifier, big: Boolean, onOpen: () -> Unit = {}, onLong: () -> Unit = {}, sizeKey: String? = null, gestures: Boolean = true) {
    val clock by rememberClock()
    val st = skinStyle()
    val slim = Prefs.skin.value == "slim"
    val mini = if (big) "" else (sizeKey ?: Prefs.miniSize.value)
    val h = when { big && slim -> 104.dp; big -> 150.dp; mini == "small" -> if (slim) 56.dp else 66.dp; mini == "large" -> 136.dp; else -> 106.dp }
    val radius = st.radius ?: (h / 2)
    val shape = RoundedCornerShape(radius)
    var dragX by remember { mutableFloatStateOf(0f) }
    var dragY by remember { mutableFloatStateOf(0f) }
    var toast by remember { mutableStateOf("") }
    var toastAt by remember { mutableLongStateOf(0L) }
    LaunchedEffect(toastAt) { if (toastAt > 0) { delay(1100); toast = "" } }
    val tilt = rememberTilt(Prefs.skin.value == "liquid")
    val edgeHere = Prefs.edgeOn.value && Prefs.edgeWhere.value != "window"
    val radio = Core.kind.value == "radio"
    val btnCol = buttonColour(st.btn)
    val hp = haptic()
    Box(modifier.fillMaxWidth().height(h)) {
        Box(
            Modifier.fillMaxSize().clip(shape)
                .drawBehind {
                    val alpha = Prefs.pillAlpha.value.coerceIn(0.05f, 1f)
                    drawIntoCanvas { c ->
                        c.saveLayer(Rect(Offset.Zero, size), Paint().apply { this.alpha = alpha })
                        paintSkin(clock, tilt)
                        c.restore()
                    }
                    if (st.waves && Prefs.vizOn.value && Prefs.vizPill.value && !Anim.lowPower.value)
                        waves(clock, levelsAt(clock), Core.palette.value.map { Color(it) }, Prefs.waveHeight.value, Prefs.waveStrength.value)
                    paintSkinBorder(radius.toPx(), st.border)
                }
                .then(if (!gestures) Modifier else Modifier
                .pointerInput(big) {
                    detectDragGestures(onDragEnd = {
                        if (kotlin.math.abs(dragX) > kotlin.math.abs(dragY)) { if (Prefs.swipePill.value) { if (dragX < -80) Core.next() else if (dragX > 80) Core.prev() } }
                        else if (!big && dragY < -50) onOpen()          // vuốt lên mở Đang Phát
                        dragX = 0f; dragY = 0f
                    }, onDragCancel = { dragX = 0f; dragY = 0f }) { ch, d -> ch.consume(); dragX += d.x; dragY += d.y }
                }
                .combinedClickable(onClick = onOpen, onLongClick = onLong,
                    onDoubleClick = if (Prefs.dblTapColour.value) ({ hp(); toast = cycleSkinColour(); toastAt = System.currentTimeMillis() }) else null)),
        ) {
            val title = Core.title.value.ifBlank { "Tom's Jukebox" }
            val sub = listOf(Core.artist.value, Core.album.value).filter { it.isNotBlank() }.joinToString(" · ")
            val playKind = if (Core.playing.value) ButtonArt.PAUSE else ButtonArt.PLAY
            val recKind = if (Core.recording.value) ButtonArt.REC_STOP else ButtonArt.REC
            val toggleRec = { if (Core.recording.value) Core.stopRecording() else Core.startRecording() }
            if (big) androidx.compose.foundation.layout.BoxWithConstraints(Modifier.fillMaxSize()) {
                val pad = if (slim) 8.dp else 11.dp
                val discSize = minOf(h - pad * 2, maxWidth * 0.3f)
                Row(Modifier.fillMaxSize().padding(start = pad, top = pad, bottom = pad, end = if (st.radius == null) h / 5 else 14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Disc(discSize, clock)
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(title, color = st.text, fontSize = 17.sp, fontWeight = FontWeight.Bold, maxLines = 1, textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth().basicMarquee())
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center, modifier = Modifier.fillMaxWidth()) {
                            Text(listOf(sub, Core.format.value).filter { it.isNotBlank() }.joinToString("  ·  "), color = st.sub, fontSize = 12.sp, maxLines = 1,
                                overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center, modifier = Modifier.weight(1f, fill = false))
                            SleepBadge(st.text)
                        }
                        if (!slim) Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                            if (radio) CtlBtn(recKind, 30.dp, btnCol) { toggleRec() } else CtlBtn(ButtonArt.PREV, 26.dp, btnCol, seekDir = -1) { Core.prev() }
                            Spacer(Modifier.width(6.dp))
                            CtlBtn(playKind, 36.dp, btnCol) { Core.toggle() }
                            Spacer(Modifier.width(6.dp))
                            CtlBtn(ButtonArt.NEXT, 26.dp, btnCol, seekDir = if (radio) 0 else 1) { if (radio) Core.nextStation() else Core.next() }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(fmtTime(Core.position.longValue), color = st.sub, fontSize = 11.sp)
                            TimeBar(Modifier.weight(1f).padding(horizontal = 4.dp), 6.dp, 8.dp)
                            Text(if (radio) "LIVE" else fmtTime(Core.duration.longValue), color = st.sub, fontSize = 11.sp)
                            if (slim) { if (radio) CtlBtn(recKind, 22.dp, btnCol) { toggleRec() }; CtlBtn(playKind, 24.dp, btnCol) { Core.toggle() } }
                        }
                    }
                }
            }
            else if (mini == "small") {
                Row(Modifier.fillMaxSize().padding(if (slim) 5.dp else 7.dp), verticalAlignment = Alignment.CenterVertically) {
                    Disc(h - if (slim) 10.dp else 14.dp, clock)
                    Spacer(Modifier.width(8.dp))
                    Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(title, color = st.text, fontSize = 14.sp, fontWeight = FontWeight.Bold, maxLines = 1, textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth().basicMarquee())
                        if (!slim) Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center, modifier = Modifier.fillMaxWidth()) {
                            Text(sub, color = st.sub, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center, modifier = Modifier.weight(1f, fill = false))
                            SleepBadge(st.sub)
                        }
                        TimeBar(Modifier.fillMaxWidth(), 4.dp, 5.dp)
                    }
                    if (radio) CtlBtn(recKind, if (slim) 22.dp else 26.dp, btnCol) { toggleRec() }
                    CtlBtn(playKind, if (slim) 24.dp else 28.dp, btnCol) { Core.toggle() }
                    CtlBtn(ButtonArt.NEXT, 22.dp, btnCol, seekDir = if (radio) 0 else 1) { if (radio) Core.nextStation() else Core.next() }
                }
            } else {
                // Vừa (2 hàng) và To: đủ ⏮ ▶ ⏭ to, thanh thời gian dày có giờ hai đầu
                val large = mini == "large"
                val disc = if (large) 76.dp else 52.dp
                Column(Modifier.fillMaxSize().padding(start = 10.dp, end = 12.dp, top = 8.dp, bottom = 6.dp)) {
                    Row(Modifier.weight(1f).fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Disc(disc, clock)
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(title, color = st.text, fontSize = if (large) 17.sp else 15.sp, fontWeight = FontWeight.Bold, maxLines = 1, textAlign = TextAlign.Center,
                                modifier = Modifier.fillMaxWidth().basicMarquee())
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center, modifier = Modifier.fillMaxWidth()) {
                                Text(if (large) listOf(sub, Core.format.value).filter { it.isNotBlank() }.joinToString("  ·  ") else sub, color = st.sub, fontSize = 12.sp, maxLines = 1,
                                    overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center, modifier = Modifier.weight(1f, fill = false))
                                SleepBadge(st.sub)
                            }
                            if (large) Row(verticalAlignment = Alignment.CenterVertically) {
                                if (radio) CtlBtn(recKind, 34.dp, btnCol) { toggleRec() } else CtlBtn(ButtonArt.PREV, 30.dp, btnCol, seekDir = -1) { Core.prev() }
                                Spacer(Modifier.width(8.dp)); CtlBtn(playKind, 40.dp, btnCol) { Core.toggle() }; Spacer(Modifier.width(8.dp))
                                CtlBtn(ButtonArt.NEXT, 30.dp, btnCol, seekDir = if (radio) 0 else 1) { if (radio) Core.nextStation() else Core.next() }
                            }
                        }
                        if (!large) {
                            if (radio) CtlBtn(recKind, 28.dp, btnCol) { toggleRec() } else CtlBtn(ButtonArt.PREV, 24.dp, btnCol, seekDir = -1) { Core.prev() }
                            CtlBtn(playKind, 32.dp, btnCol) { Core.toggle() }
                            CtlBtn(ButtonArt.NEXT, 24.dp, btnCol, seekDir = if (radio) 0 else 1) { if (radio) Core.nextStation() else Core.next() }
                        }
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(fmtTime(Core.position.longValue), color = st.sub, fontSize = 11.sp)
                        TimeBar(Modifier.weight(1f).padding(horizontal = 6.dp), if (large) 8.dp else 6.dp, if (large) 9.dp else 7.dp)
                        Text(if (radio) "LIVE" else fmtTime(Core.duration.longValue), color = st.sub, fontSize = 11.sp)
                    }
                }
            }
        }
        if (edgeHere) EdgeLight(Modifier.fillMaxSize().clip(shape), radius)
        if (toast.isNotBlank()) Box(Modifier.align(Alignment.TopCenter).padding(top = 2.dp).clip(RoundedCornerShape(10.dp)).background(Color(0xCC000000))
            .padding(horizontal = 10.dp, vertical = 3.dp)) { Text(toast, color = Color.White, fontSize = 12.sp, maxLines = 1) }
    }
}

@Composable
fun SleepBadge(c: Color) {
    val rem = Core.sleepRemaining.longValue
    if (rem >= 0 && Core.sleepMode.value != "NONE") Text("  ⏾ " + fmtTime(rem), color = c, fontSize = 11.sp, fontWeight = FontWeight.Bold)
    else if (Core.sleepMode.value == "END_TRACK" || Core.sleepMode.value == "END_QUEUE") Text("  ⏾", color = c, fontSize = 11.sp)
    if (Core.recording.value) Text("  ● REC", color = Color(0xFFFF5252), fontSize = 11.sp, fontWeight = FontWeight.Bold)
}

