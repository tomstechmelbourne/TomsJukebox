"""Player controller: queue, shuffle, repeat, gapless hand-over, play counts, resume, radio titles."""
import os
import random
import time

from PySide6.QtCore import QObject, QTimer, Signal

from .. import engine as eng
from .. import radio, scanner
from ..app_info import log


class Item(dict):
    """kind: track | radio | cd | episode | file"""

    @property
    def title(self):
        return self.get("title") or ""


def track_item(row):
    return Item(kind="track", id=row["id"], title=row["title"], artist=row["artist"], album=row["album"],
                albumartist=row["albumartist"], duration=row["duration"] or 0, art_key=row["art_key"],
                rg_track=row["rg_track"], rg_album=row["rg_album"], codec=row["codec"],
                vol_serial=row["vol_serial"], rel_path=row["rel_path"], path=row["path"])


class Player(QObject):
    changed = Signal(object)          # current Item (or None)
    state = Signal(bool)              # playing?
    queue_changed = Signal()
    message = Signal(str)
    radio_title = Signal(str)

    def __init__(self, db, null_output=False, fast=False):
        super().__init__()
        self.db = db
        self.engine = eng.Engine(null_output=null_output, fast=fast)
        self.engine.next_provider = self._provide_next
        self.queue = []
        self.order = []          # play order (indexes into queue) when shuffled
        self.pos = -1            # index into order
        self.shuffle = bool(db.get("shuffle"))
        self.repeat = db.get("repeat") or "off"
        self.current = None
        self.counted = False
        self._token = 0
        self._tokens = {}
        self._pending_next = None
        self.cast = None         # DLNA renderer when playing on TV
        self.cast_server = None
        self.cd_drive = None
        self.apply_settings()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(100)
        self._last_save = 0

    # ---------------------------------------------------------------- settings
    def apply_settings(self):
        self.engine.set_volume(self.db.get("volume") / 100.0)
        self.engine.set_eq(self.db.get("eq_on"), self.db.get("eq_gains"))
        self.engine.crossfade = float(self.db.get("crossfade") or 0)
        self.engine.gapless = bool(self.db.get("gapless"))

    # ---------------------------------------------------------------- queue
    def _rebuild_order(self, keep_current=True):
        cur = self.order[self.pos] if 0 <= self.pos < len(self.order) else None
        self.order = list(range(len(self.queue)))
        if self.shuffle:
            random.shuffle(self.order)
            if keep_current and cur is not None and cur in self.order:
                self.order.remove(cur)
                self.order.insert(0, cur)
                self.pos = 0
                return
        self.pos = self.order.index(cur) if (cur is not None and cur in self.order) else -1

    def play_list(self, items, start=0, shuffle=None):
        if not items:
            return
        if shuffle is not None:
            self.set_shuffle(shuffle, rebuild=False)
        self.queue = list(items)
        self.order = list(range(len(self.queue)))
        if self.shuffle:
            random.shuffle(self.order)
            if shuffle is None or not shuffle:
                self.order.remove(start)
                self.order.insert(0, start)
            start_pos = 0
        else:
            start_pos = start
        self.pos = start_pos
        self.queue_changed.emit()
        self._start(self.queue[self.order[self.pos]])

    def play_item(self, item):
        self.play_list([item], 0)

    def add_next(self, items):
        if not self.queue:
            return self.play_list(items, 0)
        at = self.pos + 1
        n0 = len(self.queue)
        self.queue.extend(items)
        for i, _ in enumerate(items):
            self.order.insert(at + i, n0 + i)
        self._pending_next = None
        self.queue_changed.emit()

    def add_queue(self, items):
        if not self.queue:
            return self.play_list(items, 0)
        n0 = len(self.queue)
        self.queue.extend(items)
        self.order.extend(range(n0, n0 + len(items)))
        self.queue_changed.emit()

    def upcoming(self):
        return [self.queue[i] for i in self.order[self.pos + 1:]] if self.queue else []

    def clear_queue(self):
        keep = self.current
        self.queue = [keep] if keep else []
        self.order = [0] if keep else []
        self.pos = 0 if keep else -1
        self._pending_next = None
        self.queue_changed.emit()

    def remove_upcoming(self, offset):
        idx = self.pos + 1 + offset
        if 0 <= idx < len(self.order):
            self.order.pop(idx)
            self._pending_next = None
            self.queue_changed.emit()

    def set_shuffle(self, on, rebuild=True):
        self.shuffle = bool(on)
        self.db.set("shuffle", int(self.shuffle))
        if rebuild and self.queue:
            self._rebuild_order()
            self._pending_next = None
            self.queue_changed.emit()

    def cycle_repeat(self):
        self.repeat = {"off": "all", "all": "one", "one": "off"}[self.repeat]
        self.db.set("repeat", self.repeat)
        return self.repeat

    # ---------------------------------------------------------------- sources
    def _gain(self, it):
        mode = self.db.get("replaygain")
        if it.get("kind") != "track" or mode == "off":
            return 0.0
        g = it.get("rg_album") if mode == "album" and it.get("rg_album") is not None else it.get("rg_track")
        return float(g) if g is not None else 0.0

    def source_for(self, it):
        k = it.get("kind")
        if k == "track":
            p = scanner.track_path(it)
            if not p or not os.path.exists(p):
                raise FileNotFoundError("offline")
            return eng.AVSource(p, duration=it.get("duration") or None)
        if k == "file":
            return eng.AVSource(it["path"])
        if k == "episode":
            target = it.get("local_path") if it.get("local_path") and os.path.exists(it["local_path"]) else it["url"]
            return eng.AVSource(target)
        if k == "radio":
            return radio.open_radio_source(it["url"])
        if k == "cd":
            drv = self.cd_drive
            start, end = it["lba_start"], it["lba_end"]
            total = (end - start) * 588

            def reader(off, n, _s=start):
                return drv.read_frames(_s, off, n)
            return eng.PCMSource(reader, total)
        if k == "tone":
            return eng.ToneSource(it.get("duration", 2.0))
        raise ValueError(k)

    def _new_token(self, it):
        self._token += 1
        self._tokens[self._token] = it
        if len(self._tokens) > 50:
            for t in sorted(self._tokens)[:-20]:
                self._tokens.pop(t, None)
        return self._token

    def _start(self, it, seek_to=None):
        self.current = it
        self.counted = False
        self._pending_next = None
        if self.cast is not None and it.get("kind") in ("track", "file", "episode"):
            self._start_cast(it)
            return
        try:
            src = self.source_for(it)
        except FileNotFoundError:
            from ..i18n import tr
            self.message.emit(tr("offline_track"))
            QTimer.singleShot(400, self.next)
            return
        except Exception as e:
            from ..i18n import tr
            log.warning("cannot open %s: %s", it.title, e)
            self.message.emit(tr("play_error", e=str(e)[:140]))
            self.changed.emit(it)
            self.state.emit(False)
            return
        tok = self._new_token(it)
        self._radio_src = src if it.get("kind") == "radio" else None
        self._loaded = True
        self.engine.play(tok, src, self._gain(it))
        if seek_to:
            self.engine.seek(seek_to)
        self.changed.emit(it)
        self.state.emit(True)

    def _peek_next_index(self):
        if not self.queue:
            return None
        if self.repeat == "one":
            return self.pos
        nxt = self.pos + 1
        if nxt >= len(self.order):
            if self.repeat == "all":
                return 0
            return None
        return nxt

    def _provide_next(self):
        """Called from the decoder thread for gapless / crossfade."""
        cur = self.current
        if not cur or cur.get("kind") not in ("track", "cd", "file"):
            return None
        npos = self._peek_next_index()
        if npos is None:
            return None
        it = self.queue[self.order[npos]]
        if it.get("kind") not in ("track", "cd", "file"):
            return None
        try:
            src = self.source_for(it)
        except Exception:
            return None
        tok = self._new_token(it)
        self._pending_next = (tok, npos)
        return tok, src, self._gain(it)

    # ---------------------------------------------------------------- controls
    def toggle(self):
        if self.current is None:
            if self.queue:
                self._start(self.queue[self.order[max(0, self.pos)]])
            return
        if not getattr(self, "_loaded", False) and self.cast is None:
            self.play_resumed()
            return
        if self.cast is not None:
            try:
                (self.cast.pause() if self.is_playing() else self.cast.resume())
            except Exception as e:
                self.message.emit(str(e))
            self._cast_playing = not self.is_playing()
            self.state.emit(self.is_playing())
            return
        if self.current.get("kind") == "radio" and not self.engine.paused:
            self.engine.stop()     # live radio: stop instead of pause, resume = reconnect
            self.state.emit(False)
            return
        if self.current.get("kind") == "radio" and self.engine.paused:
            self._start(self.current)
            return
        self.engine.toggle()
        self.state.emit(not self.engine.paused)

    def is_playing(self):
        if self.cast is not None:
            return getattr(self, "_cast_playing", False)
        return self.current is not None and not self.engine.paused

    def next(self):
        if not self.queue:
            return
        npos = self.pos + 1
        if npos >= len(self.order):
            if self.repeat == "all":
                npos = 0
            else:
                self.engine.stop()
                self.state.emit(False)
                return
        self.pos = npos
        self._start(self.queue[self.order[self.pos]])
        self.queue_changed.emit()

    def prev(self):
        if not self.queue:
            return
        if self.position() > 4 and self.current and self.current.get("kind") != "radio":
            self.seek(0)
            return
        self.pos = max(0, self.pos - 1)
        self._start(self.queue[self.order[self.pos]])
        self.queue_changed.emit()

    def jump_to_upcoming(self, offset):
        npos = self.pos + 1 + offset
        if 0 <= npos < len(self.order):
            self.pos = npos
            self._start(self.queue[self.order[self.pos]])
            self.queue_changed.emit()

    def seek(self, seconds):
        if self.current is None or self.current.get("kind") == "radio":
            return
        if self.cast is not None:
            return
        self.engine.seek(max(0.0, seconds))

    def position(self):
        if self.cast is not None:
            return getattr(self, "_cast_pos", 0)
        return self.engine.position()

    def duration(self):
        return (self.current or {}).get("duration") or 0

    def set_volume(self, v):
        self.engine.set_volume(v / 100.0)
        self.db.set("volume", int(v))
        if self.cast is not None:
            try:
                self.cast.set_volume(v)
            except Exception:
                pass

    def stop(self):
        self.engine.stop()
        self.state.emit(False)

    # ---------------------------------------------------------------- cast (DLNA)
    def set_cast(self, renderer):
        from .. import dlna
        if renderer is None:
            if self.cast:
                self.cast.stop()
            self.cast = None
            if self.current:
                self._start(self.current)
            return
        if self.cast_server is None:
            self.cast_server = dlna.MediaServer()
        self.engine.stop()
        self.cast = renderer
        if self.current:
            self._start_cast(self.current)

    def _start_cast(self, it):
        from .. import dlna
        p = scanner.track_path(it) if it.get("kind") == "track" else (it.get("local_path") or it.get("path"))
        if not p or not os.path.exists(p):
            from ..i18n import tr
            self.message.emit(tr("offline_track"))
            return
        try:
            url = self.cast_server.url_for(p, self.cast.host)
            self.cast.play_url(url, it.title, it.get("artist") or "", dlna.mime_for(p))
            self._cast_playing = True
            self._cast_pos = 0
            self._cast_started = time.time()
        except Exception as e:
            self.message.emit(str(e)[:160])
            self._cast_playing = False
        self.changed.emit(it)
        self.state.emit(self.is_playing())

    # ---------------------------------------------------------------- polling
    def _tick(self):
        for ev in self.engine.events():
            kind, tok = ev[0], ev[1]
            if kind == "started":
                it = self._tokens.get(tok)
                if it is not None and it is not self.current and self._pending_next and self._pending_next[0] == tok:
                    # gapless / crossfade hand-over happened in the audio thread
                    self.pos = self._pending_next[1]
                    self._pending_next = None
                    self.current = it
                    self.counted = False
                    self.changed.emit(it)
                    self.queue_changed.emit()
            elif kind == "ended":
                it = self._tokens.get(tok)
                if it is self.current and not self._pending_next:
                    self._auto_next()
            elif kind == "error":
                self.message.emit(ev[2][:160] if len(ev) > 2 else "error")
                QTimer.singleShot(600, self._auto_next)
        cur = self.current
        if cur is None:
            return
        if self.cast is not None and getattr(self, "_cast_playing", False):
            self._cast_pos = time.time() - getattr(self, "_cast_started", time.time())
        pos = self.position()
        dur = self.duration()
        if not self.counted and cur.get("kind") == "track" and (pos > 30 or (dur and pos > dur * 0.5)):
            self.counted = True
            self.db.x("UPDATE tracks SET plays=plays+1, last_played=? WHERE id=?", (time.time(), cur["id"]))
            self.db.x("INSERT INTO history(track_id, played_at) VALUES(?,?)", (cur["id"], time.time()))
        if cur.get("kind") == "radio":
            src_title = self._radio_title()
            if src_title and src_title != cur.get("now_title"):
                cur["now_title"] = src_title
                self.radio_title.emit(src_title)
        if time.time() - self._last_save > 5 and cur.get("kind") in ("track", "episode"):
            self._last_save = time.time()
            self.save_resume()

    def _radio_title(self):
        src = getattr(self, "_radio_src", None)
        icy = getattr(src, "icy", None) if src is not None else None
        return icy.title if icy is not None else ""

    def _auto_next(self):
        if self.repeat == "one" and self.current is not None:
            self._start(self.current)
            return
        if self.pos + 1 < len(self.order) or self.repeat == "all":
            self.next()
        else:
            self.state.emit(False)

    # ---------------------------------------------------------------- resume
    def save_resume(self):
        cur = self.current
        if not cur or cur.get("kind") not in ("track", "episode"):
            return
        ids = [q.get("id") for q in self.queue if q.get("kind") == "track"][:500]
        data = {"kind": cur.get("kind"), "id": cur.get("id"), "pos": round(self.position(), 1), "queue": ids,
                "index": self.order[self.pos] if 0 <= self.pos < len(self.order) else 0}
        self.db.set("resume", data)
        if cur.get("kind") == "episode":
            self.db.x("UPDATE episodes SET position=? WHERE id=?", (self.position(), cur["id"]))

    def restore_queue(self):
        """Puts the last queue back (paused) so Play continues where Tom left off."""
        r = self.db.get("resume") or {}
        if r.get("kind") != "track" or not r.get("queue"):
            return False
        rows = {row["id"]: row for row in self.db.q(
            f"SELECT * FROM tracks WHERE id IN ({','.join('?' * len(r['queue']))})", r["queue"])}
        items = [track_item(rows[i]) for i in r["queue"] if i in rows]
        if not items:
            return False
        idx = next((k for k, it in enumerate(items) if it["id"] == r.get("id")), 0)
        self.queue = items
        self.order = list(range(len(items)))
        self.pos = idx
        self.current = items[idx]
        self._resume_at = r.get("pos") or 0
        self.changed.emit(self.current)
        self.queue_changed.emit()
        return True

    def play_resumed(self):
        if self.current is None:
            return
        self._start(self.current, seek_to=getattr(self, "_resume_at", 0) or None)
        self._resume_at = 0

    def close(self):
        self.save_resume()
        if self.cast:
            self.cast.stop()
        self.engine.close()
