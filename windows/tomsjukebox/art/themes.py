"""Colour themes, skins list, time-bar colours, edge-light names, visualisation names and the 70 Bộ Chủ Đề —
the same lists as the Android app (ui/Theme.kt and ui/Motifs.kt)."""
import math
import random

from .. import i18n
from .ds import Brush, Color, Offset, Path, Stroke, PI, sin, cos, clamp
from .prefs import Prefs


def t(en, vi):
    return vi if i18n.lang() == "vi" else en


NAVY = Color(0xFF0D2C40)
NAVY_D = Color(0xFF071A26)
NAVY_L = Color(0xFF1E4A63)
TEAL = Color(0xFF0E88AA)
SKY = Color(0xFF48B0C8)
ORANGE = Color(0xFFFBB040)
ON_ORANGE = Color(0xFF2A1A00)
SPLASH_TEXT = Color(0xFFCFE6EE)


def lum(c):
    return 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b


class JTheme:
    def __init__(self, key, en, vi, top, bottom, card, text, muted, accent, onAccent, nav, light=False):
        self.key, self.en, self.vi = key, en, vi
        self.top, self.bottom, self.card, self.text, self.muted = top, bottom, card, text, muted
        self.accent, self.onAccent, self.nav, self.light = accent, onAccent, nav, light

    @property
    def name(self):
        return t(self.en, self.vi)

    def copy(self, **kw):
        d = dict(self.__dict__)
        d.update(kw)
        return JTheme(**d)


def _jt(key, en, vi, top, bottom, card, text, muted, accent, on, nav, light=False):
    return JTheme(key, en, vi, Color(top), Color(bottom), Color(card), Color(text), Color(muted), Color(accent), Color(on),
                  Color(nav), light)


W_ = 0xFFFFFFFF


class Themes:
    list = [
        _jt("toms", "Tom's Technology Solutions", "Tom's Technology Solutions", 0xFF0D2C40, 0xFF071A26, 0x1FFFFFFF, W_, 0xFF9FC3D3, 0xFFFBB040, 0xFF2A1A00, 0xFF06141E),
        _jt("dark", "Dark", "Tối", 0xFF1A1A1C, 0xFF000000, 0x1AFFFFFF, W_, 0xFFA8A8AE, 0xFFFBB040, 0xFF2A1A00, 0xFF0B0B0C),
        _jt("soft", "Soft", "Mềm Mại", 0xFFF4F8FA, 0xFFE6EEF2, 0xFFFFFFFF, 0xFF0F2A38, 0xFF4F6B79, 0xFF0E88AA, W_, 0xFFFFFFFF, True),
        _jt("frosted", "Frosted Glass", "Kính Mờ", 0xFF203A4C, 0xFF0E1C26, 0x26FFFFFF, W_, 0xFFBFD8E3, 0xFF48B0C8, 0xFF071A26, 0x99101C24),
        _jt("ocean", "Ocean", "Đại Dương", 0xFF0B3954, 0xFF04151F, 0x1FFFFFFF, W_, 0xFF9CC9D6, 0xFF2BC4C4, 0xFF00211F, 0xFF03111A),
        _jt("sunset", "Sunset", "Hoàng Hôn", 0xFF4A2335, 0xFF160A10, 0x1FFFFFFF, W_, 0xFFE2B5C2, 0xFFFB7185, 0xFF2A0710, 0xFF12080C),
        _jt("forest", "Forest", "Rừng Xanh", 0xFF12352B, 0xFF06140F, 0x1FFFFFFF, W_, 0xFFA6D5C3, 0xFF7EE3C1, 0xFF032016, 0xFF04100C),
        _jt("peach", "Peach", "Hồng Đào", 0xFFFFF1F2, 0xFFFCE4EA, 0xFFFFFFFF, 0xFF3B1622, 0xFF7A4E5B, 0xFFE0558F, W_, 0xFFFFFFFF, True),
        _jt("plum", "Plum", "Tím Than", 0xFF2A1E4A, 0xFF0F0A1E, 0x1FFFFFFF, W_, 0xFFC3B6E8, 0xFFA78BFA, 0xFF16093A, 0xFF0C0818),
        _jt("coffee", "Coffee", "Cà Phê", 0xFF3B2A20, 0xFF140D09, 0x1FFFFFFF, W_, 0xFFD9C0A8, 0xFFE0A96D, 0xFF2A1503, 0xFF100A07),
        _jt("graphite", "Graphite", "Than Chì", 0xFF2B2F33, 0xFF121416, 0x1FFFFFFF, W_, 0xFFB4BCC4, 0xFFC9D1D9, 0xFF15191D, 0xFF0D0F11),
    ]

    @staticmethod
    def now():
        key = Prefs.theme.value
        i = Motifs.of(key)
        if i is not None:
            return Motifs.theme(i)
        if key == "custom":
            a = Color(Prefs.customAccent.value)
            return Themes.list[0].copy(key="custom", en="Custom Colour", vi="Màu Tự Chọn", accent=a,
                                       onAccent=ON_ORANGE if lum(a) > 0.5 else Color.White)
        for th in Themes.list:
            if th.key == key:
                return th
        return Themes.list[0]


