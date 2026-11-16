"""Dialogs and extra windows: Settings, Equaliser, Edit Song Info, Smart Playlist, Schedule, Play On TV,
Messages, About, Feedback, Mini Player, Full Screen Visuals, Splash."""
import os
import platform
import time
import urllib.parse
from datetime import datetime

import numpy as np
from PySide6.QtCore import QDate, QPointF, QRectF, QSize, Qt, QTime, QTimer, QUrl, Signal
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QGuiApplication, QLinearGradient, QPainter,
                           QPen, QPixmap)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox, QDateEdit, QDialog,
                               QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QRadioButton, QScrollArea, QSlider, QSpinBox, QTabWidget, QTimeEdit,
                               QToolButton, QVBoxLayout, QWidget)

from .. import app_info, backup, engine, online, recorder, scanner, tags, tools
from ..i18n import lang, tr
from . import theme
from .common import run_bg
from .icons import icon
from .widgets import Cover, cover_pixmap, fmt_time, h1, h2, hint


def scroll_tab(widget):
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.NoFrame)
    sa.setWidget(widget)
    widget.setObjectName("Page")
    return sa


# =========================================================================== Settings
class SettingsDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.db = win.db
        self.setWindowTitle(tr("settings"))
        self.resize(820, 640)
        lay = QVBoxLayout(self)
        self.tabs = QTabWidget()
        lay.addWidget(self.tabs, 1)
        self._general()
        self._library()
        self._playback()
        self._radio()
        self._recording()
        self._online()
        self._data()
        self._links()
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText(tr("close"))
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _page(self, key):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(10)
        self.tabs.addTab(scroll_tab(w), tr(key).replace("&", "&&"))
        return v

    # ---- general
    def _general(self):
        v = self._page("set_general")
        v.addWidget(h2(tr("language")))
        r = QHBoxLayout()
        self.lang_grp = QButtonGroup(self)
        for code, label in (("en", "English"), ("vi", "Tiếng Việt")):
            b = QRadioButton(label)
            b.setChecked(self.db.get("lang") == code)
            b.toggled.connect(lambda on, c=code: on and self.win.set_lang(c))
            self.lang_grp.addButton(b)
            r.addWidget(b)
        r.addStretch()
        v.addLayout(r)
        v.addWidget(h2(tr("look")))
        grid = QGridLayout()
        for i, key in enumerate(theme.ORDER):
            b = QToolButton()
            b.setIcon(QPixmap(theme_preview(key)))
            b.setIconSize(QSize(150, 96))
            b.setText(tr(theme.THEMES[key]["name"]))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setCheckable(True)
            b.setChecked(self.db.get("theme") == key)
            b.setAutoExclusive(True)
            b.clicked.connect(lambda _=False, k=key: self.win.set_theme(k))
            grid.addWidget(b, i // 3, i % 3)
        v.addLayout(grid)
        v.addWidget(h2(tr("text_size")))
        r = QHBoxLayout()
        for i, lab in enumerate(("A", "A+", "A++")):
            b = QPushButton(lab)
            b.clicked.connect(lambda _=False, s=i: self.win.set_font_step(s))
            r.addWidget(b)
        r.addStretch()
        v.addLayout(r)
        v.addWidget(h2(tr("bar_color")))
        self.bar = QComboBox()
        for en, vi, val in theme.BAR_COLORS:
            pm = QPixmap(18, 18)
            pm.fill(QColor(val) if val != "cover" else QColor("#888888"))
            self.bar.addItem(QIcon_from(pm), vi if lang() == "vi" else en, val)
        self.bar.setCurrentIndex(max(0, self.bar.findData(self.db.get("bar_color"))))
        self.bar.currentIndexChanged.connect(lambda *_: self.win.set_bar_color(self.bar.currentData()))
        v.addWidget(self.bar)
        mini = QCheckBox(tr("mini_top"))
        mini.setChecked(bool(self.db.get("mini_on_top")))
        mini.toggled.connect(lambda on: self.db.set("mini_on_top", int(on)))
        v.addWidget(mini)
        v.addStretch()

    # ---- library
    def _library(self):
        v = self._page("set_library")
        v.addWidget(h2(tr("folders_title")))
        self.flist = QListWidget()
        self.flist.setMinimumHeight(160)
        v.addWidget(self.flist)
        r = QHBoxLayout()
        b1 = QPushButton(icon("add", theme.c("on_accent"), 18), tr("add_folder"))
        b1.setObjectName("Primary")
        b1.clicked.connect(lambda: (self.win.add_folder(), self._fill_folders()))
        b2 = QPushButton(icon("refresh", theme.c("ink"), 18), tr("rescan"))
        b2.clicked.connect(self.win.rescan)
        r.addWidget(b1)
        r.addWidget(b2)
        r.addStretch()
        v.addLayout(r)
        v.addWidget(hint(tr("folders_hint")))
        v.addStretch()
        self._fill_folders()

    def _fill_folders(self):
        from .. import volumes
        self.flist.clear()
        for f in self.db.q("SELECT * FROM folders ORDER BY path"):
            on = volumes.online(f["vol_serial"])
            it = QListWidgetItem(icon("folder", theme.c("teal") if on else theme.c("grey"), 18),
                                 f"{scanner.folder_path(f) or f['path']}  ·  {tr('drive_online') if on else tr('drive_offline')}")
            self.flist.addItem(it)

    # ---- playback
    def _playback(self):
        v = self._page("set_playback")
        g = QCheckBox(tr("gapless"))
        g.setChecked(bool(self.db.get("gapless")))
        g.toggled.connect(lambda on: (self.db.set("gapless", int(on)), self.win.player.apply_settings()))
        v.addWidget(g)
        r = QHBoxLayout()
        r.addWidget(QLabel(tr("crossfade")))
        cf = QSpinBox()
        cf.setRange(0, 12)
        cf.setValue(int(self.db.get("crossfade") or 0))
        cf.valueChanged.connect(lambda x: (self.db.set("crossfade", x), self.win.player.apply_settings()))
        r.addWidget(cf)
        r.addStretch()
        v.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel(tr("replaygain")))
        rg = QComboBox()
        for k in ("off", "track", "album"):
            rg.addItem(tr("rg_" + k), k)
        rg.setCurrentIndex(max(0, rg.findData(self.db.get("replaygain"))))
        rg.currentIndexChanged.connect(lambda *_: self.db.set("replaygain", rg.currentData()))
        r.addWidget(rg)
        r.addStretch()
        v.addLayout(r)
        b = QPushButton(icon("eq", theme.c("ink"), 18), tr("eq") + "…")
        b.clicked.connect(self.win.show_eq)
        v.addWidget(b, 0, Qt.AlignLeft)
        v.addWidget(hint(f"{tr('volume')}: {self.win.player.engine.device_name}"))
        v.addStretch()

    # ---- radio & location
    def _radio(self):
        v = self._page("set_radio")
        a = QCheckBox(tr("loc_windows"))
        a.setChecked(bool(self.db.get("location_windows")))
        a.toggled.connect(lambda on: self.db.set("location_windows", int(on)))
        b = QCheckBox(tr("loc_ip"))
        b.setChecked(bool(self.db.get("location_ip")))
        b.toggled.connect(lambda on: self.db.set("location_ip", int(on)))
        v.addWidget(a)
        v.addWidget(b)
        v.addWidget(hint(tr("loc_note")))
        v.addWidget(hint(tr("r_local_note")))
        v.addStretch()

    # ---- recording
    def _recording(self):
        v = self._page("set_rec")
        f = QFormLayout()
        self.rfmt = QComboBox()
        for k, val in recorder.FORMATS.items():
            self.rfmt.addItem(val[1] if lang() == "vi" else val[0], k)
        self.rfmt.setCurrentIndex(max(0, self.rfmt.findData(self.db.get("rec_fmt"))))
        self.rfmt.currentIndexChanged.connect(lambda *_: self.db.set("rec_fmt", self.rfmt.currentData()))
        f.addRow(tr("s_format"), self.rfmt)
        row = QHBoxLayout()
        self.rdir = QLineEdit(self.db.get("rec_dir") or str(app_info.default_recordings_dir()))
        self.rdir.setReadOnly(True)
        bd = QPushButton(tr("choose"))
        bd.clicked.connect(self._pick_rec_dir)
        row.addWidget(self.rdir, 1)
        row.addWidget(bd)
        f.addRow(tr("rec_folder"), row)
        v.addLayout(f)
        sp = QCheckBox(tr("rec_split"))
        sp.setChecked(bool(self.db.get("rec_split")))
        sp.toggled.connect(lambda on: self.db.set("rec_split", int(on)))
        v.addWidget(sp)
        v.addWidget(hint(tr("r_quality_note")))
        v.addWidget(hint(tr("rec_keep_awake")))
        v.addStretch()

    def _pick_rec_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr("rec_folder"), self.rdir.text())
        if d:
            self.db.set("rec_dir", d)
            self.rdir.setText(d)

    # ---- online
    def _online(self):
        v = self._page("set_online")
        a = QCheckBox(tr("online_lyrics"))
        a.setChecked(bool(self.db.get("lyrics_online")))
        a.toggled.connect(lambda on: self.db.set("lyrics_online", int(on)))
        b = QCheckBox(tr("online_mb"))
        b.setChecked(bool(self.db.get("musicbrainz")))
        b.toggled.connect(lambda on: self.db.set("musicbrainz", int(on)))
        v.addWidget(a)
        v.addWidget(b)
        v.addWidget(hint(tr("online_note")))
        v.addStretch()

    # ---- data
    def _data(self):
        v = self._page("set_data")
        r = QHBoxLayout()
        b1 = QPushButton(icon("download", theme.c("on_accent"), 18), tr("backup_now"))
        b1.setObjectName("Primary")
        b1.clicked.connect(self._backup)
        b2 = QPushButton(tr("restore"))
        b2.clicked.connect(self._restore)
        r.addWidget(b1)
        r.addWidget(b2)
        r.addStretch()
        v.addLayout(r)
        last = self.db.get("last_backup") or 0
        self.l_last = QLabel(tr("backup_last", d=datetime.fromtimestamp(last).strftime("%d/%m/%Y %H:%M") if last else tr("never")))
        v.addWidget(self.l_last)
        v.addWidget(hint(tr("backup_auto")))
        row = QHBoxLayout()
        self.bdir = QLineEdit(str(backup.default_dir(self.db)))
        self.bdir.setReadOnly(True)
        bd = QPushButton(tr("choose"))
        bd.clicked.connect(self._pick_bdir)
        row.addWidget(QLabel(tr("backup_dir")))
        row.addWidget(self.bdir, 1)
        row.addWidget(bd)
        v.addLayout(row)
        v.addSpacing(10)
        v.addWidget(QLabel(f"{tr('data_place')}: {app_info.data_dir()}"))
        v.addStretch()

    def _backup(self):
        try:
            p = backup.make(self.db)
            self.l_last.setText(tr("backup_last", d=datetime.now().strftime("%d/%m/%Y %H:%M")))
            QMessageBox.information(self, tr("backup_now"), tr("backup_done", p=str(p)))
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))

    def _restore(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("restore"), str(backup.default_dir(self.db)), "Zip (*.zip)")
        if not p or QMessageBox.question(self, tr("restore"), tr("restore_q")) != QMessageBox.Yes:
            return
        try:
            self.win.player.close()
            backup.restore(self.db, p)
            self.win.restart()
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))

    def _pick_bdir(self):
        d = QFileDialog.getExistingDirectory(self, tr("backup_dir"), self.bdir.text())
        if d:
            self.db.set("backup_dir", d)
            self.bdir.setText(d)

    # ---- links
    def _links(self):
        v = self._page("set_links")
        v.addWidget(h2(tr("disc_path")))
        row = QHBoxLayout()
        self.disc = QLineEdit(self.win.find_toms_disc() or "")
        self.disc.setReadOnly(True)
        b = QPushButton(tr("choose"))
        b.clicked.connect(self._pick_disc)
        row.addWidget(self.disc, 1)
        row.addWidget(b)
        v.addLayout(row)
        v.addWidget(h2(tr("reel_status")))
        reel = self.win.reel
        self.l_reel = QLabel(tr("reel_found", n=reel.count) if reel and reel.source else tr("reel_missing"))
        v.addWidget(self.l_reel)
        b2 = QPushButton(tr("reel_pick"))
        b2.clicked.connect(self._pick_reel)
        v.addWidget(b2, 0, Qt.AlignLeft)
        v.addWidget(h2("Tom's Dock"))
        dock_dir = app_info.shared_send_dir() / "Tom's Dock" / "Playlists"
        lab = QLabel(f"{tr('dock_folder')}: {dock_dir}")
        lab.setWordWrap(True)
        v.addWidget(lab)
        v.addWidget(hint(tr("pl_dock_note")))
        v.addStretch()

    def _pick_disc(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("disc_path"), "", "TomsDisc.exe (TomsDisc.exe *.exe)")
        if p:
            self.db.set("toms_disc_path", p)
            self.disc.setText(p)

    def _pick_reel(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("reel_pick"), "", "Database (*.db *.sqlite)")
        if p:
            self.db.set("reel_db", p)
            self.win.reel = tools.ReelLink(p)
            self.l_reel.setText(tr("reel_found", n=self.win.reel.count) if self.win.reel.source else tr("reel_missing"))


