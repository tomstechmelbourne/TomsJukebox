"""Main window of Tom's Jukebox (Samsung Music style layout with Tom's Technology Solutions top bar)."""
import os
import subprocess
import sys
import time

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMainWindow, QMessageBox, QScrollArea, QStackedWidget, QStatusBar, QToolButton,
                               QVBoxLayout, QWidget)

from .. import app_info, backup, i18n, recorder, scanner, tools, volumes, winint
from ..i18n import tr
from . import theme
from .common import open_in_explorer, run_bg
from .icons import icon
from .pages import AlbumsPage, CategoryPage, FoldersPage, PlaylistsPage, SongsPage, StatsPage
from .pages2 import CDPage, NowPlayingPage, PodcastsPage, RadioPage, RecordingsPage, ToolsPage
from .player import Player, track_item
from .compactwin import CompactMixin

NAV = [
    ("grp_library", None, None),
    ("songs", "nav_songs", "songs"), ("albums", "nav_albums", "album"), ("artists", "nav_artists", "artist"),
    ("genres", "nav_genres", "genre"), ("folders", "nav_folders", "folder"), ("playlists", "nav_playlists", "playlist"),
    ("favs", "nav_favs", "star"),
    ("grp_listen", None, None),
    ("cd", "nav_cd", "cd"), ("radio", "nav_radio", "radio"), ("podcasts", "nav_podcasts", "podcast"),
    ("recordings", "nav_recordings", "recordings"),
    ("grp_more", None, None),
    ("tools", "nav_tools", "tools"), ("stats", "nav_stats", "stats"),
]


