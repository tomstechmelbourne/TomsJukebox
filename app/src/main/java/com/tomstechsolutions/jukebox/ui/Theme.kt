package com.tomstechsolutions.jukebox.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t

val NAVY = Color(0xFF0D2C40)
val NAVY_D = Color(0xFF071A26)
val NAVY_L = Color(0xFF1E4A63)
val TEAL = Color(0xFF0E88AA)
val SKY = Color(0xFF48B0C8)
val ORANGE = Color(0xFFFBB040)
val ON_ORANGE = Color(0xFF2A1A00)
val SPLASH_TEXT = Color(0xFFCFE6EE)

data class JTheme(
    val key: String, val en: String, val vi: String,
    val top: Color, val bottom: Color, val card: Color, val text: Color, val muted: Color,
    val accent: Color, val onAccent: Color, val nav: Color, val light: Boolean = false,
) {
    val name get() = t(en, vi)
    val bg get() = Brush.verticalGradient(listOf(top, bottom))
}

/** 11 colour themes (High Contrast removed on Tom's request) + one custom colour. */
object Themes {
    val list = listOf(
        JTheme("toms", "Tom's Technology Solutions", "Tom's Technology Solutions", NAVY, NAVY_D, Color(0x1FFFFFFF), Color.White, Color(0xFF9FC3D3), ORANGE, ON_ORANGE, Color(0xFF06141E)),
        JTheme("dark", "Dark", "Tối", Color(0xFF1A1A1C), Color(0xFF000000), Color(0x1AFFFFFF), Color.White, Color(0xFFA8A8AE), ORANGE, ON_ORANGE, Color(0xFF0B0B0C)),
        JTheme("soft", "Soft", "Mềm Mại", Color(0xFFF4F8FA), Color(0xFFE6EEF2), Color(0xFFFFFFFF), Color(0xFF0F2A38), Color(0xFF4F6B79), TEAL, Color.White, Color(0xFFFFFFFF), true),
        JTheme("frosted", "Frosted Glass", "Kính Mờ", Color(0xFF203A4C), Color(0xFF0E1C26), Color(0x26FFFFFF), Color.White, Color(0xFFBFD8E3), SKY, NAVY_D, Color(0x99101C24)),
        JTheme("ocean", "Ocean", "Đại Dương", Color(0xFF0B3954), Color(0xFF04151F), Color(0x1FFFFFFF), Color.White, Color(0xFF9CC9D6), Color(0xFF2BC4C4), Color(0xFF00211F), Color(0xFF03111A)),
        JTheme("sunset", "Sunset", "Hoàng Hôn", Color(0xFF4A2335), Color(0xFF160A10), Color(0x1FFFFFFF), Color.White, Color(0xFFE2B5C2), Color(0xFFFB7185), Color(0xFF2A0710), Color(0xFF12080C)),
        JTheme("forest", "Forest", "Rừng Xanh", Color(0xFF12352B), Color(0xFF06140F), Color(0x1FFFFFFF), Color.White, Color(0xFFA6D5C3), Color(0xFF7EE3C1), Color(0xFF032016), Color(0xFF04100C)),
        JTheme("peach", "Peach", "Hồng Đào", Color(0xFFFFF1F2), Color(0xFFFCE4EA), Color(0xFFFFFFFF), Color(0xFF3B1622), Color(0xFF7A4E5B), Color(0xFFE0558F), Color.White, Color(0xFFFFFFFF), true),
        JTheme("plum", "Plum", "Tím Than", Color(0xFF2A1E4A), Color(0xFF0F0A1E), Color(0x1FFFFFFF), Color.White, Color(0xFFC3B6E8), Color(0xFFA78BFA), Color(0xFF16093A), Color(0xFF0C0818)),
        JTheme("coffee", "Coffee", "Cà Phê", Color(0xFF3B2A20), Color(0xFF140D09), Color(0x1FFFFFFF), Color.White, Color(0xFFD9C0A8), Color(0xFFE0A96D), Color(0xFF2A1503), Color(0xFF100A07)),
        JTheme("graphite", "Graphite", "Than Chì", Color(0xFF2B2F33), Color(0xFF121416), Color(0x1FFFFFFF), Color.White, Color(0xFFB4BCC4), Color(0xFFC9D1D9), Color(0xFF15191D), Color(0xFF0D0F11)),
    )