def QIcon_from(pm):
    from PySide6.QtGui import QIcon
    return QIcon(pm)


def theme_preview(key):
    t = theme.THEMES[key]

    def col(v, fallback="#FFFFFF"):
        if v.startswith("rgba"):
            n = [float(x) for x in v[5:-1].split(",")]
            return QColor(int(n[0]), int(n[1]), int(n[2]), int(n[3] * 255))
        return QColor(v)
    pm = QPixmap(300, 192)
    pm.fill(col(t["bg"]))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(0, 0, 300, 36, col(t["top"]))
    p.setPen(QColor(theme.SKY))
    p.setFont(QFont("Bahnschrift", 11, QFont.Bold))
    p.drawText(12, 24, "TOM'S")
    p.setPen(QColor(theme.ORANGE))
    p.drawText(64, 24, "JUKEBOX")
    p.fillRect(0, 36, 70, 156, col(t["nav"]))
    r = t["radius"]
    for i in range(3):
        p.setBrush(col(t["card"]))
        p.setPen(QPen(col(t["line"]), 1))
        p.drawRoundedRect(QRectF(84 + i * 70, 48, 60, 60), r * 0.6, r * 0.6)
    p.setBrush(col(t["player"]))
    p.drawRoundedRect(QRectF(80, 136, 210, 40), 20, 20)
    p.setBrush(QColor(theme.ORANGE))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(150, 154, 100, 5), 2.5, 2.5)
    p.end()
    return pm