class Skins:
    list = [("pill", "Pill (Tom's Dock)", "Viên Thuốc (Tom's Dock)"), ("xp", "XP Classic", "XP Cổ Điển"),
            ("metal", "Classic Metal", "Cổ Điển Kim Loại"), ("wood", "Wooden Amplifier", "Ampli Gỗ"),
            ("glass", "Frosted Glass", "Kính Mờ"), ("slim", "Ultra Slim", "Siêu Gọn"), ("ipod", "Classic iPod Style", "iPod Cổ Điển")]

    @staticmethod
    def xpColours():
        return [("blue", t("Blue", "Xanh Dương")), ("silver", t("Silver", "Bạc")), ("olive", t("Olive Green", "Xanh Ô Liu"))]


class BarColours:
    list = [
        ("Tom's Orange", "Cam Tom's", "#FBB040"), ("Emerald", "Xanh Lục Bảo", "#2ECC8F"),
        ("Turquoise", "Xanh Ngọc", "#2BC4C4"), ("Sky Blue", "Xanh Trời", "#48B0C8"), ("Blue", "Xanh Dương", "#4F8FF0"),
        ("Lavender", "Tím Oải Hương", "#A78BFA"), ("Peach Pink", "Hồng Đào", "#F472B6"), ("Ruby Red", "Đỏ Ruby", "#EF4444"),
        ("Lime Yellow", "Vàng Chanh", "#E8D44D"), ("Pearl White", "Trắng Ngọc Trai", "#F4F1EA"),
        ("Gold", "Vàng Kim", "#F5C542"), ("Terracotta", "Cam Đất", "#E07A4B"), ("Mint", "Xanh Bạc Hà", "#7EE3C1"),
        ("Bright Navy", "Xanh Navy Sáng", "#3F7CC4"), ("Plum", "Tím Than", "#8B5CF6"), ("Blush", "Hồng Phấn", "#F9A8D4"),
        ("Coral", "San Hô", "#FF7F6A"), ("Silver", "Bạc", "#C9D1D9"), ("Bronze", "Đồng", "#C98B4F"), ("Jade", "Xanh Ngọc Bích", "#00A884"),
        ("Rainbow", "Cầu Vồng", "grad:rainbow"), ("Sunset", "Hoàng Hôn", "grad:sunset"), ("Ocean", "Đại Dương", "grad:ocean"),
        ("Tom's Brand", "Màu Tom's", "grad:brand"), ("From Album Cover", "Theo Ảnh Bìa", "cover"),
    ]
    gradients = {
        "rainbow": [Color(x) for x in (0xFFEF4444, 0xFFF59E0B, 0xFFE8D44D, 0xFF2ECC8F, 0xFF4F8FF0, 0xFFA78BFA)],
        "sunset": [Color(x) for x in (0xFFF472B6, 0xFFFB7185, 0xFFFBB040)],
        "ocean": [Color(x) for x in (0xFF0E88AA, 0xFF2BC4C4, 0xFF7EE3C1)],
        "brand": [Color(x) for x in (0xFF48B0C8, 0xFFFBB040)],
    }

    @staticmethod
    def hex(s):
        try:
            return Color(s)
        except Exception:
            return ORANGE

    @staticmethod
    def colours(key, palette):
        i = Motifs.of(key)
        if i is not None:
            return Motifs.list[i].colours[1:]
        if key == "custom":
            return [Color(Prefs.customBar.value)]
        if key == "cover":
            return [Color(x) if not isinstance(x, Color) else x for x in palette[:3]] or [ORANGE]
        if key.startswith("grad:"):
            return BarColours.gradients.get(key[5:], [ORANGE])
        return [BarColours.hex(key)]


