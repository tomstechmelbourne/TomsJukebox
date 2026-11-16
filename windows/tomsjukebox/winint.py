"""Windows-only extras: keyboard media keys (Play/Pause, Next, Previous, Stop) even when the program is in
the background, and Previous / Play / Next buttons on the taskbar preview. Everything is guarded:
if Windows refuses, the program simply works without it (and writes it in the log)."""
import ctypes
import os
import sys
import tempfile

from .app_info import log

IS_WIN = sys.platform.startswith("win")
WM_HOTKEY = 0x0312
WM_COMMAND = 0x0111
THBN_CLICKED = 0x1800
VK = {"playpause": 0xB3, "next": 0xB0, "prev": 0xB1, "stop": 0xB2}
HOTKEY_IDS = {0xB3: "playpause", 0xB0: "next", 0xB1: "prev", 0xB2: "stop"}
THUMB_IDS = {1: "prev", 2: "playpause", 3: "next"}


def set_app_id():
    if IS_WIN:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TomsTechnologySolutions.TomsJukebox")
        except Exception:
            pass


def register_media_keys(hwnd):
    ok = []
    if not IS_WIN:
        return ok
    u32 = ctypes.windll.user32
    for name, vk in VK.items():
        try:
            if u32.RegisterHotKey(ctypes.c_void_p(hwnd), vk, 0x4000, vk):   # MOD_NOREPEAT
                ok.append(name)
        except Exception:
            pass
    log.info("media keys registered: %s", ok)
    return ok


def unregister_media_keys(hwnd):
    if IS_WIN:
        for vk in VK.values():
            try:
                ctypes.windll.user32.UnregisterHotKey(ctypes.c_void_p(hwnd), vk)
            except Exception:
                pass


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint), ("wParam", ctypes.c_size_t),
                ("lParam", ctypes.c_ssize_t), ("time", ctypes.c_uint), ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]


def parse_native(message_ptr):
    """Returns 'playpause' / 'next' / 'prev' / 'stop' for media key or taskbar button messages, else None."""
    try:
        msg = MSG.from_address(int(message_ptr))
    except Exception:
        return None
    if msg.message == WM_HOTKEY:
        return HOTKEY_IDS.get(int(msg.wParam))
    if msg.message == WM_COMMAND and (int(msg.wParam) >> 16) & 0xFFFF == THBN_CLICKED:
        return THUMB_IDS.get(int(msg.wParam) & 0xFFFF)
    return None


