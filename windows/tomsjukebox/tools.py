"""Library tools: Find Duplicates (show only, never delete), Check Files (damaged, missing cover/info,
fake lossless = MP3 renamed or converted to FLAC), Smart Playlists, Tom's Reel link."""
import glob
import json
import os
import re
import sqlite3
import unicodedata

import numpy as np

from . import scanner
from .app_info import log


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    s = re.sub(r"\b(feat|ft|remaster(ed)?|live|version)\b.*", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ------------------------------------------------------------------ duplicates
def find_duplicates(db):
    """Groups of tracks with the same artist + title and length within 3 s."""
    rows = db.q("SELECT id, title, artist, album, duration, codec, bitrate, bits, samplerate, path, vol_serial, rel_path "
                "FROM tracks WHERE missing=0 AND kind='music'")
    buckets = {}
    for r in rows:
        k = (norm(r["artist"]), norm(r["title"]))
        if not k[1]:
            continue
        buckets.setdefault(k, []).append(r)
    groups = []
    for k, items in buckets.items():
        if len(items) < 2:
            continue
        items = sorted(items, key=lambda r: r["duration"] or 0)
        cur = [items[0]]
        for r in items[1:]:
            if abs((r["duration"] or 0) - (cur[-1]["duration"] or 0)) <= 3:
                cur.append(r)
            else:
                if len(cur) > 1:
                    groups.append(cur)
                cur = [r]
        if len(cur) > 1:
            groups.append(cur)
    # best copy first: lossless, then bitrate
    def quality(r):
        lossless = (r["codec"] or "").upper() in ("FLAC", "ALAC", "WAV", "AIFF")
        return (lossless, r["bits"] or 0, r["bitrate"] or 0)
    return [sorted(g, key=quality, reverse=True) for g in groups]


# ------------------------------------------------------------------ file check
def lossy_cutoff_khz(path, seconds=20):
    """Estimate the highest frequency with real content. MP3/AAC usually stop at 16-19 kHz;
    true CD-quality FLAC goes to ~21-22 kHz. Returns kHz or None."""
    import av
    try:
        c = av.open(path)
        st = next(s for s in c.streams if s.type == "audio")
        rs = av.AudioResampler(format="flt", layout="mono", rate=44100)
        chunks, total = [], 0
        dur = float(st.duration * st.time_base) if st.duration else 0
        if dur > 60:
            c.seek(int(dur * 0.3 * 1_000_000))
        for fr in c.decode(st):
            for o in rs.resample(fr):
                a = o.to_ndarray().reshape(-1)
                chunks.append(a)
                total += len(a)
            if total > seconds * 44100:
                break
        c.close()
    except Exception as e:
        log.info("spectrum check failed %s: %s", path, e)
        return None
    if total < 44100:
        return None
    x = np.concatenate(chunks)
    n = 4096
    frames = len(x) // n
    if frames < 4:
        return None
    win = np.hanning(n)
    spec = np.zeros(n // 2 + 1)
    for i in range(frames):
        spec += np.abs(np.fft.rfft(x[i * n:(i + 1) * n] * win)) ** 2
    db_ = 10 * np.log10(spec / frames + 1e-20)
    freqs = np.fft.rfftfreq(n, 1 / 44100)
    ref = np.median(db_[(freqs > 1000) & (freqs < 4000)])
    if not np.isfinite(ref):
        return None
    # highest frequency still within 55 dB of the mid-band level
    above = np.where(db_ > ref - 55)[0]
    if not len(above):
        return None
    return float(freqs[above[-1]] / 1000)


def check_files(db, progress=None, stop=lambda: False, deep=True):
    """Returns list of (track_row, problem_code, detail)."""
    import av
    rows = db.q("SELECT * FROM tracks WHERE missing=0 AND kind='music' ORDER BY albumartist, album, track_no")
    out = []
    for i, r in enumerate(rows):
        if stop():
            break
        if progress and i % 3 == 0:
            progress(i, len(rows), r["title"] or "")
        p = scanner.track_path(r)
        if not p:
            continue
        if not os.path.exists(p):
            out.append((r, "missing_file", p))
            continue
        if not r["art_key"]:
            out.append((r, "no_cover", ""))
        if not r["artist"] or not r["album"]:
            out.append((r, "no_info", ""))
        if (r["duration"] or 0) < 1:
            out.append((r, "damaged", "length 0"))
            continue
        if deep:
            try:
                c = av.open(p)
                st = next(s for s in c.streams if s.type == "audio")
                n = 0
                for _f in c.decode(st):
                    n += 1
                    if n > 20:
                        break
                if r["duration"] > 30:
                    c.seek(int((r["duration"] - 8) * 1_000_000))
                    for _f in c.decode(st):
                        n += 1
                        if n > 40:
                            break
                c.close()
            except Exception as e:
                out.append((r, "damaged", str(e)[:120]))
                continue
            if (r["codec"] or "").upper() in ("FLAC", "ALAC", "WAV") and (r["samplerate"] or 44100) >= 44100:
                k = lossy_cutoff_khz(p)
                if k is not None and k < 19.0:
                    out.append((r, "fake_lossless", f"{k:.1f} kHz"))
    if progress:
        progress(len(rows), len(rows), "")
    return out


# ------------------------------------------------------------------ smart playlists
SMART_FIELDS = {
    "artist": "artist", "album": "album", "genre": "genre", "title": "title", "year": "year",
    "codec": "codec", "plays": "plays", "fav": "fav", "added_days": "added", "played_days": "last_played",
    "duration": "duration", "folder": "path",
}


def smart_sql(rules):
    """rules = {"match": "all"/"any", "rules": [{"field","op","value"}], "order": "...", "limit": N}"""
    import time
    parts, args = [], []
    for r in rules.get("rules", []):
        f, op, v = r.get("field"), r.get("op"), r.get("value")
        col = SMART_FIELDS.get(f)
        if not col:
            continue
        if f in ("added_days", "played_days"):
            try:
                cutoff = time.time() - float(v) * 86400
            except (TypeError, ValueError):
                continue
            parts.append(f"{col} >= ?" if op in ("within", "<=") else f"({col} IS NULL OR {col} < ?)")
            args.append(cutoff)
        elif op == "contains":
            parts.append(f"{col} LIKE ?")
            args.append(f"%{v}%")
        elif op == "not_contains":
            parts.append(f"({col} IS NULL OR {col} NOT LIKE ?)")
            args.append(f"%{v}%")
        elif op in ("=", "!=", ">", "<", ">=", "<="):
            parts.append(f"{col} {op} ?")
            args.append(v)
        elif op == "is_empty":
            parts.append(f"({col} IS NULL OR {col} = '')")
    joiner = " OR " if rules.get("match") == "any" else " AND "
    where = "missing=0 AND kind='music'" + ((" AND (" + joiner.join(parts) + ")") if parts else "")
    order = {"plays": "plays DESC", "recent": "added DESC", "random": "RANDOM()", "artist": "artist, album, track_no",
             "last_played": "last_played DESC", "title": "title"}.get(rules.get("order", "artist"), "artist, album, track_no")
    limit = int(rules.get("limit") or 0)
    sql = f"SELECT * FROM tracks WHERE {where} ORDER BY {order}" + (f" LIMIT {limit}" if limit > 0 else "")
    return sql, args


SMART_TEMPLATES = [
    ("Most Played", "Nghe Nhiều Nhất", {"match": "all", "rules": [{"field": "plays", "op": ">", "value": 0}], "order": "plays", "limit": 50}),
    ("Added In The Last 30 Days", "Thêm Trong 30 Ngày", {"match": "all", "rules": [{"field": "added_days", "op": "within", "value": 30}], "order": "recent"}),
    ("FLAC Never Played", "FLAC Chưa Nghe Bao Giờ", {"match": "all", "rules": [{"field": "codec", "op": "=", "value": "FLAC"}, {"field": "plays", "op": "=", "value": 0}], "order": "random"}),
    ("Favourites", "Yêu Thích", {"match": "all", "rules": [{"field": "fav", "op": "=", "value": 1}], "order": "artist"}),
    ("Not Played For 6 Months", "Lâu Chưa Nghe (6 Tháng)", {"match": "all", "rules": [{"field": "played_days", "op": "older", "value": 180}, {"field": "plays", "op": ">", "value": 0}], "order": "random", "limit": 100}),
]


# ------------------------------------------------------------------ Tom's Reel link
class ReelLink:
    """Reads Tom's Reel collection (read only) to show whether Tom owns an album on CD / vinyl / cassette.
    Works with the Reel database directly, or with a Reel backup zip copied over (for the phone)."""

    def __init__(self, extra_db=None):
        self.index = {}
        self.source = None
        self.count = 0
        self.load(extra_db)

    def candidates(self):
        roots = []
        ap = os.environ.get("APPDATA")
        if ap:
            roots.append(os.path.join(ap, "Tom's Reel"))
        roots.append(os.path.join(os.path.expanduser("~"), ".config", "Tom's Reel"))
        out = []
        for r in roots:
            out += glob.glob(os.path.join(r, "*.db")) + glob.glob(os.path.join(r, "*.sqlite"))
        return out

    def load(self, extra_db=None):
        self.index.clear()
        paths = ([extra_db] if extra_db else []) + self.candidates()
        for p in paths:
            if p and os.path.exists(p) and self._load_db(p):
                self.source = p
                break

    def _load_db(self, path):
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            best = None
            for t in tables:
                cols = [r[1].lower() for r in con.execute(f'PRAGMA table_info("{t}")')]
                if "title" in cols and ("format" in cols or "media" in cols or "kind" in cols):
                    best = (t, cols)
                    break
            if not best:
                con.close()
                return False
            t, cols = best
            artist_col = next((c for c in ("artist", "artists", "creator", "director") if c in cols), None)
            fmt_col = next(c for c in ("format", "media", "kind") if c in cols)
            sel = f'SELECT title, {fmt_col} AS fmt' + (f', {artist_col} AS artist' if artist_col else ", '' AS artist") + f' FROM "{t}"'
            for r in con.execute(sel):
                key = norm(r["title"])
                if not key:
                    continue
                self.index.setdefault(key, []).append((norm(r["artist"] or ""), str(r["fmt"] or "")))
                self.count += 1
            con.close()
            log.info("Tom's Reel linked: %s (%d)", path, self.count)
            return True
        except Exception as e:
            log.info("Reel link failed for %s: %s", path, e)
            return False

    def formats_for(self, album, artist):
        """Formats Tom owns for this album (e.g. ['CD', 'Vinyl'])."""
        if not album:
            return []
        hits = self.index.get(norm(album), [])
        a = norm(artist)
        out = []
        for ar, fmt in hits:
            if not a or not ar or a in ar or ar in a:
                if fmt and fmt not in out:
                    out.append(fmt)
        return out


def export_m3u(rows_paths, dest, title=None):
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        if title:
            fh.write(f"#PLAYLIST:{title}\n")
        for row, p in rows_paths:
            if not p:
                continue
            fh.write(f"#EXTINF:{int(row['duration'] or 0)},{row['artist'] or ''} - {row['title'] or ''}\n{p}\n")
    return dest


def import_m3u(path):
    base = os.path.dirname(path)
    out = []
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line if os.path.isabs(line) else os.path.normpath(os.path.join(base, line))
            out.append(p)
    return out


def dumps(o):
    return json.dumps(o, ensure_ascii=False)
