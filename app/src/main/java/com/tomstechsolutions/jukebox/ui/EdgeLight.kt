package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.RoundRect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.PathMeasure
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sin

/** "Ánh sáng chạy viền": 12 effects running around a rounded edge, like Samsung Music's old edge lighting. */
@Composable
fun EdgeLight(modifier: Modifier, radius: Dp, effectOverride: Int? = null, force: Boolean = false) {
    val clock by rememberClock()
    Canvas(modifier) {
        if (!force && !Core.playing.value) return@Canvas
        if (Anim.lowPower.value && !force) return@Canvas
        val auto = Prefs.edgeAuto.value && effectOverride == null
        val effect = effectOverride ?: if (auto) ((clock / 30f).toInt() % 12) else Prefs.edgeEffect.value
        drawEdge(effect, clock, radius.toPx(), edgeColours(), Prefs.edgeThick.value.dp.toPx(), Prefs.edgeBright.value,
            EdgeEffects.speeds[Prefs.edgeSpeed.value.coerceIn(0, 4)])
    }
}

fun edgeColours(): List<Color> = when (Prefs.edgeColour.value) {
    "rainbow" -> BarColours.gradients["rainbow"]!!
    "brand" -> listOf(SKY, ORANGE)
    "custom" -> listOf(Color(Prefs.edgeCustom.value), Color(Prefs.edgeCustom.value).copy(alpha = 0.8f))
    else -> Core.palette.value.map { Color(it) }
}

private fun colourAt(cols: List<Color>, f: Float): Color {
    if (cols.size == 1) return cols[0]
    val x = ((f % 1f + 1f) % 1f) * cols.size
    val i = x.toInt() % cols.size
    return lerp(cols[i], cols[(i + 1) % cols.size], x - x.toInt())
}

