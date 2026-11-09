package com.tomstechsolutions.jukebox.ui

import androidx.compose.ui.graphics.Color
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t

/**
 * The 70 shared themes ("chủ đề"). Each one has the same name as a visualisation and gives a colour theme,
 * a skin, a button set, a button colour, an edge light and a time-bar colour that belong together.
 * pattern: 0 waves 1 dots 2 stripes 3 rings 4 stars 5 petals 6 grid 7 swirl 8 flag 9 grain 10 mountains 11 rays
 */
data class Motif(val c: List<Long>, val pattern: Int, val btn: Int, val edge: Int, val light: Boolean = false) {
    val colours: List<Color> get() = c.map { Color(it) }
    val base get() = Color(c[0])
    val accent get() = Color(c[1])
}

object Motifs {
    private fun m(c0: Long, c1: Long, c2: Long, c3: Long, pattern: Int, btn: Int, edge: Int, light: Boolean = false) = Motif(listOf(c0, c1, c2, c3), pattern, btn, edge, light)

    val list = listOf(
        m(0xFF1E4A63, 0xFFFBB040, 0xFF48B0C8, 0xFF7EE3C1, 0, 0, 0),      // 0 Sóng Phát Sáng
        m(0xFF2B2F6B, 0xFF4F8FF0, 0xFFA78BFA, 0xFF2BC4C4, 2, 4, 18),     // 1 Cột Sóng
        m(0xFF3B1F4A, 0xFFF472B6, 0xFFA78BFA, 0xFF4F8FF0, 2, 12, 20),    // 2 Cột Đối Xứng
        m(0xFF123B5A, 0xFF2ECC8F, 0xFFE8D44D, 0xFF48B0C8, 1, 2, 9),      // 3 Chấm Nhảy
        m(0xFF0B3954, 0xFF2BC4C4, 0xFF7EE3C1, 0xFFFFFFFF, 0, 1, 5),      // 4 Đường Sóng
        m(0xFF2A1E4A, 0xFFA78BFA, 0xFFF472B6, 0xFFFBB040, 3, 3, 2),      // 5 Vòng Tròn
        m(0xFF1A1A1C, 0xFFEF4444, 0xFFE8D44D, 0xFF4F8FF0, 2, 2, 2),      // 6 Phổ Màu
        m(0xFF4A1408, 0xFFFF7A1A, 0xFFFFD54F, 0xFFE53935, 11, 6, 10),    // 7 Ngọn Lửa
        m(0xFF102030, 0xFF7DF9FF, 0xFFFFFFFF, 0xFFA78BFA, 1, 7, 14),     // 8 Hạt Bay
        m(0xFF0E3B4A, 0xFF48B0C8, 0xFF7EE3C1, 0xFFFBB040, 3, 3, 13),     // 9 Vòng Lan Toả
        m(0xFF06200F, 0xFF4CFF8A, 0xFF2ECC8F, 0xFFB8FFCF, 6, 11, 24),    // 10 Dao Động Ký
        m(0xFF0A0F2A, 0xFFFFFFFF, 0xFF9FA8DA, 0xFFFFE082, 4, 7, 14),     // 11 Bầu Trời Sao
        m(0xFF0B3954, 0xFF2BC4C4, 0xFF4F8FF0, 0xFFB3E5FC, 0, 3, 13),     // 12 Sóng Đại Dương
        m(0xFF1F1F2E, 0xFFEF4444, 0xFFF59E0B, 0xFF2ECC8F, 2, 12, 2),     // 13 Cầu Vồng Nhảy Múa
        m(0xFF141516, 0xFF34C759, 0xFFFFCC00, 0xFFFF3B30, 6, 8, 18),     // 14 Đèn LED Ampli
        m(0xFF3E2A14, 0xFFF4E9C8, 0xFFD9342B, 0xFFC9A227, 9, 8, 3),      // 15 Kim Đồng Hồ VU
        m(0xFF1C1236, 0xFFFF3DCB, 0xFF7DF9FF, 0xFFA78BFA, 3, 6, 7),      // 16 Vòng Tròn Phát Sáng
        m(0xFF4A1F35, 0xFFF8A5C2, 0xFFFFE082, 0xFFE8538A, 5, 12, 8),     // 17 Hoa Nở
        m(0xFF0A2A3A, 0xFF48B0C8, 0xFF7E57C2, 0xFF2ECC8F, 2, 4, 5),      // 18 Thác Nước Phổ
        m(0xFF3A1A40, 0xFFE8538A, 0xFFFBB040, 0xFFA78BFA, 0, 1, 15),     // 19 Dải Lụa
        m(0xFF120A20, 0xFFFFD54F, 0xFFFF5252, 0xFF7DF9FF, 4, 6, 19),     // 20 Pháo Hoa Nhạc
        m(0xFF1F3A2E, 0xFF7EC8A0, 0xFFA5D6A7, 0xFF5C6BC0, 10, 4, 15),    // 21 Núi Non
        m(0xFF0E1A2E, 0xFF7DF9FF, 0xFFA78BFA, 0xFFFFFFFF, 2, 7, 22),     // 22 Mưa Ánh Sáng
        m(0xFF202830, 0xFFC9D1D9, 0xFF48B0C8, 0xFFFFFFFF, 2, 8, 20),     // 23 Gương Đối Xứng
        m(0xFF4A0E1E, 0xFFFF4D6D, 0xFFFF8FA3, 0xFFFFE082, 5, 12, 16),    // 24 Tim Đập Nhịp
        m(0xFF1E2A3A, 0xFF90CAF9, 0xFFB0BEC5, 0xFF7E57C2, 7, 5, 2),      // 25 Lốc Xoáy
        m(0xFF0D3B5A, 0xFF81D4FA, 0xFFF8BBD0, 0xFFFFFFFF, 1, 7, 13),     // 26 Bong Bóng
        m(0xFF120830, 0xFFFF3DCB, 0xFF7DF9FF, 0xFF8B5CF6, 6, 6, 7),      // 27 Lưới Neon 3D
        m(0xFF0F2418, 0xFFFFF59D, 0xFFA5D6A7, 0xFFFFD54F, 1, 7, 8),      // 28 Đom Đóm
        m(0xFF1F2A44, 0xFF48B0C8, 0xFFF472B6, 0xFFFBB040, 3, 10, 24),    // 29 Vân Tay Âm Thanh
        m(0xFF5A2A08, 0xFFFFB300, 0xFFFFD54F, 0xFFFF7043, 11, 2, 15),    // 30 Mặt Trời Toả Tia
        m(0xFF2E1A47, 0xFFCE93D8, 0xFF4FC3F7, 0xFFFFE082, 5, 12, 12),    // 31 Cánh Bướm
        m(0xFF0F1626, 0xFFFFE08A, 0xFF4F8FF0, 0xFFFF7043, 6, 4, 9),      // 32 Thành Phố Đêm
        m(0xFF04140A, 0xFF4CFF8A, 0xFFFF5252, 0xFFB8FFCF, 6, 11, 16),    // 33 Điện Tâm Đồ
        m(0xFF0E2E3E, 0xFF7EE3C1, 0xFF48B0C8, 0xFFFFFFFF, 3, 3, 13),     // 34 Sóng Tròn Đồng Tâm
        m(0xFF1A0F33, 0xFFB388FF, 0xFFF48FB1, 0xFF80DEEA, 4, 7, 12),     // 35 Tinh Vân
        m(0xFF0E3B4A, 0xFFFFC1D6, 0xFFE8538A, 0xFF7EC8D8, 5, 12, 13),    // 36 Sen Nở Trên Hồ
        m(0xFF3A1A10, 0xFFFFB300, 0xFFE53935, 0xFF8E24AA, 1, 2, 27),     // 37 Đèn Lồng Hội An
        m(0xFF3A4A1A, 0xFFC9B037, 0xFF7CB342, 0xFF8ED1F0, 9, 10, 5),     // 38 Đồng Lúa
        m(0xFF4A3A08, 0xFFFFD000, 0xFFE65100, 0xFFFFF3B0, 5, 12, 22),    // 39 Mưa Hoa Mai
        m(0xFF151515, 0xFFFBB040, 0xFFE0E0E0, 0xFF9E9E9E, 3, 9, 0),      // 40 Đĩa Than Quay
        m(0xFF1A1A1A, 0xFFFFFFFF, 0xFF9E9E9E, 0xFFFBB040, 2, 4, 9),      // 41 Phím Đàn Piano
        m(0xFF3A1010, 0xFFFFC107, 0xFFE53935, 0xFFEEEEEE, 3, 2, 17),     // 42 Trống Nhảy
        m(0xFF2B2B2B, 0xFFF2E6C8, 0xFFFF7043, 0xFF9E9E9E, 9, 9, 9),      // 43 Băng Cassette Chạy
        m(0xFF0A0A1A, 0xFFFF1744, 0xFF00E5FF, 0xFF76FF03, 11, 6, 21),    // 44 Tia Laser Sân Khấu
        m(0xFF1A1A2E, 0xFFE0E0E0, 0xFFFF4081, 0xFF40C4FF, 1, 8, 25),     // 45 Quả Cầu Disco
        m(0xFF101018, 0xFFFFF59D, 0xFFFF7043, 0xFF7C4DFF, 11, 2, 6),     // 46 Đèn Pha Sân Khấu
        m(0xFF2A1040, 0xFFFF4081, 0xFFFFEB3B, 0xFF00E5FF, 7, 5, 2),      // 47 Kính Vạn Hoa
        m(0xFF020A04, 0xFF3CFF6E, 0xFFB8FFCF, 0xFF1B5E20, 2, 11, 22),    // 48 Mưa Chữ Ma Trận
        m(0xFF141A30, 0xFF4F8FF0, 0xFF2BC4C4, 0xFFA78BFA, 6, 4, 18),     // 49 Cột Sóng 3D Xoay
        m(0xFF0A0820, 0xFFB388FF, 0xFFFFF8E1, 0xFF4FC3F7, 7, 7, 14),     // 50 Thiên Hà Xoắn Ốc
        m(0xFF0D2A44, 0xFF81D4FA, 0xFF4FC3F7, 0xFFE1F5FE, 1, 3, 13),     // 51 Giọt Nước Rơi
        m(0xFF3E2A0C, 0xFFD4A84B, 0xFFFFE08A, 0xFF7A5A1E, 3, 8, 3),      // 52 Trống Đồng Đông Sơn
        m(0xFF4A3A1A, 0xFFF3E2B3, 0xFFC9A75C, 0xFFE53935, 7, 10, 0),     // 53 Nón Lá Xoay
        m(0xFF123A3A, 0xFF4FA3B8, 0xFF2E5D4B, 0xFFB3E5FC, 10, 3, 13),    // 54 Vịnh Hạ Long
        m(0xFFFCE4EC, 0xFFE8538A, 0xFFF8A5C2, 0xFF4E342E, 5, 12, 27, light = true),   // 55 Hoa Đào Tết
        m(0xFF1E4A7A, 0xFFFFB300, 0xFFE53935, 0xFF64B5F6, 2, 5, 15),     // 56 Diều Sáo
        m(0xFF4A0A0A, 0xFFFFD54F, 0xFFE53935, 0xFF43A047, 1, 2, 27),     // 57 Múa Lân
        m(0xFFFFDA00, 0xFFDA251D, 0xFFFFDA00, 0xFF8B1A12, 8, 2, 5, light = true),     // 58 Cờ Vàng Ba Sọc Đỏ
        m(0xFF3A0A0A, 0xFFFFC107, 0xFFD32F2F, 0xFFFF8F00, 7, 8, 10),     // 59 Rồng Múa
        m(0xFFF5F0E1, 0xFF263238, 0xFFC62828, 0xFF607D8B, 10, 10, 3, light = true),   // 60 Tranh Thuỷ Mặc
        m(0xFF3A0808, 0xFFFF5252, 0xFFFFC107, 0xFFD50000, 1, 2, 27),     // 61 Đèn Lồng Đỏ
        m(0xFF3E1010, 0xFFE53935, 0xFFFFE0B2, 0xFF3E2723, 11, 4, 6),     // 62 Quạt Giấy
        m(0xFF1A2A5A, 0xFF64B5F6, 0xFFFFC107, 0xFFE53935, 7, 5, 12),     // 63 Mây Cát Tường
        m(0xFF0D3A6E, 0xFFFF8F00, 0xFFC62828, 0xFF1976D2, 0, 12, 5),     // 64 Cá Chép Vượt Vũ Môn
        m(0xFF2A2A3A, 0xFF1565C0, 0xFFD32F2F, 0xFFFFC107, 2, 4, 9),      // 65 Cờ Phướn Trong Gió
        m(0xFF3A1A2A, 0xFFFFC107, 0xFFE53935, 0xFF1E88E5, 3, 3, 2),      // 66 Mandala Cát
        m(0xFF3A2A0A, 0xFFFFD54F, 0xFFD4A84B, 0xFFFFF3E0, 3, 8, 3),      // 67 Bát Hát
        m(0xFF1A237E, 0xFF9FA8DA, 0xFFFFFFFF, 0xFFFFCCBC, 10, 7, 14),    // 68 Dãy Himalaya
        m(0xFF2A1A05, 0xFFFFB300, 0xFFFFF59D, 0xFFFF6F00, 11, 6, 3),     // 69 Đèn Bơ
    )

