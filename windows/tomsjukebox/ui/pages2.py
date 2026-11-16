"""Pages: Audio CD, Radio, Podcasts, Radio Recordings, Library Tools, Now Playing."""
import json
import os
import subprocess
import time
from datetime import datetime

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QBrush
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QHeaderView, QInputDialog,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar,
                               QPushButton, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
                               QFileDialog, QCheckBox, QScrollArea, QApplication, QToolButton)

from .. import app_info, cdaudio, online, radio, recorder, scanner, tools
from ..i18n import lang, tr
from . import theme
from .common import open_in_explorer, run_bg
from .icons import icon
from .pages import Page
from .player import Item
from .widgets import Banner, Cover, SpinningDisc, dominant_color, fmt_time, h1, h2, hint


def tree(headers, widths=None):
    t = QTreeWidget()
    t.setHeaderLabels(headers)
    t.setRootIsDecorated(False)
    t.setAlternatingRowColors(True)
    t.setSelectionMode(QAbstractItemView.ExtendedSelection)
    t.setUniformRowHeights(True)
    t.setIconSize(QSize(18, 18))
    if widths:
        for i, w in enumerate(widths):
            t.setColumnWidth(i, w)
    t.header().setStretchLastSection(True)
    return t


# =========================================================================== Audio CD
class CDPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_cd", [("cd_play_all", "play", self.play_all, True), ("cd_rip", "disc", self.rip, False),
                               ("cd_eject", "eject", self.eject, False)])
        row = QHBoxLayout()
        self.l_drive = QLabel(tr("cd_drive"))
        self.drive = QComboBox()
        self.drive.setMinimumWidth(120)
        self.b_ref = QPushButton(icon("refresh", theme.c("ink"), 18), tr("cd_refresh"))
        self.b_ref.clicked.connect(self.refresh)
        row.addWidget(self.l_drive)
        row.addWidget(self.drive)
        row.addWidget(self.b_ref)
        row.addStretch()
        self.lay.addLayout(row)
        card = QFrame()
        card.setObjectName("Card")
        cl = QHBoxLayout(card)
        self.cover = Cover(130, 14)
        cl.addWidget(self.cover)
        info = QVBoxLayout()
        self.album = h1("")
        self.artist = h2("")
        self.status = hint("")
        info.addStretch()
        info.addWidget(self.album)
        info.addWidget(self.artist)
        info.addWidget(self.status)
        info.addStretch()
        cl.addLayout(info, 1)
        self.lay.addWidget(card)
        self.list = tree([tr("col_no"), tr("col_title"), tr("col_artist"), tr("col_len")], [50, 380, 260, 80])
        self.list.itemDoubleClicked.connect(lambda it, _c: self.play_from(self.list.indexOfTopLevelItem(it)))
        self.lay.addWidget(self.list, 1)
        self.toc = None
        self.meta = None
        self.drv = None

    def retranslate(self):
        super().retranslate()
        self.l_drive.setText(tr("cd_drive"))
        self.b_ref.setText(tr("cd_refresh"))
        self.list.setHeaderLabels([tr("col_no"), tr("col_title"), tr("col_artist"), tr("col_len")])

    def refresh(self):
        if not cdaudio.IS_WIN:
            self.status.setText(tr("cd_only_win"))
            return
        cur = self.drive.currentText()
        drives = cdaudio.cd_drives()
        self.drive.blockSignals(True)
        self.drive.clear()
        self.drive.addItems(drives)
        if cur in drives:
            self.drive.setCurrentText(cur)
        self.drive.blockSignals(False)
        if not drives:
            self.status.setText(tr("cd_none"))
            self.list.clear()
            return
        self.status.setText(tr("cd_reading"))
        letter = self.drive.currentText()
        run_bg(self._read, letter, done=self._read_done, failed=lambda e: self.status.setText(tr("cd_nodisc")))

    def _read(self, letter):
        d = cdaudio.CDDrive(letter)
        toc = d.toc()
        meta = None
        if self.db.get("musicbrainz"):
            meta = online.mb_disc(cdaudio.musicbrainz_disc_id(toc), cdaudio.toc_string(toc))
            if meta and meta.get("mbid"):
                art = online.cover_art(meta["mbid"], 250)
                if art:
                    from .. import tags
                    key = "cd_" + meta["mbid"][:12]
                    if tags.save_thumbs(key, art):
                        meta["art_key"] = key
        return d, toc, meta

    def _read_done(self, res):
        d, toc, meta = res
        if self.drv:
            self.drv.close()
        self.drv, self.toc, self.meta = d, toc, meta
        self.ctx.player.cd_drive = d
        self.list.clear()
        tr_meta = (meta or {}).get("tracks") or []
        for i, t in enumerate(toc["tracks"]):
            if not t["audio"]:
                continue
            title = tr_meta[i]["title"] if i < len(tr_meta) else tr("cd_track", n=t["number"])
            artist = tr_meta[i]["artist"] if i < len(tr_meta) else (meta or {}).get("artist", "")
            secs = (t["lba_end"] - t["lba_start"]) / 75
            it = QTreeWidgetItem([f"{t['number']:02d}", title, artist or "", fmt_time(secs)])
            it.setData(0, Qt.UserRole, i)
            self.list.addTopLevelItem(it)
        self.album.setText((meta or {}).get("album") or tr("nav_cd"))
        self.artist.setText((meta or {}).get("artist") or "")
        self.cover.set_key((meta or {}).get("art_key"), self.album.text())
        self.status.setText("" if meta else tr("cd_not_found"))

    def items(self):
        out = []
        for k in range(self.list.topLevelItemCount()):
            w = self.list.topLevelItem(k)
            t = self.toc["tracks"][w.data(0, Qt.UserRole)]
            out.append(Item(kind="cd", title=w.text(1), artist=w.text(2), album=self.album.text(),
                            duration=(t["lba_end"] - t["lba_start"]) / 75, lba_start=t["lba_start"],
                            lba_end=t["lba_end"], art_key=(self.meta or {}).get("art_key"), codec="CD"))
        return out

    def play_all(self):
        if self.toc:
            self.ctx.player.play_list(self.items(), 0)

    def play_from(self, i):
        if self.toc:
            self.ctx.player.play_list(self.items(), i)

    def eject(self):
        if self.drv:
            if self.ctx.player.current and self.ctx.player.current.get("kind") == "cd":
                self.ctx.player.stop()
            self.drv.eject()
            self.drv = None
            self.toc = None
            self.list.clear()
        elif cdaudio.IS_WIN and self.drive.currentText():
            cdaudio.CDDrive(self.drive.currentText()).eject()

    def rip(self):
        exe = self.ctx.find_toms_disc()
        if not exe:
            QMessageBox.information(self, tr("cd_rip"), tr("cd_disc_not_found"))
            return
        if self.ctx.player.current and self.ctx.player.current.get("kind") == "cd":
            self.ctx.player.stop()
        if self.drv:
            self.drv.close()
        subprocess.Popen([exe], cwd=os.path.dirname(exe))