class MainWindow(CompactMixin, QMainWindow):
    def __init__(self, db, null_audio=False, fast_audio=False):
        super().__init__()
        self.db = db
        from ..art.prefs import Prefs
        if not db.get("android_prefs"):
            from .theme import LOOK_TO_ANDROID
            Prefs.bind(db)
            Prefs.theme.value = LOOK_TO_ANDROID.get(db.get("theme") or "tts", "toms")
            bc = db.get("bar_color")
            if bc:
                Prefs.barColour.value = bc
        Prefs.bind(db)
        self.setWindowTitle(app_info.APP_NAME)
        from PySide6.QtGui import QIcon
        self.setWindowIcon(QIcon(app_info.asset("app_icon_256.png")))
        self.player = Player(db, null_output=null_audio, fast=fast_audio)
        self.reel = tools.ReelLink(db.get("reel_db") or None)
        self.recordings = []
        self.pages = {}
        self.mini = None
        self.visual = None
        self._drive_sig = None
        self._build()
        self.player.changed.connect(self._on_changed)
        self.player.message.connect(self.toast)
        self.player.state.connect(self._on_state)
        self.apply_look()
        self.go("songs")
        self.refresh_all()
        self._timers()
        self._shortcuts()
        QTimer.singleShot(300, self._after_show)

    # ================================================================ layout
    def _statusbar(self):
        sb = QStatusBar()
        sb.setSizeGripEnabled(False)
        self.setStatusBar(sb)
        self.st_left = QLabel("")
        from PySide6.QtWidgets import QSizePolicy
        self.st_left.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sb.addWidget(self.st_left, 1)
        self.b_msgs = QToolButton()
        self.b_msgs.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.b_msgs.clicked.connect(self.show_messages)
        self.b_fb = QToolButton()
        self.b_fb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.b_fb.clicked.connect(self.feedback)
        self.l_ver = QLabel()
        for wdg in (self.b_msgs, QLabel("|"), self.b_fb, QLabel("|"), self.l_ver):
            sb.addPermanentWidget(wdg)

    # ================================================================ look & language
    def set_font_step(self, s):
        self.db.set("font_step", int(s))
        self.apply_look()
        self._dirty = set(self.pages)
        self._refresh_current()

    def set_lang(self, code):
        self.db.set("lang", code)
        i18n.set_lang(code)
        self.retranslate()
        self._dirty = set(self.pages)
        self._refresh_current()

    # ================================================================ navigation
    def _refresh_current(self):
        key = getattr(self, "cur_page", "songs")
        p = self.pages.get(key)
        if p is None or key not in self._dirty:
            return
        self._dirty.discard(key)
        if hasattr(p, "filter"):
            p.filter = self.search.text().strip()
        if hasattr(p, "refresh"):
            p.refresh()
        cur = self.player.current
        if hasattr(p, "on_playing"):
            p.on_playing(cur.get("id") if cur and cur.get("kind") == "track" else None)

    def refresh_all(self):
        self._dirty = set(self.pages)
        self._refresh_current()
        self.update_status()

    def _search_later(self):
        self._search_timer.start(250)

    # ================================================================ status
    def update_status(self):
        s = self.db.one("SELECT COUNT(*) n, COUNT(DISTINCT album) a FROM tracks WHERE missing=0 AND kind='music'")
        drives = sum(1 for f in self.db.q("SELECT DISTINCT vol_serial FROM folders") if f["vol_serial"] and volumes.online(f["vol_serial"]))
        self.st_left.setText(tr("status_counts", s=s["n"] or 0, a=s["a"] or 0, d=drives))
        n = self.db.unread_count()
        self.b_msgs.setText(tr("messages") + (f" ({n})" if n else ""))

    def toast(self, text):
        self.statusBar().showMessage(text, 6000)

    # ================================================================ library actions (ctx API)
    def play_rows(self, rows, start=0, shuffle=None):
        items = [track_item(r) for r in rows if not r["missing"]]
        if not items:
            return
        start = min(max(0, start), len(items) - 1)
        self.player.play_list(items, start, shuffle=shuffle)

    def add_rows(self, rows, nxt=False):
        items = [track_item(r) for r in rows]
        (self.player.add_next if nxt else self.player.add_queue)(items)
        self.toast(f"{tr('play_next') if nxt else tr('add_queue')}: {len(items)}")

    def add_to_playlist(self, rows, pid):
        if pid is None:
            name, ok = QInputDialog.getText(self, tr("new_playlist"), tr("pl_name"))
            if not ok or not name.strip():
                return
            pid = self.db.x("INSERT INTO playlists(name, created) VALUES(?,?)", (name.strip(), time.time()))
        start = self.db.one("SELECT COALESCE(MAX(pos),-1)+1 p FROM playlist_items WHERE playlist_id=?", (pid,))["p"]
        self.db.many("INSERT INTO playlist_items(playlist_id,pos,track_id) VALUES(?,?,?)",
                     [(pid, start + i, r["id"]) for i, r in enumerate(rows)])
        self.db.push_undo(tr("add_playlist"), [("DELETE FROM playlist_items WHERE playlist_id=? AND pos>=?", (pid, start))])
        self._dirty.add("playlists")
        name = self.db.one("SELECT name FROM playlists WHERE id=?", (pid,))["name"]
        self.toast(f"{tr('add_playlist')}: {name} (+{len(rows)})")

    def remove_from_playlist(self, pid, rows):
        ids = [r["id"] for r in rows]
        items = self.db.q("SELECT * FROM playlist_items WHERE playlist_id=?", (pid,))
        self.db.push_undo(tr("remove_from_pl"), [("DELETE FROM playlist_items WHERE playlist_id=?", (pid,))] +
                          [("INSERT INTO playlist_items(playlist_id,pos,track_id) VALUES(?,?,?)", (i["playlist_id"], i["pos"], i["track_id"])) for i in items])
        self.db.x(f"DELETE FROM playlist_items WHERE playlist_id=? AND track_id IN ({','.join('?' * len(ids))})", [pid] + ids)
        self.pages["playlists"].load()

    def toggle_fav(self, rows):
        new = 0 if all(r["fav"] for r in rows) else 1
        self.db.push_undo(tr("fav_toggle"), [("UPDATE tracks SET fav=? WHERE id=?", (r["fav"], r["id"])) for r in rows])
        self.db.many("UPDATE tracks SET fav=? WHERE id=?", [(new, r["id"]) for r in rows])
        self._dirty |= {"songs", "favs", "albums", "artists", "genres", "folders", "playlists"}
        self._dirty.add(self.cur_page)
        self._refresh_current()

    def edit_info(self, rows, online=False):
        from .dialogs import TagEditor
        if TagEditor(self, rows, online_first=online).exec():
            self.refresh_all()

    def show_in_folder(self, row):
        p = scanner.track_path(row)
        if p:
            open_in_explorer(p)
        else:
            self.toast(tr("offline_track"))

    def cast_rows(self, rows):
        self.play_rows(rows, 0)
        self.show_cast()

    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, tr("add_folder"))
        if not d:
            return
        fid = scanner.add_folder(self.db, d)
        self.rescan([fid])

    def rescan(self, folder_ids=None):
        if getattr(self, "_scanning", False):
            return
        self._scanning = True
        ids = folder_ids if isinstance(folder_ids, list) else None

        def prog(a):
            n, t, f = a
            self.statusBar().showMessage(tr("scanning", n=n, t=t, f=f))

        def done(res):
            self._scanning = False
            a, u, r, _off = res
            self.statusBar().showMessage(tr("scan_done", a=a, u=u, r=r), 8000)
            self.refresh_all()

        def failed(e):
            self._scanning = False
            self.toast(e)
        run_bg(scanner.scan, self.db, with_progress=True, folder_ids=ids, done=done, failed=failed, progress=prog)

    # ================================================================ links
    def find_toms_disc(self):
        p = self.db.get("toms_disc_path")
        if p and os.path.exists(p):
            return p
        cands = []
        for base in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("PROGRAMFILES", ""), str(app_info.documents_dir()),
                     os.path.join(os.path.expanduser("~"), "Downloads"), os.path.join(os.path.expanduser("~"), "Desktop")):
            if base:
                cands += [os.path.join(base, "Tom's Disc", "TomsDisc.exe"), os.path.join(base, "TomsDisc", "TomsDisc.exe"),
                          os.path.join(base, "TomsDisc", "dist", "TomsDisc", "TomsDisc.exe")]
        for c in cands:
            if os.path.exists(c):
                return c
        dl = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.isdir(dl):
            for root, _d, files in os.walk(dl):
                if root.count(os.sep) - dl.count(os.sep) > 4:
                    continue
                if "TomsDisc.exe" in files:
                    return os.path.join(root, "TomsDisc.exe")
        return None

    # ================================================================ recording
    def start_recording(self, name, url, fmt=None, seconds=None):
        out_dir = self.db.get("rec_dir") or str(app_info.default_recordings_dir())
        rec = recorder.Recording(name, url, out_dir, fmt or self.db.get("rec_fmt"), seconds,
                                 bool(self.db.get("rec_split")), on_file=self._rec_file)
        rec.start()
        self.recordings.append(rec)
        winint.prevent_sleep(True)
        self.toast(tr("r_rec_now", s=name, t="0:00", f=recorder.FORMATS[rec.fmt][1 if i18n.lang() == "vi" else 0]))
        self.pages["recordings"].refresh()

    def _rec_file(self, path):
        # runs in the recorder thread: only touch the database here
        try:
            scanner.add_single_file(self.db, path, kind="radio")
        except Exception as e:
            app_info.log.info("add recording to library failed: %s", e)
        self._rec_saved = path

    def stop_recordings(self):
        for r in self.recordings:
            r.stop()

    def _check_recordings(self):
        alive = [r for r in self.recordings if r.is_alive()]
        if len(alive) != len(self.recordings):
            self.recordings = alive
            self._dirty.add("recordings")
            if self.cur_page == "recordings":
                self._refresh_current()
            saved = getattr(self, "_rec_saved", None)
            if saved:
                self.db.add_message(f"Recording saved: {saved}", f"Đã lưu bản thu: {saved}")
                self.toast(tr("r_rec_saved", p=saved))
                self._rec_saved = None
                self.update_status()
        if not alive:
            winint.prevent_sleep(False)
        for s in recorder.due_schedules(self.db):
            st = self.db.one("SELECT * FROM stations WHERE id=?", (s["station_id"],))
            from datetime import datetime
            self.db.x("UPDATE schedules SET last_run=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d %H:%M"), s["id"]))
            if not st:
                continue
            url = st["url"]
            if not url:
                from .. import radio
                try:
                    url = radio.resolve_station(self.db, st)
                except Exception:
                    url = None
            if url:
                self.start_recording(st["name"], url, s["fmt"], s["minutes"] * 60)
            if s["once_date"]:
                self.db.x("UPDATE schedules SET enabled=0 WHERE id=?", (s["id"],))

    def notify_state_change(self, st):
        from .. import radio
        self.banner.show_msg(tr("r_state_changed", s=radio.STATE_NAMES[st], c=radio.STATE_CITY[st]),
                             [(tr("nav_radio"), lambda: self.go("radio"), True)], icon_name="location")

    # ================================================================ windows / dialogs
    def show_settings(self, tab=None):
        from .dialogs import SettingsDialog
        d = SettingsDialog(self)
        if tab:
            names = {"data": 6, "playback": 2, "recording": 4, "radio": 3, "library": 1}
            if tab in names and names[tab] < d.tabs.count():
                d.tabs.setCurrentIndex(names[tab])
        d.exec()
        self.refresh_all()

    def show_about(self):
        from .dialogs import AboutDialog
        AboutDialog(self).exec()

    def show_eq(self):
        from .dialogs import EQDialog
        EQDialog(self).exec()

    def show_cast(self):
        from .dialogs import CastDialog
        CastDialog(self).exec()

    def show_messages(self):
        from .dialogs import MessagesDialog
        MessagesDialog(self).exec()
        self.update_status()

    def feedback(self):
        from .dialogs import send_feedback
        send_feedback(self)

    def show_visual(self):
        from .dialogs2 import Visualizer
        self.visual = Visualizer(self)
        self.visual.showFullScreen()

    def restart(self):
        from PySide6.QtCore import QProcess
        args = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
        QProcess.startDetached(sys.executable, args)
        QApplication.instance().quit()

    # ================================================================ playback hooks
    def _on_changed(self, it):
        tid = it.get("id") if it and it.get("kind") == "track" else None
        for p in self.pages.values():
            if hasattr(p, "on_playing"):
                p.on_playing(tid)
        title = f"{it.title} — {app_info.APP_NAME}" if it else app_info.APP_NAME
        self.setWindowTitle(title)
        self._auto_eq(it)

    def _auto_eq(self, it):
        """Tự Chọn Kiểu Âm Thanh Theo Thể Loại (same rules as Android)."""
        if not it or not self.db.get("eq_auto_genre"):
            return
        from .. import engine
        k = it.get("kind")
        if k in ("radio", "episode"):
            key = "voice"
        else:
            genre = ""
            if k == "track":
                r = self.db.one("SELECT genre FROM tracks WHERE id=?", (it.get("id"),))
                genre = (r["genre"] if r else "") or ""
            key = engine.eq_for_genre(genre) or "flat"
        gains = engine.EQ_PRESETS.get(key)
        if gains:
            self.db.set("eq_preset", key)
            self.db.set("eq_gains", list(gains))
            self.player.engine.set_eq(True, list(gains))

    def _on_state(self, playing):
        if getattr(self, "taskbar", None):
            self.taskbar.set_playing(playing)

    # ================================================================ timers / startup
    def _timers(self):
        self.t_rec = QTimer(self)
        self.t_rec.timeout.connect(self._check_recordings)
        self.t_rec.start(5000)
        self.t_drives = QTimer(self)
        self.t_drives.timeout.connect(self._check_drives)
        self.t_drives.start(4000)
        self.t_loc = QTimer(self)
        self.t_loc.timeout.connect(lambda: self.pages["radio"].detect())
        self.t_loc.start(30 * 60 * 1000)
        self.t_pod = QTimer(self)
        self.t_pod.timeout.connect(lambda: self.pages["podcasts"].check_all())
        self.t_pod.start(3 * 3600 * 1000)

    def _check_drives(self):
        sig = tuple(sorted(volumes.drive_map(force=True).keys()))
        if self._drive_sig is not None and sig != self._drive_sig:
            self.refresh_all()
            added = set(sig) - set(self._drive_sig)
            if added and self.db.q(f"SELECT id FROM folders WHERE vol_serial IN ({','.join('?' * len(added))})", list(added)):
                self.rescan()
        self._drive_sig = sig

    def _after_show(self):
        if not self.db.get("first_run_done"):
            self.db.add_message("Welcome to Tom's Jukebox. Add your music folders in Folders (or Settings › Library).",
                                "Chào mừng đến với Tom's Jukebox. Thêm thư mục nhạc ở mục Thư Mục (hoặc Cài Đặt › Thư Viện).", "welcome")
            self.db.set("first_run_done", 1)
        if backup.auto_due(self.db) and self.db.one("SELECT COUNT(*) c FROM tracks")["c"]:
            if backup.auto_backup(self.db) is None:
                self.db.add_message("Your last backup is more than 7 days old.", "Lần sao lưu gần nhất đã hơn 7 ngày.", "backup_old")
        self.player.restore_queue()
        self.update_status()
        if "--selftest" not in sys.argv:
            self.pages["radio"].detect()
            QTimer.singleShot(8000, lambda: self.pages["podcasts"].check_all())
            if self.db.q("SELECT id FROM folders"):
                QTimer.singleShot(2500, self.rescan)
        try:
            hwnd = int(self.winId())
            self._media_keys = winint.register_media_keys(hwnd)
            if winint.IS_WIN:
                QTimer.singleShot(1500, lambda: setattr(self, "taskbar", winint.Taskbar(hwnd, winint.button_icons())))
        except Exception as e:
            app_info.log.info("windows extras failed: %s", e)

    def _shortcuts(self):
        def sc(seq, fn):
            s = QShortcut(QKeySequence(seq), self)
            s.activated.connect(fn)
        sc("Ctrl+Right", self.player.next)
        sc("Ctrl+Left", self.player.prev)
        sc("Ctrl+F", lambda: (self.go(self.lib_key), self.search.setFocus()))
        sc("Ctrl+Z", self.undo)
        sc(Qt.Key_MediaPlay, self.player.toggle)
        sc(Qt.Key_MediaTogglePlayPause, self.player.toggle)
        sc(Qt.Key_MediaNext, self.player.next)
        sc(Qt.Key_MediaPrevious, self.player.prev)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space and not isinstance(QApplication.focusWidget(), QLineEdit):
            self.player.toggle()
            return
        super().keyPressEvent(e)

    def undo(self):
        label = self.db.undo()
        if label:
            self.toast(tr("undone", x=label))
            self.refresh_all()

    def nativeEvent(self, etype, message):
        try:
            if winint.IS_WIN and etype == b"windows_generic_MSG":
                act = winint.parse_native(message)
                if act == "playpause":
                    self.player.toggle()
                elif act == "next":
                    self.player.next()
                elif act == "prev":
                    self.player.prev()
                elif act == "stop":
                    self.player.stop()
                if act:
                    return True, 0
        except Exception:
            pass
        return super().nativeEvent(etype, message)

    def closeEvent(self, e):
        if any(r.is_alive() for r in self.recordings):
            if QMessageBox.question(self, tr("r_stop_rec"), tr("r_stop_rec") + "?") != QMessageBox.Yes:
                e.ignore()
                return
            self.stop_recordings()
            for r in self.recordings:
                r.join(timeout=5)
        self._save_geom()
        winint.unregister_media_keys(int(self.winId()))
        if self.mini:
            self.mini.close()
        self.player.close()
        super().closeEvent(e)


def _unused():
    return QAction, subprocess