# =========================================================================== Equaliser
class EQDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win, self.db = win, win.db
        self.setWindowTitle(tr("eq"))
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.on = QCheckBox(tr("eq_on"))
        self.on.setChecked(bool(self.db.get("eq_on")))
        self.on.toggled.connect(self._apply)
        top.addWidget(self.on)
        top.addStretch()
        top.addWidget(QLabel(tr("eq_preset")))
        self.preset = QComboBox()
        for k in engine.EQ_PRESETS:
            self.preset.addItem(tr("eq_" + k), k)
        self.preset.addItem(tr("eq_custom"), "custom")
        self.preset.setCurrentIndex(max(0, self.preset.findData(self.db.get("eq_preset"))))
        self.preset.activated.connect(self._preset)
        top.addWidget(self.preset)
        lay.addLayout(top)
        grid = QHBoxLayout()
        self.sliders = []
        gains = self.db.get("eq_gains")
        for i, f in enumerate(engine.EQ_FREQS):
            col = QVBoxLayout()
            val = QLabel(f"{gains[i]:+.0f}")
            val.setAlignment(Qt.AlignCenter)
            s = QSlider(Qt.Vertical)
            s.setRange(-12, 12)
            s.setValue(int(round(gains[i])))
            s.setMinimumHeight(200)
            s.valueChanged.connect(lambda x, lab=val: (lab.setText(f"{x:+d}"), self._custom()))
            name = QLabel(f"{f // 1000}k" if f >= 1000 else str(f))
            name.setAlignment(Qt.AlignCenter)
            col.addWidget(val)
            col.addWidget(s, 1, Qt.AlignHCenter)
            col.addWidget(name)
            grid.addLayout(col)
            self.sliders.append(s)
        lay.addLayout(grid)
        from ..art.themes import t as _t
        self.auto_g = QCheckBox(_t("Choose The Sound By Genre On Its Own (radio and podcasts: Clear Voice)",
                                   "Tự Chọn Kiểu Âm Thanh Theo Thể Loại (radio và podcast: Rõ Giọng Nói)"))
        self.auto_g.setChecked(bool(self.db.get("eq_auto_genre")))
        self.auto_g.toggled.connect(lambda on: self.db.set("eq_auto_genre", int(on)))
        lay.addWidget(self.auto_g)
        bb = QHBoxLayout()
        r = QPushButton(tr("reset"))
        r.clicked.connect(lambda: self._set_gains([0] * 10, "flat"))
        c = QPushButton(tr("close"))
        c.clicked.connect(self.accept)
        bb.addWidget(r)
        bb.addStretch()
        bb.addWidget(c)
        lay.addLayout(bb)
        self._busy = False

    def _set_gains(self, gains, preset):
        self._busy = True
        for s, g in zip(self.sliders, gains):
            s.setValue(int(g))
        self._busy = False
        self.preset.setCurrentIndex(max(0, self.preset.findData(preset)))
        self.db.set("eq_preset", preset)
        self._apply()

    def _preset(self, _i):
        k = self.preset.currentData()
        if k in engine.EQ_PRESETS:
            if not self.on.isChecked():
                self.on.setChecked(True)
            self._set_gains(engine.EQ_PRESETS[k], k)

    def _custom(self):
        if self._busy:
            return
        self.preset.setCurrentIndex(self.preset.findData("custom"))
        self.db.set("eq_preset", "custom")
        self._apply()

    def _apply(self):
        gains = [float(s.value()) for s in self.sliders]
        self.db.set("eq_gains", gains)
        self.db.set("eq_on", int(self.on.isChecked()))
        self.win.player.engine.set_eq(self.on.isChecked(), gains)


