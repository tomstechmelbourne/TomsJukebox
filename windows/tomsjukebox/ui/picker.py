"""The style pickers (same easy page as Android): Bộ Chủ Đề, Màu Giao Diện, Skin, Kiểu Nút, Màu Nút, Ánh Sáng Chạy Viền,
Màu Thanh Thời Gian, Hiệu Ứng Sóng Nhạc — live preview, search, group filters, ★ favourites (right-click), Recent,
🎲 random and ↶ undo."""
import math
import random

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
                               QToolButton, QVBoxLayout, QWidget)

from ..art.buttons import PLAY, ButtonArt, buttonColour
from ..art.ds import DS, Brush, Color, CornerRadius, Offset, Path, Size, Stroke
from ..art.edge import drawEdge, edgeColours
from ..art.prefs import Prefs
from ..art.skins import SkinList, paintSkin, skinStyle
from ..art.state import Core
from ..art.themes import (ORANGE, SKY, TEAL, BarColours, EdgeEffects, Motifs, Themes, VizStyles, paintMotifSkin, t)
from ..art.viz import drawViz
from . import theme
from .artplayer import ArtPlayer, clock, ticker

CATS = ["pack", "theme", "skin", "btn", "btncol", "edge", "bar", "viz"]
SAMPLE = [0.25 + 0.6 * abs(math.sin(i * 0.72 + 0.4)) for i in range(24)]


def title(cat):
    return {"pack": t("Theme Packs", "Bộ Chủ Đề"), "theme": t("Colour Theme", "Màu Giao Diện"), "skin": "Skin",
            "btn": t("Play Buttons", "Kiểu Nút Phát Nhạc"), "btncol": t("Button Colour", "Màu Nút"),
            "edge": t("Edge Lighting", "Ánh Sáng Chạy Viền"), "bar": t("Time Bar Colour", "Màu Thanh Thời Gian")}.get(
        cat, t("Visualisation", "Hiệu Ứng Sóng Nhạc"))


def _motifs():
    return [("m:%d" % i, Motifs.name(i), Motifs.groups(i)) for i in range(len(Motifs.list)) if i not in VizStyles.removed]


def items(cat):
    basic = {"basic"}
    if cat == "pack":
        return _motifs()
    if cat == "theme":
        return [(th.key, th.name, basic) for th in Themes.list] + _motifs()
    if cat == "skin":
        return [(k, SkinList.name(k), basic) for k in SkinList.keys] + _motifs()
    if cat == "btn":
        return [("b:%d" % i, ButtonArt.name(i), basic) for i in range(len(ButtonArt.names))] + _motifs()
    if cat == "btncol":
        return [(k, n, basic) for k, n in (("white", t("White", "Trắng")), ("cover", t("From Cover", "Theo Ảnh Bìa")),
                                            ("theme", t("Theme Colour", "Màu Giao Diện")), ("custom", t("Custom", "Tự Chọn")))] + _motifs()
    if cat == "edge":
        return [("e:%d" % i, EdgeEffects.name(i), basic) for i in range(len(EdgeEffects.names))] + _motifs()
    if cat == "bar":
        return [(v, t(en, vi), basic) for en, vi, v in BarColours.list] + [("custom", t("Custom Colour", "Tự Chọn Màu"), basic)] + _motifs()
    return [("v:%d" % i, VizStyles.name(i), Motifs.groups(i) | (basic if i < 36 else set())) for i in range(VizStyles.count())
            if i not in VizStyles.removed]


def current(cat):
    if cat == "pack":
        return "m:%d" % Prefs.pack.value if Prefs.pack.value >= 0 else "none"
    if cat == "theme":
        return Prefs.theme.value
    if cat == "skin":
        return Prefs.skin.value
    if cat == "btncol":
        return Prefs.btnColour.value
    if cat == "bar":
        return Prefs.barColour.value
    if cat == "btn":
        v = int(Prefs.btnStyle.value)
        return "pack" if v == -1 else ("m:%d" % (v - 100) if v >= 100 else "b:%d" % v)
    if cat == "edge":
        v = int(Prefs.edgeEffect.value)
        return "pack" if v == -1 else ("m:%d" % (v - 100) if v >= 100 else "e:%d" % v)
    return "v:%d" % int(Prefs.viz.value)


