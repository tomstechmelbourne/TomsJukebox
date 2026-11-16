"""Simple flat icons drawn with QPainter (One UI style: rounded, single colour). Same look on every PC."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

_cache = {}
_registry = {}     # QIcon.cacheKey() -> (name, color, size), used to recolour buttons when the look changes


def icon(name, color="#0F2A38", size=24):
    key = (name, color, size)
    if key in _cache:
        return _cache[key]
    ic = QIcon()
    for scale in (1, 2):
        pm = QPixmap(size * scale, size * scale)
        pm.fill(Qt.transparent)
        pm.setDevicePixelRatio(scale)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        draw(p, name, QColor(color), size)
        p.end()
        ic.addPixmap(pm)
    _cache[key] = ic
    _registry[ic.cacheKey()] = (name, color, size)
    return ic


def recolour_all(root, old_theme, new_theme):
    """Give every button icon the colour of the same role in the new look (ink, muted, teal, on_accent...)."""
    from PySide6.QtWidgets import QAbstractButton
    roles = {}
    order = ["ink", "on_accent", "teal", "muted", "accent", "nav_ink", "top_ink", "player_ink", "player", "grey"]
    for k in order:
        v = old_theme.get(k)
        if isinstance(v, str) and v.startswith("#"):
            roles.setdefault(v.lower(), k)
    for b in root.findChildren(QAbstractButton):
        info = _registry.get(b.icon().cacheKey())
        if not info:
            continue
        name, color, size = info
        role = roles.get(color.lower())
        if role and isinstance(new_theme.get(role), str) and new_theme[role].startswith("#"):
            nc = new_theme[role]
            if nc.lower() != color.lower():
                b.setIcon(icon(name, nc, size))


def draw(p, name, col, s):
    k = s / 24.0
    p.scale(k, k)
    pen = QPen(col, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    fill = QBrush(col)

    def poly(pts, filled=True):
        p.setBrush(fill if filled else Qt.NoBrush)
        p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))
        p.setBrush(Qt.NoBrush)

    if name == "play":
        p.setPen(Qt.NoPen)
        path = QPainterPath()
        path.moveTo(8, 5)
        path.lineTo(19, 12)
        path.lineTo(8, 19)
        path.closeSubpath()
        p.setBrush(fill)
        p.drawPath(path)
    elif name == "pause":
        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        p.drawRoundedRect(QRectF(6.5, 5, 4, 14), 1.5, 1.5)
        p.drawRoundedRect(QRectF(13.5, 5, 4, 14), 1.5, 1.5)
    elif name in ("next", "prev"):
        p.save()
        if name == "prev":
            p.translate(24, 0)
            p.scale(-1, 1)
        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        poly([(5, 6), (15, 12), (5, 18)])
        p.drawRoundedRect(QRectF(16, 6, 3, 12), 1.2, 1.2)
        p.restore()
    elif name == "stop":
        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        p.drawRoundedRect(QRectF(6, 6, 12, 12), 2, 2)
    elif name == "record":
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#E5484D")))
        p.drawEllipse(QPointF(12, 12), 6.5, 6.5)
    elif name == "shuffle":
        p.drawLine(QPointF(4, 7), QPointF(8, 7))
        path = QPainterPath(QPointF(8, 7))
        path.cubicTo(13, 7, 11, 17, 16, 17)
        p.drawPath(path)
        p.drawLine(QPointF(16, 17), QPointF(20, 17))
        p.drawLine(QPointF(4, 17), QPointF(8, 17))
        path = QPainterPath(QPointF(8, 17))
        path.cubicTo(13, 17, 11, 7, 16, 7)
        p.drawPath(path)
        p.drawLine(QPointF(16, 7), QPointF(20, 7))
        poly([(18, 4.5), (21, 7), (18, 9.5)])
        poly([(18, 14.5), (21, 17), (18, 19.5)])
    elif name in ("repeat", "repeat1"):
        p.drawRoundedRect(QRectF(4, 7, 16, 10), 4, 4)
        p.setPen(Qt.NoPen)
        poly([(13, 4), (16.5, 7), (13, 10)])
        poly([(11, 14), (7.5, 17), (11, 20)])
        if name == "repeat1":
            p.setPen(QPen(col, 1.6))
            p.drawLine(QPointF(12, 10), QPointF(12, 14.5))
    elif name in ("note", "songs"):
        p.setBrush(fill)
        p.drawEllipse(QPointF(8, 17), 3, 2.4)
        p.drawEllipse(QPointF(17, 15), 3, 2.4)
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(11, 17), QPointF(11, 5.5))
        p.drawLine(QPointF(20, 15), QPointF(20, 3.5))
        p.drawLine(QPointF(11, 5.5), QPointF(20, 3.5))
    elif name in ("album", "cd", "disc"):
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawEllipse(QPointF(12, 12), 2.5, 2.5)
        if name == "cd":
            p.setPen(QPen(col, 1.2))
            p.drawArc(QRectF(6, 6, 12, 12), 30 * 16, 60 * 16)
    elif name == "artist":
        p.drawEllipse(QPointF(12, 8.5), 3.8, 3.8)
        path = QPainterPath(QPointF(4.5, 20))
        path.cubicTo(5.5, 13.5, 18.5, 13.5, 19.5, 20)
        p.drawPath(path)
    elif name == "genre":
        path = QPainterPath(QPointF(4, 11))
        path.lineTo(4, 4)
        path.lineTo(11, 4)
        path.lineTo(20, 13)
        path.lineTo(13, 20)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(fill)
        p.drawEllipse(QPointF(8, 8), 1.4, 1.4)
    elif name == "folder":
        path = QPainterPath(QPointF(3.5, 7))
        path.lineTo(3.5, 18.5)
        path.lineTo(20.5, 18.5)
        path.lineTo(20.5, 8.5)
        path.lineTo(11.5, 8.5)
        path.lineTo(9.5, 6)
        path.lineTo(4.5, 6)
        path.closeSubpath()
        p.drawPath(path)
    elif name in ("playlist", "queue"):
        for y in (6, 11, 16):
            p.drawLine(QPointF(4, y), QPointF(13 if name == "playlist" else 18, y))
        if name == "playlist":
            p.setBrush(fill)
            p.drawEllipse(QPointF(16, 18), 2.4, 2)
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(18.4, 18), QPointF(18.4, 8))
            p.drawLine(QPointF(18.4, 8), QPointF(21, 9))
        else:
            p.setBrush(fill)
            poly([(4, 19), (4, 23), (7.5, 21)])
    elif name in ("star", "star_on"):
        pts = []
        for i in range(10):
            r = 9 if i % 2 == 0 else 4
            a = math.pi / 2 + i * math.pi / 5
            pts.append((12 + r * math.cos(a), 12.6 - r * math.sin(a)))
        if name == "star_on":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor("#FBB040")))
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))
        else:
            poly(pts, filled=False)
    elif name == "radio":
        p.drawRoundedRect(QRectF(3.5, 9, 17, 11), 2.5, 2.5)
        p.drawLine(QPointF(7, 9), QPointF(17, 3.5))
        p.setBrush(fill)
        p.drawEllipse(QPointF(15.5, 14.5), 2.2, 2.2)
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(6.5, 13), QPointF(10.5, 13))
        p.drawLine(QPointF(6.5, 16), QPointF(10.5, 16))
    elif name == "podcast":
        p.drawRoundedRect(QRectF(9, 3.5, 6, 10), 3, 3)
        path = QPainterPath(QPointF(6, 11))
        path.cubicTo(6, 18, 18, 18, 18, 11)
        p.drawPath(path)
        p.drawLine(QPointF(12, 16.5), QPointF(12, 20.5))
        p.drawLine(QPointF(8.5, 20.5), QPointF(15.5, 20.5))
    elif name == "recordings":
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#E5484D")))
        p.drawEllipse(QPointF(12, 12), 4, 4)
    elif name == "tools":
        path = QPainterPath(QPointF(14.5, 4))
        path.cubicTo(18.5, 3, 21.5, 6.5, 19.5, 10)
        path.lineTo(17, 9.5)
        path.lineTo(15.5, 8)
        path.lineTo(15, 5.5)
        p.drawPath(path)
        p.drawLine(QPointF(15, 9), QPointF(5, 19))
        p.drawEllipse(QPointF(5.2, 18.8), 1.4, 1.4)
    elif name == "stats":
        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        p.drawRoundedRect(QRectF(4, 12, 4, 8), 1.3, 1.3)
        p.drawRoundedRect(QRectF(10, 6, 4, 14), 1.3, 1.3)
        p.drawRoundedRect(QRectF(16, 9, 4, 11), 1.3, 1.3)
    elif name == "lyrics":
        p.drawRoundedRect(QRectF(4, 4.5, 16, 12.5), 3, 3)
        poly([(8, 17), (8, 21), (12, 17)])
        for y in (8.5, 12.5):
            p.drawLine(QPointF(8, y), QPointF(16, y))
    elif name in ("volume", "mute"):
        p.setBrush(fill)
        poly([(4, 9.5), (8, 9.5), (13, 5), (13, 19), (8, 14.5), (4, 14.5)])
        p.setBrush(Qt.NoBrush)
        if name == "volume":
            p.drawArc(QRectF(12, 8, 6, 8), -60 * 16, 120 * 16)
            p.drawArc(QRectF(12, 5, 9, 14), -60 * 16, 120 * 16)
        else:
            p.drawLine(QPointF(16, 9.5), QPointF(21, 14.5))
            p.drawLine(QPointF(21, 9.5), QPointF(16, 14.5))
    elif name == "eq":
        for x, y in ((6, 9), (12, 15), (18, 7)):
            p.drawLine(QPointF(x, 4), QPointF(x, 20))
            p.setBrush(fill)
            p.drawEllipse(QPointF(x, y), 2.4, 2.4)
            p.setBrush(Qt.NoBrush)
    elif name == "fullscreen":
        for (x, y, dx, dy) in ((4, 4, 1, 1), (20, 4, -1, 1), (4, 20, 1, -1), (20, 20, -1, -1)):
            p.drawLine(QPointF(x, y), QPointF(x + 5 * dx, y))
            p.drawLine(QPointF(x, y), QPointF(x, y + 5 * dy))
    elif name == "cast":
        p.drawRoundedRect(QRectF(3.5, 5, 17, 11.5), 2, 2)
        p.drawLine(QPointF(8, 20), QPointF(16, 20))
        p.drawLine(QPointF(12, 16.5), QPointF(12, 20))
    elif name == "settings":
        p.drawEllipse(QPointF(12, 12), 3, 3)
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(QPointF(12 + 6 * math.cos(a), 12 + 6 * math.sin(a)), QPointF(12 + 8.5 * math.cos(a), 12 + 8.5 * math.sin(a)))
        p.drawEllipse(QPointF(12, 12), 6, 6)
    elif name == "info":
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawLine(QPointF(12, 11), QPointF(12, 16.5))
        p.setBrush(fill)
        p.drawEllipse(QPointF(12, 7.8), 1.1, 1.1)
    elif name == "mini":
        p.drawRoundedRect(QRectF(3.5, 5, 17, 14), 2.5, 2.5)
        p.setBrush(fill)
        p.drawRoundedRect(QRectF(11.5, 11.5, 7, 5.5), 1.2, 1.2)
    elif name == "moon":
        path = QPainterPath()
        path.addEllipse(QPointF(12, 12), 8, 8)
        cut = QPainterPath()
        cut.addEllipse(QPointF(16, 8.5), 7, 7)
        p.setBrush(fill)
        p.setPen(Qt.NoPen)
        p.drawPath(path.subtracted(cut))
    elif name == "sun":
        p.setBrush(fill)
        p.drawEllipse(QPointF(12, 12), 4, 4)
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(QPointF(12 + 6.5 * math.cos(a), 12 + 6.5 * math.sin(a)), QPointF(12 + 9 * math.cos(a), 12 + 9 * math.sin(a)))
    elif name == "search":
        p.drawEllipse(QPointF(10.5, 10.5), 6, 6)
        p.drawLine(QPointF(15, 15), QPointF(20, 20))
    elif name == "add":
        p.drawLine(QPointF(12, 5), QPointF(12, 19))
        p.drawLine(QPointF(5, 12), QPointF(19, 12))
    elif name == "more":
        p.setBrush(fill)
        for x in (6, 12, 18):
            p.drawEllipse(QPointF(x, 12), 1.6, 1.6)
    elif name == "eject":
        p.setBrush(fill)
        poly([(5, 14), (12, 6), (19, 14)])
        p.drawRoundedRect(QRectF(5, 16.5, 14, 2.5), 1, 1)
    elif name == "refresh":
        p.drawArc(QRectF(5, 5, 14, 14), 40 * 16, 280 * 16)
        p.setBrush(fill)
        poly([(17, 3.5), (19.5, 8.5), (14, 8.5)])
    elif name == "bell":
        path = QPainterPath(QPointF(6, 17))
        path.lineTo(6, 11)
        path.cubicTo(6, 4.5, 18, 4.5, 18, 11)
        path.lineTo(18, 17)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(4.5, 17), QPointF(19.5, 17))
        p.drawArc(QRectF(10, 17, 4, 4), 180 * 16, 180 * 16)
    elif name == "chat":
        p.drawRoundedRect(QRectF(4, 5, 16, 11), 4, 4)
        poly([(8, 16), (8, 20), (12, 16)])
    elif name == "location":
        path = QPainterPath(QPointF(12, 21))
        path.cubicTo(5, 13, 5, 4, 12, 4)
        path.cubicTo(19, 4, 19, 13, 12, 21)
        p.drawPath(path)
        p.drawEllipse(QPointF(12, 10), 2.4, 2.4)
    elif name == "download":
        p.drawLine(QPointF(12, 4), QPointF(12, 15))
        poly([(7.5, 11), (12, 16), (16.5, 11)], filled=False)
        p.drawLine(QPointF(5, 19.5), QPointF(19, 19.5))
    elif name == "back":
        p.drawLine(QPointF(15, 5), QPointF(8, 12))
        p.drawLine(QPointF(8, 12), QPointF(15, 19))
    elif name == "close":
        p.drawLine(QPointF(6, 6), QPointF(18, 18))
        p.drawLine(QPointF(18, 6), QPointF(6, 18))
    elif name == "clock":
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawLine(QPointF(12, 12), QPointF(12, 7))
        p.drawLine(QPointF(12, 12), QPointF(15.5, 14))
    elif name == "web":
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawEllipse(QRectF(8.5, 3.5, 7, 17))
        p.drawLine(QPointF(3.5, 12), QPointF(20.5, 12))
    elif name == "minimize":
        p.drawLine(QPointF(6, 15), QPointF(18, 15))
    elif name == "maximize":
        p.drawRoundedRect(QRectF(6, 6, 12, 12), 2, 2)
    elif name == "pin":
        poly([(9, 4), (15, 4), (14, 10), (17, 13), (7, 13), (10, 10)], filled=False)
        p.drawLine(QPointF(12, 13), QPointF(12, 20))
    elif name == "timer":
        p.drawEllipse(QPointF(12, 13), 7.5, 7.5)
        p.drawLine(QPointF(12, 13), QPointF(12, 9))
        p.drawLine(QPointF(10, 3.5), QPointF(14, 3.5))
        p.drawLine(QPointF(17.5, 6.5), QPointF(19, 5))
    elif name == "palette":
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        for x, y in ((9, 8.5), (14.5, 8), (16.5, 12.5)):
            p.setBrush(fill)
            p.drawEllipse(QPointF(x, y), 1.4, 1.4)
        p.setBrush(Qt.NoBrush)
    else:
        p.drawEllipse(QPointF(12, 12), 6, 6)
