"""The small window (jetAudio / Winamp style): rounded frameless shell with the edge light around it, the title bar,
the Winamp-like menu bar and the tab bar with the tap effects of the Android navigation bar."""
import math

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMenuBar, QSizeGrip, QToolButton, QVBoxLayout, QWidget)

from ..art.ds import DS
from ..art.edge import paint_edge
from ..art.prefs import Prefs
from ..art.state import Core
from ..art.themes import Themes
from . import theme
from .artplayer import clock, ticker

RADIUS = 18


class ShellFrame(QFrame):
    """Rounded window body painted in the current look; the edge light runs around it while music plays."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("Shell")
        self.setAttribute(Qt.WA_StyledBackground, False)
        ticker().tick.connect(self._tick)

    def _tick(self):
        if Prefs.edgeOn.value and Prefs.edgeWhere.value != "pill" and Prefs.edgeWin.value and Core.playing:
            self.update()

    def radius(self):
        return 0 if self.win.isMaximized() else RADIUS

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        rad = self.radius()
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)
        jt = Themes.now()
        g = QLinearGradient(0, 0, 0, r.height())
        g.setColorAt(0, QColor(theme.c("bg")) if jt.light else jt.top.q())
        g.setColorAt(1, QColor(theme.c("bg")) if jt.light else jt.bottom.q())
        p.fillPath(path, g)
        p.setPen(QPen(QColor(theme.c("line")), 1))
        p.drawPath(path)
        p.end()

    def paint_edge_over(self, p):
        if Prefs.edgeOn.value and Prefs.edgeWhere.value != "pill" and Prefs.edgeWin.value and Core.playing:
            paint_edge(DS(p, self.width(), self.height()), clock(), self.radius() + 2, uri=str((self.win.player.current or {}).get("id", "")))


class EdgeOverlay(QWidget):
    """Transparent layer on top of the whole window for the edge light (mouse goes through)."""

    def __init__(self, shell):
        super().__init__(shell)
        self.shell = shell
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        ticker().tick.connect(self._tick)

    def _tick(self):
        if self.isVisible() and Prefs.edgeOn.value and Core.playing:
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.shell.paint_edge_over(p)
        p.end()


class TitleBar(QFrame):
    """Logo + TOM'S JUKEBOX (brand font never changes) + window buttons. Drag to move, double-click to maximise."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("TitleBar")
        self.setFixedHeight(46)
        h = QHBoxLayout(self)
        h.setContentsMargins(14, 4, 8, 2)
        h.setSpacing(6)
        self.logo = QLabel()
        h.addWidget(self.logo)
        col = QVBoxLayout()
        col.setSpacing(0)
        names = QHBoxLayout()
        names.setSpacing(4)
        self.b_tom = QLabel("TOM'S")
        self.b_tom.setObjectName("BrandTom")
        self.b_name = QLabel("JUKEBOX")
        self.b_name.setObjectName("BrandName")
        names.addWidget(self.b_tom)
        names.addWidget(self.b_name)
        names.addStretch()
        col.addLayout(names)
        self.slogan = QLabel("Focus On One Thing And Do It Well")
        self.slogan.setObjectName("Slogan")
        col.addWidget(self.slogan)
        self.brand_box = QWidget()
        self.brand_box.setLayout(col)
        h.addWidget(self.brand_box)
        h.addStretch()
        self.btns = {}
        for key in ("mini", "pin", "min", "max", "close"):
            b = QToolButton()
            b.setObjectName("WinBtn" if key != "close" else "WinClose")
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(34, 30)
            b.setAutoRaise(True)
            if key == "pin":
                b.setCheckable(True)
            self.btns[key] = b
            h.addWidget(b)
        self._drag = None

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            wh = self.win.windowHandle()
            if wh is not None and hasattr(wh, "startSystemMove") and wh.startSystemMove():
                return
            self._drag = e.globalPosition().toPoint() - self.win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.win.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self.win.toggle_max()