# =========================================================================== Edit song info
FIELDS = [("title", "col_title"), ("artist", "col_artist"), ("album", "col_album"), ("albumartist", "te_albumartist"),
          ("genre", "col_genre"), ("year", "col_year"), ("track_no", "te_track"), ("disc_no", "te_disc")]


class TagEditor(QDialog):
    def __init__(self, win, rows, online_first=False):
        super().__init__(win)
        self.win, self.db, self.rows = win, win.db, rows
        self.setWindowTitle(tr("te_title"))
        self.resize(820, 560)
        self.new_cover = None
        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        self.cover = Cover(200, 16)
        self.cover.set_key(rows[0]["art_key"], rows[0]["title"] or "")
        left.addWidget(self.cover)
        bc = QPushButton(tr("te_change_cover"))
        bc.clicked.connect(self._pick_cover)
        left.addWidget(bc)
        left.addStretch()
        lay.addLayout(left)
        mid = QVBoxLayout()
        if len(rows) > 1:
            mid.addWidget(hint(tr("te_multi", n=len(rows))))
        form = QFormLayout()
        self.edits = {}
        for key, lab in FIELDS:
            e = QLineEdit()
            if len(rows) == 1:
                v = rows[0][key]
                e.setText("" if v is None else str(v))
            else:
                vals = {r[key] for r in rows}
                if len(vals) == 1:
                    v = vals.pop()
                    e.setText("" if v is None else str(v))
                else:
                    e.setPlaceholderText("…")
            self.edits[key] = e
            form.addRow(tr(lab), e)
        mid.addLayout(form)
        self.files = hint("\n".join((scanner.track_path(r) or r["path"]) for r in rows[:4]) + ("\n…" if len(rows) > 4 else ""))
        mid.addWidget(self.files)
        mid.addStretch()
        bb = QHBoxLayout()
        bs = QPushButton(tr("save"))
        bs.setObjectName("Primary")
        bs.clicked.connect(self.save)
        bx = QPushButton(tr("cancel"))
        bx.clicked.connect(self.reject)
        bb.addStretch()
        bb.addWidget(bx)
        bb.addWidget(bs)
        mid.addLayout(bb)
        lay.addLayout(mid, 2)
        right = QVBoxLayout()
        bsearch = QPushButton(icon("web", theme.c("ink"), 18), tr("te_search"))
        bsearch.clicked.connect(self.search)
        right.addWidget(bsearch)
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.use)
        right.addWidget(self.results, 1)
        buse = QPushButton(tr("te_use"))
        buse.clicked.connect(lambda: self.use(self.results.currentItem()))
        right.addWidget(buse)
        lay.addLayout(right, 2)
        if online_first:
            QTimer.singleShot(200, self.search)

    def _pick_cover(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("te_change_cover"), "", "Images (*.jpg *.jpeg *.png)")
        if p:
            with open(p, "rb") as fh:
                self.new_cover = fh.read()
            key = "edit_" + str(int(time.time()))
            tags.save_thumbs(key, self.new_cover)
            self.cover.set_key(key)

    def search(self):
        self.results.clear()
        self.results.addItem(tr("working"))
        r = self.rows[0]
        run_bg(online.mb_search, self.edits["artist"].text() or r["artist"], self.edits["title"].text() or r["title"],
               done=self._found)

    def _found(self, res):
        self.results.clear()
        for c in res:
            it = QListWidgetItem(f"{c['title']} — {c['artist']}\n{c['album']} ({c['year']})")
            it.setData(Qt.UserRole, c)
            self.results.addItem(it)
        if not res:
            self.results.addItem(tr("r_offline"))

    def use(self, it):
        if not it or not it.data(Qt.UserRole):
            return
        c = it.data(Qt.UserRole)
        single = len(self.rows) == 1
        for k in ("artist", "album", "year"):
            if c.get(k):
                self.edits[k].setText(str(c[k]))
        if single:
            if c.get("title"):
                self.edits["title"].setText(c["title"])
            if c.get("track_no"):
                self.edits["track_no"].setText(str(c["track_no"]))
        if c.get("release_id"):
            run_bg(online.cover_art, c["release_id"], 500, done=self._got_cover)

    def _got_cover(self, data):
        if data:
            self.new_cover = data
            key = "edit_" + str(int(time.time()))
            tags.save_thumbs(key, data)
            self.cover.set_key(key)

    def save(self):
        vals = {}
        for key, e in self.edits.items():
            t = e.text().strip()
            if len(self.rows) > 1 and not t:
                continue
            vals[key] = t
        ok = 0
        errors = []
        for r in self.rows:
            p = scanner.track_path(r)
            if not p:
                errors.append(tr("te_failed", f=r["title"], e=tr("offline_track")))
                continue
            try:
                tags.write(p, vals, self.new_cover)
                ok += 1
            except Exception as e:
                errors.append(tr("te_failed", f=os.path.basename(p), e=e))
        # refresh records from the files
        fids = {r["folder_id"] for r in self.rows if r["folder_id"]}
        for r in self.rows:
            p = scanner.track_path(r)
            if p and os.path.exists(p):
                info = tags.read(p)
                key = tags.art_key_for(info["albumartist"] or info["artist"], info["album"], p)
                if self.new_cover:
                    tags.save_thumbs(key, self.new_cover)
                elif not tags.art_path(key, True):
                    data = tags.cover_bytes(p)
                    key = key if data and tags.save_thumbs(key, data) else r["art_key"]
                st = os.stat(p)
                self.db.x("""UPDATE tracks SET title=?, artist=?, album=?, albumartist=?, genre=?, year=?, track_no=?, disc_no=?,
                             art_key=?, mtime=?, size=? WHERE id=?""",
                          (info["title"], info["artist"], info["album"], info["albumartist"], info["genre"], info["year"],
                           info["track_no"], info["disc_no"], key, st.st_mtime, st.st_size, r["id"]))
        _ = fids
        msg = tr("te_saved", n=ok) + ("\n\n" + "\n".join(errors[:6]) if errors else "")
        QMessageBox.information(self, tr("te_title"), msg)
        self.accept()


