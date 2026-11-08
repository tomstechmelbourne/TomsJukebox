package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/** The 12 visualisations. */
@Composable
fun Visualizer(modifier: Modifier, styleOverride: Int? = null) {
    val clock by rememberClock()
    Canvas(modifier) {
        val style = styleOverride ?: if (Prefs.vizAuto.value) ((clock / 20f).toInt() % 12) else Prefs.viz.value
        drawViz(style, clock, levelsAt(clock), Core.palette.value.map { Color(it) })
    }
}

fun DrawScope.waves(time: Float, lv: FloatArray, cols: List<Color>, maxRatio: Float = 0.45f) {
    val w = size.width; val base = size.height; val maxh = size.height * maxRatio
    for (li in 0 until 5) {
        val c = cols[li % cols.size]
        val path = Path().apply { moveTo(0f, base) }
        for (k in 0..60) {
            val fx = k / 60f
            var y = 0f
            for (b in 0 until 6) {
                val cx = ((b * 0.19f + li * 0.07f + time * 0.03f * (li + 1)) % 1.2f) - 0.1f
                val wid = 0.07f + 0.02f * ((b + li) % 3)
                y += (0.2f + 0.8f * lv[(b * 3 + li * 5) % 24]) * exp(-((fx - cx) / wid).let { it * it })
            }
            path.lineTo(fx * w, base - min(1f, y) * maxh - 2f)
        }
        path.lineTo(w, base); path.close()
        drawPath(path, Brush.verticalGradient(listOf(c.copy(alpha = 0.10f), c.copy(alpha = 0.38f), c.copy(alpha = 0.62f)), base - maxh, base))
    }
}

fun DrawScope.drawViz(style: Int, time: Float, lv: FloatArray, cols: List<Color>) {
    val w = size.width; val h = size.height; val n = lv.size
    when (style) {
        0 -> waves(time, lv, cols, 0.9f)
        1, 2, 6 -> {
            val bw = w / n
            for (i in 0 until n) {
                val v = lv[i].coerceIn(0.02f, 1f)
                val c = if (style == 6) Color.hsv(i * 300f / n, 0.75f, 1f) else cols[i % cols.size]
                if (style == 2) {
                    val bh = v * h / 2
                    drawRoundRect(c, Offset(i * bw + bw * 0.15f, h / 2 - bh), Size(bw * 0.7f, bh * 2), CornerRadius(bw * 0.3f))
                } else drawRoundRect(Brush.verticalGradient(listOf(c, c.copy(alpha = 0.35f))), Offset(i * bw + bw * 0.15f, h - v * h),
                    Size(bw * 0.7f, v * h), CornerRadius(bw * 0.3f))
            }
        }
        3 -> {
            val bw = w / n
            for (i in 0 until n) {
                val dots = (lv[i] * 8).toInt()
                for (d in 0..dots) drawCircle(cols[i % cols.size].copy(alpha = 0.4f + 0.6f * d / 8f), bw * 0.28f, Offset(i * bw + bw / 2, h - d * bw * 0.75f - bw / 2))
            }
        }
        4 -> {
            val p = Path()
            for (i in 0 until n) { val x = i * w / (n - 1); val y = h / 2 - (lv[i] - 0.3f) * h * 0.8f * sin(time * 2 + i).let { if (it < 0) -1f else 1f }; if (i == 0) p.moveTo(x, y) else p.lineTo(x, y) }
            drawPath(p, cols[0].copy(alpha = 0.3f), style = Stroke(12f)); drawPath(p, cols[0], style = Stroke(4f))
        }
        5 -> {
            val r = min(w, h) * 0.28f
            for (i in 0 until n * 2) {
                val a = i * 2 * PI.toFloat() / (n * 2) + time * 0.3f
                val v = lv[i % n]
                val r2 = r + v * r * 0.9f
                drawLine(cols[i % cols.size], Offset(center.x + cos(a) * r, center.y + sin(a) * r), Offset(center.x + cos(a) * r2, center.y + sin(a) * r2), 6f)
            }
            drawCircle(cols[0].copy(alpha = 0.25f), r * 0.9f)
        }
        7 -> {
            val bw = w / n
            for (i in 0 until n) {
                val v = lv[i]; val fl = 0.85f + 0.15f * sin(time * 9 + i * 2)
                drawOval(Brush.verticalGradient(listOf(Color(0xFFFFE082), Color(0xFFFF6D00), Color(0x00FF3D00)), h - v * h * fl, h),
                    Offset(i * bw, h - v * h * fl), Size(bw * 1.2f, v * h * fl))
            }
        }
        8 -> {
            for (k in 0 until 60) {
                val life = ((time * 0.4f + k * 0.173f) % 1f)
                val x = ((k * 0.618f) % 1f) * w + sin(time + k) * 10
                val y = h - life * h * (0.4f + lv[k % n])
                drawCircle(cols[k % cols.size].copy(alpha = 1f - life), 3f + lv[k % n] * 6, Offset(x, y))
            }
        }
        9 -> {
            val avg = lv.average().toFloat()
            for (k in 0 until 5) {
                val f = ((time * 0.5f + k / 5f) % 1f)
                drawCircle(cols[k % cols.size].copy(alpha = (1 - f) * (0.3f + avg)), f * max(w, h) * 0.6f, style = Stroke(4f + avg * 8))
            }
        }
        10 -> {
            val p = Path()
            for (k in 0..120) {
                val x = k * w / 120; val i = (k * n / 121).coerceIn(0, n - 1)
                val y = h / 2 + sin(k * 0.35f + time * 8) * lv[i] * h * 0.45f
                if (k == 0) p.moveTo(x, y) else p.lineTo(x, y)
            }
            drawPath(p, Color(0xFF7CFFB2).copy(alpha = 0.35f), style = Stroke(10f)); drawPath(p, Color(0xFF7CFFB2), style = Stroke(3f))
        }
        11 -> {
            val avg = lv.average().toFloat()
            for (k in 0 until 80) {
                val z = ((time * (0.15f + avg * 0.6f) + k * 0.0125f) % 1f)
                val ang = k * 2.39996f
                val rr = z * max(w, h) * 0.7f
                drawCircle(Color.White.copy(alpha = z), 1.5f + z * 3.5f, Offset(center.x + cos(ang) * rr, center.y + sin(ang) * rr))
            }
        }
        else -> waves(time, lv, cols, 0.9f)
    }
}
