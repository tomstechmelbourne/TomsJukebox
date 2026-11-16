"""The 20 skins of the player (same as Android ui/SkinArt.kt), plus the 70 theme skins from Bộ Chủ Đề."""
import math
import random

from .ds import (Brush, Color, CornerRadius, Offset, Path, Size, Stroke, clamp, cos, dash, sin)
from .prefs import Prefs
from .state import Core
from .themes import Motifs, SkinStyle, motifSkinStyle, paintMotifSkin, t


class PillColours:
    list = [
        ("Warm Brown", "Nâu Ấm", [0xFF3A3330, 0xFF1F1B19]), ("From Album Cover", "Theo Ảnh Bìa", [0, 0]),
        ("Jet Black", "Đen Tuyền", [0xFF1C1C1C, 0xFF050505]), ("Navy", "Xanh Navy", [0xFF1E4A63, 0xFF0D2C40]),
        ("Plum", "Tím Than", [0xFF3B2A63, 0xFF1C1236]), ("Wine Red", "Đỏ Rượu Vang", [0xFF5A1A2A, 0xFF2A0A12]),
        ("Moss Green", "Xanh Rêu", [0xFF2F4A2A, 0xFF15241A]), ("Night Sea", "Xanh Biển Đêm", [0xFF123B5A, 0xFF061A2C]),
        ("Peach", "Hồng Đào", [0xFFB5536F, 0xFF6E2A3E]), ("Desert Sand", "Vàng Cát", [0xFF8A6A3A, 0xFF4A3618]),
        ("Silver Grey", "Xám Bạc", [0xFF6B7178, 0xFF3A3F45]), ("See-Through", "Trong Suốt", [0x26FFFFFF, 0x14FFFFFF]),
    ]

    @staticmethod
    def name(i):
        return t(*PillColours.list[i][:2]) if 0 <= i < len(PillColours.list) else ""

    @staticmethod
    def colours(i):
        e = PillColours.list[i] if 0 <= i < len(PillColours.list) else PillColours.list[0]
        if i == 1:
            c = Core.palette[0]
            return [c.darken(0.55), c.darken(0.25)]
        return [Color(x) for x in e[2]]


class SkinList:
    keys = ["pill", "xp", "metal", "wood", "glass", "slim", "ipod", "liquid", "grain", "marble", "clear", "lacquer",
            "ceramic", "carbon", "leather", "alu", "gold", "neon", "cassette", "tinted"]
    woodTypes = [("Walnut", "Óc Chó"), ("Oak", "Sồi"), ("Mahogany", "Gụ")]
    marbleTypes = [("White", "Trắng Vân Xám"), ("Black Gold", "Đen Vân Vàng"), ("Jade", "Xanh Ngọc")]
    _names = {
        "pill": ("Pill (Tom's Dock)", "Viên Thuốc (Tom's Dock)"), "xp": ("XP Classic", "XP Cổ Điển"),
        "metal": ("Classic Metal", "Cổ Điển Kim Loại"), "wood": ("Wooden Amplifier", "Ampli Gỗ"), "glass": ("Frosted Glass", "Kính Mờ"),
        "slim": ("Ultra Slim", "Siêu Gọn"), "ipod": ("Classic iPod Style", "iPod Cổ Điển"), "liquid": ("Liquid Glass", "Kính Lỏng"),
        "grain": ("Wood Grain", "Vân Gỗ"), "marble": ("Marble", "Cẩm Thạch"), "clear": ("Transparent", "Trong Suốt"),
        "lacquer": ("Lacquer", "Sơn Mài"), "ceramic": ("Blue Ceramic", "Gốm Men Lam"), "carbon": ("Carbon Fibre", "Sợi Carbon"),
        "leather": ("Leather", "Da Thuộc"), "alu": ("Brushed Aluminium", "Nhôm Xước"), "gold": ("Gold", "Vàng Gold"),
        "neon": ("Night Neon", "Neon Đêm"), "cassette": ("Cassette", "Băng Cassette"), "tinted": ("Tinted Glass", "Kính Mờ Màu"),
    }

    @staticmethod
    def name(k):
        if k in SkinList._names:
            return t(*SkinList._names[k])
        i = Motifs.of(k)
        if i is not None:
            return Motifs.name(i)
        return k


W = Color.White
SUBW = Color(0xFFE8DCD0)
INK = Color(0xFF1E2333)
INKSUB = Color(0xFF4A5068)


def _ss(text, sub, btn, border, radius, waves=True):
    s = SkinStyle(text, sub, btn, border, radius)
    s.sub = sub
    s.waves = waves
    return s


