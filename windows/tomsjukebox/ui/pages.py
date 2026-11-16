"""Library pages: Songs, Favourites, Albums, Artists, Genres, Folders, Playlists, Statistics."""
import json
import os
import time

from PySide6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt
from PySide6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListView,
                               QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter, QStackedWidget,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import scanner, tools, volumes
from ..i18n import tr
from . import theme
from .common import TrackTable
from .icons import icon
from .widgets import Cover, cover_pixmap, fmt_time, h1, h2, hint


def display_name(name):
    """Built-in smart playlist names follow the language on screen; names Tom typed stay as written."""
    from ..i18n import lang
    for en, vi, _r in tools.SMART_TEMPLATES:
        if name in (en, vi):
            return vi if lang() == "vi" else en
    return name


def like(text):
    return f"%{text}%"


def search_where(text, prefix="WHERE"):
    if not text:
        return "", []
    return (f" {prefix} (title LIKE ? OR artist LIKE ? OR album LIKE ? OR albumartist LIKE ? OR genre LIKE ?)",
            [like(text)] * 5)


class Page(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.setObjectName("Page")
        self.ctx = ctx
        self.db = ctx.db
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(22, 18, 22, 10)
        self.lay.setSpacing(10)
        self.filter = ""

    def header(self, title_key, buttons=()):
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(0)
        self.title = h1(tr(title_key))
        self.title_key = title_key
        self.count = QLabel("")
        self.count.setObjectName("Muted")
        col.addWidget(self.title)
        col.addWidget(self.count)
        row.addLayout(col)
        row.addStretch()
        self.hbtns = []
        for key, name, cb, primary in buttons:
            b = QPushButton(icon(name, theme.c("on_accent") if primary else theme.c("ink"), 18), tr(key))
            if primary:
                b.setObjectName("Primary")
            b.clicked.connect(cb)
            b.setProperty("tkey", key)
            row.addWidget(b)
            self.hbtns.append(b)
        self.lay.addLayout(row)

    def retranslate(self):
        if hasattr(self, "title"):
            self.title.setText(tr(self.title_key))
        for b in getattr(self, "hbtns", []):
            b.setText(tr(b.property("tkey")))

    def set_filter(self, text):
        self.filter = text
        self.refresh()

    def refresh(self):
        pass

    def on_playing(self, track_id):
        for t in self.findChildren(TrackTable):
            t.set_playing(track_id)


# --------------------------------------------------------------------------- songs / favourites
class SongsPage(Page):
    def __init__(self, ctx, favs=False):
        super().__init__(ctx)
        self.favs = favs
        self.header("nav_favs" if favs else "nav_songs",
                    [("play", "play", self.play_all, True), ("shuffle_all", "shuffle", self.shuffle_all, False)])
        self.empty = hint(tr("empty_library"))
        self.empty_btn = QPushButton(icon("folder", theme.c("on_accent"), 18), tr("add_folder"))
        self.empty_btn.setObjectName("Primary")
        self.empty_btn.clicked.connect(ctx.add_folder)
        er = QHBoxLayout()
        er.addWidget(self.empty, 1)
        er.addWidget(self.empty_btn)
        self.empty_box = QFrame()
        self.empty_box.setObjectName("Strip")
        self.empty_box.setLayout(er)
        self.lay.addWidget(self.empty_box)
        self.table = TrackTable(ctx, name="favs" if favs else "songs")
        self.lay.addWidget(self.table, 1)

    def retranslate(self):
        super().retranslate()
        self.empty.setText(tr("empty_library"))
        self.empty_btn.setText(tr("add_folder"))

    def refresh(self):
        w, a = search_where(self.filter, "AND")
        cond = "missing=0 AND kind='music'" + (" AND fav=1" if self.favs else "")
        rows = self.db.q(f"SELECT * FROM tracks WHERE {cond}{w} ORDER BY albumartist COLLATE NOCASE, album COLLATE NOCASE, disc_no, track_no, title", a)
        self.table.set_rows(rows)
        total = sum((r["duration"] or 0) for r in rows)
        self.count.setText(tr("songs_count", n=len(rows), h=fmt_time(total)))
        self.empty_box.setVisible(not self.favs and not rows and not self.filter)

    def play_all(self):
        self.ctx.play_rows(self.table.rows_in_view_order(), 0)

    def shuffle_all(self):
        self.ctx.play_rows(self.table.rows_in_view_order(), 0, shuffle=True)


# --------------------------------------------------------------------------- albums
class AlbumModel(QAbstractListModel):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.items = []

    def set_items(self, items):
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def rowCount(self, p=QModelIndex()):
        return len(self.items)

    def data(self, idx, role=Qt.DisplayRole):
        a = self.items[idx.row()]
        if role == Qt.DisplayRole:
            return f"{a['album'] or tr('unknown_album')}\n{a['aa'] or tr('unknown_artist')}"
        if role == Qt.DecorationRole:
            return cover_pixmap(a["art_key"], 150, 14 if theme.CUR["key"] != "soft" else 20, a["album"] or "",
                                self.view.devicePixelRatioF())
        if role == Qt.ToolTipRole:
            return f"{a['album']} — {a['aa']} ({a['n']})"
        return None


class AlbumsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.stack = QStackedWidget()
        grid_page = QWidget()
        gl = QVBoxLayout(grid_page)
        gl.setContentsMargins(0, 0, 0, 0)
        self.lay.addWidget(self.stack, 1)
        self.header_box = QWidget()
        hl = QVBoxLayout(self.header_box)
        hl.setContentsMargins(0, 0, 0, 0)
        old = self.lay
        self.lay = hl
        self.header("nav_albums")
        self.lay = old
        gl.addWidget(self.header_box)
        self.view = QListView()
        self.view.setObjectName("Grid")
        self.view.setViewMode(QListView.IconMode)
        self.view.setResizeMode(QListView.Adjust)
        self.view.setMovement(QListView.Static)
        self.view.setUniformItemSizes(True)
        self.view.setWordWrap(True)
        self.view.setSpacing(12)
        self.view.setIconSize(QSize(150, 150))
        self.view.setGridSize(QSize(178, 222))
        self.view.setLayoutMode(QListView.Batched)
        self.view.setBatchSize(60)
        self.model = AlbumModel(self.view)
        self.view.setModel(self.model)
        self.view.clicked.connect(lambda i: self.open_album(self.model.items[i.row()]))
        gl.addWidget(self.view, 1)
        self.stack.addWidget(grid_page)
        self.detail = AlbumDetail(ctx, self)
        self.stack.addWidget(self.detail)

    def refresh(self):
        w, a = search_where(self.filter, "AND")
        rows = self.db.q(f"""SELECT album, COALESCE(NULLIF(albumartist,''), artist) aa, MIN(art_key) art_key, COUNT(*) n,
                             MAX(year) year FROM tracks WHERE missing=0 AND kind='music'{w}
                             GROUP BY album COLLATE NOCASE, aa COLLATE NOCASE ORDER BY aa COLLATE NOCASE, album COLLATE NOCASE""", a)
        self.model.set_items(rows)
        self.count.setText(tr("albums_count", n=len(rows)))
        if self.stack.currentIndex() == 1:
            self.detail.refresh()

    def open_album(self, a):
        self.detail.show_album(a["album"], a["aa"])
        self.stack.setCurrentIndex(1)

    def retranslate(self):
        super().retranslate()
        self.detail.retranslate()


class AlbumDetail(QWidget):
    def __init__(self, ctx, owner):
        super().__init__()
        self.ctx, self.owner = ctx, owner
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        self.back = QPushButton(icon("back", theme.c("ink"), 18), tr("back"))
        self.back.clicked.connect(lambda: owner.stack.setCurrentIndex(0))
        top.addWidget(self.back)
        top.addStretch()
        lay.addLayout(top)
        card = QFrame()
        card.setObjectName("Card")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(18, 18, 18, 18)
        cl.setSpacing(20)
        self.cover = Cover(200, 18)
        cl.addWidget(self.cover)
        info = QVBoxLayout()
        self.t = h1("")
        self.t.setWordWrap(True)
        self.a = h2("")
        self.meta = QLabel("")
        self.meta.setObjectName("Muted")
        self.reel = QLabel("")
        self.reel.setObjectName("TealBadge")
        self.reel.hide()
        info.addStretch()
        info.addWidget(self.t)
        info.addWidget(self.a)
        info.addWidget(self.meta)
        rr = QHBoxLayout()
        rr.addWidget(self.reel)
        rr.addStretch()
        info.addLayout(rr)
        btns = QHBoxLayout()
        self.b_play = QPushButton(icon("play", theme.c("on_accent"), 18), tr("play"))
        self.b_play.setObjectName("Primary")
        self.b_shuf = QPushButton(icon("shuffle", theme.c("ink"), 18), tr("shuffle_all"))
        self.b_play.clicked.connect(lambda: ctx.play_rows(self.table.rows_in_view_order(), 0))
        self.b_shuf.clicked.connect(lambda: ctx.play_rows(self.table.rows_in_view_order(), 0, shuffle=True))
        btns.addWidget(self.b_play)
        btns.addWidget(self.b_shuf)
        btns.addStretch()
        info.addLayout(btns)
        info.addStretch()
        cl.addLayout(info, 1)
        lay.addWidget(card)
        self.table = TrackTable(ctx, name="album")
        lay.addWidget(self.table, 1)
        self.album = self.artist = None

    def retranslate(self):
        self.back.setText(tr("back"))
        self.b_play.setText(tr("play"))
        self.b_shuf.setText(tr("shuffle_all"))
        if self.album is not None:
            self.refresh()

    def show_album(self, album, artist):
        self.album, self.artist = album, artist
        self.refresh()

    def refresh(self):
        db = self.ctx.db
        rows = db.q("""SELECT * FROM tracks WHERE missing=0 AND kind='music' AND COALESCE(album,'')=COALESCE(?, '')
                       AND COALESCE(NULLIF(albumartist,''), artist, '')=COALESCE(?, '') ORDER BY disc_no, track_no, title""",
                    (self.album, self.artist))
        self.table.set_rows(rows)
        self.t.setText(self.album or tr("unknown_album"))
        self.a.setText(self.artist or tr("unknown_artist"))
        years = sorted({r["year"] for r in rows if r["year"]})
        fmts = sorted({r["codec"] for r in rows if r["codec"]})
        total = sum(r["duration"] or 0 for r in rows)
        bits = [str(years[-1])] if years else []
        bits += [tr("songs_count", n=len(rows), h=fmt_time(total))] + ([" / ".join(fmts)] if fmts else [])
        self.meta.setText(" · ".join(bits))
        self.cover.set_key(rows[0]["art_key"] if rows else None, self.album or "")
        owned = self.ctx.reel.formats_for(self.album, self.artist) if self.ctx.reel else []
        self.reel.setVisible(bool(owned))
        if owned:
            self.reel.setText(tr("album_on_reel", f=", ".join(owned)))


# --------------------------------------------------------------------------- artists / genres
class CategoryPage(Page):
    def __init__(self, ctx, field):
        super().__init__(ctx)
        self.field = field
        self.header("nav_artists" if field == "artist" else "nav_genres",
                    [("play", "play", self.play, True), ("shuffle_all", "shuffle", lambda: self.play(True), False)])
        sp = QSplitter()
        self.list = QListWidget()
        self.list.setMinimumWidth(220)
        self.list.currentItemChanged.connect(lambda *_: self.load())
        sp.addWidget(self.list)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        self.sel = h2("")
        rl.addWidget(self.sel)
        self.table = TrackTable(ctx, name=field)
        rl.addWidget(self.table, 1)
        sp.addWidget(right)
        sp.setSizes([260, 900])
        self.lay.addWidget(sp, 1)

    def _expr(self):
        return "COALESCE(NULLIF(artist,''),'')" if self.field == "artist" else "COALESCE(NULLIF(genre,''),'')"

    def refresh(self):
        cur = self.list.currentItem().data(Qt.UserRole) if self.list.currentItem() else None
        e = self._expr()
        args = []
        w = ""
        if self.filter:
            w = f" AND {e} LIKE ?"
            args = [like(self.filter)]
        rows = self.db.q(f"SELECT {e} k, COUNT(*) n FROM tracks WHERE missing=0 AND kind='music'{w} GROUP BY {e} COLLATE NOCASE ORDER BY k COLLATE NOCASE", args)
        self.list.blockSignals(True)
        self.list.clear()
        pick = None
        for r in rows:
            label = r["k"] or (tr("unknown_artist") if self.field == "artist" else tr("unknown_genre"))
            it = QListWidgetItem(icon("artist" if self.field == "artist" else "genre", theme.c("muted"), 18), f"{label}  ({r['n']})")
            it.setData(Qt.UserRole, r["k"])
            self.list.addItem(it)
            if r["k"] == cur:
                pick = it
        self.list.blockSignals(False)
        self.count.setText(tr("artists_count", n=len(rows)) if self.field == "artist" else f"{len(rows)}")
        if pick:
            self.list.setCurrentItem(pick)
        elif self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.table.set_rows([])
            self.sel.setText("")

    def load(self):
        it = self.list.currentItem()
        if not it:
            return
        k = it.data(Qt.UserRole)
        rows = self.db.q(f"SELECT * FROM tracks WHERE missing=0 AND kind='music' AND {self._expr()}=? COLLATE NOCASE "
                         "ORDER BY album COLLATE NOCASE, disc_no, track_no", (k,))
        self.sel.setText(it.text())
        self.table.set_rows(rows)

    def play(self, shuffle=False):
        self.ctx.play_rows(self.table.rows_in_view_order(), 0, shuffle=shuffle)


# --------------------------------------------------------------------------- folders
class FoldersPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_folders", [("add_folder", "add", ctx.add_folder, True), ("rescan", "refresh", ctx.rescan, False),
                                    ("remove_folder", "close", self.remove, False)])
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        self.ftitle = h2(tr("folders_title"))
        cl.addWidget(self.ftitle)
        self.flist = QListWidget()
        self.flist.setMaximumHeight(150)
        cl.addWidget(self.flist)
        self.fhint = hint(tr("folders_hint"))
        cl.addWidget(self.fhint)
        self.lay.addWidget(card)
        sp = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(260)
        self.tree.currentItemChanged.connect(lambda *_: self.load())
        sp.addWidget(self.tree)
        self.table = TrackTable(ctx, name="folders")
        sp.addWidget(self.table)
        sp.setSizes([300, 900])
        self.lay.addWidget(sp, 1)

    def retranslate(self):
        super().retranslate()
        self.ftitle.setText(tr("folders_title"))
        self.fhint.setText(tr("folders_hint"))

    def refresh(self):
        self.flist.clear()
        for f in self.db.q("SELECT * FROM folders ORDER BY path"):
            on = volumes.online(f["vol_serial"]) and scanner.folder_path(f) and os.path.isdir(scanner.folder_path(f))
            n = self.db.one("SELECT COUNT(*) c FROM tracks WHERE folder_id=? AND missing=0", (f["id"],))["c"]
            where = scanner.folder_path(f) or f["path"]
            lab = f"{where}   ·   {n}   ·   {tr('drive_online') if on else tr('drive_offline')}"
            if f["label"]:
                lab += f"   ·   {f['label']}"
            it = QListWidgetItem(icon("folder", theme.c("teal") if on else theme.c("grey"), 20), lab)
            it.setData(Qt.UserRole, f["id"])
            if not on:
                it.setForeground(Qt.gray)
            self.flist.addItem(it)
        self._build_tree()

    def _build_tree(self):
        self.tree.clear()
        for f in self.db.q("SELECT * FROM folders ORDER BY path"):
            root_path = scanner.folder_path(f) or f["path"]
            root = QTreeWidgetItem([os.path.basename(root_path.rstrip("\\/")) or root_path])
            root.setIcon(0, icon("folder", theme.c("teal"), 18))
            root.setData(0, Qt.UserRole, (f["id"], ""))
            self.tree.addTopLevelItem(root)
            nodes = {"": root}
            base_rel = f["rel"].rstrip("\\/")
            dirs = set()
            for r in self.db.q("SELECT rel_path FROM tracks WHERE folder_id=? AND missing=0", (f["id"],)):
                d = os.path.dirname(r["rel_path"])
                rel = d[len(base_rel):].lstrip("\\/") if d.startswith(base_rel) else d
                while rel:
                    dirs.add(rel)
                    rel = os.path.dirname(rel)
            for d in sorted(dirs, key=lambda s: (s.count(os.sep) + s.count("/"), s.lower())):
                parent = nodes.get(os.path.dirname(d), root)
                it = QTreeWidgetItem([os.path.basename(d)])
                it.setIcon(0, icon("folder", theme.c("muted"), 16))
                it.setData(0, Qt.UserRole, (f["id"], d))
                parent.addChild(it)
                nodes[d] = it
            root.setExpanded(True)

    def load(self):
        it = self.tree.currentItem()
        if not it:
            return
        fid, sub = it.data(0, Qt.UserRole)
        f = self.db.one("SELECT * FROM folders WHERE id=?", (fid,))
        base = f["rel"].rstrip("\\/")
        prefix = os.path.join(base, sub) if sub else base
        rows = self.db.q("SELECT * FROM tracks WHERE folder_id=? AND missing=0 AND rel_path LIKE ? ORDER BY rel_path",
                         (fid, prefix + "%"))
        self.table.set_rows(rows)

    def remove(self):
        it = self.flist.currentItem()
        if not it:
            return
        fid = it.data(Qt.UserRole)
        if QMessageBox.question(self, tr("remove_folder"), it.text().split("   ·")[0] + "\n\n" + tr("remove_folder") + "?") != QMessageBox.Yes:
            return
        self.db.x("DELETE FROM tracks WHERE folder_id=?", (fid,))
        self.db.x("DELETE FROM folders WHERE id=?", (fid,))
        self.ctx.refresh_all()


