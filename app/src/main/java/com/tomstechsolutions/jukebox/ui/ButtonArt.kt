package com.tomstechsolutions.jukebox.ui

import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RadialGradient
import android.graphics.RectF
import android.graphics.Shader
import com.tomstechsolutions.jukebox.t
import kotlin.math.sin

/** The 13 button sets (Tom's Dock + 12). Drawn on an Android Canvas so the app, lock screen and widgets match. */
object ButtonArt {
    const val PLAY = 0; const val PAUSE = 1; const val PREV = 2; const val NEXT = 3; const val REC = 4; const val REC_STOP = 5

    val names = listOf(
        "Tom's Dock" to "Tom's Dock", "Thin Line" to "Nét Mảnh", "Solid Circle" to "Tròn Đặc", "Ring" to "Vòng Viền",
        "Rounded Square" to "Vuông Bo Góc", "Double Arrows" to "Mũi Tên Đôi", "Neon" to "Neon", "Glass Bubble" to "Kính Bong Bóng",
        "3D Metal" to "Kim Loại 3D", "Cassette Keys" to "Phím Cassette", "Hand Drawn" to "Vẽ Tay", "Pixel 8-bit" to "Pixel 8-bit",
        "Chubby" to "Bo Tròn Mập",
    )
    fun name(i: Int) = names.getOrNull(i)?.let { t(it.first, it.second) } ?: ""

    private fun glyph(kind: Int, style: Int, x: Float, y: Float, s: Float): Path {
        val p = Path()
        fun pt(px: Float, py: Float) = floatArrayOf(x + px * s, y + py * s)
        fun tri(a: FloatArray, b: FloatArray, c: FloatArray) { p.moveTo(a[0], a[1]); p.lineTo(b[0], b[1]); p.lineTo(c[0], c[1]); p.close() }
        fun rect(l: Float, tp: Float, r: Float, b: Float) { p.addRoundRect(RectF(x + l * s, y + tp * s, x + r * s, y + b * s), s * 0.04f, s * 0.04f, Path.Direction.CW) }
        when (kind) {
            PLAY -> tri(pt(0.3f, 0.2f), pt(0.84f, 0.5f), pt(0.3f, 0.8f))
            PAUSE -> { rect(0.26f, 0.2f, 0.42f, 0.8f); rect(0.58f, 0.2f, 0.74f, 0.8f) }
            PREV -> if (style == 5) { tri(pt(0.52f, 0.24f), pt(0.14f, 0.5f), pt(0.52f, 0.76f)); tri(pt(0.88f, 0.24f), pt(0.5f, 0.5f), pt(0.88f, 0.76f)) }
                    else { rect(0.18f, 0.22f, 0.29f, 0.78f); tri(pt(0.8f, 0.22f), pt(0.34f, 0.5f), pt(0.8f, 0.78f)) }
            NEXT -> if (style == 5) { tri(pt(0.48f, 0.24f), pt(0.86f, 0.5f), pt(0.48f, 0.76f)); tri(pt(0.12f, 0.24f), pt(0.5f, 0.5f), pt(0.12f, 0.76f)) }
                    else { rect(0.71f, 0.22f, 0.82f, 0.78f); tri(pt(0.2f, 0.22f), pt(0.66f, 0.5f), pt(0.2f, 0.78f)) }
            REC -> p.addCircle(x + 0.5f * s, y + 0.5f * s, 0.27f * s, Path.Direction.CW)
            else -> rect(0.3f, 0.3f, 0.7f, 0.7f)
        }
        return p
    }