def name_of(cat, id_):
    if id_ == "pack":
        i = Motifs.of("pack")
        return t("Follow Theme Pack", "Theo Bộ Chủ Đề") + (" · " + Motifs.name(i) if i is not None else "")
    for k, n, _g in items(cat):
        if k == id_:
            return n
    if cat == "theme" and id_ == "custom":
        return t("Custom Colour", "Màu Tự Chọn")
    if id_ == "none":
        return t("Not chosen – click Change to pick one of 70", "Chưa chọn – bấm Đổi để chọn 1 trong 70 bộ")
    return "—"


def _num(id_):
    try:
        return int(id_.split(":", 1)[1])
    except (IndexError, ValueError):
        return 0


def apply(cat, id_):
    if cat == "pack":
        Motifs.applyPack(_num(id_))
    elif cat == "theme":
        Prefs.theme.value = id_
    elif cat == "skin":
        Prefs.skin.value = id_
    elif cat == "btncol":
        Prefs.btnColour.value = id_
    elif cat == "bar":
        Prefs.barColour.value = id_
    elif cat == "btn":
        Prefs.btnStyle.value = -1 if id_ == "pack" else (100 + _num(id_) if id_.startswith("m:") else _num(id_))
    elif cat == "edge":
        Prefs.edgeEffect.value = -1 if id_ == "pack" else (100 + _num(id_) if id_.startswith("m:") else _num(id_))
        Prefs.edgeAuto.value = False
        Prefs.edgeRandom.value = False
    else:
        Prefs.viz.value = _num(id_)
        Prefs.vizAuto.value = False
    if id_ != "pack":
        Motifs.addRecent(cat, id_)


def snapshot():
    return [Prefs.pack.value, Prefs.theme.value, Prefs.skin.value, Prefs.btnStyle.value, Prefs.btnColour.value,
            Prefs.edgeEffect.value, Prefs.barColour.value, Prefs.viz.value]


def restore(s):
    Prefs.pack.value, Prefs.theme.value, Prefs.skin.value, Prefs.btnStyle.value = s[0], s[1], s[2], s[3]
    Prefs.btnColour.value, Prefs.edgeEffect.value, Prefs.barColour.value, Prefs.viz.value = s[4], s[5], s[6], s[7]


