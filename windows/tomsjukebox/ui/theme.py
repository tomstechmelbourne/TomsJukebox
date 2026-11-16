"""The looks of Tom's Technology Solutions (4 standard looks + the Android colour themes and the 70 Bộ Chủ Đề colours). Every colour comes from here (no hard-coded colours in widgets)."""
from PySide6.QtGui import QColor, QPalette

NAVY, NAVY_D, NAVY_L = "#0D2C40", "#071A26", "#1E4A63"
TEAL, SKY, ORANGE, ON_ORANGE = "#0E88AA", "#48B0C8", "#FBB040", "#2A1A00"

THEMES = {
    "tts": dict(name="th_tts", bg="#F4F8FA", card="#FFFFFF", line="#DCE8EE", ink="#0F2A38", muted="#4F6B79",
                top="#0D2C40", top2="#071A26", top_ink="#FFFFFF", top_muted="#9FC3D3", nav="#FFFFFF", nav_sel="#E3F2F7",
                nav_ink="#0F2A38", accent=ORANGE, on_accent=ON_ORANGE, teal=TEAL, sky=SKY, player="#0D2C40",
                player_ink="#FFFFFF", player_muted="#9FC3D3", sel="#CDE9F2", radius=10, big_radius=14, head=20,
                input="#FFFFFF", grey="#9AAAB3", dark=False),
    "glass": dict(name="th_glass", bg="#E6F1F6", card="rgba(255,255,255,0.72)", line="rgba(13,44,64,0.12)", ink="#0F2A38",
                  muted="#4F6B79", top="rgba(13,44,64,0.86)", top2="rgba(7,26,38,0.86)", top_ink="#FFFFFF", top_muted="#B5D6E3",
                  nav="rgba(255,255,255,0.55)", nav_sel="rgba(72,176,200,0.25)", nav_ink="#0F2A38", accent=ORANGE,
                  on_accent=ON_ORANGE, teal=TEAL, sky=SKY, player="rgba(13,44,64,0.90)", player_ink="#FFFFFF",
                  player_muted="#B5D6E3", sel="rgba(72,176,200,0.30)", radius=14, big_radius=18, head=21,
                  input="rgba(255,255,255,0.85)", grey="#8FA3AD", dark=False),
    "soft": dict(name="th_soft", bg="#F2F4F7", card="#FFFFFF", line="#E3E8EE", ink="#111D27", muted="#5D6B76",
                 top="#F7F9FB", top2="#F7F9FB", top_ink="#0D2C40", top_muted="#5D6B76", nav="#F2F4F7", nav_sel="#FFFFFF",
                 nav_ink="#111D27", accent=ORANGE, on_accent=ON_ORANGE, teal=TEAL, sky=SKY, player="#FFFFFF",
                 player_ink="#111D27", player_muted="#5D6B76", sel="#E4F1F6", radius=18, big_radius=26, head=26,
                 input="#FFFFFF", grey="#A3AEB7", dark=False),
    "dark": dict(name="th_dark", bg="#0B1A24", card="#122633", line="#1F3A4A", ink="#E6F0F4", muted="#93AEBB",
                 top="#071A26", top2="#05121B", top_ink="#FFFFFF", top_muted="#93AEBB", nav="#0E202C", nav_sel="#183446",
                 nav_ink="#E6F0F4", accent=ORANGE, on_accent=ON_ORANGE, teal="#2BA3C4", sky=SKY, player="#071A26",
                 player_ink="#FFFFFF", player_muted="#93AEBB", sel="#1E4A63", radius=12, big_radius=18, head=21,
                 input="#0E202C", grey="#5C7482", dark=True),
}
ORDER = ["tts", "glass", "soft", "dark"]          # High Contrast removed (Tom, 08/11/2026)

# Android colour-theme keys that are the 4 standard looks
ANDROID_TO_LOOK = {"toms": "tts", "frosted": "glass", "soft": "soft", "dark": "dark"}
LOOK_TO_ANDROID = {v: k for k, v in ANDROID_TO_LOOK.items()}


def _hex(c, a=None):
    r, g, b = int(c.r * 255), int(c.g * 255), int(c.b * 255)
    if a is None:
        return "#%02X%02X%02X" % (r, g, b)
    return "rgba(%d,%d,%d,%.2f)" % (r, g, b, a)


