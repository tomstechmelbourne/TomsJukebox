"""Tom's Jukebox 0.9.6: the one small window (jetAudio / Winamp style) with the Tom's Dock player on top, the Winamp-style
menu bar, the tabs and the panels. Mixed into MainWindow so all the library / radio / podcast pages keep working."""
import os
import sys

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu,
                               QMenuBar, QSizeGrip, QSlider, QStackedWidget, QStatusBar, QToolButton, QVBoxLayout, QWidget)

from .. import app_info, i18n
from ..art.prefs import Prefs
from ..art.state import Core
from ..art.themes import Motifs, Themes, VizStyles, t
from ..i18n import tr
from . import theme
from .artplayer import ArtPlayer, ticker
from .icons import icon
from .shell import EdgeOverlay, ShellFrame, TabBar, TitleBar, logo_pixmap, shell_qss
from .widgets import Banner

TABS = [("now", ("Now Playing", "Đang Phát")), ("lib", ("Library", "Thư Viện")), ("radio", ("Radio", "Radio")),
        ("podcasts", ("Podcasts", "Podcast")), ("cd", ("Audio CD", "Đĩa CD")), ("recordings", ("Recordings", "Bản Thâu")),
        ("look", ("Looks", "Giao Diện"))]
LIB = ["songs", "albums", "artists", "genres", "folders", "playlists", "favs"]
LIB_NAMES = {"songs": "nav_songs", "albums": "nav_albums", "artists": "nav_artists", "genres": "nav_genres",
             "folders": "nav_folders", "playlists": "nav_playlists", "favs": "nav_favs"}


from PySide6.QtCore import QObject, Signal


class _Bus(QObject):
    msg = Signal(str)