def skinStyle(key=None):
    key = Prefs.skin.value if key is None else key
    mi = Motifs.skinMotif(key)
    if mi is not None:
        s = motifSkinStyle(mi)
        s.sub = s.muted
        s.btn = s.button
        s.waves = True
        return s
    C = Color
    if key == "xp":
        xc = Prefs.xpColour.value
        if xc == "silver":
            return _ss(INK, INKSUB, C(0xFF2B3550), C(0xFF8D90A6), 18)
        if xc == "olive":
            return _ss(W, C(0xFFF1F6E2), W, C(0xFF3F5424), 18)
        return _ss(W, C(0xFFDCE8FF), W, C(0xFF0B2F7A), 18)
    table = {
        "metal": (W, C(0xFFE6EAEE), W, C(0xFF2A2F35), 14), "wood": (C(0xFFFCE9C8), C(0xFFE2C79A), C(0xFFFCE9C8), C(0xFF2A190B), 16),
        "glass": (W, C(0xFFE6F2F7), W, C(0x66FFFFFF), None), "liquid": (W, C(0xFFEFF6FA), W, C(0x99FFFFFF), None),
        "clear": (W, C(0xFFF2F2F2), W, C(0x66FFFFFF), None), "lacquer": (C(0xFFF7E3A1), C(0xFFD9BE76), C(0xFFF7E3A1), C(0xFFC9A227), 18),
        "carbon": (W, C(0xFFCDD3D8), W, C(0xFF3A3F45), 16), "leather": (C(0xFFF6E7D2), C(0xFFE2C8A6), C(0xFFF6E7D2), C(0xFF2A160A), 20),
        "alu": (INK, INKSUB, C(0xFF2B3036), C(0xFF7F868E), 14), "neon": (W, C(0xFFFFC7EC), C(0xFF7DF9FF), C(0xFFFF3DCB), None),
        "cassette": (C(0xFFF2E6C8), C(0xFFCBBF9F), C(0xFFF2E6C8), C(0xFF111111), 12), "tinted": (W, C(0xFFF0F0F0), W, C(0x66FFFFFF), None),
    }
    if key in table:
        return _ss(*table[key])
    if key == "ipod":
        return _ss(C(0xFF111111), C(0xFF555555), C(0xFF222222), C(0xFFB8BCC2), 22, waves=False)
    if key == "grain":
        if Prefs.woodType.value == 1:
            return _ss(C(0xFF2A1A08), C(0xFF5A3E1E), C(0xFF2A1A08), C(0xFF7A5A30), 18)
        return _ss(C(0xFFFCEFD8), C(0xFFE8CFA8), C(0xFFFCEFD8), C(0xFF2A160A), 18)
    if key == "marble":
        mt = Prefs.marbleType.value
        if mt == 0:
            return _ss(INK, INKSUB, C(0xFF2A2F3A), C(0xFFBFC3C8), 20)
        return _ss(W, C(0xFFEDE6D2), W, C(0xFFC9A227) if mt == 1 else C(0xFF0E3B30), 20)
    if key == "ceramic":
        return _ss(C(0xFF15346E), C(0xFF3B5A94), C(0xFF15346E), C(0xFF1F4FA0), 22, waves=False)
    if key == "gold":
        return _ss(C(0xFF3A2A05), C(0xFF5E4710), C(0xFF3A2A05), C(0xFF9C7A1E), 20, waves=False)
    return _ss(W, SUBW, W, C(0x30FFFFFF), None)


