package com.tomstechsolutions.jukebox.playback

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.audiofx.Visualizer
import androidx.core.content.ContextCompat
import com.tomstechsolutions.jukebox.Prefs
import kotlin.math.hypot
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

/** Real music levels from Android's Visualizer (needs the microphone permission, optional). Otherwise the screen
 *  draws gentle made-up waves. */
class Viz(private val ctx: Context) {
    private var v: Visualizer? = null
    private var avgEnergy = 0f

    fun attach(session: Int) {
        release()
        if (!Prefs.realViz.value || session == 0) return
        if (ContextCompat.checkSelfPermission(ctx, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return
        try {
            val vis = Visualizer(session)
            vis.captureSize = Visualizer.getCaptureSizeRange()[1].coerceAtMost(1024)
            vis.setDataCaptureListener(object : Visualizer.OnDataCaptureListener {
                override fun onWaveFormDataCapture(vz: Visualizer?, waveform: ByteArray?, rate: Int) {}
                override fun onFftDataCapture(vz: Visualizer?, fft: ByteArray?, rate: Int) { fft?.let { onFft(it) } }
            }, Visualizer.getMaxCaptureRate() / 2, false, true)
            vis.enabled = true
            v = vis
            Core.realLevels = true
        } catch (_: Exception) { Core.realLevels = false }
    }

    private fun onFft(fft: ByteArray) {
        val n = fft.size / 2
        val out = FloatArray(24)
        var energy = 0f
        for (b in 0 until 24) {
            val lo = max(1, (n * (2.0.pow(b / 24.0 * 9.5) / 2.0.pow(9.5))).toInt())
            val hi = max(lo + 1, min(n - 1, (n * (2.0.pow((b + 1) / 24.0 * 9.5) / 2.0.pow(9.5))).toInt()))
            var m = 0f
            for (k in lo until hi) {
                val re = fft[2 * k].toFloat(); val im = fft[2 * k + 1].toFloat()
                m = max(m, hypot(re, im))
            }
            val db = (ln(1 + m) / ln(129f)).coerceIn(0f, 1f)
            out[b] = db
            energy += db
        }
        val prev = Core.levels.value
        Core.levels.value = FloatArray(24) { max(out[it], prev[it] * 0.82f) }
        avgEnergy = avgEnergy * 0.92f + energy * 0.08f
        if (energy > avgEnergy * 1.35f && energy > 4f) Core.beat.value = System.currentTimeMillis()
    }

    fun release() {
        try { v?.enabled = false; v?.release() } catch (_: Exception) { }
        v = null
        Core.realLevels = false
    }
}
