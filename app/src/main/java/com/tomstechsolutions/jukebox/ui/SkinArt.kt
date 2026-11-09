package com.tomstechsolutions.jukebox.ui

import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

data class SkinStyle(val text: Color, val sub: Color, val btn: Color, val border: Color, val radius: Dp?, val waves: Boolean = true)

/** Colours cycled by double-tapping the pill (skins Viên Thuốc and Siêu Gọn). */
object PillColours {
    val list = listOf(
        Triple("Warm Brown", "Nâu Ấm", listOf(0xFF3A3330, 0xFF1F1B19)), Triple("From Album Cover", "Theo Ảnh Bìa", listOf(0L, 0L)),
        Triple("Jet Black", "Đen Tuyền", listOf(0xFF1C1C1C, 0xFF050505)), Triple("Navy", "Xanh Navy", listOf(0xFF1E4A63, 0xFF0D2C40)),
        Triple("Plum", "Tím Than", listOf(0xFF3B2A63, 0xFF1C1236)), Triple("Wine Red", "Đỏ Rượu Vang", listOf(0xFF5A1A2A, 0xFF2A0A12)),
        Triple("Moss Green", "Xanh Rêu", listOf(0xFF2F4A2A, 0xFF15241A)), Triple("Night Sea", "Xanh Biển Đêm", listOf(0xFF123B5A, 0xFF061A2C)),
        Triple("Peach", "Hồng Đào", listOf(0xFFB5536F, 0xFF6E2A3E)), Triple("Desert Sand", "Vàng Cát", listOf(0xFF8A6A3A, 0xFF4A3618)),
        Triple("Silver Grey", "Xám Bạc", listOf(0xFF6B7178, 0xFF3A3F45)), Triple("See-Through", "Trong Suốt", listOf(0x26FFFFFFL, 0x14FFFFFFL)),
    )
    fun name(i: Int) = list.getOrNull(i)?.let { t(it.first, it.second) } ?: ""
    fun colours(i: Int): List<Color> {
        val e = list.getOrNull(i) ?: list[0]
        if (i == 1) { val c = Color(Core.palette.value[0]); return listOf(c.darken(0.55f), c.darken(0.25f)) }
        return e.third.map { Color(it.toInt()) }
    }
}

fun Color.darken(k: Float) = Color(red * k, green * k, blue * k, alpha)

object SkinList {
    val keys = listOf("pill", "xp", "metal", "wood", "glass", "slim", "ipod", "liquid", "grain", "marble", "clear", "lacquer",
        "ceramic", "carbon", "leather", "alu", "gold", "neon", "cassette", "tinted")
    val woodTypes = listOf("Walnut" to "Óc Chó", "Oak" to "Sồi", "Mahogany" to "Gụ")
    val marbleTypes = listOf("White" to "Trắng Vân Xám", "Black Gold" to "Đen Vân Vàng", "Jade" to "Xanh Ngọc")
    fun name(k: String) = when (k) {
        "pill" -> t("Pill (Tom's Dock)", "Viên Thuốc (Tom's Dock)"); "xp" -> t("XP Classic", "XP Cổ Điển"); "metal" -> t("Classic Metal", "Cổ Điển Kim Loại")
        "wood" -> t("Wooden Amplifier", "Ampli Gỗ"); "glass" -> t("Frosted Glass", "Kính Mờ"); "slim" -> t("Ultra Slim", "Siêu Gọn")
        "ipod" -> t("Classic iPod Style", "iPod Cổ Điển"); "liquid" -> t("Liquid Glass", "Kính Lỏng"); "grain" -> t("Wood Grain", "Vân Gỗ")
        "marble" -> t("Marble", "Cẩm Thạch"); "clear" -> t("Transparent", "Trong Suốt"); "lacquer" -> t("Lacquer", "Sơn Mài")
        "ceramic" -> t("Blue Ceramic", "Gốm Men Lam"); "carbon" -> t("Carbon Fibre", "Sợi Carbon"); "leather" -> t("Leather", "Da Thuộc")
        "alu" -> t("Brushed Aluminium", "Nhôm Xước"); "gold" -> t("Gold", "Vàng Gold"); "neon" -> t("Night Neon", "Neon Đêm")
        "cassette" -> t("Cassette", "Băng Cassette"); "tinted" -> t("Tinted Glass", "Kính Mờ Màu"); else -> k
    }
}

private val W = Color.White
private val SUBW = Color(0xFFE8DCD0)
private val INK = Color(0xFF1E2333)
private val INKSUB = Color(0xFF4A5068)