    fun name(i: Int) = VizStyles.name(i)

    // ---- groups shared by visualisations and themes ----
    private val nature = setOf(11, 12, 17, 19, 21, 22, 25, 26, 28, 30, 31, 34, 35, 36, 38, 39, 50, 51, 54, 55, 63, 64, 68)
    private val stage = setOf(7, 14, 16, 20, 27, 32, 44, 45, 46, 47, 48, 49)
    private val music = setOf(14, 15, 40, 41, 42, 43, 67)
    private val modern = setOf(1, 2, 3, 4, 6, 8, 9, 10, 13, 18, 23, 27, 29, 33, 47, 48, 49)
    private val classic = setOf(0, 5, 14, 15, 24, 40, 43)
    val vn = (36..39).toSet() + (52..58)
    val cn = (59..64).toSet()
    val tibet = (65..69).toSet()

    fun groups(i: Int): Set<String> = buildSet {
        if (i in nature) add("nature"); if (i in stage) add("stage"); if (i in music) add("music")
        if (i in modern) add("modern"); if (i in classic) add("classic")
        if (i in vn) { add("vn"); add("east") }; if (i in cn) { add("cn"); add("east") }; if (i in tibet) { add("tibet"); add("east") }
    }

    val filters = listOf(
        "all" to ("All" to "Tất Cả"), "fav" to ("★ Favourites" to "★ Yêu Thích"), "recent" to ("Recent" to "Gần Đây"), "basic" to ("Basic" to "Cơ Bản"),
        "east" to ("Eastern" to "Phương Đông"), "vn" to ("Vietnam" to "Việt Nam"), "cn" to ("China" to "Trung Quốc"), "tibet" to ("Tibet" to "Tây Tạng"),
        "nature" to ("Nature" to "Thiên Nhiên"), "stage" to ("Stage" to "Sân Khấu"), "music" to ("Music" to "Âm Nhạc"), "modern" to ("Modern" to "Hiện Đại"), "classic" to ("Classic" to "Cổ Điển"),
    )

