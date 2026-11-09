package com.tomstechsolutions.jukebox.ui

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.unit.dp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/** Text and button colours for a theme skin. */
fun motifSkinStyle(i: Int): SkinStyle {
    val mo = Motifs.list[i]
    return if (mo.light) SkinStyle(Color(0xFF231A14), Color(0xFF4A3A30), Color(0xFF231A14), mo.colours[3], 20.dp)
    else SkinStyle(Color.White, Motifs.lighten(mo.colours[2], 0.6f), Color.White, mo.accent.copy(alpha = 0.8f), null)
}

/** Paints a theme skin: the theme's colours plus its pattern. */
fun DrawScope.paintMotifSkin(i: Int, clock: Float) {
    val mo = Motifs.list[i]; val c = mo.colours; val w = size.width; val h = size.height
    if (mo.pattern == 8) {                                          // Cờ Vàng Ba Sọc Đỏ: nền vàng, ba sọc đỏ ở giữa
        drawRect(Color(0xFFFFDA00))
        for (s in 0 until 3) drawRect(Color(0xFFDA251D).copy(alpha = 0.85f), Offset(0f, h * (5 + s * 2) / 15f), Size(w, h / 15f))
        drawRect(Brush.verticalGradient(listOf(Color(0x40FFFFFF), Color.Transparent), 0f, h * 0.4f))
        return
    }
    if (mo.light) drawRect(Brush.verticalGradient(listOf(c[0], c[0].darken(0.92f))))
    else drawRect(Brush.linearGradient(listOf(c[0].darken(0.95f), c[0].darken(0.55f), c[0].darken(0.8f)), Offset.Zero, Offset(w, h)))
    val ink = if (mo.light) c[1].copy(alpha = 0.18f) else c[1].copy(alpha = 0.22f)
    val ink2 = if (mo.light) c[2].copy(alpha = 0.25f) else c[2].copy(alpha = 0.16f)
    when (mo.pattern) {
        0 -> for (k in 0 until 4) { val p = Path(); for (x in 0..40) { val xx = w * x / 40f; val yy = h * (0.3f + k * 0.15f) + sin(xx * 0.03f + k + clock * 0.3f) * h * 0.08f; if (x == 0) p.moveTo(xx, yy) else p.lineTo(xx, yy) }; drawPath(p, if (k % 2 == 0) ink else ink2, style = Stroke(2.5f)) }
        1 -> { var y = 8f; var r = 0; while (y < h) { var x = if (r % 2 == 0) 8f else 20f; while (x < w) { drawCircle(if ((x.toInt() / 24 + r) % 3 == 0) ink2 else ink, 3f, Offset(x, y)); x += 24f }; y += 14f; r++ } }
        2 -> { var x = -h; while (x < w) { drawLine(ink, Offset(x, h), Offset(x + h, 0f), 6f); drawLine(ink2, Offset(x + 12, h), Offset(x + 12 + h, 0f), 2f); x += 26f } }
        3 -> for (k in 1..6) { drawCircle(if (k % 2 == 0) ink else ink2, h * 0.25f * k, Offset(w * 0.85f, h * 0.5f), style = Stroke(2f)) }
        4 -> { val r = kotlin.random.Random(i); repeat(40) { drawCircle(Color.White.copy(alpha = 0.15f + r.nextFloat() * 0.4f * (0.6f + 0.4f * sin(clock + it))), 0.8f + r.nextFloat() * 1.6f, Offset(r.nextFloat() * w, r.nextFloat() * h)) } }
        5 -> for (k in 0 until 6) { val cx = w * (0.1f + k * 0.17f); val cy = h * (if (k % 2 == 0) 0.3f else 0.7f); val rr = h * 0.14f
                for (p in 0 until 5) { val a = p * 2 * PI.toFloat() / 5; drawCircle(ink, rr * 0.55f, Offset(cx + cos(a) * rr * 0.6f, cy + sin(a) * rr * 0.6f)) }; drawCircle(ink2, rr * 0.25f, Offset(cx, cy)) }
        6 -> { var x = 0f; while (x < w) { drawLine(ink, Offset(x, 0f), Offset(x, h), 1f); x += 16f }; var y = 0f; while (y < h) { drawLine(ink, Offset(0f, y), Offset(w, y), 1f); y += 16f } }
        7 -> for (k in 0 until 5) { val cx = w * (0.1f + k * 0.2f); val cy = h * 0.5f; val p = Path()
                for (t in 0..30) { val a = t / 30f * 2 * PI.toFloat() * 1.4f; val rr = h * 0.35f * (1 - t / 36f); val pt = Offset(cx + cos(a) * rr, cy + sin(a) * rr * 0.8f); if (t == 0) p.moveTo(pt.x, pt.y) else p.lineTo(pt.x, pt.y) }
                drawPath(p, if (k % 2 == 0) ink else ink2, style = Stroke(2f)) }
        9 -> for (k in 0 until 16) { val p = Path(); val y0 = h * k / 16f; for (x in 0..30) { val xx = w * x / 30f; val yy = y0 + sin(xx * 0.015f + k * 1.7f) * h * 0.05f; if (x == 0) p.moveTo(xx, yy) else p.lineTo(xx, yy) }; drawPath(p, ink, style = Stroke(1.2f)) }
        10 -> for (layer in 0 until 2) { val p = Path().apply { moveTo(0f, h) }; for (k in 0..8) p.lineTo(w * k / 8f, h * (0.45f + layer * 0.2f) + (if (k % 2 == 0) h * 0.2f else 0f)); p.lineTo(w, h); p.close(); drawPath(p, if (layer == 0) ink2 else ink) }
        11 -> rotate(clock * 4f, Offset(w * 0.9f, h * 0.5f)) { for (k in 0 until 18) { val a = k * 20f * PI.toFloat() / 180; drawLine(if (k % 2 == 0) ink else ink2, Offset(w * 0.9f, h * 0.5f), Offset(w * 0.9f + cos(a) * w, h * 0.5f + sin(a) * w), 5f) } }
    }
    drawRect(Brush.verticalGradient(listOf(Color(0x30FFFFFF), Color.Transparent), 0f, h * 0.45f))
}