class EdgeEffects:
    names = [
        ("Chasing Streaks", "Vệt Sáng Đuổi Nhau"), ("Shooting Star", "Sao Băng"), ("Spinning Rainbow", "Cầu Vồng Xoay"),
        ("Breathing", "Nhịp Thở"), ("Music Beat", "Nhịp Nhạc"), ("Colour Wave", "Sóng Màu"), ("Two Ends Meet", "Hai Đầu Gặp Nhau"),
        ("Neon", "Neon"), ("Sparkle", "Lấp Lánh"), ("Running Dashes", "Gạch Đứt Chạy"), ("Fire", "Lửa"), ("Frost", "Băng Giá"),
        ("Aurora", "Cực Quang"), ("Water Ripples", "Gợn Sóng Nước"), ("Stardust", "Bụi Sao"), ("Sliding Sunset", "Hoàng Hôn Trượt"),
        ("Heartbeat", "Tim Đập"), ("Bass Runner", "Chạy Theo Bass"), ("Edge Bars", "Cột Sóng Viền"), ("Fireworks", "Pháo Hoa"),
        ("Opposite Streaks", "Vệt Ngược Chiều"), ("Four Corners", "Bốn Góc Đuổi Nhau"), ("Falling Stars", "Mưa Sao Rơi"), ("Lightning", "Tia Chớp"),
        ("Electric", "Điện Từ"), ("Diamond Glints", "Ánh Kim Cương"), ("Christmas Lights", "Đèn Giáng Sinh"), ("Tết Lanterns", "Đèn Tết"),
    ]
    speeds = [0.3, 0.6, 1.0, 1.7, 2.8]

    @staticmethod
    def name(i):
        return t(*EdgeEffects.names[i]) if 0 <= i < len(EdgeEffects.names) else ""

    @staticmethod
    def speedName(i):
        return [t("Very Slow", "Rất Chậm"), t("Slow", "Chậm"), t("Normal", "Vừa"), t("Fast", "Nhanh"), t("Very Fast", "Rất Nhanh")][clamp(i, 0, 4)]


_VIZ = [
    ("Glowing Waves", "Sóng Phát Sáng"), ("Bars", "Cột Sóng"), ("Mirror Bars", "Cột Đối Xứng"), ("Dots", "Chấm Nhảy"),
    ("Line", "Đường Sóng"), ("Circle", "Vòng Tròn"), ("Spectrum", "Phổ Màu"), ("Flames", "Ngọn Lửa"),
    ("Particles", "Hạt Bay"), ("Rings", "Vòng Lan Toả"), ("Oscilloscope", "Dao Động Ký"), ("Starfield", "Bầu Trời Sao"),
    ("Ocean Waves", "Sóng Đại Dương"), ("Dancing Rainbow", "Cầu Vồng Nhảy Múa"), ("Amp LEDs", "Đèn LED Ampli"), ("VU Needles", "Kim Đồng Hồ VU"),
    ("Glowing Circle", "Vòng Tròn Phát Sáng"), ("Blooming Flower", "Hoa Nở"), ("Spectrum Waterfall", "Thác Nước Phổ"), ("Silk Ribbon", "Dải Lụa"),
    ("Music Fireworks", "Pháo Hoa Nhạc"), ("Mountains", "Núi Non"), ("Light Rain", "Mưa Ánh Sáng"), ("Mirror", "Gương Đối Xứng"),
    ("Beating Heart", "Tim Đập Nhịp"), ("Whirlwind", "Lốc Xoáy"), ("Bubbles", "Bong Bóng"), ("Neon Grid 3D", "Lưới Neon 3D"),
    ("Fireflies", "Đom Đóm"), ("Sound Fingerprint", "Vân Tay Âm Thanh"), ("Sunburst", "Mặt Trời Toả Tia"), ("Butterfly", "Cánh Bướm"),
    ("Night City", "Thành Phố Đêm"), ("Heart Monitor", "Điện Tâm Đồ"), ("Ripples", "Sóng Tròn Đồng Tâm"), ("Nebula", "Tinh Vân"),
    ("Lotus On The Lake", "Sen Nở Trên Hồ"), ("Hội An Lanterns", "Đèn Lồng Hội An"), ("Rice Fields", "Đồng Lúa"), ("Apricot Blossom Rain", "Mưa Hoa Mai"),
    ("Spinning Vinyl", "Đĩa Than Quay"), ("Piano Keys", "Phím Đàn Piano"), ("Jumping Drums", "Trống Nhảy"), ("Running Cassette", "Băng Cassette Chạy"),
    ("Stage Lasers", "Tia Laser Sân Khấu"), ("Disco Ball", "Quả Cầu Disco"), ("Stage Spotlights", "Đèn Pha Sân Khấu"), ("Kaleidoscope", "Kính Vạn Hoa"),
    ("Matrix Rain", "Mưa Chữ Ma Trận"), ("Rotating 3D Bars", "Cột Sóng 3D Xoay"), ("Spiral Galaxy", "Thiên Hà Xoắn Ốc"), ("Water Drops", "Giọt Nước Rơi"),
    ("Đông Sơn Bronze Drum", "Trống Đồng Đông Sơn"), ("Spinning Conical Hats", "Nón Lá Xoay"), ("Hạ Long Bay", "Vịnh Hạ Long"), ("Tết Peach Blossom", "Hoa Đào Tết"),
    ("Flute Kites", "Diều Sáo"), ("Lion Dance", "Múa Lân"), ("(removed)", "(đã bỏ)"),
    ("Dancing Dragon", "Rồng Múa"), ("Ink Wash Painting", "Tranh Thuỷ Mặc"), ("Red Lanterns", "Đèn Lồng Đỏ"), ("Paper Fan", "Quạt Giấy"),
    ("Auspicious Clouds", "Mây Cát Tường"), ("Carp Leaping The Dragon Gate", "Cá Chép Vượt Vũ Môn"),
    ("Prayer Flags In The Wind", "Cờ Phướn Trong Gió"), ("Sand Mandala", "Mandala Cát"), ("Singing Bowl", "Bát Hát"), ("Himalayas", "Dãy Himalaya"), ("Butter Lamps", "Đèn Bơ"),
    ("Multicolour Silk Waves", "Sóng Lụa Đa Sắc"), ("Soft Aurora", "Cực Quang Mềm"), ("Glowing Mirror Wave", "Sóng Đối Xứng Phát Sáng"),
    ("Rounded Colour Bars", "Cột Bo Tròn Đa Sắc"), ("Bouncing Colour Drops", "Giọt Màu Nhảy"), ("Neon Streams", "Dòng Chảy Neon"),
    ("Flying Silk", "Lụa Bay Nhiều Lớp"), ("Twisting Pastel Silk", "Lụa Xoắn Pastel"), ("Shimmering Sunset Silk", "Lụa Óng Ánh Hoàng Hôn"), ("Ocean Silk", "Lụa Đại Dương"),
    ("Green Northern Lights", "Bắc Cực Quang Xanh Lá"), ("Pink & Violet Aurora", "Cực Quang Tím Hồng"), ("Rippling Aurora Curtain", "Màn Cực Quang Gợn Sóng"), ("Aurora Over Snowy Mountains", "Cực Quang Trên Núi Tuyết"),
]


