"""Library scanning: walks music folders (internal or external drives), reads tags, keeps covers."""
import os
import time

from . import tags, volumes
from .app_info import log


def add_folder(db, path):
    path = os.path.abspath(path)
    serial, rel, label = volumes.split(path)
    row = db.one("SELECT id FROM folders WHERE vol_serial=? AND rel=?", (serial, rel))
    if row:
        return row["id"]
    return db.x("INSERT INTO folders(path,vol_serial,rel,label,added) VALUES(?,?,?,?,?)",
                (path, serial, rel, label, time.time()))


def folder_path(row):
    return volumes.locate(row["vol_serial"], row["rel"], row["path"])


def track_path(row):
    return volumes.locate(row["vol_serial"], row["rel_path"], row["path"])


def scan(db, progress=None, stop=lambda: False, folder_ids=None):
    """Scan all (or some) folders. progress(done, total, text). Returns (added, updated, removed, offline)."""
    rows = db.q("SELECT * FROM folders")
    if folder_ids:
        rows = [r for r in rows if r["id"] in folder_ids]
    added = updated = removed = 0
    offline = []
    for fr in rows:
        root = folder_path(fr)
        if not root or not os.path.isdir(root):
            offline.append(fr["path"])
            continue
        files = []
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith(".") and d.lower() not in ("$recycle.bin", "system volume information")]
            for n in fn:
                if os.path.splitext(n)[1].lower() in tags.AUDIO_EXT:
                    files.append(os.path.join(dp, n))
            if stop():
                return added, updated, removed, offline
        known = {}
        for r in db.q("SELECT id, rel_path, mtime, size FROM tracks WHERE folder_id=?", (fr["id"],)):
            known[r["rel_path"]] = r
        seen = set()
        total = len(files)
        batch = []
        for i, p in enumerate(files):
            if stop():
                break
            serial, rel, _label = volumes.split(p)
            seen.add(rel)
            try:
                st = os.stat(p)
            except OSError:
                continue
            k = known.get(rel)
            if k and abs((k["mtime"] or 0) - st.st_mtime) < 1 and k["size"] == st.st_size:
                if i % 50 == 0 and progress:
                    progress(i, total, os.path.basename(p))
                continue
            info = tags.read(p)
            key = tags.art_key_for(info["albumartist"] or info["artist"], info["album"], p)
            if not tags.art_path(key, small=True):
                data = tags.cover_bytes(p)
                if not (data and tags.save_thumbs(key, data)):
                    key = None
            vals = (fr["id"], serial, rel, p, info["title"], info["artist"], info["album"], info["albumartist"],
                    info["genre"], info["year"], info["track_no"], info["disc_no"], info["duration"],
                    info["codec"], info["bitrate"], info["samplerate"], info["bits"], info["channels"],
                    st.st_size, st.st_mtime, info["rg_track"], info["rg_album"], key)
            if k:
                db.x("""UPDATE tracks SET folder_id=?, vol_serial=?, rel_path=?, path=?, title=?, artist=?, album=?,
                        albumartist=?, genre=?, year=?, track_no=?, disc_no=?, duration=?, codec=?, bitrate=?,
                        samplerate=?, bits=?, channels=?, size=?, mtime=?, rg_track=?, rg_album=?, art_key=?,
                        missing=0 WHERE id=?""", vals + (k["id"],), commit=False)
                updated += 1
            else:
                batch.append(vals + (time.time(),))
                added += 1
            if len(batch) >= 100:
                _flush(db, batch)
            if progress and i % 5 == 0:
                progress(i, total, os.path.basename(p))
        _flush(db, batch)
        gone = [known[r]["id"] for r in known if r not in seen]
        if gone and not stop():
            db.many("UPDATE tracks SET missing=1 WHERE id=?", [(g,) for g in gone])
            removed += len(gone)
        db.commit()
    log.info("scan done +%d ~%d -%d offline=%s", added, updated, removed, offline)
    return added, updated, removed, offline


def _flush(db, batch):
    if not batch:
        return
    db.many("""INSERT OR IGNORE INTO tracks(folder_id, vol_serial, rel_path, path, title, artist, album, albumartist,
               genre, year, track_no, disc_no, duration, codec, bitrate, samplerate, bits, channels, size, mtime,
               rg_track, rg_album, art_key, added) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch)
    batch.clear()


def add_single_file(db, p, kind="music"):
    """Used for radio recordings and podcast episodes: put one file straight into the library."""
    serial, rel, _ = volumes.split(p)
    info = tags.read(p)
    st = os.stat(p)
    db.x("""INSERT OR REPLACE INTO tracks(folder_id, vol_serial, rel_path, path, title, artist, album, albumartist,
            genre, year, duration, codec, bitrate, samplerate, size, mtime, added, kind)
            VALUES(0,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
         (serial, rel, p, info["title"], info["artist"], info["album"], info["albumartist"], info["genre"],
          info["year"], info["duration"], info["codec"], info["bitrate"], info["samplerate"], st.st_size,
          st.st_mtime, time.time(), kind))