class TabBar(QWidget):
    """The tabs under the player (Đang Phát / Thư Viện / Radio / Podcast / Đĩa CD / Bản Thâu / Giao Diện) with the
    Android navigation tap effects: Sáng Lên, Viên Thuốc Trượt, Nảy Nhẹ, Gợn Sóng, Vệt Sáng Chạy, Chấm Sáng Dưới…"""
    clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.setMouseTracking(True)
        self.tabs = []          # (key, text)
        self.current = None
        self._hover = None
        self._rects = {}
        self._anim_from = None
        self._anim_t0 = 0.0
        self._tap_t0 = -10.0
        self._tap_key = None
        self.badges = set()
        ticker().tick.connect(self._tick)

    def set_tabs(self, tabs):
        self.tabs = list(tabs)
        self.update()

    def set_current(self, key, animate=True):
        if key == self.current:
            return
        if animate and self.current in self._rects:
            self._anim_from = QRectF(self._rects[self.current])
            self._anim_t0 = clock()
        self.current = key
        self.update()

    def _tick(self):
        if clock() - self._anim_t0 < 0.5 or clock() - self._tap_t0 < 0.8:
            self.update()

    def _layout(self):
        f = QFont(self.font())
        f.setBold(True)
        fm = self.fontMetrics()
        x = 8.0
        self._rects = {}
        avail = self.width() - 16
        widths = [fm.horizontalAdvance(t) + 22 for _k, t in self.tabs]
        total = sum(widths) + 4 * (len(widths) - 1)
        scale = min(1.0, avail / max(1, total))
        for (k, txt), w in zip(self.tabs, widths):
            ww = w * scale
            self._rects[k] = QRectF(x, 5, ww, self.height() - 10)
            x += ww + 4 * scale
        return f

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        f = self._layout()
        fx = set((Prefs.navFx.value or "glow").split(","))
        speed = max(0.3, float(Prefs.fxSpeed.value))
        acc = QColor(theme.c("accent"))
        on_acc = QColor(theme.c("on_accent"))
        ink = QColor(theme.c("ink"))
        muted = QColor(theme.c("muted"))
        tnow = clock()
        cur = self._rects.get(self.current)
        # sliding pill
        if cur is not None:
            r = QRectF(cur)
            if "slide" in fx and self._anim_from is not None:
                k = min(1.0, (tnow - self._anim_t0) * 3.2 * speed)
                k = 1 - (1 - k) ** 3
                a = self._anim_from
                r = QRectF(a.left() + (cur.left() - a.left()) * k, cur.top(), a.width() + (cur.width() - a.width()) * k, cur.height())
            if "bounce" in fx and tnow - self._tap_t0 < 0.4:
                s = 1 + 0.08 * math.sin((tnow - self._tap_t0) / 0.4 * math.pi)
                r = QRectF(r.center().x() - r.width() * s / 2, r.center().y() - r.height() * s / 2, r.width() * s, r.height() * s)
            if "glow" in fx:
                for i, al in ((6, 30), (3, 55)):
                    g = QColor(acc)
                    g.setAlpha(al)
                    p.setPen(Qt.NoPen)
                    p.setBrush(g)
                    p.drawRoundedRect(r.adjusted(-i, -i / 2, i, i / 2), r.height() / 2 + i, r.height() / 2 + i)
            p.setPen(Qt.NoPen)
            p.setBrush(acc)
            p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
            if "ripple" in fx and tnow - self._tap_t0 < 0.6:
                k = (tnow - self._tap_t0) / 0.6
                g = QColor(255, 255, 255, int(110 * (1 - k)))
                p.setBrush(g)
                rr = r.width() * (0.3 + k)
                p.save()
                clip = QPainterPath()
                clip.addRoundedRect(r, r.height() / 2, r.height() / 2)
                p.setClipPath(clip)
                p.drawEllipse(r.center(), rr, rr)
                p.restore()
            if "streak" in fx and tnow - self._tap_t0 < 0.7:
                k = (tnow - self._tap_t0) / 0.7
                x = r.left() + r.width() * k
                g = QLinearGradient(x - 20, 0, x + 20, 0)
                g.setColorAt(0, QColor(255, 255, 255, 0))
                g.setColorAt(0.5, QColor(255, 255, 255, 150))
                g.setColorAt(1, QColor(255, 255, 255, 0))
                p.save()
                clip = QPainterPath()
                clip.addRoundedRect(r, r.height() / 2, r.height() / 2)
                p.setClipPath(clip)
                p.fillRect(QRectF(x - 20, r.top(), 40, r.height()), g)
                p.restore()
            if "dot" in fx:
                p.setBrush(acc)
                p.drawEllipse(QPointF(cur.center().x(), self.height() - 2.5), 2.5, 2.5)
        for k, txt in self.tabs:
            r = self._rects[k]
            if k == self._hover and k != self.current:
                hv = QColor(ink)
                hv.setAlpha(22)
                p.setPen(Qt.NoPen)
                p.setBrush(hv)
                p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
            ff = QFont(f)
            ff.setBold(k == self.current)
            p.setFont(ff)
            p.setPen(on_acc if k == self.current else (ink if k == self._hover else muted))
            p.drawText(r, Qt.AlignCenter, txt)
            if k in self.badges:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#FF5252"))
                p.drawEllipse(QPointF(r.right() - 6, r.top() + 5), 3.5, 3.5)
        p.end()

    def mouseMoveEvent(self, e):
        h = None
        for k, r in self._rects.items():
            if r.contains(e.position()):
                h = k
        if h != self._hover:
            self._hover = h
            self.setCursor(Qt.PointingHandCursor if h else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        self._hover = None
        self.update()

    def mouseReleaseEvent(self, e):
        for k, r in self._rects.items():
            if r.contains(e.position()):
                self._tap_t0 = clock()
                self._tap_key = k
                self.clicked.emit(k)
                return


def logo_pixmap(path, size, dpr):
    pm = QPixmap(path).scaled(int(size * dpr), int(size * dpr), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pm.setDevicePixelRatio(dpr)
    return pm


def shell_qss():
    t = theme.CUR["c"]
    jt = Themes.now()
    ink = "#FFFFFF" if not jt.light else t["ink"]
    muted = t["muted"]
    f = theme.pt()
    return f"""
#Shell {{ background: transparent; }}
#TitleBar, #MenuRow, #BtnRow, #TabRow {{ background: transparent; }}
#TitleBar QLabel#BrandTom {{ color: {theme.SKY}; font-family: Bahnschrift, "Segoe UI"; font-weight: 700; font-size: {f + 5}pt; }}
#TitleBar QLabel#BrandName {{ color: {theme.ORANGE}; font-family: Bahnschrift, "Segoe UI"; font-weight: 700; font-size: {f + 5}pt; }}
#TitleBar QLabel#Slogan {{ color: {muted}; font-size: {f - 2.5}pt; }}
#TitleBar QToolButton {{ background: transparent; border: none; border-radius: 8px; color: {ink}; }}
#TitleBar QToolButton:hover {{ background: rgba(255,255,255,0.12); }}
#TitleBar QToolButton:checked {{ background: {t['accent']}; }}
#TitleBar QToolButton#WinClose:hover {{ background: #E5484D; }}
QMenuBar#Winamp {{ background: transparent; color: {ink}; font-weight: 600; padding: 0 6px; }}
QMenuBar#Winamp::item {{ padding: 3px 10px; border-radius: 7px; background: transparent; color: {ink}; }}
QMenuBar#Winamp::item:selected {{ background: rgba(255,255,255,0.12); }}
QMenuBar#Winamp::item:pressed {{ background: {t['accent']}; color: {t['on_accent']}; }}
#BtnRow QToolButton {{ background: transparent; border: none; border-radius: 15px; padding: 4px; color: {ink}; }}
#BtnRow QToolButton:hover {{ background: rgba(255,255,255,0.12); }}
#BtnRow QToolButton#Toggle {{ border: 1px solid {t['line']}; border-radius: 13px; padding: 3px 12px; font-weight: 700; color: {ink}; }}
#BtnRow QToolButton#Toggle:checked {{ background: {t['accent']}; color: {t['on_accent']}; border-color: {t['accent']}; }}
#BtnRow QLabel {{ color: {muted}; }}
#Panel {{ background: {t['bg']}; border-radius: 14px; border: 1px solid {t['line']}; }}
#LibChips QToolButton {{ background: {t['card']}; border: 1px solid {t['line']}; border-radius: 14px; padding: 4px 12px; font-weight: 600; }}
#LibChips QToolButton:checked {{ background: {t['accent']}; color: {t['on_accent']}; border-color: {t['accent']}; }}
QStatusBar#ShellStatus {{ background: transparent; border-top: none; }}
QStatusBar#ShellStatus QLabel {{ color: {muted}; }}
QStatusBar#ShellStatus QToolButton {{ color: {ink}; }}
"""