class VizStyles:
    names = _VIZ
    removed = {58}

    @staticmethod
    def name(i):
        return t(*_VIZ[i]) if 0 <= i < len(_VIZ) else ""

    @staticmethod
    def speed():
        return clamp(float(Prefs.vizSpeed.value), 0.25, 3.0)

    @staticmethod
    def count():
        return len(_VIZ)

    @staticmethod
    def autoPick(clock):
        favs = []
        for f in Motifs.favs("viz"):
            try:
                favs.append(int(f[2:] if f.startswith("v:") else f))
            except ValueError:
                pass
        pool = [x for x in favs if x not in VizStyles.removed] or [i for i in range(len(_VIZ)) if i not in VizStyles.removed]
        return pool[int(clock / 20.0) % len(pool)]


class Motif:
    def __init__(self, c, pattern, btn, edge, light=False):
        self.c, self.pattern, self.btn, self.edge, self.light = c, pattern, btn, edge, light
        self.colours = [Color(x) for x in c]

    @property
    def base(self):
        return self.colours[0]

    @property
    def accent(self):
        return self.colours[1]


def _m(c0, c1, c2, c3, pattern, btn, edge, light=False):
    return Motif([c0, c1, c2, c3], pattern, btn, edge, light)


class Motifs:
    list = [
        _m(0xFF1E4A63, 0xFFFBB040, 0xFF48B0C8, 0xFF7EE3C1, 0, 0, 0), _m(0xFF2B2F6B, 0xFF4F8FF0, 0xFFA78BFA, 0xFF2BC4C4, 2, 4, 18),
        _m(0xFF3B1F4A, 0xFFF472B6, 0xFFA78BFA, 0xFF4F8FF0, 2, 12, 20), _m(0xFF123B5A, 0xFF2ECC8F, 0xFFE8D44D, 0xFF48B0C8, 1, 2, 9),
        _m(0xFF0B3954, 0xFF2BC4C4, 0xFF7EE3C1, 0xFFFFFFFF, 0, 1, 5), _m(0xFF2A1E4A, 0xFFA78BFA, 0xFFF472B6, 0xFFFBB040, 3, 3, 2),
        _m(0xFF1A1A1C, 0xFFEF4444, 0xFFE8D44D, 0xFF4F8FF0, 2, 2, 2), _m(0xFF4A1408, 0xFFFF7A1A, 0xFFFFD54F, 0xFFE53935, 11, 6, 10),
        _m(0xFF102030, 0xFF7DF9FF, 0xFFFFFFFF, 0xFFA78BFA, 1, 7, 14), _m(0xFF0E3B4A, 0xFF48B0C8, 0xFF7EE3C1, 0xFFFBB040, 3, 3, 13),
        _m(0xFF06200F, 0xFF4CFF8A, 0xFF2ECC8F, 0xFFB8FFCF, 6, 11, 24), _m(0xFF0A0F2A, 0xFFFFFFFF, 0xFF9FA8DA, 0xFFFFE082, 4, 7, 14),
        _m(0xFF0B3954, 0xFF2BC4C4, 0xFF4F8FF0, 0xFFB3E5FC, 0, 3, 13), _m(0xFF1F1F2E, 0xFFEF4444, 0xFFF59E0B, 0xFF2ECC8F, 2, 12, 2),
        _m(0xFF141516, 0xFF34C759, 0xFFFFCC00, 0xFFFF3B30, 6, 8, 18), _m(0xFF3E2A14, 0xFFF4E9C8, 0xFFD9342B, 0xFFC9A227, 9, 8, 3),
        _m(0xFF1C1236, 0xFFFF3DCB, 0xFF7DF9FF, 0xFFA78BFA, 3, 6, 7), _m(0xFF4A1F35, 0xFFF8A5C2, 0xFFFFE082, 0xFFE8538A, 5, 12, 8),
        _m(0xFF0A2A3A, 0xFF48B0C8, 0xFF7E57C2, 0xFF2ECC8F, 2, 4, 5), _m(0xFF3A1A40, 0xFFE8538A, 0xFFFBB040, 0xFFA78BFA, 0, 1, 15),
        _m(0xFF120A20, 0xFFFFD54F, 0xFFFF5252, 0xFF7DF9FF, 4, 6, 19), _m(0xFF1F3A2E, 0xFF7EC8A0, 0xFFA5D6A7, 0xFF5C6BC0, 10, 4, 15),
        _m(0xFF0E1A2E, 0xFF7DF9FF, 0xFFA78BFA, 0xFFFFFFFF, 2, 7, 22), _m(0xFF202830, 0xFFC9D1D9, 0xFF48B0C8, 0xFFFFFFFF, 2, 8, 20),
        _m(0xFF4A0E1E, 0xFFFF4D6D, 0xFFFF8FA3, 0xFFFFE082, 5, 12, 16), _m(0xFF1E2A3A, 0xFF90CAF9, 0xFFB0BEC5, 0xFF7E57C2, 7, 5, 2),
        _m(0xFF0D3B5A, 0xFF81D4FA, 0xFFF8BBD0, 0xFFFFFFFF, 1, 7, 13), _m(0xFF120830, 0xFFFF3DCB, 0xFF7DF9FF, 0xFF8B5CF6, 6, 6, 7),
        _m(0xFF0F2418, 0xFFFFF59D, 0xFFA5D6A7, 0xFFFFD54F, 1, 7, 8), _m(0xFF1F2A44, 0xFF48B0C8, 0xFFF472B6, 0xFFFBB040, 3, 10, 24),
        _m(0xFF5A2A08, 0xFFFFB300, 0xFFFFD54F, 0xFFFF7043, 11, 2, 15), _m(0xFF2E1A47, 0xFFCE93D8, 0xFF4FC3F7, 0xFFFFE082, 5, 12, 12),
        _m(0xFF0F1626, 0xFFFFE08A, 0xFF4F8FF0, 0xFFFF7043, 6, 4, 9), _m(0xFF04140A, 0xFF4CFF8A, 0xFFFF5252, 0xFFB8FFCF, 6, 11, 16),
        _m(0xFF0E2E3E, 0xFF7EE3C1, 0xFF48B0C8, 0xFFFFFFFF, 3, 3, 13), _m(0xFF1A0F33, 0xFFB388FF, 0xFFF48FB1, 0xFF80DEEA, 4, 7, 12),
        _m(0xFF0E3B4A, 0xFFFFC1D6, 0xFFE8538A, 0xFF7EC8D8, 5, 12, 13), _m(0xFF3A1A10, 0xFFFFB300, 0xFFE53935, 0xFF8E24AA, 1, 2, 27),
        _m(0xFF3A4A1A, 0xFFC9B037, 0xFF7CB342, 0xFF8ED1F0, 9, 10, 5), _m(0xFF4A3A08, 0xFFFFD000, 0xFFE65100, 0xFFFFF3B0, 5, 12, 22),
        _m(0xFF151515, 0xFFFBB040, 0xFFE0E0E0, 0xFF9E9E9E, 3, 9, 0), _m(0xFF1A1A1A, 0xFFFFFFFF, 0xFF9E9E9E, 0xFFFBB040, 2, 4, 9),
        _m(0xFF3A1010, 0xFFFFC107, 0xFFE53935, 0xFFEEEEEE, 3, 2, 17), _m(0xFF2B2B2B, 0xFFF2E6C8, 0xFFFF7043, 0xFF9E9E9E, 9, 9, 9),
        _m(0xFF0A0A1A, 0xFFFF1744, 0xFF00E5FF, 0xFF76FF03, 11, 6, 21), _m(0xFF1A1A2E, 0xFFE0E0E0, 0xFFFF4081, 0xFF40C4FF, 1, 8, 25),
        _m(0xFF101018, 0xFFFFF59D, 0xFFFF7043, 0xFF7C4DFF, 11, 2, 6), _m(0xFF2A1040, 0xFFFF4081, 0xFFFFEB3B, 0xFF00E5FF, 7, 5, 2),
        _m(0xFF020A04, 0xFF3CFF6E, 0xFFB8FFCF, 0xFF1B5E20, 2, 11, 22), _m(0xFF141A30, 0xFF4F8FF0, 0xFF2BC4C4, 0xFFA78BFA, 6, 4, 18),
        _m(0xFF0A0820, 0xFFB388FF, 0xFFFFF8E1, 0xFF4FC3F7, 7, 7, 14), _m(0xFF0D2A44, 0xFF81D4FA, 0xFF4FC3F7, 0xFFE1F5FE, 1, 3, 13),
        _m(0xFF3E2A0C, 0xFFD4A84B, 0xFFFFE08A, 0xFF7A5A1E, 3, 8, 3), _m(0xFF4A3A1A, 0xFFF3E2B3, 0xFFC9A75C, 0xFFE53935, 7, 10, 0),
        _m(0xFF123A3A, 0xFF4FA3B8, 0xFF2E5D4B, 0xFFB3E5FC, 10, 3, 13), _m(0xFFFCE4EC, 0xFFE8538A, 0xFFF8A5C2, 0xFF4E342E, 5, 12, 27, True),
        _m(0xFF1E4A7A, 0xFFFFB300, 0xFFE53935, 0xFF64B5F6, 2, 5, 15), _m(0xFF4A0A0A, 0xFFFFD54F, 0xFFE53935, 0xFF43A047, 1, 2, 27),
        _m(0xFF1E4A63, 0xFFFBB040, 0xFF48B0C8, 0xFF7EE3C1, 0, 0, 0),   # 58 (removed – kept so numbers stay the same)
        _m(0xFF3A0A0A, 0xFFFFC107, 0xFFD32F2F, 0xFFFF8F00, 7, 8, 10), _m(0xFFF5F0E1, 0xFF263238, 0xFFC62828, 0xFF607D8B, 10, 10, 3, True),
        _m(0xFF3A0808, 0xFFFF5252, 0xFFFFC107, 0xFFD50000, 1, 2, 27), _m(0xFF3E1010, 0xFFE53935, 0xFFFFE0B2, 0xFF3E2723, 11, 4, 6),
        _m(0xFF1A2A5A, 0xFF64B5F6, 0xFFFFC107, 0xFFE53935, 7, 5, 12), _m(0xFF0D3A6E, 0xFFFF8F00, 0xFFC62828, 0xFF1976D2, 0, 12, 5),
        _m(0xFF2A2A3A, 0xFF1565C0, 0xFFD32F2F, 0xFFFFC107, 2, 4, 9), _m(0xFF3A1A2A, 0xFFFFC107, 0xFFE53935, 0xFF1E88E5, 3, 3, 2),
        _m(0xFF3A2A0A, 0xFFFFD54F, 0xFFD4A84B, 0xFFFFF3E0, 3, 8, 3), _m(0xFF1A237E, 0xFF9FA8DA, 0xFFFFFFFF, 0xFFFFCCBC, 10, 7, 14),
        _m(0xFF2A1A05, 0xFFFFB300, 0xFFFFF59D, 0xFFFF6F00, 11, 6, 3),
    ]
    removed = {58}

    nature = {11, 12, 17, 19, 21, 22, 25, 26, 28, 30, 31, 34, 35, 36, 38, 39, 50, 51, 54, 55, 63, 64, 68}
    stage = {7, 14, 16, 20, 27, 32, 44, 45, 46, 47, 48, 49}
    music = {14, 15, 40, 41, 42, 43, 67}
    modern = {1, 2, 3, 4, 6, 8, 9, 10, 13, 18, 23, 27, 29, 33, 47, 48, 49}
    classic = {0, 5, 14, 15, 24, 40, 43}
    vn = set(range(36, 40)) | set(range(52, 58))
    cn = set(range(59, 65))
    tibet = set(range(65, 70))

    filters = [
        ("all", ("All", "Tất Cả")), ("fav", ("★ Favourites", "★ Yêu Thích")), ("recent", ("Recent", "Gần Đây")), ("basic", ("Basic", "Cơ Bản")),
        ("east", ("Eastern", "Phương Đông")), ("vn", ("Vietnam", "Việt Nam")), ("cn", ("China", "Trung Quốc")), ("tibet", ("Tibet", "Tây Tạng")),
        ("nature", ("Nature", "Thiên Nhiên")), ("stage", ("Stage", "Sân Khấu")), ("music", ("Music", "Âm Nhạc")), ("modern", ("Modern", "Hiện Đại")),
        ("colour", ("Multicolour", "Nhiều Màu")), ("classic", ("Classic", "Cổ Điển")),
    ]

    @staticmethod
    def name(i):
        return VizStyles.name(i)

    @staticmethod
    def groups(i):
        g = set()
        if i >= 70:
            return {"modern", "stage", "colour"}
        if i in Motifs.nature:
            g.add("nature")
        if i in Motifs.stage:
            g.add("stage")
        if i in Motifs.music:
            g.add("music")
        if i in Motifs.modern:
            g.add("modern")
        if i in Motifs.classic:
            g.add("classic")
        if i in Motifs.vn:
            g |= {"vn", "east"}
        if i in Motifs.cn:
            g |= {"cn", "east"}
        if i in Motifs.tibet:
            g |= {"tibet", "east"}
        return g

    @staticmethod
    def of(key):
        key = str(key)
        if key.startswith("m:"):
            try:
                i = int(key[2:])
            except ValueError:
                return None
            return i if 0 <= i < len(Motifs.list) else None
        if key == "pack":
            p = int(Prefs.pack.value)
            return p if 0 <= p < len(Motifs.list) else None
        return None

    @staticmethod
    def ofInt(v):
        v = int(v)
        if v >= 100:
            i = v - 100
            return i if i < len(Motifs.list) else None
        if v == -1:
            p = int(Prefs.pack.value)
            return p if 0 <= p < len(Motifs.list) else None
        return None

    @staticmethod
    def skinMotif(key=None):
        return Motifs.of(Prefs.skin.value if key is None else key)

    @staticmethod
    def buttonStyle(v=None):
        v = Prefs.btnStyle.value if v is None else v
        i = Motifs.ofInt(v)
        return (clamp(int(v), 0, 12), None) if i is None else (Motifs.list[i].btn, Motifs.list[i])

    @staticmethod
    def edgeStyle(v=None):
        v = Prefs.edgeEffect.value if v is None else v
        i = Motifs.ofInt(v)
        return (clamp(int(v), 0, len(EdgeEffects.names) - 1), None) if i is None else (Motifs.list[i].edge, Motifs.list[i])

    @staticmethod
    def lighten(c, k):
        return Color(c.r + (1 - c.r) * k, c.g + (1 - c.g) * k, c.b + (1 - c.b) * k, 1.0)

    @staticmethod
    def theme(i):
        mo = Motifs.list[i]
        c = mo.colours
        on = ON_ORANGE if lum(c[1]) > 0.5 else Color.White
        if mo.light:
            return JTheme("m:%d" % i, Motifs.name(i), Motifs.name(i), c[0], c[0].darken(0.9), Color(0xFFFFFFFF), Color(0xFF231A14),
                          c[3].copy(alpha=0.8), c[1], on, Color(0xFFFFFFFF), light=True)
        return JTheme("m:%d" % i, Motifs.name(i), Motifs.name(i), c[0].darken(0.75), c[0].darken(0.25), Color(0x1FFFFFFF),
                      Color.White, Motifs.lighten(c[2], 0.45), c[1], on, c[0].darken(0.18))

    @staticmethod
    def applyPack(i):
        Prefs.pack.value = i
        Prefs.theme.value = "pack"
        Prefs.skin.value = "pack"
        Prefs.btnStyle.value = -1
        Prefs.btnColour.value = "pack"
        Prefs.edgeEffect.value = -1
        Prefs.edgeAuto.value = False
        Prefs.edgeRandom.value = False
        Prefs.barColour.value = "pack"
        Prefs.viz.value = i
        Prefs.vizAuto.value = False

    @staticmethod
    def _set(s):
        return [x for x in s.split("\n") if x.strip()]

    @staticmethod
    def isFav(cat, id_):
        return "%s|%s" % (cat, id_) in Motifs._set(Prefs.favStyles.value)

    @staticmethod
    def toggleFav(cat, id_):
        lst = Motifs._set(Prefs.favStyles.value)
        k = "%s|%s" % (cat, id_)
        if k in lst:
            lst.remove(k)
            now = False
        else:
            lst.append(k)
            now = True
        Prefs.favStyles.value = "\n".join(lst)
        return now

    @staticmethod
    def favs(cat):
        return [x.split("|", 1)[1] for x in Motifs._set(Prefs.favStyles.value) if x.startswith(cat + "|")]

    @staticmethod
    def recent(cat):
        return [x.split("|", 1)[1] for x in Motifs._set(Prefs.recentStyles.value) if x.startswith(cat + "|")]

    @staticmethod
    def addRecent(cat, id_):
        k = "%s|%s" % (cat, id_)
        lst = [k] + [x for x in Motifs._set(Prefs.recentStyles.value) if x != k]
        mine = [x for x in lst if x.startswith(cat + "|")][:5]
        other = [x for x in lst if not x.startswith(cat + "|")]
        Prefs.recentStyles.value = "\n".join((mine + other)[:60])

    @staticmethod
    def filterName(k):
        for key, (en, vi) in Motifs.filters:
            if key == k:
                return t(en, vi)
        return k