fun skinStyle(key: String = Prefs.skin.value): SkinStyle = Motifs.skinMotif(key)?.let { motifSkinStyle(it) } ?: when (key) {
    "xp" -> when (Prefs.xpColour.value) {
        "silver" -> SkinStyle(INK, INKSUB, Color(0xFF2B3550), Color(0xFF8D90A6), 18.dp)
        "olive" -> SkinStyle(W, Color(0xFFF1F6E2), W, Color(0xFF3F5424), 18.dp)
        else -> SkinStyle(W, Color(0xFFDCE8FF), W, Color(0xFF0B2F7A), 18.dp)
    }
    "metal" -> SkinStyle(W, Color(0xFFE6EAEE), W, Color(0xFF2A2F35), 14.dp)
    "wood" -> SkinStyle(Color(0xFFFCE9C8), Color(0xFFE2C79A), Color(0xFFFCE9C8), Color(0xFF2A190B), 16.dp)
    "glass" -> SkinStyle(W, Color(0xFFE6F2F7), W, Color(0x66FFFFFF), null)
    "ipod" -> SkinStyle(Color(0xFF111111), Color(0xFF555555), Color(0xFF222222), Color(0xFFB8BCC2), 22.dp, waves = false)
    "liquid" -> SkinStyle(W, Color(0xFFEFF6FA), W, Color(0x99FFFFFF), null)
    "grain" -> if (Prefs.woodType.value == 1) SkinStyle(Color(0xFF2A1A08), Color(0xFF5A3E1E), Color(0xFF2A1A08), Color(0xFF7A5A30), 18.dp)
               else SkinStyle(Color(0xFFFCEFD8), Color(0xFFE8CFA8), Color(0xFFFCEFD8), Color(0xFF2A160A), 18.dp)
    "marble" -> if (Prefs.marbleType.value == 0) SkinStyle(INK, INKSUB, Color(0xFF2A2F3A), Color(0xFFBFC3C8), 20.dp)
                else SkinStyle(W, Color(0xFFEDE6D2), W, if (Prefs.marbleType.value == 1) Color(0xFFC9A227) else Color(0xFF0E3B30), 20.dp)
    "clear" -> SkinStyle(W, Color(0xFFF2F2F2), W, Color(0x66FFFFFF), null)
    "lacquer" -> SkinStyle(Color(0xFFF7E3A1), Color(0xFFD9BE76), Color(0xFFF7E3A1), Color(0xFFC9A227), 18.dp)
    "ceramic" -> SkinStyle(Color(0xFF15346E), Color(0xFF3B5A94), Color(0xFF15346E), Color(0xFF1F4FA0), 22.dp, waves = false)
    "carbon" -> SkinStyle(W, Color(0xFFCDD3D8), W, Color(0xFF3A3F45), 16.dp)
    "leather" -> SkinStyle(Color(0xFFF6E7D2), Color(0xFFE2C8A6), Color(0xFFF6E7D2), Color(0xFF2A160A), 20.dp)
    "alu" -> SkinStyle(INK, INKSUB, Color(0xFF2B3036), Color(0xFF7F868E), 14.dp)
    "gold" -> SkinStyle(Color(0xFF3A2A05), Color(0xFF5E4710), Color(0xFF3A2A05), Color(0xFF9C7A1E), 20.dp, waves = false)
    "neon" -> SkinStyle(W, Color(0xFFFFC7EC), Color(0xFF7DF9FF), Color(0xFFFF3DCB), null)
    "cassette" -> SkinStyle(Color(0xFFF2E6C8), Color(0xFFCBBF9F), Color(0xFFF2E6C8), Color(0xFF111111), 12.dp)
    "tinted" -> SkinStyle(W, Color(0xFFF0F0F0), W, Color(0x66FFFFFF), null)
    else -> SkinStyle(W, SUBW, W, Color(0x30FFFFFF), null)
}

