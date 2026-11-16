"""SQLite storage for Tom's Jukebox (library, playlists, radio, podcasts, settings, history)."""
import json
import sqlite3
import threading
import time

from . import app_info

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS folders(
    id INTEGER PRIMARY KEY, path TEXT, vol_serial TEXT, rel TEXT, label TEXT, added REAL);
CREATE TABLE IF NOT EXISTS tracks(
    id INTEGER PRIMARY KEY,
    folder_id INTEGER, vol_serial TEXT, rel_path TEXT, path TEXT,
    title TEXT, artist TEXT, album TEXT, albumartist TEXT, genre TEXT, year INTEGER,
    track_no INTEGER, disc_no INTEGER, duration REAL,
    codec TEXT, bitrate INTEGER, samplerate INTEGER, bits INTEGER, channels INTEGER,
    size INTEGER, mtime REAL, added REAL,
    plays INTEGER DEFAULT 0, last_played REAL, fav INTEGER DEFAULT 0,
    rg_track REAL, rg_album REAL, art_key TEXT, kind TEXT DEFAULT 'music',
    missing INTEGER DEFAULT 0,
    UNIQUE(vol_serial, rel_path));
CREATE INDEX IF NOT EXISTS ix_tracks_album ON tracks(albumartist, album);
CREATE INDEX IF NOT EXISTS ix_tracks_artist ON tracks(artist);
CREATE TABLE IF NOT EXISTS playlists(
    id INTEGER PRIMARY KEY, name TEXT, smart_rules TEXT, created REAL, sort INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS playlist_items(
    playlist_id INTEGER, pos INTEGER, track_id INTEGER);
CREATE TABLE IF NOT EXISTS history(track_id INTEGER, played_at REAL);
CREATE TABLE IF NOT EXISTS stations(
    id INTEGER PRIMARY KEY, name TEXT, grp TEXT, state TEXT, city TEXT, url TEXT, query TEXT,
    homepage TEXT, codec TEXT, bitrate INTEGER, fav INTEGER DEFAULT 0, custom INTEGER DEFAULT 0,
    builtin_key TEXT UNIQUE, sort INTEGER DEFAULT 0, last_ok REAL);
CREATE TABLE IF NOT EXISTS podcasts(
    id INTEGER PRIMARY KEY, title TEXT, author TEXT, feed TEXT UNIQUE, image TEXT, art_key TEXT,
    auto_dl INTEGER DEFAULT 1, last_check REAL);
CREATE TABLE IF NOT EXISTS episodes(
    id INTEGER PRIMARY KEY, podcast_id INTEGER, guid TEXT, title TEXT, url TEXT, published REAL,
    duration REAL, local_path TEXT, position REAL DEFAULT 0, done INTEGER DEFAULT 0,
    UNIQUE(podcast_id, guid));
CREATE TABLE IF NOT EXISTS schedules(
    id INTEGER PRIMARY KEY, station_id INTEGER, start_hm TEXT, minutes INTEGER, days TEXT,
    once_date TEXT, fmt TEXT, enabled INTEGER DEFAULT 1, last_run TEXT);
CREATE TABLE IF NOT EXISTS recordings(
    id INTEGER PRIMARY KEY, station TEXT, path TEXT, started REAL, seconds REAL, fmt TEXT);
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY, at REAL, text_en TEXT, text_vi TEXT, read INTEGER DEFAULT 0, key TEXT);
"""

DEFAULTS = {
    "theme": "soft",            # Mềm Mại (One UI-like) is the default for Tom's Jukebox
    "lang": "en",
    "font_step": 0,
    "dark": 0,
    "volume": 80,
    "eq_on": 0,
    "eq_preset": "flat",
    "eq_gains": [0.0] * 10,
    "crossfade": 0,
    "gapless": 1,
    "replaygain": "track",      # off | track | album
    "bar_color": "#FBB040",
    "shuffle": 0,
    "repeat": "off",            # off | all | one
    "resume": {},
    "lyrics_online": 1,
    "musicbrainz": 1,
    "location_windows": 1,
    "location_ip": 1,
    "radio_state": "",
    "radio_state_manual": 0,
    "rec_fmt": "original",
    "rec_dir": "",
    "rec_split": 0,
    "backup_dir": "",
    "last_backup": 0,
    "toms_disc_path": "",
    "podcast_dir": "",
    "mini_on_top": 1,
    "first_run_done": 0,
    "view_albums": "grid",
    "col_widths": {},
}


class DB:
    def __init__(self, path=None):
        self.path = str(path or (app_info.data_dir() / "jukebox.db"))
        self.lock = threading.RLock()
        self.con = sqlite3.connect(self.path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA foreign_keys=OFF")
        self.con.executescript(SCHEMA)
        self._settings = {}
        for r in self.con.execute("SELECT key, value FROM settings"):
            try:
                self._settings[r["key"]] = json.loads(r["value"])
            except ValueError:
                pass
        cur = self.meta("schema")
        if cur is None:
            self.set_meta("schema", str(SCHEMA_VERSION))
        self.undo_stack = []
        self.con.commit()

    # ---- basic helpers
    def q(self, sql, args=()):
        with self.lock:
            return self.con.execute(sql, args).fetchall()

    def one(self, sql, args=()):
        with self.lock:
            return self.con.execute(sql, args).fetchone()

    def x(self, sql, args=(), commit=True):
        with self.lock:
            cur = self.con.execute(sql, args)
            if commit:
                self.con.commit()
            return cur.lastrowid

    def many(self, sql, seq):
        with self.lock:
            self.con.executemany(sql, seq)
            self.con.commit()

    def commit(self):
        with self.lock:
            self.con.commit()

    def meta(self, key):
        r = self.one("SELECT value FROM meta WHERE key=?", (key,))
        return r["value"] if r else None

    def set_meta(self, key, value):
        self.x("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value))

    # ---- settings
    def get(self, key, default=None):
        if key in self._settings:
            return self._settings[key]
        if default is not None:
            return default
        d = DEFAULTS.get(key)
        return json.loads(json.dumps(d)) if isinstance(d, (dict, list)) else d

    def set(self, key, value):
        self._settings[key] = value
        self.x("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, json.dumps(value)))

    # ---- undo (playlist edits, tag edits, removals)
    def push_undo(self, label, statements):
        """statements: list of (sql, args) that restore the previous state."""
        self.undo_stack.append((label, statements))
        del self.undo_stack[:-50]

    def undo(self):
        if not self.undo_stack:
            return None
        label, statements = self.undo_stack.pop()
        with self.lock:
            for sql, args in statements:
                self.con.execute(sql, args)
            self.con.commit()
        return label

    # ---- messages
    def add_message(self, en, vi, key=None):
        if key and self.one("SELECT id FROM messages WHERE key=? AND read=0", (key,)):
            return
        self.x("INSERT INTO messages(at,text_en,text_vi,key) VALUES(?,?,?,?)", (time.time(), en, vi, key))

    def unread_count(self):
        return self.one("SELECT COUNT(*) c FROM messages WHERE read=0")["c"]

    def close(self):
        with self.lock:
            try:
                self.con.commit()
                self.con.close()
            except sqlite3.Error:
                pass

    def safe_copy(self, dest):
        """Consistent copy of the database (used by backup)."""
        with self.lock:
            out = sqlite3.connect(str(dest))
            self.con.backup(out)
            out.close()