class SkinStyle:
    def __init__(self, text, muted, button, border, radius=None):
        self.text, self.muted, self.button, self.border, self.radius = text, muted, button, border, radius


def motifSkinStyle(i):
    mo = Motifs.list[i]
    if mo.light:
        return SkinStyle(Color(0xFF231A14), Color(0xFF4A3A30), Color(0xFF231A14), mo.colours[3], 20)
    return SkinStyle(Color.White, Motifs.lighten(mo.colours[2], 0.6), Color.White, mo.accent.copy(alpha=0.8), None)


def paintMotifSkin(ds, i, clock):
    """Paints a theme skin: the theme's colours plus its pattern."""
    mo = Motifs.list[i]
    c = mo.colours
    w, h = ds.size.width, ds.size.height
    if mo.light:
        ds.drawRect(Brush.verticalGradient([c[0], c[0].darken(0.92)]))
    else:
        ds.drawRect(Brush.linearGradient([c[0].darken(0.95), c[0].darken(0.55), c[0].darken(0.8)], Offset(0, 0), Offset(w, h)))
    ink = c[1].copy(alpha=0.18 if mo.light else 0.22)
    ink2 = c[2].copy(alpha=0.25 if mo.light else 0.16)
    pat = mo.pattern
    if pat == 0:
        for k in range(4):
            p = Path()
            for x in range(41):
                xx = w * x / 40
                yy = h * (0.3 + k * 0.15) + sin(xx * 0.03 + k + clock * 0.3) * h * 0.08
                p.moveTo(xx, yy) if x == 0 else p.lineTo(xx, yy)
            ds.drawPath(p, ink if k % 2 == 0 else ink2, style=Stroke(2.5))
    elif pat == 1:
        y, r = 8.0, 0
        while y < h:
            x = 8.0 if r % 2 == 0 else 20.0
            while x < w:
                ds.drawCircle(ink2 if (int(x) // 24 + r) % 3 == 0 else ink, 3, Offset(x, y))
                x += 24
            y += 14
            r += 1
    elif pat == 2:
        x = -h
        while x < w:
            ds.drawLine(ink, Offset(x, h), Offset(x + h, 0), 6)
            ds.drawLine(ink2, Offset(x + 12, h), Offset(x + 12 + h, 0), 2)
            x += 26
    elif pat == 3:
        for k in range(1, 7):
            ds.drawCircle(ink if k % 2 == 0 else ink2, h * 0.25 * k, Offset(w * 0.85, h * 0.5), style=Stroke(2))
    elif pat == 4:
        r = random.Random(i)
        for it in range(40):
            a = 0.15 + r.random() * 0.4 * (0.6 + 0.4 * sin(clock + it))
            ds.drawCircle(Color.White.copy(alpha=a), 0.8 + r.random() * 1.6, Offset(r.random() * w, r.random() * h))
    elif pat == 5:
        for k in range(6):
            cx = w * (0.1 + k * 0.17)
            cy = h * (0.3 if k % 2 == 0 else 0.7)
            rr = h * 0.14
            for pp in range(5):
                a = pp * 2 * PI / 5
                ds.drawCircle(ink, rr * 0.55, Offset(cx + cos(a) * rr * 0.6, cy + sin(a) * rr * 0.6))
            ds.drawCircle(ink2, rr * 0.25, Offset(cx, cy))
    elif pat == 6:
        x = 0.0
        while x < w:
            ds.drawLine(ink, Offset(x, 0), Offset(x, h), 1)
            x += 16
        y = 0.0
        while y < h:
            ds.drawLine(ink, Offset(0, y), Offset(w, y), 1)
            y += 16
    elif pat == 7:
        for k in range(5):
            cx, cy = w * (0.1 + k * 0.2), h * 0.5
            p = Path()
            for tt in range(31):
                a = tt / 30 * 2 * PI * 1.4
                rr = h * 0.35 * (1 - tt / 36)
                px, py = cx + cos(a) * rr, cy + sin(a) * rr * 0.8
                p.moveTo(px, py) if tt == 0 else p.lineTo(px, py)
            ds.drawPath(p, ink if k % 2 == 0 else ink2, style=Stroke(2))
    elif pat == 9:
        for k in range(16):
            p = Path()
            y0 = h * k / 16
            for x in range(31):
                xx = w * x / 30
                yy = y0 + sin(xx * 0.015 + k * 1.7) * h * 0.05
                p.moveTo(xx, yy) if x == 0 else p.lineTo(xx, yy)
            ds.drawPath(p, ink, style=Stroke(1.2))
    elif pat == 10:
        for layer in range(2):
            p = Path().moveTo(0, h)
            for k in range(9):
                p.lineTo(w * k / 8, h * (0.45 + layer * 0.2) + (h * 0.2 if k % 2 == 0 else 0))
            p.lineTo(w, h).close()
            ds.drawPath(p, ink2 if layer == 0 else ink)
    elif pat == 11:
        with ds.rotate(clock * 4, Offset(w * 0.9, h * 0.5)):
            for k in range(18):
                a = k * 20 * PI / 180
                ds.drawLine(ink if k % 2 == 0 else ink2, Offset(w * 0.9, h * 0.5), Offset(w * 0.9 + cos(a) * w, h * 0.5 + sin(a) * w), 5)
    ds.drawRect(Brush.verticalGradient([Color(0x30FFFFFF), Color.Transparent], 0, h * 0.45))