/** Paints the pill background for the chosen skin. */
fun DrawScope.paintSkin(clock: Float, tilt: Float, key: String = Prefs.skin.value) {
    val w = size.width; val h = size.height
    fun vg(vararg c: Long) = drawRect(Brush.verticalGradient(c.map { Color(it) }))
    Motifs.skinMotif(key)?.let { paintMotifSkin(it, clock); return }
    when (key) {
        "xp" -> {
            when (Prefs.xpColour.value) { "silver" -> vg(0xFFF6F6FA, 0xFFDADBE5, 0xFFB4B6C6); "olive" -> vg(0xFFC9D8A0, 0xFF93A867, 0xFF5B7638); else -> vg(0xFF4A8BF0, 0xFF2159CC, 0xFF0F3C9E) }
            drawRoundRect(Brush.verticalGradient(listOf(Color(0x66FFFFFF), Color(0x10FFFFFF)), 0f, h / 2), Offset(6f, 3f), Size(w - 12f, h / 2 - 3f), CornerRadius(h / 3))
        }
        "metal" -> { vg(0xFFA5ADB7, 0xFF656D78, 0xFF3A4048, 0xFF727A85); for (y in 0 until h.toInt() step 3) drawLine(Color(0x0FFFFFFF), Offset(0f, y.toFloat()), Offset(w, y.toFloat())) }
        "wood" -> vg(0xFF8B5A2B, 0xFF5C3A1A, 0xFF3E2612)
        "glass" -> vg(0x33FFFFFF, 0x1AFFFFFF)
        "ipod" -> vg(0xFFFAFAFA, 0xFFE1E3E7)
        "liquid" -> {
            vg(0x2EFFFFFF, 0x14FFFFFF, 0x24FFFFFF)
            drawRect(Brush.verticalGradient(listOf(Color(0x55FFFFFF), Color.Transparent), 0f, h * 0.45f))
            val x = ((tilt * 0.5f + 0.5f) * w + sin(clock * 0.4f) * w * 0.05f)
            drawRect(Brush.horizontalGradient(listOf(Color.Transparent, Color(0x40FFFFFF), Color.Transparent), x - w * 0.15f, x + w * 0.15f))
        }
        "grain" -> {
            val base = listOf(listOf(0xFF6B4226, 0xFF3E2414), listOf(0xFFD9B27C, 0xFFAC8452), listOf(0xFF8A3624, 0xFF4E1A10))[Prefs.woodType.value.coerceIn(0, 2)]
            drawRect(Brush.verticalGradient(base.map { Color(it) }))
            val line = if (Prefs.woodType.value == 1) Color(0x26603A10) else Color(0x33000000)
            for (i in 0 until 26) {
                val p = Path(); val y0 = h * i / 26f
                for (k in 0..40) { val x = w * k / 40f; val y = y0 + sin(x * 0.012f + i * 1.7f) * h * 0.04f + sin(x * 0.045f + i) * h * 0.01f; if (k == 0) p.moveTo(x, y) else p.lineTo(x, y) }
                drawPath(p, line, style = Stroke(1.2f + (i % 3)))
            }
            drawRoundRect(Brush.verticalGradient(listOf(Color(0x33FFFFFF), Color.Transparent), 0f, h * 0.4f), cornerRadius = CornerRadius(h / 3))
        }
        "marble" -> {
            val m = Prefs.marbleType.value.coerceIn(0, 2)
            drawRect(Brush.linearGradient(listOf(listOf(0xFFF4F2EE, 0xFFE2DFD9), listOf(0xFF1A1A1A, 0xFF0B0B0B), listOf(0xFF1F6B5A, 0xFF0F3F35))[m].map { Color(it) }))
            val vein = listOf(Color(0x4D7A7E86), Color(0x99C9A227), Color(0x66E8F5EF))[m]
            val r = Random(7)
            repeat(7) {
                val p = Path(); var x = r.nextFloat() * w * 0.2f; var y = r.nextFloat() * h
                p.moveTo(x, y)
                repeat(6) { val nx = x + w * (0.12f + r.nextFloat() * 0.15f); val ny = (y + (r.nextFloat() - 0.5f) * h * 0.8f).coerceIn(0f, h); p.quadraticTo((x + nx) / 2, y + (r.nextFloat() - 0.5f) * h, nx, ny); x = nx; y = ny }
                drawPath(p, vein, style = Stroke(0.8f + r.nextFloat() * 2.2f))
            }
            drawRect(Brush.verticalGradient(listOf(Color(0x30FFFFFF), Color.Transparent), 0f, h * 0.5f))
        }
        "clear" -> vg(0x0DFFFFFF, 0x08FFFFFF)
        "lacquer" -> {
            vg(0xFF1A0F08, 0xFF0B0B0B, 0xFF150A05)
            drawRect(Brush.verticalGradient(listOf(Color(0x30FFFFFF), Color.Transparent), 0f, h * 0.35f))
            val gold = Color(0xAAC9A227)
            for (k in 0 until 3) drawArc(gold, 180f + k * 25f, 70f, false, Offset(w - h * (1.1f + k * 0.25f), -h * 0.3f), Size(h * 1.2f, h * 1.2f), style = Stroke(1.5f))
        }
        "ceramic" -> {
            vg(0xFFF8F4EA, 0xFFEDE6D6)
            val blue = Color(0xFF1F4FA0)
            drawRoundRect(blue, Offset(5f, 5f), Size(w - 10f, h - 10f), CornerRadius(h / 4), style = Stroke(2f))
            var x = 18f
            while (x < w - 18f) { drawCircle(blue.copy(alpha = 0.55f), 3f, Offset(x, 11f)); drawCircle(blue.copy(alpha = 0.55f), 3f, Offset(x, h - 11f)); x += 16f }
            for (i in 0 until 3) { val p = Path(); for (k in 0..30) { val xx = w * k / 30f; val yy = h * (0.35f + i * 0.15f) + sin(xx * 0.05f + i) * 4f; if (k == 0) p.moveTo(xx, yy) else p.lineTo(xx, yy) }; drawPath(p, blue.copy(alpha = 0.12f), style = Stroke(2f)) }
        }
        "carbon" -> {
            vg(0xFF26282B, 0xFF141516)
            val c = 8.dp.toPx(); var y = 0f; var row = 0
            while (y < h) { var x = if (row % 2 == 0) 0f else c / 2; while (x < w) { drawRect(Brush.linearGradient(listOf(Color(0x22FFFFFF), Color(0x05FFFFFF)), Offset(x, y), Offset(x + c / 2, y + c / 2)), Offset(x, y), Size(c / 2, c / 2)); x += c }; y += c / 2; row++ }
            drawRect(Brush.verticalGradient(listOf(Color(0x22FFFFFF), Color.Transparent), 0f, h * 0.4f))
        }
        "leather" -> {
            vg(0xFF7A4A2A, 0xFF4A2A16)
            val r = Random(3); repeat(500) { drawCircle(Color.Black.copy(alpha = 0.07f), 0.8f + r.nextFloat() * 1.4f, Offset(r.nextFloat() * w, r.nextFloat() * h)) }
            drawRoundRect(Color(0xB3E8C79A), Offset(7f, 7f), Size(w - 14f, h - 14f), CornerRadius(h / 3), style = Stroke(1.6f, pathEffect = PathEffect.dashPathEffect(floatArrayOf(9f, 6f))))
        }
        "alu" -> { vg(0xFFD6DADF, 0xFFA8AEB5, 0xFFC4C9CE); val r = Random(5); for (y in 0 until h.toInt() step 2) drawLine(Color.White.copy(alpha = r.nextFloat() * 0.18f), Offset(0f, y.toFloat()), Offset(w, y.toFloat())) }
        "gold" -> { drawRect(Brush.linearGradient(listOf(Color(0xFFF7E08A), Color(0xFFD4AF37), Color(0xFFA67C1F), Color(0xFFF3D77A)), Offset.Zero, Offset(w, h)))
                    drawRect(Brush.verticalGradient(listOf(Color(0x55FFFFFF), Color.Transparent), 0f, h * 0.45f)) }
        "neon" -> vg(0xFF0E0A1A, 0xFF05030C)
        "cassette" -> {
            vg(0xFF2E2E2E, 0xFF161616)
            drawRect(Color(0xFFF2E6C8).copy(alpha = 0.12f), Offset(0f, h * 0.06f), Size(w, h * 0.1f))
            val spin = if (Core.playing.value) clock * 120f else 0f
            for (cx in listOf(w * 0.08f, w * 0.92f)) {
                val c = Offset(cx, h * 0.5f); val rr = h * 0.32f
                drawCircle(Color(0x33FFFFFF), rr, c, style = Stroke(2f)); drawCircle(Color(0x22FFFFFF), rr * 0.35f, c)
                rotate(spin, c) { for (k in 0 until 6) { val a = Math.toRadians(k * 60.0).toFloat(); drawLine(Color(0x44FFFFFF), c, Offset(c.x + cos(a) * rr * 0.8f, c.y + sin(a) * rr * 0.8f), 2f) } }
            }
        }
        "tinted" -> { val c = Color(Core.palette.value[0]); drawRect(Brush.verticalGradient(listOf(c.copy(alpha = 0.45f), c.darken(0.4f).copy(alpha = 0.55f)))) }
        else -> drawRect(Brush.verticalGradient(PillColours.colours(Prefs.pillColour.value)))
    }
}

/** The skin's outline (neon glows). */
fun DrawScope.paintSkinBorder(radiusPx: Float, border: Color, key: String = Prefs.skin.value) {
    if (key == "neon") {
        for ((wd, a) in listOf(10f to 0.15f, 5f to 0.35f, 2f to 1f)) {
            drawRoundRect(Brush.horizontalGradient(listOf(Color(0xFFFF3DCB), Color(0xFF7DF9FF))), Offset(2f, 2f), Size(size.width - 4f, size.height - 4f), CornerRadius(radiusPx), alpha = a, style = Stroke(wd))
        }
    } else if (key == "lacquer" || key == "gold" || Motifs.skinMotif(key) != null) {
        drawRoundRect(border, Offset(1.5f, 1.5f), Size(size.width - 3f, size.height - 3f), CornerRadius(radiusPx), style = Stroke(3f))
    } else drawRoundRect(border, Offset(0.5f, 0.5f), Size(size.width - 1f, size.height - 1f), CornerRadius(radiusPx), style = Stroke(1.2f))
}