# ---------------------------------------------------------------- taskbar preview buttons
class Taskbar:
    def __init__(self, hwnd, icons):
        """icons: dict name -> PIL.Image (prev, play, pause, next)."""
        self.ok = False
        self.hwnd = hwnd
        self.hicons = {}
        if not IS_WIN:
            return
        try:
            import comtypes
            import comtypes.client
            from comtypes import GUID, COMMETHOD, HRESULT
            from ctypes import wintypes

            class THUMBBUTTON(ctypes.Structure):
                _fields_ = [("dwMask", wintypes.DWORD), ("iId", wintypes.UINT), ("iBitmap", wintypes.UINT),
                            ("hIcon", wintypes.HICON), ("szTip", wintypes.WCHAR * 260), ("dwFlags", wintypes.DWORD)]
            self.THUMBBUTTON = THUMBBUTTON

            class ITaskbarList3(comtypes.IUnknown):
                _iid_ = GUID("{ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}")
                _methods_ = [
                    COMMETHOD([], HRESULT, "HrInit"),
                    COMMETHOD([], HRESULT, "AddTab", (["in"], wintypes.HWND, "hwnd")),
                    COMMETHOD([], HRESULT, "DeleteTab", (["in"], wintypes.HWND, "hwnd")),
                    COMMETHOD([], HRESULT, "ActivateTab", (["in"], wintypes.HWND, "hwnd")),
                    COMMETHOD([], HRESULT, "SetActiveAlt", (["in"], wintypes.HWND, "hwnd")),
                    COMMETHOD([], HRESULT, "MarkFullscreenWindow", (["in"], wintypes.HWND, "hwnd"), (["in"], wintypes.BOOL, "f")),
                    COMMETHOD([], HRESULT, "SetProgressValue", (["in"], wintypes.HWND, "hwnd"), (["in"], ctypes.c_ulonglong, "done"), (["in"], ctypes.c_ulonglong, "total")),
                    COMMETHOD([], HRESULT, "SetProgressState", (["in"], wintypes.HWND, "hwnd"), (["in"], ctypes.c_int, "flags")),
                    COMMETHOD([], HRESULT, "RegisterTab", (["in"], wintypes.HWND, "a"), (["in"], wintypes.HWND, "b")),
                    COMMETHOD([], HRESULT, "UnregisterTab", (["in"], wintypes.HWND, "a")),
                    COMMETHOD([], HRESULT, "SetTabOrder", (["in"], wintypes.HWND, "a"), (["in"], wintypes.HWND, "b")),
                    COMMETHOD([], HRESULT, "SetTabActive", (["in"], wintypes.HWND, "a"), (["in"], wintypes.HWND, "b"), (["in"], wintypes.DWORD, "r")),
                    COMMETHOD([], HRESULT, "ThumbBarAddButtons", (["in"], wintypes.HWND, "hwnd"), (["in"], wintypes.UINT, "n"), (["in"], ctypes.POINTER(THUMBBUTTON), "b")),
                    COMMETHOD([], HRESULT, "ThumbBarUpdateButtons", (["in"], wintypes.HWND, "hwnd"), (["in"], wintypes.UINT, "n"), (["in"], ctypes.POINTER(THUMBBUTTON), "b")),
                ]
            self.tbl = comtypes.client.CreateObject(GUID("{56FDF344-FD6D-11d0-958A-006097C9A090}"), interface=ITaskbarList3)
            self.tbl.HrInit()
            tmp = tempfile.mkdtemp(prefix="tj_icons_")
            u32 = ctypes.windll.user32
            u32.LoadImageW.restype = wintypes.HANDLE
            for name, img in icons.items():
                p = os.path.join(tmp, name + ".ico")
                img.save(p, sizes=[(16, 16), (32, 32)])
                self.hicons[name] = u32.LoadImageW(None, p, 1, 16, 16, 0x10)   # IMAGE_ICON, LR_LOADFROMFILE
            arr = (THUMBBUTTON * 3)()
            for i, (bid, nm, tip) in enumerate(((1, "prev", "Previous"), (2, "play", "Play / Pause"), (3, "next", "Next"))):
                arr[i].dwMask = 0x2 | 0x4 | 0x8
                arr[i].iId = bid
                arr[i].hIcon = self.hicons.get(nm)
                arr[i].szTip = tip
                arr[i].dwFlags = 0
            self.tbl.ThumbBarAddButtons(hwnd, 3, arr)
            self.ok = True
            log.info("taskbar buttons added")
        except Exception as e:
            log.info("taskbar buttons not available: %s", e)

    def set_playing(self, playing):
        if not self.ok:
            return
        try:
            b = self.THUMBBUTTON()
            b.dwMask = 0x2 | 0x4
            b.iId = 2
            b.hIcon = self.hicons.get("pause" if playing else "play")
            b.szTip = "Pause" if playing else "Play"
            self.tbl.ThumbBarUpdateButtons(self.hwnd, 1, ctypes.pointer(b))
        except Exception:
            pass


def button_icons():
    """White symbols for the taskbar buttons, drawn with Pillow."""
    from PIL import Image, ImageDraw
    out = {}
    for name in ("prev", "play", "pause", "next"):
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        w = (255, 255, 255, 255)
        if name == "play":
            d.polygon([(9, 6), (26, 16), (9, 26)], fill=w)
        elif name == "pause":
            d.rectangle([8, 6, 13, 26], fill=w)
            d.rectangle([19, 6, 24, 26], fill=w)
        elif name == "next":
            d.polygon([(6, 6), (20, 16), (6, 26)], fill=w)
            d.rectangle([22, 6, 26, 26], fill=w)
        else:
            d.polygon([(26, 6), (12, 16), (26, 26)], fill=w)
            d.rectangle([6, 6, 10, 26], fill=w)
        out[name] = im
    return out


def prevent_sleep(on):
    """Keep the computer awake while recording radio (ES_CONTINUOUS | ES_SYSTEM_REQUIRED)."""
    if IS_WIN:
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x00000001 if on else 0))
        except Exception:
            pass
