package com.tomstechsolutions.jukebox.ui

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.State
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.platform.LocalContext
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import kotlinx.coroutines.delay
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sin

/** One clock for all animations. In battery-saver (below 20 % and not charging) it ticks ~8 times a second. */
object Anim {
    val lowPower = mutableStateOf(false)

    fun checkBattery(ctx: Context) {
        val i = ctx.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED)) ?: return
        val level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, 100) * 100 / max(1, i.getIntExtra(BatteryManager.EXTRA_SCALE, 100))
        val plugged = i.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) != 0
        lowPower.value = Prefs.batterySaver.value && level < 20 && !plugged
    }
}

@Composable
fun rememberClock(): State<Float> {
    val t = remember { mutableFloatStateOf(0f) }
    val ctx = LocalContext.current
    LaunchedEffect(Unit) {
        var lastBattery = 0L
        val start = System.nanoTime()
        while (true) {
            if (Anim.lowPower.value) delay(120)
            withFrameNanos { now -> t.floatValue = (now - start) / 1e9f }
            val ms = System.currentTimeMillis()
            if (ms - lastBattery > 60_000) { lastBattery = ms; Anim.checkBattery(ctx) }
        }
    }
    return t
}

/** Music levels: real ones from the Visualizer when allowed, otherwise gentle made-up ones that follow play/pause. */
private val fake = FloatArray(24)
fun levelsAt(time: Float): FloatArray {
    if (Core.realLevels) return Core.levels.value
    val on = Core.playing.value
    for (i in 0 until 24) {
        val target = if (on) 0.25f + 0.65f * abs(sin(time * (1.3f + i * 0.17f) + i * 0.9f) * sin(time * 0.7f + i * 0.31f)) else 0.04f
        fake[i] = fake[i] + (target - fake[i]) * 0.15f
    }
    return fake
}

fun fmtTime(ms: Long): String {
    if (ms <= 0) return "0:00"
    val s = ms / 1000
    return if (s >= 3600) "%d:%02d:%02d".format(s / 3600, s / 60 % 60, s % 60) else "%d:%02d".format(s / 60, s % 60)
}
