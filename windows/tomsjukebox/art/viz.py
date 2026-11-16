"""The 83 music visualisations (same drawings as the Android app ui/Visuals*.kt). Entry point: drawViz()."""
from .ds import (PI, Brush, Color, CornerRadius, KRandom, Offset, Path, Size, Stroke, avg, clamp, cos, exp, sin)
from .prefs import Prefs

_peaks = [0.0] * 24


def waves(ds, time, lv, cols, maxRatio=0.45, alphaMul=1.0, soft=False):
    w = ds.size.width
    base = ds.size.height
    maxh = ds.size.height * maxRatio
    for li in range(5):
        c = cols[li % len(cols)]
        path = Path().moveTo(0, base)
        for k in range(61):
            fx = k / 60
            y = 0.0
            for b in range(6):
                cx = ((b * 0.19 + li * 0.07 + time * 0.03 * (li + 1)) % 1.2) - 0.1
                wid = 0.07 + 0.02 * ((b + li) % 3)
                d = (fx - cx) / wid
                y += (0.2 + 0.8 * lv[(b * 3 + li * 5) % 24]) * exp(-(d * d))
            path.lineTo(fx * w, base - min(1.0, y) * maxh - 2)
        path.lineTo(w, base).close()
        a = [0.05, 0.30, 0.10] if soft else [0.10, 0.38, 0.62]
        ds.drawPath(path, Brush.verticalGradient([c.copy(alpha=clamp(x * alphaMul, 0, 1)) for x in a], base - maxh, base))