    @Composable
    fun current(): JTheme {
        val key = Prefs.theme.state.value
        if (key == "custom") {
            val a = Color(Prefs.customAccent.state.value)
            return list[0].copy(key = "custom", en = "Custom Colour", vi = "Màu Tự Chọn", accent = a,
                onAccent = if (a.lum() > 0.5f) ON_ORANGE else Color.White)
        }
        return list.firstOrNull { it.key == key } ?: list[0]
    }
}

fun Color.lum(): Float = 0.2126f * red + 0.7152f * green + 0.0722f * blue

data class Skin(val key: String, val en: String, val vi: String) { val name get() = t(en, vi) }

object Skins {
    val list = listOf(
        Skin("pill", "Pill (Tom's Dock)", "Viên Thuốc (Tom's Dock)"),
        Skin("xp", "XP Classic", "XP Cổ Điển"),
        Skin("metal", "Classic Metal", "Cổ Điển Kim Loại"),
        Skin("wood", "Wooden Amplifier", "Ampli Gỗ"),
        Skin("glass", "Frosted Glass", "Kính Mờ"),
        Skin("slim", "Ultra Slim", "Siêu Gọn"),
        Skin("ipod", "Classic iPod Style", "iPod Cổ Điển"),
    )
    val xpColours = listOf("blue" to t("Blue", "Xanh Dương"), "silver" to t("Silver", "Bạc"), "olive" to t("Olive Green", "Xanh Ô Liu"))
}

/** Time-bar colours: 11 from Tom's Dock + 10 more, 4 gradients, from the album cover, and a custom colour. */
object BarColours {
    val list = listOf(
        Triple("Tom's Orange", "Cam Tom's", "#FBB040"), Triple("Emerald", "Xanh Lục Bảo", "#2ECC8F"),
        Triple("Turquoise", "Xanh Ngọc", "#2BC4C4"), Triple("Sky Blue", "Xanh Trời", "#48B0C8"), Triple("Blue", "Xanh Dương", "#4F8FF0"),
        Triple("Lavender", "Tím Oải Hương", "#A78BFA"), Triple("Peach Pink", "Hồng Đào", "#F472B6"), Triple("Ruby Red", "Đỏ Ruby", "#EF4444"),
        Triple("Lime Yellow", "Vàng Chanh", "#E8D44D"), Triple("Pearl White", "Trắng Ngọc Trai", "#F4F1EA"),
        Triple("Gold", "Vàng Kim", "#F5C542"), Triple("Terracotta", "Cam Đất", "#E07A4B"), Triple("Mint", "Xanh Bạc Hà", "#7EE3C1"),
        Triple("Bright Navy", "Xanh Navy Sáng", "#3F7CC4"), Triple("Plum", "Tím Than", "#8B5CF6"), Triple("Blush", "Hồng Phấn", "#F9A8D4"),
        Triple("Coral", "San Hô", "#FF7F6A"), Triple("Silver", "Bạc", "#C9D1D9"), Triple("Bronze", "Đồng", "#C98B4F"), Triple("Jade", "Xanh Ngọc Bích", "#00A884"),
        Triple("Rainbow", "Cầu Vồng", "grad:rainbow"), Triple("Sunset", "Hoàng Hôn", "grad:sunset"), Triple("Ocean", "Đại Dương", "grad:ocean"),
        Triple("Tom's Brand", "Màu Tom's", "grad:brand"), Triple("From Album Cover", "Theo Ảnh Bìa", "cover"),
    )
    val gradients = mapOf(
        "rainbow" to listOf(0xFFEF4444, 0xFFF59E0B, 0xFFE8D44D, 0xFF2ECC8F, 0xFF4F8FF0, 0xFFA78BFA),
        "sunset" to listOf(0xFFF472B6, 0xFFFB7185, 0xFFFBB040),
        "ocean" to listOf(0xFF0E88AA, 0xFF2BC4C4, 0xFF7EE3C1),
        "brand" to listOf(0xFF48B0C8, 0xFFFBB040),
    ).mapValues { e -> e.value.map { Color(it) } }

    fun hex(s: String): Color = try { Color(android.graphics.Color.parseColor(s)) } catch (_: Exception) { ORANGE }

