"""Optional online look-ups: MusicBrainz (+ Cover Art Archive), LRCLIB lyrics, iTunes podcast search.
Only song names / disc IDs are sent, never Tom's files or personal data."""
import json
import re
import threading
import time
import urllib.parse
import urllib.request

from . import app_info
from .app_info import log

UA = f"TomsJukebox/{app_info.VERSION} ( https://github.com/tomstechmelbourne )"
_mb_lock = threading.Lock()
_mb_last = [0.0]


def get(url, timeout=15, raw=False, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else json.loads(data.decode("utf-8", "replace"))


# ------------------------------------------------------------------ MusicBrainz
def _mb(path, params):
    with _mb_lock:  # MusicBrainz asks for at most 1 request per second
        wait = 1.1 - (time.time() - _mb_last[0])
        if wait > 0:
            time.sleep(wait)
        _mb_last[0] = time.time()
    params = dict(params, fmt="json")
    return get("https://musicbrainz.org/ws/2/" + path + "?" + urllib.parse.urlencode(params))


def _credit(ac):
    return "".join((c.get("name") or c.get("artist", {}).get("name", "")) + (c.get("joinphrase") or "") for c in ac or [])


def mb_disc(disc_id, toc_str=None):
    """Audio CD look-up -> dict(album, artist, year, mbid, tracks=[titles...]) or None."""
    try:
        params = {"inc": "recordings+artist-credits"}
        if toc_str:
            params["toc"] = toc_str
        d = _mb("discid/" + disc_id, params)
    except Exception as e:
        log.info("mb disc lookup failed: %s", e)
        return None
    rels = d.get("releases") or []
    if not rels:
        return None
    rel = rels[0]
    tracks = []
    for med in rel.get("media", []):
        if any(dd.get("id") == disc_id for dd in med.get("discs", [])) or len(rel.get("media", [])) == 1:
            for t in med.get("tracks", []):
                tracks.append({"title": t.get("title"), "artist": _credit(t.get("artist-credit")) or _credit(rel.get("artist-credit"))})
            break
    return {"album": rel.get("title"), "artist": _credit(rel.get("artist-credit")),
            "year": (rel.get("date") or "")[:4], "mbid": rel.get("id"), "tracks": tracks}


def mb_search(artist, title, album=None):
    """Recording search -> list of candidates (title, artist, album, year, track_no, release_id)."""
    q = f'recording:"{title}"'
    if artist:
        q += f' AND artist:"{artist}"'
    if album:
        q += f' AND release:"{album}"'
    try:
        d = _mb("recording", {"query": q, "limit": 8})
    except Exception as e:
        log.info("mb search failed: %s", e)
        return []
    out = []
    for r in d.get("recordings", []):
        for rel in (r.get("releases") or [])[:2]:
            tn = None
            try:
                tn = int(rel["media"][0]["track"][0]["number"])
            except Exception:
                pass
            out.append({"title": r.get("title"), "artist": _credit(r.get("artist-credit")),
                        "album": rel.get("title"), "year": (rel.get("date") or "")[:4],
                        "track_no": tn, "release_id": rel.get("id"), "score": r.get("score", 0)})
    return out


def cover_art(release_id, size=500):
    try:
        return get(f"https://coverartarchive.org/release/{release_id}/front-{size}", raw=True, timeout=20)
    except Exception as e:
        log.info("cover art failed: %s", e)
        return None


# ------------------------------------------------------------------ Lyrics
def lrclib(artist, title, album=None, duration=None):
    params = {"artist_name": artist or "", "track_name": title or ""}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = int(duration)
    try:
        d = get("https://lrclib.net/api/get?" + urllib.parse.urlencode(params), timeout=12)
    except Exception:
        try:
            res = get("https://lrclib.net/api/search?" + urllib.parse.urlencode(
                {"track_name": title or "", "artist_name": artist or ""}), timeout=12)
            d = res[0] if res else None
        except Exception as e:
            log.info("lyrics lookup failed: %s", e)
            return None
    if not d:
        return None
    return d.get("syncedLyrics") or d.get("plainLyrics")


def parse_lrc(text):
    """-> (timed: list[(seconds, line)], plain: str)"""
    timed = []
    plain = []
    for line in (text or "").splitlines():
        stamps = re.findall(r"\[(\d+):(\d+(?:\.\d+)?)\]", line)
        words = re.sub(r"\[[^\]]*\]", "", line).strip()
        if stamps:
            for m, s in stamps:
                timed.append((int(m) * 60 + float(s), words))
        elif not re.match(r"^\[[a-z]+:", line.strip()):
            plain.append(line)
    timed.sort()
    return timed, "\n".join(plain).strip()


# ------------------------------------------------------------------ Podcasts
def podcast_search(term):
    try:
        d = get("https://itunes.apple.com/search?" + urllib.parse.urlencode(
            {"media": "podcast", "term": term, "limit": 25, "country": "AU"}))
    except Exception as e:
        log.info("podcast search failed: %s", e)
        return []
    return [{"title": r.get("collectionName"), "author": r.get("artistName"), "feed": r.get("feedUrl"),
             "image": r.get("artworkUrl600") or r.get("artworkUrl100")} for r in d.get("results", []) if r.get("feedUrl")]


def podcast_feed(url):
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    raw = get(url, raw=True, timeout=25, headers={"Accept": "*/*"})
    root = ET.fromstring(raw)
    ch = root.find("channel")
    if ch is None:
        raise ValueError("not a podcast feed")
    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
    img = ch.find("itunes:image", ns)
    info = {"title": (ch.findtext("title") or "").strip(), "author": ch.findtext("itunes:author", "", ns),
            "image": img.get("href") if img is not None else (ch.findtext("image/url") or ""), "episodes": []}
    for it in ch.findall("item"):
        enc = it.find("enclosure")
        if enc is None or not enc.get("url"):
            continue
        pub = 0.0
        try:
            pub = parsedate_to_datetime(it.findtext("pubDate")).timestamp()
        except Exception:
            pass
        dur = 0.0
        ds = it.findtext("itunes:duration", "", ns) or ""
        try:
            parts = [float(p) for p in ds.split(":")]
            for p in parts:
                dur = dur * 60 + p
        except ValueError:
            pass
        hq, best = "", -1
        for alt in it.findall("{https://podcastindex.org/namespace/1.0}alternateEnclosure"):
            try:
                br = float(alt.get("bitrate") or 0)
            except ValueError:
                br = 0
            src = alt.find("{https://podcastindex.org/namespace/1.0}source")
            u = src.get("uri") if src is not None else ""
            if u.startswith("http") and br > best and "audio" in (alt.get("type") or "audio"):
                hq, best = u, br
        info["episodes"].append({"guid": it.findtext("guid") or enc.get("url"), "title": (it.findtext("title") or "").strip(),
                                 "url": enc.get("url"), "published": pub, "duration": dur, "hq": hq})
    info["episodes"].sort(key=lambda e: -(e["published"] or 0))
    return info


def download(url, dest, progress=None, stop=lambda: False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = str(dest) + ".part"
    with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as fh:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            if stop():
                raise InterruptedError()
            chunk = r.read(65536)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
            if progress:
                progress(got, total)
    import os
    os.replace(tmp, dest)
    return dest