def swatch(p, w, h, cat, id_, light=False, tm=1.3):
    """The little picture on a tile (Android Pickers.swatch)."""
    ds = DS(p, w, h)
    mi = Motifs.of(id_)
    dark = Color(0xFF0B1720)
    if cat == "pack":
        i = mi if mi is not None else 0
        paintMotifSkin(ds, i, 0.0)
        for k, c in enumerate(Motifs.list[i].colours[1:]):
            ds.drawCircle(c, h * 0.11, Offset(w * (0.62 + k * 0.12), h * 0.78))
    elif cat == "theme":
        tm_ = Motifs.theme(mi) if mi is not None else next((x for x in Themes.list if x.key == id_), Themes.list[0])
        ds.drawRect(Brush.verticalGradient([tm_.top, tm_.bottom]))
        ds.drawRoundRect(tm_.card, Offset(w * 0.1, h * 0.18), Size(w * 0.55, h * 0.18), CornerRadius(6))
        ds.drawRoundRect(tm_.card, Offset(w * 0.1, h * 0.44), Size(w * 0.4, h * 0.14), CornerRadius(6))
        ds.drawCircle(tm_.accent, h * 0.14, Offset(w * 0.8, h * 0.75))
    elif cat == "skin":
        ds.drawRect(dark)
        pw, ph = w * 0.9, h * 0.5
        st = skinStyle(id_)
        p.save()
        p.translate(w * 0.05, h * 0.25)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, pw, ph), ph / 2, ph / 2)
        p.save()
        p.setClipPath(clip)
        sub = DS(p, pw, ph)
        paintSkin(sub, 0.0, 0.0, id_)
        p.restore()
        sub = DS(p, pw, ph)
        btn = st.btn if hasattr(st, "btn") else st.button
        sub.drawCircle(btn, ph * 0.18, Offset(pw * 0.82, ph / 2))
        sub.drawRoundRect(st.text.copy(alpha=0.8), Offset(ph * 0.5, ph * 0.38), Size(pw * 0.4, ph * 0.1), CornerRadius(4))
        p.restore()
    elif cat == "btn":
        ds.drawRect(Color(0xFFE9EEF2) if light else dark)
        style = -1 if id_ == "pack" else (100 + mi if mi is not None else _num(id_))
        s = h * 0.62
        p.save()
        p.translate((w - s) / 2, (h - s) / 2)
        ButtonArt.draw(p, PLAY, style, s, QColor(0x1B, 0x27, 0x33) if light else QColor("white"))
        p.restore()
    elif cat == "btncol":
        ds.drawRect(dark)
        if mi is not None:
            c = Motifs.list[mi].accent
        elif id_ == "cover":
            c = Core.palette[0]
        elif id_ == "theme":
            c = Themes.now().accent
        elif id_ == "custom":
            c = Color(int(Prefs.btnCustom.value))
        else:
            c = Color.White
        ds.drawCircle(c, h * 0.3)
        ds.drawCircle(dark, h * 0.12)
    elif cat == "edge":
        ds.drawRoundRect(dark, cornerRadius=CornerRadius(14))
        eff, mo = Motifs.edgeStyle(-1 if id_ == "pack" else (100 + mi if mi is not None else _num(id_)))
        drawEdge(ds, eff, tm, 14, mo.colours[1:] if mo is not None else edgeColours(), 6, 1.0, 1.0)
    elif cat == "bar":
        ds.drawRect(dark)
        cols = BarColours.colours(id_, Core.palette)
        ds.drawRoundRect(Color(0x55FFFFFF), Offset(w * 0.1, h * 0.45), Size(w * 0.8, h * 0.12), CornerRadius(h * 0.06))
        br = Brush.horizontalGradient(cols if len(cols) > 1 else [cols[0], cols[0]], w * 0.1, w * 0.75)
        ds.drawRoundRect(br, Offset(w * 0.1, h * 0.45), Size(w * 0.65, h * 0.12), CornerRadius(h * 0.06))
        ds.drawCircle(Color.White, h * 0.11, Offset(w * 0.75, h * 0.51))
    else:
        ds.drawRect(dark)
        i = _num(id_)
        cols = Motifs.list[i].colours[1:] if i < len(Motifs.list) else [ORANGE, SKY, TEAL]
        drawViz(ds, i, 3.3 if tm == 1.3 else tm, SAMPLE, cols)