def from_jtheme(jt):
    """Look dict for any Android colour theme (11 themes, custom colour, 70 Bộ Chủ Đề)."""
    if jt.key in ANDROID_TO_LOOK:
        return ANDROID_TO_LOOK[jt.key]
    from ..art.ds import Color
    key = "a:" + jt.key
    light = jt.light
    top, bot = jt.top, jt.bottom
    acc = jt.accent
    if light:
        card = Color(1, 1, 1)
        bg = top
        line = Color.lerp(top, Color(0, 0, 0), 0.10)
    else:
        bg = Color.lerp(top, bot, 0.35)
        card = Color.lerp(bg, Color(1, 1, 1), 0.07)
        line = Color.lerp(bg, Color(1, 1, 1), 0.16)
    ink, muted = jt.text, jt.muted
    nav = jt.nav if jt.nav.a > 0.9 else Color.lerp(bg, Color(0, 0, 0), 0.3)
    sel = Color.lerp(card, acc, 0.28)
    d = dict(name=jt.key, bg=_hex(bg), card=_hex(card), line=_hex(line), ink=_hex(ink), muted=_hex(muted),
             top=_hex(top if not light else Color.lerp(top, Color(1, 1, 1), 0.4)), top2=_hex(bot if not light else top),
             top_ink="#FFFFFF" if not light else _hex(ink), top_muted=_hex(muted), nav=_hex(nav), nav_sel=_hex(sel),
             nav_ink=_hex(ink), accent=_hex(acc), on_accent=_hex(jt.onAccent), teal=_hex(acc), sky=_hex(Color.lerp(acc, Color(1, 1, 1), 0.3)),
             player=_hex(nav), player_ink="#FFFFFF" if not light else _hex(ink), player_muted=_hex(muted), sel=_hex(sel),
             radius=12, big_radius=18, head=21, input=_hex(card), grey=_hex(Color.lerp(muted, bg, 0.4)), dark=not light)
    THEMES[key] = d
    return key

BAR_COLORS = [("Tom's Orange", "Cam Tom's", "#FBB040"), ("Emerald", "Xanh Lục Bảo", "#2ECC8F"),
              ("Turquoise", "Xanh Ngọc", "#2BC4C4"), ("Sky Blue", "Xanh Trời", "#48B0C8"),
              ("Blue", "Xanh Dương", "#4F8FF0"), ("Lavender", "Tím Oải Hương", "#A78BFA"),
              ("Peach Pink", "Hồng Đào", "#F472B6"), ("Ruby Red", "Đỏ Ruby", "#EF4444"),
              ("Lime Yellow", "Vàng Chanh", "#E8D44D"), ("Pearl White", "Trắng Ngọc Trai", "#F4F1EA"),
              ("From Album Cover", "Theo Ảnh Bìa", "cover")]

FONT_PT = [10.0, 11.5, 13.0]

CUR = {"key": "soft", "c": THEMES["soft"], "step": 0}


def set_current(key, dark=False, step=0):
    if dark and key not in ("dark",):
        key = "dark"
    CUR["key"] = key if key in THEMES else "tts"
    CUR["c"] = THEMES[CUR["key"]]
    CUR["step"] = max(0, min(2, int(step)))
    return CUR["c"]


def c(name):
    return CUR["c"][name]


def pt(extra=0.0):
    return FONT_PT[CUR["step"]] + extra


def palette():
    t = CUR["c"]

    def col(v):
        if v.startswith("rgba"):
            nums = [float(x) for x in v[5:-1].split(",")]
            return QColor(int(nums[0]), int(nums[1]), int(nums[2]))
        return QColor(v)
    p = QPalette()
    bg, card, ink = col(t["bg"]), col(t["card"]) if not t["card"].startswith("rgba") else col("#FFFFFF" if not t["dark"] else "#122633"), col(t["ink"])
    for role, v in ((QPalette.Window, bg), (QPalette.Base, card), (QPalette.AlternateBase, bg),
                    (QPalette.WindowText, ink), (QPalette.Text, ink), (QPalette.ButtonText, ink),
                    (QPalette.Button, card), (QPalette.ToolTipBase, card), (QPalette.ToolTipText, ink),
                    (QPalette.Highlight, col(t["teal"])), (QPalette.HighlightedText, QColor("#FFFFFF")),
                    (QPalette.PlaceholderText, col(t["muted"])), (QPalette.Link, col(t["teal"]))):
        p.setColor(role, v)
    p.setColor(QPalette.Disabled, QPalette.Text, col(t["grey"]))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, col(t["grey"]))
    p.setColor(QPalette.Disabled, QPalette.WindowText, col(t["grey"]))
    return p


