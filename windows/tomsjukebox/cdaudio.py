"""Play audio CDs straight from the drive on Windows (reads the disc's table of contents and the raw
audio sectors through the Windows CD-ROM driver), and look the disc up on MusicBrainz.

Not testable on the build machine: there is no CD drive there. Tom tests on his own drives."""
import base64
import ctypes
import hashlib
import sys
import threading

from .app_info import log

IS_WIN = sys.platform.startswith("win")
IOCTL_CDROM_READ_TOC = 0x00024000
IOCTL_CDROM_RAW_READ = 0x0002403E
IOCTL_STORAGE_EJECT_MEDIA = 0x002D4808
IOCTL_STORAGE_CHECK_VERIFY = 0x002D4800
SECTOR = 2352
FRAMES_PER_SECTOR = 588


class TRACK_DATA(ctypes.Structure):
    _fields_ = [("Reserved", ctypes.c_ubyte), ("ControlAdr", ctypes.c_ubyte),
                ("TrackNumber", ctypes.c_ubyte), ("Reserved1", ctypes.c_ubyte),
                ("Address", ctypes.c_ubyte * 4)]


class CDROM_TOC(ctypes.Structure):
    _fields_ = [("Length", ctypes.c_ubyte * 2), ("FirstTrack", ctypes.c_ubyte),
                ("LastTrack", ctypes.c_ubyte), ("TrackData", TRACK_DATA * 100)]


class RAW_READ_INFO(ctypes.Structure):
    _fields_ = [("DiskOffset", ctypes.c_longlong), ("SectorCount", ctypes.c_ulong),
                ("TrackMode", ctypes.c_int)]


def cd_drives():
    if not IS_WIN:
        return []
    k32 = ctypes.windll.kernel32
    mask = k32.GetLogicalDrives()
    return [f"{chr(65 + i)}:" for i in range(26) if mask & (1 << i) and k32.GetDriveTypeW(f"{chr(65 + i)}:\\") == 5]


class CDDrive:
    def __init__(self, letter):
        self.letter = letter.rstrip("\\").rstrip(":") + ":"
        self.handle = None
        self.lock = threading.Lock()

    def _open(self):
        if self.handle:
            return self.handle
        k32 = ctypes.windll.kernel32
        k32.CreateFileW.restype = ctypes.c_void_p
        h = k32.CreateFileW(f"\\\\.\\{self.letter}", 0x80000000, 0x3, None, 3, 0, None)
        if h in (None, ctypes.c_void_p(-1).value) or h == 2 ** 64 - 1:
            raise OSError("cannot open drive " + self.letter)
        self.handle = h
        return h

    def close(self):
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(self.handle))
            self.handle = None

    def _ioctl(self, code, inbuf, outbuf):
        k32 = ctypes.windll.kernel32
        ret = ctypes.c_ulong(0)
        ok = k32.DeviceIoControl(ctypes.c_void_p(self._open()), code,
                                 ctypes.byref(inbuf) if inbuf is not None else None,
                                 ctypes.sizeof(inbuf) if inbuf is not None else 0,
                                 ctypes.byref(outbuf) if outbuf is not None else None,
                                 ctypes.sizeof(outbuf) if outbuf is not None else 0,
                                 ctypes.byref(ret), None)
        return bool(ok), ret.value

    def has_disc(self):
        try:
            ok, _ = self._ioctl(IOCTL_STORAGE_CHECK_VERIFY, None, None)
            return ok
        except OSError:
            return False

    def toc(self):
        """Returns list of dicts: number, lba_start, lba_end, audio(bool); plus leadout lba."""
        toc = CDROM_TOC()
        with self.lock:
            ok, _ = self._ioctl(IOCTL_CDROM_READ_TOC, None, toc)
        if not ok:
            raise OSError("no audio disc")
        first, last = toc.FirstTrack, toc.LastTrack
        entries = []
        for i in range(last - first + 2):
            td = toc.TrackData[i]
            m, s, f = td.Address[1], td.Address[2], td.Address[3]
            lba = (m * 60 + s) * 75 + f - 150
            entries.append((td.TrackNumber, lba, not (td.ControlAdr & 0x04)))
        tracks = []
        for i in range(len(entries) - 1):
            num, lba, audio = entries[i]
            end = entries[i + 1][1]
            tracks.append({"number": num, "lba_start": lba, "lba_end": end, "audio": audio})
        return {"first": first, "last": last, "leadout": entries[-1][1], "tracks": tracks}

    def read_frames(self, lba_start, frame_offset, n_frames):
        """Read n_frames stereo 16-bit frames starting frame_offset into a track that starts at lba_start."""
        sector = lba_start + frame_offset // FRAMES_PER_SECTOR
        count = (n_frames + FRAMES_PER_SECTOR - 1) // FRAMES_PER_SECTOR
        out = bytearray()
        with self.lock:
            while count > 0:
                c = min(count, 20)
                info = RAW_READ_INFO(sector * 2048, c, 2)
                buf = (ctypes.c_ubyte * (SECTOR * c))()
                ok, got = False, 0
                for _attempt in range(3):
                    ok, got = self._ioctl(IOCTL_CDROM_RAW_READ, info, buf)
                    if ok:
                        break
                if not ok:
                    log.warning("CD read error at sector %d", sector)
                    out += bytes(SECTOR * c)   # silence instead of stopping on a scratch
                else:
                    out += bytes(buf)[:got]
                sector += c
                count -= c
        return bytes(out[: n_frames * 4])

    def eject(self):
        try:
            with self.lock:
                self._ioctl(IOCTL_STORAGE_EJECT_MEDIA, None, None)
        finally:
            self.close()


def musicbrainz_disc_id(toc):
    first, last = toc["first"], toc["last"]
    s = "%02X%02X" % (first, last)
    offsets = [toc["leadout"] + 150] + [t["lba_start"] + 150 for t in toc["tracks"]]
    offsets += [0] * (100 - len(offsets))
    s += "".join("%08X" % o for o in offsets[:100])
    h = hashlib.sha1(s.encode("ascii")).digest()
    return base64.b64encode(h).decode("ascii").replace("+", ".").replace("/", "_").replace("=", "-")


def toc_string(toc):
    """MusicBrainz 'toc' lookup parameter (works for discs not yet linked to a disc ID)."""
    offs = [t["lba_start"] + 150 for t in toc["tracks"]]
    return "+".join(str(x) for x in [toc["first"], toc["last"], toc["leadout"] + 150] + offs)
