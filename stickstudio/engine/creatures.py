"""Non-human characters and big props for the Emu War episode.

Emu: drawn around its ground point like the stick rig, ~520 units tall at s=1 with the neck up, so the
same 3D anchors (feet + head height) place it at the right size. Legs are two segments that always bend
the emu way (the visible joint is the ankle: it points backward). Feet stay planted unless running.
"""
import math

from .core import hexc, clamp

INK = hexc("#141418")
BODY = hexc("#4f4133")
BODY_LIGHT = hexc("#7a6650")
BODY_DARK = hexc("#3a2f25")
NECK = hexc("#7f93ab")
LEG = hexc("#8d8a84")
BEAK = hexc("#2a2622")

EMU_EXPR = {  # pupil size, brow angle (+ = angry), lid
    "stare": (0.55, 0, 0.0), "angry": (0.5, 24, 0.25), "smug": (0.6, -6, 0.5), "shock": (0.32, -18, 0.0),
    "happy": (0.6, -10, 0.0), "dumb": (0.7, 0, 0.0),
}

EMU_DEFAULT = dict(x=540.0, y=1500.0, s=1.0, face=1, run=0.0, neck=1.0, head_tilt=0.0, look=0.0, expr="stare",
                   peck=0.0, wing=0.0, squash=0.0, alpha=1.0, jump=0.0, step=0.0, dust=0.0)


def _stroke_fill(ctx, fill, w=5):
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(w)
    ctx.stroke()


