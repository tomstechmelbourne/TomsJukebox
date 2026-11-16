"""Background jobs and the shared song table."""
import os
import traceback

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QObject, QRunnable, QSize, QSortFilterProxyModel, Qt,
                            QThreadPool, Signal)
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QTableView

from .. import volumes
from ..app_info import log
from ..i18n import tr
from . import theme
from .icons import icon
from .widgets import fmt_time


class _Sig(QObject):
    done = Signal(object)
    failed = Signal(str)
    progress = Signal(object)


class Job(QRunnable):
    def __init__(self, fn, args, kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.sig = _Sig()
        self.stopped = False
        self.setAutoDelete(True)

    def run(self):
        try:
            r = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            log.warning("job failed: %s\n%s", e, traceback.format_exc())
            try:
                self.sig.failed.emit(str(e))
            except RuntimeError:
                pass
            return
        try:
            self.sig.done.emit(r)
        except RuntimeError:   # window already closed
            pass


_jobs = set()


def _safe_emit(signal, value):
    try:
        signal.emit(value)
    except RuntimeError:
        pass


def run_bg(fn, *args, done=None, failed=None, progress=None, with_progress=False, **kwargs):
    """Run fn in a worker thread. If with_progress, fn gets progress=callable and stop=callable."""
    job = Job(fn, args, kwargs)
    if with_progress:
        job.kwargs["progress"] = lambda *a: _safe_emit(job.sig.progress, a)
        job.kwargs["stop"] = lambda: job.stopped
    if done:
        job.sig.done.connect(done)
    if failed:
        job.sig.failed.connect(failed)
    if progress:
        job.sig.progress.connect(progress)
    _jobs.add(job.sig)
    job.sig.done.connect(lambda *_: _jobs.discard(job.sig))
    job.sig.failed.connect(lambda *_: _jobs.discard(job.sig))
    QThreadPool.globalInstance().start(job)
    return job


COLS = [("fav", "col_fav", 34), ("track_no", "col_no", 40), ("title", "col_title", 260), ("artist", "col_artist", 170),
        ("album", "col_album", 180), ("year", "col_year", 60), ("genre", "col_genre", 110),
        ("duration", "col_len", 70), ("codec", "col_fmt", 90), ("plays", "col_plays", 70)]


class TrackModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.playing_id = None
        self._online = {}

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self._online = {}
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLS)

    def headerData(self, s, o, role=Qt.DisplayRole):
        if o == Qt.Horizontal and role == Qt.DisplayRole:
            return tr(COLS[s][1])
        if o == Qt.Horizontal and role == Qt.TextAlignmentRole:
            return int(Qt.AlignLeft | Qt.AlignVCenter) if COLS[s][0] in ("title", "artist", "album") else int(Qt.AlignCenter)
        return None

    def _is_online(self, r):
        vs = r["vol_serial"]
        if vs not in self._online:
            self._online[vs] = volumes.online(vs)
        return self._online[vs]

    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid():
            return None
        r = self.rows[idx.row()]
        key = COLS[idx.column()][0]
        if role == Qt.DisplayRole:
            if key == "fav":
                return None
            v = r[key]
            if key == "duration":
                return fmt_time(v)
            if key == "codec":
                fmt = v or ""
                if r["bits"] and r["bits"] > 16:
                    fmt += f" {r['bits']}-bit"
                elif r["bitrate"] and fmt in ("MP3", "AAC", "OPUS", "VORBIS"):
                    fmt += f" {int(r['bitrate'] / 1000)}k"
                return fmt
            if key in ("track_no", "year", "plays"):
                return "" if not v else str(v)
            return v or ""
        if role == Qt.DecorationRole and key == "fav":
            return icon("star_on" if r["fav"] else "star", theme.c("grey"), 16)
        if role == Qt.ForegroundRole:
            if r["missing"] or not self._is_online(r):
                return QColor(theme.c("grey"))
            if r["id"] == self.playing_id:
                return QColor(theme.c("teal"))
        if role == Qt.FontRole and r["id"] == self.playing_id:
            f = QFont()
            f.setBold(True)
            return f
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignLeft | Qt.AlignVCenter) if key in ("title", "artist", "album") else int(Qt.AlignCenter)
        if role == Qt.ToolTipRole and (r["missing"] or not self._is_online(r)):
            return tr("offline_track")
        if role == Qt.UserRole:
            v = r[key]
            return v if v is not None else ""
        return None


class SortProxy(QSortFilterProxyModel):
    def lessThan(self, a, b):
        va, vb = a.data(Qt.UserRole), b.data(Qt.UserRole)
        try:
            return (va or 0) < (vb or 0) if isinstance(va, (int, float)) or isinstance(vb, (int, float)) else str(va).lower() < str(vb).lower()
        except TypeError:
            return str(va) < str(vb)