# =========================================================================== Radio
class RadioPage(Page):
    TABS = ["r_favs", "r_nearby", "r_au", "r_vn", "r_vn_au", "r_search", "r_mine"]

    def __init__(self, ctx):
        super().__init__(ctx)
        radio.seed(self.db)
        self.header("nav_radio", [("r_add", "add", self.add_station, False), ("r_schedule", "clock", self.schedule, False)])
        loc = QFrame()
        loc.setObjectName("Card")
        ll = QHBoxLayout(loc)
        ll.addWidget(QLabel(pixmap=icon("location", theme.c("teal"), 24).pixmap(24, 24)))
        self.l_you = QLabel(tr("you_are_in"))
        self.l_you.setFont(self._bold())
        ll.addWidget(self.l_you)
        self.state = QComboBox()
        self.state.addItem("—", "")
        for s in radio.STATES:
            self.state.addItem(f"{s} · {radio.STATE_NAMES[s]}", s)
        self.state.activated.connect(self._state_chosen)
        ll.addWidget(self.state)
        self.l_how = QLabel("")
        self.l_how.setObjectName("Muted")
        ll.addWidget(self.l_how)
        ll.addStretch()
        self.b_detect = QPushButton(icon("location", theme.c("ink"), 18), tr("detect"))
        self.b_detect.clicked.connect(lambda: self.detect(manual=True))
        ll.addWidget(self.b_detect)
        self.lay.addWidget(loc)
        self.banner = Banner()
        self.lay.addWidget(self.banner)
        self.rec_strip = QFrame()
        self.rec_strip.setObjectName("Strip")
        rl = QHBoxLayout(self.rec_strip)
        self.rec_label = QLabel("")
        self.rec_stop = QPushButton(icon("stop", theme.c("ink"), 16), tr("r_stop_rec"))
        self.rec_stop.clicked.connect(lambda: self.ctx.stop_recordings())
        rl.addWidget(QLabel(pixmap=icon("record", "#E5484D", 18).pixmap(18, 18)))
        rl.addWidget(self.rec_label, 1)
        rl.addWidget(self.rec_stop)
        self.rec_strip.hide()
        self.lay.addWidget(self.rec_strip)
        self.tabs = QTabWidget()
        self.lists = {}
        for key in self.TABS:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(8, 8, 8, 8)
            if key == "r_search":
                sr = QHBoxLayout()
                self.q = QLineEdit()
                self.q.setPlaceholderText(tr("r_search_hint"))
                self.q.returnPressed.connect(self.do_search)
                b = QPushButton(icon("search", theme.c("ink"), 18), tr("r_search"))
                b.clicked.connect(self.do_search)
                self.b_search = b
                sr.addWidget(self.q, 1)
                sr.addWidget(b)
                v.addLayout(sr)
            if key == "r_nearby":
                self.near_note = hint(tr("r_local_note"))
                v.addWidget(self.near_note)
            t = tree([tr("r_name"), tr("r_where"), tr("r_quality")], [380, 200, 160])
            t.setSelectionMode(QAbstractItemView.SingleSelection)
            t.itemDoubleClicked.connect(lambda it, _c: self.play_item(it))
            t.setContextMenuPolicy(Qt.CustomContextMenu)
            t.customContextMenuRequested.connect(lambda pos, tt=t: self._menu(tt, pos))
            v.addWidget(t, 1)
            self.lists[key] = t
            self.tabs.addTab(w, tr(key))
        self.tabs.currentChanged.connect(lambda *_: self.load_tab())
        self.lay.addWidget(self.tabs, 1)
        act = QHBoxLayout()
        self.b_play = QPushButton(icon("play", theme.c("on_accent"), 18), tr("play"))
        self.b_play.setObjectName("Primary")
        self.b_play.clicked.connect(lambda: self.play_item(self.cur_list().currentItem()))
        self.b_rec = QPushButton(icon("record", "#E5484D", 18), tr("r_record"))
        self.b_rec.clicked.connect(self.record_selected)
        self.fmt = QComboBox()
        for k, v in recorder.FORMATS.items():
            self.fmt.addItem(v[1] if lang() == "vi" else v[0], k)
        self.fmt.setCurrentIndex(max(0, self.fmt.findData(self.db.get("rec_fmt"))))
        self.fmt.currentIndexChanged.connect(lambda *_: self.db.set("rec_fmt", self.fmt.currentData()))
        self.b_fav = QPushButton(icon("star_on", theme.c("ink"), 18), tr("r_fav_add"))
        self.b_fav.clicked.connect(self.toggle_fav_selected)
        act.addWidget(self.b_play)
        act.addWidget(self.b_rec)
        act.addWidget(self.fmt)
        act.addWidget(self.b_fav)
        act.addStretch()
        self.qnote = hint(tr("r_quality_note"))
        self.qnote.setWordWrap(True)
        self.lay.addLayout(act)
        self.lay.addWidget(self.qnote)
        self.remote = {}
        if not self.db.one("SELECT id FROM stations WHERE fav=1"):
            self.tabs.setCurrentIndex(self.TABS.index("r_au"))
        self._set_state_combo()
        self.rtimer = QTimer(self)
        self.rtimer.timeout.connect(self._rec_status)
        self.rtimer.start(1000)

    def _bold(self):
        f = self.font()
        f.setBold(True)
        return f

    def retranslate(self):
        super().retranslate()
        self.l_you.setText(tr("you_are_in"))
        self.b_detect.setText(tr("detect"))
        for i, k in enumerate(self.TABS):
            self.tabs.setTabText(i, tr(k))
        for t in self.lists.values():
            t.setHeaderLabels([tr("r_name"), tr("r_where"), tr("r_quality")])
        self.b_play.setText(tr("play"))
        self.b_rec.setText(tr("r_record"))
        self.b_fav.setText(tr("r_fav_add"))
        self.qnote.setText(tr("r_quality_note"))
        self.near_note.setText(tr("r_local_note"))
        self.q.setPlaceholderText(tr("r_search_hint"))
        self.b_search.setText(tr("r_search"))
        self.rec_stop.setText(tr("r_stop_rec"))
        for i in range(self.fmt.count()):
            v = recorder.FORMATS[self.fmt.itemData(i)]
            self.fmt.setItemText(i, v[1] if lang() == "vi" else v[0])
        self._set_state_combo()

    def _set_state_combo(self):
        s = self.db.get("radio_state") or ""
        i = self.state.findData(s)
        self.state.setCurrentIndex(max(0, i))
        self.l_how.setText(f"({tr('manual') if self.db.get('radio_state_manual') else tr('auto')})" if s else "")

    def cur_list(self):
        return self.lists[self.TABS[self.tabs.currentIndex()]]

    def refresh(self):
        self.load_tab()

    # ---- lists
    def _add_db_rows(self, t, rows):
        t.clear()
        for r in rows:
            where = r["state"] or ("Việt Nam" if r["grp"] == "vn" else ("Australia" if r["grp"].startswith("au") else ""))
            if r["city"]:
                where = f"{r['city']} · {r['state']}"
            it = QTreeWidgetItem([r["name"], where, radio.quality_text(r["codec"], r["bitrate"])])
            it.setIcon(0, icon("star_on" if r["fav"] else "radio", theme.c("teal"), 18))
            it.setData(0, Qt.UserRole, ("db", r["id"]))
            t.addTopLevelItem(it)
        if not rows:
            it = QTreeWidgetItem([tr("r_none_here"), "", ""])
            it.setDisabled(True)
            t.addTopLevelItem(it)

    def _add_remote(self, t, rows):
        t.clear()
        for k, r in enumerate(rows):
            it = QTreeWidgetItem([r["name"], r.get("state") or "", radio.quality_text(r["codec"], r["bitrate"])])
            it.setIcon(0, icon("radio", theme.c("muted"), 18))
            it.setData(0, Qt.UserRole, ("remote", r))
            t.addTopLevelItem(it)
        if not rows:
            it = QTreeWidgetItem([tr("r_none_here"), "", ""])
            it.setDisabled(True)
            t.addTopLevelItem(it)

    def load_tab(self):
        key = self.TABS[self.tabs.currentIndex()]
        t = self.lists[key]
        db = self.db
        if key == "r_favs":
            self._add_db_rows(t, db.q("SELECT * FROM stations WHERE fav=1 ORDER BY sort, name"))
        elif key == "r_au":
            self._add_db_rows(t, db.q("SELECT * FROM stations WHERE grp IN ('au','au_local') AND custom=0 ORDER BY grp, sort"))
        elif key == "r_vn":
            self._add_db_rows(t, db.q("SELECT * FROM stations WHERE grp='vn' AND custom=0 ORDER BY sort"))
        elif key == "r_mine":
            self._add_db_rows(t, db.q("SELECT * FROM stations WHERE custom=1 ORDER BY name"))
        elif key == "r_nearby":
            st = db.get("radio_state") or ""
            local = db.q("SELECT * FROM stations WHERE grp='au_local' AND state=?", (st,)) if st else []
            self._add_db_rows(t, local)
            if st:
                if st in self.remote:
                    self._append_remote(t, self.remote[st])
                else:
                    run_bg(radio.nearby, st, done=lambda rows, s=st: self._nearby_done(s, rows))
        elif key == "r_vn_au":
            if "vn_au" in self.remote:
                self._add_remote(t, self.remote["vn_au"])
            else:
                t.clear()
                t.addTopLevelItem(QTreeWidgetItem([tr("r_looking"), "", ""]))
                run_bg(radio.vietnamese_in_australia, done=self._vnau_done, failed=lambda e: self._offline(t))

    def _append_remote(self, t, rows):
        names = {t.topLevelItem(i).text(0).lower() for i in range(t.topLevelItemCount())}
        for r in rows:
            if r["name"].lower() in names:
                continue
            it = QTreeWidgetItem([r["name"], r.get("state") or "", radio.quality_text(r["codec"], r["bitrate"])])
            it.setIcon(0, icon("radio", theme.c("muted"), 18))
            it.setData(0, Qt.UserRole, ("remote", r))
            t.addTopLevelItem(it)

    def _nearby_done(self, st, rows):
        self.remote[st] = rows
        if self.TABS[self.tabs.currentIndex()] == "r_nearby" and (self.db.get("radio_state") or "") == st:
            self._append_remote(self.lists["r_nearby"], rows)

    def _vnau_done(self, rows):
        self.remote["vn_au"] = rows
        self._add_remote(self.lists["r_vn_au"], rows)

    def _offline(self, t):
        t.clear()
        t.addTopLevelItem(QTreeWidgetItem([tr("r_offline"), "", ""]))

    def do_search(self):
        text = self.q.text().strip()
        if not text:
            return
        t = self.lists["r_search"]
        t.clear()
        t.addTopLevelItem(QTreeWidgetItem([tr("r_looking"), "", ""]))
        run_bg(radio.search, text, done=lambda rows: self._add_remote(t, rows), failed=lambda e: self._offline(t))

    # ---- play / record
    def _station_from(self, it, then):
        """Calls then(name, url, db_id) once a URL is known (looks it up if needed)."""
        if it is None or it.isDisabled():
            return
        kind, val = it.data(0, Qt.UserRole)
        if kind == "remote":
            then(val["name"], val["url"], None, val)
            return
        row = self.db.one("SELECT * FROM stations WHERE id=?", (val,))
        if row["url"]:
            then(row["name"], row["url"], row["id"], dict(row))
            return
        self.ctx.toast(tr("r_looking"))

        def look():
            return radio.resolve_station(self.db, row)

        def done(url):
            if url:
                r2 = self.db.one("SELECT * FROM stations WHERE id=?", (row["id"],))
                then(row["name"], url, row["id"], dict(r2))
                self.load_tab()
            else:
                self.ctx.toast(tr("r_offline"))
        run_bg(look, done=done, failed=lambda e: self.ctx.toast(tr("r_offline")))

    def play_item(self, it):
        def go(name, url, sid, info):
            sub = info.get("city") or info.get("state") or ("Việt Nam" if info.get("grp") == "vn" else "")
            self.ctx.player.play_item(Item(kind="radio", url=url, title=name, artist=sub, station_id=sid,
                                           codec=info.get("codec"), duration=0))
        self._station_from(it, go)

    def record_selected(self):
        self._station_from(self.cur_list().currentItem(),
                           lambda name, url, sid, info: self.ctx.start_recording(name, url, self.fmt.currentData()))

    def toggle_fav_selected(self):
        it = self.cur_list().currentItem()
        if not it or it.isDisabled():
            return
        kind, val = it.data(0, Qt.UserRole)
        if kind == "db":
            self.db.x("UPDATE stations SET fav=1-fav WHERE id=?", (val,))
        else:
            ex = self.db.one("SELECT id FROM stations WHERE url=?", (val["url"],))
            if ex:
                self.db.x("UPDATE stations SET fav=1 WHERE id=?", (ex["id"],))
            else:
                self.db.x("INSERT INTO stations(name,grp,state,url,codec,bitrate,homepage,fav,custom) VALUES(?,?,?,?,?,?,?,1,1)",
                          (val["name"], "remote", val.get("state", ""), val["url"], val["codec"], val["bitrate"], val.get("homepage", "")))
        self.load_tab()

    def _menu(self, t, pos):
        it = t.itemAt(pos)
        if not it or it.isDisabled():
            return
        t.setCurrentItem(it)
        kind, val = it.data(0, Qt.UserRole)
        m = QMenu(self)
        m.addAction(icon("play", theme.c("ink"), 18), tr("play"), lambda: self.play_item(it))
        m.addAction(icon("record", "#E5484D", 18), tr("r_record"), self.record_selected)
        m.addAction(icon("clock", theme.c("ink"), 18), tr("r_schedule"), lambda: self.schedule(it))
        fav = kind == "db" and self.db.one("SELECT fav FROM stations WHERE id=?", (val,))["fav"]
        m.addAction(icon("star_on", theme.c("ink"), 18), tr("r_fav_remove") if fav else tr("r_fav_add"), self.toggle_fav_selected)
        home = val.get("homepage") if kind == "remote" else self.db.one("SELECT homepage FROM stations WHERE id=?", (val,))["homepage"]
        if home:
            import webbrowser
            m.addAction(icon("web", theme.c("ink"), 18), tr("r_homepage"), lambda: webbrowser.open(home))
        if kind == "db" and self.db.one("SELECT custom FROM stations WHERE id=?", (val,))["custom"]:
            m.addSeparator()
            m.addAction(tr("r_delete"), lambda: (self.db.x("DELETE FROM stations WHERE id=?", (val,)), self.load_tab()))
        m.exec(t.viewport().mapToGlobal(pos))

    def add_station(self):
        name, ok = QInputDialog.getText(self, tr("r_add"), tr("r_name"))
        if not ok or not name.strip():
            return
        url, ok = QInputDialog.getText(self, tr("r_add"), tr("r_url"))
        if not ok or not url.strip().startswith("http"):
            return
        self.db.x("INSERT INTO stations(name,grp,url,custom,fav) VALUES(?,?,?,1,0)", (name.strip(), "mine", url.strip()))
        self.tabs.setCurrentIndex(self.TABS.index("r_mine"))
        self.load_tab()

    def schedule(self, it=None):
        from .dialogs import ScheduleDialog
        sid = None
        it = it if it is not None and not isinstance(it, bool) else self.cur_list().currentItem()
        if it and not it.isDisabled():
            kind, val = it.data(0, Qt.UserRole)
            if kind == "db":
                sid = val
            else:
                ex = self.db.one("SELECT id FROM stations WHERE url=?", (val["url"],))
                sid = ex["id"] if ex else self.db.x(
                    "INSERT INTO stations(name,grp,state,url,codec,bitrate,custom) VALUES(?,?,?,?,?,?,1)",
                    (val["name"], "remote", val.get("state", ""), val["url"], val["codec"], val["bitrate"]))
        ScheduleDialog(self, self.db, None, sid).exec()
        self.ctx.pages["recordings"].refresh()

    # ---- location
    def _state_chosen(self, _i):
        s = self.state.currentData() or ""
        self.db.set("radio_state", s)
        self.db.set("radio_state_manual", 1 if s else 0)
        self._set_state_combo()
        if self.TABS[self.tabs.currentIndex()] == "r_nearby":
            self.load_tab()

    def detect(self, manual=False):
        if manual:
            self.db.set("radio_state_manual", 0)
        if self.db.get("radio_state_manual") and not manual:
            return
        self.l_how.setText(tr("working"))
        run_bg(radio.detect_state, bool(self.db.get("location_windows")), bool(self.db.get("location_ip")),
               done=lambda r: self._detected(r, manual), failed=lambda e: self._detected((None, ""), manual))

    def _detected(self, res, manual):
        st, _how = res
        old = self.db.get("radio_state") or ""
        if not st:
            self._set_state_combo()
            if manual:
                self.banner.show_msg(tr("r_detect_fail"), icon_name="location")
            return
        if not old or manual:
            self.db.set("radio_state", st)
            self._set_state_combo()
            self.load_tab()
            return
        if st != old:
            def switch():
                self.db.set("radio_state", st)
                self._set_state_combo()
                self.tabs.setCurrentIndex(self.TABS.index("r_nearby"))
                self.load_tab()
            self.banner.show_msg(tr("r_state_changed", s=radio.STATE_NAMES[st], c=radio.STATE_CITY[st]),
                                 [(tr("r_switch"), switch, True), (tr("r_keep"), lambda: self.db.set("radio_state_manual", 1), False)],
                                 icon_name="location")
            self.ctx.notify_state_change(st)
        self._set_state_combo()

    def _rec_status(self):
        recs = [r for r in self.ctx.recordings if r.is_alive()]
        self.rec_strip.setVisible(bool(recs))
        if recs:
            r = recs[0]
            fmt = recorder.FORMATS[r.fmt][1 if lang() == "vi" else 0]
            self.rec_label.setText(tr("r_rec_now", s=r.station, t=fmt_time(r.elapsed), f=fmt) +
                                   (f"  ·  {r.title}" if r.title else "") + (f"  (+{len(recs) - 1})" if len(recs) > 1 else ""))


