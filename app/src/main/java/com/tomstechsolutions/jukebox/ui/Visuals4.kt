package com.tomstechsolutions.jukebox.ui

import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import kotlin.math.exp
import kotlin.math.min
import kotlin.math.sin

/** Bảng màu rực rỡ nhiều sắc (hồng – tím – xanh – ngọc – cam) cho các sóng nhạc mới. */
val VIVID = listOf(Color(0xFFFF3B6B), Color(0xFFE040FB), Color(0xFF7C4DFF), Color(0xFF448AFF), Color(0xFF18FFFF), Color(0xFFFFAB40))

/** 6 sóng nhạc nhiều màu (70–75), mềm mại kiểu điện thoại đời mới – hình vẽ riêng của Tom's Jukebox. */
fun DrawScope.drawViz4(style: Int, time: Float, lv: FloatArray, cols: List<Color>) {
    val w = size.width; val h = size.height; val n = lv.size
    val pal = VIVID
    fun level(fx: Float, shift: Int): Float {                       // smooth level along x from the bands
        var a = 0f
        for (b in 0 until 5) { val c = (b * 0.21f + 0.08f + shift * 0.05f + time * 0.03f * (1 + shift % 3)) % 1.05f
            a += lv[(b * 4 + shift * 3) % n] * exp(-((fx - c) / 0.11f).let { it * it }) }
        return min(1f, a)
    }
    when (style) {
        70 -> for (li in 4 downTo 0) {                                                  // Sóng Lụa Đa Sắc
            val p = Path().apply { moveTo(0f, h) }
            for (k in 0..60) { val fx = k / 60f; val y = h * 0.92f - h * 0.75f * level(fx, li) * (0.6f + 0.4f * sin(fx * 3.1416f)); p.lineTo(fx * w, y) }
            p.lineTo(w, h); p.close()
            drawPath(p, Brush.horizontalGradient(listOf(pal[li].copy(alpha = 0.55f), pal[li + 1].copy(alpha = 0.45f))))
        }
        71 -> for (li in 0 until 5) {                                                    // Cực Quang Mềm
            for (k in 0..44) { val fx = k / 44f; val v = level(fx, li + 2)
                val top = h * (0.15f + 0.25f * sin(fx * 5f + time * 0.6f + li)) ; val len = h * (0.25f + 0.55f * v)
                drawLine(Brush.verticalGradient(listOf(pal[li].copy(alpha = 0f), pal[li].copy(alpha = 0.35f + 0.3f * v), pal[(li + 1) % 6].copy(alpha = 0f)), top, top + len),
                    Offset(fx * w, top), Offset(fx * w, top + len), w / 44f * 1.2f) }
        }
        72 -> {                                                                          // Sóng Đối Xứng Phát Sáng
            val mid = h / 2
            for (li in 0 until 4) {
                val up = Path(); val dn = Path()
                for (k in 0..80) { val fx = k / 80f; val a = h * 0.45f * level(fx, li) * sin(fx * 3.1416f); val x = fx * w
                    if (k == 0) { up.moveTo(x, mid - a); dn.moveTo(x, mid + a) } else { up.lineTo(x, mid - a); dn.lineTo(x, mid + a) } }
                val br = Brush.horizontalGradient(listOf(pal[li], pal[li + 1], pal[li + 2]))
                drawPath(up, br, alpha = 0.25f, style = Stroke(10f, cap = StrokeCap.Round)); drawPath(dn, br, alpha = 0.25f, style = Stroke(10f, cap = StrokeCap.Round))
                drawPath(up, br, style = Stroke(2.5f, cap = StrokeCap.Round)); drawPath(dn, br, style = Stroke(2.5f, cap = StrokeCap.Round))
            }
        }
        73 -> {                                                                          // Cột Bo Tròn Đa Sắc
            val bars = 28; val bw = w / bars
            for (k in 0 until bars) { val v = lv[k % n].coerceIn(0.04f, 1f); val bh = h * 0.9f * v; val x = k * bw + bw * 0.18f
                drawRoundRect(Brush.verticalGradient(listOf(pal[(k / 5) % 6], pal[(k / 5 + 1) % 6], pal[(k / 5 + 2) % 6]), h / 2 - bh / 2, h / 2 + bh / 2),
                    Offset(x, h / 2 - bh / 2), Size(bw * 0.64f, bh), CornerRadius(bw * 0.32f)) }
        }
        74 -> for (k in 0 until 18) {                                                    // Giọt Màu Nhảy
            val fx = (k + 0.5f) / 18f; val v = lv[(k * 4) % n]; val bounce = kotlin.math.abs(sin(time * 2.2f + k * 0.7f))
            val r = min(w / 18f, h) * (0.18f + 0.3f * v); val y = h * 0.85f - (h * 0.6f) * v * bounce
            val c = pal[k % 6]
            drawCircle(Brush.radialGradient(listOf(c.copy(alpha = 0.6f), Color.Transparent), Offset(fx * w, y), r * 2.6f), r * 2.6f, Offset(fx * w, y))
            drawCircle(c, r, Offset(fx * w, y))
        }
        else -> for (li in 0 until 6) {                                                  // Dòng Chảy Neon
            val p = Path()
            for (k in 0..90) { val fx = k / 90f; val y = h / 2 + sin(fx * (6f + li) + time * (1.2f + li * 0.25f)) * h * 0.38f * (0.2f + level(fx, li))
                if (k == 0) p.moveTo(fx * w, y) else p.lineTo(fx * w, y) }
            drawPath(p, pal[li], alpha = 0.22f, style = Stroke(9f, cap = StrokeCap.Round))
            drawPath(p, pal[li], style = Stroke(2.2f, cap = StrokeCap.Round))
        }
    }
    @Suppress("UNUSED_VARIABLE") val unused = cols
}