    // 8x8 pixel glyphs
    private val pixels = mapOf(
        PLAY to listOf("..#.....", "..##....", "..###...", "..####..", "..####..", "..###...", "..##....", "..#....."),
        PAUSE to listOf("........", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", "........"),
        PREV to listOf("........", ".#...##.", ".#..###.", ".#.####.", ".#.####.", ".#..###.", ".#...##.", "........"),
        NEXT to listOf("........", ".##...#.", ".###..#.", ".####.#.", ".####.#.", ".###..#.", ".##...#.", "........"),
        REC to listOf("........", "..####..", ".######.", ".######.", ".######.", ".######.", "..####..", "........"),
        REC_STOP to listOf("........", "........", "..####..", "..####..", "..####..", "..####..", "........", "........"),
    )

    fun draw(c: Canvas, kind: Int, style: Int, size: Float, color: Int, pressed: Boolean = false, glow: Float = 0f) {
        val pc = Paint(Paint.ANTI_ALIAS_FLAG)
        val col = if (kind == REC || kind == REC_STOP) 0xFFFF4D4D.toInt() else color
        val cx = size / 2; val cy = size / 2
        val dark = 0xFF1B1F24.toInt()
        val inner = size * 0.58f; val ix = (size - inner) / 2
        fun fillGlyph(g: Path, k: Int, paintCol: Int, round: Float = 0.05f) {
            pc.reset(); pc.isAntiAlias = true; pc.color = paintCol; pc.style = Paint.Style.FILL_AND_STROKE
            pc.strokeJoin = Paint.Join.ROUND; pc.strokeWidth = size * round; c.drawPath(g, pc)
        }
        when (style) {
            1 -> { pc.color = col; pc.style = Paint.Style.STROKE; pc.strokeWidth = size * 0.045f; pc.strokeJoin = Paint.Join.ROUND
                   c.drawPath(glyph(kind, style, size * 0.12f, size * 0.12f, size * 0.76f), pc) }
            2 -> { pc.color = col; c.drawCircle(cx, cy, size * 0.47f, pc); fillGlyph(glyph(kind, style, ix, ix, inner), kind, if (kind >= REC) 0xFFFFFFFF.toInt() else dark) }
            3 -> { pc.color = col; pc.style = Paint.Style.STROKE; pc.strokeWidth = size * 0.05f; c.drawCircle(cx, cy, size * 0.44f, pc)
                   fillGlyph(glyph(kind, style, ix, ix, inner), kind, col) }
            4 -> { pc.color = (col and 0x00FFFFFF) or 0x33000000; c.drawRoundRect(RectF(size * 0.04f, size * 0.04f, size * 0.96f, size * 0.96f), size * 0.24f, size * 0.24f, pc)
                   fillGlyph(glyph(kind, style, ix, ix, inner), kind, col) }
            6 -> { val g = glyph(kind, style, size * 0.14f, size * 0.14f, size * 0.72f)
                   val a = (0.35f + glow * 0.5f).coerceIn(0f, 1f)
                   for ((w, al) in listOf(0.22f to 0.12f * a, 0.14f to 0.25f * a, 0.07f to 0.6f)) {
                       pc.reset(); pc.isAntiAlias = true; pc.style = Paint.Style.STROKE; pc.strokeJoin = Paint.Join.ROUND
                       pc.strokeWidth = size * w; pc.color = col; pc.alpha = (al * 255).toInt(); c.drawPath(g, pc)
                   }
                   pc.strokeWidth = size * 0.025f; pc.color = 0xFFFFFFFF.toInt(); pc.alpha = 230; c.drawPath(g, pc) }
            7 -> { pc.shader = RadialGradient(cx * 0.8f, cy * 0.7f, size * 0.6f, intArrayOf(0x66FFFFFF, 0x22FFFFFF, 0x10FFFFFF), null, Shader.TileMode.CLAMP)
                   c.drawCircle(cx, cy, size * 0.46f, pc); pc.shader = null
                   pc.style = Paint.Style.STROKE; pc.strokeWidth = size * 0.02f; pc.color = 0x88FFFFFF.toInt(); c.drawCircle(cx, cy, size * 0.46f, pc)
                   pc.style = Paint.Style.FILL; pc.color = 0x55FFFFFF; c.drawOval(RectF(size * 0.26f, size * 0.1f, size * 0.66f, size * 0.3f), pc)
                   fillGlyph(glyph(kind, style, ix, ix, inner), kind, col) }
            8 -> { pc.shader = LinearGradient(0f, 0f, 0f, size, intArrayOf(0xFFF2F4F7.toInt(), 0xFFA9B0B8.toInt(), 0xFF6E757D.toInt()), null, Shader.TileMode.CLAMP)
                   c.drawCircle(cx, cy, size * 0.47f, pc)
                   pc.shader = LinearGradient(0f, 0f, 0f, size, intArrayOf(0xFF8C939B.toInt(), 0xFFE6E9ED.toInt()), null, Shader.TileMode.CLAMP)
                   c.drawCircle(cx, cy, size * 0.39f, pc); pc.shader = null
                   fillGlyph(glyph(kind, style, ix, ix, inner), kind, if (kind >= REC) 0xFFD93030.toInt() else 0xFF2E3338.toInt()) }
            9 -> { val dy = if (pressed) size * 0.05f else 0f
                   pc.color = 0xFF2A2A2A.toInt(); c.drawRoundRect(RectF(size * 0.06f, size * 0.14f, size * 0.94f, size * 0.92f), size * 0.08f, size * 0.08f, pc)
                   pc.shader = LinearGradient(0f, size * 0.1f, 0f, size * 0.85f, intArrayOf(0xFFF4F1EA.toInt(), 0xFFCFC8BA.toInt()), null, Shader.TileMode.CLAMP)
                   c.drawRoundRect(RectF(size * 0.08f, size * 0.08f + dy, size * 0.92f, size * 0.84f + dy), size * 0.07f, size * 0.07f, pc); pc.shader = null
                   fillGlyph(glyph(kind, style, size * 0.25f, size * 0.21f + dy, size * 0.5f), kind, if (kind >= REC) 0xFFD93030.toInt() else 0xFF2B2B2B.toInt()) }
            10 -> { val g = glyph(kind, style, size * 0.12f, size * 0.12f, size * 0.76f)
                    val m = android.graphics.PathMeasure(g, true); val out = Path()
                    do {
                        val len = m.length; var d = 0f; var first = true
                        while (d <= len) {
                            val pos = FloatArray(2); m.getPosTan(d, pos, null)
                            val j = sin(d * 0.9f + pos[0] * 0.3f) * size * 0.018f
                            if (first) { out.moveTo(pos[0] + j, pos[1] - j); first = false } else out.lineTo(pos[0] + j, pos[1] - j)
                            d += size * 0.03f
                        }
                        out.close()
                    } while (m.nextContour())
                    pc.color = col; pc.style = Paint.Style.STROKE; pc.strokeWidth = size * 0.06f; pc.strokeCap = Paint.Cap.ROUND; pc.strokeJoin = Paint.Join.ROUND
                    c.drawPath(out, pc) }
            11 -> { val rows = pixels[kind] ?: return; val cell = size / 8f; pc.color = col
                    rows.forEachIndexed { r, line -> line.forEachIndexed { k, ch -> if (ch == '#') c.drawRect(k * cell, r * cell, (k + 1) * cell - 1, (r + 1) * cell - 1, pc) } } }
            12 -> fillGlyph(glyph(kind, style, size * 0.16f, size * 0.16f, size * 0.68f), kind, col, 0.16f)
            else -> fillGlyph(glyph(kind, style, size * 0.1f, size * 0.1f, size * 0.8f), kind, col)
        }
    }

    /** For widgets (RemoteViews). */
    fun bitmap(kind: Int, style: Int, px: Int, color: Int): android.graphics.Bitmap {
        val b = android.graphics.Bitmap.createBitmap(px, px, android.graphics.Bitmap.Config.ARGB_8888)
        draw(Canvas(b), kind, style, px.toFloat(), color)
        return b
    }
}
