"""Visualisations 36–69: 16 new ones and the Eastern ones (same drawings as Android ui/Visuals3.kt)."""
import math

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont, QPen

from .ds import (PI, ROUND, Brush, Color, CornerRadius, Offset, Path, Size, Stroke, avg, clamp, cos, sin)

TAU = 2 * PI
_GLYPHS = "アイウエオカキクケコ01ガギグ7ザジズ9ナニヌネノ音楽"


def _p(path_builder):
    return path_builder


def drawViz3(ds, style, time, lv, cols):
    w, h = ds.size.width, ds.size.height
    n = len(lv)
    a_ = avg(lv)
    bass = (lv[0] + lv[1] + lv[2]) / 3
    treb = (lv[n - 1] + lv[n - 2] + lv[n - 3]) / 3
    m = min(w, h)
    center = ds.center

    def col(i):
        return cols[((i % len(cols)) + len(cols)) % len(cols)]

    def hash_(k):
        return (k * 0.6180339) % 1

    if style == 36:                                                       # Sen Nở Trên Hồ
        ds.drawRect(Brush.verticalGradient([Color(0xFF0E3B4A), Color(0xFF05202A)], h * 0.55, h), Offset(0, h * 0.55), Size(w, h * 0.45))
        for k in range(5):
            f = (time * 0.3 + k / 5) % 1
            ds.drawOval(Color(0xFF7EC8D8).copy(alpha=(1 - f) * 0.4), Offset(w / 2 - f * w * 0.45, h * 0.7 - f * h * 0.08), Size(f * w * 0.9, f * h * 0.16), style=Stroke(2))
        cx, cy = w / 2, h * 0.66
        opn = 0.4 + bass * 0.6
        for ring in range(3):
            petals = 8 - ring * 2
            ln = m * (0.42 - ring * 0.1) * (0.6 + opn * 0.4)
            for k in range(petals):
                a = -90 + (k - (petals - 1) / 2) * (150 / petals) * (0.5 + opn * 0.5)
                with ds.rotate(a + 90, Offset(cx, cy)):
                    ds.drawOval(Brush.verticalGradient([Color(0xFFFFC1D6), Color(0xFFE8538A)], cy - ln, cy), Offset(cx - ln * 0.17, cy - ln), Size(ln * 0.34, ln))
        ds.drawCircle(Color(0xFFFFE082), m * 0.05, Offset(cx, cy - m * 0.04))
        ds.drawOval(Color(0xFF2E7D32), Offset(w * 0.08, h * 0.78), Size(w * 0.22, h * 0.08))
        ds.drawOval(Color(0xFF388E3C), Offset(w * 0.7, h * 0.82), Size(w * 0.2, h * 0.07))
    elif style == 37:                                                     # Đèn Lồng Hội An
        hues = [0xFFE53935, 0xFFFFB300, 0xFF8E24AA, 0xFF43A047, 0xFF1E88E5, 0xFFF4511E, 0xFFD81B60]
        for k in range(7):
            x = w * (k + 0.5) / 7
            sway = sin(time * 1.3 + k) * 6
            y = h * (0.35 + (k % 2) * 0.12) + sway
            r = m * 0.09 * (1 + lv[k * 3 % n] * 0.35)
            hue = Color(hues[k])
            ds.drawLine(Color(0xFF6D4C41), Offset(x, 0), Offset(x + sway * 0.3, y - r * 1.2), 2)
            ds.drawCircle(Brush.radialGradient([hue.copy(alpha=clamp(0.45 + lv[k] * 0.4, 0, 1)), Color.Transparent], Offset(x, y), r * 2.4), r * 2.4, Offset(x, y))
            ds.drawOval(hue, Offset(x - r * 0.8, y - r * 1.1), Size(r * 1.6, r * 2.2))
            for s in (-1, 0, 1):
                ds.drawLine(Color(0x55000000), Offset(x + s * r * 0.4, y - r), Offset(x + s * r * 0.4, y + r), 1.5)
            ds.drawRect(Color(0xFFFFD54F), Offset(x - r * 0.35, y - r * 1.25), Size(r * 0.7, r * 0.2))
            ds.drawRect(Color(0xFFFFD54F), Offset(x - r * 0.35, y + r * 1.05), Size(r * 0.7, r * 0.2))
            ds.drawLine(Color(0xFFFFD54F), Offset(x, y + r * 1.25), Offset(x, y + r * 1.7), 2)
    elif style == 38:                                                     # Đồng Lúa
        ds.drawRect(Brush.verticalGradient([Color(0xFF8ED1F0), Color(0xFFFFE0A3)], 0, h * 0.5), Offset(0, 0), Size(w, h * 0.5))
        ds.drawCircle(Color(0xFFFFF3B0), m * 0.08, Offset(w * 0.8, h * 0.2))
        for k in range(90):
            x = w * k / 90 + hash_(k) * 6
            v = lv[k % n]
            bend = sin(time * 1.5 + k * 0.2) * (6 + v * 18)
            top = h * (0.45 + hash_(k + 3) * 0.12) - v * h * 0.15
            c = Color(0xFFC9B037) if k % 3 == 0 else Color(0xFF7CB342)
            p = Path().moveTo(x, h).quadraticTo(x + bend * 0.3, (h + top) / 2, x + bend, top)
            ds.drawPath(p, c, style=Stroke(2.2))
            ds.drawOval(Color(0xFFE6C34A), Offset(x + bend - 2, top - 5), Size(4, 9))
    elif style == 39:                                                     # Mưa Hoa Mai
        for k in range(40):
            sp = 0.15 + hash_(k) * 0.2 + a_ * 0.4
            y = ((time * sp + hash_(k * 7)) % 1) * h
            x = hash_(k * 3) * w + sin(time + k) * 20
            r = 4 + hash_(k * 5) * 5 + lv[k % n] * 3
            with ds.rotate(time * 60 + k * 30, Offset(x, y)):
                for pp in range(5):
                    a = pp * TAU / 5
                    ds.drawCircle(Color(0xFFFFD000), r * 0.55, Offset(x + cos(a) * r * 0.6, y + sin(a) * r * 0.6))
            ds.drawCircle(Color(0xFFE65100), r * 0.25, Offset(x, y))
    elif style == 40:                                                     # Đĩa Than Quay
        r = m * 0.44
        c = center
        ds.drawCircle(Color(0xFF111111), r, c)
        for g in range(18):
            ds.drawCircle(Color.White.copy(alpha=0.04 + lv[g % n] * 0.12), r * (0.4 + g * 0.033), c, style=Stroke(1))
        with ds.rotate(time * (120 + bass * 200), c):
            ds.drawArc(Color.White.copy(alpha=0.18), 0, 40, True, c - Offset(r, r), Size(r * 2, r * 2))
            ds.drawArc(Color.White.copy(alpha=0.1), 180, 30, True, c - Offset(r, r), Size(r * 2, r * 2))
        ds.drawCircle(col(0), r * 0.32, c)
        ds.drawCircle(Color(0xFF111111), r * 0.04, c)
        arm = Offset(c.x + r * 1.05, c.y - r * 0.9)
        ds.drawLine(Color(0xFFBDBDBD), arm, Offset(c.x + r * 0.45, c.y + r * 0.25), 6, ROUND)
        ds.drawCircle(Color(0xFF9E9E9E), 10, arm)
    elif style == 41:                                                     # Phím Đàn Piano
        keys = 14
        kw = w / keys
        for k in range(keys):
            v = lv[(k * n // keys) % n]
            down = v > 0.55
            ds.drawRoundRect(col(k) if down else Color(0xFFF7F7F7), Offset(k * kw + 1, h * 0.25 + (4 if down else 0)), Size(kw - 2, h * 0.75), CornerRadius(4))
            ds.drawCircle(col(k).copy(alpha=v * 0.6), kw * 0.5, Offset(k * kw + kw / 2, h * 0.2 - v * h * 0.15))
        for k in range(keys - 1):
            if k % 7 == 2 or k % 7 == 6:
                continue
            v = lv[(k * 2 + 1) % n]
            ds.drawRoundRect(col(k + 3).darken(0.6) if v > 0.6 else Color(0xFF151515), Offset((k + 1) * kw - kw * 0.3, h * 0.25), Size(kw * 0.6, h * 0.45), CornerRadius(3))
    elif style == 42:                                                     # Trống Nhảy
        drums = [(0.2, 0.7, 0.17), (0.5, 0.75, 0.22), (0.8, 0.7, 0.17), (0.35, 0.38, 0.12), (0.65, 0.38, 0.12)]
        for i, (fx, fy, fr) in enumerate(drums):
            v = bass if i == 1 else lv[(i * 5) % n]
            r = m * fr * (1 + v * 0.15)
            cc = Offset(w * fx, h * fy - v * 6)
            ds.drawRect(col(i).darken(0.5), Offset(cc.x - r, cc.y), Size(r * 2, r * 0.6))
            ds.drawOval(Color(0xFFEEEEEE), Offset(cc.x - r, cc.y - r * 0.3), Size(r * 2, r * 0.6))
            ds.drawOval(col(i).copy(alpha=v), Offset(cc.x - r * 1.3, cc.y - r * 0.5), Size(r * 2.6, r), style=Stroke(3))
        for fx in (0.08, 0.92):
            c1 = Offset(w * fx, h * 0.25)
            ds.drawOval(Color(0xFFFFC107).copy(alpha=clamp(0.6 + treb * 0.4, 0, 1)), Offset(c1.x - m * 0.1, c1.y - 6 - treb * 6), Size(m * 0.2, 12))
    elif style == 43:                                                     # Băng Cassette Chạy
        bw = min(w * 0.9, h * 1.6)
        bh = bw * 0.62
        o = Offset((w - bw) / 2, (h - bh) / 2)
        ds.drawRoundRect(Color(0xFF2B2B2B), o, Size(bw, bh), CornerRadius(12))
        ds.drawRoundRect(col(0), o + Offset(bw * 0.06, bh * 0.08), Size(bw * 0.88, bh * 0.25), CornerRadius(6))
        ds.drawRoundRect(Color(0xFF1A1A1A), o + Offset(bw * 0.2, bh * 0.4), Size(bw * 0.6, bh * 0.3), CornerRadius(bh * 0.15))
        for i, fx in enumerate((0.32, 0.68)):
            c = o + Offset(bw * fx, bh * 0.55)
            r = bh * ((0.11 + (time * 0.01 % 0.05)) if i == 0 else (0.15 - (time * 0.01 % 0.05)))
            ds.drawCircle(Color(0xFF5D4037), r, c)
            ds.drawCircle(Color.White, bh * 0.06, c)
            with ds.rotate(time * (200 + a_ * 300), c):
                for s in range(6):
                    a = s * TAU / 6
                    ds.drawLine(Color(0xFF333333), c, c + Offset(cos(a), sin(a)) * (bh * 0.055), 2)
        for i in range(12):
            v = lv[i * 2]
            ds.drawRect(Color.White.copy(alpha=0.8), o + Offset(bw * 0.1 + i * bw * 0.067, bh * 0.3 - v * bh * 0.18), Size(bw * 0.04, v * bh * 0.18))
    elif style == 44:                                                     # Tia Laser Sân Khấu
        for k in range(10):
            src = Offset(w * (0.1 if k % 2 == 0 else 0.9), h)
            a = -PI / 2 + sin(time * (0.7 + k * 0.13) + k) * 0.9
            ln = max(w, h) * 1.4
            end = src + Offset(cos(a), sin(a)) * ln
            v = lv[k * 2 % n]
            ds.drawLine(col(k).copy(alpha=0.15 + v * 0.3), src, end, 10)
            ds.drawLine(col(k).copy(alpha=clamp(0.6 + v * 0.4, 0, 1)), src, end, 2)
    elif style == 45:                                                     # Quả Cầu Disco
        c = Offset(w / 2, h * 0.42)
        r = m * 0.28
        ds.drawLine(Color(0xFF9E9E9E), Offset(c.x, 0), Offset(c.x, c.y - r), 2)
        for k in range(16):
            a = k * TAU / 16 + time * 0.6
            v = lv[k % n]
            ds.drawLine(col(k).copy(alpha=0.12 + v * 0.35), c, c + Offset(cos(a), sin(a)) * max(w, h), 5 + v * 8)
        ds.drawCircle(Color(0xFFB0BEC5), r, c)
        for row in range(-4, 5):
            for cl in range(-6, 7):
                yy = row / 5
                ring = math.sqrt(max(0.0, 1 - yy * yy))
                xx = (((cl / 6 + time * 0.1) % 2) + 2) % 2 - 1
                if abs(xx) > 0.95:
                    continue
                px = c.x + xx * r * ring
                py = c.y + yy * r
                sh = (row * 7 + cl * 3 + int(time * 4)) % 5 == 0
                ds.drawRect(Color.White if sh else Color(0xFF90A4AE).copy(alpha=0.6 + 0.4 * ring), Offset(px - 3, py - 3), Size(6 * max(ring, 0.3), 6))
    elif style == 46:                                                     # Đèn Pha Sân Khấu
        for k in range(5):
            sx = w * (k + 0.5) / 5
            a = sin(time * 0.6 + k * 1.3) * 0.35
            v = lv[k * 4 % n]
            bx = sx + sin(a) * h
            spread = w * (0.12 + v * 0.08)
            p = Path().moveTo(sx - 6, 0).lineTo(sx + 6, 0).lineTo(bx + spread, h).lineTo(bx - spread, h).close()
            ds.drawPath(p, Brush.verticalGradient([col(k).copy(alpha=clamp(0.55 + v * 0.3, 0, 1)), col(k).copy(alpha=0.05)]))
            ds.drawOval(col(k).copy(alpha=clamp(0.35 + v * 0.4, 0, 1)), Offset(bx - spread, h - 14), Size(spread * 2, 20))
    elif style == 47:                                                     # Kính Vạn Hoa
        seg = 12
        for s in range(seg):
            with ds.rotate(s * 360 / seg + time * 8, center):
                for k in range(6):
                    v = lv[(k * 4 + s) % n]
                    d = m * (0.08 + k * 0.07)
                    sz = 6 + v * 18
                    p = Path().moveTo(center.x + d, center.y - sz).lineTo(center.x + d + sz, center.y).lineTo(center.x + d, center.y + sz * 0.3).close()
                    ds.drawPath(p, col(k + s).copy(alpha=clamp(0.55 + v * 0.4, 0, 1)))
    elif style == 48:                                                     # Mưa Chữ Ma Trận
        ds.drawRect(Color(0xFF020A04))
        colsN = max(8, int(w / 14))
        f = QFont("Consolas")
        f.setStyleHint(QFont.Monospace)
        f.setPixelSize(14)
        ds.p.setFont(f)
        for c in range(colsN):
            sp = 0.25 + hash_(c) * 0.5 + lv[c % n] * 0.6
            head = ((time * sp + hash_(c * 13)) % 1.3) * h
            for r in range(14):
                y = head - r * 16
                if y < 0 or y > h:
                    continue
                if r == 0:
                    ds.p.setPen(QPen(QColor(255, 255, 255)))
                else:
                    ds.p.setPen(QPen(QColor(60, 255, 110, int((1 - r / 14) * 255))))
                ds.p.drawText(QPointF(c * 14, y), _GLYPHS[(c * 7 + r + int(time * 6)) % len(_GLYPHS)])
    elif style == 49:                                                     # Cột Sóng 3D Xoay
        rows = 6
        for r in range(rows - 1, -1, -1):
            for i in range(12):
                ang = time * 0.5
                x0 = (i - 6) * m * 0.06
                z = (r - 3) * m * 0.06
                x = x0 * cos(ang) - z * sin(ang)
                zz = x0 * sin(ang) + z * cos(ang)
                sc = 1 / (1.6 + zz / m)
                v = lv[(i * 2 + r) % n]
                bh = v * h * 0.45 * sc
                px = center.x + x * sc * 1.6
                base = h * 0.8 - zz * 0.3
                bwid = m * 0.045 * sc
                ds.drawRect(col(i + r).darken(0.55), Offset(px - bwid / 2 + bwid * 0.3, base - bh - bwid * 0.3), Size(bwid, bh))
                ds.drawRect(col(i + r), Offset(px - bwid / 2, base - bh), Size(bwid, bh))
    elif style == 50:                                                     # Thiên Hà Xoắn Ốc
        for k in range(260):
            arm = k % 3
            d = k / 260
            a = d * 9 + arm * TAU / 3 + time * 0.25
            r = d * m * 0.5
            j = (hash_(k) - 0.5) * 14
            v = lv[k % n]
            base = Color(0xFFFFF3C4) if d < 0.25 else col(arm)
            ds.drawCircle(base.copy(alpha=clamp(0.35 + v * 0.6, 0, 1)), 1.2 + v * 2.5, center + Offset(cos(a) * r + j, sin(a) * r * 0.6 + j))
        rr = m * 0.12 * (1 + bass * 0.5)
        ds.drawCircle(Brush.radialGradient([Color(0xFFFFF8E1), Color.Transparent], center, rr), rr)
    elif style == 51:                                                     # Giọt Nước Rơi
        for k in range(8):
            x = w * (k + 0.5) / 8
            period = 1.6 + hash_(k) * 1.2
            ph = ((time + hash_(k * 3) * 3) % period) / period
            surf = h * 0.8
            v = lv[k * 3 % n]
            if ph < 0.5:
                y = ph / 0.5 * surf
                ds.drawOval(Color(0xFF81D4FA), Offset(x - 4, y - 8), Size(8, 12))
            else:
                f = (ph - 0.5) / 0.5
                ds.drawOval(Color(0xFF81D4FA).copy(alpha=1 - f), Offset(x - f * (40 + v * 50), surf - f * 8), Size(f * (80 + v * 100), f * 16), style=Stroke(2))
            ds.drawLine(Color(0xFF4FC3F7).copy(alpha=0.3), Offset(0, surf), Offset(w, surf), 1.5)

    # ───────────── Phương Đông – Việt Nam ─────────────
    elif style == 52:                                                     # Trống Đồng Đông Sơn
        c = center
        r = m * 0.46
        bronze = Color(0xFFB8860B)
        ds.drawCircle(Brush.radialGradient([Color(0xFFD4A84B), Color(0xFF6B4E16)], c, r), r, c)
        with ds.rotate(time * 6, c):
            for ring in range(1, 7):
                ds.drawCircle(Color(0xFF4A3410), r * ring / 6.5, c, style=Stroke(2))
            star = 14
            sr = r * 0.16 * (1 + bass * 0.4)
            p = Path()
            for k in range(star * 2):
                a = k * PI / star
                rr = sr if k % 2 == 0 else sr * 0.45
                pt = c + Offset(cos(a), sin(a)) * rr
                p.moveTo(pt.x, pt.y) if k == 0 else p.lineTo(pt.x, pt.y)
            p.close()
            ds.drawPath(p, Color(0xFFFFE08A))
            for k in range(10):
                a = k * TAU / 10
                v = lv[k * 2 % n]
                pt = c + Offset(cos(a), sin(a)) * (r * 0.58)
                ds.drawCircle(Color(0xFF4A3410), 5 + v * 4, pt)
                ds.drawLine(Color(0xFF4A3410), pt, pt + Offset(cos(a + 1.2), sin(a + 1.2)) * (r * 0.12), 3)
            for k in range(36):
                a = k * TAU / 36
                ds.drawCircle(Color(0xFF4A3410), 2.5, c + Offset(cos(a), sin(a)) * (r * 0.85))
        ds.drawCircle(bronze.copy(alpha=clamp(0.25 + bass * 0.5, 0, 1)), r, c, style=Stroke(6 + bass * 10))
    elif style == 53:                                                     # Nón Lá Xoay
        for k in range(3):
            c = Offset(w * (0.2 + k * 0.3), h * (0.55 + (k % 2) * 0.1) - lv[k * 6] * 12)
            r = m * (0.2 + (k % 2) * 0.05)
            tilt = sin(time * 1.2 + k) * 0.25
            p = Path().moveTo(c.x, c.y - r * 0.85).lineTo(c.x + r, c.y + r * tilt * 0.3).quadraticTo(c.x, c.y + r * 0.35, c.x - r, c.y - r * tilt * 0.3).close()
            ds.drawPath(p, Brush.linearGradient([Color(0xFFF3E2B3), Color(0xFFC9A75C)], c - Offset(r, r), c + Offset(r, r)))
            with ds.rotate(time * 30 * (1 if k % 2 == 0 else -1), Offset(c.x, c.y - r * 0.85)):
                for s in range(7):
                    a = s * TAU / 7
                    ds.drawLine(Color(0x55704A12), Offset(c.x, c.y - r * 0.85), Offset(c.x + cos(a) * r * 0.2, c.y - r * 0.85 + abs(sin(a)) * r * 0.9), 1.2)
            ds.drawLine(Color(0xFFE53935), Offset(c.x - r * 0.6, c.y), Offset(c.x, c.y + r * 0.5), 2)
            ds.drawLine(Color(0xFFE53935), Offset(c.x + r * 0.6, c.y), Offset(c.x, c.y + r * 0.5), 2)
    elif style == 54:                                                     # Vịnh Hạ Long
        ds.drawRect(Brush.verticalGradient([Color(0xFFB3E5FC), Color(0xFFE1F5FE)], 0, h * 0.6), Offset(0, 0), Size(w, h * 0.6))
        for layer in range(3):
            for k in range(6):
                x = w * (k / 5) + layer * 30 - (time * (4 + layer * 3)) % (w / 5)
                v = lv[(k * 3 + layer) % n]
                hh = h * (0.25 + hash_(k + layer * 7) * 0.25 + v * 0.08) * (1 - layer * 0.15)
                bw = w * 0.07
                g = h * 0.62
                p = Path().moveTo(x - bw, g).cubicTo(x - bw, g - hh, x - bw * 0.3, g - hh * 1.1, x, g - hh).cubicTo(x + bw * 0.4, g - hh * 0.9, x + bw, g - hh * 0.6, x + bw, g).close()
                ds.drawPath(p, Color(0xFF2E5D4B).copy(alpha=0.45 + layer * 0.25))
        ds.drawRect(Brush.verticalGradient([Color(0xFF4FA3B8), Color(0xFF1C5566)], h * 0.62, h), Offset(0, h * 0.62), Size(w, h * 0.38))
        for k in range(20):
            y = h * 0.66 + k * 4
            x0 = (time * 20 + k * 37) % max(1.0, w)
            ds.drawLine(Color.White.copy(alpha=0.15 + lv[k % n] * 0.2), Offset(x0, y), Offset(x0 + 30, y), 1.5)
        bx = (time * 15) % (w + 80) - 40
        by = h * 0.7 + sin(time * 2) * 2
        ds.drawRect(Color(0xFF5D4037), Offset(bx - 22, by), Size(44, 7))
        sail = Path().moveTo(bx, by - 30).lineTo(bx + 16, by - 4).lineTo(bx - 14, by - 4).close()
        ds.drawPath(sail, Color(0xFFD84315))
    elif style == 55:                                                     # Hoa Đào Tết
        br = Path().moveTo(0, h * 0.3).quadraticTo(w * 0.3, h * 0.15, w * 0.55, h * 0.35).quadraticTo(w * 0.75, h * 0.5, w, h * 0.4)
        ds.drawPath(br, Color(0xFF4E342E), style=Stroke(7, cap=ROUND))
        for k in range(14):
            fx = hash_(k)
            x = w * fx
            y = h * (0.3 + sin(fx * 3) * 0.08) + (hash_(k * 5) - 0.5) * 30
            v = lv[k % n]
            r = 8 + v * 6
            for pp in range(5):
                a = pp * TAU / 5 + k
                ds.drawCircle(Color(0xFFF8A5C2), r * 0.6, Offset(x + cos(a) * r * 0.6, y + sin(a) * r * 0.6))
            ds.drawCircle(Color(0xFFD81B60), r * 0.3, Offset(x, y))
        for k in range(30):
            y = ((time * (0.1 + hash_(k) * 0.15 + a_ * 0.3) + hash_(k * 9)) % 1) * h
            x = hash_(k * 2) * w + sin(time * 1.5 + k) * 30
            with ds.rotate(time * 90 + k * 40, Offset(x, y)):
                ds.drawOval(Color(0xFFF8BBD0).copy(alpha=0.85), Offset(x - 4, y - 2.5), Size(8, 5))
    elif style == 56:                                                     # Diều Sáo
        ds.drawRect(Brush.verticalGradient([Color(0xFF64B5F6), Color(0xFFBBDEFB)]))
        kites = [Color(0xFFE53935), Color(0xFFFFB300), Color(0xFF43A047)]
        for k in range(3):
            c = Offset(w * (0.25 + k * 0.25) + sin(time * 0.7 + k * 2) * 25, h * (0.3 + (k % 2) * 0.15) + cos(time * 0.9 + k) * 15 - lv[k * 5] * 10)
            s = m * 0.12
            p = Path().moveTo(c.x, c.y - s).lineTo(c.x + s * 0.75, c.y).lineTo(c.x, c.y + s * 1.2).lineTo(c.x - s * 0.75, c.y).close()
            ds.drawPath(p, kites[k])
            ds.drawLine(Color(0x88000000), Offset(c.x, c.y - s), Offset(c.x, c.y + s * 1.2), 1.2)
            ds.drawLine(Color(0x88000000), Offset(c.x - s * 0.75, c.y), Offset(c.x + s * 0.75, c.y), 1.2)
            tail = Path().moveTo(c.x, c.y + s * 1.2)
            for tt in range(1, 11):
                tail.lineTo(c.x + sin(time * 3 + tt * 0.7) * 8, c.y + s * 1.2 + tt * 7)
            ds.drawPath(tail, Color(0xFFFFEB3B), style=Stroke(2))
            ds.drawLine(Color(0x66FFFFFF), c, Offset(w * 0.5, h), 0.8)
            for r in range(1, 4):
                k2 = s * (0.6 + r * 0.4)
                ds.drawArc(Color.White.copy(alpha=lv[(k * 4 + r) % n] * 0.6), -40, 80, False, c - Offset(k2, k2), Size(s * (1.2 + r * 0.8), s * (1.2 + r * 0.8)), style=Stroke(2))
    elif style == 57:                                                     # Múa Lân
        c = Offset(w / 2 + sin(time * 1.4) * w * 0.1, h * 0.55 - bass * h * 0.1)
        s = m * 0.32
        for k in range(1, 9):
            bx = c.x - k * s * 0.32
            by = c.y + sin(time * 4 - k * 0.6) * 10 + s * 0.25
            ds.drawCircle(Color(0xFFFFB300) if k % 2 == 0 else Color(0xFFE53935), s * 0.22, Offset(bx, by))
        ds.drawRoundRect(Color(0xFFE53935), c - Offset(s * 0.5, s * 0.45), Size(s, s * 0.8), CornerRadius(s * 0.3))
        ds.drawRoundRect(Color(0xFFFFD54F), c - Offset(s * 0.42, s * 0.6), Size(s * 0.84, s * 0.22), CornerRadius(s * 0.1))
        blink = 0.2 if (time * 2 % 3) < 0.15 else 1.0
        for e in (-1, 1):
            ds.drawOval(Color.White, Offset(c.x + e * s * 0.2 - s * 0.12, c.y - s * 0.2), Size(s * 0.24, s * 0.2 * blink))
            ds.drawCircle(Color.Black, s * 0.05, Offset(c.x + e * s * 0.2, c.y - s * 0.1))
        ds.drawCircle(Color(0xFF43A047), s * 0.1, c - Offset(0, s * 0.42))
        jaw = s * (0.05 + bass * 0.2)
        ds.drawRoundRect(Color(0xFFFFF59D), Offset(c.x - s * 0.4, c.y + s * 0.2 + jaw), Size(s * 0.8, s * 0.14), CornerRadius(8))
        for k in range(10):
            a = k * TAU / 10 + time
            ds.drawCircle(Color(0xFFFFEB3B).copy(alpha=treb), 3, c + Offset(cos(a), sin(a)) * (s * 0.9))

    # ───────────── Phương Đông – Trung Quốc ─────────────
    elif style == 59:                                                     # Rồng Múa
        segs = 26
        for k in range(segs, -1, -1):
            f = k / segs
            x = w * (0.08 + f * 0.84)
            v = lv[k % n]
            y = h / 2 + sin(time * 2.5 - f * 7) * h * (0.18 + v * 0.12)
            r = m * max(0.07 - f * 0.035, 0.02)
            ds.drawCircle(Color(0xFFD32F2F), r, Offset(x, y))
            ds.drawCircle(Color(0xFFFFC107), r * 0.4, Offset(x, y - r * 0.5))
            if k % 4 == 0:
                ds.drawLine(Color(0xFFFFC107), Offset(x, y + r), Offset(x - 6, y + r * 1.8), 2)
        hx = w * 0.08
        hy = h / 2 + sin(time * 2.5) * h * (0.18 + lv[0] * 0.12)
        hr = m * 0.11
        ds.drawCircle(Color(0xFFD32F2F), hr, Offset(hx, hy))
        ds.drawCircle(Color.White, hr * 0.2, Offset(hx - hr * 0.3, hy - hr * 0.3))
        ds.drawCircle(Color.Black, hr * 0.1, Offset(hx - hr * 0.3, hy - hr * 0.3))
        ds.drawLine(Color(0xFFFFC107), Offset(hx, hy - hr), Offset(hx + hr * 0.6, hy - hr * 1.8), 3)
        ds.drawLine(Color(0xFFFFC107), Offset(hx - hr, hy + hr * 0.2), Offset(hx - hr * 2, hy + sin(time * 4) * hr), 2)
        pr = hr * 0.5 * (1 + bass * 0.4)
        pc = Offset(hx - hr * 2.2, hy - hr)
        ds.drawCircle(Brush.radialGradient([Color(0xFFFFF59D), Color(0xFFFF8F00)], pc, pr), pr, pc)
    elif style == 60:                                                     # Tranh Thuỷ Mặc
        ds.drawRect(Color(0xFFF5F0E1))
        for layer in range(4):
            p = Path().moveTo(0, h)
            for k in range(31):
                x = w * k / 30
                v = lv[(k + layer * 5) % n]
                p.lineTo(x, h * (0.85 - layer * 0.14) - (sin(k * 0.6 + layer * 2) * 0.5 + 0.5) * h * (0.25 - layer * 0.03) - v * h * 0.08)
            p.lineTo(w, h).close()
            ds.drawPath(p, Color(0xFF263238).copy(alpha=0.12 + layer * 0.15))
        for k in range(4):
            x = (time * 12 + k * w / 4) % (w + 40) - 20
            y = h * 0.25 + sin(time + k) * 10
            ds.drawLine(Color(0xFF263238), Offset(x - 8, y), Offset(x, y + 4), 1.5)
            ds.drawLine(Color(0xFF263238), Offset(x, y + 4), Offset(x + 8, y), 1.5)
        ds.drawCircle(Color(0xFFC62828).copy(alpha=0.8), m * 0.05, Offset(w * 0.85, h * 0.2))
        ds.drawRect(Color(0xFFC62828), Offset(w * 0.06, h * 0.08), Size(m * 0.06, m * 0.08))
    elif style == 61:                                                     # Đèn Lồng Đỏ
        for row in range(2):
            for k in range(5):
                x = w * (k + 0.5 + row * 0.5) / 5.5
                y = h * (0.3 + row * 0.38) + sin(time + k + row) * 5
                v = lv[(k * 4 + row * 2) % n]
                r = m * 0.1 * (1 + v * 0.2)
                ds.drawLine(Color(0xFF5D4037), Offset(x, y - r * 2), Offset(x, y - r * 0.9), 1.5)
                ds.drawCircle(Brush.radialGradient([Color(0xFFFF5252).copy(alpha=clamp(0.3 + v * 0.5, 0, 1)), Color.Transparent], Offset(x, y), r * 2.2), r * 2.2, Offset(x, y))
                ds.drawOval(Color(0xFFD50000), Offset(x - r, y - r * 0.85), Size(r * 2, r * 1.7))
                for s in range(-2, 3):
                    ds.drawArc(Color(0x55000000), -90, 180, False, Offset(x - abs(s) * r * 0.2 - r * 0.1, y - r * 0.85), Size(abs(s) * r * 0.4 + r * 0.2, r * 1.7), style=Stroke(1))
                ds.drawRect(Color(0xFFFFC107), Offset(x - r * 0.4, y - r * 1), Size(r * 0.8, r * 0.18))
                ds.drawRect(Color(0xFFFFC107), Offset(x - r * 0.4, y + r * 0.82), Size(r * 0.8, r * 0.18))
                for tt in (-1, 0, 1):
                    ds.drawLine(Color(0xFFFFC107), Offset(x + tt * 4, y + r), Offset(x + tt * 4 + sin(time * 2) * 2, y + r * 1.6), 1.5)
    elif style == 62:                                                     # Quạt Giấy
        c = Offset(w / 2, h * 0.88)
        r = m * 0.8
        opn = 0.55 + bass * 0.45
        ribs = 16
        span = 160 * opn
        start = -90 - span / 2
        for k in range(ribs):
            a0 = start + k * span / ribs
            col0 = Color(0xFFE53935) if k % 2 == 0 else Color(0xFFC62828)
            ds.drawArc(col0, a0, span / ribs, True, c - Offset(r, r), Size(r * 2, r * 2))
            ds.drawArc(Color(0xFFFFE0B2).copy(alpha=clamp(0.35 + lv[k % n] * 0.5, 0, 1)), a0, span / ribs, True, c - Offset(r * 0.55, r * 0.55), Size(r * 1.1, r * 1.1))
        ds.drawCircle(Color(0xFF3E2723), m * 0.15, c)
        for k in range(ribs + 1):
            a = math.radians(start + k * span / ribs)
            ds.drawLine(Color(0xFF3E2723), c, c + Offset(cos(a), sin(a)) * r, 1.5)
    elif style == 63:                                                     # Mây Cát Tường
        for k in range(6):
            x = ((time * (10 + k * 3) + k * w / 5) % (w + m)) - m * 0.4
            y = h * (0.2 + (k % 3) * 0.28)
            s = m * (0.12 + lv[k * 3 % n] * 0.05)
            c = col(k).copy(alpha=0.85)
            for sp in range(3):
                p = Path()
                for tt in range(41):
                    a = tt / 40 * TAU * 1.3
                    rr = s * (1 - tt / 48)
                    px, py = x + sp * s * 0.9 + cos(a) * rr * 0.6, y + sin(a) * rr * 0.5
                    p.moveTo(px, py) if tt == 0 else p.lineTo(px, py)
                ds.drawPath(p, c, style=Stroke(3, cap=ROUND))
            ds.drawLine(c, Offset(x - s * 0.4, y + s * 0.45), Offset(x + s * 2.6, y + s * 0.45), 3, ROUND)
    elif style == 64:                                                     # Cá Chép Vượt Vũ Môn
        ds.drawRect(Brush.verticalGradient([Color(0xFF0D47A1), Color(0xFF1976D2)]))
        gx = w * 0.72
        ds.drawRect(Color(0xFFC62828), Offset(gx - m * 0.18, h * 0.15), Size(m * 0.04, h * 0.7))
        ds.drawRect(Color(0xFFC62828), Offset(gx + m * 0.14, h * 0.15), Size(m * 0.04, h * 0.7))
        ds.drawRect(Color(0xFFC62828), Offset(gx - m * 0.24, h * 0.12), Size(m * 0.48, m * 0.05))
        for k in range(3):
            ph = (time * 0.35 + k / 3) % 1
            x = w * (0.05 + ph * 0.8)
            y = h * 0.8 - sin(ph * PI) * h * (0.5 + bass * 0.2)
            s = m * 0.08
            ang = math.degrees(cos(ph * PI) * -0.9)
            with ds.rotate(ang, Offset(x, y)):
                ds.drawOval(Color(0xFFFF8F00), Offset(x - s, y - s * 0.4), Size(s * 2, s * 0.8))
                tl = Path().moveTo(x - s * 0.9, y).lineTo(x - s * 1.6, y - s * 0.5).lineTo(x - s * 1.6, y + s * 0.5).close()
                ds.drawPath(tl, Color(0xFFFFB300))
                ds.drawCircle(Color.Black, 2.5, Offset(x + s * 0.6, y - s * 0.1))
        for k in range(25):
            y = h * 0.82 + sin(time * 3 + k) * 3
            ds.drawCircle(Color.White.copy(alpha=clamp(0.3 + lv[k % n] * 0.5, 0, 1)), 2, Offset(w * k / 25, y))

    # ───────────── Phương Đông – Tây Tạng ─────────────
    elif style == 65:                                                     # Cờ Phướn Trong Gió
        flags = [0xFF1565C0, 0xFFFFFFFF, 0xFFD32F2F, 0xFF2E7D32, 0xFFFFC107]
        for line in range(2):
            y0 = h * (0.25 + line * 0.4)
            fw = w / 12
            ds.drawLine(Color(0xFF795548), Offset(0, y0), Offset(w, y0 + h * 0.08), 1.5)
            for k in range(12):
                x = k * fw
                v = lv[(k * 2 + line) % n]
                yy = y0 + h * 0.08 * k / 12
                wave = sin(time * 3 + k * 0.8) * (4 + v * 12)
                p = Path().moveTo(x + 2, yy).lineTo(x + fw - 2, yy).lineTo(x + fw - 2 + wave, yy + fw * 0.9).lineTo(x + 2 + wave, yy + fw * 0.9).close()
                ds.drawPath(p, Color(flags[k % 5]))
                ds.drawCircle(Color(0x33000000), fw * 0.15, Offset(x + fw / 2 + wave / 2, yy + fw * 0.45))
    elif style == 66:                                                     # Mandala Cát
        rings = 6
        for r in range(rings, 0, -1):
            rr = m * 0.075 * r * (1 + bass * 0.05)
            petals = 6 + r * 2
            v = lv[r * 3 % n]
            with ds.rotate(time * (6 if r % 2 == 0 else -6), center):
                for k in range(petals):
                    a = k * TAU / petals
                    pt = center + Offset(cos(a), sin(a)) * rr
                    ds.drawCircle(col(r + k % 2).copy(alpha=clamp(0.6 + v * 0.4, 0, 1)), m * 0.018 * (1 + v), pt)
                ds.drawCircle(col(r).copy(alpha=0.5), rr, center, style=Stroke(2))
        sq = m * 0.5
        ds.drawRect(Color(0xFFFFC107).copy(alpha=0.5), center - Offset(sq / 2, sq / 2), Size(sq, sq), style=Stroke(2))
        ds.drawCircle(Color(0xFFFFF3E0), m * 0.04, center)
    elif style == 67:                                                     # Bát Hát
        c = Offset(w / 2, h * 0.62)
        r = m * 0.28
        for k in range(6):
            f = (time * 0.35 + k / 6) % 1
            ds.drawCircle(Color(0xFFFFD54F).copy(alpha=(1 - f) * clamp(0.25 + a_ * 0.6, 0, 1)), r + f * m * 0.5, c, style=Stroke(2.5))
        ds.drawArc(Brush.verticalGradient([Color(0xFFD4A84B), Color(0xFF7A5A1E)], c.y, c.y + r), 0, 180, True, c - Offset(r, r * 0.9), Size(r * 2, r * 1.8))
        ds.drawOval(Color(0xFF5D4313), c - Offset(r, r * 0.12), Size(r * 2, r * 0.24))
        ds.drawOval(Color(0xFFE8C66E), c - Offset(r, r * 0.12), Size(r * 2, r * 0.24), style=Stroke(3))
        ma = time * 1.8
        mp = c + Offset(cos(ma) * r * 0.95, sin(ma) * r * 0.1 - r * 0.05)
        ds.drawLine(Color(0xFF5D4037), mp, mp + Offset(r * 0.5, -r * 0.7), 8, ROUND)
    elif style == 68:                                                     # Dãy Himalaya
        ds.drawRect(Brush.verticalGradient([Color(0xFF1A237E), Color(0xFF7986CB), Color(0xFFFFCCBC)]))
        mc = [Color(0xFF9FA8DA), Color(0xFF5C6BC0), Color(0xFF283593)]
        for layer in range(3):
            p = Path().moveTo(0, h)
            pts = 9
            for k in range(pts + 1):
                x = w * k / pts
                v = lv[(k * 2 + layer * 4) % n]
                y = h * (0.35 + layer * 0.17) + (h * 0.15 if k % 2 == 0 else 0) - v * h * 0.06
                p.lineTo(x, y)
            p.lineTo(w, h).close()
            ds.drawPath(p, mc[layer])
        for k in range(1, 9, 2):
            x = w * k / 9
            y = h * 0.35
            p = Path().moveTo(x, y).lineTo(x + w * 0.04, y + h * 0.05).lineTo(x - w * 0.04, y + h * 0.05).close()
            ds.drawPath(p, Color.White)
        for k in range(40):
            x = hash_(k) * w
            y = hash_(k * 3) * h * 0.3
            ds.drawCircle(Color.White.copy(alpha=clamp((sin(time * 2 + k) * 0.5 + 0.5) * (0.3 + treb), 0, 1)), 1.3, Offset(x, y))
    else:                                                                 # Đèn Bơ (69) and the retired slot
        for k in range(9):
            x = w * (k + 0.5) / 9
            base = h * 0.82
            v = lv[k * 2 % n]
            fh = m * (0.1 + v * 0.08) * (1 + sin(time * 9 + k) * 0.08)
            ds.drawCircle(Brush.radialGradient([Color(0xFFFFB300).copy(alpha=clamp(0.35 + v * 0.3, 0, 1)), Color.Transparent], Offset(x, base - fh), fh * 2.5), fh * 2.5, Offset(x, base - fh))
            ds.drawRoundRect(Color(0xFFB8860B), Offset(x - m * 0.04, base), Size(m * 0.08, m * 0.06), CornerRadius(4))
            ds.drawRect(Color(0xFF8D6E1E), Offset(x - m * 0.015, base + m * 0.06), Size(m * 0.03, m * 0.05))
            fl = Path().moveTo(x, base - fh * 1.6).quadraticTo(x + fh * 0.4 + sin(time * 7 + k) * 3, base - fh * 0.5, x, base).quadraticTo(x - fh * 0.4, base - fh * 0.5, x, base - fh * 1.6)
            ds.drawPath(fl, Brush.verticalGradient([Color(0xFFFFF59D), Color(0xFFFF6F00)], base - fh * 1.6, base))
