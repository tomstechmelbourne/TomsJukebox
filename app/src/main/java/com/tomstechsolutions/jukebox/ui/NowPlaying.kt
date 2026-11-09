package com.tomstechsolutions.jukebox.ui

import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.media3.common.Player
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.LyricLine
import com.tomstechsolutions.jukebox.data.Lyrics
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.delay
import kotlin.math.roundToInt

fun openOutputSwitcher(ctx: Context) {
    val tries = listOf(
        Intent("com.android.settings.panel.action.MEDIA_OUTPUT").putExtra("com.android.settings.panel.extra.PACKAGE_NAME", ctx.packageName),
        Intent("com.android.systemui.action.LAUNCH_MEDIA_OUTPUT_DIALOG").setPackage("com.android.systemui").putExtra("package_name", ctx.packageName),
        Intent(Settings.ACTION_CAST_SETTINGS), Intent(Settings.ACTION_BLUETOOTH_SETTINGS),
    )
    for (i in tries) {
        try {
            if (i.action == "com.android.systemui.action.LAUNCH_MEDIA_OUTPUT_DIALOG") { ctx.sendBroadcast(i); return }
            ctx.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); return
        } catch (_: Exception) { }
    }
}

@Composable
fun NowPlayingScreen(act: MainActivity, th: JTheme, embedded: Boolean, onClose: () -> Unit, onDriving: () -> Unit) {
    val ctx = LocalContext.current
    val pal = Core.palette.value
    var view by remember { mutableIntStateOf(0) }  // 0 cover, 1 lyrics, 2 queue
    if (act.showLyrics.value) { view = 1; act.showLyrics.value = false }
    val bg = Brush.verticalGradient(listOf(Color(pal[0]).copy(alpha = 0.55f).compositeOverDark(), Color(0xFF15100F), Color(0xFF0A0A0B)))
    androidx.compose.foundation.layout.BoxWithConstraints(Modifier.fillMaxSize()) {
    val short = maxHeight < 560.dp
    val tiny = maxHeight < 430.dp
    Box(Modifier.fillMaxSize().background(if (embedded) Brush.verticalGradient(listOf(Color.Transparent, Color.Transparent)) else bg)
        .then(if (embedded) Modifier else Modifier.windowInsetsPadding(WindowInsets.safeDrawing)).clickable(enabled = false) {}) {
        Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (!embedded) IconBtn(Gl.down, Color.White) { onClose() } else Spacer(Modifier.width(44.dp))
                Text(t("Now Playing", "Đang Phát"), color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Bold, textAlign = TextAlign.Center, modifier = Modifier.weight(1f))
                IconBtn(Gl.car, Color.White) { onDriving() }
                Box {
                    var menu by remember { mutableStateOf(false) }
                    IconBtn(Gl.more, Color.White) { menu = true }
                    androidx.compose.material3.DropdownMenu(menu, { menu = false }) {
                        if (Core.kind.value == "track") {
                            androidx.compose.material3.DropdownMenuItem({ Text(t("Hide From Library", "Bỏ Khỏi Thư Viện")) }, { menu = false; act.hideSongs(listOf(Core.uri.value)) })
                            androidx.compose.material3.DropdownMenuItem({ Text(t("Delete From Phone", "Xoá Khỏi Máy")) }, { menu = false; act.deleteSongs(listOf(Core.uri.value)) })
                        }
                        androidx.compose.material3.DropdownMenuItem({ Text(t("Sleep Timer", "Hẹn Giờ Tắt Nhạc")) }, { menu = false; act.showSleep.value = true })
                    }
                }
            }
            if (tiny && view == 0) Spacer(Modifier.weight(1f))
            else Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                when (view) {
                    1 -> LyricsView(Modifier.fillMaxSize())
                    2 -> QueueView(th, Modifier.fillMaxSize())
                    else -> CoverArea()
                }
            }
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(Core.title.value.ifBlank { "Tom's Jukebox" }, color = Color.White, fontSize = 22.sp, fontFamily = AppFonts.title(), fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(listOf(Core.artist.value, Core.album.value).filter { it.isNotBlank() }.joinToString("  ·  "), color = Color(0xFFE8DCD0), fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    if (Core.format.value.isNotBlank() && !short) Text(Core.format.value, color = Color(0xFFB8A99C), fontSize = 12.sp)
                }
                val fav = Core.uri.value.isNotBlank() && Core.uri.value in Prefs.favSet()
                IconBtn(if (fav) Gl.starFull else Gl.star, if (fav) ORANGE else Color.White) { if (Core.uri.value.isNotBlank()) Prefs.toggleFav(Core.uri.value) }
            }
            if (Core.error.value.isNotBlank()) Text(Core.error.value, color = Color(0xFFFFB4A9), fontSize = 12.sp)
            if (!short && Prefs.vizOn.value && Prefs.vizStrip.value) Visualizer(Modifier.fillMaxWidth().height(46.dp).padding(vertical = 4.dp))
            if (Prefs.skin.value == "ipod") IpodWheel()
            else if (Prefs.playerStyle.value == "card") CardPlayer(Modifier.padding(vertical = 6.dp), compact = false, onLong = { act.showSleep.value = true })
            else Pill(Modifier.padding(vertical = 6.dp), big = true, onLong = { act.showSleep.value = true })
            if (!short) PodTools()
            // extra buttons row: Danh Sách – Lời Bài Hát – Xáo Trộn – Lặp Lại – Hẹn Giờ – Chỉnh Âm – Kết Nối Thiết Bị
            Row(Modifier.fillMaxWidth().padding(bottom = 6.dp), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
                IconBtn(Gl.queue, Color.White, 22.dp, active = view == 2) { view = if (view == 2) 0 else 2 }
                IconBtn(Gl.lyrics, Color.White, 22.dp, active = view == 1) { view = if (view == 1) 0 else 1 }
                IconBtn(Gl.shuffle, Color.White, 22.dp, active = Core.shuffle.value) { Core.toggleShuffle() }
                IconBtn(if (Core.repeat.value == Player.REPEAT_MODE_ONE) Gl.repeatOne else Gl.repeat, Color.White, 22.dp, active = Core.repeat.value != Player.REPEAT_MODE_OFF) { Core.cycleRepeat() }
                IconBtn(Gl.timer, Color.White, 22.dp, active = Core.sleepMode.value != "NONE") { act.showSleep.value = true }
                IconBtn(Gl.eq, Color.White, 22.dp) { act.tab.intValue = 3; onClose() }
                IconBtn(Gl.cast, Color.White, 22.dp) { openOutputSwitcher(ctx) }
            }
        }
    }
    }
}

