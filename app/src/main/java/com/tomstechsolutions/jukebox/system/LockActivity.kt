package com.tomstechsolutions.jukebox.system

import android.app.KeyguardManager
import android.content.res.Configuration
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.unit.IntOffset
import com.tomstechsolutions.jukebox.Prefs
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import com.tomstechsolutions.jukebox.ui.EdgeLight
import com.tomstechsolutions.jukebox.ui.Pill
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Optional Tom's Jukebox lock screen: big clock, the pill at the bottom like One UI, edge lighting around the screen. */
class LockActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 27) { setShowWhenLocked(true); setTurnScreenOn(true) }
        else {
            @Suppress("DEPRECATION")
            window.addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON)
        }
        Core.connect(applicationContext)
        setContent {
            var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
            var drag by remember { mutableFloatStateOf(0f) }
            LaunchedEffect(Unit) { while (true) { now = System.currentTimeMillis(); delay(1000) } }
            LaunchedEffect(Core.playing.value) { if (!Core.playing.value) { delay(15_000); if (!Core.playing.value) finish() } }
            Box(Modifier.fillMaxSize().background(Color.Black).pointerInput(Unit) {
                detectVerticalDragGestures(onDragEnd = { if (drag < -200) unlock(); drag = 0f }) { _, dy -> drag += dy }
            }.pointerInput(Unit) {
                detectTapGestures(onDoubleTap = { Prefs.lockY.value = -1f; Prefs.lockX.value = 0.5f; Prefs.lockYLand.value = -1f; Prefs.lockXLand.value = 0.5f })
            }) {
                Core.art.value?.let { a ->
                    Image(a.asImageBitmap(), null, Modifier.fillMaxSize().then(if (Build.VERSION.SDK_INT >= 31) Modifier.blur(50.dp) else Modifier),
                        contentScale = ContentScale.Crop, alpha = 0.35f)
                }
                Column(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing).padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Spacer(Modifier.height(60.dp))
                    Text(SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(now)), color = Color.White, fontSize = 88.sp, fontWeight = FontWeight.Light)
                    Text(SimpleDateFormat(t("EEEE, d MMMM", "EEEE, 'ngày' d 'tháng' M"), if (t("en", "vi") == "vi") Locale("vi") else Locale.ENGLISH).format(Date(now)),
                        color = Color(0xFFDDDDDD), fontSize = 18.sp)
                    Spacer(Modifier.weight(1f))
                    Text(t("Swipe up to unlock", "Vuốt lên để mở khoá"), color = Color(0xFF999999), fontSize = 13.sp, modifier = Modifier.padding(top = 14.dp, bottom = 8.dp))
                }
                LockPill()
                EdgeLight(Modifier.fillMaxSize(), com.tomstechsolutions.jukebox.ui.screenCorner())
            }
        }
    }

    private fun unlock() {
        val km = getSystemService(KEYGUARD_SERVICE) as KeyguardManager
        if (Build.VERSION.SDK_INT >= 26) km.requestDismissKeyguard(this, null)
        finish()
    }
}

/**
 * Viên thuốc kéo thả: nhấn giữ nửa giây rồi kéo. Tự hít vào Trên / Giữa / Dưới (tắt được),
 * tránh vùng đồng hồ, vùng vân tay và chữ "Vuốt lên"; nhớ vị trí riêng khi xoay ngang.
 */
@Composable
private fun LockPill() {
    val hp = LocalHapticFeedback.current
    val land = LocalConfiguration.current.orientation == Configuration.ORIENTATION_LANDSCAPE
    val yPref = if (land) Prefs.lockYLand else Prefs.lockY
    val xPref = if (land) Prefs.lockXLand else Prefs.lockX
    var dragging by remember { mutableStateOf(false) }
    var dy by remember { mutableFloatStateOf(0f) }
    var dx by remember { mutableFloatStateOf(0f) }
    BoxWithConstraints(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
        val dens = LocalDensity.current
        val size = Prefs.lockSize.value
        val card = Prefs.lockStyle.value == "card"
        val pillW = minOf(maxWidth - 24.dp, 460.dp)
        val pillH = if (card) (pillW - 20.dp) / 1.25f + 200.dp else when (size) { "small" -> 66.dp; "large" -> 150.dp; else -> 106.dp }
        val top = if (land) 16.dp else if (Prefs.lockStyle.value == "card") 200.dp else 230.dp     // dưới đồng hồ
        val bottomGap = if (land) 40.dp else 130.dp              // vân tay + chữ "Vuốt lên"
        with(dens) {
            val minY = top.toPx(); val maxY = (maxHeight - bottomGap - pillH).toPx().coerceAtLeast(minY)
            val maxX = (maxWidth - pillW).toPx().coerceAtLeast(0f)
            val f = yPref.value.let { if (it < 0f) 1f else it.coerceIn(0f, 1f) }
            val baseY = minY + (maxY - minY) * f
            val baseX = maxX * xPref.value.coerceIn(0f, 1f)
            val y = (baseY + dy).coerceIn(minY, maxY); val x = (baseX + dx).coerceIn(0f, maxX)
            if (dragging) {
                for (g in listOf(0f, 0.5f, 1f)) {
                    val gy = minY + (maxY - minY) * g + pillH.toPx() / 2
                    Box(Modifier.offset { IntOffset(0, gy.toInt()) }.fillMaxWidth().height(1.dp).background(Color(0x55FFFFFF)))
                }
            }
            Box(Modifier.offset { IntOffset(x.toInt(), y.toInt()) }.width(pillW).height(pillH)
                .graphicsLayer { alpha = Prefs.lockAlpha.value.coerceIn(0.2f, 1f); scaleX = if (dragging) 1.04f else 1f; scaleY = if (dragging) 1.04f else 1f }
                .pointerInput(Prefs.lockLocked.value, land) {
                    if (Prefs.lockLocked.value) return@pointerInput
                    detectDragGesturesAfterLongPress(
                        onDragStart = { dragging = true; hp.performHapticFeedback(HapticFeedbackType.LongPress) },
                        onDragEnd = {
                            var nf = if (maxY > minY) ((y - minY) / (maxY - minY)) else 1f
                            if (Prefs.lockSnap.value) nf = listOf(0f, 0.5f, 1f).minBy { kotlin.math.abs(it - nf) }
                            yPref.value = if (nf >= 0.999f) -1f else nf
                            xPref.value = if (maxX > 0f) x / maxX else 0.5f
                            dx = 0f; dy = 0f; dragging = false
                            hp.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        },
                        onDragCancel = { dx = 0f; dy = 0f; dragging = false },
                    ) { ch, d -> ch.consume(); dx += d.x; dy += d.y }
                }) {
                if (card) com.tomstechsolutions.jukebox.ui.LockCard()
                else when (size) {
                    "large" -> Pill(Modifier, big = true, gestures = false)
                    else -> Pill(Modifier, big = false, sizeKey = size, gestures = false)
                }
                Text(if (Prefs.lockLocked.value) "🔒" else "🔓", fontSize = 13.sp, modifier = Modifier.align(Alignment.TopEnd).offset { IntOffset(0, -30) }
                    .pointerInput(Unit) { detectTapGestures { Prefs.lockLocked.value = !Prefs.lockLocked.value } }.padding(6.dp))
            }
        }
    }
}
