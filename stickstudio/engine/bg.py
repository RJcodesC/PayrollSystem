"""Flat-colour cartoon backgrounds. Static layers are cached; animated bits are drawn live.
All drawn in world coordinates on a canvas a bit larger than the frame (camera margin)."""
import math
import random

import cairo

from .core import W, H, hexc, noise1
from .rig import INK, _star
from .text import text_center

M = 160  # margin around the frame for camera moves / shake
_cache = {}


def _cached(key, fn):
    if key not in _cache:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W + 2 * M, H + 2 * M)
        c = cairo.Context(surf)
        c.translate(M, M)
        fn(c)
        _cache[key] = surf
    return _cache[key]


def blit(ctx, key, fn):
    ctx.set_source_surface(_cached(key, fn), -M, -M)
    ctx.paint()


def outline(ctx, w=5):
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(w)
    ctx.set_line_join(1)
    ctx.stroke()


def fill_out(ctx, color, w=5):
    ctx.set_source_rgb(*hexc(color))
    ctx.fill_preserve()
    outline(ctx, w)


def rect(ctx, x, y, w, h, color, lw=5):
    ctx.rectangle(x, y, w, h)
    fill_out(ctx, color, lw)


def sky(ctx, top="#8fd3f4", bottom="#d9f1fb"):
    g = cairo.LinearGradient(0, -M, 0, 1400)
    g.add_color_stop_rgb(0, *hexc(top))
    g.add_color_stop_rgb(1, *hexc(bottom))
    ctx.rectangle(-M, -M, W + 2 * M, H + 2 * M)
    ctx.set_source(g)
    ctx.fill()


