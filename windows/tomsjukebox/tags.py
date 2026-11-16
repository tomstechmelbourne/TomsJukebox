"""Read / write song information and cover art with mutagen (MP3, M4A/ALAC, FLAC, OGG, Opus, WAV...)."""
import base64
import hashlib
import io
import os
import re

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TXXX, Frames
from mutagen.mp4 import MP4, MP4Cover

from .app_info import log, sub

AUDIO_EXT = {".mp3", ".m4a", ".m4b", ".aac", ".alac", ".flac", ".wav", ".wave", ".ogg", ".oga",
             ".opus", ".wma", ".aif", ".aiff", ".ape", ".wv", ".mka", ".dsf"}

ID3_MAP = {"title": "TIT2", "artist": "TPE1", "album": "TALB", "albumartist": "TPE2",
           "genre": "TCON", "year": "TDRC", "track_no": "TRCK", "disc_no": "TPOS"}
MP4_MAP = {"title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb", "albumartist": "aART",
           "genre": "\xa9gen", "year": "\xa9day"}
VORBIS_MAP = {"title": "title", "artist": "artist", "album": "album", "albumartist": "albumartist",
              "genre": "genre", "year": "date", "track_no": "tracknumber", "disc_no": "discnumber"}


def _first(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        v = v[0] if v else None
    if v is None:
        return None
    return str(v).strip()


def _int(v):
    v = _first(v)
    if not v:
        return None
    m = re.match(r"\s*(\d+)", v)
    return int(m.group(1)) if m else None


def _gain(v):
    v = _first(v)
    if not v:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)", v)
    return float(m.group(1)) if m else None


def read(path):
    """Returns dict of info. Never raises (bad files give a minimal record)."""
    info = {"title": None, "artist": None, "album": None, "albumartist": None, "genre": None,
            "year": None, "track_no": None, "disc_no": None, "duration": 0.0, "codec": None,
            "bitrate": None, "samplerate": None, "bits": None, "channels": None,
            "rg_track": None, "rg_album": None, "has_art": False}
    try:
        f = mutagen.File(path)
    except Exception as e:  # damaged file
        log.info("tag read failed %s: %s", path, e)
        f = None
    ext = os.path.splitext(path)[1].lower()
    if f is not None:
        i = getattr(f, "info", None)
        if i is not None:
            info["duration"] = float(getattr(i, "length", 0) or 0)
            br = getattr(i, "bitrate", None)
            info["bitrate"] = int(br) if br else None
            info["samplerate"] = getattr(i, "sample_rate", None)
            info["bits"] = getattr(i, "bits_per_sample", None) or None
            info["channels"] = getattr(i, "channels", None)
            codec = getattr(i, "codec", None)
            info["codec"] = (str(codec) if codec else type(f).__name__).upper()
        tags = f.tags
        if isinstance(f, MP4):
            t = tags or {}
            for k, key in MP4_MAP.items():
                info[k] = _first(t.get(key))
            trk = t.get("trkn")
            if trk:
                info["track_no"] = trk[0][0] or None
            dk = t.get("disk")
            if dk:
                info["disc_no"] = dk[0][0] or None
            info["has_art"] = bool(t.get("covr"))
            for k2, field in (("rg_track", "----:com.apple.iTunes:replaygain_track_gain"),
                              ("rg_album", "----:com.apple.iTunes:replaygain_album_gain")):
                if t.get(field):
                    try:
                        info[k2] = _gain(bytes(t[field][0]).decode("utf-8", "ignore"))
                    except Exception:
                        pass
            if info["codec"] in (None, "MP4") or str(info["codec"]).lower().startswith("mp4a"):
                info["codec"] = "AAC"
            if "alac" in str(getattr(f.info, "codec", "")).lower():
                info["codec"] = "ALAC"
        elif tags is not None and hasattr(tags, "getall"):  # ID3 (mp3, wav, aiff)
            for k, key in ID3_MAP.items():
                fr = tags.get(key)
                info[k] = _first(fr.text) if fr is not None and hasattr(fr, "text") else None
            info["track_no"] = _int(info["track_no"])
            info["disc_no"] = _int(info["disc_no"])
            info["has_art"] = bool(tags.getall("APIC"))
            for fr in tags.getall("TXXX"):
                d = (fr.desc or "").lower()
                if d == "replaygain_track_gain":
                    info["rg_track"] = _gain(fr.text)
                elif d == "replaygain_album_gain":
                    info["rg_album"] = _gain(fr.text)
            if ext == ".mp3":
                info["codec"] = "MP3"
        elif tags is not None:  # Vorbis comments (FLAC, OGG, Opus)
            for k, key in VORBIS_MAP.items():
                info[k] = _first(tags.get(key))
            info["track_no"] = _int(info["track_no"])
            info["disc_no"] = _int(info["disc_no"])
            info["rg_track"] = _gain(tags.get("replaygain_track_gain"))
            info["rg_album"] = _gain(tags.get("replaygain_album_gain"))
            info["has_art"] = bool(getattr(f, "pictures", None)) or bool(tags.get("metadata_block_picture"))
        if isinstance(f, FLAC):
            info["codec"] = "FLAC"
        elif ext == ".opus":
            info["codec"] = "OPUS"
        elif ext in (".ogg", ".oga"):
            info["codec"] = "VORBIS"
        elif ext in (".wav", ".wave"):
            info["codec"] = "WAV"
    if isinstance(info["year"], str):
        info["year"] = _int(info["year"])
    if not info["title"]:
        info["title"] = os.path.splitext(os.path.basename(path))[0]
    return info


