"""Hẹn Giờ Tắt Nhạc (sleep timer): after some minutes, at the end of this song or at the end of the queue, with a gentle fade."""
import time

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QVBoxLayout)

from ..art.prefs import Prefs
from ..art.themes import t
from .widgets import fmt_time, h2, hint


class SleepTimer(QObject):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.mode = "NONE"          # NONE / TIME / END_TRACK / END_QUEUE
        self.until = 0.0
        self.fade = 60
        self._vol0 = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(500)
        win.player.changed.connect(self._changed)

    def remaining(self):
        if self.mode != "TIME":
            return -1
        return max(0, self.until - time.time())

    def start_minutes(self, m, fade):
        self.cancel()
        self.mode = "TIME"
        self.until = time.time() + m * 60
        self.fade = fade
        Prefs.sleepMinutes.value = int(m)
        Prefs.sleepFade.value = int(fade)

    def start_end(self, which):
        self.cancel()
        self.mode = which

    def cancel(self):
        self.mode = "NONE"
        if self._vol0 is not None:
            self.win.player.set_volume(self._vol0)
            self._vol0 = None

    def _changed(self, it):
        if self.mode == "END_TRACK" and getattr(self, "_seen", None) is not None and it is not self._seen:
            self._stop()
        self._seen = it

    def _tick(self):
        p = self.win.player
        if self.mode == "TIME":
            rem = self.remaining()
            if rem <= 0:
                self._stop()
            elif rem <= self.fade and self.fade > 0:
                if self._vol0 is None:
                    self._vol0 = int(self.win.db.get("volume") or 80)
                p.set_volume(int(self._vol0 * rem / self.fade))
        elif self.mode == "END_QUEUE":
            if p.current is None or (not p.upcoming() and not p.is_playing()):
                self._stop()
        elif self.mode == "END_TRACK":
            if getattr(self, "_seen", None) is None:
                self._seen = p.current

    def _stop(self):
        p = self.win.player
        if p.is_playing():
            p.toggle()
        vol = self._vol0
        self.mode = "NONE"
        self._vol0 = None
        if vol is not None:
            QTimer.singleShot(400, lambda: p.set_volume(vol))
        self.win.toast(t("Sleep timer: music stopped", "Hẹn giờ: đã tắt nhạc"))

    def badge(self):
        if self.mode == "TIME":
            return "⏾ " + fmt_time(self.remaining())
        if self.mode in ("END_TRACK", "END_QUEUE"):
            return "⏾"
        return ""


class SleepDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        if not hasattr(win, "sleep"):
            win.sleep = SleepTimer(win)
        st = win.sleep
        self.setWindowTitle(t("Sleep Timer", "Hẹn Giờ Tắt Nhạc"))
        v = QVBoxLayout(self)
        v.addWidget(h2(t("Stop The Music After", "Tắt Nhạc Sau")))
        grid = QGridLayout()
        for i, m in enumerate((10, 15, 20, 30, 45, 60, 90, 120)):
            b = QPushButton(t(f"{m} min", f"{m} phút"))
            b.clicked.connect(lambda _=False, mm=m: self._go(mm))
            grid.addWidget(b, i // 4, i % 4)
        v.addLayout(grid)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("Or choose minutes:", "Hoặc chọn số phút:")))
        self.mins = QSpinBox()
        self.mins.setRange(1, 600)
        self.mins.setValue(int(Prefs.sleepMinutes.value))
        row.addWidget(self.mins)
        ok = QPushButton(t("Start", "Bắt Đầu"))
        ok.setObjectName("Primary")
        ok.clicked.connect(lambda: self._go(self.mins.value()))
        row.addWidget(ok)
        row.addStretch()
        v.addLayout(row)
        row2 = QHBoxLayout()
        b1 = QPushButton(t("At The End Of This Song", "Hết Bài Này"))
        b1.clicked.connect(lambda: (st.start_end("END_TRACK"), self.accept()))
        b2 = QPushButton(t("At The End Of The Queue", "Hết Danh Sách"))
        b2.clicked.connect(lambda: (st.start_end("END_QUEUE"), self.accept()))
        row2.addWidget(b1)
        row2.addWidget(b2)
        v.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel(t("Fade out over (seconds):", "Nhỏ dần trong (giây):")))
        self.fade = QSpinBox()
        self.fade.setRange(0, 300)
        self.fade.setValue(int(Prefs.sleepFade.value))
        row3.addWidget(self.fade)
        row3.addStretch()
        v.addLayout(row3)
        self.state = hint("")
        v.addWidget(self.state)
        bb = QHBoxLayout()
        cancel = QPushButton(t("Turn Off Sleep Timer", "Tắt Hẹn Giờ"))
        cancel.clicked.connect(lambda: (st.cancel(), self._show()))
        close = QPushButton(t("Close", "Đóng"))
        close.clicked.connect(self.accept)
        bb.addWidget(cancel)
        bb.addStretch()
        bb.addWidget(close)
        v.addLayout(bb)
        self._show()

    def _go(self, m):
        self.win.sleep.start_minutes(m, self.fade.value())
        self.accept()

    def _show(self):
        st = self.win.sleep
        if st.mode == "TIME":
            self.state.setText(t("Music stops in ", "Nhạc sẽ tắt sau ") + fmt_time(st.remaining()))
        elif st.mode == "END_TRACK":
            self.state.setText(t("Music stops at the end of this song.", "Nhạc sẽ tắt khi hết bài này."))
        elif st.mode == "END_QUEUE":
            self.state.setText(t("Music stops at the end of the queue.", "Nhạc sẽ tắt khi hết danh sách."))
        else:
            self.state.setText(t("The sleep timer is off.", "Chưa hẹn giờ tắt nhạc."))


def _unused():
    return QButtonGroup, QCheckBox, Qt
