"""A small drawing layer over QPainter that mirrors the Compose DrawScope used by the Android app, so the
visualisations, skins, edge lights and button sets look the same on Windows and Android."""
import colorsys
import math
import random
from contextlib import contextmanager

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
                           QRadialGradient)

PI = math.pi
sin, cos, exp, sqrt, atan2, hypot, floor = math.sin, math.cos, math.exp, math.sqrt, math.atan2, math.hypot, math.floor


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def avg(seq):
    seq = list(seq)
    return sum(seq) / len(seq) if seq else 0.0


def kmod(a, b):
    """Kotlin-style remainder (sign of the dividend)."""
    return math.fmod(a, b)


class Color:
    __slots__ = ("r", "g", "b", "a")

    def __init__(self, r=0.0, g=None, b=None, a=1.0):
        if g is None:                       # Color(0xAARRGGBB) or QColor / "#rrggbb"
            if isinstance(r, Color):
                self.r, self.g, self.b, self.a = r.r, r.g, r.b, r.a
                return
            if isinstance(r, str):
                q = QColor(r)
                self.r, self.g, self.b, self.a = q.redF(), q.greenF(), q.blueF(), q.alphaF()
                return
            if isinstance(r, QColor):
                self.r, self.g, self.b, self.a = r.redF(), r.greenF(), r.blueF(), r.alphaF()
                return
            v = int(r) & 0xFFFFFFFF
            if v <= 0xFFFFFF:
                v |= 0xFF000000
            self.a = ((v >> 24) & 255) / 255
            self.r = ((v >> 16) & 255) / 255
            self.g = ((v >> 8) & 255) / 255
            self.b = (v & 255) / 255
            return
        if isinstance(r, int) and isinstance(g, int) and isinstance(b, int) and (r > 1 or g > 1 or b > 1):
            self.r, self.g, self.b = r / 255, g / 255, b / 255
            self.a = a / 255 if isinstance(a, int) and a > 1 else float(a)
        else:
            self.r, self.g, self.b, self.a = float(r), float(g), float(b), float(a)

    def copy(self, alpha=None, red=None, green=None, blue=None):
        return Color(self.r if red is None else red, self.g if green is None else green,
                     self.b if blue is None else blue, self.a if alpha is None else clamp(alpha, 0.0, 1.0))

    @property
    def alpha(self):
        return self.a

    def q(self, mul=1.0):
        c = QColor()
        c.setRgbF(clamp(self.r, 0, 1), clamp(self.g, 0, 1), clamp(self.b, 0, 1), clamp(self.a * mul, 0, 1))
        return c

    def darken(self, f):
        k = 1 - clamp(f, 0, 1)
        return Color(self.r * k, self.g * k, self.b * k, self.a)

    def lighten(self, f):
        return Color(self.r + (1 - self.r) * f, self.g + (1 - self.g) * f, self.b + (1 - self.b) * f, self.a)

    def luminance(self):
        return 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b

    def to_hex(self):
        return "#%02X%02X%02X" % (int(clamp(self.r, 0, 1) * 255), int(clamp(self.g, 0, 1) * 255), int(clamp(self.b, 0, 1) * 255))

    @staticmethod
    def hsv(h, s, v, a=1.0):
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, clamp(s, 0, 1), clamp(v, 0, 1))
        return Color(r, g, b, a)

    @staticmethod
    def lerp(a, b, t):
        t = clamp(t, 0, 1)
        return Color(lerp(a.r, b.r, t), lerp(a.g, b.g, t), lerp(a.b, b.b, t), lerp(a.a, b.a, t))

    def __repr__(self):
        return "Color(%s, a=%.2f)" % (self.to_hex(), self.a)


Color.White = Color(1, 1, 1, 1)
Color.Black = Color(0, 0, 0, 1)
Color.Transparent = Color(0, 0, 0, 0)
Color.Red = Color(1, 0, 0, 1)
Color.Yellow = Color(1, 1, 0, 1)
Color.Gray = Color(0.53, 0.53, 0.53, 1)


def color_lerp(a, b, t):
    return Color.lerp(a, b, t)


