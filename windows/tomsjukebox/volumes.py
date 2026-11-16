"""External drive support: remember files by drive serial number + path inside the drive,
so a drive that comes back with a different letter (E: -> F:) is still recognised."""
import os
import sys
import time
from pathlib import Path

IS_WIN = sys.platform.startswith("win")
_cache = {"t": 0.0, "map": {}}


def _win_drives():
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.windll.kernel32
    out = {}
    mask = k32.GetLogicalDrives()
    for i in range(26):
        if not mask & (1 << i):
            continue
        root = f"{chr(65 + i)}:\\"
        dtype = k32.GetDriveTypeW(root)
        if dtype in (0, 1, 5):   # unknown, no root, CD-ROM (CDs are handled separately)
            continue
        serial = wintypes.DWORD()
        name = ctypes.create_unicode_buffer(261)
        old = k32.SetErrorMode(1)   # no "insert disk" pop-ups
        try:
            ok = k32.GetVolumeInformationW(root, name, 261, ctypes.byref(serial), None, None, None, 0)
        finally:
            k32.SetErrorMode(old)
        if ok:
            out[f"{serial.value:08X}"] = (root, name.value, dtype)
    return out


def drive_map(force=False):
    """serial -> (root, label, type). Cached for 3 seconds."""
    if not IS_WIN:
        return {}
    now = time.time()
    if force or now - _cache["t"] > 3:
        try:
            _cache["map"] = _win_drives()
        except Exception:
            _cache["map"] = {}
        _cache["t"] = now
    return _cache["map"]


def split(path: str):
    """Absolute path -> (vol_serial, rel_path, label)."""
    p = os.path.abspath(path)
    if IS_WIN:
        drv = os.path.splitdrive(p)[0].upper()
        for serial, (root, label, _t) in drive_map().items():
            if root.rstrip("\\").upper() == drv:
                return serial, p[len(drv):].lstrip("\\/"), label
        return "", p, ""
    return "", p, ""


def locate(vol_serial: str, rel_path: str, fallback: str = ""):
    """Current absolute path, or None when the drive is not plugged in."""
    if not vol_serial:
        return rel_path if os.path.exists(rel_path) else (fallback if fallback and os.path.exists(fallback) else None)
    info = drive_map().get(vol_serial)
    if not info:
        return None
    return str(Path(info[0]) / rel_path)


def online(vol_serial: str) -> bool:
    return (not vol_serial) or (vol_serial in drive_map())


def drive_label(vol_serial: str) -> str:
    info = drive_map().get(vol_serial)
    if not info:
        return ""
    return f"{info[1] or 'Drive'} ({info[0].rstrip(chr(92))})"