def qss():
    t = CUR["c"]
    f = pt()
    r, R = t["radius"], t["big_radius"]
    top_btn_hover = "rgba(255,255,255,0.12)" if t["top_ink"] == "#FFFFFF" else "rgba(13,44,64,0.08)"
    return f"""
* {{ font-family: "Segoe UI", "Noto Sans", Arial; font-size: {f}pt; color: {t['ink']}; }}
QMainWindow, QDialog, #Body, #PageArea {{ background: {t['bg']}; }}
QWidget#Page, QScrollArea, QScrollArea > QWidget > QWidget, QStackedWidget, QTabWidget::pane > QWidget {{ background: {t['bg']}; }}
QToolTip {{ background: {t['card'] if not t['card'].startswith('rgba') else '#FFFFFF'}; color: {t['ink']}; border: 1px solid {t['line']}; padding: 4px; }}

#TopBar {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {t['top']}, stop:1 {t['top2']});
          border-bottom: 1px solid {t['line']}; }}
#TopBar QLabel {{ color: {t['top_ink']}; }}
#TopBar QLabel#BrandTom {{ color: {SKY}; font-family: Bahnschrift, "Segoe UI"; font-weight: 700; font-size: {f + 6}pt; }}
#TopBar QLabel#BrandName {{ color: {ORANGE}; font-family: Bahnschrift, "Segoe UI"; font-weight: 700; font-size: {f + 6}pt; }}
#TopBar QLabel#Slogan {{ color: {t['top_muted']}; font-size: {f - 1.5}pt; }}
#TopBar QToolButton {{ color: {t['top_ink']}; background: transparent; border: none; border-radius: {r}px;
                      padding: 6px 9px; font-weight: 600; }}
#TopBar QToolButton:hover {{ background: {top_btn_hover}; }}
#TopBar QToolButton:checked {{ background: {t['accent']}; color: {t['on_accent']}; }}
#TopBar QLineEdit {{ background: {t['input']}; color: {t['ink']}; border: 1px solid {t['line']}; border-radius: {R}px;
                    padding: 7px 14px; min-width: 260px; }}

#SideNav {{ background: {t['nav']}; border-right: 1px solid {t['line']}; }}
#SideNav QToolButton {{ text-align: left; background: transparent; border: none; border-radius: {r}px; padding: 7px 12px;
                       color: {t['nav_ink']}; font-size: {f + 0.5}pt; }}
#SideNav QToolButton:hover {{ background: {t['nav_sel']}; }}
#SideNav QToolButton:checked {{ background: {t['nav_sel']}; color: {t['on_accent'] if CUR['key'] == 'contrast' else t['teal']}; font-weight: 700; border-left: 4px solid {t['accent']}; }}
#SideNav QLabel#NavGroup {{ color: {t['muted']}; font-size: {f - 1}pt; font-weight: 700; padding: 8px 12px 1px 12px; }}

QLabel#H1 {{ font-size: {f + t['head'] - 10}pt; font-weight: 700; color: {t['ink']}; }}
QLabel#H2 {{ font-size: {f + 3}pt; font-weight: 700; color: {t['ink']}; }}
QLabel#Muted {{ color: {t['muted']}; }}
QLabel#Hint {{ color: {t['muted']}; font-size: {f - 0.5}pt; }}
QLabel#Badge {{ background: {t['accent']}; color: {t['on_accent']}; border-radius: 9px; padding: 2px 10px; font-weight: 700; }}
QLabel#TealBadge {{ background: {t['teal']}; color: #FFFFFF; border-radius: 9px; padding: 2px 10px; font-weight: 700; }}
QFrame#Card {{ background: {t['card']}; border: 1px solid {t['line']}; border-radius: {R}px; }}
QFrame#Strip {{ background: {t['sel']}; border-radius: {r}px; }}

QPushButton {{ background: {t['card']}; border: 1px solid {t['line']}; border-radius: {r}px; padding: 8px 16px; font-weight: 600; }}
QPushButton:hover {{ border-color: {t['teal']}; }}
QPushButton:disabled {{ color: {t['grey']}; }}
QPushButton#Primary {{ background: {t['accent']}; color: {t['on_accent']}; border: none; }}
QPushButton#Primary:hover {{ background: {'#FFC566' if t['accent'] == ORANGE else t['accent']}; }}
QPushButton#Teal {{ background: {t['teal']}; color: #FFFFFF; border: none; }}
QPushButton#Danger {{ color: #C0392B; }}
QToolButton {{ border-radius: {r}px; padding: 5px; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit, QDateEdit, QPlainTextEdit, QTextEdit {{
    background: {t['input']}; border: 1px solid {t['line']}; border-radius: {r}px; padding: 6px 8px; color: {t['ink']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {t['card'] if not t['card'].startswith('rgba') else '#FFFFFF'}; color: {t['ink']};
    selection-background-color: {t['teal']}; selection-color: #FFFFFF; }}
QCheckBox, QRadioButton {{ spacing: 8px; }}

QTableView, QTreeView, QListView, QListWidget, QTreeWidget, QTableWidget {{
    background: {t['card'] if not t['card'].startswith('rgba') else ('#FFFFFF' if not t['dark'] else '#122633')};
    alternate-background-color: {t['bg']}; border: 1px solid {t['line']}; border-radius: {r}px;
    selection-background-color: {t['sel']}; selection-color: {t['ink']}; gridline-color: {t['line']}; outline: 0; }}
QListView#Grid {{ background: {t['bg']}; border: none; }}
QHeaderView::section {{ background: {t['bg']}; color: {t['muted']}; border: none; border-bottom: 1px solid {t['line']};
    padding: 7px 6px; font-weight: 700; }}
QTableView::item, QTreeView::item, QListWidget::item {{ padding: 4px; }}

QTabWidget::pane {{ border: 1px solid {t['line']}; border-radius: {r}px; background: {t['bg']}; top: -1px; }}
QTabBar::tab {{ background: transparent; padding: 8px 16px; border-radius: {r}px; margin: 2px; color: {t['muted']}; font-weight: 600; }}
QTabBar::tab:selected {{ background: {t['card'] if not t['card'].startswith('rgba') else '#FFFFFF'}; color: {t['teal']}; border: 1px solid {t['line']}; }}

QScrollBar:vertical {{ background: {t['bg']}; width: 14px; margin: 2px; border-radius: 6px; }}
QScrollBar::handle:vertical {{ background: {t['teal']}; min-height: 40px; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: {t['accent']}; }}
QScrollBar:horizontal {{ background: {t['bg']}; height: 14px; margin: 2px; border-radius: 6px; }}
QScrollBar::handle:horizontal {{ background: {t['teal']}; min-width: 40px; border-radius: 5px; }}
QScrollBar::handle:horizontal:hover {{ background: {t['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSlider::groove:horizontal {{ height: 6px; background: {t['line']}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {t['teal']}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {t['accent']}; width: 16px; margin: -6px 0; border-radius: 8px; }}
QSlider::groove:vertical {{ width: 6px; background: {t['line']}; border-radius: 3px; }}
QSlider::add-page:vertical {{ background: {t['teal']}; border-radius: 3px; }}
QSlider::handle:vertical {{ background: {t['accent']}; height: 16px; margin: 0 -6px; border-radius: 8px; }}

#PlayerBar {{ background: transparent; }}
#Pill {{ background: {t['player']}; border-radius: 34px; border: 1px solid {t['line']}; }}
#Pill QLabel {{ color: {t['player_ink']}; }}
#Pill QLabel#PillSub {{ color: {t['player_muted']}; font-size: {f - 0.5}pt; }}
#Pill QToolButton {{ color: {t['player_ink']}; background: transparent; border: none; border-radius: 18px; padding: 6px; }}
#Pill QToolButton:hover {{ background: {'rgba(255,255,255,0.12)' if t['player_ink'] == '#FFFFFF' else 'rgba(0,0,0,0.06)'}; }}
#Pill QToolButton:checked {{ color: {t['accent']}; }}
#Pill QToolButton#PlayBtn {{ background: {t['player_ink']}; color: {t['player']}; border-radius: 24px; }}

QStatusBar {{ background: {t['bg']}; border-top: 1px solid {t['line']}; }}
QStatusBar QLabel {{ color: {t['muted']}; padding: 0 6px; }}
QStatusBar QToolButton {{ border: none; color: {t['ink']}; padding: 3px 10px; font-weight: 600; }}
QStatusBar QToolButton:hover {{ color: {t['teal']}; }}
QMenu {{ background: {t['card'] if not t['card'].startswith('rgba') else '#FFFFFF'}; border: 1px solid {t['line']}; padding: 6px; border-radius: {r}px; }}
QMenu::item {{ padding: 7px 26px 7px 14px; border-radius: 6px; color: {t['ink']}; }}
QMenu::item:selected {{ background: {t['sel']}; }}
QMenu::separator {{ height: 1px; background: {t['line']}; margin: 4px 8px; }}
QProgressBar {{ border: 1px solid {t['line']}; border-radius: 6px; text-align: center; background: {t['card'] if not t['card'].startswith('rgba') else '#FFFFFF'}; }}
QProgressBar::chunk {{ background: {t['teal']}; border-radius: 5px; }}
"""
