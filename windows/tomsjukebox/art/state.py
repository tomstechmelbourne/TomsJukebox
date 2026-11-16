"""Live playback state the drawings read (album colours, playing, levels) — the Windows side of Android's Core."""
from .ds import Color


class _Core:
    def __init__(self):
        self.palette = [Color(0xFF48B0C8), Color(0xFFFBB040), Color(0xFF7EE3C1), Color(0xFF2C9CC0), Color(0xFFC7F0FA)]
        self.playing = False
        self.recording = False
        self.levels = [0.04] * 24
        self.dpr = 1.0

    def set_palette(self, colours):
        out = []
        for c in colours or []:
            out.append(c if isinstance(c, Color) else Color(c))
        while len(out) < 5:
            out.append(out[-1] if out else Color(0xFF48B0C8))
        self.palette = out


Core = _Core()