# --------------------------------------------------------------------------- playlists
class PlaylistsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_playlists", [("new_playlist", "add", self.new, True), ("pl_new_smart", "settings", self.new_smart, False),
                                      ("pl_import", "download", self.import_m3u, False)])
        sp = QSplitter()
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setMinimumWidth(230)
        self.list.currentItemChanged.connect(lambda *_: self.load())
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        ll.addWidget(self.list)
        sp.addWidget(left)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        hr = QHBoxLayout()
        self.sel = h2("")
        hr.addWidget(self.sel)
        hr.addStretch()
        self.b_play = QPushButton(icon("play", theme.c("on_accent"), 18), tr("play"))
        self.b_play.setObjectName("Primary")
        self.b_play.clicked.connect(lambda: ctx.play_rows(self.table.rows_in_view_order(), 0))
        self.b_export = QPushButton(tr("pl_export"))
        self.b_export.clicked.connect(self.export)
        self.b_dock = QPushButton(tr("pl_to_dock"))
        self.b_dock.clicked.connect(self.to_dock)
        self.b_edit = QPushButton(tr("edit"))
        self.b_edit.clicked.connect(self.edit)
        for b in (self.b_play, self.b_export, self.b_dock, self.b_edit):
            hr.addWidget(b)
        rl.addLayout(hr)
        self.table = TrackTable(ctx, name="playlist", playlist_id=-1)
        rl.addWidget(self.table, 1)
        sp.addWidget(right)
        sp.setSizes([260, 900])
        self.lay.addWidget(sp, 1)

    def retranslate(self):
        super().retranslate()
        self.b_play.setText(tr("play"))
        self.b_export.setText(tr("pl_export"))
        self.b_dock.setText(tr("pl_to_dock"))
        self.b_edit.setText(tr("edit"))
        self.refresh()

    def _ensure_smart(self):
        if self.db.get("smart_seeded"):
            return
        from ..i18n import lang
        for en, vi, rules in tools.SMART_TEMPLATES[:3]:
            self.db.x("INSERT INTO playlists(name, smart_rules, created) VALUES(?,?,?)",
                      (vi if lang() == "vi" else en, json.dumps(rules), time.time()))
        self.db.set("smart_seeded", 1)

    def refresh(self):
        self._ensure_smart()
        cur = self.current_id()
        self.list.blockSignals(True)
        self.list.clear()
        pick = None
        for pl in self.db.q("SELECT * FROM playlists ORDER BY (smart_rules IS NULL), sort, name COLLATE NOCASE"):
            smart = pl["smart_rules"] is not None
            it = QListWidgetItem(icon("settings" if smart else "playlist", theme.c("teal") if smart else theme.c("muted"), 18),
                                 display_name(pl["name"]) + (f"   ({tr('pl_smart')})" if smart else ""))
            it.setData(Qt.UserRole, pl["id"])
            self.list.addItem(it)
            if pl["id"] == cur:
                pick = it
        self.list.blockSignals(False)
        self.count.setText(str(self.list.count()))
        if pick:
            self.list.setCurrentItem(pick)
        elif self.list.count():
            self.list.setCurrentRow(0)
        self.load()

    def current_id(self):
        it = self.list.currentItem()
        return it.data(Qt.UserRole) if it else None

    def rows_for(self, pid):
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        if not pl:
            return []
        if pl["smart_rules"]:
            sql, args = tools.smart_sql(json.loads(pl["smart_rules"]))
            return self.db.q(sql, args)
        return self.db.q("SELECT t.* FROM playlist_items i JOIN tracks t ON t.id=i.track_id WHERE i.playlist_id=? ORDER BY i.pos", (pid,))

    def load(self):
        pid = self.current_id()
        if pid is None:
            self.table.set_rows([])
            self.sel.setText("")
            return
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        self.table.playlist_id = None if pl["smart_rules"] else pid
        rows = self.rows_for(pid)
        self.table.set_rows(rows)
        self.sel.setText(f"{display_name(pl['name'])}  ·  {tr('songs_count', n=len(rows), h=fmt_time(sum(r['duration'] or 0 for r in rows)))}")
        self.b_edit.setVisible(bool(pl["smart_rules"]))

    def new(self):
        name, ok = QInputDialog.getText(self, tr("new_playlist"), tr("pl_name"))
        if ok and name.strip():
            pid = self.db.x("INSERT INTO playlists(name, created) VALUES(?,?)", (name.strip(), time.time()))
            self.refresh()
            self._select(pid)
            return pid
        return None

    def _select(self, pid):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == pid:
                self.list.setCurrentRow(i)

    def new_smart(self):
        from .dialogs import SmartDialog
        d = SmartDialog(self, None)
        if d.exec():
            name, rules = d.result_value()
            pid = self.db.x("INSERT INTO playlists(name, smart_rules, created) VALUES(?,?,?)", (name, json.dumps(rules), time.time()))
            self.refresh()
            self._select(pid)

    def edit(self):
        pid = self.current_id()
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        if not pl or not pl["smart_rules"]:
            return
        from .dialogs import SmartDialog
        d = SmartDialog(self, (pl["name"], json.loads(pl["smart_rules"])))
        if d.exec():
            name, rules = d.result_value()
            self.db.x("UPDATE playlists SET name=?, smart_rules=? WHERE id=?", (name, json.dumps(rules), pid))
            self.refresh()

    def _menu(self, pos):
        from PySide6.QtWidgets import QMenu
        pid = self.current_id()
        if pid is None:
            return
        m = QMenu(self)
        m.addAction(tr("pl_rename"), self.rename)
        m.addAction(tr("pl_export"), self.export)
        m.addAction(tr("pl_to_dock"), self.to_dock)
        m.addSeparator()
        m.addAction(tr("pl_delete"), self.delete)
        m.exec(self.list.mapToGlobal(pos))

    def rename(self):
        pid = self.current_id()
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        name, ok = QInputDialog.getText(self, tr("pl_rename"), tr("pl_name"), text=pl["name"])
        if ok and name.strip():
            self.db.push_undo(tr("pl_rename"), [("UPDATE playlists SET name=? WHERE id=?", (pl["name"], pid))])
            self.db.x("UPDATE playlists SET name=? WHERE id=?", (name.strip(), pid))
            self.refresh()

    def delete(self):
        pid = self.current_id()
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        if QMessageBox.question(self, tr("pl_delete"), f"{pl['name']}?") != QMessageBox.Yes:
            return
        items = self.db.q("SELECT * FROM playlist_items WHERE playlist_id=?", (pid,))
        undo = [("INSERT INTO playlists(id,name,smart_rules,created,sort) VALUES(?,?,?,?,?)",
                 (pl["id"], pl["name"], pl["smart_rules"], pl["created"], pl["sort"]))]
        undo += [("INSERT INTO playlist_items(playlist_id,pos,track_id) VALUES(?,?,?)", (i["playlist_id"], i["pos"], i["track_id"])) for i in items]
        self.db.push_undo(tr("pl_delete"), undo)
        self.db.x("DELETE FROM playlist_items WHERE playlist_id=?", (pid,))
        self.db.x("DELETE FROM playlists WHERE id=?", (pid,))
        self.refresh()

    def _rows_paths(self, pid):
        return [(r, scanner.track_path(r)) for r in self.rows_for(pid)]

    def export(self):
        pid = self.current_id()
        if pid is None:
            return
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        path, _ = QFileDialog.getSaveFileName(self, tr("pl_export"), pl["name"] + ".m3u8", "Playlist (*.m3u8 *.m3u)")
        if path:
            tools.export_m3u(self._rows_paths(pid), path, pl["name"])
            self.ctx.toast(tr("saved"))

    def to_dock(self):
        from ..app_info import shared_send_dir
        pid = self.current_id()
        if pid is None:
            return
        pl = self.db.one("SELECT * FROM playlists WHERE id=?", (pid,))
        d = shared_send_dir() / "Tom's Dock" / "Playlists"
        d.mkdir(parents=True, exist_ok=True)
        from ..recorder import safe_name
        p = d / (safe_name(pl["name"]) + ".m3u8")
        tools.export_m3u(self._rows_paths(pid), str(p), pl["name"])
        QMessageBox.information(self, tr("pl_to_dock"), tr("pl_sent", p=str(p)) + "\n\n" + tr("pl_dock_note"))

    def import_m3u(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("pl_import"), "", "Playlist (*.m3u *.m3u8)")
        if not path:
            return
        files = tools.import_m3u(path)
        ids = []
        for f in files:
            serial, rel, _ = volumes.split(f)
            r = self.db.one("SELECT id FROM tracks WHERE vol_serial=? AND rel_path=?", (serial, rel))
            if r:
                ids.append(r["id"])
        name = os.path.splitext(os.path.basename(path))[0]
        pid = self.db.x("INSERT INTO playlists(name, created) VALUES(?,?)", (name, time.time()))
        self.db.many("INSERT INTO playlist_items(playlist_id,pos,track_id) VALUES(?,?,?)", [(pid, i, t) for i, t in enumerate(ids)])
        self.refresh()
        self._select(pid)
        self.ctx.toast(f"{name}: {len(ids)}/{len(files)}")


