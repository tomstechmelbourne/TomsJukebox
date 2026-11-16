"""Podcast extras from the Android app: suggested groups (Tin Tức Tiếng Việt, Công Giáo, Tin Tức Úc, Hài Kịch Úc, Âm Nhạc,
Thiếu Nhi, Kể Chuyện), stale news channels hidden, high-quality downloads, and the 4 ways to keep a podcast:
● record on the player, ✂ A–B clip, 💾 save the whole episode, ⏰ auto-save each new episode."""
import json
import os
import threading
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout)

from .. import app_info, online, recorder
from ..art.themes import t
from .widgets import fmt_time, h2, hint

NEWS_MAX_AGE = 60 * 24 * 3600

GROUPS = [
    ("vnnews", "Vietnamese News", "Tin Tức Tiếng Việt", ["1571503601", "1574624782", "1731182745", "161320292"], True),
    ("catholic", "Catholic", "Công Giáo", ["1551917143", "1676412067", "1587296543", "1853452424", "1884241839", "1555201608", "1586455389",
                                           "1801959745", "1539568321", "129684370", "1151970163", "1065019039", "1709182712", "1649296291"], False),
    ("aunews", "Australian News", "Tin Tức Úc", ["1713274928", "1896828280", "1349523628", "297778503", "297778504", "297778505", "73329715",
                                                 "1527948302", "1436450976", "1444390972", "1821376327", "1775573992", "291212440", "92455788"], True),
    ("comedy", "Australian Comedy", "Hài Kịch Úc", ["1121926361", "1852311207", "1459332175", "350709505", "1455446173"], True),
    ("music", "Music", "Âm Nhạc", ["919801673", "364978669", "1441212236", "156556864", "1535418229", "788236947", "1868596227", "1495217848",
                                   "1516748346"], False),
    ("kids", "Kids", "Thiếu Nhi", ["1851914571", "1674951226", "1468817120", "1376821352", "1491841381", "1093699006", "1450698399", "1532630528",
                                   "1610576181", "1454826120", "1257569536", "1233834541", "719585944"], False),
    ("stories", "Vietnamese Stories & Audiobooks", "Kể Chuyện & Sách Nói Tiếng Việt", ["1571282770", "1505235567", "1573541336", "1651180294",
                                                                                        "1833727223", "1538340531", "6814196004", "1702660933",
                                                                                        "1567914655", "1671433065", "1734826819", "1517025287"], False),
]


def _parse_iso(s):
    try:
        return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return 0


def lookup_group(db, key):
    """Channels of one group from Apple Podcasts (by fixed id), kept for a day. News channels that stopped are left out."""
    g = next(x for x in GROUPS if x[0] == key)
    cache = {}
    try:
        cache = json.loads(db.get("pod_groups_cache") or "{}")
    except Exception:
        cache = {}
    ent = cache.get(key)
    if ent and time.time() - ent.get("time", 0) < 86400 and ent.get("list"):
        return ent["list"]
    ids, news = g[3], g[4]
    got = {}
    for country in ("", "&country=vn", "&country=au"):
        need = [i for i in ids if i not in got]
        if not need:
            break
        try:
            o = json.loads(online.get("https://itunes.apple.com/lookup?id=" + ",".join(need) + country, timeout=15))
        except Exception:
            continue
        for r in o.get("results", []):
            cid = str(r.get("collectionId", ""))
            if cid in need and r.get("feedUrl"):
                rel = _parse_iso(r.get("releaseDate") or "")
                if news and rel and time.time() - rel > NEWS_MAX_AGE:
                    got[cid] = None
                    continue
                got[cid] = {"title": r.get("collectionName", ""), "author": r.get("artistName", ""), "feed": r["feedUrl"],
                            "image": r.get("artworkUrl600", "")}
    out = [got[i] for i in ids if got.get(i)]
    if out:
        cache[key] = {"time": time.time(), "list": out}
        try:
            db.set("pod_groups_cache", json.dumps(cache))
        except Exception:
            pass
    return out


# ------------------------------------------------------------------ folders and saving
def pod_rec_dir(db):
    d = os.path.join(db.get("rec_dir") or str(app_info.default_recordings_dir()), "Podcast")
    os.makedirs(d, exist_ok=True)
    return d