    // ---- which theme a setting points at ----
    /** "m:12" → 12, "pack" → the chosen theme pack, anything else → null. */
    fun of(key: String): Int? = when {
        key.startsWith("m:") -> key.removePrefix("m:").toIntOrNull()?.takeIf { it in list.indices }
        key == "pack" -> Prefs.pack.value.takeIf { it in list.indices }
        else -> null
    }
    /** For number settings: 100+i → i, -1 → pack. */
    fun ofInt(v: Int): Int? = when {
        v >= 100 -> (v - 100).takeIf { it in list.indices }
        v == -1 -> Prefs.pack.value.takeIf { it in list.indices }
        else -> null
    }

    fun skinMotif(key: String = Prefs.skin.value) = of(key)
    /** The real button set to draw (0..12) and the theme colours for the ring behind it, if any. */
    fun buttonStyle(v: Int = Prefs.btnStyle.value): Pair<Int, Motif?> { val i = ofInt(v); return if (i == null) v.coerceIn(0, 12) to null else list[i].btn to list[i] }
    fun edgeStyle(v: Int = Prefs.edgeEffect.value): Pair<Int, Motif?> { val i = ofInt(v); return if (i == null) v.coerceIn(0, EdgeEffects.names.size - 1) to null else list[i].edge to list[i] }

