"""Opening animation (6 styles, like the Android app): Icon Nở Ra, Đĩa Quay Vào, Sóng Nhạc Đánh Thức, Hình Khối Biến Hình,
Theo Màu Ảnh Bìa, Ngẫu Nhiên. Drawn at the screen's real resolution (sharp at 150–200 %)."""
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .. import app_info
from ..art.prefs import Prefs
from ..art.state import Core


class AnimatedSplash(QWidget):
    def __init__(self, dpr, on_done):
        super().__init__(None, Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        from .dialogs import splash_pixmap
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.base = splash_pixmap(dpr, logo_on=False)
        self.logo = QPixmap(app_info.asset("app_icon_1024.png"))
        self.setFixedSize(640, 400)
        st = int(Prefs.splashStyle.value)
        self.style = random.randint(0, 4) if st == 5 else st
        self.dur = 0.75 if Prefs.splashFast.value else 1.25
        self.on_done = on_done
        self.t0 = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self._done = False

    def _tick(self):
        self.update()

    def finish_when_ready(self):
        """Called once the main window is built: close when the animation has played."""
        left = self.dur - (time.monotonic() - self.t0)
        QTimer.singleShot(int(max(0, left) * 1000) + 120, self._finish)

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self.close()
        self.on_done()

    def mousePressEvent(self, e):
        self._finish()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 22, 22)
        p.setClipPath(clip)
        p.drawPixmap(self.rect(), self.base)
        k = min(1.0, (time.monotonic() - self.t0) / self.dur)
        e_ = 1 - (1 - k) ** 3
        cx, cy, r = 320.0, 104.0, 70.0
        s = self.style
        if s == 0:                                   # Icon Nở Ra
            sc = 0.4 + 0.6 * e_ + 0.06 * math.sin(k * math.pi)
            self._logo(p, cx, cy, r * sc, 1.0 * min(1, k * 2))
            p.setPen(QPen(QColor(251, 176, 64, int(160 * (1 - k))), 3))
            p.drawEllipse(QPointF(cx, cy), r * (0.8 + k * 0.9), r * (0.8 + k * 0.9))
        elif s == 1:                                 # Đĩa Quay Vào
            x = -80 + (cx + 80) * e_
            p.save()
            p.translate(x, cy)
            p.rotate(-360 * (1 - e_) * 1.5)
            p.translate(-x, -cy)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(17, 17, 17))
            p.drawEllipse(QPointF(x, cy), r, r)
            for g in range(5):
                p.setPen(QPen(QColor(255, 255, 255, 30), 1))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(x, cy), r * (0.45 + g * 0.1), r * (0.45 + g * 0.1))
            p.restore()
            self._logo(p, x, cy, r * 0.62, 1.0)
        elif s == 2:                                 # Sóng Nhạc Đánh Thức
            for i in range(24):
                h = (10 + 40 * abs(math.sin(i * 0.7 + k * 9))) * (1 - abs(k - 0.5) * 1.6 if k < 0.8 else 0.2)
                x = cx - 168 + i * 14
                col = QColor(72, 176, 200) if i % 2 == 0 else QColor(251, 176, 64)
                col.setAlpha(int(220 * (1 - k * 0.7)))
                p.setPen(Qt.NoPen)
                p.setBrush(col)
                p.drawRoundedRect(QRectF(x, cy - max(2, h) / 2, 8, max(2, h)), 4, 4)
            self._logo(p, cx, cy, r * min(1, max(0, (k - 0.35) / 0.65)), min(1.0, max(0.0, (k - 0.3) * 2)))
        elif s == 3:                                 # Hình Khối Biến Hình
            rad = r * (1 - e_) * 0.9 + 6
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(251, 176, 64, int(200 * (1 - k))))
            p.save()
            p.translate(cx, cy)
            p.rotate(90 * e_)
            p.drawRoundedRect(QRectF(-r, -r, 2 * r, 2 * r), rad, rad)
            p.restore()
            self._logo(p, cx, cy, r * e_, e_)
        else:                                        # Theo Màu Ảnh Bìa
            cols = [c.q() for c in Core.palette[:4]]
            for i, c in enumerate(cols):
                a = k * math.pi * 2 + i * math.pi / 2
                c.setAlpha(int(150 * (1 - k * 0.6)))
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                p.drawEllipse(QPointF(cx + math.cos(a) * 60 * (1 - k), cy + math.sin(a) * 30 * (1 - k)), r * 0.9, r * 0.9)
            self._logo(p, cx, cy, r * (0.6 + 0.4 * e_), min(1.0, k * 1.5))
        p.end()

    def _logo(self, p, x, y, r, alpha):
        if r <= 1:
            return
        p.save()
        p.setOpacity(max(0.0, min(1.0, alpha)))
        p.drawPixmap(QRectF(x - r, y - r, 2 * r, 2 * r), self.logo, QRectF(self.logo.rect()))
        p.restore()
