"""Demo library (for chay_demo.bat and the self-test): short generated tunes in several formats.
No real music is included; the tunes are simple chords made by the program."""
import math
import os

import numpy as np

ALBUMS = [
    ("Demo Melodies", "Tom's Jukebox Band", "Pop", 2024, "flac", [("Morning In Deanside", 0), ("Yarra Sunset", 3), ("Tram 86", 5)]),
    ("Giai Điệu Mẫu", "Ban Nhạc Thử", "Nhạc Vàng", 1975, "mp3", [("Chiều Sài Gòn", 2), ("Mưa Trên Phố", 7), ("Bến Xưa", 9)]),
    ("Road Trip Tones", "The Test Signals", "Rock", 2019, "m4a", [("Hume Highway", 4), ("Great Ocean Road", 0)]),
    ("Quiet Evening", "Sample Strings", "Classical", 2010, "opus", [("Nocturne For Sine", 5), ("Slow Waltz", 2)]),
]

NOTES = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25, 587.33, 659.25]


def tune(seconds, root_idx, rate=44100):
    n = int(seconds * rate)
    t = np.arange(n) / rate
    out = np.zeros(n, np.float32)
    beat = 0.5
    prog = [0, 3, 4, 0, 5, 3, 4, 0]
    for k in range(int(seconds / beat)):
        s, e = int(k * beat * rate), int((k + 1) * beat * rate)
        root = NOTES[(root_idx + prog[k % len(prog)]) % len(NOTES)]
        seg = t[s:e] - t[s]
        env = np.exp(-seg * 3.0)
        for mult, amp in ((1, 0.22), (1.25, 0.12), (1.5, 0.12), (0.5, 0.15)):
            out[s:e] += (amp * env * np.sin(2 * math.pi * root * mult * seg)).astype(np.float32)
    fade = min(n, rate)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return np.clip(out, -0.95, 0.95)


def write_audio(path, samples, codec, rate=44100):
    import av
    if codec == "libopus":
        rate = 48000
    c = av.open(path, "w")
    s = c.add_stream(codec, rate=rate)
    s.layout = "stereo"
    if codec in ("libmp3lame", "aac"):
        s.bit_rate = 192000
    fmts = [f.name for f in (s.codec_context.codec.audio_formats or [])]
    fmt = fmts[0] if fmts else "s16"
    x = samples
    if rate != 44100:
        idx = np.linspace(0, len(x) - 1, int(len(x) * rate / 44100))
        x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
    st = np.stack([x, x])
    step = 1024
    for i in range(0, st.shape[1], step):
        ch = st[:, i:i + step]
        if fmt in ("s16", "s16p"):
            a = (ch * 32767).astype(np.int16)
            a = a.T.reshape(1, -1) if fmt == "s16" else a
        elif fmt in ("s32", "s32p"):
            a = (ch * 2147483647).astype(np.int32)
            a = a.T.reshape(1, -1) if fmt == "s32" else a
        elif fmt == "flt":
            a = ch.T.reshape(1, -1).astype(np.float32)
        else:
            a = ch.astype(np.float32)
        f = av.AudioFrame.from_ndarray(np.ascontiguousarray(a), format=fmt, layout="stereo")
        f.sample_rate = rate
        for p in s.encode(f):
            c.mux(p)
    for p in s.encode(None):
        c.mux(p)
    c.close()


def make_library(folder, seconds=24):
    from . import tags
    os.makedirs(folder, exist_ok=True)
    codec_of = {"flac": "flac", "mp3": "libmp3lame", "m4a": "aac", "opus": "libopus"}
    made = []
    for album, artist, genre, year, ext, songs in ALBUMS:
        d = os.path.join(folder, artist, album)
        os.makedirs(d, exist_ok=True)
        for i, (title, root) in enumerate(songs, 1):
            p = os.path.join(d, f"{i:02d} {title}.{ext}")
            if not os.path.exists(p):
                write_audio(p, tune(seconds, root), codec_of[ext])
                tags.write(p, {"title": title, "artist": artist, "album": album, "albumartist": artist,
                               "genre": genre, "year": year, "track_no": i})
            made.append(p)
        lrc = os.path.join(d, f"01 {songs[0][0]}.lrc")
        if not os.path.exists(lrc):
            with open(lrc, "w", encoding="utf-8") as fh:
                fh.write("[ti:%s]\n[00:01.00]%s\n[00:05.00]♪ ♪ ♪\n[00:09.00]Tom's Jukebox demo lyrics\n"
                         "[00:14.00]Lời bài hát chạy theo nhạc\n[00:19.00]♪\n" % (songs[0][0], songs[0][0]))
    return made