    fun theme(i: Int): JTheme {
        val mo = list[i]; val c = mo.colours
        return if (mo.light) JTheme("m:$i", name(i), name(i), c[0], c[0].darken(0.9f), Color(0xFFFFFFFF), Color(0xFF231A14), c[3].copy(alpha = 0.8f),
            c[1], if (c[1].lum() > 0.5f) ON_ORANGE else Color.White, Color(0xFFFFFFFF), light = true)
        else JTheme("m:$i", name(i), name(i), c[0].darken(0.75f), c[0].darken(0.25f), Color(0x1FFFFFFF), Color.White,
            lighten(c[2], 0.45f), c[1], if (c[1].lum() > 0.5f) ON_ORANGE else Color.White, c[0].darken(0.18f))
    }

    fun lighten(c: Color, k: Float) = Color(c.red + (1 - c.red) * k, c.green + (1 - c.green) * k, c.blue + (1 - c.blue) * k, 1f)

    /** Bộ Chủ Đề: one tap changes all six looks and the visualisation. */
    fun applyPack(i: Int) {
        Prefs.pack.value = i
        Prefs.theme.value = "pack"; Prefs.skin.value = "pack"; Prefs.btnStyle.value = -1; Prefs.btnColour.value = "pack"
        Prefs.edgeEffect.value = -1; Prefs.edgeAuto.value = false; Prefs.edgeRandom.value = false
        Prefs.barColour.value = "pack"; Prefs.viz.value = i; Prefs.vizAuto.value = false
    }