# =========================================================================== Podcasts
class PodcastsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_podcasts", [("p_refresh", "refresh", self.check_all, False)])
        sr = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText(tr("p_search"))
        self.q.returnPressed.connect(self.search)
        self.b_s = QPushButton(icon("search", theme.c("ink"), 18), tr("p_search"))
        self.b_s.clicked.connect(self.search)
        self.b_sbs = QPushButton(tr("p_sbs_vn"))
        self.b_sbs.clicked.connect(lambda: (self.q.setText("SBS Vietnamese"), self.search()))
        sr.addWidget(self.q, 1)
        sr.addWidget(self.b_s)
        sr.addWidget(self.b_sbs)
        self.lay.addLayout(sr)
        from .podtools import GROUPS, ensure_schema
        ensure_schema(self.db)
        from .lookpage import FlowLayout
        gw = QWidget()
        gw.setObjectName("LibChips")
        gr = FlowLayout(gw, 4)
        self._flows = [(gw, gr)]
        self.g_label = QLabel()
        gr.addWidget(self.g_label)
        self.g_btns = []
        for key, en, vi, _ids, _news in GROUPS:
            b = QToolButton()
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("names", (en, vi))
            b.clicked.connect(lambda _=False, k=key: self.show_group(k))
            gr.addWidget(b)
            self.g_btns.append(b)
        self.lay.addWidget(gw)
        self.results = tree([tr("p_search"), tr("col_artist")], [420, 300])
        self.results.setMaximumHeight(180)
        self.results.hide()
        self.results.itemDoubleClicked.connect(lambda it, _c: self.subscribe(it.data(0, Qt.UserRole)))
        self.lay.addWidget(self.results)
        sp = QSplitter()
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.subs = QListWidget()
        self.subs.setIconSize(QSize(48, 48))
        self.subs.setMinimumWidth(260)
        self.subs.currentItemChanged.connect(lambda *_: self.load())
        self.subs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.subs.customContextMenuRequested.connect(self._sub_menu)
        ll.addWidget(self.subs)
        self.empty = hint(tr("p_none"))
        ll.addWidget(self.empty)
        sp.addWidget(left)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        hr = QHBoxLayout()
        self.ptitle = h2("")
        hr.addWidget(self.ptitle, 1)
        rl.addLayout(hr)
        from .lookpage import FlowLayout
        cbw = QWidget()
        cbf = FlowLayout(cbw, 4)
        self._flows.append((cbw, cbf))
        self.auto = QCheckBox(tr("p_auto"))
        self.auto.toggled.connect(self._auto_toggled)
        cbf.addWidget(self.auto)
        self.autosave = QCheckBox()
        self.autosave.toggled.connect(self._autosave_toggled)
        cbf.addWidget(self.autosave)
        rl.addWidget(cbw)
        self.stale = QLabel()
        self.stale.setObjectName("Badge")
        self.stale.hide()
        rl.addWidget(self.stale)
        self.eps = tree([tr("p_episodes"), tr("col_added"), tr("col_len"), ""], [460, 120, 80, 120])
        self.eps.itemDoubleClicked.connect(lambda it, _c: self.play_ep(it))
        self.eps.setContextMenuPolicy(Qt.CustomContextMenu)
        self.eps.customContextMenuRequested.connect(self._ep_menu)
        self.eps.setMinimumHeight(150)
        rl.addWidget(self.eps, 1)
        bw = QWidget()
        br = FlowLayout(bw, 4)
        self._flows.append((bw, br))
        self.b_play = QPushButton(icon("play", theme.c("on_accent"), 18), tr("play"))
        self.b_play.setObjectName("Primary")
        self.b_play.clicked.connect(lambda: self.play_ep(self.eps.currentItem()))
        self.b_dl = QPushButton(icon("download", theme.c("ink"), 18), tr("p_download"))
        self.b_dl.clicked.connect(lambda: self.download(self.eps.currentItem()))
        self.b_save = QPushButton("💾")
        self.b_save.clicked.connect(lambda: self.save_ep(self.eps.currentItem()))
        self.b_clip = QPushButton("✂")
        self.b_clip.clicked.connect(self.clip_now)
        br.addWidget(self.b_play)
        br.addWidget(self.b_dl)
        br.addWidget(self.b_save)
        br.addWidget(self.b_clip)
        self.prog = QProgressBar()
        self.prog.setFixedWidth(200)
        self.prog.hide()
        br.addWidget(self.prog)
        rl.addWidget(bw)
        sp.addWidget(right)
        sp.setOrientation(Qt.Vertical)
        self.subs.setMinimumWidth(0)
        self.subs.setMinimumHeight(70)
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 3)
        sp.setSizes([120, 480])
        sp.setChildrenCollapsible(False)
        sp.setMinimumHeight(380)
        self.lay.addWidget(sp, 1)
        self._wrap_scroll()
        self.downloading = set()

    def _fit_flows(self):
        for w, f in getattr(self, "_flows", ()):
            if w.width() > 0:
                w.setMinimumHeight(f.heightForWidth(w.width()))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self._fit_flows)

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._fit_flows)

    def _wrap_scroll(self):
        # Short window or big text: the whole page scrolls instead of squashing the lists.
        inner = QWidget()
        inner.setObjectName("PageInner")
        il = QVBoxLayout(inner)
        old = self.lay
        il.setContentsMargins(old.contentsMargins())
        il.setSpacing(old.spacing())
        stretches = [old.stretch(i) for i in range(old.count())]
        for st in stretches:
            item = old.takeAt(0)
            if item.widget() is not None:
                il.addWidget(item.widget(), st)
            elif item.layout() is not None:
                lay = item.layout()
                lay.setParent(None)
                il.addLayout(lay, st)
            else:
                il.addItem(item)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QScrollArea.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sc.setWidget(inner)
        sc.setStyleSheet("QScrollArea{background:transparent}")
        sc.viewport().setAutoFillBackground(False)
        inner.setAutoFillBackground(False)
        inner.setStyleSheet("#PageInner{background:transparent}")
        old.setContentsMargins(0, 0, 0, 0)
        old.addWidget(sc)
        self.lay = il

    def retranslate(self):
        super().retranslate()
        self.q.setPlaceholderText(tr("p_search"))
        self.b_s.setText(tr("p_search"))
        self.b_sbs.setText(tr("p_sbs_vn"))
        self.empty.setText(tr("p_none"))
        self.auto.setText(tr("p_auto"))
        self.b_play.setText(tr("play"))
        self.b_dl.setText(tr("p_download"))
        self._names()
        self.eps.setHeaderLabels([tr("p_episodes"), tr("col_added"), tr("col_len"), ""])
        self.results.setHeaderLabels([tr("p_search"), tr("col_artist")])
        self.load()
        QTimer.singleShot(0, self._fit_flows)

    def _names(self):
        from ..art.themes import t
        self.g_label.setText(t("Suggested:", "Gợi Ý:"))
        for b in self.g_btns:
            b.setText(t(*b.property("names")).replace("&", "&&"))
        self.autosave.setText("⏰ " + t("Auto-save new episodes", "Tự lưu tập mới"))
        self.b_save.setText("💾 " + t("Save", "Lưu Cả Tập"))
        self.b_clip.setText("✂ A–B")
        self.b_save.setToolTip(t("Save the whole episode to Recordings", "Lưu cả tập vào Bản Thâu Âm"))
        self.b_clip.setToolTip(t("Cut a part (A–B) of the episode that is playing", "Cắt một đoạn (A–B) của tập đang phát"))

    def show_group(self, key):
        from .podtools import lookup_group
        self.results.clear()
        self.results.show()
        self.results.addTopLevelItem(QTreeWidgetItem([tr("working"), ""]))
        run_bg(lookup_group, self.db, key, done=self._results)

    def _autosave_toggled(self, on):
        from .podtools import set_autosave
        it = self.subs.currentItem()
        if it:
            set_autosave(self.db, it.data(Qt.UserRole), on)

    def save_ep(self, it):
        from .podtools import save_episode_bg
        e = self._ep(it)
        if e:
            save_episode_bg(self.ctx, e)

    def clip_now(self):
        from ..art.themes import t
        from .podtools import ClipDialog
        cur = self.ctx.player.current
        if not cur or cur.get("kind") != "episode":
            self.ctx.toast(t("Play an episode first, then cut a part of it.", "Hãy phát một tập trước rồi cắt đoạn."))
            return
        ClipDialog(self.ctx).exec()

    def folder(self):
        d = self.db.get("podcast_dir") or str(app_info.documents_dir() / app_info.APP_NAME / "Podcasts")
        os.makedirs(d, exist_ok=True)
        return d

    def refresh(self):
        cur = self.subs.currentItem().data(Qt.UserRole) if self.subs.currentItem() else None
        self.subs.blockSignals(True)
        self.subs.clear()
        pick = None
        for p in self.db.q("SELECT * FROM podcasts ORDER BY title COLLATE NOCASE"):
            new = self.db.one("SELECT COUNT(*) c FROM episodes WHERE podcast_id=? AND done=0", (p["id"],))["c"]
            it = QListWidgetItem(p["title"] + (f"\n{tr('p_new', n=new)}" if new else ""))
            from .widgets import cover_pixmap
            it.setIcon(cover_pixmap(p["art_key"], 48, 10, p["title"] or ""))
            it.setData(Qt.UserRole, p["id"])
            self.subs.addItem(it)
            if p["id"] == cur:
                pick = it
        self.subs.blockSignals(False)
        self.empty.setVisible(self.subs.count() == 0)
        if pick:
            self.subs.setCurrentItem(pick)
        elif self.subs.count():
            self.subs.setCurrentRow(0)
        self.load()

    def load(self):
        it = self.subs.currentItem()
        self.eps.clear()
        if not it:
            self.ptitle.setText("")
            return
        pid = it.data(Qt.UserRole)
        p = self.db.one("SELECT * FROM podcasts WHERE id=?", (pid,))
        self.ptitle.setText(p["title"])
        self.auto.blockSignals(True)
        self.auto.setChecked(bool(p["auto_dl"]))
        self.auto.blockSignals(False)
        from ..art.themes import t
        from .podtools import NEWS_MAX_AGE, autosave_ids
        self.autosave.blockSignals(True)
        self.autosave.setChecked(int(pid) in autosave_ids(self.db))
        self.autosave.blockSignals(False)
        newest = self.db.one("SELECT MAX(published) m FROM episodes WHERE podcast_id=?", (pid,))["m"] or 0
        n_all = self.db.one("SELECT COUNT(*) c FROM episodes WHERE podcast_id=?", (pid,))["c"]
        if newest and time.time() - newest > NEWS_MAX_AGE:
            self.stale.setText(t("This channel has stopped updating", "Kênh này đã ngưng cập nhật") + " · "
                               + t("newest episode ", "tập mới nhất ") + datetime.fromtimestamp(newest).strftime("%d/%m/%Y"))
            self.stale.show()
        else:
            self.stale.hide()
        self.ptitle.setText(p["title"] + (t(f"  ·  {n_all} episodes (newest 300 shown)", f"  ·  {n_all} tập (hiện 300 tập mới nhất)") if n_all > 300 else ""))
        for e in self.db.q("SELECT * FROM episodes WHERE podcast_id=? ORDER BY published DESC LIMIT 300", (pid,)):
            d = datetime.fromtimestamp(e["published"]).strftime("%d/%m/%Y") if e["published"] else ""
            st = tr("p_downloaded") if e["local_path"] and os.path.exists(e["local_path"]) else ""
            w = QTreeWidgetItem([e["title"], d, fmt_time(e["duration"]) if e["duration"] else "", st])
            w.setIcon(0, icon("podcast", theme.c("grey") if e["done"] else theme.c("teal"), 18))
            w.setData(0, Qt.UserRole, e["id"])
            self.eps.addTopLevelItem(w)

    def _auto_toggled(self, on):
        it = self.subs.currentItem()
        if it:
            self.db.x("UPDATE podcasts SET auto_dl=? WHERE id=?", (int(on), it.data(Qt.UserRole)))

    def search(self):
        text = self.q.text().strip()
        if not text:
            return
        self.results.clear()
        self.results.show()
        self.results.addTopLevelItem(QTreeWidgetItem([tr("working"), ""]))
        run_bg(online.podcast_search, text, done=self._results)

    def _results(self, rows):
        self.results.clear()
        for r in rows:
            it = QTreeWidgetItem([r["title"], r["author"] or ""])
            it.setIcon(0, icon("add", theme.c("teal"), 18))
            it.setData(0, Qt.UserRole, r)
            it.setToolTip(0, tr("p_sub"))
            self.results.addTopLevelItem(it)
        if not rows:
            self.results.addTopLevelItem(QTreeWidgetItem([tr("r_offline"), ""]))

    def subscribe(self, r):
        if not r:
            return
        if not self.db.one("SELECT id FROM podcasts WHERE feed=?", (r["feed"],)):
            self.db.x("INSERT INTO podcasts(title, author, feed, image) VALUES(?,?,?,?)", (r["title"], r["author"], r["feed"], r["image"]))
        self.results.hide()
        self.refresh()
        self.check_all()

    def check_all(self):
        run_bg(self._check, done=self._checked)

    def _check(self):
        from .. import tags
        from .podtools import autosave_ids
        new_total = 0
        to_dl = []
        to_save = []
        autos = autosave_ids(self.db)
        for p in self.db.q("SELECT * FROM podcasts"):
            try:
                info = online.podcast_feed(p["feed"])
            except Exception as e:
                app_info.log.info("feed failed %s: %s", p["feed"], e)
                continue
            if not p["art_key"] and info.get("image"):
                try:
                    data = online.get(info["image"], raw=True)
                    key = "pod_" + str(p["id"])
                    if tags.save_thumbs(key, data):
                        self.db.x("UPDATE podcasts SET art_key=? WHERE id=?", (key, p["id"]))
                except Exception:
                    pass
            first = not self.db.one("SELECT id FROM episodes WHERE podcast_id=?", (p["id"],))
            for k, e in enumerate(info["episodes"][:200]):
                before = self.db.con.total_changes
                self.db.x("INSERT OR IGNORE INTO episodes(podcast_id,guid,title,url,published,duration,done,hq) VALUES(?,?,?,?,?,?,?,?)",
                          (p["id"], e["guid"], e["title"], e["url"], e["published"], e["duration"], 1 if first and k >= 3 else 0, e.get("hq") or None), commit=False)
                if self.db.con.total_changes > before and not first:
                    new_total += 1
                    if p["id"] in autos:
                        to_save.append((p["id"], e["guid"]))
            self.db.commit()
            self.db.x("UPDATE podcasts SET last_check=? WHERE id=?", (time.time(), p["id"]))
            if p["auto_dl"]:
                for e in self.db.q("SELECT * FROM episodes WHERE podcast_id=? AND done=0 AND local_path IS NULL ORDER BY published DESC LIMIT 2", (p["id"],)):
                    to_dl.append(e["id"])
        from .podtools import save_whole
        for pid, guid in to_save:
            e = self.db.one("SELECT e.*, p.title ptitle FROM episodes e JOIN podcasts p ON p.id=e.podcast_id WHERE e.podcast_id=? AND e.guid=?", (pid, guid))
            if e:
                try:
                    save_whole(self.db, e, e["ptitle"])
                except Exception as ex:
                    app_info.log.info("auto-save failed: %s", ex)
        return to_dl

    def _checked(self, to_dl):
        self.refresh()
        for eid in to_dl:
            self._download_id(eid)

    def _ep(self, it):
        if not it:
            return None
        return self.db.one("SELECT e.*, p.title ptitle, p.art_key FROM episodes e JOIN podcasts p ON p.id=e.podcast_id WHERE e.id=?",
                           (it.data(0, Qt.UserRole),))

    def play_ep(self, it):
        e = self._ep(it)
        if not e:
            return
        from .podtools import best_url
        item = Item(kind="episode", id=e["id"], title=e["title"], artist=e["ptitle"], url=best_url(self.db, e), local_path=e["local_path"],
                    duration=e["duration"] or 0, art_key=e["art_key"])
        self.ctx.player.play_item(item)
        if e["position"] and e["position"] > 10 and (not e["duration"] or e["position"] < e["duration"] - 20):
            QTimer.singleShot(800, lambda: self.ctx.player.seek(e["position"]))
        self.db.x("UPDATE episodes SET done=1 WHERE id=?", (e["id"],))

    def download(self, it):
        e = self._ep(it)
        if e:
            self._download_id(e["id"])

    def _download_id(self, eid):
        if eid in self.downloading:
            return
        from .podtools import best_url
        e = self.db.one("SELECT e.*, p.title ptitle FROM episodes e JOIN podcasts p ON p.id=e.podcast_id WHERE e.id=?", (eid,))
        url = best_url(self.db, e)
        ext = os.path.splitext(url.split("?")[0])[1] or ".mp3"
        d = os.path.join(self.folder(), recorder.safe_name(e["ptitle"]))
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, recorder.safe_name(e["title"])[:90] + ext)
        self.downloading.add(eid)
        self.prog.show()

        def prog(got, total):
            if total:
                self.prog.setValue(int(got * 100 / total))

        def done(_r):
            self.downloading.discard(eid)
            self.db.x("UPDATE episodes SET local_path=? WHERE id=?", (dest, eid))
            self.prog.setVisible(bool(self.downloading))
            self.load()

        def failed(err):
            self.downloading.discard(eid)
            self.prog.setVisible(bool(self.downloading))
            self.ctx.toast(err[:120])
        run_bg(lambda progress=None, stop=None: online.download(url, dest, progress, stop),
               with_progress=True, done=done, failed=failed, progress=lambda a: prog(*a))

    def _ep_menu(self, pos):
        it = self.eps.itemAt(pos)
        if not it:
            return
        from ..art.themes import t
        m = QMenu(self)
        m.addAction(tr("play"), lambda: self.play_ep(it))
        m.addAction(tr("p_download"), lambda: self.download(it))
        m.addAction("💾 " + t("Save Whole Episode To Recordings", "Lưu Cả Tập Vào Bản Thâu Âm"), lambda: self.save_ep(it))
        m.addAction(t("Add To Queue", "Thêm Vào Hàng Đợi"), lambda: self.queue_ep(it))
        m.addAction(tr("p_mark_done"), lambda: (self.db.x("UPDATE episodes SET done=1 WHERE id=?", (it.data(0, Qt.UserRole),)), self.load()))
        m.exec(self.eps.viewport().mapToGlobal(pos))

    def _sub_menu(self, pos):
        it = self.subs.itemAt(pos)
        if not it:
            return
        from ..art.themes import t
        from .podtools import autosave_ids, set_autosave
        pid = it.data(Qt.UserRole)
        m = QMenu(self)
        m.addAction("▶ " + t("Play Newest Episode", "Phát Tập Mới Nhất"), lambda: self.play_newest(pid))
        m.addAction("💾 " + t("Save Newest Episode", "Lưu Tập Mới Nhất"), lambda: self.save_newest(pid))
        a = m.addAction("⏰ " + t("Auto-Save Each New Episode", "Tự Lưu Mỗi Tập Mới"))
        a.setCheckable(True)
        a.setChecked(int(pid) in autosave_ids(self.db))
        a.toggled.connect(lambda on: (set_autosave(self.db, pid, on), self.load()))
        p = self.db.one("SELECT * FROM podcasts WHERE id=?", (pid,))
        a2 = m.addAction(t("Download New Episodes On Their Own", "Tự Tải Tập Mới"))
        a2.setCheckable(True)
        a2.setChecked(bool(p["auto_dl"]))
        a2.toggled.connect(lambda on: (self.db.x("UPDATE podcasts SET auto_dl=? WHERE id=?", (int(on), pid)), self.load()))
        m.addAction(t("Copy Feed Link (to share)", "Chép Đường Dẫn Kênh (để chia sẻ)"), lambda: QApplication.clipboard().setText(p["feed"]))
        m.addSeparator()
        m.addAction(tr("p_unsub"), lambda: self.unsub(pid))
        m.exec(self.subs.mapToGlobal(pos))

    def _newest(self, pid):
        return self.db.one("SELECT e.*, p.title ptitle, p.art_key FROM episodes e JOIN podcasts p ON p.id=e.podcast_id WHERE e.podcast_id=? "
                           "ORDER BY e.published DESC LIMIT 1", (pid,))

    def play_newest(self, pid):
        e = self._newest(pid)
        if e:
            self.ctx.player.play_item(Item(kind="episode", id=e["id"], title=e["title"], artist=e["ptitle"], url=e["url"],
                                           local_path=e["local_path"], duration=e["duration"] or 0, art_key=e["art_key"]))

    def save_newest(self, pid):
        from .podtools import save_episode_bg
        e = self._newest(pid)
        if e:
            save_episode_bg(self.ctx, e)

    def queue_ep(self, it):
        e = self._ep(it)
        if e:
            self.ctx.player.add_queue([Item(kind="episode", id=e["id"], title=e["title"], artist=e["ptitle"], url=e["url"],
                                               local_path=e["local_path"], duration=e["duration"] or 0, art_key=e["art_key"])])

    def unsub(self, pid):
        if QMessageBox.question(self, tr("p_unsub"), tr("p_unsub") + "?") == QMessageBox.Yes:
            self.db.x("DELETE FROM episodes WHERE podcast_id=?", (pid,))
            self.db.x("DELETE FROM podcasts WHERE id=?", (pid,))
            self.refresh()


