"""Visualisations 70–83: six multicolour ones, four silk ribbons and four northern lights (Android ui/Visuals4.kt)."""
from .ds import ROUND, Brush, Color, CornerRadius, Offset, Path, Size, Stroke, clamp, exp, sin

VIVID = [Color(0xFFFF3B6B), Color(0xFFE040FB), Color(0xFF7C4DFF), Color(0xFF448AFF), Color(0xFF18FFFF), Color(0xFFFFAB40)]


def drawViz4(ds, style, time, lv, cols):
    w, h = ds.size.width, ds.size.height
    n = len(lv)
    pal = VIVID

    def level(fx, shift):
        a = 0.0
        for b in range(5):
            c = (b * 0.21 + 0.08 + shift * 0.05 + time * 0.03 * (1 + shift % 3)) % 1.05
            d = (fx - c) / 0.11
            a += lv[(b * 4 + shift * 3) % n] * exp(-(d * d))
        return min(1.0, a)

    if style == 70:                                                       # Sóng Lụa Đa Sắc
        for li in range(4, -1, -1):
            p = Path().moveTo(0, h)
            for k in range(61):
                fx = k / 60
                y = h * 0.92 - h * 0.75 * level(fx, li) * (0.6 + 0.4 * sin(fx * 3.1416))
                p.lineTo(fx * w, y)
            p.lineTo(w, h).close()
            ds.drawPath(p, Brush.horizontalGradient([pal[li].copy(alpha=0.55), pal[li + 1].copy(alpha=0.45)]))
    elif style == 71:                                                     # Cực Quang Mềm
        for li in range(5):
            for k in range(45):
                fx = k / 44
                v = level(fx, li + 2)
                top = h * (0.15 + 0.25 * sin(fx * 5 + time * 0.6 + li))
                ln = h * (0.25 + 0.55 * v)
                br = Brush.verticalGradient([pal[li].copy(alpha=0), pal[li].copy(alpha=0.35 + 0.3 * v), pal[(li + 1) % 6].copy(alpha=0)], top, top + ln)
                ds.drawLine(br, Offset(fx * w, top), Offset(fx * w, top + ln), w / 44 * 1.2)
    elif style == 72:                                                     # Sóng Đối Xứng Phát Sáng
        mid = h / 2
        for li in range(4):
            up, dn = Path(), Path()
            for k in range(81):
                fx = k / 80
                a = h * 0.45 * level(fx, li) * sin(fx * 3.1416)
                x = fx * w
                if k == 0:
                    up.moveTo(x, mid - a)
                    dn.moveTo(x, mid + a)
                else:
                    up.lineTo(x, mid - a)
                    dn.lineTo(x, mid + a)
            br = Brush.horizontalGradient([pal[li], pal[li + 1], pal[li + 2]])
            ds.drawPath(up, br, alpha=0.25, style=Stroke(10, cap=ROUND))
            ds.drawPath(dn, br, alpha=0.25, style=Stroke(10, cap=ROUND))
            ds.drawPath(up, br, style=Stroke(2.5, cap=ROUND))
            ds.drawPath(dn, br, style=Stroke(2.5, cap=ROUND))
    elif style == 73:                                                     # Cột Bo Tròn Đa Sắc
        bars = 28
        bw = w / bars
        for k in range(bars):
            v = clamp(lv[k % n], 0.04, 1)
            bh = h * 0.9 * v
            x = k * bw + bw * 0.18
            br = Brush.verticalGradient([pal[(k // 5) % 6], pal[(k // 5 + 1) % 6], pal[(k // 5 + 2) % 6]], h / 2 - bh / 2, h / 2 + bh / 2)
            ds.drawRoundRect(br, Offset(x, h / 2 - bh / 2), Size(bw * 0.64, bh), CornerRadius(bw * 0.32))
    elif style == 74:                                                     # Giọt Màu Nhảy
        for k in range(18):
            fx = (k + 0.5) / 18
            v = lv[(k * 4) % n]
            bounce = abs(sin(time * 2.2 + k * 0.7))
            r = min(w / 18, h) * (0.18 + 0.3 * v)
            y = h * 0.85 - (h * 0.6) * v * bounce
            c = pal[k % 6]
            ds.drawCircle(Brush.radialGradient([c.copy(alpha=0.6), Color.Transparent], Offset(fx * w, y), r * 2.6), r * 2.6, Offset(fx * w, y))
            ds.drawCircle(c, r, Offset(fx * w, y))
    elif 76 <= style <= 79:                                               # 4 kiểu dải lụa
        sets = [VIVID,
                [Color(x) for x in (0xFFFFD1DC, 0xFFB388FF, 0xFF80D8FF, 0xFFFFFFFF, 0xFFFFE0B2, 0xFFB9F6CA)],
                [Color(x) for x in (0xFFFF6E40, 0xFFFF4081, 0xFFFFAB40, 0xFFAA00FF, 0xFFFFD740, 0xFFFF8A80)],
                [Color(x) for x in (0xFF00E5FF, 0xFF2979FF, 0xFF1DE9B6, 0xFF651FFF, 0xFF84FFFF, 0xFF00B0FF)]]
        pc = sets[style - 76]
        ribbons = 3 if style == 77 else 5
        for li in range(ribbons):
            pts = 70
            ys = [0.0] * (pts + 1)
            th = [0.0] * (pts + 1)
            for k in range(pts + 1):
                fx = k / pts
                twist = sin(fx * 6 + time * 1.4 + li * 2) if style == 77 else 1.0
                ys[k] = h * (0.5 + 0.28 * sin(fx * (2.2 + li * 0.4) + time * (0.5 + li * 0.12) + li)) - h * 0.25 * level(fx, li)
                th[k] = h * (0.05 + 0.12 * level(fx, li + 1)) * twist
            top = Path()
            for k in range(pts + 1):
                x = w * k / pts
                top.moveTo(x, ys[k] - th[k]) if k == 0 else top.lineTo(x, ys[k] - th[k])
            for k in range(pts, -1, -1):
                top.lineTo(w * k / pts, ys[k] + th[k])
            top.close()
            ds.drawPath(top, Brush.horizontalGradient([pc[li % 6].copy(alpha=0.5), pc[(li + 1) % 6].copy(alpha=0.6), pc[(li + 2) % 6].copy(alpha=0.45)]))
            bot = Path()
            for k in range(pts + 1):
                x = w * k / pts
                bot.moveTo(x, ys[k] - th[k]) if k == 0 else bot.lineTo(x, ys[k] - th[k])
            ds.drawPath(bot, Color.White.copy(alpha=0.55 if style == 78 else 0.3), style=Stroke(1.5))
    elif 80 <= style <= 83:                                               # 4 kiểu bắc cực quang
        sets = [[Color(0xFF00E676), Color(0xFF1DE9B6), Color(0xFF00B0FF)], [Color(0xFFE040FB), Color(0xFFFF4081), Color(0xFF7C4DFF)],
                [Color(0xFF69F0AE), Color(0xFFB388FF), Color(0xFF18FFFF)], [Color(0xFF00E5FF), Color(0xFF76FF03), Color(0xFFEA80FC)]]
        pc = sets[style - 80]
        ds.drawRect(Brush.verticalGradient([Color(0xFF020814), Color(0xFF071B2E)]))
        for k in range(40):
            sx = ((k * 0.618) % 1) * w
            sy = ((k * 0.377) % 1) * h * 0.6
            s2 = sin(time * 2 + k)
            ds.drawCircle(Color.White.copy(alpha=0.3 + 0.4 * s2 * s2), 1.2, Offset(sx, sy))
        for layer in range(3):
            colsN = 60
            for k in range(colsN + 1):
                fx = k / colsN
                v = level(fx, layer + 1)
                base = h * (0.35 + 0.12 * sin(fx * (3 + layer) + time * (0.35 + layer * 0.15) + layer * 2)) + (h * 0.05 * sin(fx * 30 + time * 4) if style == 82 else 0)
                ln = h * (0.18 + 0.45 * v) * (1.3 if style == 81 else 1.0)
                c = pc[layer]
                br = Brush.verticalGradient([c.copy(alpha=0), c.copy(alpha=0.18 + 0.35 * v), c.copy(alpha=0.05)], base - ln * 0.3, base + ln)
                ds.drawLine(br, Offset(fx * w, base - ln * 0.3), Offset(fx * w, base + ln), w / colsN * 1.6)
        if style == 83:
            p = Path().moveTo(0, h)
            for k in range(11):
                p.lineTo(w * k / 10, h * (0.88 if k % 2 == 0 else 0.72) - h * 0.06 * lv[(k * 2) % n])
            p.lineTo(w, h).close()
            ds.drawPath(p, Color(0xFF0B1220))
            for k in range(1, 10, 2):
                x = w * k / 10
                y = h * 0.72 - h * 0.06 * lv[(k * 2) % n]
                ds.drawPath(Path().moveTo(x, y).lineTo(x + w * 0.035, y + h * 0.05).lineTo(x - w * 0.035, y + h * 0.05).close(), Color(0xFFE3F2FD))
    else:                                                                 # Dòng Chảy Neon (75)
        for li in range(6):
            p = Path()
            for k in range(91):
                fx = k / 90
                y = h / 2 + sin(fx * (6 + li) + time * (1.2 + li * 0.25)) * h * 0.38 * (0.2 + level(fx, li))
                p.moveTo(fx * w, y) if k == 0 else p.lineTo(fx * w, y)
            ds.drawPath(p, pal[li], alpha=0.22, style=Stroke(9, cap=ROUND))
            ds.drawPath(p, pal[li], style=Stroke(2.2, cap=ROUND))