def cloud(ctx, x, y, s=1.0, color="#ffffff"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.new_path()
    for (cx, cy, r) in ((0, 0, 55), (60, -25, 70), (130, 0, 55), (65, 20, 50)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc(color))
    ctx.fill()
    ctx.restore()


def tree(ctx, x, y, s=1.0, c1="#5aa152", c2="#3f7f3a"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rectangle(-14, -120, 28, 120)
    fill_out(ctx, "#7a5634")
    ctx.new_path()
    for (cx, cy, r) in ((0, -190, 85), (-60, -140, 60), (60, -140, 60)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    fill_out(ctx, c1)
    ctx.arc(20, -200, 40, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexc(c2), 0.5)
    ctx.fill()
    ctx.restore()


def eiffel(ctx, cx, base, h, color="#a07a52", line="#4a3420", lw=5):
    """Stylised Eiffel Tower silhouette with lattice."""
    hw0 = h * 0.24

    def half(u):  # half-width at height fraction u
        return hw0 * (1 - u) ** 2.6 + h * 0.012

    us = [i / 60 for i in range(61)]
    ah = h * 0.13
    aw = half(0.02) * 0.72

    def body():
        ctx.new_path()
        ctx.move_to(cx - half(0), base)
        for u in us:
            ctx.line_to(cx - half(u), base - u * h)
        ctx.line_to(cx, base - h * 1.04)
        for u in reversed(us):
            ctx.line_to(cx + half(u), base - u * h)
        ctx.close_path()
        ctx.new_sub_path()  # arch hole
        ctx.move_to(cx - aw, base)
        ctx.curve_to(cx - aw, base - ah * 1.2, cx + aw, base - ah * 1.2, cx + aw, base)
        ctx.close_path()

    body()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgb(*hexc(color))
    ctx.fill_preserve()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.set_source_rgb(*hexc(line))
    ctx.set_line_width(lw)
    ctx.set_line_join(1)
    ctx.stroke()
    # lattice crosses
    ctx.set_line_width(max(1.5, lw * 0.45))
    levels = [0.0, 0.08, 0.17, 0.26, 0.36, 0.48, 0.6, 0.72, 0.84]
    for a, b in zip(levels, levels[1:]):
        ya, yb = base - a * h, base - b * h
        if a < 0.17:
            continue
        ctx.move_to(cx - half(a), ya)
        ctx.line_to(cx + half(b), yb)
        ctx.move_to(cx + half(a), ya)
        ctx.line_to(cx - half(b), yb)
    ctx.stroke()
    # leg lattice on the lower legs
    for side in (-1, 1):
        for i in range(4):
            u0, u1 = 0.02 + i * 0.04, 0.06 + i * 0.04
            xo0, xo1 = half(u0), half(u1)
            xi0, xi1 = xo0 * 0.62, xo1 * 0.62
            ctx.move_to(cx + side * xo0, base - u0 * h)
            ctx.line_to(cx + side * xi1, base - u1 * h)
            ctx.move_to(cx + side * xi0, base - u0 * h)
            ctx.line_to(cx + side * xo1, base - u1 * h)
    ctx.stroke()
    # platforms
    for u, ext in ((0.17, 1.12), (0.36, 1.15), (0.84, 1.6)):
        w = half(u) * ext
        ctx.rectangle(cx - w, base - u * h - h * 0.012, 2 * w, h * 0.024)
        ctx.set_source_rgb(*hexc(color))
        ctx.fill_preserve()
        ctx.set_source_rgb(*hexc(line))
        ctx.set_line_width(lw * 0.8)
        ctx.stroke()


def building(ctx, x, y, w, h, color="#efe1c4", roof="#6d7fa1", rnd=None):
    rnd = rnd or random.Random(int(x * 7 + w))
    rect(ctx, x, y - h, w, h, color)
    ctx.move_to(x - 10, y - h)
    ctx.line_to(x + 18, y - h - 70)
    ctx.line_to(x + w - 18, y - h - 70)
    ctx.line_to(x + w + 10, y - h)
    ctx.close_path()
    fill_out(ctx, roof)
    cols = max(2, int(w // 70))
    rows = max(2, int(h // 110))
    gx = w / cols
    for r in range(rows):
        for c in range(cols):
            wx = x + c * gx + gx * 0.25
            wy = y - h + 30 + r * (h - 60) / rows
            rect(ctx, wx, wy, gx * 0.5, 62, "#8fb7d9" if rnd.random() > 0.2 else "#f6d77a", 4)
            ctx.move_to(wx - 6, wy + 66)
            ctx.line_to(wx + gx * 0.5 + 6, wy + 66)
            outline(ctx, 4)


# ---------------------------------------------------------------- scenes
GROUND_Y = 1560


def paris(ctx, t, variant="day"):
    def static(c):
        if variant == "sunset":
            sky(c, "#f59e6b", "#fde3b0")
        else:
            sky(c)
        # far hills
        c.move_to(-M, 1250)
        c.curve_to(200, 1150, 500, 1230, 700, 1180)
        c.curve_to(900, 1140, 1100, 1210, W + M, 1170)
        c.line_to(W + M, 1500)
        c.line_to(-M, 1500)
        c.close_path()
        c.set_source_rgb(*hexc("#9fcf8f" if variant == "day" else "#d9a27c"))
        c.fill()
        eiffel(c, 540, 1330, 1080)
        building(c, -60, 1420, 300, 380, "#efe1c4", "#6d7fa1")
        building(c, 860, 1420, 300, 420, "#f1d9c7", "#5f6f8f")
        # trees and street
        tree(c, 210, 1440, 1.1)
        tree(c, 880, 1440, 1.15)
        c.rectangle(-M, 1420, W + 2 * M, H)
        c.set_source_rgb(*hexc("#d8c39b"))
        c.fill()
        c.move_to(-M, 1420)
        c.line_to(W + M, 1420)
        outline(c, 5)
        # road with perspective
        c.move_to(380, 1420)
        c.line_to(700, 1420)
        c.line_to(1060, H + M)
        c.line_to(20, H + M)
        c.close_path()
        c.set_source_rgb(*hexc("#c4ab80"))
        c.fill()
        rng = random.Random(4)
        c.set_source_rgba(*INK, 0.25)
        c.set_line_width(3)
        for i in range(60):
            x, y = rng.uniform(0, W), rng.uniform(1450, H)
            c.move_to(x, y)
            c.line_to(x + 30, y)
        c.stroke()
        # lamp post
        for lx in (120, 960):
            c.rectangle(lx - 6, 1150, 12, 290)
            fill_out(c, "#2f2f38", 4)
            c.arc(lx, 1140, 24, 0, 2 * math.pi)
            fill_out(c, "#f6d77a", 4)
        # sun
        if variant == "day":
            c.arc(900, 220, 90, 0, 2 * math.pi)
            c.set_source_rgb(*hexc("#fff3b0"))
            c.fill()
        else:
            c.arc(820, 1120, 150, 0, 2 * math.pi)
            c.set_source_rgba(*hexc("#ffd36e"), 0.6)
            c.fill()

    blit(ctx, "paris_" + variant, static)
    # drifting clouds (live)
    for i, (x0, y, s) in enumerate(((100, 300, 1.0), (650, 520, 0.8), (-200, 760, 0.7))):
        x = (x0 + t * (14 + i * 6)) % (W + 500) - 250
        cloud(ctx, x, y, s, "#ffffff" if variant == "day" else "#ffe7cc")


def hotel(ctx, t):
    def static(c):
        # wallpaper stripes
        c.rectangle(-M, -M, W + 2 * M, H + 2 * M)
        c.set_source_rgb(*hexc("#8e2f3f"))
        c.fill()
        for i in range(-2, 16):
            c.rectangle(i * 90, -M, 34, 1500 + M)
            c.set_source_rgb(*hexc("#a33a4c"))
            c.fill()
        # wainscot
        rect(c, -M, 1100, W + 2 * M, 400, "#6e3b23")
        for i in range(-1, 8):
            rect(c, i * 170 + 30, 1150, 120, 280, "#7f4a2d", 4)
        # big window with the tower visible
        rect(c, 330, 260, 420, 640, "#9fd8f2", 8)
        c.save()
        c.rectangle(330, 260, 420, 640)
        c.clip()
        eiffel(c, 540, 930, 600, lw=4)
        c.restore()
        c.move_to(540, 260)
        c.line_to(540, 900)
        c.move_to(330, 580)
        c.line_to(750, 580)
        outline(c, 8)
        # curtains
        for x, d in ((300, 1), (780, -1)):
            c.move_to(x, 220)
            c.curve_to(x + d * 90, 500, x - d * 20, 700, x + d * 70, 960)
            c.line_to(x - d * 60, 960)
            c.line_to(x - d * 60, 220)
            c.close_path()
            fill_out(c, "#d4a12c")
        rect(c, 230, 200, 620, 30, "#d4a12c")
        # floor
        c.rectangle(-M, 1500, W + 2 * M, H)
        c.set_source_rgb(*hexc("#5a3320"))
        c.fill()
        c.move_to(-M, 1500)
        c.line_to(W + M, 1500)
        outline(c, 6)
        # rug
        c.save()
        c.translate(540, 1700)
        c.scale(520, 120)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        fill_out(c, "#2f5d8a", 6)
        # picture frame
        rect(c, 840, 380, 170, 210, "#d4a12c", 6)
        rect(c, 860, 400, 130, 170, "#7fb3d5", 4)

    blit(ctx, "hotel", static)
    # swinging chandelier
    ang = math.sin(t * 1.6) * 0.06
    ctx.save()
    ctx.translate(540, -M)
    ctx.rotate(ang)
    ctx.move_to(0, 0)
    ctx.line_to(0, 260)
    outline(ctx, 5)
    ctx.translate(0, 300)
    ctx.move_to(-120, 0)
    ctx.curve_to(-90, 60, 90, 60, 120, 0)
    ctx.close_path()
    fill_out(ctx, "#e0b43a")
    for x in (-100, -50, 0, 50, 100):
        ctx.rectangle(x - 7, -40, 14, 40)
        fill_out(ctx, "#fff6dd", 3)
        flick = 1 + 0.15 * noise1(t * 6, x)
        ctx.arc(x, -50, 9 * flick, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#ffcf4a"))
        ctx.fill()
    ctx.restore()


def table(ctx, x, y, w=520):
    rect(ctx, x - w / 2, y - 30, w, 36, "#8a5a35")
    for lx in (x - w / 2 + 30, x + w / 2 - 48):
        rect(ctx, lx, y + 6, 18, 150, "#6e4426")


def hills(ctx, t):
    def static(c):
        sky(c, "#7cc6ef", "#e4f6ff")
        # alps
        c.move_to(-M, 1100)
        pts = [(-50, 700), (150, 1000), (330, 620), (520, 980), (720, 560), (930, 950), (W + M, 700)]
        for x, y in pts:
            c.line_to(x, y)
        c.line_to(W + M, 1400)
        c.line_to(-M, 1400)
        c.close_path()
        fill_out(c, "#8aa0c8")
        for x, y in pts[1:-1]:
            if y < 700:
                c.move_to(x, y)
                c.line_to(x - 70, y + 110)
                c.line_to(x - 20, y + 90)
                c.line_to(x + 20, y + 120)
                c.line_to(x + 75, y + 105)
                c.close_path()
                fill_out(c, "#ffffff", 4)
        c.move_to(-M, 1300)
        c.curve_to(300, 1180, 700, 1320, W + M, 1220)
        c.line_to(W + M, H + M)
        c.line_to(-M, H + M)
        c.close_path()
        fill_out(c, "#7cc26e")
        c.rectangle(-M, 1420, W + 2 * M, H)
        c.set_source_rgb(*hexc("#6aad5d"))
        c.fill()
        c.move_to(-M, 1420)
        c.line_to(W + M, 1420)
        outline(c, 5)
        tree(c, 120, 1440, 0.9, "#4f9a49")
        tree(c, 980, 1440, 1.0, "#4f9a49")
        # signpost
        rect(c, 760, 1180, 16, 260, "#7a5634", 4)
        rect(c, 650, 1150, 250, 80, "#f3e2b3", 5)
        from .text import text_center
        text_center(c, "AUSTRIA", 775, 1190, 50, "#2c2c34")

    blit(ctx, "hills", static)
    for i, (x0, y, s) in enumerate(((0, 250, 0.9), (600, 420, 0.7))):
        x = (x0 + t * 18) % (W + 500) - 250
        cloud(ctx, x, y, s)


def police(ctx, t):
    def static(c):
        c.rectangle(-M, -M, W + 2 * M, H + 2 * M)
        c.set_source_rgb(*hexc("#c9d6e8"))
        c.fill()
        for i in range(-2, 14):
            c.move_to(-M, i * 120)
            c.line_to(W + M, i * 120)
        c.set_source_rgba(*INK, 0.08)
        c.set_line_width(3)
        c.stroke()
        rect(c, 190, 300, 700, 170, "#2b4a9b", 7)
        from .text import text_center
        text_center(c, "POLICE", 540, 385, 120, "#ffffff")
        # wanted poster
        rect(c, 120, 620, 260, 330, "#f3e2b3", 5)
        text_center(c, "WANTED", 250, 670, 46, "#8e2f3f")
        c.arc(250, 790, 70, 0, 2 * math.pi)
        fill_out(c, "#f6efe6", 4)
        c.rectangle(205, 680, 90, 50)
        c.set_source_rgb(*hexc("#1d1d22"))
        c.fill()
        c.arc(222, 785, 8, 0, 2 * math.pi)
        c.arc(278, 785, 8, 0, 2 * math.pi)
        c.set_source_rgb(*INK)
        c.fill()
        text_center(c, "?", 250, 905, 60, "#2c2c34")
        # desk
        rect(c, 560, 1180, 420, 300, "#6e4426", 6)
        rect(c, 600, 1220, 340, 90, "#7f4a2d", 4)
        # floor
        c.rectangle(-M, 1500, W + 2 * M, H)
        c.set_source_rgb(*hexc("#8a96a8"))
        c.fill()
        c.move_to(-M, 1500)
        c.line_to(W + M, 1500)
        outline(c, 6)

    blit(ctx, "police", static)


def newspaper(ctx, t, headline=("THE EIFFEL TOWER", "IS RUSTING!"), sub="Repairs would cost a fortune"):
    def static(c):
        c.rectangle(-M, -M, W + 2 * M, H + 2 * M)
        c.set_source_rgb(*hexc("#3a2c26"))
        c.fill()
        c.save()
        c.translate(540, 960)
        c.rotate(math.radians(-3))
        c.rectangle(-470, -720, 940, 1440)
        fill_out(c, "#efe9da", 8)
        from .text import text_center
        text_center(c, "LE PARIS DAILY", 0, -620, 78, "#1d1d22", font="DejaVu Serif")
        c.move_to(-430, -560)
        c.line_to(430, -560)
        c.move_to(-430, -548)
        c.line_to(430, -548)
        outline(c, 4)
        text_center(c, "1925", 0, -510, 34, "#1d1d22", font="DejaVu Serif")
        text_center(c, headline[0], 0, -390, 92, "#1d1d22")
        text_center(c, headline[1], 0, -280, 110, "#b8333a")
        text_center(c, sub, 0, -190, 44, "#3a3a44", font="DejaVu Serif")
        # picture: rusty tower
        rect(c, -400, -130, 800, 520, "#cfe6f2", 6)
        c.save()
        c.rectangle(-400, -130, 800, 520)
        c.clip()
        eiffel(c, 0, 400, 480, color="#b2703a", lw=4)
        rng = random.Random(9)
        for i in range(40):
            c.arc(rng.uniform(-110, 110), rng.uniform(40, 380), rng.uniform(4, 11), 0, 2 * math.pi)
            c.set_source_rgba(*hexc("#8a3d14"), 0.8)
            c.fill()
        c.restore()
        c.set_source_rgba(*INK, 0.45)
        c.set_line_width(5)
        for col in (-1, 1):
            for i in range(9):
                y = 440 + i * 30
                c.move_to(col * 420, y)
                c.line_to(col * 20, y)
        c.stroke()
        c.restore()

    blit(ctx, "news_" + "_".join(headline), static)


def stage(ctx, t, color="#f6d77a"):
    """Plain punchy background for title / end cards."""
    ctx.rectangle(-M, -M, W + 2 * M, H + 2 * M)
    ctx.set_source_rgb(*hexc(color))
    ctx.fill()
    ctx.save()
    ctx.translate(540, 960)
    ctx.rotate(t * 0.15)
    for i in range(16):
        ctx.move_to(0, 0)
        a0 = i * 2 * math.pi / 16
        ctx.line_to(math.cos(a0) * 2000, math.sin(a0) * 2000)
        ctx.line_to(math.cos(a0 + 0.2) * 2000, math.sin(a0 + 0.2) * 2000)
        ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.25)
    ctx.fill()
    ctx.restore()


def sparkle_burst(ctx, x, y, p, color="#ffd84a", n=8, r=120):
    """Particles flying outwards, p in 0..1."""
    if p <= 0 or p >= 1:
        return
    for i in range(n):
        a = i * 2 * math.pi / n + 0.3
        d = r * (0.3 + p)
        _star(ctx, x + math.cos(a) * d, y + math.sin(a) * d, 16 * (1 - p), 7 * (1 - p))
        ctx.set_source_rgba(*hexc(color), 1 - p)
        ctx.fill()


def dust(ctx, x, y, p, n=6):
    if p <= 0 or p >= 1:
        return
    for i in range(n):
        dx = -i * 38 - p * 120
        r = (24 + i * 4) * (1 - p) + 4
        ctx.arc(x + dx, y - 20 - (i % 2) * 18 - p * 30, r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.85, 0.82, 0.76, 0.85 * (1 - p))
        ctx.fill()


def speed_lines(ctx, p, color=(1, 1, 1)):
    if p <= 0:
        return
    rng = random.Random(int(p * 1000) % 7)
    ctx.set_source_rgba(*color, 0.55 * p)
    ctx.set_line_width(6)
    for i in range(18):
        y = rng.uniform(0, H)
        x = rng.uniform(-200, W)
        ctx.move_to(x, y)
        ctx.line_to(x + rng.uniform(200, 500), y)
    ctx.stroke()