def cover_bytes(path):
    """Embedded cover, or cover/folder.jpg next to the file."""
    try:
        f = mutagen.File(path)
    except Exception:
        f = None
    data = None
    if f is not None:
        try:
            if isinstance(f, MP4):
                c = (f.tags or {}).get("covr")
                if c:
                    data = bytes(c[0])
            elif isinstance(f, FLAC) and f.pictures:
                data = f.pictures[0].data
            elif f.tags is not None and hasattr(f.tags, "getall"):
                ap = f.tags.getall("APIC")
                if ap:
                    data = ap[0].data
            elif f.tags is not None and f.tags.get("metadata_block_picture"):
                pic = Picture(base64.b64decode(f.tags["metadata_block_picture"][0]))
                data = pic.data
        except Exception as e:
            log.info("cover read failed %s: %s", path, e)
    if data:
        return data
    folder = os.path.dirname(path)
    try:
        names = {n.lower(): n for n in os.listdir(folder)}
    except OSError:
        return None
    for cand in ("cover.jpg", "folder.jpg", "front.jpg", "cover.png", "folder.png", "albumart.jpg"):
        if cand in names:
            try:
                with open(os.path.join(folder, names[cand]), "rb") as fh:
                    return fh.read()
            except OSError:
                return None
    return None


def art_key_for(albumartist, album, path):
    base = f"{(albumartist or '').lower()}|{(album or '').lower()}" if album else path.lower()
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]


def save_thumbs(key, data):
    """Store a 600 px and a 160 px JPEG copy of a cover. Returns True on success."""
    from PIL import Image
    d = sub("art")
    big, small = d / f"{key}.jpg", d / f"{key}_s.jpg"
    if big.exists() and small.exists():
        return True
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((600, 600))
        im.save(big, "JPEG", quality=88)
        im.thumbnail((160, 160))
        im.save(small, "JPEG", quality=85)
        return True
    except Exception as e:
        log.info("thumb failed: %s", e)
        return False


def art_path(key, small=False):
    if not key:
        return None
    p = sub("art") / (f"{key}_s.jpg" if small else f"{key}.jpg")
    return str(p) if p.exists() else None


def write(path, values, cover=None):
    """values: dict with any of title, artist, album, albumartist, genre, year, track_no, disc_no.
    cover: JPEG/PNG bytes or None. Raises on failure."""
    f = mutagen.File(path)
    if f is None:
        raise ValueError("unsupported file")
    if isinstance(f, MP4):
        if f.tags is None:
            f.add_tags()
        for k, key in MP4_MAP.items():
            if k in values:
                v = values[k]
                if v in (None, ""):
                    f.tags.pop(key, None)
                else:
                    f.tags[key] = [str(v)]
        if "track_no" in values and values["track_no"]:
            f.tags["trkn"] = [(int(values["track_no"]), 0)]
        if "disc_no" in values and values["disc_no"]:
            f.tags["disk"] = [(int(values["disc_no"]), 0)]
        if cover:
            fmt = MP4Cover.FORMAT_PNG if cover[:4] == b"\x89PNG" else MP4Cover.FORMAT_JPEG
            f.tags["covr"] = [MP4Cover(cover, imageformat=fmt)]
        f.save()
        return
    ext = os.path.splitext(path)[1].lower()
    if ext in (".mp3", ".wav", ".aif", ".aiff"):
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()
        for k, key in ID3_MAP.items():
            if k in values:
                v = values[k]
                tags.delall(key)
                if v not in (None, ""):
                    tags.add(Frames[key](encoding=3, text=[str(v)]))
        if cover:
            tags.delall("APIC")
            mime = "image/png" if cover[:4] == b"\x89PNG" else "image/jpeg"
            tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=cover))
        tags.save(path)
        return
    # Vorbis-comment formats
    if f.tags is None:
        f.add_tags()
    for k, key in VORBIS_MAP.items():
        if k in values:
            v = values[k]
            if v in (None, ""):
                if key in f.tags:
                    del f.tags[key]
            else:
                f.tags[key] = [str(v)]
    if cover:
        pic = Picture()
        pic.type = 3
        pic.mime = "image/png" if cover[:4] == b"\x89PNG" else "image/jpeg"
        pic.data = cover
        if isinstance(f, FLAC):
            f.clear_pictures()
            f.add_picture(pic)
        else:
            f.tags["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
    f.save()


def write_replaygain_txxx(path, gain):  # kept small: used by tests only
    tags = ID3(path)
    tags.add(TXXX(encoding=3, desc="replaygain_track_gain", text=[f"{gain:.2f} dB"]))
    tags.save(path)