# =========================================================================== Smart playlist
class SmartDialog(QDialog):
    FIELDS = ["artist", "album", "genre", "title", "year", "codec", "plays", "fav", "added_days", "played_days", "duration", "folder"]
    OPS = ["contains", "not_contains", "=", "!=", ">", "<", "within", "older", "is_empty"]
    ORDERS = ["artist", "plays", "recent", "random", "last_played", "title"]

    def __init__(self, parent, existing):
        super().__init__(parent)
        self.setWindowTitle(tr("pl_new_smart"))
        self.resize(720, 460)
        lay = QVBoxLayout(self)
        top = QFormLayout()
        self.name = QLineEdit(existing[0] if existing else "")
        top.addRow(tr("pl_name"), self.name)
        self.tpl = QComboBox()
        self.tpl.addItem("—", None)
        for en, vi, rules in tools.SMART_TEMPLATES:
            self.tpl.addItem(vi if lang() == "vi" else en, (vi if lang() == "vi" else en, rules))
        self.tpl.activated.connect(self._template)
        top.addRow(tr("sp_template"), self.tpl)
        self.match = QComboBox()
        self.match.addItem(tr("sp_match_all"), "all")
        self.match.addItem(tr("sp_match_any"), "any")
        top.addRow("", self.match)
        lay.addLayout(top)
        self.rules_box = QVBoxLayout()
        lay.addLayout(self.rules_box)
        add = QPushButton(icon("add", theme.c("ink"), 16), tr("sp_add_rule"))
        add.clicked.connect(lambda: self._add_rule())
        lay.addWidget(add, 0, Qt.AlignLeft)
        bottom = QFormLayout()
        self.order = QComboBox()
        for o in self.ORDERS:
            self.order.addItem(tr("o_" + o), o)
        self.limit = QSpinBox()
        self.limit.setRange(0, 5000)
        bottom.addRow(tr("sp_order"), self.order)
        bottom.addRow(tr("sp_limit"), self.limit)
        lay.addLayout(bottom)
        lay.addStretch()
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("save"))
        bb.button(QDialogButtonBox.Cancel).setText(tr("cancel"))
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.rows = []
        if existing:
            self._load(existing[1])
        else:
            self._add_rule()

    def _load(self, rules):
        for w in self.rows:
            w[0].hide()
            w[0].deleteLater()
        self.rows = []
        self.match.setCurrentIndex(0 if rules.get("match", "all") == "all" else 1)
        for r in rules.get("rules", []):
            self._add_rule(r)
        self.order.setCurrentIndex(max(0, self.order.findData(rules.get("order", "artist"))))
        self.limit.setValue(int(rules.get("limit") or 0))

    def _template(self, _i):
        d = self.tpl.currentData()
        if d:
            if not self.name.text():
                self.name.setText(d[0])
            self._load(d[1])

    def _add_rule(self, r=None):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        f = QComboBox()
        for k in self.FIELDS:
            f.addItem(tr("f_" + k), k)
        o = QComboBox()
        for k in self.OPS:
            o.addItem(tr("op_" + k) if k.isalpha() or "_" in k else k, k)
        v = QLineEdit()
        x = QToolButton()
        x.setIcon(icon("close", theme.c("muted"), 14))
        x.clicked.connect(lambda: (w.hide(), self.rows.remove(row)))
        for wid in (f, o):
            h.addWidget(wid)
        h.addWidget(v, 1)
        h.addWidget(x)
        if r:
            f.setCurrentIndex(max(0, f.findData(r.get("field"))))
            o.setCurrentIndex(max(0, o.findData(r.get("op"))))
            v.setText(str(r.get("value", "")))
        row = (w, f, o, v)
        self.rows.append(row)
        self.rules_box.addWidget(w)

    def _ok(self):
        if not self.name.text().strip():
            self.name.setFocus()
            return
        self.accept()

    def result_value(self):
        rules = {"match": self.match.currentData(), "order": self.order.currentData(), "limit": self.limit.value(),
                 "rules": [{"field": f.currentData(), "op": o.currentData(), "value": v.text()} for _w, f, o, v in self.rows]}
        return self.name.text().strip(), rules


