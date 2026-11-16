"""Backup / Restore (one zip: database, covers, lyrics, settings). Weekly automatic backup, keep 5."""
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

from . import app_info

KEEP = 5


def default_dir(db):
    d = db.get("backup_dir") or ""
    return Path(d) if d else app_info.data_dir() / "Backups"


def make(db, dest_dir=None, label="SaoLuu"):
    dest_dir = Path(dest_dir or default_dir(db))
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = dest_dir / f"TomsJukebox-{label}-{stamp}.zip"
    with tempfile.TemporaryDirectory() as td:
        dbcopy = Path(td) / "jukebox.db"
        db.safe_copy(dbcopy)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(dbcopy, "jukebox.db")
            for sub in ("art", "lyrics", "podcast_art"):
                p = app_info.data_dir() / sub
                if p.exists():
                    for f in p.rglob("*"):
                        if f.is_file():
                            z.write(f, f"{sub}/{f.relative_to(p)}")
            z.writestr("backup_info.json", json.dumps({
                "app": app_info.APP_NAME, "version": app_info.VERSION, "made": stamp,
                "data_dir": str(app_info.data_dir()), "user": os.environ.get("USERNAME", "")}, ensure_ascii=False))
    db.set("last_backup", time.time())
    prune(dest_dir)
    return out


def prune(dest_dir):
    files = sorted(Path(dest_dir).glob("TomsJukebox-Tu*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[KEEP:]:
        try:
            f.unlink()
        except OSError:
            pass


def restore(db, zip_path):
    """Saves the current data as one more backup first, then replaces data from the zip.
    The caller must restart the program afterwards."""
    with zipfile.ZipFile(zip_path) as z:
        if "jukebox.db" not in z.namelist():
            raise ValueError("not a Tom's Jukebox backup")
    make(db, label="TruocKhiKhoiPhuc")
    data = app_info.data_dir()
    db.close()
    with zipfile.ZipFile(zip_path) as z:
        for sub in ("art", "lyrics", "podcast_art"):
            shutil.rmtree(data / sub, ignore_errors=True)
        for wal in ("jukebox.db-wal", "jukebox.db-shm"):
            try:
                (data / wal).unlink()
            except OSError:
                pass
        z.extractall(data)
    return True


def auto_due(db, days=7):
    return time.time() - float(db.get("last_backup") or 0) > days * 86400


def auto_backup(db):
    try:
        return make(db, label="TuDong")
    except Exception as e:
        app_info.log.warning("auto backup failed: %s", e)
        return None


def restart_program():
    os.execl(sys.executable, sys.executable, *sys.argv)