fun DrawScope.drawEdge(effect: Int, time: Float, radiusPx: Float, cols: List<Color>, thick: Float, bright: Float, speed: Float) {
    val inset = thick / 2 + 1
    val path = Path().apply {
        addRoundRect(RoundRect(inset, inset, size.width - inset, size.height - inset, CornerRadius(max(0f, radiusPx - inset))))
    }
    val pm = PathMeasure(); pm.setPath(path, true)
    val len = pm.length
    if (len <= 0f) return
    val t = time * speed
    var beatBoost = 0f
    if (Prefs.edgeBeat.value) {
        val since = System.currentTimeMillis() - Core.beat.longValue
        beatBoost = if (since < 300) (1f - since / 300f) * 0.6f else 0f
        if (!Core.realLevels) beatBoost = max(beatBoost, levelsAt(time).take(4).average().toFloat() * 0.25f)
    }
    val a = (bright + beatBoost).coerceIn(0.05f, 1f)

    fun seg(from: Float, segLen: Float, c: Color, w: Float = thick, alpha: Float = a) {
        val dst = Path()
        var s = ((from % len) + len) % len
        val e = s + segLen
        if (e <= len) pm.getSegment(s, e, dst, true)
        else { pm.getSegment(s, len, dst, true); pm.getSegment(0f, e - len, dst, true) }
        drawPath(dst, c.copy(alpha = alpha * 0.28f), style = Stroke(w * 3.2f, cap = StrokeCap.Round))
        drawPath(dst, c.copy(alpha = alpha), style = Stroke(w, cap = StrokeCap.Round))
        s += 0
    }
    fun whole(c: Color, alpha: Float = a, w: Float = thick) {
        drawPath(path, c.copy(alpha = alpha * 0.25f), style = Stroke(w * 3.5f))
        drawPath(path, c.copy(alpha = alpha), style = Stroke(w))
    }
    fun wholeBrush(b: Brush, alpha: Float = a) {
        drawPath(path, b, alpha = alpha * 0.25f, style = Stroke(thick * 3.5f))
        drawPath(path, b, alpha = alpha, style = Stroke(thick))
    }

    when (effect) {
        0 -> for (k in 0 until 3) seg(t * len * 0.18f + k * len / 3f, len * 0.12f, colourAt(cols, k / 3f))       // chasing streaks
        1 -> {                                                                                                      // shooting star
            val head = t * len * 0.28f
            for (k in 0 until 14) {
                val f = k / 14f
                seg(head - len * 0.22f * f, len * 0.022f, colourAt(cols, f * 0.5f), thick * (1f - f * 0.7f), a * (1f - f))
            }
        }
        2 -> rotate(t * 90f) { wholeBrush(Brush.sweepGradient(BarColours.gradients["rainbow"]!! + BarColours.gradients["rainbow"]!!.first(), center)) }
        3 -> whole(colourAt(cols, t * 0.05f), a * (0.15f + 0.85f * sin(t * 1.6f).let { it * it }))                // breathing
        4 -> {                                                                                                      // music beat
            val lv = levelsAt(time); val avg = lv.average().toFloat()
            whole(colourAt(cols, t * 0.1f), (0.2f + avg * 1.2f + beatBoost).coerceIn(0f, 1f), thick * (0.8f + avg * 1.6f))
        }
        5 -> wholeBrush(Brush.linearGradient(List(6) { colourAt(cols, it / 6f + t * 0.15f) }, Offset.Zero, Offset(size.width, size.height)))
        6 -> {                                                                                                      // two ends meet
            val p = (t * 0.35f) % 1f
            val bottomMid = len * 0.0f + (size.width / 2 - radiusPx).coerceAtLeast(0f) + 0f
            val start = bottomMid
            val grow = len / 2f * p
            seg(start, grow, colourAt(cols, 0f), alpha = a * (1f - p * 0.3f))
            seg(start - grow, grow, colourAt(cols, 0.5f), alpha = a * (1f - p * 0.3f))
        }
        7 -> {                                                                                                      // neon
            val flicker = if (sin(t * 23f) > 0.97f) 0.5f else 1f
            val c = colourAt(cols, 0f)
            drawPath(path, c.copy(alpha = a * 0.15f * flicker), style = Stroke(thick * 6f))
            whole(c, a * flicker)
            drawPath(path, Color.White.copy(alpha = 0.7f * a * flicker), style = Stroke(thick * 0.35f))
        }
        8 -> {                                                                                                      // sparkle
            whole(colourAt(cols, 0f), a * 0.18f)
            for (k in 0 until 26) {
                val ph = (t * 1.3f + k * 0.37f)
                val tw = sin(ph * PI.toFloat()).let { it * it }
                val pos = pm.getPosition(((k * 0.618f + (ph.toInt() * 0.13f)) % 1f) * len)
                drawCircle(colourAt(cols, k / 26f).copy(alpha = a * tw), thick * 0.9f * (0.5f + tw), pos)
                drawCircle(Color.White.copy(alpha = a * tw * 0.8f), thick * 0.35f, pos)
            }
        }
        9 -> {                                                                                                      // running dashes
            val dash = PathEffect.dashPathEffect(floatArrayOf(thick * 5, thick * 4), -t * thick * 18)
            drawPath(path, colourAt(cols, t * 0.1f).copy(alpha = a * 0.25f), style = Stroke(thick * 3f, pathEffect = dash))
            drawPath(path, colourAt(cols, t * 0.1f).copy(alpha = a), style = Stroke(thick, cap = StrokeCap.Round, pathEffect = dash))
        }
        10 -> {                                                                                                     // fire
            val fire = listOf(Color(0xFFFF3D00), Color(0xFFFF9100), Color(0xFFFFD54F))
            for (k in 0 until 18) {
                val fl = abs(sin(t * 3.1f + k * 1.7f))
                seg(k * len / 18f + sin(t + k) * 8, len / 18f * (0.4f + fl * 0.8f), fire[k % 3], thick * (0.6f + fl), a * (0.4f + 0.6f * fl))
            }
        }
        11 -> {                                                                                                     // frost
            whole(Color(0xFFBFE9FF), a * 0.45f)
            seg(t * len * 0.12f, len * 0.18f, Color.White, thick, a)
            seg(t * len * 0.12f + len / 2, len * 0.18f, Color(0xFF7FD3FF), thick, a * 0.8f)
        }
        else -> whole(colourAt(cols, 0f))
    }
}

/** A small box that previews one effect (used in Settings). */
@Composable
fun EdgePreview(effect: Int, modifier: Modifier) {
    val clock by rememberClock()
    Canvas(modifier) {
        drawRoundRect(Color(0xFF0B1720), cornerRadius = CornerRadius(14.dp.toPx()))
        drawEdge(effect, clock, 14.dp.toPx(), edgeColours(), 3.dp.toPx(), 1f, EdgeEffects.speeds[Prefs.edgeSpeed.value.coerceIn(0, 4)])
    }
}

@Suppress("unused") private fun Size.minDim() = minOf(width, height)