# =========================================================================== Recordings
class RecordingsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_recordings", [("s_add", "clock", self.add, True), ("open_folder", "folder", self.open_folder, False)])
        self.l_active = h2(tr("s_active"))
        self.active = tree([tr("s_station"), tr("col_len"), tr("s_format"), ""], [320, 100, 220, 200])
        self.active.setMaximumHeight(120)
        self.b_stop = QPushButton(icon("stop", theme.c("ink"), 16), tr("r_stop_rec"))
        self.b_stop.clicked.connect(self.stop_sel)
        self.lay.addWidget(self.l_active)
        self.lay.addWidget(self.active)
        r = QHBoxLayout()
        r.addWidget(self.b_stop)
        self.awake = hint(tr("rec_keep_awake"))
        r.addWidget(self.awake, 1)
        self.lay.addLayout(r)
        self.l_sched = h2(tr("s_list"))
        self.lay.addWidget(self.l_sched)
        self.sched = tree([tr("s_station"), tr("s_start"), tr("s_minutes"), tr("s_days"), tr("s_format"), tr("s_enabled")],
                          [260, 90, 80, 220, 200, 60])
        self.sched.setMaximumHeight(170)
        self.sched.itemDoubleClicked.connect(lambda it, _c: self.edit(it))
        self.lay.addWidget(self.sched)
        sb = QHBoxLayout()
        self.b_edit = QPushButton(tr("s_edit"))
        self.b_edit.clicked.connect(lambda: self.edit(self.sched.currentItem()))
        self.b_del = QPushButton(tr("s_delete"))
        self.b_del.clicked.connect(self.delete)
        sb.addWidget(self.b_edit)
        sb.addWidget(self.b_del)
        sb.addStretch()
        self.lay.addLayout(sb)
        self.l_list = h2(tr("rec_list"))
        self.lay.addWidget(self.l_list)
        from .common import TrackTable
        self.table = TrackTable(ctx, name="recordings")
        self.lay.addWidget(self.table, 1)
        self.t = QTimer(self)
        self.t.timeout.connect(self._tick)
        self.t.start(1000)

    def retranslate(self):
        super().retranslate()
        for w, k in ((self.l_active, "s_active"), (self.l_sched, "s_list"), (self.l_list, "rec_list"),
                     (self.b_stop, "r_stop_rec"), (self.b_edit, "s_edit"), (self.b_del, "s_delete"), (self.awake, "rec_keep_awake")):
            w.setText(tr(k))
        self.sched.setHeaderLabels([tr("s_station"), tr("s_start"), tr("s_minutes"), tr("s_days"), tr("s_format"), tr("s_enabled")])
        self.active.setHeaderLabels([tr("s_station"), tr("col_len"), tr("s_format"), ""])
        self.refresh()

    def rec_dir(self):
        return self.db.get("rec_dir") or str(app_info.default_recordings_dir())

    def open_folder(self):
        os.makedirs(self.rec_dir(), exist_ok=True)
        open_in_explorer(self.rec_dir())

    def refresh(self):
        self.sched.clear()
        days = tr("days_short").split(",")
        for s in self.db.q("SELECT s.*, st.name FROM schedules s LEFT JOIN stations st ON st.id=s.station_id ORDER BY start_hm"):
            when = s["once_date"] or ", ".join(days[int(d)] for d in (s["days"] or "").split(",") if d.strip().isdigit())
            fmt = recorder.FORMATS.get(s["fmt"] or "original", recorder.FORMATS["original"])[1 if lang() == "vi" else 0]
            it = QTreeWidgetItem([s["name"] or "?", s["start_hm"], str(s["minutes"]), when, fmt, "✓" if s["enabled"] else ""])
            it.setData(0, Qt.UserRole, s["id"])
            self.sched.addTopLevelItem(it)
        self.table.set_rows(self.db.q("SELECT * FROM tracks WHERE kind='radio' ORDER BY added DESC"))
        self._tick()

    def _tick(self):
        recs = [r for r in self.ctx.recordings if r.is_alive()]
        if self.active.topLevelItemCount() != len(recs):
            self.active.clear()
            for r in recs:
                it = QTreeWidgetItem([r.station, "", "", ""])
                it.setData(0, Qt.UserRole, id(r))
                self.active.addTopLevelItem(it)
        for i, r in enumerate(recs):
            it = self.active.topLevelItem(i)
            it.setText(1, fmt_time(r.elapsed))
            it.setText(2, recorder.FORMATS[r.fmt][1 if lang() == "vi" else 0])
            it.setText(3, r.title or (r.error or "")[:60])

    def stop_sel(self):
        it = self.active.currentItem()
        for r in self.ctx.recordings:
            if it is None or id(r) == it.data(0, Qt.UserRole):
                r.stop()

    def add(self):
        from .dialogs import ScheduleDialog
        ScheduleDialog(self, self.db, None, None).exec()
        self.refresh()

    def edit(self, it):
        if not it:
            return
        from .dialogs import ScheduleDialog
        ScheduleDialog(self, self.db, it.data(0, Qt.UserRole), None).exec()
        self.refresh()

    def delete(self):
        it = self.sched.currentItem()
        if it:
            self.db.x("DELETE FROM schedules WHERE id=?", (it.data(0, Qt.UserRole),))
            self.refresh()


