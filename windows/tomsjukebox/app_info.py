"""Program identity, folders and logging for Tom's Jukebox."""
import logging
import os
import sys
from pathlib import Path

APP_NAME = "Tom's Jukebox"
APP_EXE = "TomsJukebox"
VERSION = "0.9.6-beta"
BRAND = "Tom's Technology Solutions"
SLOGAN = "Focus On One Thing And Do It Well"
FEEDBACK_EMAIL = "tomstechmelbourne@gmail.com"

DEMO = "--demo" in sys.argv


def base_dir() -> Path:
    """Folder with assets (works for source run and PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def asset(name: str) -> str:
    return str(base_dir() / "assets" / name)


def data_dir() -> Path:
    root = os.environ.get("APPDATA") or str(Path.home() / ".config")
    name = APP_NAME + (" Demo" if DEMO else "")
    override = os.environ.get("TOMSJUKEBOX_DATA")
    p = Path(override) if override else Path(root) / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def sub(name: str) -> Path:
    p = data_dir() / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def documents_dir() -> Path:
    home = Path.home()
    for cand in (home / "Documents", home / "OneDrive" / "Documents", home):
        if cand.exists():
            return cand
    return home


def default_recordings_dir() -> Path:
    p = documents_dir() / APP_NAME / ("Recordings Demo" if DEMO else "Radio Recordings")
    return p


def shared_send_dir() -> Path:
    """Shared hand-off folder used by every Tom's Technology Solutions program."""
    return documents_dir() / BRAND / "Gui Sang"


_log_ready = False


def setup_logging():
    global _log_ready
    if _log_ready:
        return
    _log_ready = True
    logf = data_dir() / "TomsJukebox.log"
    try:
        if logf.exists() and logf.stat().st_size > 2_000_000:
            logf.replace(logf.with_suffix(".old.log"))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(logf, encoding="utf-8")]
        + ([logging.StreamHandler()] if sys.stderr and "--selftest" in sys.argv else []),
    )
    logging.getLogger("tomsjukebox").info("%s %s start, data=%s", APP_NAME, VERSION, data_dir())


log = logging.getLogger("tomsjukebox")
