"""Ánh Sáng Chạy Viền: the 28 edge-light effects of the Android app (ui/EdgeLight.kt), running around a rounded rectangle."""
import math
import random
import time as _time

from .ds import PI, ROUND, Brush, Color, Offset, Path, Stroke, avg, clamp, dash, sin
from .prefs import Prefs
from .state import Core
from .themes import ORANGE, SKY, BarColours, EdgeEffects, Motifs


class RoundRectMeasure:
    """Length / position / segment along a rounded rectangle (stand-in for Android's PathMeasure)."""

    def __init__(self, left, top, right, bottom, r):
        self.l, self.t, self.r_, self.b = left, top, right, bottom
        w, h = right - left, bottom - top
        self.rad = r = max(0.0, min(r, w / 2, h / 2))
        self.sw, self.sh = w - 2 * r, h - 2 * r
        self.arc = PI * r / 2
        self.parts = [self.sw, self.arc, self.sh, self.arc, self.sw, self.arc, self.sh, self.arc]
        self.length = sum(self.parts)

    def position(self, d):
        L = self.length
        if L <= 0:
            return Offset(self.l, self.t)
        d = d % L
        l, t, rr, b, r = self.l, self.t, self.r_, self.b, self.rad
        for i, ln in enumerate(self.parts):
            if d <= ln or i == 7:
                f = d / ln if ln > 0 else 0
                if i == 0:
                    return Offset(l + r + self.sw * f, t)
                if i == 2:
                    return Offset(rr, t + r + self.sh * f)
                if i == 4:
                    return Offset(rr - r - self.sw * f, b)
                if i == 6:
                    return Offset(l, b - r - self.sh * f)
                cx, cy, a0 = {1: (rr - r, t + r, -90), 3: (rr - r, b - r, 0), 5: (l + r, b - r, 90), 7: (l + r, t + r, 180)}[i]
                a = math.radians(a0 + 90 * f)
                return Offset(cx + math.cos(a) * r, cy + math.sin(a) * r)
            d -= ln
        return Offset(l, t)

    def segment(self, s, e, step=3.0):
        p = Path()
        if e <= s:
            return p
        n = max(2, int((e - s) / step) + 1)
        for k in range(n + 1):
            pt = self.position(s + (e - s) * k / n)
            p.moveTo(pt.x, pt.y) if k == 0 else p.lineTo(pt.x, pt.y)
        return p


def edgeColours():
    ec = Prefs.edgeColour.value
    if ec == "rainbow":
        return BarColours.gradients["rainbow"]
    if ec == "brand":
        return [SKY, ORANGE]
    if ec == "custom":
        c = Color(Prefs.edgeCustom.value)
        return [c, c.copy(alpha=0.8)]
    return list(Core.palette)


def colourAt(cols, f):
    if len(cols) == 1:
        return cols[0]
    x = ((f % 1) + 1) % 1 * len(cols)
    i = int(x) % len(cols)
    return Color.lerp(cols[i], cols[(i + 1) % len(cols)], x - int(x))


def current_effect(clock, uri=""):
    count = len(EdgeEffects.names)
    chosen, mo = Motifs.edgeStyle()
    if Prefs.edgeRandom.value:
        return (hash(uri) & 0x7fffffff) % count, mo
    if Prefs.edgeAuto.value:
        return int(clock / 30) % count, mo
    return chosen, mo


def paint_edge(ds, clock, radiusPx, effect_override=None, uri="", scale=1.0):
    """Draws the chosen effect with the user's settings (or a preview of one effect)."""
    eff, mo = current_effect(clock, uri)
    if effect_override is not None:
        eff, mo = effect_override, None
    cols = mo.colours[1:] if mo is not None else edgeColours()
    drawEdge(ds, eff, clock, radiusPx, cols, float(Prefs.edgeThick.value) * scale, float(Prefs.edgeBright.value),
             EdgeEffects.speeds[clamp(int(Prefs.edgeSpeed.value), 0, 4)])


