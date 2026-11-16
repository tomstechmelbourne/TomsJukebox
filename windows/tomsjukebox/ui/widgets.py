"""Shared widgets: covers, spinning disc, sound-wave seek bar, pill player bar (Samsung Music style)."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMenu, QSizePolicy, QSlider, QToolButton,
                               QVBoxLayout, QWidget)

from .. import tags
from ..i18n import tr
from . import theme
from .icons import icon

_pm_cache = {}


def fmt_time(s):
    s = int(max(0, s or 0))
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def placeholder(size, seed="", radius=12):
    key = ("ph", size, seed[:20], radius, theme.CUR["key"])
    if key in _pm_cache:
        return _pm_cache[key]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    h = (sum(ord(c) for c in seed) * 37) % 360 if seed else 195
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor.fromHsv(h, 90, 120))
    g.setColorAt(1, QColor.fromHsv((h + 40) % 360, 120, 70))
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    p.fillPath(path, QBrush(g))
    ic = icon("note", "#FFFFFF", max(16, size // 2))
    p.setOpacity(0.85)
    s2 = max(16, size // 2)
    p.drawPixmap((size - s2) // 2, (size - s2) // 2, ic.pixmap(s2, s2))
    p.end()
    _pm_cache[key] = pm
    return pm


def cover_pixmap(art_key, size, radius=12, seed="", dpr=1.0):
    real = int(size * dpr)
    key = (art_key, real, radius)
    if art_key and key in _pm_cache:
        return _pm_cache[key]
    path = tags.art_path(art_key, small=real <= 170) if art_key else None
    if not path:
        pm = placeholder(real, seed, int(radius * dpr))
        pm = QPixmap(pm)
        pm.setDevicePixelRatio(dpr)
        return pm
    src = QPixmap(path)
    if src.isNull():
        return placeholder(real, seed, radius)
    src = src.scaled(real, real, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    pm = QPixmap(real, real)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, real, real), radius * dpr, radius * dpr)
    p.setClipPath(clip)
    p.drawPixmap(0, 0, src)
    p.end()
    pm.setDevicePixelRatio(dpr)
    if len(_pm_cache) > 1500:
        _pm_cache.clear()
    _pm_cache[key] = pm
    return pm


def dominant_color(art_key, default="#0E88AA"):
    path = tags.art_path(art_key, small=True) if art_key else None
    if not path:
        return QColor(default)
    img = QImage(path)
    if img.isNull():
        return QColor(default)
    img = img.scaled(24, 24)
    best, score = QColor(default), -1
    for y in range(24):
        for x in range(24):
            c = QColor(img.pixel(x, y))
            sc = c.saturationF() * 1.6 + (1 - abs(c.valueF() - 0.6))
            if sc > score:
                score, best = sc, c
    return best


def readable_on_dark(c: QColor):
    """Make a colour bright enough for the dark player groove."""
    h, s, v, _a = c.getHsvF()
    return QColor.fromHsvF(max(0.0, h), min(1.0, max(0.45, s)), max(0.78, v))


class Cover(QLabel):
    clicked = Signal()

    def __init__(self, size=56, radius=12, parent=None):
        super().__init__(parent)
        self.sz, self.radius = size, radius
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.set_key(None)

    def set_key(self, key, seed=""):
        self.setPixmap(cover_pixmap(key, self.sz, self.radius, seed, self.devicePixelRatioF()))

    def mousePressEvent(self, e):
        self.clicked.emit()


class SpinningDisc(QWidget):
    """A record that spins while music plays, with the album cover as its label."""
    clicked = Signal()

    def __init__(self, size=56, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.angle = 0.0
        self.playing = False
        self.cover = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.setCursor(Qt.PointingHandCursor)

    def set_key(self, key, seed=""):
        s = int(self.width() * 0.56 * self.devicePixelRatioF())
        self.cover = cover_pixmap(key, s / self.devicePixelRatioF(), 999, seed, self.devicePixelRatioF())
        self.update()

    def set_playing(self, on):
        self.playing = on
        if on:
            self.timer.start(40)
        else:
            self.timer.stop()

    def _step(self):
        self.angle = (self.angle + 3.0) % 360
        self.update()

    def mousePressEvent(self, e):
        self.clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w = self.width()
        c = QPointF(w / 2, w / 2)
        r = w / 2 - 1
        g = QRadialGradient(c, r)
        g.setColorAt(0, QColor("#2A2F36"))
        g.setColorAt(0.7, QColor("#111418"))
        g.setColorAt(1, QColor("#05070A"))
        p.setBrush(QBrush(g))
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r, r)
        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        for k in range(4):
            rr = r * (0.62 + k * 0.09)
            p.drawEllipse(c, rr, rr)
        p.save()
        p.translate(c)
        p.rotate(self.angle)
        if self.cover is not None:
            cw = self.cover.width() / self.cover.devicePixelRatio()
            p.drawPixmap(QPointF(-cw / 2, -cw / 2), self.cover)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
        p.drawArc(QRectF(-r * 0.85, -r * 0.85, r * 1.7, r * 1.7), 20 * 16, 40 * 16)
        p.restore()
        p.setBrush(QColor("#0B0D10"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, w * 0.04, w * 0.04)


class WaveSeek(QWidget):
    """Seek bar on a dark groove with a sound wave rising and falling behind it (colour selectable)."""
    seeked = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.levels = np.zeros(48)
        self.pos = 0.0
        self.dur = 0.0
        self.color = QColor(theme.ORANGE)
        self.live = False
        self.drag = None
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def set_levels(self, lv):
        self.levels = self.levels * 0.55 + np.asarray(lv) * 0.45
        self.update()

    def set_pos(self, pos, dur):
        if self.drag is None:
            self.pos, self.dur = pos, dur
            self.update()

    def _frac_at(self, x):
        m = 10
        return max(0.0, min(1.0, (x - m) / max(1, self.width() - 2 * m)))

    def mousePressEvent(self, e):
        if self.dur > 0 and not self.live:
            self.drag = self._frac_at(e.position().x())
            self.update()

    def mouseMoveEvent(self, e):
        if self.drag is not None:
            self.drag = self._frac_at(e.position().x())
            self.update()

    def mouseReleaseEvent(self, e):
        if self.drag is not None:
            f = self.drag
            self.drag = None
            self.pos = f * self.dur
            self.seeked.emit(f * self.dur)
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        m = 10
        mid = h / 2
        # sound wave behind (mirrored bars)
        n = len(self.levels)
        bw = (w - 2 * m) / n
        wave = QColor(self.color)
        wave.setAlpha(80)
        p.setPen(Qt.NoPen)
        p.setBrush(wave)
        for i, v in enumerate(self.levels):
            bh = max(2.0, v * (h - 6))
            x = m + i * bw
            p.drawRoundedRect(QRectF(x + bw * 0.2, mid - bh / 2, bw * 0.6, bh), 1.5, 1.5)
        # groove
        groove = QRectF(m, mid - 3.5, w - 2 * m, 7)
        p.setBrush(QColor(0, 0, 0, 120) if not theme.c("dark") and theme.CUR["key"] == "soft" else QColor(0, 0, 0, 150))
        p.drawRoundedRect(groove, 3.5, 3.5)
        if self.live:
            p.setBrush(self.color)
            p.drawRoundedRect(groove, 3.5, 3.5)
            return
        f = self.drag if self.drag is not None else (self.pos / self.dur if self.dur > 0 else 0)
        f = max(0.0, min(1.0, f))
        done = QRectF(m, mid - 3.5, (w - 2 * m) * f, 7)
        p.setBrush(self.color)
        p.drawRoundedRect(done, 3.5, 3.5)
        kx = m + (w - 2 * m) * f
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(QPen(self.color, 2.5))
        p.drawEllipse(QPointF(kx, mid), 7.5, 7.5)


def tool(name, tip, color=None, size=22, checkable=False):
    b = QToolButton()
    b.setIcon(icon(name, color or theme.c("player_ink"), size))
    b.setIconSize(QSize(size, size))
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    b.setAutoRaise(True)
    b.setProperty("iconName", name)
    return b


class PillPlayer(QWidget):
    """Bottom player bar: pill shape, spinning disc, title, controls, sound-wave seek, extras."""
    open_now = Signal()
    want_lyrics = Signal()
    want_queue = Signal()
    want_eq = Signal()
    want_cast = Signal()
    want_visual = Signal()
    want_color = Signal(str)

    def __init__(self, player, db, parent=None):
        super().__init__(parent)
        self.setObjectName("PlayerBar")
        self.player, self.db = player, db
        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 6, 14, 8)
        self.pill = QFrame()
        self.pill.setObjectName("Pill")
        self.pill.setMinimumHeight(70)
        outer.addWidget(self.pill)
        lay = QHBoxLayout(self.pill)
        lay.setContentsMargins(10, 6, 18, 6)
        lay.setSpacing(8)
        self.disc = SpinningDisc(56)
        self.disc.clicked.connect(self.open_now)
        lay.addWidget(self.disc)
        info = QVBoxLayout()
        info.setSpacing(0)
        self.title = QLabel(tr("nothing_playing"))
        self.title.setCursor(Qt.PointingHandCursor)
        f = self.title.font()
        f.setBold(True)
        self.title.setFont(f)
        self.sub = QLabel("")
        self.sub.setObjectName("PillSub")
        for lab in (self.title, self.sub):
            lab.setMinimumWidth(80)
            lab.setMaximumWidth(260)
            lab.mousePressEvent = lambda e: self.open_now.emit()
        info.addStretch()
        info.addWidget(self.title)
        info.addWidget(self.sub)
        info.addStretch()
        lay.addLayout(info, 2)
        self.b_shuffle = tool("shuffle", tr("shuffle"), checkable=True)
        self.b_prev = tool("prev", tr("prev"), size=24)
        self.b_play = tool("play", tr("play"), theme.c("player"), 26)
        self.b_play.setObjectName("PlayBtn")
        self.b_play.setFixedSize(48, 48)
        self.b_next = tool("next", tr("next"), size=24)
        self.b_repeat = tool("repeat", tr("repeat"), checkable=True)
        for b in (self.b_shuffle, self.b_prev, self.b_play, self.b_next, self.b_repeat):
            lay.addWidget(b)
        mid = QVBoxLayout()
        mid.setSpacing(0)
        self.wave = WaveSeek()
        self.wave.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wave.customContextMenuRequested.connect(self._color_menu)
        times = QHBoxLayout()
        self.t_pos = QLabel("0:00")
        self.t_pos.setObjectName("PillSub")
        self.t_dur = QLabel("0:00")
        self.t_dur.setObjectName("PillSub")
        times.addWidget(self.t_pos)
        times.addStretch()
        self.badge = QLabel("")
        self.badge.setObjectName("PillSub")
        times.addWidget(self.badge)
        times.addStretch()
        times.addWidget(self.t_dur)
        mid.addStretch()
        mid.addWidget(self.wave)
        mid.addLayout(times)
        mid.addStretch()
        lay.addLayout(mid, 5)
        self.b_lyrics = tool("lyrics", tr("lyrics"))
        self.b_queue = tool("queue", tr("queue"))
        self.b_eq = tool("eq", tr("eq"))
        self.b_cast = tool("cast", tr("cast"))
        self.b_visual = tool("fullscreen", tr("visual"))
        self.b_vol = tool("volume", tr("mute"))
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setFixedWidth(90)
        self.vol.setValue(int(db.get("volume")))
        self.vol.setToolTip(tr("volume"))
        for b in (self.b_lyrics, self.b_queue, self.b_eq, self.b_cast, self.b_visual, self.b_vol):
            lay.addWidget(b)
        lay.addWidget(self.vol)
        # wiring
        self.b_play.clicked.connect(player.toggle)
        self.b_next.clicked.connect(player.next)
        self.b_prev.clicked.connect(player.prev)
        self.b_shuffle.setChecked(player.shuffle)
        self.b_shuffle.toggled.connect(player.set_shuffle)
        self.b_repeat.clicked.connect(self._repeat)
        self.b_lyrics.clicked.connect(self.want_lyrics)
        self.b_queue.clicked.connect(self.want_queue)
        self.b_eq.clicked.connect(self.want_eq)
        self.b_cast.clicked.connect(self.want_cast)
        self.b_visual.clicked.connect(self.want_visual)
        self.b_vol.clicked.connect(self._mute)
        self.vol.valueChanged.connect(player.set_volume)
        self.wave.seeked.connect(player.seek)
        player.changed.connect(self.on_changed)
        player.state.connect(self.on_state)
        player.radio_title.connect(lambda t: self.sub.setText(t))
        self._repeat_icon()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)
        self.apply_color()

    def compact(self, small):
        for b in (self.b_visual, self.b_cast):
            b.setVisible(not small)
        self.vol.setFixedWidth(60 if small else 90)

    def retheme(self):
        for b in (self.b_shuffle, self.b_prev, self.b_next, self.b_repeat, self.b_lyrics, self.b_queue,
                  self.b_eq, self.b_cast, self.b_visual, self.b_vol):
            b.setIcon(icon(b.property("iconName"), theme.c("player_ink"), 22 if b not in (self.b_prev, self.b_next) else 24))
        self._repeat_icon()
        self.on_state(self.player.is_playing())
        self.apply_color()

    def retranslate(self):
        for b, k in ((self.b_shuffle, "shuffle"), (self.b_prev, "prev"), (self.b_next, "next"), (self.b_lyrics, "lyrics"),
                     (self.b_queue, "queue"), (self.b_eq, "eq"), (self.b_cast, "cast"), (self.b_visual, "visual"),
                     (self.b_vol, "mute")):
            b.setToolTip(tr(k))
        self.vol.setToolTip(tr("volume"))
        if self.player.current is None:
            self.title.setText(tr("nothing_playing"))
        self._repeat_icon()

    def _color_menu(self, pos):
        m = QMenu(self)
        cur = self.db.get("bar_color")
        from ..i18n import lang
        for en, vi, val in theme.BAR_COLORS:
            a = m.addAction(vi if lang() == "vi" else en)
            a.setCheckable(True)
            a.setChecked(val == cur)
            a.triggered.connect(lambda _=False, v=val: self.want_color.emit(v))
        m.exec(self.wave.mapToGlobal(pos))

    def apply_color(self):
        val = self.db.get("bar_color") or theme.ORANGE
        if theme.CUR["key"] == "contrast":
            col = QColor("#FFFF00")
        elif val == "cover":
            cur = self.player.current or {}
            col = readable_on_dark(dominant_color(cur.get("art_key")))
        else:
            col = QColor(val)
        self.wave.color = col
        self.wave.update()

    def _repeat(self):
        self.player.cycle_repeat()
        self._repeat_icon()

    def _repeat_icon(self):
        r = self.player.repeat
        self.b_repeat.setChecked(r != "off")
        self.b_repeat.setIcon(icon("repeat1" if r == "one" else "repeat", theme.c("accent") if r != "off" else theme.c("player_ink"), 22))
        self.b_repeat.setToolTip({"off": tr("repeat_off"), "all": tr("repeat_all"), "one": tr("repeat_one")}[r])
        self.b_shuffle.setIcon(icon("shuffle", theme.c("accent") if self.player.shuffle else theme.c("player_ink"), 22))

    def _mute(self):
        e = self.player.engine
        e.muted = not e.muted
        self.b_vol.setIcon(icon("mute" if e.muted else "volume", theme.c("player_ink"), 22))

    def on_changed(self, it):
        if it is None:
            self.title.setText(tr("nothing_playing"))
            self.sub.setText("")
            self.disc.set_key(None)
            return
        self.title.setText(it.title)
        self.title.setToolTip(it.title)
        k = it.get("kind")
        sub = it.get("artist") or ""
        if k == "radio":
            sub = it.get("now_title") or it.get("artist") or ""
        self.sub.setText(sub)
        self.disc.set_key(it.get("art_key"), it.title)
        self.wave.live = k == "radio"
        self.badge.setText(tr("live") if k == "radio" else (it.get("codec") or ""))
        self.apply_color()
        self.b_shuffle.setIcon(icon("shuffle", theme.c("accent") if self.player.shuffle else theme.c("player_ink"), 22))

    def on_state(self, playing):
        self.b_play.setIcon(icon("pause" if playing else "play", theme.c("player"), 26))
        self.b_play.setToolTip(tr("pause") if playing else tr("play"))
        self.disc.set_playing(playing)

    def _tick(self):
        pl = self.player
        if pl.current is None:
            return
        pos, dur = pl.position(), pl.duration()
        self.wave.set_pos(pos, dur)
        self.t_pos.setText(fmt_time(pos))
        self.t_dur.setText(fmt_time(dur) if dur else ("●" if pl.current.get("kind") == "radio" else "0:00"))
        if pl.is_playing() and pl.cast is None:
            self.wave.set_levels(pl.engine.levels(48))
        else:
            self.wave.set_levels(np.zeros(48))


class Banner(QFrame):
    """Inline message strip with up to two buttons (e.g. 'You are now in NSW. Switch?')."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Strip")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 8, 8)
        self.ic = QLabel()
        self.text = QLabel()
        self.text.setWordWrap(True)
        lay.addWidget(self.ic)
        lay.addWidget(self.text, 1)
        self.btns = QHBoxLayout()
        lay.addLayout(self.btns)
        x = QToolButton()
        x.setIcon(icon("close", theme.c("muted"), 16))
        x.clicked.connect(self.hide)
        lay.addWidget(x)
        self.hide()

    def show_msg(self, text, buttons=(), icon_name="info"):
        from PySide6.QtWidgets import QPushButton
        while self.btns.count():
            w = self.btns.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        self.ic.setPixmap(icon(icon_name, theme.c("teal"), 22).pixmap(22, 22))
        self.text.setText(text)
        for label, cb, primary in buttons:
            b = QPushButton(label)
            if primary:
                b.setObjectName("Primary")
            b.clicked.connect(lambda _=False, f=cb: (f(), self.hide()))
            self.btns.addWidget(b)
        self.show()


def h1(text):
    lab = QLabel(text)
    lab.setObjectName("H1")
    return lab


def h2(text):
    lab = QLabel(text)
    lab.setObjectName("H2")
    return lab


def hint(text):
    lab = QLabel(text)
    lab.setObjectName("Hint")
    lab.setWordWrap(True)
    return lab


def bold_font(w, extra=0):
    f = QFont(w.font())
    f.setBold(True)
    if extra:
        f.setPointSizeF(f.pointSizeF() + extra)
    return f


def angle_wave(t, i):
    return 0.5 + 0.5 * math.sin(t * 3 + i * 0.4)