    /** Colours to paint the bar with (one colour = solid). */
    fun colours(key: String, palette: IntArray): List<Color> = when {
        key == "custom" -> listOf(Color(Prefs.customBar.value))
        key == "cover" -> palette.take(3).map { Color(it) }
        key.startsWith("grad:") -> gradients[key.removePrefix("grad:")] ?: listOf(ORANGE)
        else -> listOf(hex(key))
    }
}

object EdgeEffects {
    val names = listOf(
        "Chasing Streaks" to "Vệt Sáng Đuổi Nhau", "Shooting Star" to "Sao Băng", "Spinning Rainbow" to "Cầu Vồng Xoay",
        "Breathing" to "Nhịp Thở", "Music Beat" to "Nhịp Nhạc", "Colour Wave" to "Sóng Màu", "Two Ends Meet" to "Hai Đầu Gặp Nhau",
        "Neon" to "Neon", "Sparkle" to "Lấp Lánh", "Running Dashes" to "Gạch Đứt Chạy", "Fire" to "Lửa", "Frost" to "Băng Giá",
        "Aurora" to "Cực Quang", "Water Ripples" to "Gợn Sóng Nước", "Stardust" to "Bụi Sao", "Sliding Sunset" to "Hoàng Hôn Trượt",
        "Heartbeat" to "Tim Đập", "Bass Runner" to "Chạy Theo Bass", "Edge Bars" to "Cột Sóng Viền", "Fireworks" to "Pháo Hoa",
        "Opposite Streaks" to "Vệt Ngược Chiều", "Four Corners" to "Bốn Góc Đuổi Nhau", "Falling Stars" to "Mưa Sao Rơi", "Lightning" to "Tia Chớp",
        "Electric" to "Điện Từ", "Diamond Glints" to "Ánh Kim Cương", "Christmas Lights" to "Đèn Giáng Sinh", "Tết Lanterns" to "Đèn Tết",
    )
    fun name(i: Int) = names.getOrNull(i)?.let { t(it.first, it.second) } ?: ""
    val speeds = listOf(0.3f, 0.6f, 1f, 1.7f, 2.8f)
    fun speedName(i: Int) = listOf(t("Very Slow", "Rất Chậm"), t("Slow", "Chậm"), t("Normal", "Vừa"), t("Fast", "Nhanh"), t("Very Fast", "Rất Nhanh"))[i.coerceIn(0, 4)]
}

object VizStyles {
    val names = listOf(
        "Glowing Waves" to "Sóng Phát Sáng", "Bars" to "Cột Sóng", "Mirror Bars" to "Cột Đối Xứng", "Dots" to "Chấm Nhảy",
        "Line" to "Đường Sóng", "Circle" to "Vòng Tròn", "Spectrum" to "Phổ Màu", "Flames" to "Ngọn Lửa",
        "Particles" to "Hạt Bay", "Rings" to "Vòng Lan Toả", "Oscilloscope" to "Dao Động Ký", "Starfield" to "Bầu Trời Sao",
        "Ocean Waves" to "Sóng Đại Dương", "Dancing Rainbow" to "Cầu Vồng Nhảy Múa", "Amp LEDs" to "Đèn LED Ampli", "VU Needles" to "Kim Đồng Hồ VU",
        "Glowing Circle" to "Vòng Tròn Phát Sáng", "Blooming Flower" to "Hoa Nở", "Spectrum Waterfall" to "Thác Nước Phổ", "Silk Ribbon" to "Dải Lụa",
        "Music Fireworks" to "Pháo Hoa Nhạc", "Mountains" to "Núi Non", "Light Rain" to "Mưa Ánh Sáng", "Mirror" to "Gương Đối Xứng",
        "Beating Heart" to "Tim Đập Nhịp", "Whirlwind" to "Lốc Xoáy", "Bubbles" to "Bong Bóng", "Neon Grid 3D" to "Lưới Neon 3D",
        "Fireflies" to "Đom Đóm", "Sound Fingerprint" to "Vân Tay Âm Thanh", "Sunburst" to "Mặt Trời Toả Tia", "Butterfly" to "Cánh Bướm",
        "Night City" to "Thành Phố Đêm", "Heart Monitor" to "Điện Tâm Đồ", "Ripples" to "Sóng Tròn Đồng Tâm", "Nebula" to "Tinh Vân",
    )
    fun name(i: Int) = names.getOrNull(i)?.let { t(it.first, it.second) } ?: ""
}
