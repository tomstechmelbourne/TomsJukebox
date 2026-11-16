"""Phím Tắt (all menu shortcuts, Tom can change each one) and the full-screen visualisation with the 83 styles."""
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QKeySequenceEdit, QLabel, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from ..art import fonts
from ..art.ds import DS
from ..art.prefs import Prefs
from ..art.state import Core
from ..art.themes import VizStyles, t
from ..art.viz import drawViz
from .artplayer import clock, ticker


def saved(db):
    try:
        return json.loads(db.get("shortcuts") or "{}")
    except Exception:
        return {}


class ShortcutsDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle(t("Keyboard Shortcuts", "Phím Tắt"))
        self.resize(620, 640)
        v = QVBoxLayout(self)
        lab = QLabel(t("Click a shortcut and press the new keys. Single letters work like Winamp (Z X C V B).",
                       "Bấm vào ô phím tắt rồi nhấn tổ hợp phím mới. Phím một chữ giống Winamp (Z X C V B)."))
        lab.setWordWrap(True)
        lab.setObjectName("Hint")
        v.addWidget(lab)
        self.tab = QTableWidget(0, 2)
        self.tab.setHorizontalHeaderLabels([t("Action", "Việc"), t("Shortcut", "Phím Tắt")])
        self.tab.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tab.verticalHeader().hide()
        self.edits = []
        for a in win.actions():
            if a.shortcut().isEmpty() and not a.property("defKey"):
                continue
            r = self.tab.rowCount()
            self.tab.insertRow(r)
            self.tab.setItem(r, 0, QTableWidgetItem(a.text().replace("&", "")))
            e = QKeySequenceEdit(a.shortcut())
            self.tab.setCellWidget(r, 1, e)
            self.edits.append((a, e))
        v.addWidget(self.tab, 1)
        h = QHBoxLayout()
        reset = QPushButton(t("Back To The Original Keys", "Trả Về Phím Gốc"))
        reset.clicked.connect(self._reset)
        ok = QPushButton(t("Save", "Lưu"))
        ok.setObjectName("Primary")
        ok.clicked.connect(self._save)
        h.addWidget(reset)
        h.addStretch()
        h.addWidget(ok)
        v.addLayout(h)

    def _save(self):
        d = {}
        for a, e in self.edits:
            key = a.property("actKey")
            if key:
                d[key] = e.keySequence().toString()
        self.win.db.set("shortcuts", json.dumps(d))
        self.win._build_menus()
        self.accept()

    def _reset(self):
        self.win.db.set("shortcuts", "{}")
        self.win._build_menus()
        self.accept()


class Visualizer(QWidget):
    """Full-screen visualisation. ↑ ↓ change style · ← → song · Space play/pause · Esc close."""

    def __init__(self, win):
        super().__init__(None)
        self.win = win
        self.setWindowTitle(t("Full Screen Visuals", "Hình Ảnh Theo Nhạc Toàn Màn Hình"))
        self.setCursor(Qt.BlankCursor)
        self.style = VizStyles.autoPick(clock()) if Prefs.vizAuto.value else int(Prefs.viz.value)
        self._msg_t = clock()
        ticker().tick.connect(self.update)

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key_Escape, Qt.Key_F11):
            self.close()
        elif k == Qt.Key_Space:
            self.win.player.toggle()
        elif k == Qt.Key_Right:
            self.win.player.next()
        elif k == Qt.Key_Left:
            self.win.player.prev()
        elif k in (Qt.Key_Up, Qt.Key_Down):
            n = VizStyles.count()
            s = self.style
            while True:
                s = (s + (1 if k == Qt.Key_Down else -1)) % n
                if s not in VizStyles.removed:
                    break
            self.style = s
            Prefs.viz.value = s
            self._msg_t = clock()

    def mouseDoubleClickEvent(self, e):
        self.close()

    def closeEvent(self, e):
        try:
            ticker().tick.disconnect(self.update)
        except Exception:
            pass
        super().closeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(4, 10, 16))
        tm = clock()
        st = VizStyles.autoPick(tm) if Prefs.vizAuto.value else self.style
        drawViz(DS(p, self.width(), self.height()), st, tm * VizStyles.speed(), Core.levels, Core.palette)
        it = self.win.player.current
        if it:
            f = fonts.title_font(34)
            p.setFont(f)
            p.setPen(QColor(255, 255, 255, 220))
            p.drawText(self.rect().adjusted(40, 0, -40, -70), Qt.AlignBottom | Qt.AlignLeft, it.title or "")
            f2 = QFont()
            f2.setPixelSize(18)
            p.setFont(f2)
            p.setPen(QColor(255, 255, 255, 170))
            p.drawText(self.rect().adjusted(40, 0, -40, -40), Qt.AlignBottom | Qt.AlignLeft, it.get("artist") or "")
        if clock() - self._msg_t < 2.5:
            f3 = QFont()
            f3.setPixelSize(16)
            p.setFont(f3)
            p.setPen(QColor(255, 255, 255, 200))
            p.drawText(self.rect().adjusted(0, 30, -40, 0), Qt.AlignTop | Qt.AlignRight,
                       VizStyles.name(st) + "   ·   ↑ ↓ " + t("change", "đổi kiểu") + "   ·   Esc")
        p.end()


def _unused():
    return QKeySequence