# =========================================================================== Schedule
class ScheduleDialog(QDialog):
    def __init__(self, parent, db, sched_id, station_id):
        super().__init__(parent)
        self.db, self.sid = db, sched_id
        self.setWindowTitle(tr("r_schedule"))
        s = db.one("SELECT * FROM schedules WHERE id=?", (sched_id,)) if sched_id else None
        lay = QVBoxLayout(self)
        f = QFormLayout()
        self.station = QComboBox()
        for st in db.q("SELECT id, name FROM stations ORDER BY fav DESC, name COLLATE NOCASE"):
            self.station.addItem(st["name"], st["id"])
        want = s["station_id"] if s else station_id
        if want:
            self.station.setCurrentIndex(max(0, self.station.findData(want)))
        f.addRow(tr("s_station"), self.station)
        self.start = QTimeEdit()
        self.start.setDisplayFormat("HH:mm")
        self.start.setTime(QTime.fromString(s["start_hm"], "HH:mm") if s else QTime(19, 0))
        f.addRow(tr("s_start"), self.start)
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 600)
        self.minutes.setValue(s["minutes"] if s else 60)
        f.addRow(tr("s_minutes"), self.minutes)
        dl = QHBoxLayout()
        self.days = []
        chosen = [int(d) for d in (s["days"] or "").split(",") if d.strip().isdigit()] if s else []
        for i, d in enumerate(tr("days_short").split(",")):
            c = QCheckBox(d)
            c.setChecked(i in chosen)
            dl.addWidget(c)
            self.days.append(c)
        f.addRow(tr("s_days"), dl)
        ol = QHBoxLayout()
        self.once = QCheckBox()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.date.setDate(QDate.fromString(s["once_date"], "yyyy-MM-dd") if s and s["once_date"] else QDate.currentDate())
        self.once.setChecked(bool(s and s["once_date"]))
        ol.addWidget(self.once)
        ol.addWidget(self.date)
        ol.addStretch()
        f.addRow(tr("s_once"), ol)
        self.fmt = QComboBox()
        for k, v in recorder.FORMATS.items():
            self.fmt.addItem(v[1] if lang() == "vi" else v[0], k)
        self.fmt.setCurrentIndex(max(0, self.fmt.findData(s["fmt"] if s else db.get("rec_fmt"))))
        f.addRow(tr("s_format"), self.fmt)
        self.enabled = QCheckBox()
        self.enabled.setChecked(bool(s["enabled"]) if s else True)
        f.addRow(tr("s_enabled"), self.enabled)
        lay.addLayout(f)
        lay.addWidget(hint(tr("rec_keep_awake")))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("save"))
        bb.button(QDialogButtonBox.Cancel).setText(tr("cancel"))
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def save(self):
        if self.station.currentData() is None:
            return
        days = ",".join(str(i) for i, c in enumerate(self.days) if c.isChecked())
        once = self.date.date().toString("yyyy-MM-dd") if self.once.isChecked() else None
        vals = (self.station.currentData(), self.start.time().toString("HH:mm"), self.minutes.value(), days, once,
                self.fmt.currentData(), int(self.enabled.isChecked()))
        if self.sid:
            self.db.x("UPDATE schedules SET station_id=?, start_hm=?, minutes=?, days=?, once_date=?, fmt=?, enabled=? WHERE id=?", vals + (self.sid,))
        else:
            self.db.x("INSERT INTO schedules(station_id,start_hm,minutes,days,once_date,fmt,enabled) VALUES(?,?,?,?,?,?,?)", vals)
        self.accept()


# =========================================================================== Play on TV
class CastDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle(tr("c_title"))
        self.resize(520, 420)
        lay = QVBoxLayout(self)
        lay.addWidget(hint(tr("c_note")))
        self.status = QLabel(tr("c_searching"))
        lay.addWidget(self.status)
        self.list = QListWidget()
        self.list.setIconSize(QSize(28, 28))
        self.list.itemDoubleClicked.connect(self.pick)
        lay.addWidget(self.list, 1)
        r = QHBoxLayout()
        here = QPushButton(icon("volume", theme.c("ink"), 18), tr("c_play_here"))
        here.clicked.connect(lambda: (win.player.set_cast(None), self.accept()))
        again = QPushButton(icon("refresh", theme.c("ink"), 18), tr("c_search"))
        again.clicked.connect(self.search)
        r.addWidget(here)
        r.addStretch()
        r.addWidget(again)
        lay.addLayout(r)
        self.found = []
        self.search()

    def search(self):
        from .. import dlna
        self.list.clear()
        self.status.setText(tr("c_searching"))
        run_bg(dlna.discover, 3.0, done=self._done, failed=lambda e: self._done([]))

    def _done(self, rens):
        self.found = rens
        self.list.clear()
        for r in rens:
            it = QListWidgetItem(icon("cast", theme.c("teal"), 28), f"{r.name}\n{r.host}")
            self.list.addItem(it)
        self.status.setText("" if rens else tr("c_none"))

    def pick(self, it):
        i = self.list.row(it)
        if 0 <= i < len(self.found):
            self.win.player.set_cast(self.found[i])
            self.win.toast(tr("c_playing_on", d=self.found[i].name))
            self.accept()


# =========================================================================== Messages
class MessagesDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.db = win.db
        self.setWindowTitle(tr("messages"))
        self.resize(560, 420)
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.setWordWrap(True)
        lay.addWidget(self.list, 1)
        for m in self.db.q("SELECT * FROM messages ORDER BY at DESC LIMIT 200"):
            when = datetime.fromtimestamp(m["at"]).strftime("%d/%m/%Y %H:%M")
            it = QListWidgetItem(icon("bell", theme.c("accent") if not m["read"] else theme.c("grey"), 20),
                                 f"{when}\n{m['text_vi'] if lang() == 'vi' else m['text_en']}")
            self.list.addItem(it)
        if not self.list.count():
            self.list.addItem(tr("msg_none"))
        r = QHBoxLayout()
        b = QPushButton(tr("mark_read"))
        b.clicked.connect(lambda: (self.db.x("UPDATE messages SET read=1"), win.update_status(), self.accept()))
        c = QPushButton(tr("close"))
        c.clicked.connect(self.accept)
        r.addWidget(b)
        r.addStretch()
        r.addWidget(c)
        lay.addLayout(r)


# =========================================================================== About
class OneOfLabel(QLabel):
    """'One of Tom's Technology Solutions Products' in the approved two colours on navy."""

    def __init__(self, size_pt=None):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setTextFormat(Qt.RichText)
        sz = size_pt or theme.pt(1)
        self.setText(f'<span style="color:#CFE6EE; font-size:{sz}pt">One of </span>'
                     f'<span style="color:#FBB040; font-size:{sz}pt; font-weight:700">Tom\'s Technology Solutions</span>'
                     f'<span style="color:#CFE6EE; font-size:{sz}pt"> Products</span>')


class AboutDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.setWindowTitle(tr("about"))
        self.setMinimumWidth(640)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 12)
        band = QFrame()
        band.setStyleSheet(f"background: {theme.NAVY};")
        bl = QVBoxLayout(band)
        bl.setContentsMargins(20, 22, 20, 18)
        logo = QLabel()
        dpr = self.devicePixelRatioF()
        pm = QPixmap(app_info.asset("app_icon_1024.png")).scaled(int(110 * dpr), int(110 * dpr), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pm.setDevicePixelRatio(dpr)
        logo.setPixmap(pm)
        logo.setAlignment(Qt.AlignCenter)
        bl.addWidget(logo)
        name = QLabel()
        name.setTextFormat(Qt.RichText)
        name.setAlignment(Qt.AlignCenter)
        name.setText(f'<span style="font-family:Bahnschrift,Segoe UI; font-size:{theme.pt(12)}pt; font-weight:700; color:{theme.SKY}">TOM\'S </span>'
                     f'<span style="font-family:Bahnschrift,Segoe UI; font-size:{theme.pt(12)}pt; font-weight:700; color:{theme.ORANGE}">JUKEBOX</span>')
        bl.addWidget(name)
        slog = QLabel(app_info.SLOGAN)
        slog.setAlignment(Qt.AlignCenter)
        slog.setStyleSheet("color:#CFE6EE;")
        bl.addWidget(slog)
        ver = QLabel(f"{tr('version')} {app_info.VERSION}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color:#9FC3D3;")
        bl.addWidget(ver)
        bl.addWidget(OneOfLabel())
        lay.addWidget(band)
        body = QVBoxLayout()
        body.setContentsMargins(26, 14, 26, 0)
        desc = QLabel(tr("about_desc"))
        desc.setAlignment(Qt.AlignCenter)
        body.addWidget(desc)
        grid = QFormLayout()
        grid.addRow(QLabel(f"<b>{tr('idea')}:</b>"), QLabel(app_info.BRAND))
        grid.addRow(QLabel(f"<b>{tr('built_by')}:</b>"), QLabel("Claude (Anthropic)"))
        gw = QHBoxLayout()
        gw.addStretch()
        gw.addLayout(grid)
        gw.addStretch()
        body.addLayout(gw)
        for k in ("credits", "credits2", "trademarks"):
            lab = hint(tr(k))
            lab.setAlignment(Qt.AlignCenter)
            body.addWidget(lab)
        lay.addLayout(body)
        c = QPushButton(tr("close"))
        c.clicked.connect(self.accept)
        lay.addWidget(c, 0, Qt.AlignCenter)


def send_feedback(win):
    t = theme.THEMES[win.db.get("theme")]["name"]
    subject = f"{'Góp Ý' if lang() == 'vi' else 'Feedback'} {app_info.APP_NAME} {app_info.VERSION}"
    body = (f"\n\n---\n{app_info.APP_NAME} {app_info.VERSION}\nWindows: {platform.platform()}\n"
            f"Look: {tr(t)}\nText size: {['A', 'A+', 'A++'][int(win.db.get('font_step') or 0)]}\nLanguage: {lang()}\n")
    url = f"mailto:{app_info.FEEDBACK_EMAIL}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    if not QDesktopServices.openUrl(QUrl(url)):
        d = QDialog(win)
        d.setWindowTitle(tr("feedback"))
        v = QVBoxLayout(d)
        v.addWidget(QLabel(tr("fb_fallback")))
        e = QLineEdit(app_info.FEEDBACK_EMAIL)
        e.setReadOnly(True)
        v.addWidget(e)
        b = QPushButton(tr("copy_addr"))
        b.clicked.connect(lambda: (QGuiApplication.clipboard().setText(app_info.FEEDBACK_EMAIL), b.setText(tr("copied"))))
        v.addWidget(b)
        d.exec()


# =========================================================================== Mini player
class MiniPlayer(QWidget):
    def __init__(self, win):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | (Qt.WindowStaysOnTopHint if win.db.get("mini_on_top") else Qt.Widget))
        self.win = win
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(tr("mini"))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame()
        self.frame.setObjectName("Pill")
        lay.addWidget(self.frame)
        h = QHBoxLayout(self.frame)
        h.setContentsMargins(10, 6, 12, 6)
        from .widgets import SpinningDisc, tool
        self.disc = SpinningDisc(46)
        self.disc.clicked.connect(self._back)
        h.addWidget(self.disc)
        col = QVBoxLayout()
        self.t = QLabel("")
        self.t.setFixedWidth(170)
        self.s = QLabel("")
        self.s.setObjectName("PillSub")
        self.s.setFixedWidth(170)
        col.addWidget(self.t)
        col.addWidget(self.s)
        h.addLayout(col)
        self.b_prev = tool("prev", tr("prev"))
        self.b_play = tool("play", tr("play"), theme.c("player"), 22)
        self.b_play.setObjectName("PlayBtn")
        self.b_play.setFixedSize(40, 40)
        self.b_next = tool("next", tr("next"))
        self.b_close = tool("close", tr("close"), size=16)
        for b in (self.b_prev, self.b_play, self.b_next, self.b_close):
            h.addWidget(b)
        p = win.player
        self.b_prev.clicked.connect(p.prev)
        self.b_next.clicked.connect(p.next)
        self.b_play.clicked.connect(p.toggle)
        self.b_close.clicked.connect(self._back)
        p.changed.connect(self.on_changed)
        p.state.connect(self.on_state)
        p.radio_title.connect(self.s.setText)
        self.on_changed(p.current)
        self.on_state(p.is_playing())
        self._drag = None
        self.resize(470, 72)

    def _back(self):
        self.hide()
        self.win.showNormal()
        self.win.activateWindow()

    def on_changed(self, it):
        if it is None:
            self.t.setText(tr("nothing_playing"))
            self.s.setText("")
            return
        fm = self.t.fontMetrics()
        self.t.setText(fm.elidedText(it.title, Qt.ElideRight, 165))
        self.s.setText(it.get("artist") or "")
        self.disc.set_key(it.get("art_key"), it.title)

    def on_state(self, on):
        self.b_play.setIcon(icon("pause" if on else "play", theme.c("player"), 22))
        self.disc.set_playing(on)

    def mousePressEvent(self, e):
        self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None


