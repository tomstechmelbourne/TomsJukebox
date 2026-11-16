"""The player at the top of the window, drawn like the Android app:
- "Mặc Định (Tom's Tech)" card (default): album cover as the background, "Máy tính này" + output button, title in the title font,
  colourful waves on the time bar and buttons in frosted circles;
- "Viên Thuốc" pill (Tom's Dock): skin, spinning disc, title, buttons, waves and the time bar inside.
Both follow Skin, Kiểu Nút / Màu Nút, Ánh Sáng Chạy Viền, Hiệu Ứng Sóng Nhạc and Bộ Chủ Đề."""
import math
import time

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .. import tags
from ..art import fonts
from ..art.buttons import NEXT, PAUSE, PLAY, PREV, REC, REC_STOP, ButtonArt, buttonColour
from ..art.ds import DS, Brush, Color, CornerRadius, Offset, Path, Size, Stroke, clamp, exp, sin
from ..art.edge import paint_edge
from ..art.prefs import Prefs
from ..art.skins import PillColours, SkinList, paintSkin, paintSkinBorder, skinStyle
from ..art.state import Core
from ..art.themes import ORANGE, BarColours, Motifs, Skins, VizStyles, lum, t
from ..art.viz import drawViz, waves
from ..i18n import tr
from .widgets import fmt_time

T0 = time.monotonic()


def clock():
    return time.monotonic() - T0


class Ticker(QObject):
    """One clock for every animation (about 30 frames a second, slower when the window is hidden)."""
    tick = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(33)
        self.player = None
        self._fake = [0.04] * 24

    def slow(self, on):
        self.timer.setInterval(250 if on else 33)

    def _step(self):
        self.update_levels()
        self.tick.emit()

    def update_levels(self):
        p = self.player
        playing = bool(p and p.is_playing())
        Core.playing = playing
        real = None
        if playing and p.cast is None:
            try:
                arr = p.engine.levels(24)
                if len(arr) == 24 and float(max(arr)) > 0.001:
                    real = [float(x) for x in arr]
            except Exception:
                real = None
        tm = clock()
        out = Core.levels
        for i in range(24):
            if real is not None:
                target = real[i]
            elif playing:
                target = 0.25 + 0.65 * abs(math.sin(tm * (1.3 + i * 0.17) + i * 0.9) * math.sin(tm * 0.7 + i * 0.31))
            else:
                target = 0.04
            out[i] = out[i] + (target - out[i]) * (0.45 if real is not None else 0.15)
        Core.levels = out


TICKER = None


def ticker():
    global TICKER
    if TICKER is None:
        TICKER = Ticker()
    return TICKER


# ------------------------------------------------------------------ cover and palette
_cover_cache = {}


def cover_image(art_key):
    if not art_key:
        return None
    if art_key in _cover_cache:
        return _cover_cache[art_key]
    path = tags.art_path(art_key, small=False)
    img = QImage(path) if path else QImage()
    if img.isNull():
        img = None
    if len(_cover_cache) > 40:
        _cover_cache.clear()
    _cover_cache[art_key] = img
    return img