def paintSkin(ds, clock, tilt=0.0, key=None):
    """Paints the player background for the chosen skin."""
    key = Prefs.skin.value if key is None else key
    w, h = ds.size.width, ds.size.height

    def vg(*c):
        ds.drawRect(Brush.verticalGradient([Color(x) for x in c]))

    mi = Motifs.skinMotif(key)
    if mi is not None:
        paintMotifSkin(ds, mi, clock)
        return
    if key == "xp":
        xc = Prefs.xpColour.value
        if xc == "silver":
            vg(0xFFF6F6FA, 0xFFDADBE5, 0xFFB4B6C6)
        elif xc == "olive":
            vg(0xFFC9D8A0, 0xFF93A867, 0xFF5B7638)
        else:
            vg(0xFF4A8BF0, 0xFF2159CC, 0xFF0F3C9E)
        ds.drawRoundRect(Brush.verticalGradient([Color(0x66FFFFFF), Color(0x10FFFFFF)], 0, h / 2), Offset(6, 3), Size(w - 12, h / 2 - 3), CornerRadius(h / 3))
    elif key == "metal":
        vg(0xFFA5ADB7, 0xFF656D78, 0xFF3A4048, 0xFF727A85)
        for y in range(0, int(h), 3):
            ds.drawLine(Color(0x0FFFFFFF), Offset(0, y), Offset(w, y))
    elif key == "wood":
        vg(0xFF8B5A2B, 0xFF5C3A1A, 0xFF3E2612)
    elif key == "glass":
        vg(0x33FFFFFF, 0x1AFFFFFF)
    elif key == "ipod":
        vg(0xFFFAFAFA, 0xFFE1E3E7)
    elif key == "liquid":
        vg(0x2EFFFFFF, 0x14FFFFFF, 0x24FFFFFF)
        ds.drawRect(Brush.verticalGradient([Color(0x55FFFFFF), Color.Transparent], 0, h * 0.45))
        x = (tilt * 0.5 + 0.5) * w + sin(clock * 0.4) * w * 0.05
        ds.drawRect(Brush.horizontalGradient([Color.Transparent, Color(0x40FFFFFF), Color.Transparent], x - w * 0.15, x + w * 0.15))
    elif key == "grain":
        wt = clamp(int(Prefs.woodType.value), 0, 2)
        base = [[0xFF6B4226, 0xFF3E2414], [0xFFD9B27C, 0xFFAC8452], [0xFF8A3624, 0xFF4E1A10]][wt]
        ds.drawRect(Brush.verticalGradient([Color(x) for x in base]))
        line = Color(0x26603A10) if wt == 1 else Color(0x33000000)
        for i in range(26):
            p = Path()
            y0 = h * i / 26
            for k in range(41):
                x = w * k / 40
                y = y0 + sin(x * 0.012 + i * 1.7) * h * 0.04 + sin(x * 0.045 + i) * h * 0.01
                p.moveTo(x, y) if k == 0 else p.lineTo(x, y)
            ds.drawPath(p, line, style=Stroke(1.2 + (i % 3)))
        ds.drawRoundRect(Brush.verticalGradient([Color(0x33FFFFFF), Color.Transparent], 0, h * 0.4), cornerRadius=CornerRadius(h / 3))
    elif key == "marble":
        mt = clamp(int(Prefs.marbleType.value), 0, 2)
        base = [[0xFFF4F2EE, 0xFFE2DFD9], [0xFF1A1A1A, 0xFF0B0B0B], [0xFF1F6B5A, 0xFF0F3F35]][mt]
        ds.drawRect(Brush.linearGradient([Color(x) for x in base]))
        vein = [Color(0x4D7A7E86), Color(0x99C9A227), Color(0x66E8F5EF)][mt]
        r = random.Random(7)
        for _ in range(7):
            p = Path()
            x = r.random() * w * 0.2
            y = r.random() * h
            p.moveTo(x, y)
            for _ in range(6):
                nx = x + w * (0.12 + r.random() * 0.15)
                ny = clamp(y + (r.random() - 0.5) * h * 0.8, 0, h)
                p.quadraticTo((x + nx) / 2, y + (r.random() - 0.5) * h, nx, ny)
                x, y = nx, ny
            ds.drawPath(p, vein, style=Stroke(0.8 + r.random() * 2.2))
        ds.drawRect(Brush.verticalGradient([Color(0x30FFFFFF), Color.Transparent], 0, h * 0.5))
    elif key == "clear":
        vg(0x0DFFFFFF, 0x08FFFFFF)
    elif key == "lacquer":
        vg(0xFF1A0F08, 0xFF0B0B0B, 0xFF150A05)
        ds.drawRect(Brush.verticalGradient([Color(0x30FFFFFF), Color.Transparent], 0, h * 0.35))
        gold = Color(0xAAC9A227)
        for k in range(3):
            ds.drawArc(gold, 180 + k * 25, 70, False, Offset(w - h * (1.1 + k * 0.25), -h * 0.3), Size(h * 1.2, h * 1.2), style=Stroke(1.5))
    elif key == "ceramic":
        vg(0xFFF8F4EA, 0xFFEDE6D6)
        blue = Color(0xFF1F4FA0)
        ds.drawRoundRect(blue, Offset(5, 5), Size(w - 10, h - 10), CornerRadius(h / 4), style=Stroke(2))
        x = 18.0
        while x < w - 18:
            ds.drawCircle(blue.copy(alpha=0.55), 3, Offset(x, 11))
            ds.drawCircle(blue.copy(alpha=0.55), 3, Offset(x, h - 11))
            x += 16
        for i in range(3):
            p = Path()
            for k in range(31):
                xx = w * k / 30
                yy = h * (0.35 + i * 0.15) + sin(xx * 0.05 + i) * 4
                p.moveTo(xx, yy) if k == 0 else p.lineTo(xx, yy)
            ds.drawPath(p, blue.copy(alpha=0.12), style=Stroke(2))
    elif key == "carbon":
        vg(0xFF26282B, 0xFF141516)
        c = 8 * Core.dpr
        y, row = 0.0, 0
        while y < h:
            x = 0.0 if row % 2 == 0 else c / 2
            while x < w:
                ds.drawRect(Brush.linearGradient([Color(0x22FFFFFF), Color(0x05FFFFFF)], Offset(x, y), Offset(x + c / 2, y + c / 2)), Offset(x, y), Size(c / 2, c / 2))
                x += c
            y += c / 2
            row += 1
        ds.drawRect(Brush.verticalGradient([Color(0x22FFFFFF), Color.Transparent], 0, h * 0.4))
    elif key == "leather":
        vg(0xFF7A4A2A, 0xFF4A2A16)
        r = random.Random(3)
        for _ in range(500):
            ds.drawCircle(Color.Black.copy(alpha=0.07), 0.8 + r.random() * 1.4, Offset(r.random() * w, r.random() * h))
        ds.drawRoundRect(Color(0xB3E8C79A), Offset(7, 7), Size(w - 14, h - 14), CornerRadius(h / 3), style=Stroke(1.6, pathEffect=dash([9, 6])))
    elif key == "alu":
        vg(0xFFD6DADF, 0xFFA8AEB5, 0xFFC4C9CE)
        r = random.Random(5)
        for y in range(0, int(h), 2):
            ds.drawLine(Color.White.copy(alpha=r.random() * 0.18), Offset(0, y), Offset(w, y))
    elif key == "gold":
        ds.drawRect(Brush.linearGradient([Color(0xFFF7E08A), Color(0xFFD4AF37), Color(0xFFA67C1F), Color(0xFFF3D77A)], Offset(0, 0), Offset(w, h)))
        ds.drawRect(Brush.verticalGradient([Color(0x55FFFFFF), Color.Transparent], 0, h * 0.45))
    elif key == "neon":
        vg(0xFF0E0A1A, 0xFF05030C)
    elif key == "cassette":
        vg(0xFF2E2E2E, 0xFF161616)
        ds.drawRect(Color(0xFFF2E6C8).copy(alpha=0.12), Offset(0, h * 0.06), Size(w, h * 0.1))
        spin = clock * 120 if Core.playing else 0
        for cx in (w * 0.08, w * 0.92):
            c = Offset(cx, h * 0.5)
            rr = h * 0.32
            ds.drawCircle(Color(0x33FFFFFF), rr, c, style=Stroke(2))
            ds.drawCircle(Color(0x22FFFFFF), rr * 0.35, c)
            with ds.rotate(spin, c):
                for k in range(6):
                    a = math.radians(k * 60)
                    ds.drawLine(Color(0x44FFFFFF), c, Offset(c.x + cos(a) * rr * 0.8, c.y + sin(a) * rr * 0.8), 2)
    elif key == "tinted":
        c = Core.palette[0]
        ds.drawRect(Brush.verticalGradient([c.copy(alpha=0.45), c.darken(0.4).copy(alpha=0.55)]))
    else:
        ds.drawRect(Brush.verticalGradient(PillColours.colours(int(Prefs.pillColour.value))))


def paintSkinBorder(ds, radiusPx, border, key=None):
    key = Prefs.skin.value if key is None else key
    w, h = ds.size.width, ds.size.height
    if key == "neon":
        for wd, a in ((10, 0.15), (5, 0.35), (2, 1.0)):
            ds.drawRoundRect(Brush.horizontalGradient([Color(0xFFFF3DCB), Color(0xFF7DF9FF)]), Offset(2, 2), Size(w - 4, h - 4), CornerRadius(radiusPx), alpha=a, style=Stroke(wd))
    elif key in ("lacquer", "gold") or Motifs.skinMotif(key) is not None:
        ds.drawRoundRect(border, Offset(1.5, 1.5), Size(w - 3, h - 3), CornerRadius(radiusPx), style=Stroke(3))
    else:
        ds.drawRoundRect(border, Offset(0.5, 0.5), Size(w - 1, h - 1), CornerRadius(radiusPx), style=Stroke(1.2))
