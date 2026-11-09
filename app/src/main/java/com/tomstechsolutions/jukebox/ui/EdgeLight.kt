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
        val count = EdgeEffects.names.size
        val (chosen, mo) = Motifs.edgeStyle()
        val effect = effectOverride ?: when {
            Prefs.edgeRandom.value -> ((Core.uri.value.hashCode() and 0x7fffffff) % count)
            auto -> ((clock / 30f).toInt() % count)
            else -> chosen
        }
        drawEdge(effect, clock, radius.toPx(), if (mo != null && effectOverride == null) mo.colours.drop(1) else edgeColours(), Prefs.edgeThick.value.dp.toPx(), Prefs.edgeBright.value,
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
        in 12..27 -> drawEdge2(effect, t, time, path, pm, len, radiusPx, cols, thick, a, beatBoost)
        else -> whole(colourAt(cols, 0f))
    }
}

private fun DrawScope.drawEdge2(effect: Int, t: Float, time: Float, path: Path, pm: PathMeasure, len: Float, radiusPx: Float,
                                cols: List<Color>, thick: Float, a: Float, beat: Float) {
    fun seg(from: Float, segLen: Float, c: Color, w: Float = thick, alpha: Float = a) {
        val dst = Path(); val s = ((from % len) + len) % len; val e = s + segLen.coerceAtMost(len)
        if (e <= len) pm.getSegment(s, e, dst, true) else { pm.getSegment(s, len, dst, true); pm.getSegment(0f, e - len, dst, true) }
        drawPath(dst, c.copy(alpha = (alpha * 0.28f).coerceIn(0f, 1f)), style = Stroke(w * 3.2f, cap = StrokeCap.Round))
        drawPath(dst, c.copy(alpha = alpha.coerceIn(0f, 1f)), style = Stroke(w, cap = StrokeCap.Round))
    }
    fun whole(c: Color, alpha: Float = a, w: Float = thick) {
        drawPath(path, c.copy(alpha = (alpha * 0.25f).coerceIn(0f, 1f)), style = Stroke(w * 3.5f)); drawPath(path, c.copy(alpha = alpha.coerceIn(0f, 1f)), style = Stroke(w))
    }
    fun pos(d: Float) = pm.getPosition(((d % len) + len) % len)
    val lv = levelsAt(time); val avg = lv.average().toFloat(); val bass = (lv[0] + lv[1] + lv[2]) / 3f
    when (effect) {
        12 -> { val aur = listOf(Color(0xFF3DFFB0), Color(0xFF3DA8FF), Color(0xFFB45CFF), Color(0xFFFF6FB5))       // Cực Quang
            for (k in 0 until 4) seg(t * len * 0.05f + k * len / 4f, len * 0.3f, aur[k], thick * (1.2f + sin(t + k) * 0.4f), a * 0.7f) }
        13 -> { val n = 120; for (k in 0 until n) { val d = len * k / n; val p = pos(d)                               // Gợn Sóng Nước
                val r = thick * (0.5f + (sin(d * 0.03f - t * 4f) * 0.5f + 0.5f) * (1f + avg * 2f)); drawCircle(colourAt(cols, k / n.toFloat()).copy(alpha = a * 0.6f), r, p) } }
        14 -> { val r = kotlin.random.Random(9); repeat(160) { k -> val d = (r.nextFloat() * len + t * len * 0.02f * (0.5f + r.nextFloat())); val p = pos(d)   // Bụi Sao
                val tw = sin(time * 4 + k) * 0.5f + 0.5f; drawCircle(colourAt(cols, r.nextFloat()).copy(alpha = a * tw), 0.6f + r.nextFloat() * thick * 0.4f, p) } }
        15 -> drawPath(path, Brush.sweepGradient(listOf(Color(0xFFFF9A3C), Color(0xFFFF5E7E), Color(0xFF9B5CFF), Color(0xFFFF9A3C))), alpha = a, style = Stroke(thick))   // Hoàng Hôn Trượt
        16 -> { val ph = (time * 1.2f) % 1f; val pulse = if (ph < 0.12f) 1f else if (ph in 0.22f..0.34f) 0.7f else 0.15f   // Tim Đập
                whole(Color(0xFFFF4D6D), (a * (pulse + beat)).coerceIn(0f, 1f), thick * (1f + pulse * 0.8f)) }
        17 -> { val speed = 0.1f + bass * 0.9f; seg(time * len * speed, len * (0.08f + bass * 0.15f), colourAt(cols, 0f), thick * (1f + bass)) ;   // Chạy Theo Bass
                seg(time * len * speed + len / 2, len * (0.08f + bass * 0.15f), colourAt(cols, 0.5f), thick * (1f + bass)) }
        18 -> { val n = 96; for (k in 0 until n) { val d = len * k / n; val p = pos(d); val p2 = pos(d + 1f)              // Cột Sóng Viền
                val nx = -(p2.y - p.y); val ny = (p2.x - p.x); val l = kotlin.math.sqrt(nx * nx + ny * ny).coerceAtLeast(0.001f)
                val v = lv[k % lv.size] * thick * 6f
                drawLine(colourAt(cols, k / n.toFloat()).copy(alpha = a), p, Offset(p.x + nx / l * v, p.y + ny / l * v), thick * 0.6f) } }
        19 -> { val corners = listOf(Offset(radiusPx, radiusPx), Offset(size.width - radiusPx, radiusPx), Offset(size.width - radiusPx, size.height - radiusPx), Offset(radiusPx, size.height - radiusPx))   // Pháo Hoa
                corners.forEachIndexed { i, c -> val life = ((time * 0.7f + i * 0.25f + beat) % 1f)
                    for (k in 0 until 12) { val ang = k * 30f * 3.14159f / 180f; val r = life * radiusPx * 1.6f
                        drawCircle(colourAt(cols, k / 12f).copy(alpha = a * (1 - life)), thick * 0.5f, Offset(c.x + kotlin.math.cos(ang) * r, c.y + sin(ang) * r)) } }
                whole(colourAt(cols, 0f), a * 0.2f) }
        20 -> { val p = (t * 0.25f) % 1f; seg(p * len, len * 0.12f, colourAt(cols, 0f)); seg(-p * len, len * 0.12f, colourAt(cols, 0.5f))   // Vệt Ngược Chiều
                if (kotlin.math.abs(p - 0.5f) < 0.03f || p < 0.03f) whole(Color.White, a * 0.6f) }
        21 -> for (k in 0 until 4) seg(len * k / 4f + t * len * 0.08f, len * 0.07f, colourAt(cols, k / 4f))            // Bốn Góc Đuổi Nhau
        22 -> { for (k in 0 until 30) { val side = if (k % 2 == 0) thick else size.width - thick                          // Mưa Sao Rơi
                val y = ((t * 0.3f + k * 0.071f) % 1f) * size.height
                drawLine(colourAt(cols, k / 30f).copy(alpha = a), Offset(side, y), Offset(side, y - thick * 6), thick * 0.7f) } }
        23 -> { whole(Color(0xFFBFD7FF), a * 0.15f)                                                                       // Tia Chớp
                val flash = (sin(time * 7.3f) * sin(time * 3.1f)) > 0.85f || beat > 0.45f
                if (flash) { val start = ((time * 1000).toInt() % 997) / 997f * len; val pth = Path(); val r = kotlin.random.Random((time * 10).toInt())
                    for (k in 0..16) { val p = pos(start + k * len * 0.012f); val j = (r.nextFloat() - 0.5f) * thick * 5; if (k == 0) pth.moveTo(p.x + j, p.y + j) else pth.lineTo(p.x + j, p.y - j) }
                    drawPath(pth, Color.White.copy(alpha = a), style = Stroke(thick * 0.8f)); drawPath(pth, Color(0xFF7FB2FF).copy(alpha = a * 0.4f), style = Stroke(thick * 3)) } }
        24 -> { val n = 140; val pth = Path(); for (k in 0..n) { val d = len * k / n; val p = pos(d); val j = sin(d * 0.2f + t * 12f) * thick * (0.6f + avg * 2f)   // Điện Từ
                if (k == 0) pth.moveTo(p.x + j, p.y + j) else pth.lineTo(p.x + j, p.y - j) }
                drawPath(pth, Color(0xFF8CF2FF).copy(alpha = a * 0.3f), style = Stroke(thick * 2.5f)); drawPath(pth, Color.White.copy(alpha = a), style = Stroke(thick * 0.5f)) }
        25 -> { whole(Color.White, a * 0.1f); for (k in 0 until 18) { val ph = (time * 0.9f + k * 0.37f) % 1f; val p = pos(len * ((k * 0.618f) % 1f))   // Ánh Kim Cương
                val s = thick * 2.5f * sin(ph * 3.14159f); drawLine(Color.White.copy(alpha = a), Offset(p.x - s, p.y), Offset(p.x + s, p.y), 1.5f); drawLine(Color.White.copy(alpha = a), Offset(p.x, p.y - s), Offset(p.x, p.y + s), 1.5f) } }
        26 -> { val bulbs = listOf(Color(0xFFFF3B30), Color(0xFF34C759), Color(0xFFFFCC00), Color(0xFF0A84FF), Color(0xFFFF2D9A))   // Đèn Giáng Sinh
                val n = 48; drawPath(path, Color(0xFF1E5F2A).copy(alpha = a * 0.6f), style = Stroke(thick * 0.4f))
                for (k in 0 until n) { val on = ((k + (t * 3).toInt()) % 3) != 0; val p = pos(len * k / n)
                    drawCircle(bulbs[k % bulbs.size].copy(alpha = if (on) a else a * 0.2f), thick * 0.9f, p); if (on) drawCircle(bulbs[k % bulbs.size].copy(alpha = a * 0.25f), thick * 2.2f, p) } }
        else -> { whole(Color(0xFFD7261E), a * 0.6f)                                                                      // Đèn Tết
                val n = 20; for (k in 0 until n) { val p = pos(len * k / n + t * len * 0.02f); drawCircle(Color(0xFFFFD54F).copy(alpha = a), thick * 1.1f, p) }
                seg(t * len * 0.15f, len * 0.1f, Color(0xFFFFE082)) }
    }
}

/** The real corner radius of the phone's screen (Android 12+), or the user's own setting. */
@Composable
fun screenCorner(): Dp {
    val manual = Prefs.edgeCorner.value
    if (manual >= 0f) return manual.dp
    val view = androidx.compose.ui.platform.LocalView.current
    val density = androidx.compose.ui.platform.LocalDensity.current
    if (android.os.Build.VERSION.SDK_INT >= 31) {
        val r = view.rootWindowInsets?.getRoundedCorner(android.view.RoundedCorner.POSITION_TOP_LEFT)?.radius ?: 0
        if (r > 0) return with(density) { r.toDp() }
    }
    return 30.dp
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