private fun Color.compositeOverDark(): Color = Color(red * alpha + 0.06f * (1 - alpha), green * alpha + 0.05f * (1 - alpha), blue * alpha + 0.05f * (1 - alpha), 1f)

/** Big cover in the middle. Swipe left/right = next/previous, double-tap = favourite ★. */
@Composable
fun CoverArea() {
    val art = Core.art.value
    var drag by remember { mutableFloatStateOf(0f) }
    var heart by remember { mutableStateOf(0L) }
    val off by animateFloatAsState(drag, label = "drag")
    Box(Modifier.fillMaxSize()
        .pointerInput(Unit) {
            detectHorizontalDragGestures(onDragEnd = {
                if (drag < -120) Core.next() else if (drag > 120) Core.prev()
                drag = 0f
            }) { _, dx -> drag += dx }
        }
        .pointerInput(Unit) {
            detectTapGestures(onDoubleTap = {
                if (Core.uri.value.isNotBlank()) { if (Prefs.toggleFav(Core.uri.value)) heart = System.currentTimeMillis() }
            })
        }, contentAlignment = Alignment.Center) {
        Box(Modifier.fillMaxSize(0.9f).aspectRatio(1f, matchHeightConstraintsFirst = true).offset { IntOffset(off.roundToInt(), 0) }
            .clip(RoundedCornerShape(26.dp)).background(Color(0xFF1C2A33)), contentAlignment = Alignment.Center) {
            if (art != null) Image(art.asImageBitmap(), null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            else G(Gl.note, Color(0x66FFFFFF), 96.dp)
        }
        val since = System.currentTimeMillis() - heart
        if (since < 900) G(Gl.starFull, ORANGE.copy(alpha = 1f - since / 900f), (90 * (1f + since / 900f * 0.6f)).dp)
    }
}

@Composable
fun LyricsView(modifier: Modifier) {
    val ctx = LocalContext.current
    var lines by remember { mutableStateOf<List<LyricLine>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    val title = Core.title.value; val artist = Core.artist.value
    LaunchedEffect(title, artist) {
        if (Core.kind.value == "radio") { lines = emptyList(); return@LaunchedEffect }
        loading = true
        lines = Lyrics.get(ctx, title, artist, Core.album.value, Core.duration.longValue / 1000)
        loading = false
    }
    val pos = Core.position.longValue
    val cur = lines.indexOfLast { it.timeMs in 0..pos }
    val state = rememberLazyListState()
    LaunchedEffect(cur) { if (cur > 2) state.animateScrollToItem((cur - 2).coerceAtLeast(0)) }
    Box(modifier, contentAlignment = Alignment.Center) {
        when {
            loading -> Text(t("Looking for lyrics…", "Đang tìm lời bài hát…"), color = Color(0xFFCCCCCC))
            lines.isEmpty() -> Text(t("No lyrics found for this song.", "Chưa có lời cho bài này."), color = Color(0xFFCCCCCC))
            else -> LazyColumn(state = state, modifier = Modifier.fillMaxSize()) {
                itemsIndexed(lines) { i, l ->
                    Text(l.text.ifBlank { "♪" }, color = if (i == cur) ORANGE else Color.White.copy(alpha = if (i < cur) 0.45f else 0.8f),
                        fontSize = if (i == cur) 22.sp else 18.sp, fontWeight = if (i == cur) FontWeight.Bold else FontWeight.Normal,
                        modifier = Modifier.fillMaxWidth().clickable { if (l.timeMs >= 0) Core.seekTo(l.timeMs) }.padding(vertical = 6.dp))
                }
            }
        }
    }
}

@Composable
fun QueueView(th: JTheme, modifier: Modifier) {
    val q = Core.queue.value
    Column(modifier) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(t("Queue", "Hàng Chờ") + " (${q.size})", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            Btn(t("Clear", "Xoá Hết"), th, Gl.trash) { Core.clearQueue() }
        }
        val state = rememberLazyListState()
        LaunchedEffect(Unit) { if (Core.index.value > 2) state.scrollToItem(Core.index.value - 2) }
        LazyColumn(state = state, modifier = Modifier.weight(1f)) {
            itemsIndexed(q) { i, it ->
                Row2(it.title, it.artist, th.copy(text = Color.White, muted = Color(0xFFBBBBBB)), selected = i == Core.index.value,
                    leading = { Text("${i + 1}", color = Color(0xFF999999), fontSize = 12.sp, modifier = Modifier.width(26.dp)) },
                    trailing = {
                        IconBtn(Gl.up, Color(0xFFCCCCCC), 18.dp, pad = 6.dp) { Core.move(i, i - 1) }
                        IconBtn(Gl.down, Color(0xFFCCCCCC), 18.dp, pad = 6.dp) { Core.move(i, i + 1) }
                        IconBtn(Gl.close, Color(0xFFCCCCCC), 18.dp, pad = 6.dp) { Core.removeAt(i) }
                    }) { Core.playAt(i) }
            }
        }
    }
}

/** iPod Classic style: a click wheel instead of the pill buttons (original drawing). */
@Composable
fun IpodWheel() {
    val hp = haptic()
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        TimeBar(Modifier.fillMaxWidth().padding(horizontal = 20.dp), 6.dp, 7.dp)
        Box(Modifier.size(190.dp).clip(CircleShape).background(Brush.verticalGradient(listOf(Color(0xFFF7F7F8), Color(0xFFD9DBDF))))
            .pointerInput(Unit) {
                detectTapGestures { o ->
                    val c = Offset(size.width / 2f, size.height / 2f); val d = o - c
                    hp()
                    when {
                        d.getDistance() < size.width * 0.2f -> Core.toggle()
                        kotlin.math.abs(d.x) > kotlin.math.abs(d.y) -> if (d.x > 0) Core.next() else Core.prev()
                        d.y > 0 -> Core.toggle()
                        else -> Core.stop()
                    }
                }
            }, contentAlignment = Alignment.Center) {
            Canvas(Modifier.fillMaxSize()) { drawCircle(Color(0x22000000), size.minDimension * 0.2f + 2, style = Stroke(2f)) }
            Text("MENU", color = Color(0xFF8A8F98), fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.align(Alignment.TopCenter).padding(top = 16.dp))
            G(Gl.prev, Color(0xFF8A8F98), 20.dp, Modifier.align(Alignment.CenterStart).padding(start = 16.dp))
            G(Gl.next, Color(0xFF8A8F98), 20.dp, Modifier.align(Alignment.CenterEnd).padding(end = 16.dp))
            G(if (Core.playing.value) Gl.pause else Gl.play, Color(0xFF8A8F98), 18.dp, Modifier.align(Alignment.BottomCenter).padding(bottom = 16.dp))
            Box(Modifier.size(76.dp).clip(CircleShape).background(Brush.verticalGradient(listOf(Color(0xFFE9EAEC), Color(0xFFCFD2D6)))))
        }
    }
}