class Offset:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)

    def __add__(self, o):
        return Offset(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Offset(self.x - o.x, self.y - o.y)

    def __mul__(self, k):
        return Offset(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __truediv__(self, k):
        return Offset(self.x / k, self.y / k)

    def __neg__(self):
        return Offset(-self.x, -self.y)

    def p(self):
        return QPointF(self.x, self.y)

    def distance(self):
        return math.hypot(self.x, self.y)


Offset.Zero = Offset(0, 0)


class Size:
    __slots__ = ("width", "height")

    def __init__(self, w=0.0, h=0.0):
        self.width, self.height = float(w), float(h)

    @property
    def minDimension(self):
        return min(self.width, self.height)

    @property
    def maxDimension(self):
        return max(self.width, self.height)

    @property
    def center(self):
        return Offset(self.width / 2, self.height / 2)


def CornerRadius(x, y=None):
    return (float(x), float(x if y is None else y))


BUTT, ROUND, SQUARE = "butt", "round", "square"


class Stroke:
    def __init__(self, width=1.0, cap=BUTT, join=None, pathEffect=None):
        self.width = float(width)
        self.cap = cap
        self.join = join
        self.dash = pathEffect


def dash(intervals, phase=0.0):
    return (list(intervals), float(phase))


class Brush:
    """A gradient that is resolved against the drawing area when used."""

    def __init__(self, kind, colors, a=None, b=None, radius=None, stops=None):
        self.kind, self.colors, self.a, self.b, self.radius, self.stops = kind, list(colors), a, b, radius, stops

    @staticmethod
    def verticalGradient(colors, startY=0.0, endY=None):
        return Brush("v", _colors(colors), startY, endY, stops=_stops(colors))

    @staticmethod
    def horizontalGradient(colors, startX=0.0, endX=None):
        return Brush("h", _colors(colors), startX, endX, stops=_stops(colors))

    @staticmethod
    def linearGradient(colors, start=None, end=None):
        return Brush("l", _colors(colors), start, end, stops=_stops(colors))

    @staticmethod
    def radialGradient(colors, center=None, radius=None):
        return Brush("r", _colors(colors), center, None, radius, stops=_stops(colors))

    @staticmethod
    def sweepGradient(colors, center=None):
        return Brush("s", _colors(colors), center, stops=_stops(colors))

    def qbrush(self, w, h, alpha=1.0):
        k = self.kind
        if k == "v":
            g = QLinearGradient(0, self.a or 0, 0, h if self.b is None or self.b == float("inf") else self.b)
        elif k == "h":
            g = QLinearGradient(self.a or 0, 0, w if self.b is None or self.b == float("inf") else self.b, 0)
        elif k == "l":
            s = self.a or Offset(0, 0)
            e = self.b or Offset(w, h)
            ex = w if e.x == float("inf") else e.x
            ey = h if e.y == float("inf") else e.y
            g = QLinearGradient(s.x, s.y, ex, ey)
        elif k == "r":
            c = self.a or Offset(w / 2, h / 2)
            r = self.radius or min(w, h) / 2
            g = QRadialGradient(c.x, c.y, max(0.01, r))
        else:
            c = self.a or Offset(w / 2, h / 2)
            g = QConicalGradient(c.x, c.y, 0)
        n = len(self.colors)
        for i, col in enumerate(self.colors):
            t = self.stops[i] if self.stops else (i / (n - 1) if n > 1 else 0)
            if k == "s":
                t = 1 - t                     # Qt's conical gradient turns the other way
            g.setColorAt(clamp(t, 0, 1), col.q(alpha))
        g.setSpread(QLinearGradient.PadSpread)
        return QBrush(g)


def _colors(colors):
    out = []
    for c in colors:
        if isinstance(c, tuple):
            c = c[1]
        out.append(c if isinstance(c, Color) else Color(c))
    return out


def _stops(colors):
    if colors and isinstance(colors[0], tuple):
        return [c[0] for c in colors]
    return None


class Path:
    def __init__(self):
        self.qp = QPainterPath()
        self.qp.setFillRule(Qt.WindingFill)

    def moveTo(self, x, y):
        self.qp.moveTo(x, y)
        return self

    def lineTo(self, x, y):
        if self.qp.elementCount() == 0:
            self.qp.moveTo(x, y)
        else:
            self.qp.lineTo(x, y)
        return self

    def relativeLineTo(self, dx, dy):
        p = self.qp.currentPosition()
        self.qp.lineTo(p.x() + dx, p.y() + dy)
        return self

    def quadraticBezierTo(self, x1, y1, x2, y2):
        self.qp.quadTo(x1, y1, x2, y2)
        return self

    quadraticTo = quadraticBezierTo

    def cubicTo(self, x1, y1, x2, y2, x3, y3):
        self.qp.cubicTo(x1, y1, x2, y2, x3, y3)
        return self

    def close(self):
        self.qp.closeSubpath()
        return self

    def addOval(self, rect):
        self.qp.addEllipse(_rect(rect))
        return self

    def addRect(self, rect):
        self.qp.addRect(_rect(rect))
        return self

    def addRoundRect(self, rect, rx, ry=None):
        self.qp.addRoundedRect(_rect(rect), rx, rx if ry is None else ry)
        return self

    def isEmpty(self):
        return self.qp.isEmpty()


def Rect(left, top, right, bottom):
    return QRectF(left, top, right - left, bottom - top)


def rect_at(offset, size):
    return QRectF(offset.x, offset.y, size.width, size.height)


def _rect(r):
    if isinstance(r, QRectF):
        return r
    if isinstance(r, tuple) and len(r) == 2:
        return rect_at(*r)
    return QRectF(*r)


class DS:
    """The drawing scope: size, center and the draw* calls."""

    def __init__(self, painter: QPainter, w, h):
        self.p = painter
        self.size = Size(w, h)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    @property
    def center(self):
        return Offset(self.size.width / 2, self.size.height / 2)

    # ---- paint helpers
    def _fill(self, paint, alpha):
        if isinstance(paint, Brush):
            return paint.qbrush(self.size.width, self.size.height, alpha)
        if not isinstance(paint, Color):
            paint = Color(paint)
        return QBrush(paint.q(alpha))

    def _setup(self, paint, alpha, style):
        p = self.p
        if style is None or style == "fill":
            p.setPen(Qt.NoPen)
            p.setBrush(self._fill(paint, alpha))
        else:
            pen = QPen(self._fill(paint, alpha), max(0.01, style.width))
            pen.setCapStyle({BUTT: Qt.FlatCap, ROUND: Qt.RoundCap, SQUARE: Qt.SquareCap}.get(style.cap, Qt.FlatCap))
            pen.setJoinStyle(Qt.RoundJoin)
            if style.dash:
                iv = [max(0.01, v / max(0.01, style.width)) for v in style.dash[0]]
                pen.setDashPattern(iv)
                pen.setDashOffset(style.dash[1] / max(0.01, style.width))
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

    # ---- shapes
    def drawLine(self, paint, start, end, strokeWidth=1.0, cap=BUTT, alpha=1.0, pathEffect=None):
        self._setup(paint, alpha, Stroke(strokeWidth or 1.0, cap, pathEffect=pathEffect))
        self.p.drawLine(start.p(), end.p())

    def drawCircle(self, paint, radius=None, center=None, alpha=1.0, style=None):
        if radius is None:
            radius = self.size.minDimension / 2
        if center is None:
            center = self.center
        if radius <= 0:
            return
        self._setup(paint, alpha, style)
        self.p.drawEllipse(center.p(), radius, radius)

    def drawRect(self, paint, topLeft=None, size=None, alpha=1.0, style=None):
        topLeft = topLeft or Offset(0, 0)
        size = size or Size(self.size.width - topLeft.x, self.size.height - topLeft.y)
        if size.width == 0 or size.height == 0:
            return
        self._setup(paint, alpha, style)
        self.p.drawRect(QRectF(topLeft.x, topLeft.y, size.width, size.height).normalized())

    def drawRoundRect(self, paint, topLeft=None, size=None, cornerRadius=(0.0, 0.0), alpha=1.0, style=None):
        topLeft = topLeft or Offset(0, 0)
        size = size or Size(self.size.width - topLeft.x, self.size.height - topLeft.y)
        if size.width == 0 or size.height == 0:
            return
        if not isinstance(cornerRadius, tuple):
            cornerRadius = (float(cornerRadius), float(cornerRadius))
        r = QRectF(topLeft.x, topLeft.y, size.width, size.height).normalized()
        rx = min(cornerRadius[0], r.width() / 2)
        ry = min(cornerRadius[1], r.height() / 2)
        self._setup(paint, alpha, style)
        self.p.drawRoundedRect(r, rx, ry)

    def drawOval(self, paint, topLeft=None, size=None, alpha=1.0, style=None):
        topLeft = topLeft or Offset(0, 0)
        size = size or Size(self.size.width - topLeft.x, self.size.height - topLeft.y)
        self._setup(paint, alpha, style)
        self.p.drawEllipse(QRectF(topLeft.x, topLeft.y, size.width, size.height).normalized())

    def drawArc(self, paint, startAngle, sweepAngle, useCenter, topLeft=None, size=None, alpha=1.0, style=None):
        topLeft = topLeft or Offset(0, 0)
        size = size or Size(self.size.width - topLeft.x, self.size.height - topLeft.y)
        r = QRectF(topLeft.x, topLeft.y, size.width, size.height).normalized()
        self._setup(paint, alpha, style)
        # Compose: degrees clockwise from 3 o'clock. Qt: 1/16 degree, counter-clockwise.
        a, s = int(-startAngle * 16), int(-sweepAngle * 16)
        if useCenter:
            self.p.drawPie(r, a, s)
        else:
            self.p.drawArc(r, a, s)

    def drawPath(self, path, paint, alpha=1.0, style=None):
        self._setup(paint, alpha, style)
        self.p.drawPath(path.qp if isinstance(path, Path) else path)

    def drawPoints(self, points, paint, strokeWidth=2.0, alpha=1.0):
        self._setup(paint, alpha, Stroke(strokeWidth, ROUND))
        for pt in points:
            self.p.drawPoint(pt.p())

    def drawText(self, text, x, y, color, size_px=14.0, bold=False, align="center", family=None):
        f = QFont(family or self.p.font().family())
        f.setPixelSize(max(1, int(size_px)))
        f.setBold(bold)
        self.p.setFont(f)
        self.p.setPen(QPen(color.q() if isinstance(color, Color) else QColor(color)))
        fm = self.p.fontMetrics()
        tw = fm.horizontalAdvance(text)
        dx = {"center": -tw / 2, "left": 0, "right": -tw}[align]
        self.p.drawText(QPointF(x + dx, y), text)

    # ---- transforms
    @contextmanager
    def rotate(self, degrees, pivot=None):
        pivot = pivot or self.center
        self.p.save()
        self.p.translate(pivot.x, pivot.y)
        self.p.rotate(degrees)
        self.p.translate(-pivot.x, -pivot.y)
        try:
            yield
        finally:
            self.p.restore()

    @contextmanager
    def translate(self, left=0.0, top=0.0):
        self.p.save()
        self.p.translate(left, top)
        try:
            yield
        finally:
            self.p.restore()

    @contextmanager
    def scale(self, sx, sy=None, pivot=None):
        pivot = pivot or self.center
        self.p.save()
        self.p.translate(pivot.x, pivot.y)
        self.p.scale(sx, sx if sy is None else sy)
        self.p.translate(-pivot.x, -pivot.y)
        try:
            yield
        finally:
            self.p.restore()

    @contextmanager
    def clipPath(self, path):
        self.p.save()
        self.p.setClipPath(path.qp if isinstance(path, Path) else path, Qt.IntersectClip)
        try:
            yield
        finally:
            self.p.restore()

    @contextmanager
    def clipRect(self, left, top, right, bottom):
        self.p.save()
        self.p.setClipRect(QRectF(left, top, right - left, bottom - top), Qt.IntersectClip)
        try:
            yield
        finally:
            self.p.restore()

    @contextmanager
    def inset(self, left, top=None, right=None, bottom=None):
        top = left if top is None else top
        right = left if right is None else right
        bottom = top if bottom is None else bottom
        old = self.size
        self.p.save()
        self.p.translate(left, top)
        self.size = Size(old.width - left - right, old.height - top - bottom)
        try:
            yield
        finally:
            self.size = old
            self.p.restore()

    @contextmanager
    def layer(self, alpha):
        """Draw a group with one overall opacity."""
        self.p.save()
        self.p.setOpacity(self.p.opacity() * clamp(alpha, 0, 1))
        try:
            yield
        finally:
            self.p.restore()


class KRandom:
    """kotlin.random.Random(seed) stand-in (same use, not the same numbers)."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def nextFloat(self):
        return self.r.random()

    def nextInt(self, a, b=None):
        if b is None:
            return self.r.randrange(a)
        return self.r.randrange(a, b)
