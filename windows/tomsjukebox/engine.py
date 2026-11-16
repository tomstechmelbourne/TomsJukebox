"""Audio engine for Tom's Jukebox.

Decodes with PyAV (FFmpeg: MP3, AAC, ALAC, FLAC, WAV, OGG, Opus, WMA...), resamples everything to
44.1 kHz stereo float, applies ReplayGain + 10-band equaliser, and plays through PortAudio (sounddevice).
Gapless playback and crossfade are done here by joining / mixing the next song in the decoder thread.
The engine has no Qt dependency: the UI polls `events()` and `position()`.
"""
import collections
import math
import queue
import threading
import time

import numpy as np

from .app_info import log

RATE = 44100
BLOCK = 1024
EQ_FREQS = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_PRESETS = {   # the same 30 as the Android app, plus Loudness
    "flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "rock": [5, 4, 3, 1, -1, -1, 1, 3, 4, 5],
    "pop": [-1, 1, 3, 4, 3, 1, -1, -1, 1, 2],
    "jazz": [3, 2, 1, 2, -1, -1, 0, 1, 2, 3],
    "classical": [4, 3, 2, 1, -1, -1, 0, 2, 3, 4],
    "bass": [7, 6, 5, 3, 1, 0, 0, 0, 0, 0],
    "treble": [0, 0, 0, 0, 0, 1, 2, 4, 6, 7],
    "vocal": [-2, -2, -1, 1, 3, 4, 4, 2, 0, -1],
    "bolero": [2, 2, 1, 1, 2, 3, 3, 2, 1, 1],
    "dance": [6, 5, 2, 0, 0, -2, -1, 2, 4, 4],
    "hiphop": [6, 5, 2, 3, -1, -1, 1, 0, 2, 3],
    "acoustic": [3, 3, 2, 1, 1, 1, 2, 3, 2, 1],
    "piano": [2, 1, 0, 2, 3, 1, 3, 4, 2, 2],
    "electronic": [5, 4, 1, 0, -2, 2, 1, 1, 4, 5],
    "cailuong": [0, 1, 1, 2, 3, 3, 2, 3, 2, 0],
    "headphones": [4, 3, 1, 0, -1, 0, 1, 2, 3, 2],
    "laptop": [-4, -2, 2, 4, 3, 2, 2, 3, 2, 1],
    "night": [-3, -2, -1, 0, 1, 2, 2, 1, -1, -3],
    "bass_light": [3, 3, 2, 1, 0, 0, 0, 0, 0, 0],
    "bass_super": [10, 9, 7, 4, 1, 0, 0, 0, 0, 0],
    "bass_cut": [-6, -5, -4, -2, 0, 0, 0, 0, 0, 0],
    "treble_light": [0, 0, 0, 0, 0, 0, 1, 2, 3, 3],
    "treble_super": [0, 0, 0, 0, 0, 1, 3, 6, 8, 9],
    "treble_cut": [0, 0, 0, 0, 0, 0, -1, -3, -5, -6],
    "vshape": [7, 6, 3, 0, -2, -2, 0, 3, 6, 7],
    "loud": [1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
    "voice": [-4, -3, -1, 1, 4, 5, 5, 3, 0, -2],
    "car": [5, 4, 2, 0, -1, 0, 2, 3, 3, 2],
    "bt_speaker": [5, 4, 3, 2, 0, 0, 1, 2, 2, 1],
    "hall": [3, 2, 1, 0, 1, 2, 3, 3, 4, 4],
    "loudness": [5, 4, 1, 0, -1, 0, 0, 1, 4, 5],
}


def eq_for_genre(genre):
    """Kiểu chỉnh âm tự chọn theo thể loại (same rules as Android)."""
    g = (genre or "").lower()
    rules = [(("rock", "metal"), "rock"), (("hip", "rap"), "hiphop"), (("dance", "edm", "house"), "dance"),
             (("electr", "techno", "trance"), "electronic"), (("jazz", "blues"), "jazz"), (("classic", "opera"), "classical"),
             (("acoustic", "folk"), "acoustic"), (("piano",), "piano"), (("bolero", "trữ tình", "tru tinh"), "bolero"),
             (("cải lương", "cai luong", "dân ca"), "cailuong"), (("ballad", "vocal"), "vocal"), (("pop",), "pop"),
             (("podcast", "talk", "news", "speech", "tin tức"), "voice")]
    for keys, k in rules:
        if any(x in g for x in keys):
            return k
    return None


# --------------------------------------------------------------------------- sources
class Source:
    """A playable thing. `blocks()` yields float32 arrays shaped (n, 2) at RATE."""
    duration = 0.0
    seekable = True
    title_hint = None

    def blocks(self):
        raise NotImplementedError

    def seek(self, seconds):
        pass

    def close(self):
        pass


class AVSource(Source):
    """File or network stream decoded by PyAV."""

    def __init__(self, target, fmt=None, options=None, duration=None, live=False):
        import av
        self.av = av
        self.target = target
        self.container = av.open(target, mode="r", format=fmt, options=options or {}, timeout=(10.0, 20.0))
        self.stream = next(s for s in self.container.streams if s.type == "audio")
        self.stream.thread_type = "AUTO"
        d = duration
        if d is None:
            if self.stream.duration and self.stream.time_base:
                d = float(self.stream.duration * self.stream.time_base)
            elif self.container.duration:
                d = self.container.duration / 1_000_000
        self.duration = float(d or 0.0)
        self.live = live
        self.seekable = (not live) and self.duration > 0
        self._new_resampler()
        self._seek_to = None
        self.codec_name = self.stream.codec_context.name
        self.bitrate = self.stream.bit_rate or self.container.bit_rate or 0

    def _new_resampler(self):
        self.resampler = self.av.AudioResampler(format="flt", layout="stereo", rate=RATE)

    def seek(self, seconds):
        self._seek_to = max(0.0, float(seconds))

    def blocks(self):
        while True:
            if self._seek_to is not None:
                t = self._seek_to
                self._seek_to = None
                try:
                    self.container.seek(int(t * 1_000_000), any_frame=False, backward=True)
                except Exception as e:
                    log.info("seek failed: %s", e)
                self._new_resampler()
                yield ("seeked", t)
            try:
                packet_iter = self.container.decode(self.stream)
                for frame in packet_iter:
                    for out in self.resampler.resample(frame):
                        arr = out.to_ndarray()
                        # packed flt stereo -> shape (1, n*2)
                        arr = arr.reshape(-1, 2).astype(np.float32, copy=False)
                        ts = float(frame.pts * frame.time_base) if frame.pts is not None else None
                        yield (arr, ts)
                    if self._seek_to is not None:
                        break
                else:
                    for out in self.resampler.resample(None):
                        yield (out.to_ndarray().reshape(-1, 2).astype(np.float32, copy=False), None)
                    return
            except self.av.error.EOFError:
                return
            except Exception as e:
                if self._seek_to is not None:
                    continue
                log.warning("decode error %s: %s", self.target if isinstance(self.target, str) else "stream", e)
                raise

    def close(self):
        try:
            self.container.close()
        except Exception:
            pass


class PCMSource(Source):
    """Raw 16-bit stereo 44.1 kHz from a reader function (audio CD)."""

    def __init__(self, reader, total_frames):
        self.reader = reader            # reader(frame_offset, n_frames) -> bytes
        self.total = total_frames
        self.duration = total_frames / 44100.0
        self.pos = 0
        self._seek_to = None

    def seek(self, seconds):
        self._seek_to = seconds

    def blocks(self):
        chunk = 588 * 20   # 20 CD sectors per read
        while self.pos < self.total:
            if self._seek_to is not None:
                self.pos = int(self._seek_to * 44100) // 588 * 588
                self._seek_to = None
                yield ("seeked", self.pos / 44100.0)
            n = min(chunk, self.total - self.pos)
            data = self.reader(self.pos, n)
            if not data:
                return
            a = np.frombuffer(data, dtype="<i2").astype(np.float32).reshape(-1, 2) / 32768.0
            ts = self.pos / 44100.0
            self.pos += len(a)
            yield (a, ts)


class ToneSource(Source):
    """Test source (self-test / demo without files)."""

    def __init__(self, seconds=2.0, freq=440.0):
        self.duration = seconds
        self.freq = freq
        self.pos = 0
        self._seek_to = None

    def seek(self, seconds):
        self._seek_to = seconds

    def blocks(self):
        total = int(self.duration * RATE)
        while self.pos < total:
            if self._seek_to is not None:
                self.pos = int(self._seek_to * RATE)
                self._seek_to = None
                yield ("seeked", self.pos / RATE)
            n = min(BLOCK * 4, total - self.pos)
            t = (np.arange(n) + self.pos) / RATE
            s = (0.2 * np.sin(2 * math.pi * self.freq * t)).astype(np.float32)
            ts = self.pos / RATE
            self.pos += n
            yield (np.stack([s, s], axis=1), ts)


# --------------------------------------------------------------------------- equaliser
def _peaking(f0, gain_db, q=1.41):
    a = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * f0 / RATE
    alpha = math.sin(w0) / (2 * q)
    b0, b1, b2 = 1 + alpha * a, -2 * math.cos(w0), 1 - alpha * a
    a0, a1, a2 = 1 + alpha / a, -2 * math.cos(w0), 1 - alpha / a
    return [b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]


class Equalizer:
    def __init__(self):
        self.on = False
        self.gains = [0.0] * 10
        self.sos = None
        self.zi = None
        self.pre = 1.0

    def set(self, on, gains):
        self.on = bool(on)
        self.gains = [float(g) for g in gains][:10] + [0.0] * (10 - len(gains))
        if self.on and any(abs(g) > 0.05 for g in self.gains):
            self.sos = np.array([_peaking(f, g) for f, g in zip(EQ_FREQS, self.gains)], dtype=np.float64)
            self.zi = np.zeros((len(EQ_FREQS), 2, 2))
            self.pre = 10 ** (-max(0.0, max(self.gains)) * 0.6 / 20)   # headroom to avoid clipping
        else:
            self.sos = None

    def reset(self):
        if self.sos is not None:
            self.zi = np.zeros((len(EQ_FREQS), 2, 2))

    def process(self, x):
        if self.sos is None:
            return x
        from scipy.signal import sosfilt
        y, self.zi = sosfilt(self.sos, x * self.pre, axis=0, zi=self.zi)
        return y.astype(np.float32)


# --------------------------------------------------------------------------- outputs
class _NullOutput:
    """Used when no sound device is available (tests, or a computer without audio)."""

    def __init__(self, callback, fast=False):
        self.cb = callback
        self.fast = fast
        self.run = True
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def _loop(self):
        buf = np.zeros((BLOCK, 2), np.float32)
        while self.run:
            self.cb(buf, BLOCK, None, None)
            time.sleep(0.0 if self.fast else BLOCK / RATE)

    def close(self):
        self.run = False


class Engine:
    def __init__(self, null_output=False, fast=False):
        self.q = queue.Queue(maxsize=10)
        self.lock = threading.RLock()
        self.volume = 0.8
        self.muted = False
        self.paused = True
        self.eq = Equalizer()
        self.crossfade = 0.0
        self.gapless = True
        self.next_provider = None     # callable -> (token, Source, gain_db) or None
        self._events = collections.deque()
        self._cmd = queue.Queue()
        self._cur = None             # (token, source, gain)
        self._pos = 0.0
        self._cur_token = None
        self._play_token = None
        self.last_block = np.zeros((BLOCK, 2), np.float32)
        self._gen = 0                # bumps on stop/seek to drop stale blocks
        self.device_name = "none"
        self.output = None
        self.error = None
        self._leftover = None
        self._open_output(null_output, fast)
        self.th = threading.Thread(target=self._producer, daemon=True, name="decoder")
        self.th.start()

    # ---- output
    def _open_output(self, null_output, fast):
        if not null_output:
            try:
                import sounddevice as sd
                self.output = sd.OutputStream(samplerate=RATE, channels=2, dtype="float32",
                                              blocksize=BLOCK, latency="high", callback=self._callback)
                self.output.start()
                try:
                    self.device_name = sd.query_devices(sd.default.device[1])["name"]
                except Exception:
                    self.device_name = "default"
                return
            except Exception as e:
                self.error = str(e)
                log.warning("no sound device, using silent output: %s", e)
        self.output = _NullOutput(self._callback, fast=fast)
        self.device_name = "silent"

    def _callback(self, outdata, frames, _time, _status):
        filled = 0
        out = np.zeros((frames, 2), np.float32)
        if not self.paused:
            while filled < frames:
                if self._leftover is None:
                    try:
                        item = self.q.get_nowait()
                    except queue.Empty:
                        break
                    if item[0] != self._gen:
                        continue
                    _g, token, ts, arr, kind = item
                    if kind == "end":
                        self._events.append(("ended", token))
                        continue
                    if token != self._play_token:
                        self._play_token = token
                        self._events.append(("started", token))
                    self._leftover = [token, ts, arr]
                token, ts, arr = self._leftover
                n = min(frames - filled, len(arr))
                out[filled:filled + n] = arr[:n]
                filled += n
                if ts is not None:
                    self._pos = ts + n / RATE
                    self._cur_token = token
                if n >= len(arr):
                    self._leftover = None
                else:
                    self._leftover = [token, (ts + n / RATE) if ts is not None else None, arr[n:]]
        vol = 0.0 if self.muted else self.volume
        out *= vol * vol   # perceptual curve
        np.clip(out, -1.0, 1.0, out=out)
        self.last_block = out
        if outdata is not None:
            outdata[:] = out

    # ---- commands (UI thread)
    def play(self, token, source, gain_db=0.0):
        self._cmd.put(("play", token, source, gain_db))
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def toggle(self):
        self.paused = not self.paused

    def stop(self):
        self._cmd.put(("stop",))
        self.paused = True

    def seek(self, seconds):
        self._cmd.put(("seek", seconds))

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))

    def set_eq(self, on, gains):
        with self.lock:
            self.eq.set(on, gains)

    def position(self):
        return self._pos

    def current_token(self):
        return self._cur_token

    def events(self):
        out = []
        while self._events:
            out.append(self._events.popleft())
        return out

    def levels(self, bands=48):
        """Spectrum levels 0..1 for the sound wave / visualiser."""
        blk = self.last_block
        if blk is None or len(blk) < 256:
            return np.zeros(bands)
        mono = blk.mean(axis=1)[-1024:]
        if len(mono) < 1024:
            mono = np.pad(mono, (0, 1024 - len(mono)))
        spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))[1:]
        edges = np.unique(np.geomspace(1, len(spec), bands + 1).astype(int))
        vals = np.array([spec[a:b].mean() if b > a else 0 for a, b in zip(edges[:-1], edges[1:])])
        if len(vals) < bands:
            vals = np.pad(vals, (0, bands - len(vals)))
        vals = np.log10(1 + vals * 4) / 1.6
        return np.clip(vals, 0, 1)

    def close(self):
        self._cmd.put(("quit",))
        try:
            if hasattr(self.output, "stop"):
                self.output.stop()
            self.output.close()
        except Exception:
            pass

    # ---- decoder thread
    def _flush(self):
        self._gen += 1
        self._leftover = None
        try:
            while True:
                self.q.get_nowait()
        except queue.Empty:
            pass

    def _put(self, token, ts, arr, kind="pcm"):
        gen = self._gen
        while True:
            try:
                self.q.put((gen, token, ts, arr, kind), timeout=0.05)
                return True
            except queue.Full:
                if not self._cmd.empty():
                    return False

    def _producer(self):
        cur = None          # dict(token, src, gen, gain)
        nxt = None
        while True:
            # commands
            try:
                cmd = self._cmd.get(timeout=0.02 if cur is None else 0)
            except queue.Empty:
                cmd = None
            if cmd:
                if cmd[0] == "quit":
                    return
                if cmd[0] in ("play", "stop"):
                    self._flush()
                    for c in (cur, nxt):
                        if c:
                            c["src"].close()
                    cur = nxt = None
                    self._play_token = None
                    if cmd[0] == "play":
                        _, token, src, gain = cmd
                        cur = self._wrap(token, src, gain)
                        self._pos = 0.0
                        self._cur_token = token
                    continue
                if cmd[0] == "seek" and cur is not None:
                    if nxt:
                        nxt["src"].close()
                        nxt = None
                    self._flush()
                    cur["src"].seek(cmd[1])
                    self._pos = cmd[1]
                    with self.lock:
                        self.eq.reset()
                    continue
            if cur is None:
                continue
            try:
                item = next(cur["gen"])
            except StopIteration:
                item = None
            except Exception as e:
                self._events.append(("error", cur["token"], str(e)))
                cur["src"].close()
                cur = None
                continue
            if item is None:
                # song finished -> gapless join or end
                cur["src"].close()
                if nxt is None and self.gapless and self.next_provider:
                    nxt = self._ask_next()
                self._put(cur["token"], None, None, "end")
                if nxt is not None and "buf" in nxt:
                    nxt["gen"] = _chain_buffer(nxt.pop("buf"), nxt["gen"])
                cur, nxt = nxt, None
                continue
            arr, ts = item
            if isinstance(arr, str):   # "seeked"
                continue
            if cur["gain"] != 1.0:
                arr = arr * cur["gain"]
            with self.lock:
                arr = self.eq.process(arr)
            # crossfade: start mixing the next song in the last N seconds
            xf = self.crossfade
            dur = cur["src"].duration
            if xf > 0 and dur > xf * 2 and ts is not None and self.next_provider and ts >= dur - xf:
                if nxt is None and not cur.get("asked"):
                    cur["asked"] = True
                    nxt = self._ask_next()
                if nxt is not None:
                    arr = self._mix(cur, nxt, arr, ts, dur, xf)
            if not self._put(cur["token"], ts, arr):
                continue

    def _wrap(self, token, src, gain_db):
        return {"token": token, "src": src, "gen": src.blocks(), "gain": 10 ** ((gain_db or 0) / 20)}

    def _ask_next(self):
        try:
            r = self.next_provider()
        except Exception as e:
            log.warning("next provider failed: %s", e)
            r = None
        if not r:
            return None
        token, src, gain = r
        return self._wrap(token, src, gain)

    def _mix(self, cur, nxt, arr, ts, dur, xf):
        n = len(arr)
        buf = nxt.setdefault("buf", np.zeros((0, 2), np.float32))
        while len(buf) < n:
            try:
                it = next(nxt["gen"])
            except StopIteration:
                break
            if isinstance(it[0], str):
                continue
            b = it[0] * nxt["gain"]
            buf = np.concatenate([buf, b])
        take = buf[:n]
        nxt["buf"] = buf[n:]
        if len(take) < n:
            take = np.pad(take, ((0, n - len(take)), (0, 0)))
        t = ts + np.arange(n) / RATE
        k = np.clip((t - (dur - xf)) / xf, 0, 1)[:, None]
        mixed = arr * np.cos(k * math.pi / 2) + take * np.sin(k * math.pi / 2)
        return mixed.astype(np.float32)


def _chain_buffer(buf, gen):
    if buf is not None and len(buf):
        yield (buf, None)
    yield from gen
