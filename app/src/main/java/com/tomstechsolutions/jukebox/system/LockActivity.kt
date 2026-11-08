package com.tomstechsolutions.jukebox.system

import android.app.KeyguardManager
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
                    Pill(Modifier.padding(horizontal = 4.dp), big = true)
                    Text(t("Swipe up to unlock", "Vuốt lên để mở khoá"), color = Color(0xFF999999), fontSize = 13.sp, modifier = Modifier.padding(top = 14.dp, bottom = 8.dp))
                }
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
