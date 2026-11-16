"""Font Chữ: the computer's own font, the 10 bundled Saigon 1985 sign-painting fonts (Thái Hiệu – Fontzin) and fonts Tom adds
himself (.ttf / .otf). The brand text "TOM'S JUKEBOX" never changes font."""
import os
import re
import shutil

from PySide6.QtGui import QFont, QFontDatabase

from .. import app_info
from .prefs import Prefs
from .themes import t

BUILT_IN = [
    ("default", "Computer Default", "Mặc Định Của Máy", None),
    ("sg85_saigon1985", "Saigon 1985 (Script)", "Sài Gòn 1985 (Chữ Viết)", "sg85_saigon1985.ttf"),
    ("sg85_cua_hang", "Cửa Hàng 99", "Cửa Hàng 99", "sg85_cua_hang.ttf"),
    ("sg85_chi_son_1", "Chí Sơn 1", "Chí Sơn 1", "sg85_chi_son_1.ttf"),
    ("sg85_chi_son_2", "Chí Sơn 2", "Chí Sơn 2", "sg85_chi_son_2.ttf"),
    ("sg85_hien_khanh_1", "Hiền Khánh 1", "Hiền Khánh 1", "sg85_hien_khanh_1.ttf"),
    ("sg85_hien_khanh_2", "Hiền Khánh 2", "Hiền Khánh 2", "sg85_hien_khanh_2.ttf"),
    ("sg85_hien_khanh_3", "Hiền Khánh 3", "Hiền Khánh 3", "sg85_hien_khanh_3.ttf"),
    ("sg85_hong_ky_1", "Hồng Ký 1", "Hồng Ký 1", "sg85_hong_ky_1.ttf"),
    ("sg85_hong_ky_2", "Hồng Ký 2", "Hồng Ký 2", "sg85_hong_ky_2.ttf"),
    ("sg85_phat_tai", "Phát Tài", "Phát Tài", "sg85_phat_tai.ttf"),
]

_families = {}


def user_dir():
    d = app_info.data_dir() / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def custom():
    out = []
    try:
        for f in sorted(os.listdir(user_dir())):
            if f.lower().endswith((".ttf", ".otf")):
                n = os.path.splitext(f)[0]
                out.append(("file:" + f, n, n, None))
    except OSError:
        pass
    return out


def all_fonts():
    return BUILT_IN + custom()


def name(key):
    for k, en, vi, _f in all_fonts():
        if k == key:
            return t(en, vi)
    return t("Computer Default", "Mặc Định Của Máy")


def family(key):
    """Qt family name for a font key, or None for the computer's default."""
    if not key or key == "default":
        return None
    if key in _families:
        return _families[key]
    path = None
    if key.startswith("file:"):
        path = str(user_dir() / key[5:])
    else:
        for k, _en, _vi, f in BUILT_IN:
            if k == key and f:
                path = app_info.asset(os.path.join("fonts", "Saigon1985", f))
    fam = None
    if path and os.path.exists(path):
        fid = QFontDatabase.addApplicationFont(path)
        if fid >= 0:
            fams = QFontDatabase.applicationFontFamilies(fid)
            fam = fams[0] if fams else None
    _families[key] = fam
    return fam


def title_font(px=16, bold=True):
    f = QFont()
    fam = family(Prefs.fontTitle.value)
    if fam:
        f.setFamily(fam)
    f.setPixelSize(max(1, int(px)))
    f.setBold(bold and not fam)
    return f


def body_family():
    return family(Prefs.fontBody.value)


def import_font(path):
    """'+ Thêm Font Từ Máy': copies the .ttf / .otf into the app folder and checks it opens. Returns the key or None."""
    base = os.path.basename(path)
    nm = re.sub(r"[^\w .-]", "_", base)
    if not nm.lower().endswith((".ttf", ".otf")):
        nm += ".ttf"
    dst = user_dir() / nm
    try:
        shutil.copyfile(path, dst)
    except OSError:
        return None
    fid = QFontDatabase.addApplicationFont(str(dst))
    if fid < 0:
        try:
            dst.unlink()
        except OSError:
            pass
        return None
    QFontDatabase.removeApplicationFont(fid)
    key = "file:" + nm
    _families.pop(key, None)
    return key


def remove(key):
    if not key.startswith("file:"):
        return
    try:
        (user_dir() / key[5:]).unlink()
    except OSError:
        pass
    _families.pop(key, None)
    if Prefs.fontTitle.value == key:
        Prefs.fontTitle.value = "default"
    if Prefs.fontBody.value == key:
        Prefs.fontBody.value = "default"