def drawEdge(ds, effect, time, radiusPx, cols, thick, bright, speed):
    W, H = ds.size.width, ds.size.height
    inset = thick / 2 + 1
    pm = RoundRectMeasure(inset, inset, W - inset, H - inset, max(0.0, radiusPx - inset))
    path = Path().addRoundRect((inset, inset, W - 2 * inset, H - 2 * inset), pm.rad, pm.rad)
    ln = pm.length
    if ln <= 0:
        return
    t = time * speed
    lv = Core.levels
    beatBoost = 0.0
    if Prefs.edgeBeat.value:
        beatBoost = avg(lv[:4]) * 0.25
    a = clamp(bright + beatBoost, 0.05, 1.0)

    def seg(frm, segLen, c, w=thick, alpha=a):
        s = ((frm % ln) + ln) % ln
        segLen = min(segLen, ln)
        e = s + segLen
        if e <= ln:
            dst = pm.segment(s, e)
            dst2 = None
        else:
            dst = pm.segment(s, ln)
            dst2 = pm.segment(0, e - ln)
        for d in (dst, dst2):
            if d is None:
                continue
            ds.drawPath(d, c.copy(alpha=clamp(alpha * 0.28, 0, 1)), style=Stroke(w * 3.2, cap=ROUND))
            ds.drawPath(d, c.copy(alpha=clamp(alpha, 0, 1)), style=Stroke(w, cap=ROUND))

    def whole(c, alpha=a, w=thick):
        ds.drawPath(path, c.copy(alpha=clamp(alpha * 0.25, 0, 1)), style=Stroke(w * 3.5))
        ds.drawPath(path, c.copy(alpha=clamp(alpha, 0, 1)), style=Stroke(w))

    def wholeBrush(b, alpha=a):
        ds.drawPath(path, b, alpha=alpha * 0.25, style=Stroke(thick * 3.5))
        ds.drawPath(path, b, alpha=alpha, style=Stroke(thick))

    def pos(d):
        return pm.position(((d % ln) + ln) % ln)

    av = avg(lv)
    bass = (lv[0] + lv[1] + lv[2]) / 3
    center = ds.center

    if effect == 0:                                                       # chasing streaks
        for k in range(3):
            seg(t * ln * 0.18 + k * ln / 3, ln * 0.12, colourAt(cols, k / 3))
    elif effect == 1:                                                     # shooting star
        head = t * ln * 0.28
        for k in range(14):
            f = k / 14
            seg(head - ln * 0.22 * f, ln * 0.022, colourAt(cols, f * 0.5), thick * (1 - f * 0.7), a * (1 - f))
    elif effect == 2:                                                     # spinning rainbow
        rb = BarColours.gradients["rainbow"]
        with ds.rotate(t * 90):
            wholeBrush(Brush.sweepGradient(rb + [rb[0]], center))
    elif effect == 3:                                                     # breathing
        s = sin(t * 1.6)
        whole(colourAt(cols, t * 0.05), a * (0.15 + 0.85 * s * s))
    elif effect == 4:                                                     # music beat
        whole(colourAt(cols, t * 0.1), clamp(0.2 + av * 1.2 + beatBoost, 0, 1), thick * (0.8 + av * 1.6))
    elif effect == 5:                                                     # colour wave
        wholeBrush(Brush.linearGradient([colourAt(cols, i / 6 + t * 0.15) for i in range(6)], Offset(0, 0), Offset(W, H)))
    elif effect == 6:                                                     # two ends meet
        p = (t * 0.35) % 1
        start = max(0.0, W / 2 - radiusPx)
        grow = ln / 2 * p
        seg(start, grow, colourAt(cols, 0), alpha=a * (1 - p * 0.3))
        seg(start - grow, grow, colourAt(cols, 0.5), alpha=a * (1 - p * 0.3))
    elif effect == 7:                                                     # neon
        flicker = 0.5 if sin(t * 23) > 0.97 else 1.0
        c = colourAt(cols, 0)
        ds.drawPath(path, c.copy(alpha=a * 0.15 * flicker), style=Stroke(thick * 6))
        whole(c, a * flicker)
        ds.drawPath(path, Color.White.copy(alpha=0.7 * a * flicker), style=Stroke(thick * 0.35))
    elif effect == 8:                                                     # sparkle
        whole(colourAt(cols, 0), a * 0.18)
        for k in range(26):
            ph = t * 1.3 + k * 0.37
            s = sin(ph * PI)
            tw = s * s
            p = pm.position(((k * 0.618 + int(ph) * 0.13) % 1) * ln)
            ds.drawCircle(colourAt(cols, k / 26).copy(alpha=a * tw), thick * 0.9 * (0.5 + tw), p)
            ds.drawCircle(Color.White.copy(alpha=a * tw * 0.8), thick * 0.35, p)
    elif effect == 9:                                                     # running dashes
        dsh = dash([thick * 5, thick * 4], -t * thick * 18)
        c = colourAt(cols, t * 0.1)
        ds.drawPath(path, c.copy(alpha=a * 0.25), style=Stroke(thick * 3, pathEffect=dsh))
        ds.drawPath(path, c.copy(alpha=a), style=Stroke(thick, cap=ROUND, pathEffect=dsh))
    elif effect == 10:                                                    # fire
        fire = [Color(0xFFFF3D00), Color(0xFFFF9100), Color(0xFFFFD54F)]
        for k in range(18):
            fl = abs(sin(t * 3.1 + k * 1.7))
            seg(k * ln / 18 + sin(t + k) * 8, ln / 18 * (0.4 + fl * 0.8), fire[k % 3], thick * (0.6 + fl), a * (0.4 + 0.6 * fl))
    elif effect == 11:                                                    # frost
        whole(Color(0xFFBFE9FF), a * 0.45)
        seg(t * ln * 0.12, ln * 0.18, Color.White, thick, a)
        seg(t * ln * 0.12 + ln / 2, ln * 0.18, Color(0xFF7FD3FF), thick, a * 0.8)
    elif effect == 12:                                                    # Cực Quang
        aur = [Color(0xFF3DFFB0), Color(0xFF3DA8FF), Color(0xFFB45CFF), Color(0xFFFF6FB5)]
        for k in range(4):
            seg(t * ln * 0.05 + k * ln / 4, ln * 0.3, aur[k], thick * (1.2 + sin(t + k) * 0.4), a * 0.7)
    elif effect == 13:                                                    # Gợn Sóng Nước
        n = 120
        for k in range(n):
            d = ln * k / n
            r = thick * (0.5 + (sin(d * 0.03 - t * 4) * 0.5 + 0.5) * (1 + av * 2))
            ds.drawCircle(colourAt(cols, k / n).copy(alpha=a * 0.6), r, pos(d))
    elif effect == 14:                                                    # Bụi Sao
        r = random.Random(9)
        for k in range(160):
            d = r.random() * ln + t * ln * 0.02 * (0.5 + r.random())
            tw = sin(time * 4 + k) * 0.5 + 0.5
            ds.drawCircle(colourAt(cols, r.random()).copy(alpha=a * tw), 0.6 + r.random() * thick * 0.4, pos(d))
    elif effect == 15:                                                    # Hoàng Hôn Trượt
        ds.drawPath(path, Brush.sweepGradient([Color(0xFFFF9A3C), Color(0xFFFF5E7E), Color(0xFF9B5CFF), Color(0xFFFF9A3C)]), alpha=a, style=Stroke(thick))
    elif effect == 16:                                                    # Tim Đập
        ph = (time * 1.2) % 1
        pulse = 1.0 if ph < 0.12 else 0.7 if 0.22 <= ph <= 0.34 else 0.15
        whole(Color(0xFFFF4D6D), clamp(a * (pulse + beatBoost), 0, 1), thick * (1 + pulse * 0.8))
    elif effect == 17:                                                    # Chạy Theo Bass
        sp = 0.1 + bass * 0.9
        seg(time * ln * sp, ln * (0.08 + bass * 0.15), colourAt(cols, 0), thick * (1 + bass))
        seg(time * ln * sp + ln / 2, ln * (0.08 + bass * 0.15), colourAt(cols, 0.5), thick * (1 + bass))
    elif effect == 18:                                                    # Cột Sóng Viền
        n = 96
        for k in range(n):
            d = ln * k / n
            p = pos(d)
            p2 = pos(d + 1)
            nx, ny = -(p2.y - p.y), (p2.x - p.x)
            ll = max(0.001, math.hypot(nx, ny))
            v = lv[k % len(lv)] * thick * 6
            ds.drawLine(colourAt(cols, k / n).copy(alpha=a), p, Offset(p.x + nx / ll * v, p.y + ny / ll * v), thick * 0.6)
    elif effect == 19:                                                    # Pháo Hoa
        corners = [Offset(radiusPx, radiusPx), Offset(W - radiusPx, radiusPx), Offset(W - radiusPx, H - radiusPx), Offset(radiusPx, H - radiusPx)]
        for i, c in enumerate(corners):
            life = (time * 0.7 + i * 0.25 + beatBoost) % 1
            for k in range(12):
                ang = math.radians(k * 30)
                r = life * radiusPx * 1.6
                ds.drawCircle(colourAt(cols, k / 12).copy(alpha=a * (1 - life)), thick * 0.5, Offset(c.x + math.cos(ang) * r, c.y + math.sin(ang) * r))
        whole(colourAt(cols, 0), a * 0.2)
    elif effect == 20:                                                    # Vệt Ngược Chiều
        p = (t * 0.25) % 1
        seg(p * ln, ln * 0.12, colourAt(cols, 0))
        seg(-p * ln, ln * 0.12, colourAt(cols, 0.5))
        if abs(p - 0.5) < 0.03 or p < 0.03:
            whole(Color.White, a * 0.6)
    elif effect == 21:                                                    # Bốn Góc Đuổi Nhau
        for k in range(4):
            seg(ln * k / 4 + t * ln * 0.08, ln * 0.07, colourAt(cols, k / 4))
    elif effect == 22:                                                    # Mưa Sao Rơi
        for k in range(30):
            side = thick if k % 2 == 0 else W - thick
            y = ((t * 0.3 + k * 0.071) % 1) * H
            ds.drawLine(colourAt(cols, k / 30).copy(alpha=a), Offset(side, y), Offset(side, y - thick * 6), thick * 0.7)
    elif effect == 23:                                                    # Tia Chớp
        whole(Color(0xFFBFD7FF), a * 0.15)
        flash = (sin(time * 7.3) * sin(time * 3.1)) > 0.85 or beatBoost > 0.45
        if flash:
            start = (int(time * 1000) % 997) / 997 * ln
            pth = Path()
            r = random.Random(int(time * 10))
            for k in range(17):
                p = pos(start + k * ln * 0.012)
                j = (r.random() - 0.5) * thick * 5
                pth.moveTo(p.x + j, p.y + j) if k == 0 else pth.lineTo(p.x + j, p.y - j)
            ds.drawPath(pth, Color.White.copy(alpha=a), style=Stroke(thick * 0.8))
            ds.drawPath(pth, Color(0xFF7FB2FF).copy(alpha=a * 0.4), style=Stroke(thick * 3))
    elif effect == 24:                                                    # Điện Từ
        n = 140
        pth = Path()
        for k in range(n + 1):
            d = ln * k / n
            p = pos(d)
            j = sin(d * 0.2 + t * 12) * thick * (0.6 + av * 2)
            pth.moveTo(p.x + j, p.y + j) if k == 0 else pth.lineTo(p.x + j, p.y - j)
        ds.drawPath(pth, Color(0xFF8CF2FF).copy(alpha=a * 0.3), style=Stroke(thick * 2.5))
        ds.drawPath(pth, Color.White.copy(alpha=a), style=Stroke(thick * 0.5))
    elif effect == 25:                                                    # Ánh Kim Cương
        whole(Color.White, a * 0.1)
        for k in range(18):
            ph = (time * 0.9 + k * 0.37) % 1
            p = pos(ln * ((k * 0.618) % 1))
            s = thick * 2.5 * sin(ph * PI)
            ds.drawLine(Color.White.copy(alpha=a), Offset(p.x - s, p.y), Offset(p.x + s, p.y), 1.5)
            ds.drawLine(Color.White.copy(alpha=a), Offset(p.x, p.y - s), Offset(p.x, p.y + s), 1.5)
    elif effect == 26:                                                    # Đèn Giáng Sinh
        bulbs = [Color(0xFFFF3B30), Color(0xFF34C759), Color(0xFFFFCC00), Color(0xFF0A84FF), Color(0xFFFF2D9A)]
        n = 48
        ds.drawPath(path, Color(0xFF1E5F2A).copy(alpha=a * 0.6), style=Stroke(thick * 0.4))
        for k in range(n):
            on = ((k + int(t * 3)) % 3) != 0
            p = pos(ln * k / n)
            ds.drawCircle(bulbs[k % len(bulbs)].copy(alpha=a if on else a * 0.2), thick * 0.9, p)
            if on:
                ds.drawCircle(bulbs[k % len(bulbs)].copy(alpha=a * 0.25), thick * 2.2, p)
    elif effect == 27:                                                    # Đèn Tết
        whole(Color(0xFFD7261E), a * 0.6)
        n = 20
        for k in range(n):
            ds.drawCircle(Color(0xFFFFD54F).copy(alpha=a), thick * 1.1, pos(ln * k / n + t * ln * 0.02))
        seg(t * ln * 0.15, ln * 0.1, Color(0xFFFFE082))
    else:
        whole(colourAt(cols, 0))