def drawViz(ds, style, time, lv, cols):
    """lv: 24 levels 0..1, cols: list of Color (album colours)."""
    if not cols:
        cols = [Color(0xFF48B0C8), Color(0xFFFBB040), Color(0xFF7EE3C1)]
    w, h = ds.size.width, ds.size.height
    n = len(lv)
    center = ds.center
    if style == 0:
        waves(ds, time, lv, cols, 0.9, float(Prefs.waveStrength.value), soft=True)
    elif style in (1, 2, 6):
        bw = w / n
        for i in range(n):
            v = clamp(lv[i], 0.02, 1)
            c = Color.hsv(i * 300 / n, 0.75, 1) if style == 6 else cols[i % len(cols)]
            if style == 2:
                bh = v * h / 2
                ds.drawRoundRect(c, Offset(i * bw + bw * 0.15, h / 2 - bh), Size(bw * 0.7, bh * 2), CornerRadius(bw * 0.3))
            else:
                ds.drawRoundRect(Brush.verticalGradient([c, c.copy(alpha=0.35)], h - v * h, h), Offset(i * bw + bw * 0.15, h - v * h),
                                 Size(bw * 0.7, v * h), CornerRadius(bw * 0.3))
    elif style == 3:
        bw = w / n
        for i in range(n):
            dots = int(lv[i] * 8)
            for d in range(dots + 1):
                ds.drawCircle(cols[i % len(cols)].copy(alpha=0.4 + 0.6 * d / 8), bw * 0.28, Offset(i * bw + bw / 2, h - d * bw * 0.75 - bw / 2))
    elif style == 4:
        p = Path()
        for i in range(n):
            x = i * w / (n - 1)
            sg = -1.0 if sin(time * 2 + i) < 0 else 1.0
            y = h / 2 - (lv[i] - 0.3) * h * 0.8 * sg
            p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
        ds.drawPath(p, cols[0].copy(alpha=0.3), style=Stroke(12))
        ds.drawPath(p, cols[0], style=Stroke(4))
    elif style == 5:
        r = min(w, h) * 0.28
        for i in range(n * 2):
            a = i * 2 * PI / (n * 2) + time * 0.3
            v = lv[i % n]
            r2 = r + v * r * 0.9
            ds.drawLine(cols[i % len(cols)], Offset(center.x + cos(a) * r, center.y + sin(a) * r), Offset(center.x + cos(a) * r2, center.y + sin(a) * r2), 6)
        ds.drawCircle(cols[0].copy(alpha=0.25), r * 0.9)
    elif style == 7:
        bw = w / n
        for i in range(n):
            v = lv[i]
            fl = 0.85 + 0.15 * sin(time * 9 + i * 2)
            ds.drawOval(Brush.verticalGradient([Color(0xFFFFE082), Color(0xFFFF6D00), Color(0x00FF3D00)], h - v * h * fl, h),
                        Offset(i * bw, h - v * h * fl), Size(bw * 1.2, v * h * fl))
    elif style == 8:
        for k in range(60):
            life = (time * 0.4 + k * 0.173) % 1
            x = ((k * 0.618) % 1) * w + sin(time + k) * 10
            y = h - life * h * (0.4 + lv[k % n])
            ds.drawCircle(cols[k % len(cols)].copy(alpha=1 - life), 3 + lv[k % n] * 6, Offset(x, y))
    elif style == 9:
        a_ = avg(lv)
        for k in range(5):
            f = (time * 0.5 + k / 5) % 1
            ds.drawCircle(cols[k % len(cols)].copy(alpha=(1 - f) * (0.3 + a_)), f * max(w, h) * 0.6, style=Stroke(4 + a_ * 8))
    elif style == 10:
        p = Path()
        for k in range(121):
            x = k * w / 120
            i = clamp(k * n // 121, 0, n - 1)
            y = h / 2 + sin(k * 0.35 + time * 8) * lv[i] * h * 0.45
            p.moveTo(x, y) if k == 0 else p.lineTo(x, y)
        ds.drawPath(p, Color(0xFF7CFFB2).copy(alpha=0.35), style=Stroke(10))
        ds.drawPath(p, Color(0xFF7CFFB2), style=Stroke(3))
    elif style == 11:
        a_ = avg(lv)
        for k in range(80):
            z = (time * (0.15 + a_ * 0.6) + k * 0.0125) % 1
            ang = k * 2.39996
            rr = z * max(w, h) * 0.7
            ds.drawCircle(Color.White.copy(alpha=z), 1.5 + z * 3.5, Offset(center.x + cos(ang) * rr, center.y + sin(ang) * rr))
    elif 12 <= style <= 35:
        drawViz2(ds, style, time, lv, cols)
    elif 36 <= style <= 69:
        from .viz3 import drawViz3
        drawViz3(ds, style, time, lv, cols)
    elif 70 <= style <= 89:
        from .viz4 import drawViz4
        drawViz4(ds, style, time, lv, cols)
    else:
        waves(ds, time, lv, cols, 0.9, soft=True)


def drawViz2(ds, style, time, lv, cols):
    """The 24 visualisations added in 0.9.2."""
    w, h = ds.size.width, ds.size.height
    n = len(lv)
    center = ds.center
    a_ = avg(lv)
    bass = (lv[0] + lv[1] + lv[2]) / 3

    def col(i):
        return cols[((i % len(cols)) + len(cols)) % len(cols)]

    if style == 12:                                                       # Sóng Đại Dương
        for layer in range(4):
            p = Path().moveTo(0, h)
            for k in range(61):
                x = w * k / 60
                y = h * (0.45 + layer * 0.12) - sin(x * 0.02 + time * (1.2 + layer * 0.3) + layer) * h * 0.12 * (0.4 + lv[(k // 3) % n])
                p.lineTo(x, y)
            p.lineTo(w, h).close()
            ds.drawPath(p, col(layer).copy(alpha=0.25 + layer * 0.1))
    elif style == 13:                                                     # Cầu Vồng Nhảy Múa
        bw = w / n
        for i in range(n):
            v = lv[i]
            c = Color.hsv(i * 330 / n, 0.8, 1)
            ds.drawRect(c, Offset(i * bw + 1, h - v * h), Size(bw - 2, v * h))
            old = _peaks[i] if i < len(_peaks) else 0.0
            pk = v if v > old else max(0.0, old - 0.01)
            if i < len(_peaks):
                _peaks[i] = pk
            ds.drawRect(Color.White, Offset(i * bw + 1, h - pk * h - 4), Size(bw - 2, 3))
    elif style == 14:                                                     # Đèn LED Ampli
        for ch in range(2):
            v = avg(lv[:12]) if ch == 0 else avg(lv[12:])
            seg = 20
            sw = w / seg
            for k in range(seg):
                on = k < (v * 1.6 * seg)
                c = Color(0xFFFF3B30) if k > seg * 0.85 else Color(0xFFFFCC00) if k > seg * 0.65 else Color(0xFF34C759)
                ds.drawRoundRect(c.copy(alpha=1 if on else 0.12), Offset(k * sw + 2, h * (0.2 + ch * 0.4)), Size(sw - 4, h * 0.25), CornerRadius(3))
    elif style == 15:                                                     # Kim Đồng Hồ VU
        import math
        for ch in range(2):
            cx = w * (0.27 + ch * 0.46)
            cy = h * 0.95
            r = min(w * 0.22, h * 0.85)
            ds.drawArc(Color(0xFFF4E9C8), 200, 140, True, Offset(cx - r, cy - r), Size(r * 2, r * 2))
            ds.drawArc(Color(0xFFD9342B), 305, 35, False, Offset(cx - r * 0.85, cy - r * 0.85), Size(r * 1.7, r * 1.7), style=Stroke(4))
            v = avg(lv[:12]) if ch == 0 else avg(lv[12:])
            a = math.radians(200 + 140 * clamp(v * 1.4, 0, 1))
            ds.drawLine(Color(0xFF222222), Offset(cx, cy), Offset(cx + cos(a) * r * 0.92, cy + sin(a) * r * 0.92), 3)
    elif style == 16:                                                     # Vòng Tròn Phát Sáng
        r = min(w, h) * 0.3 * (1 + bass * 0.3)
        for k in range(4):
            ds.drawCircle(col(k).copy(alpha=0.18), r + k * 8 + a_ * 30, style=Stroke(10 - k * 2))
        ds.drawCircle(col(0), r, style=Stroke(4))
    elif style == 17:                                                     # Hoa Nở
        petals = 10
        for k in range(petals):
            a = k * 360 / petals + time * 10
            ln = min(w, h) * (0.2 + lv[k * 2 % n] * 0.3)
            with ds.rotate(a):
                ds.drawOval(col(k).copy(alpha=0.55), Offset(center.x - ln * 0.18, center.y - ln), Size(ln * 0.36, ln))
        ds.drawCircle(Color(0xFFFFE082), min(w, h) * 0.06)
    elif style == 18:                                                     # Thác Nước Phổ
        rows = 14
        for r in range(rows):
            for i in range(n):
                v = lv[(i + r) % n] * (1 - r / rows)
                c = Color.hsv((200 + v * 160) % 360, 0.7, 0.4 + v * 0.6)
                ds.drawRect(c.copy(alpha=0.3 + v * 0.7), Offset(i * w / n, r * h / rows), Size(w / n + 1, h / rows + 1))
    elif style == 19:                                                     # Dải Lụa
        for band in range(3):
            p = Path()
            for k in range(81):
                x = w * k / 80
                y = h / 2 + sin(x * 0.015 + time * (0.8 + band * 0.4) + band) * h * (0.15 + a_ * 0.3) * (1 + band * 0.2)
                p.moveTo(x, y) if k == 0 else p.lineTo(x, y)
            ds.drawPath(p, col(band).copy(alpha=0.18), style=Stroke(26))
            ds.drawPath(p, col(band).copy(alpha=0.7), style=Stroke(3))
    elif style == 20:                                                     # Pháo Hoa Nhạc
        for b in range(5):
            life = (time * 0.6 + b * 0.21) % 1
            c0 = Offset(w * (0.15 + b * 0.18), h * (0.3 + (b % 2) * 0.25))
            for k in range(14):
                a = k * 2 * PI / 14
                r = life * min(w, h) * (0.15 + lv[b * 4 % n] * 0.25)
                ds.drawCircle(col(b + k).copy(alpha=1 - life), 2.5, Offset(c0.x + cos(a) * r, c0.y + sin(a) * r))
    elif style == 21:                                                     # Núi Non
        for layer in range(4):
            p = Path().moveTo(0, h)
            for k in range(25):
                x = w * k / 24
                v = lv[(k + layer * 5) % n]
                p.lineTo(x, h * (0.85 - layer * 0.12) - v * h * (0.35 - layer * 0.05) - (h * 0.06 if k % 2 == 0 else 0))
            p.lineTo(w, h).close()
            ds.drawPath(p, col(layer).darken(0.35 + layer * 0.2))
    elif style == 22:                                                     # Mưa Ánh Sáng
        for k in range(70):
            speed = 0.4 + a_ * 1.6
            y = ((time * speed + k * 0.137) % 1) * h
            x = ((k * 0.618) % 1) * w
            ds.drawLine(col(k).copy(alpha=0.7), Offset(x, y), Offset(x, y - 10 - a_ * 30), 2)
    elif style == 23:                                                     # Gương Đối Xứng
        bw = w / n
        for i in range(n):
            v = lv[i] * h * 0.45
            ds.drawRect(col(i), Offset(i * bw + 1, h / 2 - v), Size(bw - 2, v))
            ds.drawRect(col(i).copy(alpha=0.3), Offset(i * bw + 1, h / 2), Size(bw - 2, v * 0.8))
    elif style == 24:                                                     # Tim Đập Nhịp
        s = min(w, h) * (0.28 + bass * 0.18)
        cx, cy = center.x, center.y
        p = Path()
        p.moveTo(cx, cy + s * 0.9)
        p.cubicTo(cx - s * 1.4, cy, cx - s * 0.6, cy - s * 1.1, cx, cy - s * 0.35)
        p.cubicTo(cx + s * 0.6, cy - s * 1.1, cx + s * 1.4, cy, cx, cy + s * 0.9)
        ds.drawPath(p, Color(0xFFFF4D6D))
        ds.drawPath(p, Color(0x66FF4D6D), style=Stroke(10))
    elif style == 25:                                                     # Lốc Xoáy
        for k in range(90):
            a = k * 0.35 + time * (1.5 + a_ * 4)
            r = (k / 90) * min(w, h) * 0.48
            ds.drawCircle(col(k).copy(alpha=0.8), 2 + lv[k % n] * 4, Offset(center.x + cos(a) * r, center.y + sin(a) * r))
    elif style == 26:                                                     # Bong Bóng
        for k in range(24):
            life = (time * 0.25 + k * 0.13) % 1
            x = ((k * 0.381) % 1) * w + sin(time + k) * 8
            r = 4 + lv[k % n] * 16
            ds.drawCircle(col(k).copy(alpha=(1 - life) * 0.8), r, Offset(x, h - life * h), style=Stroke(2))
    elif style == 27:                                                     # Lưới Neon 3D
        rows, colsN = 10, 16
        for r in range(rows):
            p = Path()
            z = r / rows
            for c in range(colsN + 1):
                x = w * c / colsN
                v = lv[(c + r) % n]
                y = h * (0.25 + z * 0.7) - v * h * 0.25 * (1 - z * 0.5)
                p.moveTo(x, y) if c == 0 else p.lineTo(x, y)
            ds.drawPath(p, Color(0xFFFF3DCB).copy(alpha=0.3 + z * 0.6), style=Stroke(1.5))
    elif style == 28:                                                     # Đom Đóm
        for k in range(40):
            x = ((k * 0.618) % 1) * w + sin(time * 0.7 + k) * 30
            y = ((k * 0.414) % 1) * h + cos(time * 0.5 + k * 1.3) * 20
            tw = clamp((sin(time * 3 + k) * 0.5 + 0.5) * (0.4 + a_), 0, 1)
            ds.drawCircle(Color(0xFFFFF59D).copy(alpha=tw * 0.4), 8, Offset(x, y))
            ds.drawCircle(Color(0xFFFFF59D).copy(alpha=tw), 2.5, Offset(x, y))
    elif style == 29:                                                     # Vân Tay Âm Thanh
        for k in range(14):
            p = Path()
            rr = (k + 1) * min(w, h) * 0.032
            for a in range(61):
                ang = a * 2 * PI / 60
                rad = rr + sin(ang * 5 + k + time * 2) * lv[(a + k) % n] * 6
                px, py = center.x + cos(ang) * rad, center.y + sin(ang) * rad
                p.moveTo(px, py) if a == 0 else p.lineTo(px, py)
            p.close()
            ds.drawPath(p, col(k).copy(alpha=0.7), style=Stroke(1.5))
    elif style == 30:                                                     # Mặt Trời Toả Tia
        m = min(w, h)
        for k in range(36):
            a = k * 10 * PI / 180 + time * 0.2
            ln = m * (0.15 + lv[k % n] * 0.4)
            d = Offset(cos(a), sin(a))
            ds.drawLine(Color(0xFFFFB300).copy(alpha=0.8), center + d * (m * 0.1), center + d * ln, 3)
        ds.drawCircle(Color(0xFFFFD54F), m * 0.1)
    elif style == 31:                                                     # Cánh Bướm
        flap = 0.6 + bass * 0.5
        for side in (-1.0, 1.0):
            p = Path().moveTo(center.x, center.y)
            p.cubicTo(center.x + side * w * 0.3 * flap, center.y - h * 0.6, center.x + side * w * 0.42 * flap, center.y + h * 0.1, center.x, center.y + h * 0.05)
            p.cubicTo(center.x + side * w * 0.25 * flap, center.y + h * 0.5, center.x + side * w * 0.05, center.y + h * 0.45, center.x, center.y)
            ds.drawPath(p, Brush.radialGradient([col(0), col(2).copy(alpha=0.4)], center, w * 0.4))
    elif style == 32:                                                     # Thành Phố Đêm
        bw = w / n
        for i in range(n):
            bh = (0.25 + lv[i] * 0.7) * h
            ds.drawRect(Color(0xFF1B2638), Offset(i * bw, h - bh), Size(bw - 2, bh))
            y = h - bh + 6
            while y < h - 6:
                if ((i * 7 + int(y) // 9) % 3) != 0:
                    ds.drawRect(Color(0xFFFFE08A).copy(alpha=0.6 + lv[i] * 0.4), Offset(i * bw + 3, y), Size(bw - 8, 3))
                y += 9
    elif style == 33:                                                     # Điện Tâm Đồ
        p = Path()
        beat = bass
        for k in range(101):
            x = w * k / 100
            ph = ((k / 100 + time * 0.5) % 0.25) / 0.25
            if 0.40 <= ph <= 0.45:
                d = -h * 0.1
            elif 0.45 <= ph <= 0.5:
                d = h * (0.35 + beat * 0.3)
            elif 0.5 <= ph <= 0.55:
                d = -h * 0.25
            else:
                d = 0
            y = h / 2 - d
            p.moveTo(x, y) if k == 0 else p.lineTo(x, y)
        ds.drawPath(p, Color(0xFF4CFF8A).copy(alpha=0.3), style=Stroke(8))
        ds.drawPath(p, Color(0xFF4CFF8A), style=Stroke(2.5))
    elif style == 34:                                                     # Sóng Tròn Đồng Tâm
        for k in range(6):
            f = (time * 0.4 + k / 6) % 1
            ds.drawCircle(col(k).copy(alpha=(1 - f) * (0.4 + a_)), f * max(w, h) * 0.55, style=Stroke(3))
    else:                                                                 # Tinh Vân
        m = min(w, h)
        for k in range(5):
            a = time * 0.1 + k * 1.25
            c = center + Offset(cos(a), sin(a)) * (m * 0.2)
            ds.drawCircle(Brush.radialGradient([col(k).copy(alpha=clamp(0.35 + a_ * 0.4, 0, 1)), Color.Transparent], c, m * (0.35 + lv[k * 3 % n] * 0.2)), m * 0.6, c)
        r = KRandom(11)
        for _ in range(50):
            ds.drawCircle(Color.White.copy(alpha=r.nextFloat()), 1.2, Offset(r.nextFloat() * w, r.nextFloat() * h))
