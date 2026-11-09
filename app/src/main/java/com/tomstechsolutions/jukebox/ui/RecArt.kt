package com.tomstechsolutions.jukebox.ui

import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t

/** Nút Thâu Âm: 16 kiểu riêng (0 = theo bộ nút đang chọn) và nhiều màu. Khi đang thâu, nút đổi thành nút dừng cùng kiểu. */
object RecArt {
    val names = listOf(
        "Same As Button Set" to "Theo Bộ Nút", "Classic Red Dot" to "Chấm Tròn Cổ Điển", "Ring And Dot" to "Vòng Viền Có Chấm",
        "Microphone" to "Micro", "Studio Mic" to "Micro Phòng Thu", "Cassette Reels" to "Cuộn Băng Cassette", "Vinyl" to "Đĩa Than",
        "Dot With Sound Waves" to "Chấm Có Sóng Âm", "REC Badge" to "Chữ REC", "Glowing Dot" to "Chấm Phát Sáng",
        "Rounded Square" to "Vuông Bo Góc", "Heart" to "Trái Tim", "Star" to "Ngôi Sao", "Pixel 8-bit" to "Pixel 8-bit",
        "On-Air Light" to "Đèn On Air", "Tape Recorder" to "Máy Ghi Âm",
    )
    fun name(i: Int) = names.getOrNull(i)?.let { t(it.first, it.second) } ?: ""

    val colours = listOf(
        Triple("red", "Red", "Đỏ") , Triple("orange", "Orange", "Cam"), Triple("pink", "Pink", "Hồng"), Triple("purple", "Purple", "Tím"),
        Triple("blue", "Blue", "Xanh Dương"), Triple("teal", "Teal", "Xanh Ngọc"), Triple("green", "Green", "Xanh Lá"), Triple("yellow", "Yellow", "Vàng"),
        Triple("white", "White", "Trắng"), Triple("cover", "From Cover", "Theo Ảnh Bìa"), Triple("theme", "Theme Colour", "Màu Giao Diện"), Triple("custom", "Custom", "Tự Chọn"),
    )
    fun colour(k: String = Prefs.recColour.value): Int = when (k) {
        "orange" -> 0xFFFF8F1F.toInt(); "pink" -> 0xFFFF4F9A.toInt(); "purple" -> 0xFFA855F7.toInt(); "blue" -> 0xFF3B82F6.toInt()
        "teal" -> 0xFF14B8A6.toInt(); "green" -> 0xFF22C55E.toInt(); "yellow" -> 0xFFFACC15.toInt(); "white" -> 0xFFFFFFFF.toInt()
        "cover" -> Core.palette.value[0]; "theme" -> Themes.now().accent.toArgb(); "custom" -> Prefs.recCustom.value
        else -> 0xFFFF3B3B.toInt()
    }