    // ---- favourites and recent, per picker ----
    private fun set(s: String) = s.split('\n').filter { it.isNotBlank() }
    fun isFav(cat: String, id: String) = "$cat|$id" in set(Prefs.favStyles.value)
    fun toggleFav(cat: String, id: String): Boolean {
        val l = set(Prefs.favStyles.value).toMutableList(); val k = "$cat|$id"
        val now = if (k in l) { l.remove(k); false } else { l.add(k); true }
        Prefs.favStyles.value = l.joinToString("\n"); return now
    }
    fun favs(cat: String) = set(Prefs.favStyles.value).filter { it.startsWith("$cat|") }.map { it.substringAfter('|') }
    fun recent(cat: String) = set(Prefs.recentStyles.value).filter { it.startsWith("$cat|") }.map { it.substringAfter('|') }
    fun addRecent(cat: String, id: String) {
        val k = "$cat|$id"; val l = (listOf(k) + set(Prefs.recentStyles.value).filter { it != k })
        val mine = l.filter { it.startsWith("$cat|") }.take(5); val other = l.filter { !it.startsWith("$cat|") }
        Prefs.recentStyles.value = (mine + other).take(60).joinToString("\n")
    }

    fun filterName(k: String) = filters.firstOrNull { it.first == k }?.second?.let { t(it.first, it.second) } ?: k
}