# =========================================================================== Full screen visuals
class Visualizer(QWidget):
    def __init__(self, win):
        super().__init__(None)
        self.win = win
        self.setWindowTitle(tr("visual"))
        self.levels = np.zeros(64)
        self.peaks = np.zeros(64)
        self.t0 = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)
        self.setCursor(Qt.BlankCursor)
        self.setMouseTracking(True)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_F11):
            self.close()
        elif e.key() == Qt.Key_Space:
            self.win.player.toggle()
        elif e.key() == Qt.Key_Right:
            self.win.player.next()
        elif e.key() == Qt.Key_Left:
            self.win.player.prev()

    def mouseDoubleClickEvent(self, e):
        self.close()

    def closeEvent(self, e):
        self.timer.stop()
        super().closeEvent(e)

    def _tick(self):
        p = self.win.player
        lv = p.engine.levels(64) if p.is_playing() and p.cast is None else np.zeros(64)
        self.levels = self.levels * 0.6 + lv * 0.4
        self.peaks = np.maximum(self.peaks - 0.01, self.levels)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        it = self.win.player.current or {}
        from .widgets import dominant_color, readable_on_dark
        col = readable_on_dark(dominant_color(it.get("art_key")))
        g = QLinearGradient(0, 0, 0, h)
        dark = QColor(col).darker(520)
        g.setColorAt(0, dark)
        g.setColorAt(1, QColor("#05080B"))
        p.fillRect(self.rect(), QBrush(g))
        cs = int(min(w, h) * 0.42)
        pm = cover_pixmap(it.get("art_key"), cs, 28, it.get("title") or "", self.devicePixelRatioF())
        p.drawPixmap(int(w / 2 - cs / 2), int(h * 0.12), pm)
        f = QFont("Segoe UI", max(14, int(h / 32)), QFont.Bold)
        p.setFont(f)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(0, h * 0.12 + cs + 18, w, h / 16), Qt.AlignCenter, it.get("title") or tr("nothing_playing"))
        f.setBold(False)
        f.setPointSize(max(11, int(h / 48)))
        p.setFont(f)
        p.setPen(QColor("#CFE6EE"))
        p.drawText(QRectF(0, h * 0.12 + cs + 18 + h / 16, w, h / 20), Qt.AlignCenter, it.get("now_title") or it.get("artist") or "")
        n = len(self.levels)
        base = h * 0.95
        maxh = h * 0.22
        bw = w / n
        for i in range(n):
            v = self.levels[i]
            bh = max(3, v * maxh)
            c = QColor(col)
            c.setAlphaF(0.55 + 0.45 * v)
            p.setBrush(c)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(i * bw + bw * 0.18, base - bh, bw * 0.64, bh), 3, 3)
            p.setBrush(QColor(255, 255, 255, 180))
            p.drawRoundedRect(QRectF(i * bw + bw * 0.18, base - self.peaks[i] * maxh - 6, bw * 0.64, 3), 1.5, 1.5)


# =========================================================================== Splash
def splash_pixmap(dpr=1.0, logo_on=True):
    W, H = 640, 400
    pm = QPixmap(int(W * dpr), int(H * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(QColor(theme.NAVY))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    g = QLinearGradient(0, 0, 0, H)
    g.setColorAt(0, QColor(theme.NAVY))
    g.setColorAt(1, QColor(theme.NAVY_D))
    p.fillRect(QRectF(0, 0, W, H), QBrush(g))
    logo = QPixmap(app_info.asset("app_icon_1024.png"))
    if logo_on:
        p.drawPixmap(QRectF(W / 2 - 70, 34, 140, 140), logo, QRectF(0, 0, logo.width(), logo.height()))
    f = QFont("Bahnschrift", 30, QFont.Bold)
    p.setFont(f)
    fm = p.fontMetrics()
    a, b = "TOM'S ", "JUKEBOX"
    total = fm.horizontalAdvance(a) + fm.horizontalAdvance(b)
    x = (W - total) / 2
    p.setPen(QColor(theme.SKY))
    p.drawText(QPointF(x, 222), a)
    p.setPen(QColor(theme.ORANGE))
    p.drawText(QPointF(x + fm.horizontalAdvance(a), 222), b)
    p.setFont(QFont("Segoe UI", 11))
    p.setPen(QColor("#CFE6EE"))
    p.drawText(QRectF(0, 234, W, 24), Qt.AlignCenter, app_info.SLOGAN)
    p.setFont(QFont("Segoe UI", 10))
    p.setPen(QColor("#9FC3D3"))
    p.drawText(QRectF(20, 272, W - 40, 40), Qt.AlignCenter | Qt.TextWordWrap, tr("app_line"))
    f2 = QFont("Segoe UI", 11)
    p.setFont(f2)
    fm2 = p.fontMetrics()
    parts = [("One of ", "#CFE6EE", False), ("Tom's Technology Solutions", "#FBB040", True), (" Products", "#CFE6EE", False)]
    widths = []
    for txt, _c, bold in parts:
        f2.setBold(bold)
        p.setFont(f2)
        widths.append(p.fontMetrics().horizontalAdvance(txt))
    x = (W - sum(widths)) / 2
    for (txt, c, bold), wdt in zip(parts, widths):
        f2.setBold(bold)
        p.setFont(f2)
        p.setPen(QColor(c))
        p.drawText(QPointF(x, 352), txt)
        x += wdt
    _ = fm2
    p.setFont(QFont("Segoe UI", 9))
    p.setPen(QColor("#6F93A5"))
    p.drawText(QRectF(0, 372, W - 16, 20), Qt.AlignRight, f"{tr('version')} {app_info.VERSION}")
    p.end()
    return pm


def _unused():
    return QApplication, QDoubleSpinBox, Signal, fmt_time, h1