class CompactMixin:
    def bus_toast(self, text):
        """Toast from a background thread."""
        self._bus.msg.emit(text)

    # ================================================================ layout
    def _build(self):
        self._bus = _Bus()
        self._bus.msg.connect(self.toast)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.shell = ShellFrame(self)
        self.setCentralWidget(self.shell)
        v = QVBoxLayout(self.shell)
        v.setContentsMargins(8, 4, 8, 4)
        v.setSpacing(4)
        self.titlebar = TitleBar(self)
        tb = self.titlebar
        self.logo, self.brand_box, self.slogan = tb.logo, tb.brand_box, tb.slogan
        tb.btns["mini"].clicked.connect(self.show_mini)
        tb.btns["pin"].clicked.connect(self.toggle_pin)
        tb.btns["min"].clicked.connect(self.showMinimized)
        tb.btns["max"].clicked.connect(self.toggle_max)
        tb.btns["close"].clicked.connect(self.close)
        v.addWidget(tb)
        self.menu = QMenuBar()
        self.menu.setObjectName("Winamp")
        self.menu.setNativeMenuBar(False)
        v.addWidget(self.menu)
        self.pill = ArtPlayer(self)
        self.pill.open_now.connect(lambda: self.go("now"))
        self.pill.want_cast.connect(self.show_cast)
        self.pill.want_menu.connect(self._player_menu)
        self.pill.want_record.connect(self.toggle_record)
        self.pill.want_fav.connect(self.fav_current)
        v.addWidget(self.pill)
        v.addWidget(self._btnrow())
        self.tabbar = TabBar()
        self.tabbar.clicked.connect(self._tab_clicked)
        v.addWidget(self.tabbar)
        self.panel = QFrame()
        self.panel.setObjectName("Panel")
        pv = QVBoxLayout(self.panel)
        pv.setContentsMargins(6, 6, 6, 6)
        pv.setSpacing(6)
        self.banner = Banner()
        pv.addWidget(self.banner)
        pv.addWidget(self._libbar())
        self.stack = QStackedWidget()
        self.stack.setObjectName("PageArea")
        pv.addWidget(self.stack, 1)
        v.addWidget(self.panel, 1)
        self._statusbar()
        self.statusBar().setObjectName("ShellStatus")
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        self.statusBar().addPermanentWidget(grip)
        self.overlay = EdgeOverlay(self.shell)
        self.overlay.raise_()
        # compatibility with the old big window
        self.nav_btns, self.nav_groups, self.top_btns = {}, [], {}
        self.sidenav = QWidget()
        self._make_pages()
        self._build_menus()
        Prefs.listen(self._pref_changed)
        if Prefs.winOnTop.value:
            self.toggle_pin(True)
        self._tray()
        self.resize(600, 860)
        self.setMinimumSize(500, 420)
        self._restore_geom()

    def _make_pages(self):
        from .pages import AlbumsPage, CategoryPage, FoldersPage, PlaylistsPage, SongsPage, StatsPage
        from .pages2 import CDPage, NowPlayingPage, PodcastsPage, RadioPage, RecordingsPage, ToolsPage
        from .lookpage import LookPage
        P = self.pages
        P["songs"] = SongsPage(self)
        P["favs"] = SongsPage(self, favs=True)
        P["albums"] = AlbumsPage(self)
        P["artists"] = CategoryPage(self, "artist")
        P["genres"] = CategoryPage(self, "genre")
        P["folders"] = FoldersPage(self)
        P["playlists"] = PlaylistsPage(self)
        P["cd"] = CDPage(self)
        P["radio"] = RadioPage(self)
        P["podcasts"] = PodcastsPage(self)
        P["recordings"] = RecordingsPage(self)
        P["tools"] = ToolsPage(self)
        P["stats"] = StatsPage(self)
        P["now"] = NowPlayingPage(self)
        P["look"] = LookPage(self)
        for k, p in P.items():
            if hasattr(p, "lay"):
                p.lay.setContentsMargins(10, 8, 10, 6)
            self.stack.addWidget(p)
        self._dirty = set(P)
        self.lib_key = "songs"

    def _btnrow(self):
        w = QFrame()
        w.setObjectName("BtnRow")
        h = QHBoxLayout(w)
        h.setContentsMargins(6, 0, 6, 0)
        h.setSpacing(2)
        self.rb = {}

        def b(key, ic, tip, cb, checkable=False, text=None):
            x = QToolButton()
            if text:
                x.setText(text)
                x.setObjectName("Toggle")
            else:
                x.setProperty("iconName", ic)
                x.setIconSize(QSize(20, 20))
            x.setToolTip(tip)
            x.setCheckable(checkable)
            x.setCursor(Qt.PointingHandCursor)
            x.clicked.connect(cb)
            self.rb[key] = x
            return x
        for key, ic, tip, cb in (("shuffle", "shuffle", "shuffle", lambda: self.player.set_shuffle(not self.player.shuffle)),
                                 ("repeat", "repeat", "repeat_off", self._repeat),
                                 ("stop", "stop", "stop", self.player.stop),
                                 ("cast", "cast", "cast", self.show_cast),
                                 ("visual", "fullscreen", "visual", self.show_visual),
                                 ("sleep", "timer", "sleep", self.show_sleep)):
            h.addWidget(b(key, ic, tr(tip) if tip in i18n.T else tip, cb))
        h.addSpacing(4)
        h.addWidget(b("mute", "volume", tr("mute"), self._mute))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setValue(int(self.db.get("volume") or 80))
        self.vol_slider.valueChanged.connect(self._volume)
        h.addWidget(self.vol_slider)
        self.vol_label = QLabel("")
        h.addWidget(self.vol_label)
        h.addStretch()
        h.addWidget(b("eq", None, tr("eq"), self.show_eq, text="EQ"))
        h.addWidget(b("ly", None, tr("lyrics"), lambda: self._now_tab(0), text="LY"))
        h.addWidget(b("pl", None, tr("queue"), lambda: self._now_tab(1), text="PL"))
        more = b("more", "more", t("More", "Thêm"), lambda: self._more_menu())
        h.addWidget(more)
        return w

    def _libbar(self):
        w = QFrame()
        w.setObjectName("LibChips")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        from .lookpage import FlowLayout
        chips_host = QWidget()
        row = FlowLayout(chips_host, 4)
        self.lib_chips = {}
        for k in LIB:
            c = QToolButton()
            c.setCheckable(True)
            c.setAutoExclusive(True)
            c.setCursor(Qt.PointingHandCursor)
            c.clicked.connect(lambda _=False, kk=k: self.go(kk))
            self.lib_chips[k] = c
            row.addWidget(c)
        v.addWidget(chips_host)
        r2 = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(150)
        self.search.textChanged.connect(self._search_later)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        r2.addWidget(self.search, 1)
        self.b_addsongs = QToolButton()
        self.b_addsongs.setObjectName("AddBtn")
        self.b_addsongs.setCursor(Qt.PointingHandCursor)
        self.b_addsongs.clicked.connect(self.add_songs)
        self.b_addfolder = QToolButton()
        self.b_addfolder.setCursor(Qt.PointingHandCursor)
        self.b_addfolder.clicked.connect(self.add_folder)
        self.b_rescan = QToolButton()
        self.b_rescan.setCursor(Qt.PointingHandCursor)
        self.b_rescan.clicked.connect(lambda: self.rescan())
        for x in (self.b_addsongs, self.b_addfolder, self.b_rescan):
            x.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            r2.addWidget(x)
        v.addLayout(r2)
        self.libbar = w
        return w

    # ================================================================ menus (Winamp layout)
    def _act(self, menu, text, cb=None, key=None, checkable=False, checked=False):
        a = QAction(text, menu)
        if key:
            from .dialogs2 import saved
            akey = text.replace("&", "").replace("…", "").strip()
            a.setProperty("actKey", akey)
            a.setProperty("defKey", key)
            custom = getattr(self, "_custom_keys", None)
            if custom is None:
                custom = self._custom_keys = saved(self.db)
            if akey in custom:
                key = custom[akey]
        if key:
            a.setShortcut(QKeySequence(key))
            a.setShortcutContext(Qt.WindowShortcut)
            a.setShortcutVisibleInContextMenu(True)
            self.addAction(a)
        a.setCheckable(checkable)
        if checkable:
            a.setChecked(checked)
        if cb:
            a.triggered.connect(cb)
        menu.addAction(a)
        return a

    def _build_menus(self):
        m = self.menu
        m.clear()
        self._custom_keys = None
        for a in list(self.actions()):
            self.removeAction(a)
        A = self._act
        f = m.addMenu(t("&File", "&Tệp"))
        A(f, t("Play File…", "Phát File…"), self.play_file, "L")
        A(f, t("Play URL / Radio…", "Phát Địa Chỉ URL / Radio…"), self.play_url, "Ctrl+L")
        A(f, t("Play Folder…", "Phát Thư Mục…"), self.play_folder, "Shift+L")
        A(f, t("Play Audio CD", "Phát Đĩa CD"), lambda: self.go("cd"), "Ctrl+D")
        f.addSeparator()
        A(f, t("Add Songs To Library…", "Thêm Bài Hát Vào Thư Viện…"), self.add_songs)
        A(f, t("Add Folder To Library…", "Thêm Thư Mục Vào Thư Viện…"), self.add_folder)
        A(f, t("Rescan Library", "Quét Lại Thư Viện"), lambda: self.rescan(), "F5")
        f.addSeparator()
        A(f, t("Open Playlist (.m3u)…", "Mở Playlist (.m3u)…"), self.open_m3u, "Ctrl+O")
        A(f, t("Save Queue As Playlist…", "Lưu Hàng Đợi Thành Playlist…"), self.save_m3u, "Ctrl+S")
        f.addSeparator()
        A(f, t("Edit Song Info…", "Sửa Thông Tin Bài…"), self.edit_current, "Alt+3")
        A(f, t("Show In Folder", "Mở Thư Mục Chứa Bài"), self.show_current_folder)
        f.addSeparator()
        A(f, t("Back Up / Restore…", "Sao Lưu / Khôi Phục…"), lambda: self.show_settings(tab="data"))
        A(f, t("Exit", "Thoát"), self.close, "Alt+F4")

        p = m.addMenu(t("&Play", "&Phát"))
        A(p, t("Previous", "Bài Trước"), self.player.prev, "Z")
        A(p, t("Play", "Phát"), self._play_only, "X")
        A(p, t("Pause", "Tạm Dừng"), self.player.toggle, "C")
        A(p, t("Stop", "Dừng"), self.player.stop, "V")
        A(p, t("Next", "Bài Kế"), self.player.next, "B")
        p.addSeparator()
        adv = p.addMenu(t("Advanced Playback", "Phát Nâng Cao"))
        A(adv, t("Sleep Timer…", "Hẹn Giờ Tắt Nhạc…"), self.show_sleep, "Ctrl+T")
        A(adv, t("Play Settings (gapless, crossfade, even volume)…", "Cài Đặt Phát Nhạc (liền mạch, chuyển mượt, cân bằng âm lượng)…"),
          lambda: self.show_settings(tab="playback"))
        jt = p.addMenu(t("Jump To", "Nhảy Tới"))
        A(jt, t("Jump To Time…", "Nhảy Tới Thời Gian…"), self.jump_time, "Ctrl+J")
        A(jt, t("Jump To Song In Queue…", "Nhảy Tới Bài Trong Hàng Đợi…"), lambda: self._now_tab(1), "J")
        p.addSeparator()
        A(p, t("Back 5 Seconds", "Lùi 5 Giây"), lambda: self._nudge(-5), "Left")
        A(p, t("Forward 5 Seconds", "Tới 5 Giây"), lambda: self._nudge(5), "Right")
        p.addSeparator()
        self.a_repeat = A(p, t("Repeat", "Lặp Lại"), self._repeat, "R", checkable=True, checked=self.player.repeat != "off")
        self.a_shuffle = A(p, t("Shuffle", "Trộn Bài"), lambda: self.player.set_shuffle(not self.player.shuffle), "S", checkable=True, checked=self.player.shuffle)
        p.addSeparator()
        A(p, t("Volume Up", "Tăng Âm Lượng"), lambda: self.vol_slider.setValue(self.vol_slider.value() + 5), "Up")
        A(p, t("Volume Down", "Giảm Âm Lượng"), lambda: self.vol_slider.setValue(self.vol_slider.value() - 5), "Down")
        A(p, t("Record Radio / Podcast", "Thâu Radio / Podcast"), self.toggle_record, "Ctrl+R")

        o = m.addMenu(t("&Options", "Tù&y Chọn"))
        looks = o.addMenu(t("Look", "Giao Diện"))
        g = QActionGroup(looks)
        for key, en, vi in (("toms", "Tom's Technology Solutions", "Tom's Technology Solutions"), ("frosted", "Frosted Glass", "Kính Mờ"),
                            ("soft", "Soft (One UI style)", "Mềm Mại (Kiểu One UI)"), ("dark", "Dark", "Tối")):
            a = A(looks, t(en, vi), lambda _=False, k=key: setattr(Prefs.theme, "value", k), checkable=True, checked=Prefs.theme.value == key)
            g.addAction(a)
        looks.addSeparator()
        A(looks, t("More Colour Themes…", "Thêm Màu Giao Diện…"), lambda: self.show_picker("theme"))
        A(o, t("Theme Packs (70)…", "Bộ Chủ Đề (70)…"), lambda: self.show_picker("pack"))
        A(o, t("Skin…", "Skin…"), lambda: self.show_picker("skin"))
        A(o, t("Play Buttons…", "Kiểu Nút Phát Nhạc…"), lambda: self.show_picker("btn"))
        A(o, t("Edge Lighting…", "Ánh Sáng Chạy Viền…"), lambda: self.show_picker("edge"))
        A(o, t("Music Visualisation…", "Hiệu Ứng Sóng Nhạc…"), lambda: self.show_picker("viz"))
        A(o, t("Time Bar Colour…", "Màu Thanh Thời Gian…"), lambda: self.show_picker("bar"))
        ps = o.addMenu(t("Player Style", "Kiểu Thanh Phát Nhạc"))
        g2 = QActionGroup(ps)
        for key, en, vi in (("card", "Default (Tom's Tech)", "Mặc Định (Tom's Tech)"), ("pill", "Pill", "Viên Thuốc")):
            g2.addAction(A(ps, t(en, vi), lambda _=False, k=key: setattr(Prefs.playerStyle, "value", k), checkable=True,
                           checked=Prefs.playerStyle.value == key))
        A(o, t("Equaliser…", "Chỉnh Âm…"), self.show_eq, "Alt+G")
        o.addSeparator()
        A(o, t("Always On Top", "Luôn Nằm Trên"), lambda on: self.toggle_pin(on), "Ctrl+A", checkable=True, checked=Prefs.winOnTop.value)
        sz = o.addMenu(t("Text Size", "Cỡ Chữ"))
        g3 = QActionGroup(sz)
        for i, s in enumerate(("A", "A+", "A++")):
            g3.addAction(A(sz, s, lambda _=False, k=i: self.set_font_step(k), checkable=True, checked=int(self.db.get("font_step") or 0) == i))
        lg = o.addMenu(t("Language", "Ngôn Ngữ"))
        g4 = QActionGroup(lg)
        g4.addAction(A(lg, "English", lambda: self.set_lang("en"), checkable=True, checked=i18n.lang() == "en"))
        g4.addAction(A(lg, "Tiếng Việt", lambda: self.set_lang("vi"), checkable=True, checked=i18n.lang() == "vi"))
        o.addSeparator()
        A(o, t("Settings…", "Cài Đặt…"), self.show_settings, "Ctrl+P")

        vw = m.addMenu(t("&View", "&Xem"))
        for key, en, vi, k in (("now", "Now Playing", "Đang Phát", "Alt+E"), ("lib", "Library", "Thư Viện", "Alt+L"),
                               ("radio", "Radio", "Radio", "Alt+R"), ("podcasts", "Podcasts", "Podcast", "Alt+O"),
                               ("cd", "Audio CD", "Đĩa CD", "Alt+C"), ("recordings", "Recordings", "Bản Thâu Âm", "Alt+B"),
                               ("look", "Looks", "Giao Diện", "Alt+K")):
            A(vw, t(en, vi), lambda _=False, kk=key: self._tab_clicked(kk), k)
        vw.addSeparator()
        A(vw, t("Library Tools (duplicates, broken files)", "Dọn Thư Viện (bài trùng, file lỗi)"), lambda: self.go("tools"))
        A(vw, t("Statistics", "Thống Kê"), lambda: self.go("stats"))
        vw.addSeparator()
        self.a_shade = A(vw, t("Player Only (hide the panel)", "Chỉ Thanh Phát (ẩn bảng dưới)"), self.toggle_panel, "Ctrl+W", checkable=True,
                         checked=False)
        A(vw, t("Mini Player", "Trình Phát Mini"), self.show_mini, "Ctrl+M")
        A(vw, t("Full Screen Visuals", "Hình Ảnh Theo Nhạc Toàn Màn Hình"), self.show_visual, "F11")

        h = m.addMenu(t("&Help", "Trợ &Giúp"))
        A(h, t("Keyboard Shortcuts", "Phím Tắt"), self.show_shortcuts, "F1")
        A(h, t("Messages", "Tin Nhắn"), self.show_messages)
        A(h, t("Feedback…", "Góp Ý…"), self.feedback)
        h.addSeparator()
        A(h, t("About Tom's Jukebox", "Giới Thiệu Tom's Jukebox"), self.show_about)

    # ================================================================ look & language
    def apply_look(self):
        old = dict(theme.CUR["c"])
        jt = Themes.now()
        key = theme.from_jtheme(jt)
        theme.set_current(key, False, self.db.get("font_step"))
        from .icons import recolour_all
        if self.pages:
            recolour_all(self, old, theme.CUR["c"])
        i18n.set_lang(self.db.get("lang"))
        app = QApplication.instance()
        app.setStyle("Fusion")
        app.setPalette(theme.palette())
        from ..art import fonts
        body = fonts.body_family()
        qss = theme.qss()
        if body:
            qss = qss.replace('font-family: "Segoe UI", "Noto Sans", Arial;', f'font-family: "{body}", "Segoe UI", Arial;', 1)
        app.setStyleSheet(qss + shell_qss())
        ink = "#FFFFFF" if not jt.light else theme.c("ink")
        self._ink = ink
        dpr = self.devicePixelRatioF()
        self.logo.setPixmap(logo_pixmap(app_info.asset("app_icon_256.png"), 32, dpr))
        self._logo_cache = None
        for key, ic in (("mini", "mini"), ("pin", "pin"), ("min", "minimize"), ("max", "maximize"), ("close", "close")):
            self.titlebar.btns[key].setIcon(icon(ic, ink, 16))
        for key, x in self.rb.items():
            n = x.property("iconName")
            if n:
                x.setIcon(icon(n, ink, 20))
        self._repeat_icon()
        for x, ic in ((self.b_addsongs, "add"), (self.b_addfolder, "folder"), (self.b_rescan, "refresh")):
            x.setIcon(icon(ic, theme.c("ink"), 16))
        self.b_msgs.setIcon(icon("bell", ink, 16))
        self.b_fb.setIcon(icon("chat", ink, 16))
        self.pill.retheme()
        self.shell.update()
        self._responsive()
        self.retranslate()

    def logo_pixmap(self, size):
        if getattr(self, "_logo_cache", None) is None or self._logo_cache[0] != size:
            from PySide6.QtGui import QPixmap
            pm = QPixmap(app_info.asset("app_icon_256.png")).scaled(size * 2, size * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._logo_cache = (size, pm)
        return self._logo_cache[1]

    def retranslate(self):
        self.tabbar.set_tabs([(k, t(*n)) for k, n in TABS])
        for k, c in self.lib_chips.items():
            c.setText(tr(LIB_NAMES[k]))
        self.search.setPlaceholderText(tr("search"))
        self.b_addsongs.setText(t("Add Songs", "Thêm Bài"))
        self.b_addfolder.setText(t("Add Folder", "Thêm Thư Mục"))
        self.b_rescan.setText(t("Rescan", "Quét Lại"))
        self.b_addsongs.setToolTip(t("Add songs to the library…", "Thêm bài hát vào thư viện…"))
        self.b_addfolder.setToolTip(t("Add a folder to the library…", "Thêm thư mục vào thư viện…"))
        tips = {"mini": "mini", "min": None, "max": None, "close": "close"}
        self.titlebar.btns["mini"].setToolTip(tr("mini"))
        self.titlebar.btns["pin"].setToolTip(t("Always On Top", "Luôn Nằm Trên"))
        self.titlebar.btns["min"].setToolTip(t("Minimise", "Thu Nhỏ"))
        self.titlebar.btns["max"].setToolTip(t("Maximise", "Phóng To"))
        self.titlebar.btns["close"].setToolTip(tr("close"))
        del tips
        self.b_fb.setText(tr("feedback"))
        self.l_ver.setText(f"{tr('version')} {app_info.VERSION}")
        self._build_menus()
        for p in self.pages.values():
            if hasattr(p, "retranslate"):
                p.retranslate()
        self.update_status()

    def _responsive(self):
        big = int(self.db.get("font_step") or 0) >= 2
        narrow = self.width() < 560
        self.slogan.setVisible(not big and not narrow)
        self.brand_box.setVisible(not (big and narrow))
        for k in ("cast", "visual", "sleep"):
            self.rb[k].setVisible(not narrow)
        self.vol_slider.setFixedWidth(70 if narrow else 100)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.shell.rect())
        if self.pages:
            self._responsive()

    def set_theme(self, key):
        from .theme import LOOK_TO_ANDROID
        Prefs.theme.value = LOOK_TO_ANDROID.get(key, key)

    def toggle_dark(self):
        if Prefs.theme.value == "dark":
            Prefs.theme.value = self.db.get("theme_before_dark") or "toms"
        else:
            self.db.set("theme_before_dark", Prefs.theme.value)
            Prefs.theme.value = "dark"

    def set_bar_color(self, val):
        Prefs.barColour.value = val

    def _pref_changed(self, name):
        if name in ("theme", "pack", "customAccent", "fontBody", "*"):
            QTimer.singleShot(0, self.apply_look)
        if name in ("playerStyle", "skin", "*"):
            self.pill.update_height()
        if name in ("lang",):
            pass
        self.pill.update()
        self.shell.update()
        if "look" in self.pages:
            self.pages["look"].refresh_rows()

    # ================================================================ navigation
    def _tab_clicked(self, key):
        if key == "lib":
            self.go(self.lib_key)
        else:
            self.go(key)
        if self.a_shade.isChecked():
            self.toggle_panel(False)

    def go(self, key):
        if key not in self.pages:
            return
        self.cur_page = key
        lib = key in LIB
        if lib:
            self.lib_key = key
            self.lib_chips[key].setChecked(True)
            self.tabbar.set_current("lib")
        elif key in dict(TABS):
            self.tabbar.set_current(key)
        else:
            self.tabbar.set_current(None)
        self.libbar.setVisible(lib)
        self.stack.setCurrentWidget(self.pages[key])
        self._refresh_current()

    def _do_search(self):
        text = self.search.text().strip()
        if getattr(self, "cur_page", "songs") not in ("songs", "albums", "artists", "genres", "favs"):
            self.go("songs")
        p = self.pages[self.cur_page]
        p.set_filter(text)
        for k in ("songs", "albums", "artists", "genres", "favs"):
            if k != self.cur_page:
                self._dirty.add(k)

    def _now_tab(self, i):
        self.go("now")
        self.pages["now"].show_tab(i)

    # ================================================================ window
    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.shell.update()

    def toggle_pin(self, on=None):
        if on is None or isinstance(on, bool) is False:
            on = self.titlebar.btns["pin"].isChecked()
        Prefs.winOnTop.value = bool(on)
        self.titlebar.btns["pin"].setChecked(bool(on))
        vis = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(on))
        if vis:
            self.show()

    def toggle_panel(self, on=None):
        if on is None or not isinstance(on, bool):
            on = not self.panel.isHidden()
        shade = bool(on)
        self.a_shade.setChecked(shade)
        if shade:
            self._full_h = self.height()
            self.panel.hide()
            self.tabbar.hide()
            self.setMinimumHeight(0)
            QTimer.singleShot(0, lambda: self.resize(self.width(), self.sizeHint().height()))
        else:
            self.panel.show()
            self.tabbar.show()
            self.setMinimumHeight(420)
            self.resize(self.width(), max(600, getattr(self, "_full_h", 860)))

    def _restore_geom(self):
        g = Prefs.winGeom.value
        if g:
            try:
                x, y, w, h = [int(v) for v in g.split(",")]
                scr = QApplication.primaryScreen().availableGeometry()
                if scr.intersects(self.geometry().adjusted(x - self.x(), y - self.y(), 0, 0)):
                    self.setGeometry(x, y, max(500, w), max(420, h))
            except Exception:
                pass

    def _save_geom(self):
        if not self.isMaximized():
            gg = self.geometry()
            Prefs.winGeom.value = f"{gg.x()},{gg.y()},{gg.width()},{gg.height()}"

    # ================================================================ buttons
    def _volume(self, v):
        self.db.set("volume", int(v))
        self.player.set_volume(int(v))
        self.vol_label.setText(f"{int(v)}%")

    def _mute(self):
        e = self.player.engine
        e.muted = not e.muted
        self.rb["mute"].setIcon(icon("mute" if e.muted else "volume", getattr(self, "_ink", "#FFFFFF"), 20))

    def _repeat(self):
        self.player.cycle_repeat()
        self._repeat_icon()

    def _repeat_icon(self):
        r = self.player.repeat
        ink = getattr(self, "_ink", "#FFFFFF")
        self.rb["repeat"].setIcon(icon("repeat1" if r == "one" else "repeat", theme.c("accent") if r != "off" else ink, 20))
        self.rb["repeat"].setToolTip({"off": tr("repeat_off"), "all": tr("repeat_all"), "one": tr("repeat_one")}[r])
        self.rb["shuffle"].setIcon(icon("shuffle", theme.c("accent") if self.player.shuffle else ink, 20))
        if hasattr(self, "a_repeat"):
            self.a_repeat.setChecked(r != "off")
            self.a_shuffle.setChecked(self.player.shuffle)

    def _play_only(self):
        if not self.player.is_playing():
            self.player.toggle()

    def _nudge(self, s):
        if self.player.current is not None:
            self.player.seek(max(0, (self.player.position() or 0) + s))

    def _more_menu(self):
        m = QMenu(self)
        A = self._act
        A(m, t("Sleep Timer…", "Hẹn Giờ Tắt Nhạc…"), self.show_sleep)
        A(m, t("Play On TV / Speaker…", "Phát Ra TV / Loa…"), self.show_cast)
        A(m, t("Full Screen Visuals", "Hình Ảnh Theo Nhạc Toàn Màn Hình"), self.show_visual)
        A(m, tr("mini"), self.show_mini)
        m.addSeparator()
        A(m, t("Theme Packs…", "Bộ Chủ Đề…"), lambda: self.show_picker("pack"))
        A(m, t("Looks…", "Giao Diện…"), lambda: self.go("look"))
        A(m, tr("settings") + "…", self.show_settings)
        A(m, tr("about") + "…", self.show_about)
        m.exec(self.rb["more"].mapToGlobal(self.rb["more"].rect().bottomLeft()))

    def _player_menu(self, pos):
        m = QMenu(self)
        A = self._act
        ps = m.addMenu(t("Player Style", "Kiểu Thanh Phát Nhạc"))
        for key, en, vi in (("card", "Default (Tom's Tech)", "Mặc Định (Tom's Tech)"), ("pill", "Pill", "Viên Thuốc")):
            A(ps, t(en, vi), lambda _=False, k=key: setattr(Prefs.playerStyle, "value", k), checkable=True, checked=Prefs.playerStyle.value == key)
        for cat, en, vi in (("pack", "Theme Packs…", "Bộ Chủ Đề…"), ("skin", "Skin…", "Skin…"), ("btn", "Play Buttons…", "Kiểu Nút Phát Nhạc…"),
                            ("btncol", "Button Colour…", "Màu Nút…"), ("edge", "Edge Lighting…", "Ánh Sáng Chạy Viền…"),
                            ("viz", "Music Visualisation…", "Hiệu Ứng Sóng Nhạc…"), ("bar", "Time Bar Colour…", "Màu Thanh Thời Gian…")):
            A(m, t(en, vi), lambda _=False, c=cat: self.show_picker(c))
        m.addSeparator()
        A(m, t("Edge Lighting On", "Bật Ánh Sáng Chạy Viền"), lambda on: setattr(Prefs.edgeOn, "value", on), checkable=True, checked=Prefs.edgeOn.value)
        A(m, t("Visualisation On", "Bật Hiệu Ứng Sóng Nhạc"), lambda on: setattr(Prefs.vizOn, "value", on), checkable=True, checked=Prefs.vizOn.value)
        m.exec(pos)

    def show_picker(self, cat):
        from .picker import StylePicker
        StylePicker(self, cat).exec()
        self.pill.update()

    def show_sleep(self):
        from .sleep import SleepDialog
        SleepDialog(self).exec()

    def show_shortcuts(self):
        from .dialogs2 import ShortcutsDialog
        ShortcutsDialog(self).exec()

    # ================================================================ library / files
    def add_songs(self):
        from .. import scanner
        files, _ = QFileDialog.getOpenFileNames(self, t("Add Songs", "Thêm Bài Hát"), "",
                                                t("Music", "Nhạc") + " (*.mp3 *.m4a *.aac *.flac *.wav *.ogg *.opus *.wma *.alac *.aiff *.ape)")
        if not files:
            return
        n = 0
        for fpath in files:
            try:
                scanner.add_single_file(self.db, fpath)
                n += 1
            except Exception as e:
                app_info.log.info("add file failed: %s", e)
        self.toast(t(f"Added {n} songs", f"Đã thêm {n} bài"))
        self.refresh_all()

    def play_file(self):
        from .player import Item
        files, _ = QFileDialog.getOpenFileNames(self, t("Play File", "Phát File"), "",
                                                t("Music", "Nhạc") + " (*.mp3 *.m4a *.aac *.flac *.wav *.ogg *.opus *.wma *.aiff);;*.*")
        if files:
            self.player.play_list([Item(kind="file", path=fp, title=os.path.splitext(os.path.basename(fp))[0]) for fp in files], 0)

    def play_folder(self):
        from .player import Item
        d = QFileDialog.getExistingDirectory(self, t("Play Folder", "Phát Thư Mục"))
        if not d:
            return
        exts = (".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".opus", ".wma", ".aiff")
        files = []
        for root, _dirs, names in os.walk(d):
            files += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith(exts)]
        if files:
            self.player.play_list([Item(kind="file", path=fp, title=os.path.splitext(os.path.basename(fp))[0]) for fp in files], 0)

    def play_url(self):
        from .player import Item
        url, ok = QInputDialog.getText(self, t("Play URL / Radio", "Phát Địa Chỉ URL / Radio"), t("Address (http…):", "Địa chỉ (http…):"))
        if ok and url.strip():
            self.player.play_list([Item(kind="radio", url=url.strip(), title=url.strip(), name=url.strip())], 0)

    def open_m3u(self):
        from .player import Item
        f, _ = QFileDialog.getOpenFileName(self, t("Open Playlist", "Mở Playlist"), "", "Playlist (*.m3u *.m3u8)")
        if not f:
            return
        items = []
        base = os.path.dirname(f)
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith(("http://", "https://")):
                        items.append(Item(kind="radio", url=line, title=line, name=line))
                    else:
                        fp = line if os.path.isabs(line) else os.path.join(base, line)
                        if os.path.exists(fp):
                            items.append(Item(kind="file", path=fp, title=os.path.splitext(os.path.basename(fp))[0]))
        except OSError:
            return
        if items:
            self.player.play_list(items, 0)

    def save_m3u(self):
        f, _ = QFileDialog.getSaveFileName(self, t("Save Playlist", "Lưu Playlist"), "Tom's Jukebox.m3u", "Playlist (*.m3u)")
        if not f:
            return
        from .. import scanner
        lines = ["#EXTM3U"]
        for it in self.player.queue:
            p = None
            if it.get("kind") == "track":
                try:
                    row = self.db.one("SELECT * FROM tracks WHERE id=?", (it.get("id"),))
                    p = scanner.track_path(row) if row else None
                except Exception:
                    p = None
            else:
                p = it.get("path") or it.get("url")
            if p:
                lines.append(f"#EXTINF:{int(it.get('duration') or -1)},{it.get('artist') or ''} - {it.title}")
                lines.append(p)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        self.toast(t("Playlist saved", "Đã lưu playlist"))

    def jump_time(self):
        dur = self.player.duration() or 0
        if dur <= 0:
            return
        s, ok = QInputDialog.getText(self, t("Jump To Time", "Nhảy Tới Thời Gian"), t("Time (m:ss):", "Thời gian (phút:giây):"))
        if not ok:
            return
        try:
            parts = [int(x) for x in s.strip().split(":")]
            sec = 0
            for x in parts:
                sec = sec * 60 + x
            self.player.seek(min(dur - 1, max(0, sec)))
        except ValueError:
            pass

    def _current_row(self):
        it = self.player.current
        if not it or it.get("kind") != "track":
            return None
        return self.db.one("SELECT * FROM tracks WHERE id=?", (it.get("id"),))

    def edit_current(self):
        r = self._current_row()
        if r:
            self.edit_info([r])

    def show_current_folder(self):
        r = self._current_row()
        if r:
            self.show_in_folder(r)

    def fav_current(self):
        r = self._current_row()
        if r:
            self.toggle_fav([r])
            self.pill.update()

    # ================================================================ recording (radio + podcast)
    def toggle_record(self):
        it = self.player.current
        if not it:
            return
        k = it.get("kind")
        if k == "radio":
            alive = [r for r in self.recordings if r.is_alive()]
            if alive:
                self.stop_recordings()
                self.pill.recording = False
                Core.recording = False
            else:
                url = it.get("url") or it.get("stream")
                if not url:
                    try:
                        from .. import radio
                        url = radio.resolve_station(self.db, it)
                    except Exception:
                        url = None
                if url:
                    self.start_recording(it.get("name") or it.title, url)
                    self.pill.recording = True
                    Core.recording = True
        elif k == "episode":
            from .podtools import pod_record_toggle
            on = pod_record_toggle(self)
            self.pill.recording = on
            Core.recording = on
        self.pill.update()

    # ================================================================ mini player / tray
    def _tray(self):
        """Icon in the corner of the taskbar (the Windows stand-in for the phone's notification controls)."""
        from PySide6.QtWidgets import QSystemTrayIcon
        self.tray = None
        if not Prefs.trayIcon.value or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        from PySide6.QtGui import QIcon
        tr_ = QSystemTrayIcon(QIcon(app_info.asset("app_icon_256.png")), self)
        m = QMenu()
        m.addAction(t("Play / Pause", "Phát / Tạm Dừng"), self.player.toggle)
        m.addAction(t("Next", "Bài Kế"), self.player.next)
        m.addAction(t("Previous", "Bài Trước"), self.player.prev)
        m.addSeparator()
        m.addAction(tr("mini"), self.show_mini)
        m.addAction(t("Open Tom's Jukebox", "Mở Tom's Jukebox"), lambda: (self.showNormal(), self.raise_(), self.activateWindow()))
        m.addSeparator()
        m.addAction(t("Exit", "Thoát"), self.close)
        tr_.setContextMenu(m)
        self._tray_menu = m
        tr_.activated.connect(lambda reason: reason == QSystemTrayIcon.Trigger and (self.showNormal(), self.raise_(), self.activateWindow()))
        tr_.setToolTip(app_info.APP_NAME)
        self.player.changed.connect(lambda it: tr_.setToolTip((it.title + " — " if it else "") + app_info.APP_NAME))
        tr_.show()
        self.tray = tr_

    def show_mini(self):
        from .miniplayer import MiniPlayer
        if self.mini is None:
            self.mini = MiniPlayer(self)
        self.mini.place()
        self.mini.show()
        self.showMinimized()

    def changeEvent(self, e):
        super().changeEvent(e)
        try:
            ticker().slow(self.isMinimized() and not (self.mini and self.mini.isVisible()))
        except Exception:
            pass