def ensure_schema(db):
    for sql in ("ALTER TABLE episodes ADD COLUMN hq TEXT",):
        try:
            db.x(sql)
        except Exception:
            pass


def best_url(db, e):
    try:
        hq = e["hq"]
    except (IndexError, KeyError):
        hq = None
    if db.get("pod_hq") and hq:
        return hq
    return e["url"]


def save_whole(db, e, ptitle, progress=None):
    """💾 Lưu Cả Tập: copy (or download) the whole episode into Recordings/Podcast."""
    src = e["local_path"] if e["local_path"] and os.path.exists(e["local_path"]) else None
    url = best_url(db, e)
    ext = os.path.splitext((src or url).split("?")[0])[1] or ".mp3"
    dest = os.path.join(pod_rec_dir(db), recorder.safe_name(f"{ptitle} - {e['title']}")[:120] + ext)
    if os.path.exists(dest):
        return dest
    if src:
        import shutil
        shutil.copyfile(src, dest)
    else:
        online.download(url, dest, progress)
    return dest


def save_clip(db, src, title, podcast, a, b):
    """✂ Cut the part A–B straight from the original file (no re-encoding, so no loss of quality)."""
    import av
    a, b = max(0.0, float(a)), float(b)
    if b <= a + 1:
        raise ValueError(t("Choose a longer part.", "Hãy chọn đoạn dài hơn."))
    inp = av.open(src, timeout=20)
    ist = inp.streams.audio[0]
    codec = (ist.codec_context.name or "").lower()
    ext = ".m4a"
    for key, e in (("mp3", ".mp3"), ("aac", ".m4a"), ("opus", ".ogg"), ("vorbis", ".ogg"), ("flac", ".flac")):
        if codec.startswith(key):
            ext = e
            break
    stamp = f"{fmt_time(a).replace(':', '.')}-{fmt_time(b).replace(':', '.')}"
    dest = os.path.join(pod_rec_dir(db), recorder.safe_name(f"{podcast} - {title} ({stamp})")[:140] + ext)
    out = av.open(dest, "w")
    if hasattr(out, "add_stream_from_template"):
        ost = out.add_stream_from_template(ist)
    else:
        ost = out.add_stream(template=ist)
    inp.seek(int(a / ist.time_base), stream=ist, any_frame=False, backward=True)
    first = None
    for pkt in inp.demux(ist):
        if pkt.dts is None:
            continue
        ts = float(pkt.pts * ist.time_base) if pkt.pts is not None else float(pkt.dts * ist.time_base)
        if ts < a - 0.05:
            continue
        if ts > b:
            break
        if first is None:
            first = pkt.pts if pkt.pts is not None else pkt.dts
        if pkt.pts is not None:
            pkt.pts -= first
        pkt.dts = max(0, pkt.dts - first)
        pkt.stream = ost
        out.mux(pkt)
    out.close()
    inp.close()
    return dest


def autosave_ids(db):
    try:
        return set(json.loads(db.get("pod_autosave") or "[]"))
    except Exception:
        return set()


def set_autosave(db, pid, on):
    s = autosave_ids(db)
    (s.add if on else s.discard)(int(pid))
    db.set("pod_autosave", json.dumps(sorted(s)))


# ------------------------------------------------------------------ ● record on the player while a podcast plays
_rec = {"from": None, "eid": None}


def pod_record_toggle(win):
    """First press: remember where we are. Second press: save that part (cut from the episode). Returns True while recording."""
    p = win.player
    it = p.current
    if not it or it.get("kind") != "episode":
        return False
    if _rec["from"] is None or _rec["eid"] != it.get("id"):
        _rec["from"] = p.position() or 0
        _rec["eid"] = it.get("id")
        win.toast(t("Recording this podcast… press ● again to save", "Đang thâu podcast… bấm ● lần nữa để lưu"))
        return True
    a, b = _rec["from"], p.position() or 0
    _rec["from"] = None
    _save_part(win, it, a, b)
    return False


