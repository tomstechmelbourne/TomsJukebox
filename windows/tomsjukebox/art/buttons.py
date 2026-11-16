"""The 13 button sets and the 15 record-button designs (Android ui/ButtonArt.kt and ui/RecArt.kt), drawn with QPainter."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPainterPath,
                           QPainterPathStroker, QPen, QRadialGradient)

from .prefs import Prefs
from .state import Core
from .themes import Motifs, Themes, t

PLAY, PAUSE, PREV, NEXT, REC, REC_STOP = 0, 1, 2, 3, 4, 5


def _qc(v, alpha=None):
    if isinstance(v, QColor):
        c = QColor(v)
    elif isinstance(v, int):
        v &= 0xFFFFFFFF
        if v <= 0xFFFFFF:
            v |= 0xFF000000
        c = QColor((v >> 16) & 255, (v >> 8) & 255, v & 255, (v >> 24) & 255)
    elif hasattr(v, "q"):
        c = v.q()
    else:
        c = QColor(v)
    if alpha is not None:
        c.setAlpha(int(alpha))
    return c


class ButtonArt:
    names = [("Tom's Dock", "Tom's Dock"), ("Thin Line", "Nét Mảnh"), ("Solid Circle", "Tròn Đặc"), ("Ring", "Vòng Viền"),
             ("Rounded Square", "Vuông Bo Góc"), ("Double Arrows", "Mũi Tên Đôi"), ("Neon", "Neon"), ("Glass Bubble", "Kính Bong Bóng"),
             ("3D Metal", "Kim Loại 3D"), ("Cassette Keys", "Phím Cassette"), ("Hand Drawn", "Vẽ Tay"), ("Pixel 8-bit", "Pixel 8-bit"),
             ("Chubby", "Bo Tròn Mập")]

    pixels = {
        PLAY: ["..#.....", "..##....", "..###...", "..####..", "..####..", "..###...", "..##....", "..#....."],
        PAUSE: ["........", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", "........"],
        PREV: ["........", ".#...##.", ".#..###.", ".#.####.", ".#.####.", ".#..###.", ".#...##.", "........"],
        NEXT: ["........", ".##...#.", ".###..#.", ".####.#.", ".####.#.", ".###..#.", ".##...#.", "........"],
        REC: ["........", "..####..", ".######.", ".######.", ".######.", ".######.", "..####..", "........"],
        REC_STOP: ["........", "........", "..####..", "..####..", "..####..", "..####..", "........", "........"],
    }

    @staticmethod
    def name(i):
        return t(*ButtonArt.names[i]) if 0 <= i < len(ButtonArt.names) else ""

    @staticmethod
    def glyph(kind, style, x, y, s):
        p = QPainterPath()
        p.setFillRule(Qt.WindingFill)

        def pt(px, py):
            return QPointF(x + px * s, y + py * s)

        def tri(a, b, c):
            p.moveTo(a)
            p.lineTo(b)
            p.lineTo(c)
            p.closeSubpath()

        def rect(l, tp, r, b):
            p.addRoundedRect(QRectF(x + l * s, y + tp * s, (r - l) * s, (b - tp) * s), s * 0.04, s * 0.04)

        if kind == PLAY:
            tri(pt(0.3, 0.2), pt(0.84, 0.5), pt(0.3, 0.8))
        elif kind == PAUSE:
            rect(0.26, 0.2, 0.42, 0.8)
            rect(0.58, 0.2, 0.74, 0.8)
        elif kind == PREV:
            if style == 5:
                tri(pt(0.52, 0.24), pt(0.14, 0.5), pt(0.52, 0.76))
                tri(pt(0.88, 0.24), pt(0.5, 0.5), pt(0.88, 0.76))
            else:
                rect(0.18, 0.22, 0.29, 0.78)
                tri(pt(0.8, 0.22), pt(0.34, 0.5), pt(0.8, 0.78))
        elif kind == NEXT:
            if style == 5:
                tri(pt(0.48, 0.24), pt(0.86, 0.5), pt(0.48, 0.76))
                tri(pt(0.12, 0.24), pt(0.5, 0.5), pt(0.12, 0.76))
            else:
                rect(0.71, 0.22, 0.82, 0.78)
                tri(pt(0.2, 0.22), pt(0.66, 0.5), pt(0.2, 0.78))
        elif kind == REC:
            p.addEllipse(QPointF(x + 0.5 * s, y + 0.5 * s), 0.27 * s, 0.27 * s)
        else:
            rect(0.3, 0.3, 0.7, 0.7)
        return p

    @staticmethod
    def draw(c: QPainter, kind, styleIn, size, color, pressed=False, glow=0.0):
        c.save()
        c.setRenderHint(QPainter.Antialiasing, True)
        try:
            if kind in (REC, REC_STOP) and int(Prefs.recStyle.value) > 0:
                RecArt.draw(c, kind == REC_STOP, int(Prefs.recStyle.value), size, RecArt.colour(), pressed)
                return
            style, deco = Motifs.buttonStyle(styleIn)
            if deco is not None:
                cs = deco.c
                g = QConicalGradient(size / 2, size / 2, 0)
                for i, v in enumerate((cs[1], cs[2], cs[3], cs[1])):
                    g.setColorAt(i / 3, _qc(v))
                c.setPen(QPen(QBrush(g), size * 0.06))
                c.setBrush(Qt.NoBrush)
                c.drawEllipse(QPointF(size / 2, size / 2), size * 0.47, size * 0.47)
                rg = QRadialGradient(size / 2, size / 2, size * 0.47)
                rg.setColorAt(0, _qc(cs[1], 0x40))
                rg.setColorAt(1, _qc(cs[2], 0x10))
                c.setPen(Qt.NoPen)
                c.setBrush(QBrush(rg))
                c.drawEllipse(QPointF(size / 2, size / 2), size * 0.44, size * 0.44)
            col = _qc(RecArt.colour()) if kind in (REC, REC_STOP) else _qc(color)
            cx = cy = size / 2
            dark = _qc(0xFF1B1F24)
            inner = size * 0.58
            ix = (size - inner) / 2

            def fillGlyph(g, paintCol, rnd=0.05):
                pen = QPen(paintCol, size * rnd)
                pen.setJoinStyle(Qt.RoundJoin)
                c.setPen(pen)
                c.setBrush(paintCol)
                c.drawPath(g)

            def fill(col_):
                c.setPen(Qt.NoPen)
                c.setBrush(col_)

            def stroke(col_, w):
                pen = QPen(col_, w)
                pen.setJoinStyle(Qt.RoundJoin)
                c.setPen(pen)
                c.setBrush(Qt.NoBrush)

            if style == 1:
                stroke(col, size * 0.045)
                c.drawPath(ButtonArt.glyph(kind, style, size * 0.12, size * 0.12, size * 0.76))
            elif style == 2:
                fill(col)
                c.drawEllipse(QPointF(cx, cy), size * 0.47, size * 0.47)
                fillGlyph(ButtonArt.glyph(kind, style, ix, ix, inner), QColor(255, 255, 255) if kind >= REC else dark)
            elif style == 3:
                stroke(col, size * 0.05)
                c.drawEllipse(QPointF(cx, cy), size * 0.44, size * 0.44)
                fillGlyph(ButtonArt.glyph(kind, style, ix, ix, inner), col)
            elif style == 4:
                cc = QColor(col)
                cc.setAlpha(0x33)
                fill(cc)
                c.drawRoundedRect(QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92), size * 0.24, size * 0.24)
                fillGlyph(ButtonArt.glyph(kind, style, ix, ix, inner), col)
            elif style == 6:
                g = ButtonArt.glyph(kind, style, size * 0.14, size * 0.14, size * 0.72)
                a = min(1.0, max(0.0, 0.35 + glow * 0.5))
                for w, al in ((0.22, 0.12 * a), (0.14, 0.25 * a), (0.07, 0.6)):
                    cc = QColor(col)
                    cc.setAlphaF(al)
                    stroke(cc, size * w)
                    c.drawPath(g)
                stroke(QColor(255, 255, 255, 230), size * 0.025)
                c.drawPath(g)
            elif style == 7:
                rg = QRadialGradient(cx * 0.8, cy * 0.7, size * 0.6)
                rg.setColorAt(0, QColor(255, 255, 255, 0x66))
                rg.setColorAt(0.5, QColor(255, 255, 255, 0x22))
                rg.setColorAt(1, QColor(255, 255, 255, 0x10))
                c.setPen(Qt.NoPen)
                c.setBrush(QBrush(rg))
                c.drawEllipse(QPointF(cx, cy), size * 0.46, size * 0.46)
                stroke(QColor(255, 255, 255, 0x88), size * 0.02)
                c.drawEllipse(QPointF(cx, cy), size * 0.46, size * 0.46)
                fill(QColor(255, 255, 255, 0x55))
                c.drawEllipse(QRectF(size * 0.26, size * 0.1, size * 0.4, size * 0.2))
                fillGlyph(ButtonArt.glyph(kind, style, ix, ix, inner), col)
            elif style == 8:
                lg = QLinearGradient(0, 0, 0, size)
                lg.setColorAt(0, _qc(0xFFF2F4F7))
                lg.setColorAt(0.5, _qc(0xFFA9B0B8))
                lg.setColorAt(1, _qc(0xFF6E757D))
                c.setPen(Qt.NoPen)
                c.setBrush(QBrush(lg))
                c.drawEllipse(QPointF(cx, cy), size * 0.47, size * 0.47)
                lg2 = QLinearGradient(0, 0, 0, size)
                lg2.setColorAt(0, _qc(0xFF8C939B))
                lg2.setColorAt(1, _qc(0xFFE6E9ED))
                c.setBrush(QBrush(lg2))
                c.drawEllipse(QPointF(cx, cy), size * 0.39, size * 0.39)
                fillGlyph(ButtonArt.glyph(kind, style, ix, ix, inner), _qc(0xFFD93030) if kind >= REC else _qc(0xFF2E3338))
            elif style == 9:
                dy = size * 0.05 if pressed else 0
                fill(_qc(0xFF2A2A2A))
                c.drawRoundedRect(QRectF(size * 0.06, size * 0.14, size * 0.88, size * 0.78), size * 0.08, size * 0.08)
                lg = QLinearGradient(0, size * 0.1, 0, size * 0.85)
                lg.setColorAt(0, _qc(0xFFF4F1EA))
                lg.setColorAt(1, _qc(0xFFCFC8BA))
                c.setBrush(QBrush(lg))
                c.drawRoundedRect(QRectF(size * 0.08, size * 0.08 + dy, size * 0.84, size * 0.76), size * 0.07, size * 0.07)
                fillGlyph(ButtonArt.glyph(kind, style, size * 0.25, size * 0.21 + dy, size * 0.5), _qc(0xFFD93030) if kind >= REC else _qc(0xFF2B2B2B))
            elif style == 10:
                g = ButtonArt.glyph(kind, style, size * 0.12, size * 0.12, size * 0.76)
                out = QPainterPath()
                for poly in g.toSubpathPolygons():
                    pts = list(poly)
                    if len(pts) < 2:
                        continue
                    first = True
                    for i in range(len(pts)):
                        a, b = pts[i], pts[(i + 1) % len(pts)]
                        seglen = math.hypot(b.x() - a.x(), b.y() - a.y())
                        steps = max(1, int(seglen / (size * 0.03)))
                        for k in range(steps):
                            f = k / steps
                            x = a.x() + (b.x() - a.x()) * f
                            y = a.y() + (b.y() - a.y()) * f
                            j = math.sin(i * 1.7 + k * 0.9 + x * 0.3) * size * 0.018
                            if first:
                                out.moveTo(x + j, y - j)
                                first = False
                            else:
                                out.lineTo(x + j, y - j)
                    out.closeSubpath()
                pen = QPen(col, size * 0.06)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                c.setPen(pen)
                c.setBrush(Qt.NoBrush)
                c.drawPath(out)
            elif style == 11:
                rows = ButtonArt.pixels.get(kind)
                cell = size / 8
                fill(col)
                for r, line in enumerate(rows or []):
                    for k, ch in enumerate(line):
                        if ch == "#":
                            c.drawRect(QRectF(k * cell, r * cell, cell - 1, cell - 1))
            elif style == 12:
                fillGlyph(ButtonArt.glyph(kind, style, size * 0.16, size * 0.16, size * 0.68), col, 0.16)
            else:
                fillGlyph(ButtonArt.glyph(kind, style, size * 0.1, size * 0.1, size * 0.8), col)
        finally:
            c.restore()


class RecArt:
    names = [("Same As Button Set", "Theo Bộ Nút"), ("Classic Red Dot", "Chấm Tròn Cổ Điển"), ("Ring And Dot", "Vòng Viền Có Chấm"),
             ("Microphone", "Micro"), ("Studio Mic", "Micro Phòng Thu"), ("Cassette Reels", "Cuộn Băng Cassette"), ("Vinyl", "Đĩa Than"),
             ("Dot With Sound Waves", "Chấm Có Sóng Âm"), ("REC Badge", "Chữ REC"), ("Glowing Dot", "Chấm Phát Sáng"),
             ("Rounded Square", "Vuông Bo Góc"), ("Heart", "Trái Tim"), ("Star", "Ngôi Sao"), ("Pixel 8-bit", "Pixel 8-bit"),
             ("On-Air Light", "Đèn On Air"), ("Tape Recorder", "Máy Ghi Âm")]
    colours = [("red", "Red", "Đỏ"), ("orange", "Orange", "Cam"), ("pink", "Pink", "Hồng"), ("purple", "Purple", "Tím"),
               ("blue", "Blue", "Xanh Dương"), ("teal", "Teal", "Xanh Ngọc"), ("green", "Green", "Xanh Lá"), ("yellow", "Yellow", "Vàng"),
               ("white", "White", "Trắng"), ("cover", "From Cover", "Theo Ảnh Bìa"), ("theme", "Theme Colour", "Màu Giao Diện"), ("custom", "Custom", "Tự Chọn")]

    @staticmethod
    def name(i):
        return t(*RecArt.names[i]) if 0 <= i < len(RecArt.names) else ""

    @staticmethod
    def colour(k=None):
        k = Prefs.recColour.value if k is None else k
        table = {"orange": 0xFFFF8F1F, "pink": 0xFFFF4F9A, "purple": 0xFFA855F7, "blue": 0xFF3B82F6, "teal": 0xFF14B8A6,
                 "green": 0xFF22C55E, "yellow": 0xFFFACC15, "white": 0xFFFFFFFF}
        if k in table:
            return QColor(_qc(table[k]))
        if k == "cover":
            return Core.palette[0].q()
        if k == "theme":
            return Themes.now().accent.q()
        if k == "custom":
            return _qc(int(Prefs.recCustom.value))
        return _qc(0xFFFF3B3B)

    @staticmethod
    def draw(c: QPainter, stop, design, s, col, pressed=False):
        col = _qc(col)
        white = QColor(255, 255, 255)
        cx = cy = s / 2
        k = 0.92 if pressed else 1.0
        c.save()
        c.setRenderHint(QPainter.Antialiasing, True)
        c.translate(cx, cy)
        c.scale(k, k)
        c.translate(-cx, -cy)

        def fill(q):
            c.setPen(Qt.NoPen)
            c.setBrush(q)

        def stroke(w, q=None):
            pen = QPen(q or col, w)
            pen.setCapStyle(Qt.RoundCap)
            c.setPen(pen)
            c.setBrush(Qt.NoBrush)

        def stopSquare(r, q=None):
            fill(q or white)
            c.drawRoundedRect(QRectF(cx - r, cy - r, 2 * r, 2 * r), r * 0.25, r * 0.25)

        def circle(x, y, r, q):
            fill(q)
            c.drawEllipse(QPointF(x, y), r, r)

        def text(txt, x, y, size, q):
            f = QFont(c.font())
            f.setBold(True)
            f.setPixelSize(max(1, int(size)))
            c.setFont(f)
            c.setPen(q)
            w = c.fontMetrics().horizontalAdvance(txt)
            c.drawText(QPointF(x - w / 2, y), txt)

        if design == 1:
            stopSquare(s * 0.26, col) if stop else circle(cx, cy, s * 0.32, col)
        elif design == 2:
            stroke(s * 0.07)
            c.drawEllipse(QPointF(cx, cy), s * 0.42, s * 0.42)
            stopSquare(s * 0.17, col) if stop else circle(cx, cy, s * 0.24, col)
        elif design in (3, 4):
            w = 0.26 if design == 4 else 0.2
            fill(col)
            c.drawRoundedRect(QRectF(cx - s * w / 2, s * 0.12, s * w, s * 0.46), s * w / 2, s * w / 2)
            if design == 4:
                stroke(s * 0.02, QColor(0, 0, 0, 0x66))
                for i in range(4):
                    c.drawLine(QPointF(cx - s * 0.1, s * (0.2 + i * 0.08)), QPointF(cx + s * 0.1, s * (0.2 + i * 0.08)))
            stroke(s * 0.06)
            c.drawArc(QRectF(cx - s * 0.28, s * 0.22, s * 0.56, s * 0.46), 0, -180 * 16)
            c.drawLine(QPointF(cx, s * 0.68), QPointF(cx, s * 0.84))
            c.drawLine(QPointF(cx - s * 0.16, s * 0.86), QPointF(cx + s * 0.16, s * 0.86))
            if stop:
                circle(s * 0.8, s * 0.2, s * 0.15, white)
                fill(col)
                c.drawRect(QRectF(s * 0.74, s * 0.14, s * 0.12, s * 0.12))
        elif design == 5:
            stroke(s * 0.05)
            c.drawRoundedRect(QRectF(s * 0.06, s * 0.22, s * 0.88, s * 0.56), s * 0.08, s * 0.08)
            for x in (0.32, 0.68):
                circle(s * x, cy, s * 0.13, col)
                circle(s * x, cy, s * 0.05, _qc(0xFF222222))
            stopSquare(s * 0.09) if stop else circle(cx, s * 0.32, s * 0.05, white)
        elif design == 6:
            circle(cx, cy, s * 0.44, _qc(0xFF111111))
            for r in (0.36, 0.3):
                stroke(s * 0.01, QColor(255, 255, 255, 0x33))
                c.drawEllipse(QPointF(cx, cy), s * r, s * r)
            circle(cx, cy, s * 0.18, col)
            stopSquare(s * 0.08) if stop else circle(cx, cy, s * 0.04, _qc(0xFF111111))
        elif design == 7:
            stopSquare(s * 0.16, col) if stop else circle(cx, cy, s * 0.18, col)
            for i in (1, 2):
                r = s * (0.24 + i * 0.1)
                q = QColor(col)
                q.setAlpha(255 - i * 70)
                stroke(s * 0.045, q)
                rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
                c.drawArc(rect, 40 * 16, -80 * 16)
                c.drawArc(rect, -140 * 16, -80 * 16)
        elif design == 8:
            fill(col)
            c.drawRoundedRect(QRectF(s * 0.04, s * 0.28, s * 0.92, s * 0.44), s * 0.1, s * 0.1)
            circle(s * 0.2, cy, s * 0.07, white)
            text("STOP" if stop else "REC", s * 0.58, cy + s * 0.085, s * 0.24, white)
        elif design == 9:
            rg = QRadialGradient(cx, cy, s * 0.48)
            rg.setColorAt(0, col)
            q0 = QColor(col)
            q0.setAlpha(0)
            rg.setColorAt(1, q0)
            c.setPen(Qt.NoPen)
            c.setBrush(QBrush(rg))
            c.drawEllipse(QPointF(cx, cy), s * 0.48, s * 0.48)
            circle(cx, cy, s * 0.24, col)
            stopSquare(s * 0.1) if stop else circle(cx - s * 0.07, cy - s * 0.07, s * 0.06, QColor(255, 255, 255, 0x88))
        elif design == 10:
            fill(col)
            c.drawRoundedRect(QRectF(s * 0.1, s * 0.1, s * 0.8, s * 0.8), s * 0.22, s * 0.22)
            stopSquare(s * 0.16) if stop else circle(cx, cy, s * 0.16, white)
        elif design == 11:
            h = QPainterPath()
            h.moveTo(cx, s * 0.82)
            h.cubicTo(s * 0.02, s * 0.48, s * 0.2, s * 0.08, cx, s * 0.3)
            h.cubicTo(s * 0.8, s * 0.08, s * 0.98, s * 0.48, cx, s * 0.82)
            h.closeSubpath()
            fill(col)
            c.drawPath(h)
            stopSquare(s * 0.1) if stop else circle(cx, s * 0.46, s * 0.08, white)
        elif design == 12:
            st = QPainterPath()
            for i in range(10):
                a = math.pi * i / 5 - math.pi / 2
                r = s * 0.46 if i % 2 == 0 else s * 0.2
                x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
                st.moveTo(x, y) if i == 0 else st.lineTo(x, y)
            st.closeSubpath()
            fill(col)
            c.drawPath(st)
            stopSquare(s * 0.09) if stop else circle(cx, cy + s * 0.02, s * 0.07, white)
        elif design == 13:
            g = (["........", "..####..", "..####..", "..####..", "..####..", "........"] if stop else
                 ["..####..", ".######.", "########", "########", ".######.", "..####.."])
            u = s / 8
            fill(col)
            for r, row in enumerate(g):
                for cc, ch in enumerate(row):
                    if ch == "#":
                        c.drawRect(QRectF(cc * u, (r + 1) * u, u - 1, u - 1))
        elif design == 14:
            if stop:
                fill(col)
            else:
                stroke(s * 0.05)
            c.drawRoundedRect(QRectF(s * 0.02, s * 0.26, s * 0.96, s * 0.48), s * 0.08, s * 0.08)
            text("ON AIR", cx, cy + s * 0.07, s * 0.2, white if stop else col)
        else:
            stroke(s * 0.05)
            c.drawRoundedRect(QRectF(s * 0.14, s * 0.08, s * 0.72, s * 0.84), s * 0.12, s * 0.12)
            stroke(s * 0.03)
            for i in range(4):
                c.drawLine(QPointF(s * 0.3, s * (0.2 + i * 0.07)), QPointF(s * 0.7, s * (0.2 + i * 0.07)))
            stopSquare(s * 0.12, col) if stop else circle(cx, s * 0.66, s * 0.14, col)
        c.restore()


def buttonColour(skin_btn=None):
    """Màu Nút (same rule as Android): theme pack → its accent, cover, theme, custom, else the skin's own button colour."""
    k = Prefs.btnColour.value
    i = Motifs.of(k)
    if i is not None:
        return Motifs.list[i].accent.q()
    if k == "cover":
        return Core.palette[0].q()
    if k == "theme":
        return Themes.now().accent.q()
    if k == "custom":
        return _qc(int(Prefs.btnCustom.value))
    if skin_btn is None:
        return QColor(255, 255, 255)
    return _qc(skin_btn)
