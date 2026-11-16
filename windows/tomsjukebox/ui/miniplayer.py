"""Trình Phát Mini: a small pill that floats above other windows (the Windows stand-in for the phone's Now Bar and widgets).
Drag it anywhere; it remembers where it was. Double-click the cover to go back to the big window."""
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QWidget

from ..art.prefs import Prefs
from .artplayer import ArtPlayer


class MiniPlayer(QWidget):
    def __init__(self, win):
        flags = Qt.Tool | Qt.FramelessWindowHint
        if Prefs.miniOnTop.value or win.db.get("mini_on_top"):
            flags |= Qt.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.win = win
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Tom's Jukebox Mini")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.art = ArtPlayer(win, self, force_style="pill")
        self.art.setFixedHeight(120)
        self.art.open_now.connect(self._back)
        self.art.want_cast.connect(win.show_cast)
        self.art.want_record.connect(win.toggle_record)
        self.art.want_fav.connect(win.fav_current)
        self.art.want_menu.connect(self._menu)
        lay.addWidget(self.art)
        self.resize(440, 120)
        self._drag = None

    def place(self):
        g = Prefs.miniGeom.value
        scr = QGuiApplication.primaryScreen().availableGeometry()
        if g:
            try:
                x, y = [int(v) for v in g.split(",")[:2]]
                if scr.contains(QPoint(x + 20, y + 20)):
                    self.move(x, y)
                    return
            except ValueError:
                pass
        self.move(scr.right() - self.width() - 24, scr.bottom() - self.height() - 24)

    def _menu(self, pos):
        from PySide6.QtWidgets import QMenu
        from ..art.themes import t
        m = QMenu(self)
        m.addAction(t("Back To The Big Window", "Về Cửa Sổ Chính"), self._back)
        a = m.addAction(t("Stay On Top", "Luôn Nằm Trên"))
        a.setCheckable(True)
        a.setChecked(bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
        a.toggled.connect(self._top)
        m.addAction(t("Close Mini Player", "Đóng Trình Phát Mini"), self.hide)
        m.exec(pos)

    def _top(self, on):
        Prefs.miniOnTop.value = on
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        self.show()

    def _back(self):
        self.hide()
        self.win.showNormal()
        self.win.raise_()
        self.win.activateWindow()

    # drag anywhere on the pill (the player keeps clicks on its buttons)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            Prefs.miniGeom.value = f"{self.x()},{self.y()}"
        self._drag = None