def _save_part(win, it, a, b):
    src = it.get("local_path") if it.get("local_path") and os.path.exists(it.get("local_path")) else it.get("url")
    title, podcast = it.title, it.get("artist") or "Podcast"
    db = win.db

    def work():
        try:
            dest = save_clip(db, src, title, podcast, a, b)
            win.bus_toast(t("Saved to Recordings: ", "Đã lưu vào Bản Thâu Âm: ") + os.path.basename(dest))
        except Exception as e:
            app_info.log.info("podcast clip failed: %s", e)
            win.bus_toast(t("Could not save this part: ", "Không lưu được đoạn này: ") + str(e)[:80])
    threading.Thread(target=work, daemon=True).start()


class ClipDialog(QDialog):
    """✂ Cắt Đoạn A–B for the episode that is playing."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        p = win.player
        self.it = p.current
        dur = p.duration() or 0
        self.setWindowTitle(t("Cut A Part (A–B)", "Cắt Đoạn A–B"))
        self.resize(520, 260)
        v = QVBoxLayout(self)
        v.addWidget(h2((self.it.title if self.it else "") or "Podcast"))
        v.addWidget(hint(t("Move the two sliders (or press Mark A / Mark B while listening), then Save Part. The part is cut straight from the episode, so the quality stays the same.",
                           "Kéo hai thanh trượt (hoặc bấm Đánh Dấu A / B khi đang nghe), rồi bấm Lưu Đoạn. Đoạn được cắt thẳng từ tập gốc nên giữ nguyên chất lượng.")))
        self.dur = max(1, int(dur))
        pos = int(p.position() or 0)
        self.sa = QSlider(Qt.Horizontal)
        self.sb = QSlider(Qt.Horizontal)
        for s in (self.sa, self.sb):
            s.setRange(0, self.dur)
        self.sa.setValue(max(0, pos - 60))
        self.sb.setValue(min(self.dur, pos))
        self.la = QLabel()
        self.lb = QLabel()
        for lab, s, name in ((self.la, self.sa, "A"), (self.lb, self.sb, "B")):
            r = QHBoxLayout()
            r.addWidget(QLabel(name))
            r.addWidget(s, 1)
            r.addWidget(lab)
            v.addLayout(r)
            s.valueChanged.connect(self._show)
        r = QHBoxLayout()
        ma = QPushButton(t("Mark A Here", "Đánh Dấu A"))
        ma.clicked.connect(lambda: self.sa.setValue(int(self.win.player.position() or 0)))
        mb = QPushButton(t("Mark B Here", "Đánh Dấu B"))
        mb.clicked.connect(lambda: self.sb.setValue(int(self.win.player.position() or 0)))
        save = QPushButton("✂ " + t("Save Part", "Lưu Đoạn"))
        save.setObjectName("Primary")
        save.clicked.connect(self._save)
        whole = QPushButton("💾 " + t("Save Whole Episode", "Lưu Cả Tập"))
        whole.clicked.connect(self._whole)
        for b in (ma, mb, save, whole):
            r.addWidget(b)
        v.addLayout(r)
        self._show()

    def _show(self):
        self.la.setText(fmt_time(self.sa.value()))
        self.lb.setText(fmt_time(self.sb.value()))

    def _save(self):
        a, b = sorted((self.sa.value(), self.sb.value()))
        if self.it:
            _save_part(self.win, self.it, a, b)
        self.accept()

    def _whole(self):
        it = self.it
        if not it:
            return
        e = self.win.db.one("SELECT e.*, p.title ptitle FROM episodes e JOIN podcasts p ON p.id=e.podcast_id WHERE e.id=?", (it.get("id"),))
        if e:
            save_episode_bg(self.win, e)
        self.accept()


def save_episode_bg(win, e):
    db = win.db
    win.toast(t("Saving the whole episode…", "Đang lưu cả tập…"))

    def work():
        try:
            dest = save_whole(db, e, e["ptitle"])
            win.bus_toast(t("Saved to Recordings: ", "Đã lưu vào Bản Thâu Âm: ") + os.path.basename(dest))
        except Exception as ex:
            win.bus_toast(t("Could not save: ", "Không lưu được: ") + str(ex)[:80])
    threading.Thread(target=work, daemon=True).start()
