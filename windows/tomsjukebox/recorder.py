"""Radio recording: keep the original stream (best quality the station sends) or convert to
FLAC / WAV 24-bit / ALAC / MP3 320 / AAC 256 / Opus. Reconnects by itself when the internet drops."""
import os
import re
import threading
import time
from datetime import datetime

from . import radio
from .app_info import log

FORMATS = {
    # key: (label_en, label_vi, extension, codec, options)
    "original": ("Keep Original (Best)", "Giữ Nguyên Bản Gốc (Tốt Nhất)", None, None, {}),
    "flac": ("FLAC (Lossless)", "FLAC (Không Mất Chất Lượng)", ".flac", "flac", {}),
    "wav24": ("WAV 24-bit", "WAV 24-bit", ".wav", "pcm_s24le", {}),
    "alac": ("ALAC (Apple Lossless)", "ALAC (Apple Lossless)", ".m4a", "alac", {}),
    "mp3_320": ("MP3 320 kbps", "MP3 320 kbps", ".mp3", "libmp3lame", {"b": 320000}),
    "aac_256": ("AAC 256 kbps", "AAC 256 kbps", ".m4a", "aac", {"b": 256000}),
    "opus": ("Opus 192 kbps", "Opus 192 kbps", ".opus", "libopus", {"b": 192000}),
}


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|]+', " ", s or "").strip()
    return re.sub(r"\s+", " ", s)[:120] or "Radio"


class Recording(threading.Thread):
    def __init__(self, station_name, url, out_dir, fmt="original", seconds=None, split=False, on_file=None):
        super().__init__(daemon=True, name="recorder")
        self.station = station_name
        self.url = url
        self.out_dir = str(out_dir)
        self.fmt = fmt if fmt in FORMATS else "original"
        self.limit = seconds
        self.split = split
        self.on_file = on_file          # callback(path) when a file is finished
        self.stop_ev = threading.Event()
        self.started_at = time.time()
        self.files = []
        self.error = None
        self.title = ""
        self.reconnects = 0
        self.bytes = 0

    # ---- control
    def stop(self):
        self.stop_ev.set()

    @property
    def elapsed(self):
        return time.time() - self.started_at

    def _timeout(self):
        return self.stop_ev.is_set() or (self.limit and self.elapsed >= self.limit)

    def _path(self, ext, title=None):
        os.makedirs(self.out_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H.%M")
        name = f"{safe_name(self.station)} - {stamp}"
        if title:
            name += f" - {safe_name(title)}"
        p = os.path.join(self.out_dir, name + ext)
        n = 2
        while os.path.exists(p):
            p = os.path.join(self.out_dir, f"{name} ({n}){ext}")
            n += 1
        return p

    def _finish(self, path):
        if not path or not os.path.exists(path) or os.path.getsize(path) < 2048:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
            return
        try:
            from . import tags
            tags.write(path, {"title": self.title or os.path.splitext(os.path.basename(path))[0],
                              "artist": self.station, "album": "Radio Recordings",
                              "genre": "Radio", "year": datetime.now().year})
        except Exception as e:
            log.info("could not tag recording: %s", e)
        self.files.append(path)
        if self.on_file:
            try:
                self.on_file(path)
            except Exception:
                pass

    def run(self):
        try:
            if self.fmt == "original" and not self.url.lower().split("?")[0].endswith(".m3u8"):
                self._run_original()
            else:
                self._run_convert()
        except Exception as e:
            self.error = str(e)
            log.warning("recording failed: %s", e)

    # ---- original stream bytes (no re-encoding at all)
    def _run_original(self):
        fh = path = None
        last_title = None
        while not self._timeout():
            try:
                icy = radio.IcyStream(self.url)
            except Exception as e:
                self.error = str(e)
                if not self._wait_retry():
                    break
                continue
            self.error = None
            try:
                if fh is None:
                    path = self._path(icy.ext)
                    fh = open(path, "wb")
                while not self._timeout():
                    data = icy.read(16384)
                    if not data:
                        raise OSError("stream ended")
                    if icy.title and icy.title != last_title:
                        self.title = icy.title
                        if self.split and last_title is not None:
                            fh.close()
                            self._finish(path)
                            path = self._path(icy.ext, icy.title)
                            fh = open(path, "wb")
                        last_title = icy.title
                    fh.write(data)
                    self.bytes += len(data)
            except Exception as e:
                log.info("recording dropped (%s), reconnecting", e)
                self.reconnects += 1
            finally:
                icy.close()
            if not self._timeout() and not self._wait_retry():
                break
        if fh:
            fh.close()
            self._finish(path)

    def _wait_retry(self):
        for _ in range(10):  # wait 5 s, but stop at once if asked
            if self._timeout():
                return False
            time.sleep(0.5)
        return True

    # ---- decode + encode to the chosen format
    def _run_convert(self):
        import av
        _l1, _l2, ext, codec, opts = FORMATS[self.fmt if self.fmt != "original" else "aac_256"]
        if self.fmt == "original":          # HLS stream: copy as AAC 256 (safest)
            ext, codec, opts = ".m4a", "aac", {"b": 256000}
        rate = 48000 if codec == "libopus" else 44100
        out_path = self._path(ext)
        oc = av.open(out_path, "w")
        st = oc.add_stream(codec, rate=rate)
        st.layout = "stereo"
        if "b" in opts:
            st.bit_rate = opts["b"]
        fmt_name = st.codec_context.codec.audio_formats[0].name if st.codec_context.codec.audio_formats else "s16"
        resampler = av.AudioResampler(format=fmt_name, layout="stereo", rate=rate)
        written = 0
        try:
            while not self._timeout():
                ic = None
                icy = None
                try:
                    if self.url.lower().split("?")[0].endswith(".m3u8"):
                        ic = av.open(self.url, timeout=(10.0, 20.0))
                    else:
                        icy = radio.IcyStream(self.url)
                        ic = av.open(icy, format=icy.fmt)
                    self.error = None
                    ist = next(s for s in ic.streams if s.type == "audio")
                    for frame in ic.decode(ist):
                        if icy is not None and icy.title:
                            self.title = icy.title
                        frame.pts = None
                        for f2 in resampler.resample(frame):
                            for pkt in st.encode(f2):
                                oc.mux(pkt)
                                self.bytes += pkt.size
                            written += f2.samples
                        if self._timeout():
                            break
                except Exception as e:
                    self.error = str(e)
                    log.info("recording (convert) dropped: %s", e)
                    self.reconnects += 1
                finally:
                    if icy:
                        icy.close()
                    if ic:
                        try:
                            ic.close()
                        except Exception:
                            pass
                if not self._timeout() and not self._wait_retry():
                    break
            for f2 in resampler.resample(None):
                for pkt in st.encode(f2):
                    oc.mux(pkt)
            for pkt in st.encode(None):
                oc.mux(pkt)
        finally:
            oc.close()
        self._finish(out_path if written else None)


def due_schedules(db, now=None):
    """Schedules whose start minute is now. days: '0,1,2' (Mon=0) or once_date 'YYYY-MM-DD'."""
    now = now or datetime.now()
    hm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    out = []
    for s in db.q("SELECT * FROM schedules WHERE enabled=1"):
        if s["start_hm"] != hm:
            continue
        if s["last_run"] == f"{today} {hm}":
            continue
        if s["once_date"]:
            if s["once_date"] != today:
                continue
        else:
            days = [int(d) for d in (s["days"] or "").split(",") if d.strip().isdigit()]
            if days and now.weekday() not in days:
                continue
        out.append(s)
    return out