# --------------------------------------------------------------------------- statistics
class StatsPage(Page):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.header("nav_stats")
        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        self.lay.addLayout(self.grid)
        self.most = TrackTable(ctx, name="stats_most", sortable=False)
        self.recent = TrackTable(ctx, name="stats_recent", sortable=False)
        row = QHBoxLayout()
        c1 = QVBoxLayout()
        self.l_most = h2(tr("st_most"))
        c1.addWidget(self.l_most)
        c1.addWidget(self.most)
        c2 = QVBoxLayout()
        self.l_recent = h2(tr("st_recent"))
        c2.addWidget(self.l_recent)
        c2.addWidget(self.recent)
        row.addLayout(c1)
        row.addLayout(c2)
        self.lay.addLayout(row, 1)
        self.cards = []

    def retranslate(self):
        super().retranslate()
        self.l_most.setText(tr("st_most"))
        self.l_recent.setText(tr("st_recent"))

    def _card(self, i, title, value, sub=""):
        while len(self.cards) <= i:
            f = QFrame()
            f.setObjectName("Card")
            v = QVBoxLayout(f)
            a, b, c = QLabel(), h1(""), QLabel()
            a.setObjectName("Muted")
            c.setObjectName("Hint")
            for w in (a, b, c):
                v.addWidget(w)
            f.labels = (a, b, c)
            self.grid.addWidget(f, 0, len(self.cards))
            self.cards.append(f)
        a, b, c = self.cards[i].labels
        a.setText(title)
        b.setText(value)
        c.setText(sub)

    def refresh(self):
        db = self.db
        s = db.one("SELECT COUNT(*) n, SUM(duration) d, COUNT(DISTINCT album) a, COUNT(DISTINCT artist) ar FROM tracks WHERE missing=0 AND kind='music'")
        month = time.time() - 30 * 86400
        lm = db.one("SELECT COUNT(*) n FROM history WHERE played_at>?", (month,))["n"]
        self._card(0, tr("st_total"), str(s["n"] or 0), tr("st_hours", h=int((s["d"] or 0) / 3600)))
        self._card(1, tr("nav_albums"), str(s["a"] or 0), tr("artists_count", n=s["ar"] or 0))
        self._card(2, tr("st_listened"), str(lm), tr("nav_songs"))
        fm = db.q("SELECT codec, COUNT(*) n FROM tracks WHERE missing=0 AND kind='music' GROUP BY codec ORDER BY n DESC LIMIT 4")
        self._card(3, tr("st_formats"), " · ".join(f"{r['codec'] or '?'}" for r in fm[:2]) or "-",
                   " · ".join(f"{r['codec'] or '?'} {r['n']}" for r in fm))
        self.most.set_rows(db.q("SELECT * FROM tracks WHERE plays>0 AND missing=0 ORDER BY plays DESC LIMIT 50"))
        self.recent.set_rows(db.q("SELECT * FROM tracks WHERE last_played IS NOT NULL AND missing=0 ORDER BY last_played DESC LIMIT 50"))