class Tile(QWidget):
    chosen = Signal(str)
    starred = Signal(str)

    def __init__(self, cat, id_, name, on, fav, light):
        super().__init__()
        self.cat, self.id_, self.name, self.on, self.fav, self.light = cat, id_, name, on, fav, light
        self.setFixedSize(118, 104)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(name + "\n" + t("Click to use · right-click for ★", "Nhấn để dùng · nhấn chuột phải để ★"))
        self._pm = None
        self._hover = False

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = QColor(theme.c("accent"))
        bg = QColor(acc) if self.on else QColor(theme.c("card"))
        if self.on:
            bg.setAlpha(60)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setPen(QPen(acc, 2) if self.on else (QPen(QColor(theme.c("teal")), 1) if self._hover else Qt.NoPen))
        p.setBrush(bg)
        p.drawRoundedRect(r, 14, 14)
        sr = QRectF(7, 7, self.width() - 14, 58)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(sr, 10, 10)
        p.setClipPath(clip)
        p.translate(sr.topLeft())
        try:
            if self.id_ == "pack":
                i = Motifs.of("pack") or 0
                swatch(p, sr.width(), sr.height(), "pack", "m:%d" % i, self.light)
            else:
                swatch(p, sr.width(), sr.height(), self.cat, self.id_, self.light)
        except Exception:
            pass
        p.restore()
        if self.fav:
            p.setPen(QColor("#FFD54F"))
            f = QFont()
            f.setPixelSize(15)
            p.setFont(f)
            p.drawText(QRectF(sr.right() - 20, sr.top() + 1, 18, 18), Qt.AlignCenter, "★")
        if ":" in self.id_ and _num(self.id_) in Motifs.vn:
            f = QFont()
            f.setPixelSize(8)
            p.setFont(f)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 0x99))
            p.drawRoundedRect(QRectF(sr.left() + 4, sr.top() + 4, 16, 11), 3, 3)
            p.setPen(QColor("white"))
            p.drawText(QRectF(sr.left() + 4, sr.top() + 4, 16, 11), Qt.AlignCenter, "VN")
        f = QFont()
        f.setPixelSize(11)
        f.setBold(self.on)
        p.setFont(f)
        p.setPen(acc if self.on else QColor(theme.c("ink")))
        p.drawText(QRectF(4, 66, self.width() - 8, 36), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, self.name)
        p.end()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.chosen.emit(self.id_)
        elif e.button() == Qt.RightButton and self.id_ != "pack":
            self.starred.emit(self.id_)


