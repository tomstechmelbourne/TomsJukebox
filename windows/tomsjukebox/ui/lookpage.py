"""Tab "Giao Diện": every look setting of the Android app in one place — Bộ Chủ Đề and the 7 style pickers, player style,
visualisation, edge lighting, record button, fonts, tab effects and the opening animation."""
from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLayout, QMenu, QPushButton,
                               QScrollArea, QSlider, QToolButton, QVBoxLayout, QWidget)

from ..art import fonts
from ..art.buttons import RecArt
from ..art.ds import DS, Color
from ..art.edge import drawEdge, edgeColours, paint_edge
from ..art.prefs import Prefs
from ..art.skins import PillColours, SkinList
from ..art.state import Core
from ..art.themes import EdgeEffects, Motifs, Skins, t
from . import theme
from .artplayer import WaveColours, clock, ticker
from .picker import CATS, current, name_of, swatch, title


class FlowLayout(QLayout):
    def __init__(self, parent=None, spacing=6):
        super().__init__(parent)
        self.items = []
        self.sp = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, i):
        return self.items[i] if 0 <= i < len(self.items) else None

    def takeAt(self, i):
        return self.items.pop(i) if 0 <= i < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._do(QRect(0, 0, w, 0), True)

    def setGeometry(self, r):
        super().setGeometry(r)
        self._do(r, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self.items:
            s = s.expandedTo(it.minimumSize())
        return s

    def _do(self, r, test):
        x, y, lh = r.x(), r.y(), 0
        for it in self.items:
            hint = it.sizeHint()
            if x + hint.width() > r.right() and lh > 0:
                x = r.x()
                y += lh + self.sp
                lh = 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self.sp
            lh = max(lh, hint.height())
        return y + lh - r.y()


def chip(text, on, cb):
    b = QToolButton()
    b.setText(text)
    b.setCheckable(True)
    b.setChecked(on)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(cb)
    return b


class Swatch(QWidget):
    clicked = Signal()

    def __init__(self, cat):
        super().__init__()
        self.cat = cat
        self.setFixedSize(64, 42)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 10, 10)
        p.setClipPath(clip)
        cur = current(self.cat)
        try:
            if cur == "pack" or cur == "none":
                swatch(p, self.width(), self.height(), "pack", "m:%d" % (Motifs.of("pack") or 0))
            elif cur:
                swatch(p, self.width(), self.height(), self.cat, cur)
            else:
                p.fillRect(self.rect(), QColor(0x0B, 0x17, 0x20))
        except Exception:
            p.fillRect(self.rect(), QColor(0x0B, 0x17, 0x20))
        p.end()

    def mouseReleaseEvent(self, e):
        self.clicked.emit()


class HueBar(QWidget):
    """Pick a colour by sliding along the rainbow."""
    changed = Signal(int)

    def __init__(self, value):
        super().__init__()
        self.setFixedHeight(26)
        self.setCursor(Qt.PointingHandCursor)
        c = QColor((value >> 16) & 255, (value >> 8) & 255, value & 255)
        self.h = max(0, c.hsvHue())

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        for i in range(7):
            g.setColorAt(i / 6, QColor.fromHsv(int(i * 60) % 360, 205, 255))
        r = QRectF(12, 8, self.width() - 24, 10)
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(r, 5, 5)
        x = r.left() + r.width() * self.h / 359
        p.setBrush(QColor.fromHsv(self.h, 190, 255))
        p.setPen(QPen(QColor("white"), 2))
        p.drawEllipse(QRectF(x - 9, 4, 18, 18))
        p.end()

    def _set(self, x):
        r = self.width() - 24
        self.h = int(max(0, min(359, (x - 12) / max(1, r) * 359)))
        c = QColor.fromHsv(self.h, 190, 255)
        self.changed.emit(0xFF000000 | (c.red() << 16) | (c.green() << 8) | c.blue())
        self.update()

    def mousePressEvent(self, e):
        self._set(e.position().x())

    def mouseMoveEvent(self, e):
        self._set(e.position().x())


class EdgePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)
        ticker().tick.connect(self._tick)

    def _tick(self):
        if self.isVisible():
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 14, 14)
        p.setClipPath(clip)
        p.fillRect(self.rect(), QColor(0x0B, 0x17, 0x20))
        eff, mo = Motifs.edgeStyle()
        drawEdge(DS(p, self.width(), self.height()), eff, clock(), 14, mo.colours[1:] if mo is not None else edgeColours(),
                 3, 1.0, EdgeEffects.speeds[max(0, min(4, int(Prefs.edgeSpeed.value)))])
        p.end()


class RecTile(QWidget):
    clicked = Signal(int)

    def __init__(self, i, on):
        super().__init__()
        self.i, self.on = i, on
        self.setFixedSize(84, 74)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(RecArt.name(i))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = QColor(theme.c("accent"))
        p.setPen(QPen(acc, 2) if self.on else Qt.NoPen)
        p.setBrush(QColor(0x0B, 0x17, 0x20))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 12, 12)
        s = 34
        p.save()
        p.translate((self.width() - s) / 2, 8)
        if self.i == 0:
            from ..art.buttons import REC, ButtonArt
            old = Prefs.recStyle._v
            Prefs.recStyle._v = 0
            ButtonArt.draw(p, REC, int(Prefs.btnStyle.value), s, QColor("white"))
            Prefs.recStyle._v = old
        else:
            RecArt.draw(p, False, self.i, s, RecArt.colour())
        p.restore()
        f = QFont()
        f.setPixelSize(10)
        p.setFont(f)
        p.setPen(acc if self.on else QColor("#E6F0F4"))
        p.drawText(QRectF(2, 46, self.width() - 4, 26), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, RecArt.name(self.i))
        p.end()

    def mouseReleaseEvent(self, e):
        self.clicked.emit(self.i)


class FontTile(QWidget):
    clicked = Signal(str)
    remove = Signal(str)

    def __init__(self, key, name, on):
        super().__init__()
        self.key, self.name, self.on = key, name, on
        self.setFixedSize(150, 64)
        self.setCursor(Qt.PointingHandCursor)
        if key.startswith("file:"):
            self.setToolTip(t("Right-click to remove this font", "Nhấn chuột phải để xoá font này"))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = QColor(theme.c("accent"))
        p.setPen(QPen(acc, 2) if self.on else QPen(QColor(theme.c("line")), 1))
        p.setBrush(QColor(theme.c("card")))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 12, 12)
        f = QFont()
        fam = fonts.family(self.key)
        if fam:
            f.setFamily(fam)
        f.setPixelSize(20)
        p.setFont(f)
        p.setPen(QColor(theme.c("ink")))
        p.drawText(QRectF(6, 4, self.width() - 12, 32), Qt.AlignCenter, "Sài Gòn Aa")
        f2 = QFont()
        f2.setPixelSize(11)
        f2.setBold(self.on)
        p.setFont(f2)
        p.setPen(acc if self.on else QColor(theme.c("muted")))
        p.drawText(QRectF(4, 38, self.width() - 8, 22), Qt.AlignCenter, self.name)
        p.end()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton and self.key.startswith("file:"):
            self.remove.emit(self.key)
        elif e.button() == Qt.LeftButton:
            self.clicked.emit(self.key)


class LookPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.setObjectName("Page")
        self.ctx = ctx
        self.db = ctx.db
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 8, 10, 6)
        self.sa = QScrollArea()
        self.sa.setWidgetResizable(True)
        self.sa.setFrameShape(QFrame.NoFrame)
        self.lay.addWidget(self.sa)
        self._rows = {}
        self.rebuild()

    def refresh(self):
        self.rebuild()

    def retranslate(self):
        self.rebuild()

    def refresh_rows(self):
        for cat, (sw, lab) in self._rows.items():
            try:
                sw.update()
                lab.setText(name_of(cat, current(cat)))
            except RuntimeError:
                pass

    # ---- small builders
    def _section(self, v, text, hint_text=None):
        h = QLabel(text)
        h.setObjectName("H2")
        v.addSpacing(6)
        v.addWidget(h)
        if hint_text:
            x = QLabel(hint_text)
            x.setObjectName("Hint")
            x.setWordWrap(True)
            v.addWidget(x)

    def _card(self, v):
        c = QFrame()
        c.setObjectName("Card")
        cv = QVBoxLayout(c)
        cv.setContentsMargins(12, 10, 12, 10)
        cv.setSpacing(6)
        v.addWidget(c)
        return cv

    def _switch(self, v, text, pref, hint_text=None, after=None):
        cb = QCheckBox(text)
        cb.setChecked(bool(pref.value))

        def go(on):
            pref.value = on
            if after:
                after(on)
        cb.toggled.connect(go)
        v.addWidget(cb)
        if hint_text:
            x = QLabel(hint_text)
            x.setObjectName("Hint")
            x.setWordWrap(True)
            v.addWidget(x)
        return cb

    def _slider(self, v, text, lo, hi, val, fmt, setter, steps=100):
        row = QHBoxLayout()
        lab = QLabel(text)
        row.addWidget(lab)
        s = QSlider(Qt.Horizontal)
        s.setRange(0, steps)
        s.setValue(int(round((val - lo) / (hi - lo) * steps)))
        out = QLabel(fmt(val))
        out.setMinimumWidth(70)

        def ch(x):
            fv = lo + (hi - lo) * x / steps
            out.setText(fmt(fv))
            setter(fv)
        s.valueChanged.connect(ch)
        row.addWidget(s, 1)
        row.addWidget(out)
        v.addLayout(row)

    def _chips(self, v, pairs, cur, setter, label=None):
        if label:
            lab = QLabel(label)
            v.addWidget(lab)
        host = QWidget()
        host.setObjectName("LibChips")
        fl = FlowLayout(host)
        for k, n in pairs:
            fl.addWidget(chip(n, k == cur, lambda _=False, kk=k: (setter(kk), self.rebuild())))
        v.addWidget(host)

    # ---- the page
    def rebuild(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(4, 4, 4, 12)
        v.setSpacing(6)
        title_l = QLabel(t("Looks", "Giao Diện"))
        title_l.setObjectName("H1")
        title_l.setFont(fonts.title_font(26))
        v.addWidget(title_l)
        self._rows = {}

        # Bộ Chủ Đề and the style pickers
        self._section(v, t("Theme Packs And Styles", "Bộ Chủ Đề Và Kiểu Dáng"),
                      t("Pick a Theme Pack to change everything at once, or change each part on its own.",
                        "Chọn Bộ Chủ Đề để đổi tất cả một lần, hoặc đổi riêng từng mục."))
        for cat in CATS:
            row = QFrame()
            row.setObjectName("Card")
            h = QHBoxLayout(row)
            h.setContentsMargins(8, 6, 8, 6)
            sw = Swatch(cat)
            sw.clicked.connect(lambda c=cat: self.ctx.show_picker(c))
            h.addWidget(sw)
            col = QVBoxLayout()
            col.setSpacing(0)
            a = QLabel(title(cat))
            a.setStyleSheet("font-weight: 600;")
            b = QLabel(name_of(cat, current(cat)))
            b.setObjectName("Muted")
            col.addWidget(a)
            col.addWidget(b)
            h.addLayout(col, 1)
            btn = QPushButton(t("Change", "Đổi"))
            btn.setObjectName("Primary")
            btn.clicked.connect(lambda _=False, c=cat: self.ctx.show_picker(c))
            h.addWidget(btn)
            v.addWidget(row)
            self._rows[cat] = (sw, b)
        cv = self._card(v)
        bt = QPushButton(t("Custom Theme Colour", "Màu Giao Diện Tự Chọn"))
        bt.clicked.connect(lambda: (setattr(Prefs.theme, "value", "custom"), self.rebuild()))
        cv.addWidget(bt)
        if Prefs.theme.value == "custom":
            hb = HueBar(int(Prefs.customAccent.value))
            hb.changed.connect(lambda c: setattr(Prefs.customAccent, "value", c))
            cv.addWidget(hb)
        sk = Prefs.skin.value
        if sk == "xp":
            self._chips(cv, Skins.xpColours(), Prefs.xpColour.value, lambda k: setattr(Prefs.xpColour, "value", k), t("XP colour", "Màu XP"))
        elif sk == "grain":
            self._chips(cv, [(i, t(*n)) for i, n in enumerate(SkinList.woodTypes)], Prefs.woodType.value, lambda k: setattr(Prefs.woodType, "value", k), t("Wood", "Loại gỗ"))
        elif sk == "marble":
            self._chips(cv, [(i, t(*n)) for i, n in enumerate(SkinList.marbleTypes)], Prefs.marbleType.value, lambda k: setattr(Prefs.marbleType, "value", k), t("Marble", "Loại đá"))
        elif sk in ("pill", "slim"):
            self._chips(cv, [(i, PillColours.name(i)) for i in range(len(PillColours.list))], Prefs.pillColour.value,
                        lambda k: setattr(Prefs.pillColour, "value", k), t("Pill colour (or double-click the pill)", "Màu viên thuốc (hoặc nhấp 2 lần vào viên thuốc)"))
        self._slider(cv, t("Pill Transparency", "Độ Trong Suốt Viên Thuốc"), 0, 0.95, 1 - float(Prefs.pillAlpha.value), lambda x: f"{int(x * 100)}%",
                     lambda x: setattr(Prefs.pillAlpha, "value", 1 - x))
        self._slider(cv, t("Wave Strength", "Độ Đậm Sóng Nhạc"), 0, 1.6, float(Prefs.waveStrength.value), lambda x: f"{int(x * 100)}%",
                     lambda x: setattr(Prefs.waveStrength, "value", x))
        self._slider(cv, t("Wave Height", "Độ Cao Sóng"), 0.2, 0.95, float(Prefs.waveHeight.value), lambda x: f"{int(x * 100)}%",
                     lambda x: setattr(Prefs.waveHeight, "value", x))
        self._switch(cv, t("Double-Click The Pill To Change Colour", "Nhấp 2 Lần Vào Viên Thuốc Để Đổi Màu"), Prefs.dblTapColour)
        self._chips(cv, [(0.85, t("Small", "Nhỏ")), (1.0, t("Medium", "Vừa")), (1.2, t("Large", "To")), (1.45, t("Very Large", "Rất To"))],
                    float(Prefs.btnScale.value), lambda k: setattr(Prefs.btnScale, "value", k), t("Button size", "Cỡ nút"))
        if Prefs.btnColour.value == "custom":
            cv.addWidget(QLabel(t("Button colour", "Màu nút")))
            hb = HueBar(int(Prefs.btnCustom.value))
            hb.changed.connect(lambda c: setattr(Prefs.btnCustom, "value", c))
            cv.addWidget(hb)
        if Prefs.barColour.value == "custom":
            cv.addWidget(QLabel(t("Time bar colour", "Màu thanh thời gian")))
            hb = HueBar(int(Prefs.customBar.value))
            hb.changed.connect(lambda c: setattr(Prefs.customBar, "value", c))
            cv.addWidget(hb)

        # player style
        self._section(v, t("Player Style", "Kiểu Thanh Phát Nhạc"),
                      t("Default (Tom's Tech): the cover fills the card, music waves sit on the time bar, buttons in frosted circles.",
                        "Mặc Định (Tom's Tech): ảnh bìa làm nền thẻ, sóng nhạc nằm trên thanh thời gian, nút trong vòng kính mờ."))
        cv = self._card(v)
        self._chips(cv, [("card", t("Default (Tom's Tech)", "Mặc Định (Tom's Tech)")), ("pill", t("Pill", "Viên Thuốc"))],
                    Prefs.playerStyle.value, lambda k: setattr(Prefs.playerStyle, "value", k))
        self._chips(cv, [("cover", t("Cover", "Ảnh Bìa")), ("skin", t("Follow Skin", "Theo Skin")), ("mix", t("Cover + Skin", "Ảnh Bìa + Skin"))],
                    Prefs.cardBg.value, lambda k: setattr(Prefs.cardBg, "value", k), t("Card background:", "Nền thẻ:"))
        self._switch(cv, t("Music Visualisation Behind The Card", "Hiệu Ứng Sóng Nhạc Chạy Sau Thẻ"), Prefs.cardViz)
        self._chips(cv, [(i, t(*n)) for i, n in enumerate(WaveColours.shapes)], int(Prefs.waveShape.value),
                    lambda k: setattr(Prefs.waveShape, "value", k), t("Waves on the time bar – shape:", "Sóng nhạc trên thanh thời gian – kiểu:"))
        self._chips(cv, [(k, t(en, vi)) for k, en, vi in WaveColours.list], Prefs.waveCols.value,
                    lambda k: setattr(Prefs.waveCols, "value", k), t("Colours:", "Màu sắc:"))
        x = QLabel(t("The card also follows Button Style, Button Colour, Edge Light and the Theme Pack you choose.",
                     "Thẻ cũng theo Kiểu Nút, Màu Nút, Ánh Sáng Chạy Viền và Bộ Chủ Đề bạn chọn."))
        x.setObjectName("Hint")
        x.setWordWrap(True)
        cv.addWidget(x)

        # visualisation
        self._section(v, t("Music Visualisation", "Hiệu Ứng Sóng Nhạc"))
        cv = self._card(v)
        self._switch(cv, t("Visualisation On", "Bật Hiệu Ứng Sóng Nhạc"), Prefs.vizOn)
        self._switch(cv, t("Show In The Player", "Hiện Trong Thanh Phát Nhạc"), Prefs.vizPill)
        self._switch(cv, t("Change Automatically (every 20 s, ★ favourites first)", "Tự Đổi Kiểu (mỗi 20 giây, ưu tiên ★ yêu thích)"), Prefs.vizAuto)
        self._slider(cv, t("Speed", "Tốc Độ"), 0.25, 3.0, float(Prefs.vizSpeed.value), lambda x: f"{x:.2f}×", lambda x: setattr(Prefs.vizSpeed, "value", x))
        r = QHBoxLayout()
        b1 = QPushButton(t("Choose Visualisation…", "Chọn Hiệu Ứng…"))
        b1.setObjectName("Primary")
        b1.clicked.connect(lambda: self.ctx.show_picker("viz"))
        b2 = QPushButton(t("Full Screen", "Toàn Màn Hình"))
        b2.clicked.connect(self.ctx.show_visual)
        r.addWidget(b1)
        r.addWidget(b2)
        r.addStretch()
        cv.addLayout(r)

        # edge lighting
        self._section(v, t("Edge Lighting", "Ánh Sáng Chạy Viền"))
        cv = self._card(v)
        self._switch(cv, t("Edge Lighting On", "Bật Ánh Sáng Chạy Viền"), Prefs.edgeOn, t("Only while music is playing.", "Chỉ chạy khi đang phát nhạc."))
        cv.addWidget(EdgePreview())
        self._slider(cv, t("Speed", "Tốc Độ"), 0, 4, int(Prefs.edgeSpeed.value), lambda x: EdgeEffects.speedName(int(round(x))),
                     lambda x: setattr(Prefs.edgeSpeed, "value", int(round(x))), steps=4)
        self._chips(cv, [("cover", t("From Cover", "Theo Ảnh Bìa")), ("rainbow", t("Rainbow", "Cầu Vồng")), ("brand", t("Tom's Colours", "Màu Tom's")),
                         ("custom", t("Custom", "Tự Chọn"))], Prefs.edgeColour.value, lambda k: setattr(Prefs.edgeColour, "value", k), t("Colour", "Màu"))
        if Prefs.edgeColour.value == "custom":
            hb = HueBar(int(Prefs.edgeCustom.value))
            hb.changed.connect(lambda c: setattr(Prefs.edgeCustom, "value", c))
            cv.addWidget(hb)
        self._slider(cv, t("Thickness", "Độ Dày"), 2, 10, float(Prefs.edgeThick.value), lambda x: f"{int(x)}", lambda x: setattr(Prefs.edgeThick, "value", x))
        self._slider(cv, t("Brightness", "Độ Sáng"), 0.2, 1.0, float(Prefs.edgeBright.value), lambda x: f"{int(x * 100)}%", lambda x: setattr(Prefs.edgeBright, "value", x))
        self._chips(cv, [("window", t("Window Edge", "Viền Cửa Sổ")), ("pill", t("Around The Player", "Quanh Thanh Phát Nhạc")), ("both", t("Both", "Cả Hai"))],
                    Prefs.edgeWhere.value, lambda k: setattr(Prefs.edgeWhere, "value", k), t("Where", "Chạy Ở Đâu"))
        self._switch(cv, t("Pulse With The Beat", "Nhấp Nháy Theo Nhịp"), Prefs.edgeBeat)
        self._switch(cv, t("Change Effect Automatically", "Tự Đổi Hiệu Ứng"), Prefs.edgeAuto, t("A new effect every 30 seconds.", "Mỗi 30 giây đổi một kiểu."))
        self._switch(cv, t("Random For Each Song", "Ngẫu Nhiên Mỗi Bài"), Prefs.edgeRandom, after=lambda on: on and setattr(Prefs.edgeAuto, "value", False))

        # record button
        self._section(v, t("Record Button", "Nút Thâu Âm"), t("Used for radio and podcasts.", "Dùng khi nghe radio và podcast."))
        cv = self._card(v)
        host = QWidget()
        fl = FlowLayout(host)
        for i in range(len(RecArt.names)):
            tl = RecTile(i, int(Prefs.recStyle.value) == i)
            tl.clicked.connect(lambda k: (setattr(Prefs.recStyle, "value", k), self.rebuild()))
            fl.addWidget(tl)
        cv.addWidget(host)
        self._chips(cv, [(k, t(en, vi)) for k, en, vi in RecArt.colours], Prefs.recColour.value,
                    lambda k: setattr(Prefs.recColour, "value", k), t("Colour", "Màu"))
        if Prefs.recColour.value == "custom":
            hb = HueBar(int(Prefs.recCustom.value))
            hb.changed.connect(lambda c: setattr(Prefs.recCustom, "value", c))
            cv.addWidget(hb)
        self._switch(cv, t("Blink While Recording", "Nhấp Nháy Khi Đang Thâu"), Prefs.recBlink)

        # fonts
        self._section(v, t("Fonts", "Font Chữ"), t("The brand name TOM'S JUKEBOX always keeps its own font.",
                                                    "Chữ TOM'S JUKEBOX luôn giữ kiểu chữ gốc."))
        for which, pref in ((t("Titles and song names", "Font tiêu đề & tên bài"), Prefs.fontTitle), (t("Normal text", "Font chữ thường"), Prefs.fontBody)):
            cv = self._card(v)
            cv.addWidget(QLabel(which))
            host = QWidget()
            fl = FlowLayout(host)
            for k, en, vi, _f in fonts.all_fonts():
                tl = FontTile(k, t(en, vi), pref.value == k)
                tl.clicked.connect(lambda key, pr=pref: (setattr(pr, "value", key), self.rebuild()))
                tl.remove.connect(self._remove_font)
                fl.addWidget(tl)
            cv.addWidget(host)
        r = QHBoxLayout()
        add = QPushButton("+ " + t("Add Font From This Computer…", "Thêm Font Từ Máy…"))
        add.clicked.connect(self._add_font)
        r.addWidget(add)
        r.addStretch()
        v.addLayout(r)
        x = QLabel(t("Saigon 1985 fonts by Thái Hiệu (Fontzin). Right-click a font you added to remove it.",
                     "Bộ font Saigon 1985 của Thái Hiệu (Fontzin). Nhấn chuột phải vào font bạn đã thêm để xoá."))
        x.setObjectName("Hint")
        x.setWordWrap(True)
        v.addWidget(x)

        # tab effects + opening animation
        self._section(v, t("Tap Effects And Opening", "Hiệu Ứng Khi Bấm Và Khi Mở Chương Trình"))
        cv = self._card(v)
        cur_fx = set((Prefs.navFx.value or "glow").split(","))
        host = QWidget()
        host.setObjectName("LibChips")
        fl = FlowLayout(host)
        for k, en, vi in (("glow", "Light Up", "Sáng Lên"), ("slide", "Sliding Pill", "Viên Thuốc Trượt"), ("bounce", "Gentle Bounce", "Nảy Nhẹ"),
                          ("ripple", "Ripple", "Gợn Sóng"), ("streak", "Running Streak", "Vệt Sáng Chạy"), ("dot", "Glowing Dot", "Chấm Sáng Dưới")):
            def tog(_=False, kk=k):
                s = set((Prefs.navFx.value or "glow").split(","))
                s ^= {kk}
                Prefs.navFx.value = ",".join(sorted(s)) or "glow"
            fl.addWidget(chip(t(en, vi), k in cur_fx, tog))
        cv.addWidget(QLabel(t("When you click a tab (choose several):", "Khi bấm vào các mục (chọn được nhiều kiểu):")))
        cv.addWidget(host)
        self._slider(cv, t("Effect speed", "Tốc độ hiệu ứng"), 0.5, 2.0, float(Prefs.fxSpeed.value), lambda x: f"{x:.1f}×", lambda x: setattr(Prefs.fxSpeed, "value", x))
        self._chips(cv, [(0, t("Icon Blooms", "Icon Nở Ra")), (1, t("Disc Spins In", "Đĩa Quay Vào")), (2, t("Waves Wake Up", "Sóng Nhạc Đánh Thức")),
                         (3, t("Morphing Shapes", "Hình Khối Biến Hình")), (4, t("Cover Colours", "Theo Màu Ảnh Bìa")), (5, t("Random", "Ngẫu Nhiên"))],
                    int(Prefs.splashStyle.value), lambda k: setattr(Prefs.splashStyle, "value", k), t("Opening animation:", "Hiệu ứng khi mở chương trình:"))
        self._switch(cv, t("Show The Opening Animation", "Hiện Hiệu Ứng Khi Mở"), Prefs.splashOn)
        self._switch(cv, t("Fast", "Nhanh"), Prefs.splashFast)
        self._switch(cv, t("Disc Spins With The Beat", "Đĩa Quay Theo Nhịp"), Prefs.spinBeat)
        v.addStretch()
        bar = self.sa.verticalScrollBar().value()
        self.sa.setWidget(page)
        self.sa.verticalScrollBar().setValue(bar)

    def _add_font(self):
        f, _ = QFileDialog.getOpenFileName(self, t("Add Font", "Thêm Font"), "", "Font (*.ttf *.otf)")
        if not f:
            return
        key = fonts.import_font(f)
        if key is None:
            self.ctx.toast(t("This file isn't a font that Windows can open.", "File này không phải font mở được."))
        else:
            self.ctx.toast(t("Font added", "Đã thêm font"))
        self.rebuild()

    def _remove_font(self, key):
        fonts.remove(key)
        self.rebuild()


def _unused():
    return QMenu, Color, Core, paint_edge