# =========================================================================== Library tools
class ToolsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_tools")
        self.tabs = QTabWidget()
        # duplicates
        d = QWidget()
        dl = QVBoxLayout(d)
        self.d_hint = hint(tr("t_dupes_hint"))
        dl.addWidget(self.d_hint)
        r = QHBoxLayout()
        self.d_btn = QPushButton(icon("search", theme.c("on_accent"), 18), tr("t_start"))
        self.d_btn.setObjectName("Primary")
        self.d_btn.clicked.connect(self.run_dupes)
        self.d_count = QLabel("")
        r.addWidget(self.d_btn)
        r.addWidget(self.d_count, 1)
        dl.addLayout(r)
        self.d_tree = QTreeWidget()
        self.d_tree.setHeaderLabels([tr("col_title"), tr("col_artist"), tr("col_album"), tr("col_fmt"), tr("col_len"), tr("file")])
        for i, w in enumerate((260, 180, 180, 110, 70, 400)):
            self.d_tree.setColumnWidth(i, w)
        self.d_tree.itemDoubleClicked.connect(lambda it, _c: self._open(it))
        dl.addWidget(self.d_tree, 1)
        self.tabs.addTab(d, tr("t_dupes"))
        # file check
        c = QWidget()
        clay = QVBoxLayout(c)
        self.c_hint = hint(tr("t_check_hint"))
        clay.addWidget(self.c_hint)
        r2 = QHBoxLayout()
        self.c_btn = QPushButton(icon("search", theme.c("on_accent"), 18), tr("t_start"))
        self.c_btn.setObjectName("Primary")
        self.c_btn.clicked.connect(self.run_check)
        self.c_stop = QPushButton(tr("t_stop"))
        self.c_stop.clicked.connect(self.stop_check)
        self.c_stop.setEnabled(False)
        self.c_prog = QProgressBar()
        self.c_count = QLabel("")
        r2.addWidget(self.c_btn)
        r2.addWidget(self.c_stop)
        r2.addWidget(self.c_prog, 1)
        r2.addWidget(self.c_count)
        clay.addLayout(r2)
        self.c_tree = tree([tr("problem"), tr("col_title"), tr("col_artist"), tr("col_fmt"), tr("file")], [300, 240, 180, 100, 400])
        self.c_tree.itemDoubleClicked.connect(lambda it, _c: self._open(it))
        clay.addWidget(self.c_tree, 1)
        self.tabs.addTab(c, tr("t_check"))
        self.lay.addWidget(self.tabs, 1)
        self.job = None

    def retranslate(self):
        super().retranslate()
        self.d_tree.setHeaderLabels([tr("col_title"), tr("col_artist"), tr("col_album"), tr("col_fmt"), tr("col_len"), tr("file")])
        self.c_tree.setHeaderLabels([tr("problem"), tr("col_title"), tr("col_artist"), tr("col_fmt"), tr("file")])
        self.tabs.setTabText(0, tr("t_dupes"))
        self.tabs.setTabText(1, tr("t_check"))
        self.d_hint.setText(tr("t_dupes_hint"))
        self.c_hint.setText(tr("t_check_hint"))
        self.d_btn.setText(tr("t_start"))
        self.c_btn.setText(tr("t_start"))
        self.c_stop.setText(tr("t_stop"))

    def _open(self, it):
        p = it.data(0, Qt.UserRole + 1)
        if p:
            open_in_explorer(p)

    def run_dupes(self):
        self.d_btn.setEnabled(False)
        run_bg(tools.find_duplicates, self.db, done=self._dupes)

    def _dupes(self, groups):
        self.d_btn.setEnabled(True)
        self.d_tree.clear()
        for g in groups:
            top = QTreeWidgetItem([g[0]["title"] or "", g[0]["artist"] or "", "", "", "", f"{len(g)}×"])
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            for k, r in enumerate(g):
                p = scanner.track_path(r) or r["path"]
                fmt = (r["codec"] or "") + (f" {r['bits']}-bit" if r["bits"] else (f" {int((r['bitrate'] or 0) / 1000)}k" if r["bitrate"] else ""))
                ch = QTreeWidgetItem([("★ " + tr("t_best") + " · " if k == 0 else "") + (r["title"] or ""), r["artist"] or "",
                                      r["album"] or "", fmt, fmt_time(r["duration"]), p])
                ch.setData(0, Qt.UserRole + 1, p)
                top.addChild(ch)
            self.d_tree.addTopLevelItem(top)
            top.setExpanded(True)
        self.d_count.setText(tr("t_groups", n=len(groups)))

    def run_check(self):
        self.c_btn.setEnabled(False)
        self.c_stop.setEnabled(True)
        self.c_tree.clear()
        self.job = run_bg(tools.check_files, self.db, with_progress=True, done=self._checked,
                          progress=lambda a: (self.c_prog.setMaximum(max(1, a[1])), self.c_prog.setValue(a[0])))

    def stop_check(self):
        if self.job:
            self.job.stopped = True

    def _checked(self, probs):
        self.c_btn.setEnabled(True)
        self.c_stop.setEnabled(False)
        for r, code, detail in probs:
            text = tr("pr_" + code, d=detail)
            if code == "damaged" and detail:
                text += f" ({detail[:60]})"
            p = scanner.track_path(r) or r["path"]
            it = QTreeWidgetItem([text, r["title"] or "", r["artist"] or "", r["codec"] or "", p])
            it.setData(0, Qt.UserRole + 1, p)
            it.setIcon(0, icon("info", "#E5484D" if code in ("damaged", "missing_file", "fake_lossless") else theme.c("accent"), 18))
            self.c_tree.addTopLevelItem(it)
        self.c_count.setText(tr("t_problems", n=len(probs)))