class LivePreview(QWidget):
    """Visualisation preview strip (for the viz picker)."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(90)
        ticker().tick.connect(self.update)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 16, 16)
        p.setClipPath(clip)
        p.fillRect(self.rect(), QColor(0x0B, 0x17, 0x20))
        tm = clock()
        st = VizStyles.autoPick(tm) if Prefs.vizAuto.value else int(Prefs.viz.value)
        drawViz(DS(p, self.width(), self.height()), st, tm * VizStyles.speed(), Core.levels if Core.playing else SAMPLE, Core.palette)
        p.end()


class StylePicker(QDialog):
    def __init__(self, win, cat):
        super().__init__(win)
        self.win, self.cat = win, cat
        self.setWindowTitle(title(cat))
        self.resize(640, 760)
        self.query = ""
        self.filter = "all"
        self.undo = None
        v = QVBoxLayout(self)
        v.setSpacing(8)
        top = QHBoxLayout()
        h = QLabel(title(cat))
        h.setObjectName("H2")
        top.addWidget(h, 1)
        rnd = QPushButton("🎲 " + t("Random", "Ngẫu Nhiên"))
        rnd.clicked.connect(self._random)
        top.addWidget(rnd)
        self.b_undo = QPushButton("↶ " + t("Undo", "Hoàn Tác"))
        self.b_undo.setEnabled(False)
        self.b_undo.clicked.connect(self._undo)
        top.addWidget(self.b_undo)
        v.addLayout(top)
        if cat == "viz":
            v.addWidget(LivePreview())
        else:
            self.preview = ArtPlayer(win)
            v.addWidget(self.preview)
        self.now = QLabel("")
        self.now.setObjectName("Muted")
        v.addWidget(self.now)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Search…", "Tìm kiểu…"))
        self.search.textChanged.connect(self._query)
        v.addWidget(self.search)
        chips = QHBoxLayout()
        chips.setSpacing(4)
        self.chips = {}
        self.all = items(cat)
        has_basic = any("basic" in g for _k, _n, g in self.all)
        from .lookpage import FlowLayout
        row = QWidget()
        rl = FlowLayout(row, 4)
        for k, (en, vi) in Motifs.filters:
            if k == "basic" and not has_basic:
                continue
            b = QToolButton()
            b.setText(t(en, vi))
            b.setCheckable(True)
            b.setAutoExclusive(True)
            b.setChecked(k == "all")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, kk=k: self._filter(kk))
            rl.addWidget(b)
            self.chips[k] = b
        row.setObjectName("LibChips")
        v.addWidget(row)
        self.sa = QScrollArea()
        self.sa.setWidgetResizable(True)
        self.sa.setFrameShape(QFrame.NoFrame)
        v.addWidget(self.sa, 1)
        foot = QLabel(t("Click to use · right-click for ★ · ↶ undo", "Nhấn để dùng · nhấn chuột phải để ★ · ↶ hoàn tác"))
        foot.setObjectName("Hint")
        foot.setAlignment(Qt.AlignCenter)
        v.addWidget(foot)
        bb = QHBoxLayout()
        bb.addStretch()
        c = QPushButton(t("Close", "Đóng"))
        c.clicked.connect(self.accept)
        bb.addWidget(c)
        v.addLayout(bb)
        self._fill()

    def _query(self, s):
        self.query = s.strip().lower()
        QTimer.singleShot(150, self._fill)

    def _filter(self, k):
        self.filter = k
        self._fill()

    def _fill(self):
        cur = current(self.cat)
        favs = set(Motifs.favs(self.cat))
        recent = Motifs.recent(self.cat)
        light = Themes.now().light
        shown = [it for it in self.all if self.query in it[1].lower()]
        if self.filter == "fav":
            shown = [it for it in shown if it[0] in favs]
        elif self.filter == "recent":
            shown = sorted([it for it in shown if it[0] in recent], key=lambda it: recent.index(it[0]))
        elif self.filter != "all":
            shown = [it for it in shown if self.filter in it[2]]
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setContentsMargins(4, 4, 4, 4)
        cols = max(3, (self.sa.viewport().width() - 10) // 124)

        def grid_of(lst):
            g = QGridLayout()
            g.setSpacing(6)
            for i, (k, n, _gr) in enumerate(lst):
                tl = Tile(self.cat, k, n, k == cur, k in favs, light)
                tl.chosen.connect(self._choose)
                tl.starred.connect(self._star)
                g.addWidget(tl, i // cols, i % cols)
            g.setColumnStretch(cols, 1)
            return g
        if recent and self.filter == "all" and not self.query:
            lab = QLabel(t("Recent", "Gần Đây"))
            lab.setObjectName("Muted")
            lay.addWidget(lab)
            lay.addLayout(grid_of([it for r in recent for it in self.all if it[0] == r]))
            lab2 = QLabel(t("All Styles", "Tất Cả Các Kiểu") + f" ({len(self.all)})")
            lab2.setObjectName("Muted")
            lay.addWidget(lab2)
        lst = list(shown)
        if self.cat not in ("pack", "viz") and Prefs.pack.value >= 0 and self.filter == "all" and not self.query:
            lst = [("pack", name_of(self.cat, "pack"), set())] + lst
        if lst:
            lay.addLayout(grid_of(lst))
        else:
            e = QLabel(t("Right-click a style to add it to ★ Favourites.", "Nhấn chuột phải vào một kiểu để thêm vào ★ Yêu Thích.")
                       if self.filter == "fav" else t("Nothing found.", "Không tìm thấy kiểu nào."))
            e.setObjectName("Muted")
            lay.addWidget(e)
        lay.addStretch()
        self.sa.setWidget(host)
        self.now.setText(t("Now: ", "Đang chọn: ") + name_of(self.cat, cur))

    def _choose(self, id_):
        self.undo = snapshot()
        self.b_undo.setEnabled(True)
        apply(self.cat, id_)
        self._fill()

    def _star(self, id_):
        Motifs.toggleFav(self.cat, id_)
        self._fill()

    def _random(self):
        pool = [it for it in self.all if self.query in it[1].lower()] or self.all
        self._choose(random.choice(pool)[0])

    def _undo(self):
        if self.undo:
            restore(self.undo)
            self.undo = None
            self.b_undo.setEnabled(False)
            self._fill()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self._fill)


def _unused():
    return QSize, Path, Stroke, buttonColour