class Emu:
    def __init__(self, name="emu", seed=0.0, tint=1.0):
        self.name, self.seed, self.tint = name, seed, tint

    def _leg(self, ctx, hip, foot, l1, l2):
        """Two-bone leg whose joint bends backward (emu 'knee' = ankle). Returns the joint point."""
        dx, dy = foot[0] - hip[0], foot[1] - hip[1]
        D = max(abs(l1 - l2) + 1, min(l1 + l2 - 0.5, math.hypot(dx, dy)))
        a = math.atan2(dy, dx)
        al = math.acos(clamp((l1 * l1 + D * D - l2 * l2) / (2 * l1 * D), -1, 1))
        # joint on the BACK side (-x in local facing space)
        j = (hip[0] + math.cos(a + al) * l1, hip[1] + math.sin(a + al) * l1)
        for col, w in ((INK, 26), (LEG, 16)):
            ctx.set_source_rgb(*col)
            ctx.set_line_width(w)
            ctx.set_line_cap(1)
            ctx.set_line_join(1)
            ctx.move_to(*hip)
            ctx.line_to(*j)
            ctx.line_to(*foot)
            ctx.stroke()
        # three forward toes
        for ang in (-0.35, 0.0, 0.35):
            ex = foot[0] + math.cos(ang) * 40
            ey = foot[1] + math.sin(ang) * 10
            for col, w in ((INK, 14), (LEG, 7)):
                ctx.set_source_rgb(*col)
                ctx.set_line_width(w)
                ctx.move_to(*foot)
                ctx.line_to(ex, ey)
                ctx.stroke()
        return j

    def draw(self, ctx, P, t):
        P = {**EMU_DEFAULT, **P}
        face = 1 if P["face"] >= 0 else -1
        ctx.save()
        ctx.translate(P["x"], P["y"] - P["jump"])
        ctx.scale(P["s"] * face, P["s"])
        if P["squash"]:
            ctx.scale(1 + P["squash"] * 0.12, 1 - P["squash"] * 0.12)
        if P["alpha"] < 1:
            ctx.push_group()
        run = P["run"]
        ph = t * run * 2 * math.pi + self.seed * 3 if run > 0 else 0.0
        bob = -abs(math.sin(ph)) * 22 if run > 0 else 0.0
        lean = 0.32 if run > 0 else 0.0  # body tips forward when running
        body_c = (0.0, -255 + bob)
        hipL = (-14, body_c[1] + 52)
        # feet: planted when standing, big ellipse strides when running
        if run > 0:
            feet = []
            for k in (0, 1):
                q = ph + k * math.pi
                feet.append((math.cos(q) * 95 + 10, -max(0.0, math.sin(q)) * 70))
        else:
            st = P["step"]
            feet = [(-26 + 30 * st, 0.0), (32 - 10 * st, -18 * max(0, math.sin(st * math.pi)))]
        # far leg first (darker)
        self._leg(ctx, (hipL[0] + 6, hipL[1]), feet[1], 150, 150)
        # tail + body
        ctx.save()
        ctx.translate(*body_c)
        ctx.rotate(-lean * 0.35)
        ctx.move_to(-150, -10)
        ctx.curve_to(-160, -110, 40, -150, 110, -70)
        ctx.curve_to(150, -30, 120, 60, 40, 80)
        ctx.curve_to(-40, 95, -120, 70, -170, 40)
        ctx.curve_to(-205, 30, -200, 0, -150, -10)
        ctx.close_path()
        _stroke_fill(ctx, BODY, 7)
        # shaggy feather strokes (deterministic, they don't jitter)
        ctx.set_line_cap(1)
        for i in range(26):
            u = (i * 0.618 + self.seed) % 1
            v = (i * 0.383 + self.seed * 0.5) % 1
            x0 = -150 + u * 250
            y0 = -90 + v * 150 - 0.0012 * (x0 + 20) ** 2 * 0.8
            if y0 > 60:
                continue
            ctx.move_to(x0, y0)
            ctx.curve_to(x0 - 14, y0 + 16, x0 - 22, y0 + 30, x0 - 30, y0 + 38)
            ctx.set_source_rgb(*(BODY_LIGHT if i % 3 else BODY_DARK))
            ctx.set_line_width(5)
            ctx.stroke()
        # tiny wing
        w = P["wing"]
        ctx.save()
        ctx.translate(10, -40)
        ctx.rotate(-0.4 - w * 0.9 * abs(math.sin(t * 18)))
        ctx.move_to(0, 0)
        ctx.curve_to(-20, 20, -60, 30, -70, 18)
        ctx.curve_to(-50, 0, -20, -8, 0, 0)
        _stroke_fill(ctx, BODY_DARK, 4)
        ctx.restore()
        ctx.restore()
        # near leg
        self._leg(ctx, hipL, feet[0], 150, 150)
        # neck: S-curve from the chest to the head, raised by P["neck"], dipped by peck
        nk = P["neck"]
        pk = P["peck"]
        base = (body_c[0] + 95, body_c[1] - 70)
        head = (base[0] + 60 + 90 * pk + 30 * lean, base[1] - (200 * nk) + 260 * pk + 40 * lean)
        c1 = (base[0] + 60, base[1] - 40)
        c2 = (head[0] - 70, head[1] + 90 * (1 - pk))
        for col, wdt in ((INK, 46), (NECK, 34)):
            ctx.set_source_rgb(*col)
            ctx.set_line_width(wdt)
            ctx.move_to(*base)
            ctx.curve_to(*c1, *c2, *head)
            ctx.stroke()
        # dark feather streaks down the back of the neck
        ctx.set_source_rgb(*BODY_DARK)
        ctx.set_line_width(7)
        for k in range(5):
            u = 0.15 + k * 0.16
            x = (1 - u) ** 3 * base[0] + 3 * (1 - u) ** 2 * u * c1[0] + 3 * (1 - u) * u * u * c2[0] + u ** 3 * head[0]
            y = (1 - u) ** 3 * base[1] + 3 * (1 - u) ** 2 * u * c1[1] + 3 * (1 - u) * u * u * c2[1] + u ** 3 * head[1]
            ctx.move_to(x - 16, y + 4)
            ctx.line_to(x - 4, y - 8)
            ctx.stroke()
        # head
        ctx.save()
        ctx.translate(*head)
        ctx.rotate(math.radians(P["head_tilt"]) + 0.15 * pk)
        ctx.save()
        ctx.scale(1.0, 0.86)
        ctx.arc(0, 0, 46, 0, 2 * math.pi)
        ctx.restore()
        _stroke_fill(ctx, NECK, 5)
        # feather mohawk
        for k in range(5):
            a = math.radians(-150 + k * 22)
            ctx.move_to(math.cos(a) * 34, math.sin(a) * 34)
            ctx.line_to(math.cos(a) * 66 - 8, math.sin(a) * 66 - 6)
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(9)
            ctx.stroke()
            ctx.move_to(math.cos(a) * 34, math.sin(a) * 34)
            ctx.line_to(math.cos(a) * 62 - 8, math.sin(a) * 62 - 6)
            ctx.set_source_rgb(*BODY_DARK)
            ctx.set_line_width(5)
            ctx.stroke()
        # beak: flat, slightly open when pecking
        op = 6 + 10 * pk
        ctx.move_to(32, -8)
        ctx.curve_to(60, -14, 86, -8, 96, -2)
        ctx.curve_to(80, 0, 60, 2, 34, 4)
        ctx.close_path()
        _stroke_fill(ctx, BEAK, 4)
        ctx.move_to(34, 6)
        ctx.curve_to(56, 8 + op * 0.3, 78, 6 + op * 0.4, 90, 4)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        # the eye: big and unsettlingly calm
        pup, brow, lid = EMU_EXPR.get(P["expr"], EMU_EXPR["stare"])
        ex, ey, er = 8, -10, 22
        ctx.arc(ex, ey, er, 0, 2 * math.pi)
        _stroke_fill(ctx, (1, 1, 1), 4)
        ctx.arc(ex + 6 + 6 * P["look"], ey + 1, er * pup, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#c4661f"))  # orange iris ring
        ctx.fill()
        ctx.arc(ex + 6 + 6 * P["look"], ey + 1, er * pup * 0.55, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.arc(ex + 2 + 6 * P["look"], ey - 5, 4, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        if lid > 0:
            ctx.save()
            ctx.arc(ex, ey, er, 0, 2 * math.pi)
            ctx.clip()
            ctx.rectangle(ex - er, ey - er, er * 2, er * 2 * lid)
            ctx.set_source_rgb(*NECK)
            ctx.fill()
            ctx.restore()
        ctx.save()  # brow
        ctx.translate(ex, ey - er - 4)
        ctx.rotate(math.radians(brow))
        ctx.move_to(-22, 0)
        ctx.line_to(22, 0)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.restore()
        ctx.restore()  # head
        if P["dust"] > 0 and run > 0:
            for k in range(4):
                q = (t * 3 + k * 0.25) % 1
                ctx.arc(-120 - q * 200, -10 - q * 30, 18 + q * 30, 0, 2 * math.pi)
                ctx.set_source_rgba(0.85, 0.68, 0.45, 0.45 * (1 - q) * P["dust"])
                ctx.fill()
        if P["alpha"] < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(P["alpha"])
        ctx.restore()
        hx = P["x"] + head[0] * P["s"] * face
        hy = P["y"] - P["jump"] + head[1] * P["s"]
        return {"head": (hx, hy)}


# ---------------------------------------------------------------- Lewis gun (side view)
def lewis_gun(ctx, x, y, s, face=1, angle=0.0, t=0.0, fire=0.0, bipod=True):
    """Draw a Lewis gun with its muzzle pointing toward `face`. (x, y) = the pistol grip.
    Returns world points for hands: grip (trigger hand) and fore (support hand on the shroud/drum)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * face, s)
    ctx.rotate(math.radians(-angle))
    ctx.set_line_join(1)
    ctx.set_line_cap(1)
    # wooden butt stock
    ctx.move_to(-20, -40)
    ctx.line_to(-150, -52)
    ctx.line_to(-160, -8)
    ctx.line_to(-30, -14)
    ctx.close_path()
    _stroke_fill(ctx, hexc("#7a4a22"), 5)
    # receiver
    ctx.rectangle(-30, -60, 110, 46)
    _stroke_fill(ctx, hexc("#2b2d31"), 5)
    # pistol grip
    ctx.move_to(-8, -16)
    ctx.line_to(4, 40)
    ctx.line_to(26, 40)
    ctx.line_to(20, -16)
    ctx.close_path()
    _stroke_fill(ctx, hexc("#5e3a1c"), 4)
    # fat cooling shroud with fins + thin muzzle
    ctx.rectangle(80, -68, 240, 60)
    _stroke_fill(ctx, hexc("#34373c"), 5)
    ctx.set_source_rgb(*hexc("#1e2023"))
    ctx.set_line_width(4)
    for k in range(9):
        ctx.move_to(100 + k * 24, -64)
        ctx.line_to(100 + k * 24, -12)
        ctx.stroke()
    ctx.rectangle(320, -48, 70, 20)
    _stroke_fill(ctx, hexc("#2b2d31"), 4)
    # pan magazine on top (flat drum seen from the side) - spins while firing
    ctx.save()
    ctx.translate(40, -72)
    ctx.scale(1, 0.32)
    ctx.arc(0, 0, 70, 0, 2 * math.pi)
    ctx.restore()
    _stroke_fill(ctx, hexc("#3b3e44"), 5)
    sp = t * 20 * fire
    for k in range(6):
        a = sp + k * math.pi / 3
        ctx.move_to(40 + math.cos(a) * 60, -72 + math.sin(a) * 60 * 0.32)
        ctx.line_to(40 + math.cos(a) * 20, -72 + math.sin(a) * 20 * 0.32)
        ctx.set_source_rgb(*hexc("#1e2023"))
        ctx.set_line_width(3)
        ctx.stroke()
    if bipod:
        for dx in (-30, 30):
            ctx.move_to(300, -20)
            ctx.line_to(300 + dx, 70)
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(7)
            ctx.stroke()
    if fire > 0 and (t * 24) % 1 < 0.5:  # muzzle flash on alternate frames
        ctx.move_to(390, -38)
        for k in range(9):
            a = math.radians(-60 + k * 15)
            r = 70 if k % 2 == 0 else 32
            ctx.line_to(400 + math.cos(a) * r, -38 + math.sin(a) * r)
        ctx.close_path()
        ctx.set_source_rgb(*hexc("#ffd23f"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*hexc("#ff7a1a"))
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.restore()

    def w(px, py):
        a = math.radians(-angle)
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        return x + rx * s * face, y + ry * s

    return {"grip": w(14, 20), "fore": w(130, -14), "stock": w(-150, -30)}
