package com.tomstechsolutions.jukebox.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.delay

/** Hiệu ứng sóng nhạc toàn màn hình. Vuốt ngang để đổi kiểu, chạm để hiện nút. */
@Composable
fun FullViz(onClose: () -> Unit) {
    BackHandler { onClose() }
    var shown by remember { mutableStateOf(true) }
    var touched by remember { mutableLongStateOf(System.currentTimeMillis()) }
    var drag by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(touched) { delay(3500); shown = false }
    val n = VizStyles.names.size
    fun step(d: Int) { var v = ((Prefs.viz.value + d) % n + n) % n; if (v in VizStyles.removed) v = ((v + d) % n + n) % n; Prefs.viz.value = v; Prefs.vizAuto.value = false; touched = System.currentTimeMillis(); shown = true }
    Box(Modifier.fillMaxSize().background(Color.Black)
        .pointerInput(Unit) { detectTapGestures { shown = !shown; touched = System.currentTimeMillis() } }
        .pointerInput(Unit) { detectHorizontalDragGestures(onDragEnd = { if (drag < -80) step(1) else if (drag > 80) step(-1); drag = 0f }) { _, dx -> drag += dx } }) {
        Visualizer(Modifier.fillMaxSize())
        AnimatedVisibility(shown, enter = fadeIn(), exit = fadeOut()) {
            Column(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing).padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconBtn(Gl.back, Color.White, pad = 12.dp) { onClose() }
                    Column(Modifier.weight(1f)) {
                        Text(VizStyles.name(Prefs.viz.value), color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        Text("${Prefs.viz.value + 1} / $n", color = Color(0xFFBBBBBB), fontSize = 12.sp)
                    }
                    val fav = Motifs.isFav("viz", "v:${Prefs.viz.value}")
                    Text(if (fav) "★" else "☆", color = Color(0xFFFFD54F), fontSize = 28.sp, modifier = Modifier.clip(RoundedCornerShape(20.dp))
                        .pointerInput(Prefs.viz.value) { detectTapGestures { Motifs.toggleFav("viz", "v:${Prefs.viz.value}"); touched = System.currentTimeMillis() } }.padding(10.dp))
                }
                Spacer(Modifier.weight(1f))
                Text(Core.title.value, color = Color.White, fontSize = 16.sp, maxLines = 1, modifier = Modifier.fillMaxWidth())
                Text(t("Swipe left / right for another effect", "Vuốt trái / phải để đổi hiệu ứng"), color = Color(0xFFBBBBBB), fontSize = 12.sp)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CtlBtn(ButtonArt.PREV, 30.dp, Color.White, -1) { Core.prev() }
                    CtlBtn(if (Core.playing.value) ButtonArt.PAUSE else ButtonArt.PLAY, 40.dp, Color.White) { Core.toggle() }
                    CtlBtn(ButtonArt.NEXT, 30.dp, Color.White, 1) { Core.next() }
                }
            }
        }
    }
}