@Composable
fun DrivingScreen(th: JTheme, onClose: () -> Unit) {
    var drag by remember { mutableFloatStateOf(0f) }
    Box(Modifier.fillMaxSize().background(Color.Black).windowInsetsPadding(WindowInsets.safeDrawing)
        .pointerInput(Unit) { detectHorizontalDragGestures(onDragEnd = { if (drag < -120) Core.next() else if (drag > 120) Core.prev(); drag = 0f }) { _, dx -> drag += dx } }) {
        Column(Modifier.fillMaxSize().padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                G(Gl.car, ORANGE, 30.dp); Spacer(Modifier.width(10.dp))
                Text(t("Driving Mode", "Chế Độ Lái Xe"), color = ORANGE, fontSize = 20.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                IconBtn(Gl.close, Color.White, 32.dp) { onClose() }
            }
            Spacer(Modifier.weight(1f))
            Text(Core.title.value.ifBlank { "Tom's Jukebox" }, color = Color.White, fontSize = 34.sp, fontFamily = AppFonts.title(), fontWeight = FontWeight.Bold, maxLines = 2, textAlign = TextAlign.Center)
            Text(Core.artist.value, color = Color(0xFFBBBBBB), fontSize = 22.sp, maxLines = 1, textAlign = TextAlign.Center)
            Spacer(Modifier.height(30.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                val bc = buttonColour(Color.White)
                if (Core.kind.value == "radio") CtlBtn(if (Core.recording.value) ButtonArt.REC_STOP else ButtonArt.REC, 72.dp, bc) { if (Core.recording.value) Core.stopRecording() else Core.startRecording() }
                else CtlBtn(ButtonArt.PREV, 72.dp, bc, seekDir = -1) { Core.prev() }
                Spacer(Modifier.width(16.dp))
                CtlBtn(if (Core.playing.value) ButtonArt.PAUSE else ButtonArt.PLAY, 96.dp, bc) { Core.toggle() }
                Spacer(Modifier.width(16.dp))
                CtlBtn(ButtonArt.NEXT, 72.dp, bc, seekDir = if (Core.kind.value == "radio") 0 else 1) { if (Core.kind.value == "radio") Core.nextStation() else Core.next() }
            }
            Spacer(Modifier.height(20.dp))
            TimeBar(Modifier.fillMaxWidth(), 8.dp, 10.dp)
            Spacer(Modifier.weight(1f))
            Text(t("Swipe left / right to change song", "Vuốt trái / phải để đổi bài"), color = Color(0xFF888888), fontSize = 14.sp)
        }
    }
    LaunchedEffect(Unit) { while (true) delay(1000) }
}