# =========================================================================== Now Playing
class NowBackground(QWidget):
    def __init__(self):
        super().__init__()
        self.col = QColor(theme.c("teal"))
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, e):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        c1 = QColor(self.col)
        c1.setAlpha(150 if not theme.c("dark") else 120)
        g.setColorAt(0, c1)
        g.setColorAt(1, QColor(theme.c("bg") if not theme.c("bg").startswith("rgba") else "#E6F1F6"))
        p.fillRect(self.rect(), QBrush(g))


class NowPlayingPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.setObjectName("Page")
        self.ctx = ctx
        self.db = ctx.db
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.bg = NowBackground()
        outer.addWidget(self.bg)
        lay = QHBoxLayout(self.bg)
        lay.setContentsMargins(36, 26, 36, 16)
        lay.setSpacing(30)
        left = QVBoxLayout()
        left.addStretch()
        art = QWidget()
        art.setFixedSize(470, 360)
        self.disc = SpinningDisc(330, art)
        self.disc.move(130, 15)
        self.cover = Cover(340, 26, art)
        self.cover.move(0, 10)
        left.addWidget(art, 0, Qt.AlignCenter)
        self.t = h1("")
        self.t.setWordWrap(True)
        self.t.setAlignment(Qt.AlignCenter)
        self.a = h2("")
        self.a.setAlignment(Qt.AlignCenter)
        self.al = QLabel("")
        self.al.setObjectName("Muted")
        self.al.setAlignment(Qt.AlignCenter)
        self.reel = QLabel("")
        self.reel.setObjectName("TealBadge")
        self.reel.hide()
        left.addWidget(self.t)
        left.addWidget(self.a)
        left.addWidget(self.al)
        left.addWidget(self.reel, 0, Qt.AlignCenter)
        left.addStretch()
        self.leftw = QWidget()
        self.leftw.setLayout(left)
        lay.addWidget(self.leftw, 3)
        self.side = QTabWidget()
        self.side.setMinimumWidth(280)
        self.lyr = QListWidget()
        self.lyr.setWordWrap(True)
        self.lyr.setSpacing(4)
        self.lyr.setFocusPolicy(Qt.NoFocus)
        self.lyr.setSelectionMode(QAbstractItemView.NoSelection)
        self.side.addTab(self.lyr, tr("lyrics"))
        qw = QWidget()
        ql = QVBoxLayout(qw)
        self.queue = QListWidget()
        self.queue.setIconSize(QSize(40, 40))
        self.queue.itemDoubleClicked.connect(lambda it: ctx.player.jump_to_upcoming(it.data(Qt.UserRole)))
        self.queue.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue.customContextMenuRequested.connect(self._queue_menu)
        ql.addWidget(self.queue)
        self.b_clear = QPushButton(tr("clear_queue"))
        self.b_clear.clicked.connect(ctx.player.clear_queue)
        ql.addWidget(self.b_clear)
        self.side.addTab(qw, tr("queue"))
        lay.addWidget(self.side, 2)
        self.timed = []
        self.cur_line = -1
        self.lyr_for = None
        ctx.player.changed.connect(self.on_changed)
        ctx.player.state.connect(self.disc.set_playing)
        ctx.player.queue_changed.connect(self.fill_queue)
        ctx.player.radio_title.connect(lambda t: self.a.setText(t))
        self.tm = QTimer(self)
        self.tm.timeout.connect(self._tick)
        self.tm.start(250)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        small = self.width() < 900
        self.leftw.setVisible(not small)
        self.bg.layout().setContentsMargins(*(6, 6, 6, 6) if small else (36, 26, 36, 16))

    def retranslate(self):
        self.side.setTabText(0, tr("lyrics"))
        self.side.setTabText(1, tr("queue"))
        self.b_clear.setText(tr("clear_queue"))
        self.fill_queue()
        if not getattr(self, "timed", None) and self.lyr.count() == 1 and self.lyr.item(0).data(Qt.UserRole + 7):
            self.lyr.item(0).setText(tr("no_lyrics"))

    def show_tab(self, i):
        self.side.setCurrentIndex(i)

    def on_changed(self, it):
        if it is None:
            return
        self.t.setText(it.title)
        self.a.setText(it.get("now_title") or it.get("artist") or "")
        self.al.setText(" · ".join(x for x in (it.get("album") or "", it.get("codec") or "") if x))
        self.cover.set_key(it.get("art_key"), it.title)
        self.disc.set_key(it.get("art_key"), it.title)
        self.bg.col = dominant_color(it.get("art_key"), theme.c("teal"))
        self.bg.update()
        owned = self.ctx.reel.formats_for(it.get("album"), it.get("albumartist") or it.get("artist")) if self.ctx.reel and it.get("kind") == "track" else []
        self.reel.setVisible(bool(owned))
        if owned:
            self.reel.setText(tr("album_on_reel", f=", ".join(owned)))
        self.load_lyrics(it)
        self.fill_queue()

    def fill_queue(self):
        from .widgets import cover_pixmap
        self.queue.clear()
        up = self.ctx.player.upcoming()
        for k, q in enumerate(up[:300]):
            w = QListWidgetItem(f"{q.title}\n{q.get('artist') or ''}")
            w.setIcon(cover_pixmap(q.get("art_key"), 40, 8, q.title))
            w.setData(Qt.UserRole, k)
            self.queue.addItem(w)
        if not up:
            w = QListWidgetItem(tr("queue_empty"))
            w.setFlags(Qt.NoItemFlags)
            self.queue.addItem(w)

    def _queue_menu(self, pos):
        it = self.queue.itemAt(pos)
        if not it or it.data(Qt.UserRole) is None:
            return
        m = QMenu(self)
        m.addAction(tr("play"), lambda: self.ctx.player.jump_to_upcoming(it.data(Qt.UserRole)))
        m.addAction(tr("remove_from_pl"), lambda: self.ctx.player.remove_upcoming(it.data(Qt.UserRole)))
        m.exec(self.queue.mapToGlobal(pos))

    # ---- lyrics
    def _set_lines(self, timed, plain):
        self.lyr.clear()
        self.timed = timed
        self.cur_line = -1
        if timed:
            for _t, line in timed:
                w = QListWidgetItem(line or "♪")
                w.setTextAlignment(Qt.AlignCenter)
                self.lyr.addItem(w)
        elif plain:
            for line in plain.splitlines():
                w = QListWidgetItem(line)
                w.setTextAlignment(Qt.AlignCenter)
                self.lyr.addItem(w)
        else:
            w = QListWidgetItem(tr("no_lyrics"))
            w.setData(Qt.UserRole + 7, True)
            w.setTextAlignment(Qt.AlignCenter)
            self.lyr.addItem(w)

    def load_lyrics(self, it):
        self.lyr_for = id(it)
        if it.get("kind") != "track":
            self._set_lines([], "")
            return
        p = scanner.track_path(it)
        cands = []
        if p:
            base = os.path.splitext(p)[0]
            cands = [base + ".lrc", base + ".txt"]
        cache = app_info.sub("lyrics") / f"{it['id']}.lrc"
        cands.append(str(cache))
        for c in cands:
            if os.path.exists(c):
                try:
                    with open(c, encoding="utf-8-sig", errors="replace") as fh:
                        timed, plain = online.parse_lrc(fh.read())
                    self._set_lines(timed, plain)
                    return
                except OSError:
                    pass
        if not self.db.get("lyrics_online"):
            self._set_lines([], "")
            return
        self.lyr.clear()
        self.lyr.addItem(tr("lyrics_loading"))
        token = id(it)

        def fetch():
            return online.lrclib(it.get("artist"), it.title, it.get("album"), it.get("duration"))

        def done(text):
            if self.lyr_for != token:
                return
            if text:
                try:
                    cache.write_text(text, encoding="utf-8")
                except OSError:
                    pass
            self._set_lines(*online.parse_lrc(text or "")) if text else self._set_lines([], "")
        run_bg(fetch, done=done, failed=lambda e: self._set_lines([], ""))

    def _tick(self):
        if not self.timed or not self.isVisible():
            return
        pos = self.ctx.player.position() + 0.3
        idx = -1
        for i, (t, _l) in enumerate(self.timed):
            if t <= pos:
                idx = i
            else:
                break
        if idx != self.cur_line and idx >= 0:
            for i in (self.cur_line, idx):
                if 0 <= i < self.lyr.count():
                    w = self.lyr.item(i)
                    f = w.font()
                    f.setBold(i == idx)
                    f.setPointSizeF(theme.pt(3 if i == idx else 0))
                    w.setFont(f)
                    w.setForeground(QColor(theme.c("teal") if i == idx else theme.c("ink")))
            self.cur_line = idx
            self.lyr.scrollToItem(self.lyr.item(idx), QAbstractItemView.PositionAtCenter)


def _unused():
    return json, QHeaderView, QFileDialog