class TrackTable(QTableView):
    """Song list used by every page. ctx = main window (provides the actions)."""

    def __init__(self, ctx, playlist_id=None, sortable=True, name="songs"):
        super().__init__()
        self.ctx = ctx
        self.name = name
        self.playlist_id = playlist_id
        self.model_ = TrackModel(self)
        self.proxy = SortProxy(self)
        self.proxy.setSourceModel(self.model_)
        self.setModel(self.proxy)
        self.setSortingEnabled(sortable)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.setWordWrap(False)
        self.setIconSize(QSize(16, 16))
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setStretchLastSection(False)
        hh.setHighlightSections(False)
        widths = (ctx.db.get("col_widths") or {}).get(name, {})
        for i, (k, _l, w) in enumerate(COLS):
            self.setColumnWidth(i, int(widths.get(k, w)))
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.sectionResized.connect(self._save_width)
        self.doubleClicked.connect(self._dbl)
        self.clicked.connect(self._click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.setDragEnabled(playlist_id is not None)
        self.verticalHeader().setDefaultSectionSize(int(theme.pt() * 3.3))

    def _save_width(self, i, _old, new):
        allw = self.ctx.db.get("col_widths") or {}
        allw.setdefault(self.name, {})[COLS[i][0]] = new
        self.ctx.db.set("col_widths", allw)

    def set_rows(self, rows):
        self.model_.set_rows(rows)
        self.verticalHeader().setDefaultSectionSize(int(theme.pt() * 3.3))

    def rows_in_view_order(self):
        return [self.model_.rows[self.proxy.mapToSource(self.proxy.index(i, 0)).row()] for i in range(self.proxy.rowCount())]

    def selected_rows(self):
        idxs = sorted({self.proxy.mapToSource(i).row() for i in self.selectionModel().selectedRows()})
        return [self.model_.rows[i] for i in idxs]

    def set_playing(self, track_id):
        self.model_.playing_id = track_id
        self.viewport().update()

    def _dbl(self, idx):
        rows = self.rows_in_view_order()
        self.ctx.play_rows(rows, idx.row())

    def _click(self, idx):
        if COLS[idx.column()][0] == "fav":
            r = self.model_.rows[self.proxy.mapToSource(idx).row()]
            self.ctx.toggle_fav([r])

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and self.currentIndex().isValid():
            self._dbl(self.currentIndex())
            return
        super().keyPressEvent(e)

    def _menu(self, pos):
        rows = self.selected_rows()
        if not rows:
            return
        m = QMenu(self)
        c = theme.c("ink")
        m.addAction(icon("play", c, 18), tr("play"), lambda: self.ctx.play_rows(rows, 0))
        m.addAction(icon("next", c, 18), tr("play_next"), lambda: self.ctx.add_rows(rows, nxt=True))
        m.addAction(icon("queue", c, 18), tr("add_queue"), lambda: self.ctx.add_rows(rows))
        sub = m.addMenu(icon("playlist", c, 18), tr("add_playlist"))
        sub.addAction(tr("new_playlist"), lambda: self.ctx.add_to_playlist(rows, None))
        for pl in self.ctx.db.q("SELECT id, name FROM playlists WHERE smart_rules IS NULL ORDER BY sort, name"):
            sub.addAction(pl["name"], lambda _=False, i=pl["id"]: self.ctx.add_to_playlist(rows, i))
        m.addSeparator()
        m.addAction(icon("star_on", c, 18), tr("fav_toggle"), lambda: self.ctx.toggle_fav(rows))
        m.addAction(icon("settings", c, 18), tr("edit_info"), lambda: self.ctx.edit_info(rows))
        m.addAction(icon("web", c, 18), tr("find_online"), lambda: self.ctx.edit_info(rows, online=True))
        m.addAction(icon("folder", c, 18), tr("show_folder"), lambda: self.ctx.show_in_folder(rows[0]))
        m.addAction(icon("cast", c, 18), tr("play_tv"), lambda: self.ctx.cast_rows(rows))
        if self.playlist_id:
            m.addSeparator()
            a = QAction(tr("remove_from_pl"), m)
            a.triggered.connect(lambda: self.ctx.remove_from_playlist(self.playlist_id, rows))
            m.addAction(a)
        m.exec(self.viewport().mapToGlobal(pos))


def open_in_explorer(path):
    import subprocess
    import sys
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                os.startfile(path)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path) if os.path.isfile(path) else path])
    except Exception as e:
        log.info("open folder failed: %s", e)