def palette_from_image(img, n=5):
    """A few bright colours from the cover (for the waves, edge light and 'from cover' colours)."""
    if img is None or img.isNull():
        return None
    small = img.scaled(28, 28, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    cands = []
    for y in range(small.height()):
        for x in range(small.width()):
            c = QColor(small.pixel(x, y))
            h, s, v, _ = c.getHsvF()
            if v < 0.12:
                continue
            cands.append((s * 1.4 + (1 - abs(v - 0.7)), h, s, v, c))
    cands.sort(key=lambda e: -e[0])
    picked = []
    for sc, h, s, v, c in cands:
        if all(min(abs(h - ph), 1 - abs(h - ph)) > 0.06 or abs(v - pv) > 0.3 for ph, pv, _c in picked):
            picked.append((h, v, c))
        if len(picked) >= n:
            break
    if not picked:
        return None
    out = []
    for h, v, c in picked:
        hh, ss, vv, _ = c.getHsvF()
        c2 = QColor.fromHsvF(max(0.0, hh), min(1.0, ss * 1.1 + 0.05), max(0.55, vv))
        out.append(Color(c2))
    return out


def output_name(player):
    if player is not None and player.cast is not None:
        try:
            return player.cast.name
        except Exception:
            return t("TV / Wi-Fi Speaker", "TV / Loa Wi-Fi")
    return t("This computer", "Máy tính này")


class WaveColours:
    list = [("vivid", "Vivid", "Rực Rỡ"), ("cover", "From Cover", "Theo Ảnh Bìa"), ("sunset", "Sunset", "Hoàng Hôn"),
            ("ocean", "Ocean", "Đại Dương"), ("aurora", "Aurora", "Cực Quang"), ("rainbow", "Rainbow", "Cầu Vồng"),
            ("candy", "Candy", "Kẹo Ngọt"), ("neon", "Neon", "Neon"), ("gold", "Gold", "Vàng Ánh Kim"), ("forest", "Forest", "Rừng Xanh"),
            ("bar", "Time Bar Colour", "Theo Màu Thanh Thời Gian")]
    shapes = [("Soft Hills", "Đồi Mềm"), ("Silk Ribbons", "Dải Lụa"), ("Glowing Mirror", "Đối Xứng Phát Sáng"), ("Rounded Bars", "Cột Bo Tròn")]

    @staticmethod
    def of(k):
        C = Color
        if k == "bar":
            c = BarColours.colours(Prefs.barColour.value, Core.palette)
            return c if len(c) >= 2 else [c[0], c[0].copy(alpha=0.7)]
        if k == "cover":
            p = Core.palette
            return [p[0], p[1], p[2], p[1]]
        table = {
            "sunset": (0xFFFF6E40, 0xFFFF4081, 0xFFFFAB40, 0xFFAA00FF), "ocean": (0xFF00E5FF, 0xFF2979FF, 0xFF1DE9B6, 0xFF3D5AFE),
            "aurora": (0xFF69F0AE, 0xFF18FFFF, 0xFFB388FF, 0xFFEA80FC), "rainbow": (0xFFFF5252, 0xFFFFD740, 0xFF69F0AE, 0xFF448AFF, 0xFFE040FB),
            "candy": (0xFFFF80AB, 0xFFB388FF, 0xFF84FFFF, 0xFFFFFF8D), "neon": (0xFF76FF03, 0xFFFF1744, 0xFF00E5FF, 0xFFD500F9),
            "gold": (0xFFFFD54F, 0xFFFFB300, 0xFFFFE082, 0xFFFF8F00), "forest": (0xFF64DD17, 0xFF00C853, 0xFFAEEA00, 0xFF1DE9B6),
        }
        return [C(x) for x in table.get(k, (0xFFFF3B5C, 0xFFE040FB, 0xFF7C4DFF, 0xFF448AFF))]


def cycle_skin_colour():
    """Double-click on the pill: next colour (or next wood / marble / XP variant). Returns the name to show."""
    sk = Prefs.skin.value
    if sk == "grain":
        Prefs.woodType.value = (Prefs.woodType.value + 1) % 3
        return t(*SkinList.woodTypes[Prefs.woodType.value])
    if sk == "marble":
        Prefs.marbleType.value = (Prefs.marbleType.value + 1) % 3
        return t(*SkinList.marbleTypes[Prefs.marbleType.value])
    if sk == "xp":
        lst = ["blue", "silver", "olive"]
        i = (lst.index(Prefs.xpColour.value) + 1) % 3 if Prefs.xpColour.value in lst else 0
        Prefs.xpColour.value = lst[i]
        return Skins.xpColours()[i][1]
    if sk in ("pill", "slim"):
        Prefs.pillColour.value = (Prefs.pillColour.value + 1) % len(PillColours.list)
        return PillColours.name(Prefs.pillColour.value)
    return t("This skin has one colour – try Pill, Wood Grain or Marble", "Skin này chỉ có một màu – thử Viên Thuốc, Vân Gỗ hoặc Cẩm Thạch")


# ------------------------------------------------------------------ the widget
class ArtPlayer(QWidget):
    open_now = Signal()
    want_cast = Signal()
    want_menu = Signal(object)
    toast = Signal(str)
    want_record = Signal()
    want_fav = Signal()

    def __init__(self, mw, parent=None, force_style=None):
        super().__init__(parent)
        self.force = force_style
        self.mw = mw
        self.player = mw.player
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        self._hits = []
        self._hover = None
        self._pressed = None
        self._drag = None
        self._seek_rect = None
        self._msg, self._msg_at = "", 0.0
        self._art_key = None
        self._img = None
        self._disc_angle = 0.0
        self._last = clock()
        self.recording = False
        ticker().player = self.player
        ticker().tick.connect(self._tick)
        self.player.changed.connect(self._on_changed)
        self.player.state.connect(lambda _p: self.update())
        self.update_height()

    # ---- sizing
    def style_now(self):
        return self.force or Prefs.playerStyle.value

    def update_height(self):
        if self.force == "mini":
            self.setFixedHeight(84)
        elif self.style_now() == "card":
            self.setFixedHeight(214)
        else:
            self.setFixedHeight(104 if Prefs.skin.value == "slim" else 138)
        self.update()

    def _on_changed(self, it):
        key = it.get("art_key") if it else None
        if key != self._art_key:
            self._art_key = key
            self._img = cover_image(key)
            pal = palette_from_image(self._img)
            if pal:
                Core.set_palette(pal)
            else:
                Core.set_palette([Color(0xFF48B0C8), Color(0xFFFBB040), Color(0xFF7EE3C1), Color(0xFF2C9CC0), Color(0xFFC7F0FA)])
        self.update()

    def show_msg(self, text):
        self._msg, self._msg_at = text, clock()
        self.update()

    def _tick(self):
        if not self.isVisible():
            return
        now = clock()
        dt = now - self._last
        self._last = now
        if Core.playing:
            speed = 40 + (sum(Core.levels[:4]) / 4 * 160 if Prefs.spinBeat.value else 0)
            self._disc_angle = (self._disc_angle + dt * speed) % 360
        self.update()

    # ---- state helpers
    def _kind(self):
        it = self.player.current
        return (it or {}).get("kind") or ""

    def _texts(self):
        title, sub, fmt = self._texts0()
        sl = getattr(self.mw, "sleep", None)
        b = sl.badge() if sl is not None else ""
        if b:
            fmt = (fmt + "  " + b).strip()
        return title, sub, fmt

    def _texts0(self):
        it = self.player.current
        if not it:
            return "Tom's Jukebox", tr("nothing_playing"), ""
        title = it.title or "Tom's Jukebox"
        k = it.get("kind")
        if k == "radio":
            sub = it.get("now_title") or it.get("artist") or ""
        else:
            sub = " · ".join(x for x in (it.get("artist") or "", it.get("album") or "") if x)
        fmt = (it.get("codec") or "").upper()
        return title, sub, fmt

    def _times(self):
        pos = self.player.position() or 0
        dur = self.player.duration() or 0
        return pos, dur

    # ---- painting
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self._hits = []
        if self.style_now() == "card":
            self._paint_card(p)
        else:
            self._paint_pill(p)
        p.end()

    def _rounded(self, rect, r):
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        return path

    def _edge(self, p, rect, radius):
        if Prefs.edgeOn.value and Prefs.edgeWhere.value != "window" and Core.playing:
            p.save()
            p.translate(rect.topLeft())
            paint_edge(DS(p, rect.width(), rect.height()), clock(), radius, uri=str((self.player.current or {}).get("id", "")))
            p.restore()

    def _btn(self, p, kind, rect, colour, glass=False):
        """Draws one button in the chosen button set and remembers where it is."""
        name = {PLAY: "play", PAUSE: "play", PREV: "prev", NEXT: "next", REC: "rec", REC_STOP: "rec"}[kind]
        hov = self._hover == name
        if glass:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 0x44 if hov else 0x33))
            p.drawEllipse(rect)
            s = rect.width() * 0.5
            inner = QRectF(rect.center().x() - s / 2, rect.center().y() - s / 2, s, s)
        else:
            s = rect.width() * float(Prefs.btnScale.value)
            inner = QRectF(rect.center().x() - s / 2, rect.center().y() - s / 2, s, s)
            if hov:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 0x22))
                p.drawEllipse(rect.adjusted(-3, -3, 3, 3))
        blink = kind == REC_STOP and Prefs.recBlink.value and int(clock() * 2) % 2 == 1
        p.save()
        if blink:
            p.setOpacity(0.35)
        p.translate(inner.topLeft())
        glow = sum(Core.levels[:4]) / 4
        ButtonArt.draw(p, kind, int(Prefs.btnStyle.value), inner.width(), colour, pressed=self._pressed == name, glow=glow)
        p.restore()
        self._hits.append((rect.adjusted(-4, -4, 4, 4), name))

    def _icon_btn(self, p, rect, name, glyph, colour, active=False):
        """Small line icon (shuffle, repeat, cast, +/✓)."""
        hov = self._hover == name
        if hov:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 0x22))
            p.drawEllipse(rect)
        col = QColor(ORANGE.q()) if active else QColor(colour)
        pen = QPen(col, max(1.6, rect.width() * 0.08))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        c = rect.center()
        s = rect.width() * 0.3
        x, y = c.x(), c.y()
        if glyph == "shuffle":
            p.drawLine(QPointF(x - s, y - s * 0.6), QPointF(x + s, y + s * 0.6))
            p.drawLine(QPointF(x - s, y + s * 0.6), QPointF(x + s, y - s * 0.6))
            for yy, d in ((y + s * 0.6, 1), (y - s * 0.6, -1)):
                p.drawLine(QPointF(x + s, yy), QPointF(x + s * 0.55, yy))
                p.drawLine(QPointF(x + s, yy), QPointF(x + s, yy - d * s * 0.45))
        elif glyph in ("repeat", "repeat1"):
            r = QRectF(x - s, y - s * 0.65, 2 * s, 1.3 * s)
            p.drawRoundedRect(r, s * 0.45, s * 0.45)
            p.drawLine(QPointF(x + s * 0.2, y - s * 0.65), QPointF(x - s * 0.1, y - s * 0.95))
            p.drawLine(QPointF(x + s * 0.2, y - s * 0.65), QPointF(x - s * 0.1, y - s * 0.35))
            if glyph == "repeat1":
                f = QFont()
                f.setPixelSize(int(s * 1.0))
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignCenter, "1")
        elif glyph == "cast":
            r = QRectF(x - s, y - s * 0.8, 2 * s, 1.4 * s)
            p.drawRoundedRect(r, 2, 2)
            p.drawLine(QPointF(x - s * 0.5, y + s * 0.95), QPointF(x + s * 0.5, y + s * 0.95))
        elif glyph in ("plus", "check"):
            p.drawEllipse(QPointF(x, y), s * 1.45, s * 1.45)
            if glyph == "plus":
                p.drawLine(QPointF(x - s * 0.7, y), QPointF(x + s * 0.7, y))
                p.drawLine(QPointF(x, y - s * 0.7), QPointF(x, y + s * 0.7))
            else:
                p.drawLine(QPointF(x - s * 0.7, y), QPointF(x - s * 0.15, y + s * 0.55))
                p.drawLine(QPointF(x - s * 0.15, y + s * 0.55), QPointF(x + s * 0.75, y - s * 0.55))
        self._hits.append((rect, name))

    def _marquee(self, p, text, rect, font, colour, align=Qt.AlignHCenter):
        p.setFont(font)
        p.setPen(QColor(colour))
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        if tw <= rect.width():
            p.drawText(rect, align | Qt.AlignVCenter, text)
            return
        p.save()
        p.setClipRect(rect)
        gap = 60
        off = (clock() * 30) % (tw + gap)
        y = rect.center().y() + fm.ascent() / 2 - fm.descent() / 2
        p.drawText(QPointF(rect.left() - off, y), text)
        p.drawText(QPointF(rect.left() - off + tw + gap, y), text)
        p.restore()

    def _toast(self, p, rect):
        if self._msg and clock() - self._msg_at < 1.4:
            f = QFont()
            f.setPixelSize(12)
            p.setFont(f)
            fm = QFontMetrics(f)
            w = fm.horizontalAdvance(self._msg) + 20
            r = QRectF(rect.center().x() - w / 2, rect.top() + 4, w, 20)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 0xCC))
            p.drawRoundedRect(r, 10, 10)
            p.setPen(QColor("white"))
            p.drawText(r, Qt.AlignCenter, self._msg)
        elif self._msg:
            self._msg = ""

    # ---- card (Mặc Định (Tom's Tech))
    def _paint_card(self, p):
        W, H = self.width(), self.height()
        rect = QRectF(2, 2, W - 4, H - 4)
        radius = 34.0
        clip = self._rounded(rect, radius)
        p.save()
        p.setClipPath(clip)
        p.translate(rect.topLeft())
        w, h = rect.width(), rect.height()
        ds = DS(p, w, h)
        bg = Prefs.cardBg.value
        tm = clock()
        if bg != "skin":
            if self._img is not None:
                src = self._img
                sc = max(w / src.width(), h / src.height())
                sw, sh = w / sc, h / sc
                p.drawImage(QRectF(0, 0, w, h), src, QRectF((src.width() - sw) / 2, (src.height() - sh) / 2, sw, sh))
            else:
                ds.drawRect(Brush.linearGradient([c.darken(0.5) for c in Core.palette]))
            ds.drawRect(Brush.verticalGradient([Color(0x99000000), Color(0x77000000), Color(0xCC000000)]))
        if bg != "cover":
            a = 0.55 if bg == "mix" else clamp(float(Prefs.pillAlpha.value), 0.05, 1.0)
            with ds.layer(a):
                paintSkin(ds, tm, 0.0)
            ds.drawRect(Color(0x55000000))
        if Prefs.cardViz.value and Prefs.vizOn.value and Prefs.vizPill.value:
            st = VizStyles.autoPick(tm) if Prefs.vizAuto.value else int(Prefs.viz.value)
            with ds.layer(0.45):
                drawViz(ds, st, tm * VizStyles.speed(), Core.levels, Core.palette)
        if bg != "cover":
            paintSkinBorder(ds, radius, skinStyle().border)
        p.restore()
        # content
        pad = 22.0
        x0, x1 = rect.left() + pad, rect.right() - pad
        # row 1: output name + cast button
        f = QFont()
        f.setPixelSize(14)
        f.setWeight(QFont.Medium)
        p.setFont(f)
        p.setPen(QColor(0xE0, 0xE0, 0xE0))
        p.drawText(QRectF(x0, rect.top() + 12, x1 - x0 - 34, 24), Qt.AlignLeft | Qt.AlignVCenter, output_name(self.player))
        self._icon_btn(p, QRectF(x1 - 28, rect.top() + 10, 28, 28), "cast", "cast", QColor("white"))
        # row 2: logo + title
        title, sub, fmt = self._texts()
        tf = fonts.title_font(19)
        ty = rect.top() + 42
        fm = QFontMetrics(tf)
        tw = min(fm.horizontalAdvance(title), x1 - x0 - 30)
        lx = rect.center().x() - (tw + 28) / 2
        logo = self.mw.logo_pixmap(22) if hasattr(self.mw, "logo_pixmap") else None
        if logo is not None:
            p.drawPixmap(QRectF(lx, ty + 4, 22, 22), logo, QRectF(logo.rect()))
        self._marquee(p, title, QRectF(lx + 28, ty, tw + 2, 30), tf, "white", Qt.AlignLeft)
        self._hits.append((QRectF(x0, ty, x1 - x0, 30), "open"))
        # sub line
        f2 = QFont()
        f2.setPixelSize(12)
        sline = "  ·  ".join(x for x in (sub, fmt) if x)
        self._marquee(p, sline, QRectF(x0, ty + 28, x1 - x0, 18), f2, QColor(0xD8, 0xD8, 0xD8))
        # wave seek bar + times
        sb = QRectF(x0 - 6, ty + 48, x1 - x0 + 12, 40)
        self._wave_seek(p, sb)
        pos, dur = self._times()
        f3 = QFont()
        f3.setPixelSize(12)
        p.setFont(f3)
        p.setPen(QColor(0xBD, 0xBD, 0xBD))
        live = self._kind() == "radio"
        p.drawText(QRectF(x0, sb.bottom(), 80, 16), Qt.AlignLeft | Qt.AlignVCenter, fmt_time(pos))
        p.drawText(QRectF(x1 - 80, sb.bottom(), 80, 16), Qt.AlignRight | Qt.AlignVCenter, "LIVE" if live else fmt_time(dur))
        # buttons
        by = rect.bottom() - 36
        big = 50.0
        col = buttonColour(QColor("white"))
        cx = rect.center().x()
        gap = (x1 - x0) / 4.6
        self._icon_btn(p, QRectF(cx - gap * 2 - 15, by - 15, 30, 30), "shuffle", "shuffle", QColor("white"), active=self.player.shuffle)
        self._btn(p, PREV, QRectF(cx - gap - big * 0.425, by - big * 0.425, big * 0.85, big * 0.85), col, glass=True)
        self._btn(p, PAUSE if Core.playing else PLAY, QRectF(cx - big / 2, by - big / 2, big, big), col, glass=True)
        self._btn(p, NEXT, QRectF(cx + gap - big * 0.425, by - big * 0.425, big * 0.85, big * 0.85), col, glass=True)
        k = self._kind()
        if k in ("radio", "episode"):
            self._btn(p, REC_STOP if self.recording else REC, QRectF(cx + gap * 2 - 15, by - 15, 30, 30), col)
        else:
            self._plus_check(p, QRectF(cx + gap * 2 - 15, by - 15, 30, 30), self._is_fav())
        self._edge(p, rect, radius)
        self._toast(p, rect)

    def _plus_check(self, p, rect, fav):
        hov = self._hover == "fav"
        col = QColor(ORANGE.q()) if fav else QColor("white")
        if hov:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 0x22))
            p.drawEllipse(rect.adjusted(-2, -2, 2, 2))
        pen = QPen(col, 2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(rect.adjusted(3, 3, -3, -3))
        f = QFont()
        f.setPixelSize(int(rect.height() * 0.62))
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, "✓" if fav else "+")
        self._hits.append((rect, "fav"))

    def _is_fav(self):
        it = self.player.current
        if not it or it.get("kind") != "track":
            return False
        try:
            r = self.mw.db.one("SELECT fav FROM tracks WHERE id=?", (it.get("id"),))
            return bool(r and r["fav"])
        except Exception:
            return False

    def _wave_seek(self, p, r):
        """Time bar with colourful waves over the played part and a glowing knob (Android WaveSeekBar)."""
        self._seek_rect = r
        p.save()
        p.translate(r.topLeft())
        ds = DS(p, r.width(), r.height())
        w0, h0 = r.width(), r.height()
        kr = 9.0
        left = kr
        w = w0 - 2 * kr
        y = h0 - kr - 2
        th = 4.0
        pos, dur = self._times()
        frac = clamp(pos / dur, 0, 1) if dur > 0 else 0.0
        if self._drag is not None:
            frac = self._drag
        x = left + w * frac
        tm = clock()
        lv = Core.levels
        live = Core.playing
        layers = WaveColours.of(Prefs.waveCols.value)
        shape = int(Prefs.waveShape.value)
        top = h0 - 2 * kr - 6

        def amp(fx, li):
            a = 0.0
            for b in range(3):
                centre = (b * 0.33 + li * 0.13 + (tm * (0.04 + li * 0.01) if live else 0)) % 1
                d = (fx - centre) / 0.12
                a += lv[(b * 5 + li * 3) % len(lv)] * exp(-(d * d))
            return min(a * 0.75, 1.0) * max(0.0, sin(fx * math.pi)) * (1.0 if live else 0.35)

        if x - left > 4:
            if shape == 1:
                for li, c in enumerate(layers):
                    pth = Path()
                    for k in range(51):
                        fx = k / 50
                        py = y - th / 2 - top * amp(fx, li) * (0.55 + 0.45 * sin(fx * 9 + tm * 2 + li))
                        pth.moveTo(left, py) if k == 0 else pth.lineTo(left + (x - left) * fx, py)
                    ds.drawPath(pth, c.copy(alpha=0.3), style=Stroke(7))
                    ds.drawPath(pth, c, style=Stroke(2.2))
            elif shape == 2:
                for li, c in enumerate(layers):
                    up, dn = Path(), Path()
                    half = max(6.0, h0 - y)
                    for k in range(51):
                        fx = k / 50
                        px = left + (x - left) * fx
                        a = amp(fx, li)
                        if k == 0:
                            up.moveTo(px, y - top * a)
                            dn.moveTo(px, y + half * a * 0.6)
                        else:
                            up.lineTo(px, y - top * a)
                            dn.lineTo(px, y + half * a * 0.6)
                    ds.drawPath(up, c.copy(alpha=0.35), style=Stroke(8))
                    ds.drawPath(up, c, style=Stroke(2))
                    ds.drawPath(dn, c.copy(alpha=0.25), style=Stroke(5))
            elif shape == 3:
                bars = max(1, int((x - left) / 9))
                for k in range(bars):
                    fx = (k + 0.5) / bars
                    bh = max(2.0, top * amp(fx, k % 4))
                    ds.drawRoundRect(layers[clamp(k * len(layers) // bars, 0, len(layers) - 1)], Offset(left + k * 9 + 1.5, y - th / 2 - bh), Size(6, bh), CornerRadius(3))
            else:
                for li, c in enumerate(layers):
                    pth = Path().moveTo(left, y)
                    for k in range(41):
                        fx = k / 40
                        pth.lineTo(left + (x - left) * fx, y - th / 2 - top * amp(fx, li))
                    pth.lineTo(x, y).close()
                    ds.drawPath(pth, c.copy(alpha=0.55))
        ds.drawRoundRect(Color(0x66FFFFFF), Offset(x, y - th / 2), Size(max(0.0, left + w - x), th), CornerRadius(th / 2))
        ds.drawRoundRect(Brush.horizontalGradient([Color.White.copy(alpha=0.6), Color.White], left, max(left + 1, x)), Offset(left, y - th / 2), Size(x - left, th), CornerRadius(th / 2))
        glow = Core.palette[0] if lum(Core.palette[0]) >= 0.12 else Color(0xFFFF3B3B)
        ds.drawCircle(Brush.radialGradient([glow.copy(alpha=0.7), Color.Transparent], Offset(x, y), kr * 2.6), kr * 2.6, Offset(x, y))
        ds.drawCircle(Color.White, kr, Offset(x, y))
        ds.drawCircle(glow, kr * 0.72, Offset(x, y))
        p.restore()

    # ---- pill (Viên Thuốc, Tom's Dock)
    def _paint_pill(self, p):
        W, H = self.width(), self.height()
        rect = QRectF(2, 2, W - 4, H - 4)
        st = skinStyle()
        radius = float(st.radius) if st.radius is not None else rect.height() / 2
        tm = clock()
        p.save()
        p.setClipPath(self._rounded(rect, radius))
        p.translate(rect.topLeft())
        w, h = rect.width(), rect.height()
        ds = DS(p, w, h)
        with ds.layer(clamp(float(Prefs.pillAlpha.value), 0.05, 1.0)):
            paintSkin(ds, tm, 0.0)
        if getattr(st, "waves", True) and Prefs.vizOn.value and Prefs.vizPill.value:
            waves(ds, tm, Core.levels, Core.palette, float(Prefs.waveHeight.value), float(Prefs.waveStrength.value))
        paintSkinBorder(ds, radius, st.border)
        p.restore()
        slim = Prefs.skin.value == "slim"
        padv = 8 if slim else 11
        disc = rect.height() - padv * 2
        dr = QRectF(rect.left() + padv + (4 if st.radius is None else 0), rect.top() + padv, disc, disc)
        self._disc(p, dr)
        self._hits.append((dr, "open"))
        x0 = dr.right() + 10
        x1 = rect.right() - (rect.height() / 5 if st.radius is None else 14)
        title, sub, fmt = self._texts()
        tcol = st.text.q()
        scol = st.sub.q() if hasattr(st, "sub") else st.muted.q()
        self._marquee(p, title, QRectF(x0, rect.top() + padv - 2, x1 - x0, 24), fonts.title_font(16), tcol)
        f2 = QFont()
        f2.setPixelSize(12)
        sline = "  ·  ".join(x for x in (sub, fmt) if x)
        if self.recording:
            sline = (sline + "   ● REC").strip()
        self._marquee(p, sline, QRectF(x0, rect.top() + padv + 20, x1 - x0, 18), f2, scol)
        col = buttonColour(st.btn.q() if hasattr(st, "btn") else st.button.q())
        k = self._kind()
        rec_on = k in ("radio", "episode")
        cx = (x0 + x1) / 2
        if not slim:
            by = rect.top() + padv + 56
            if rec_on:
                self._btn(p, REC_STOP if self.recording else REC, QRectF(cx - 62 - 15, by - 15, 30, 30), col)
            else:
                self._btn(p, PREV, QRectF(cx - 60 - 13, by - 13, 26, 26), col)
            self._btn(p, PAUSE if Core.playing else PLAY, QRectF(cx - 18, by - 18, 36, 36), col)
            self._btn(p, NEXT, QRectF(cx + 60 - 13, by - 13, 26, 26), col)
        # time bar with times kept clear of the rounded ends
        ty = rect.bottom() - padv - 8
        f3 = QFont()
        f3.setPixelSize(11)
        p.setFont(f3)
        p.setPen(scol)
        pos, dur = self._times()
        tl = fmt_time(pos)
        tr_ = "LIVE" if k == "radio" else fmt_time(dur)
        fm = QFontMetrics(f3)
        end_pad = 0 if st.radius is not None else rect.height() * 0.08
        p.drawText(QRectF(x0, ty - 8, 60, 16), Qt.AlignLeft | Qt.AlignVCenter, tl)
        right_end = x1 - (60 if slim else 0)
        p.drawText(QRectF(right_end - 60 - end_pad, ty - 8, 60, 16), Qt.AlignRight | Qt.AlignVCenter, tr_)
        bar = QRectF(x0 + fm.horizontalAdvance(tl) + 8, ty - 4, (right_end - end_pad - fm.horizontalAdvance(tr_) - 8) - (x0 + fm.horizontalAdvance(tl) + 8), 8)
        self._time_bar(p, bar)
        if slim:
            if rec_on:
                self._btn(p, REC_STOP if self.recording else REC, QRectF(x1 - 56, ty - 11, 22, 22), col)
            self._btn(p, PAUSE if Core.playing else PLAY, QRectF(x1 - 28, ty - 12, 24, 24), col)
        self._edge(p, rect, radius)
        self._toast(p, rect)

    def _disc(self, p, r):
        p.save()
        c = r.center()
        rad = r.width() / 2
        clip = QPainterPath()
        clip.addEllipse(c, rad, rad)
        p.setClipPath(clip)
        p.translate(c)
        p.rotate(self._disc_angle)
        p.translate(-c)
        if self._img is not None:
            src = self._img
            s = min(src.width(), src.height())
            p.drawImage(r, src, QRectF((src.width() - s) / 2, (src.height() - s) / 2, s, s))
        else:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            g.setColorAt(0, Core.palette[0].q())
            g.setColorAt(1, Core.palette[1].darken(0.6).q())
            p.fillRect(r, g)
            for k in range(1, 6):
                p.setPen(QPen(QColor(255, 255, 255, 30), 1))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(c, rad * k / 6, rad * k / 6)
        p.restore()
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.setBrush(QColor(20, 20, 20))
        p.drawEllipse(c, rad * 0.12, rad * 0.12)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1.2))
        p.drawEllipse(c, rad - 0.6, rad - 0.6)

    def _time_bar(self, p, r):
        self._seek_rect = r.adjusted(-6, -8, 6, 8)
        pos, dur = self._times()
        frac = clamp(pos / dur, 0, 1) if dur > 0 else 0.0
        if self._drag is not None:
            frac = self._drag
        cols = BarColours.colours(Prefs.barColour.value, Core.palette)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 0x55))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        done = QRectF(r.left(), r.top(), max(r.height(), r.width() * frac), r.height())
        if len(cols) > 1:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            for i, c in enumerate(cols):
                g.setColorAt(i / (len(cols) - 1), c.q())
            p.setBrush(g)
        else:
            p.setBrush(cols[0].q())
        p.drawRoundedRect(done, r.height() / 2, r.height() / 2)
        kx = r.left() + r.width() * frac
        p.setBrush(QColor("white"))
        p.drawEllipse(QPointF(kx, r.center().y()), r.height() * 0.9, r.height() * 0.9)

    # ---- mouse
    def _hit(self, pos):
        for rect, name in reversed(self._hits):
            if rect.contains(pos):
                return name
        if self._seek_rect is not None and self._seek_rect.contains(pos):
            return "seek"
        return None

    def mouseMoveEvent(self, e):
        pos = e.position()
        if self.force and self._pressed is None and e.buttons() & Qt.LeftButton:
            e.ignore()
            return
        if self._drag is not None and self._seek_rect is not None:
            r = self._seek_rect
            self._drag = clamp((pos.x() - r.left() - 9) / max(1.0, r.width() - 18), 0, 1)
            self.update()
            return
        h = self._hit(pos)
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.PointingHandCursor if h else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        self._hover = None
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.want_menu.emit(e.globalPosition().toPoint())
            return
        if e.button() != Qt.LeftButton:
            return
        h = self._hit(e.position())
        self._pressed = h
        if h is None and self.force:
            e.ignore()
            return
        if h == "seek":
            r = self._seek_rect
            self._drag = clamp((e.position().x() - r.left() - 9) / max(1.0, r.width() - 18), 0, 1)
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.force and self._pressed is None and self._drag is None:
            e.ignore()
            return
        h = self._hit(e.position())
        pressed = self._pressed
        self._pressed = None
        if self._drag is not None:
            frac = self._drag
            self._drag = None
            dur = self.player.duration() or 0
            if dur > 0:
                self.player.seek(frac * dur)
            self.update()
            return
        if h is None or h != pressed:
            self.update()
            return
        pl = self.player
        if h == "play":
            pl.toggle()
        elif h == "prev":
            pl.prev()
        elif h == "next":
            pl.next()
        elif h == "rec":
            self.want_record.emit()
        elif h == "shuffle":
            pl.set_shuffle(not pl.shuffle)
        elif h == "cast":
            self.want_cast.emit()
        elif h == "fav":
            self.want_fav.emit()
        elif h == "open":
            self.open_now.emit()
        self.update()

    def mouseDoubleClickEvent(self, e):
        if self.style_now() != "card" and Prefs.dblTapColour.value and self._hit(e.position()) in (None, "open"):
            self.show_msg(cycle_skin_colour())

    def wheelEvent(self, e):
        d = 5 if e.angleDelta().y() > 0 else -5
        try:
            v = int(self.mw.db.get("volume") or 80)
        except Exception:
            v = 80
        v = int(clamp(v + d, 0, 100))
        self.mw.db.set("volume", v)
        self.player.set_volume(v)
        if hasattr(self.mw, "vol_slider"):
            self.mw.vol_slider.blockSignals(True)
            self.mw.vol_slider.setValue(v)
            self.mw.vol_slider.blockSignals(False)
        self.show_msg(t("Volume", "Âm Lượng") + f" {v}%")

    # compatibility with the old player bar API
    def retheme(self):
        self.update_height()

    def retranslate(self):
        self.update()

    def compact(self, small):
        pass

    def apply_color(self):
        self.update()