    /** Draws style [style] (1..15). [stop] = the recording is running, so show the stop sign. */
    fun draw(c: Canvas, stop: Boolean, design: Int, s: Float, col: Int, pressed: Boolean = false) {
        val p = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = col }
        val cx = s / 2; val cy = s / 2
        val k = if (pressed) 0.92f else 1f
        c.save(); c.scale(k, k, cx, cy)
        fun stopSquare(r: Float, colr: Int = 0xFFFFFFFF.toInt()) { val q = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = colr }; c.drawRoundRect(cx - r, cy - r, cx + r, cy + r, r * 0.25f, r * 0.25f, q) }
        fun stroke(w: Float) = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = col; style = Paint.Style.STROKE; strokeWidth = w; strokeCap = Paint.Cap.ROUND }
        when (design) {
            1 -> if (stop) stopSquare(s * 0.26f, col) else c.drawCircle(cx, cy, s * 0.32f, p)
            2 -> { c.drawCircle(cx, cy, s * 0.42f, stroke(s * 0.07f)); if (stop) stopSquare(s * 0.17f, col) else c.drawCircle(cx, cy, s * 0.24f, p) }
            3, 4 -> {                                                       // micro
                val w = if (design == 4) 0.26f else 0.2f
                c.drawRoundRect(cx - s * w / 2 * 1.0f, s * 0.12f, cx + s * w / 2, s * 0.58f, s * w / 2, s * w / 2, p)
                if (design == 4) { val g = stroke(s * 0.02f).apply { color = 0x66000000 }; for (i in 0..3) c.drawLine(cx - s * 0.1f, s * (0.2f + i * 0.08f), cx + s * 0.1f, s * (0.2f + i * 0.08f), g) }
                c.drawArc(RectF(cx - s * 0.28f, s * 0.22f, cx + s * 0.28f, s * 0.68f), 0f, 180f, false, stroke(s * 0.06f))
                c.drawLine(cx, s * 0.68f, cx, s * 0.84f, stroke(s * 0.06f)); c.drawLine(cx - s * 0.16f, s * 0.86f, cx + s * 0.16f, s * 0.86f, stroke(s * 0.06f))
                if (stop) { c.drawCircle(s * 0.8f, s * 0.2f, s * 0.15f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() }); stopSquare(0f); val q = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = col }
                    c.drawRect(s * 0.74f, s * 0.14f, s * 0.86f, s * 0.26f, q) }
            }
            5 -> {                                                          // cuộn băng cassette
                c.drawRoundRect(s * 0.06f, s * 0.22f, s * 0.94f, s * 0.78f, s * 0.08f, s * 0.08f, stroke(s * 0.05f))
                for (x in listOf(0.32f, 0.68f)) { c.drawCircle(s * x, cy, s * 0.13f, p); c.drawCircle(s * x, cy, s * 0.05f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF222222.toInt() }) }
                if (stop) stopSquare(s * 0.09f) else c.drawCircle(cx, s * 0.32f, s * 0.05f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() })
            }
            6 -> {                                                          // đĩa than
                c.drawCircle(cx, cy, s * 0.44f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF111111.toInt() })
                for (r in listOf(0.36f, 0.3f)) c.drawCircle(cx, cy, s * r, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0x33FFFFFF; style = Paint.Style.STROKE; strokeWidth = s * 0.01f })
                c.drawCircle(cx, cy, s * 0.18f, p)
                if (stop) stopSquare(s * 0.08f) else c.drawCircle(cx, cy, s * 0.04f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF111111.toInt() })
            }
            7 -> {                                                          // chấm có sóng âm
                if (stop) stopSquare(s * 0.16f, col) else c.drawCircle(cx, cy, s * 0.18f, p)
                for (i in 1..2) { val r = s * (0.24f + i * 0.1f); val st = stroke(s * 0.045f).apply { alpha = 255 - i * 70 }
                    c.drawArc(RectF(cx - r, cy - r, cx + r, cy + r), -40f, 80f, false, st); c.drawArc(RectF(cx - r, cy - r, cx + r, cy + r), 140f, 80f, false, st) }
            }
            8 -> {                                                          // chữ REC
                c.drawRoundRect(s * 0.04f, s * 0.28f, s * 0.96f, s * 0.72f, s * 0.1f, s * 0.1f, p)
                val tp = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt(); textSize = s * 0.24f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.CENTER }
                c.drawCircle(s * 0.2f, cy, s * 0.07f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() })
                c.drawText(if (stop) "STOP" else "REC", s * 0.58f, cy + s * 0.085f, tp)
            }
            9 -> {                                                          // chấm phát sáng
                val g = Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = android.graphics.RadialGradient(cx, cy, s * 0.48f, intArrayOf(col, col and 0x00FFFFFF), null, android.graphics.Shader.TileMode.CLAMP) }
                c.drawCircle(cx, cy, s * 0.48f, g); c.drawCircle(cx, cy, s * 0.24f, p)
                if (stop) stopSquare(s * 0.1f) else c.drawCircle(cx - s * 0.07f, cy - s * 0.07f, s * 0.06f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0x88FFFFFF.toInt() })
            }
            10 -> { c.drawRoundRect(s * 0.1f, s * 0.1f, s * 0.9f, s * 0.9f, s * 0.22f, s * 0.22f, p); if (stop) stopSquare(s * 0.16f) else c.drawCircle(cx, cy, s * 0.16f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() }) }
            11 -> {                                                         // trái tim
                val h = Path().apply { moveTo(cx, s * 0.82f); cubicTo(s * 0.02f, s * 0.48f, s * 0.2f, s * 0.08f, cx, s * 0.3f); cubicTo(s * 0.8f, s * 0.08f, s * 0.98f, s * 0.48f, cx, s * 0.82f); close() }
                c.drawPath(h, p); if (stop) stopSquare(s * 0.1f) else c.drawCircle(cx, s * 0.46f, s * 0.08f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() })
            }
            12 -> {                                                         // ngôi sao
                val st = Path(); for (i in 0 until 10) { val a = Math.PI * i / 5 - Math.PI / 2; val r = if (i % 2 == 0) s * 0.46f else s * 0.2f
                    val x = cx + (Math.cos(a) * r).toFloat(); val y = cy + (Math.sin(a) * r).toFloat(); if (i == 0) st.moveTo(x, y) else st.lineTo(x, y) }
                st.close(); c.drawPath(st, p); if (stop) stopSquare(s * 0.09f) else c.drawCircle(cx, cy + s * 0.02f, s * 0.07f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() })
            }
            13 -> {                                                         // pixel 8-bit
                val g = if (stop) listOf("........", "..####..", "..####..", "..####..", "..####..", "........") else listOf("..####..", ".######.", "########", "########", ".######.", "..####..")
                val u = s / 8; g.forEachIndexed { r, row -> row.forEachIndexed { cc, ch -> if (ch == '#') c.drawRect(cc * u, (r + 1) * u, (cc + 1) * u - 1, (r + 2) * u - 1, p) } }
            }
            14 -> {                                                         // đèn On Air
                c.drawRoundRect(s * 0.02f, s * 0.26f, s * 0.98f, s * 0.74f, s * 0.08f, s * 0.08f, if (stop) p else stroke(s * 0.05f))
                val tp = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = if (stop) 0xFFFFFFFF.toInt() else col; textSize = s * 0.2f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.CENTER }
                c.drawText("ON AIR", cx, cy + s * 0.07f, tp)
            }
            else -> {                                                       // máy ghi âm
                c.drawRoundRect(s * 0.14f, s * 0.08f, s * 0.86f, s * 0.92f, s * 0.12f, s * 0.12f, stroke(s * 0.05f))
                val g = stroke(s * 0.03f); for (i in 0..3) c.drawLine(s * 0.3f, s * (0.2f + i * 0.07f), s * 0.7f, s * (0.2f + i * 0.07f), g)
                if (stop) stopSquare(s * 0.12f, col) else c.drawCircle(cx, s * 0.66f, s * 0.14f, p)
            }
        }
        c.restore()
    }
}
