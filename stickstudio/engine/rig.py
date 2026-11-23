"""Rigged 2D stick-figure characters drawn with pycairo.

Coordinates: a character is drawn around its ground point (x, y) = point between the feet.
Limb angles are in degrees: 0 = hanging straight down, positive = swung toward the
direction the character faces. Elbows bend forward (+), knees bend backward (+).
"""
import math
from dataclasses import dataclass, field

from .core import hexc, clamp, lerp

INK = hexc("#141418")
SKIN = hexc("#f6efe6")

# ---- geometry (scale 1) ----
THIGH, SHIN = 100, 98
TORSO = 150
HEAD_R = 80
UPPER_ARM, FOREARM = 82, 78
LIMB_W = 10
OUTLINE = 6

EXPRESSIONS = {
    #            eye  pupil lid   brow(angle, raise) mouth
    "neutral":  (1.0, 1.0, 0.0, (0, 0), "soft"),
    "smile":    (1.0, 1.0, 0.0, (-4, 4), "smile"),
    "grin":     (1.0, 1.0, 0.15, (-6, 6), "grin"),
    "smug":     (1.0, 1.0, 0.45, (8, 0), "smirk"),
    "sly":      (0.95, 1.0, 0.55, (16, -2), "smirk"),
    "shock":    (1.25, 0.6, 0.0, (-14, 16), "o"),
    "worried":  (1.05, 0.9, 0.1, (-20, 8), "wobble"),
    "sad":      (1.0, 1.0, 0.35, (-18, 2), "frown"),
    "angry":    (1.0, 0.9, 0.3, (22, -6), "frown"),
    "embarrassed": (0.95, 1.0, 0.45, (-16, 4), "wobble"),
    "excited":  (1.15, 1.0, 0.0, (-8, 12), "grin"),
    "greedy":   (1.2, 1.0, 0.0, (-8, 12), "grin"),   # sparkly eyes
    "thinking": (1.0, 1.0, 0.25, (10, 4), "flat"),
    "wink":     (1.0, 1.0, 0.0, (-6, 6), "grin"),
}

DEFAULT_POSE = dict(
    x=540.0, y=1560.0, s=1.0, face=1, lean=0.0, tilt=0.0, bob=0.0, jump=0.0,
    # back arm / front arm (shoulder, elbow); back leg / front leg (hip, knee)
    ba=-10.0, bb=12.0, fa=10.0, fb=12.0,
    bl=-5.0, bk=4.0, fl=5.0, fk=4.0,
    expr="neutral", look=0.0, lookY=0.0, walk=0.0, run=0.0, alpha=1.0,
    hold=None, hold_back=None, blush=0.0, sweat=0.0, mouth=None, hat_off=0.0,
    idle=1.0, blink=1.0, squash=0.0, prop_angle=0.0,
)


@dataclass
class Look:
    coat: str = "#5b6ee1"
    coat_dark: str = "#3d4bb0"
    tie: str = None
    hat: str = None          # tophat | bowler | flatcap | kepi | None
    hat_color: str = "#1d1d22"
    hat_band: str = "#b8333a"
    hair: str = None         # tuft | side | curl | None
    mustache: str = None     # curly | thick | None
    glasses: bool = False
    monocle: bool = False
    skin: str = "#f6efe6"
    badge: bool = False
    height: float = 1.0
    width: float = 1.0
    belly: float = 0.0
    stick: bool = False      # thin "pure stick" body (no coat), like classic stick-figure horror shorts
    limb: str = None         # limb fill colour; None = solid ink. With a colour, limbs get an ink outline.


def _v(angle_deg, face):
    a = math.radians(angle_deg)
    return math.sin(a) * face, math.cos(a)


class Character:
    def __init__(self, name, look: Look, seed=0.0):
        self.name = name
        self.look = look
        self.seed = seed

    # ------------------------------------------------------------------ helpers
    def _limb(self, ctx, p0, a1, l1, a2, l2, face, width):
        dx, dy = _v(a1, face)
        p1 = (p0[0] + dx * l1, p0[1] + dy * l1)
        dx, dy = _v(a2, face)
        p2 = (p1[0] + dx * l2, p1[1] + dy * l2)
        ctx.set_line_cap(1)  # round
        ctx.set_line_join(1)
        passes = [(INK, width)]
        if self.look.limb:
            passes = [(INK, width + 9), (hexc(self.look.limb), width)]
        for col, w in passes:
            ctx.set_source_rgb(*col)
            ctx.set_line_width(w)
            ctx.move_to(*p0)
            ctx.line_to(*p1)
            ctx.line_to(*p2)
            ctx.stroke()
        return p1, p2

    def _hand(self, ctx, p, r=12):
        ctx.arc(p[0], p[1], r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc(self.look.skin))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4.5)
        ctx.stroke()

    def _shoe(self, ctx, p, face, ang):
        ctx.save()
        ctx.translate(p[0], p[1])
        ctx.rotate(math.radians(-ang * 0.35) * face)
        ctx.scale(1, 0.48)
        ctx.arc(face * 13, 0, 25, 0, 2 * math.pi)
        ctx.restore()
        if self.look.limb:
            ctx.set_source_rgb(*hexc(self.look.limb))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(4)
            ctx.stroke()
        else:
            ctx.set_source_rgb(*INK)
            ctx.fill()

    # ------------------------------------------------------------------ pose
    def resolve(self, P, t):
        """Apply procedural layers (idle, walk/run cycles) to a pose dict."""
        P = {**DEFAULT_POSE, **P}
        sd = self.seed
        idle = P["idle"]
        if idle:
            P["bob"] += math.sin(t * 2.4 + sd) * 2.5 * idle
            P["tilt"] += math.sin(t * 1.3 + sd * 2) * 2.0 * idle
            P["ba"] += math.sin(t * 2.4 + sd) * 2.0 * idle
            P["fa"] -= math.sin(t * 2.4 + sd + 0.5) * 2.0 * idle
        if P["walk"] > 0 or P["run"] > 0:
            run = P["run"] > 0
            sp = P["run"] if run else P["walk"]
            ph = t * sp * 2 * math.pi + sd
            amp = 42 if run else 26
            s = math.sin(ph)
            P["fl"] = amp * s + (8 if run else 2)
            P["bl"] = -amp * s + (8 if run else 2)
            P["fk"] = 10 + (55 if run else 30) * max(0.0, math.cos(ph))
            P["bk"] = 10 + (55 if run else 30) * max(0.0, -math.cos(ph))
            if not P.get("lock_arms"):
                P["fa"] = -amp * 0.8 * s + (15 if run else 0)
                P["fb"] = 70 if run else 18
            if not P.get("lock_arms"):
                P["ba"] = amp * 0.8 * s + (15 if run else 0)
                P["bb"] = 70 if run else 18
            P["bob"] += -abs(math.cos(ph)) * (12 if run else 6)
            if run:
                P["lean"] += 14
        return P

    # ------------------------------------------------------------------ draw
    def draw(self, ctx, P, t, mouth_open=0.0):
        P = self.resolve(P, t)
        lk = self.look
        face = 1 if P["face"] >= 0 else -1
        s = P["s"]
        ctx.save()
        ctx.translate(P["x"], P["y"] - P["jump"])
        ctx.scale(s, s)
        if P["squash"]:
            ctx.scale(1 + P["squash"] * 0.12, 1 - P["squash"] * 0.12)
        alpha = P["alpha"]
        if alpha < 1:
            ctx.push_group()

        legs = (THIGH + SHIN) * lk.height
        hip = (0.0, -legs + 6 + P["bob"])
        lean = P["lean"]
        tdx, tdy = math.sin(math.radians(lean)) * face, -math.cos(math.radians(lean))
        tl = TORSO * lk.height
        neck = (hip[0] + tdx * tl, hip[1] + tdy * tl)
        shoulder = (hip[0] + tdx * (tl - 18), hip[1] + tdy * (tl - 18))

        # legs
        for (a, k) in ((P["bl"], P["bk"]), (P["fl"], P["fk"])):
            knee, foot = self._limb(ctx, hip, a, THIGH * lk.height, a - k, SHIN * lk.height, face, LIMB_W)
            self._shoe(ctx, foot, face, a - k)

        # back arm (+ prop)
        elbow_b, hand_b = self._limb(ctx, shoulder, P["ba"], UPPER_ARM, P["ba"] + P["bb"], FOREARM, face, LIMB_W)
        if P["hold_back"]:
            draw_prop(ctx, P["hold_back"], hand_b, face, P["prop_angle"], t)
        self._hand(ctx, hand_b)

        # torso / coat
        if lk.stick:
            self._limb(ctx, hip, 180 - lean, 0.001, 180 - lean, math.hypot(neck[0] - hip[0], neck[1] - hip[1]) + 4,
                       face, LIMB_W + 4)
        else:
            self._torso(ctx, hip, neck, face, lean)

        # head
        hc = (neck[0] + tdx * (HEAD_R - 4), neck[1] + tdy * (HEAD_R - 4))
        self._head(ctx, hc, P, t, face, mouth_open)

        # front arm (+ prop)
        elbow_f, hand_f = self._limb(ctx, shoulder, P["fa"], UPPER_ARM, P["fa"] + P["fb"], FOREARM, face, LIMB_W)
        if P["hold"]:
            draw_prop(ctx, P["hold"], hand_f, face, P["prop_angle"], t)
        self._hand(ctx, hand_f)

        if alpha < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha)
        ctx.restore()
        # world-space anchor points (useful for props / effects)
        return {"hand_f": hand_f, "hand_b": hand_b, "head": hc}

    def _torso(self, ctx, hip, neck, face, lean):
        lk = self.look
        ax = (neck[0] - hip[0], neck[1] - hip[1])
        L = math.hypot(*ax)
        ux, uy = ax[0] / L, ax[1] / L
        px, py = -uy, ux
        wb, wt = 46 * lk.width + lk.belly * 18, 36 * lk.width
        ext = 22
        b = (hip[0] - ux * ext, hip[1] - uy * ext)
        top = (neck[0] - ux * 4, neck[1] - uy * 4)
        mid = (lerp(b[0], top[0], 0.45), lerp(b[1], top[1], 0.45))
        wm = wb + lk.belly * 16
        pts = [
            (b[0] + px * wb, b[1] + py * wb),
            (mid[0] + px * wm, mid[1] + py * wm),
            (top[0] + px * wt, top[1] + py * wt),
            (top[0] - px * wt, top[1] - py * wt),
            (mid[0] - px * wm, mid[1] - py * wm),
            (b[0] - px * wb, b[1] - py * wb),
        ]
        def body_path():
            ctx.new_path()
            ctx.move_to(*pts[0])
            ctx.curve_to(*pts[1], *pts[1], *pts[2])
            ctx.line_to(*pts[3])
            ctx.curve_to(*pts[4], *pts[4], *pts[5])
            ctx.close_path()
        body_path()
        ctx.set_source_rgb(*hexc(lk.coat))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip_preserve()
        # shading strip on the back side
        ctx.set_source_rgba(*hexc(lk.coat_dark), 0.9)
        ctx.move_to(top[0] - px * wt * face, top[1] - py * wt * face)
        ctx.line_to(b[0] - px * wb * face, b[1] - py * wb * face)
        ctx.line_to(b[0] - px * wb * 0.35 * face, b[1] - py * wb * 0.35 * face)
        ctx.line_to(top[0] - px * wt * 0.4 * face, top[1] - py * wt * 0.4 * face)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
        body_path()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(OUTLINE)
        ctx.set_line_join(1)
        ctx.stroke()
        ux, uy = -ux, -uy  # collar/tie hang downward from the neck
        # collar / shirt V + tie
        cx = top[0] + px * 6 * face
        cy = top[1] + py * 6 * face
        ctx.move_to(cx - px * 18 - ux * 0, cy - py * 18)
        ctx.line_to(cx + ux * 42, cy + uy * 42)
        ctx.line_to(cx + px * 18, cy + py * 18)
        ctx.close_path()
        ctx.set_source_rgb(0.98, 0.98, 0.98)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3.5)
        ctx.stroke()
        if lk.tie:
            ctx.move_to(cx - px * 6, cy - py * 6)
            ctx.line_to(cx + px * 6, cy + py * 6)
            ctx.line_to(cx + ux * 46 + px * 7, cy + uy * 46 + py * 7)
            ctx.line_to(cx + ux * 54, cy + uy * 54)
            ctx.line_to(cx + ux * 46 - px * 7, cy + uy * 46 - py * 7)
            ctx.close_path()
            ctx.set_source_rgb(*hexc(lk.tie))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(3)
            ctx.stroke()
        # buttons
        for f in (0.35, 0.55, 0.75):
            bx = lerp(top[0], b[0], f) + px * 4 * face
            by = lerp(top[1], b[1], f) + py * 4 * face
            if f == 0.35 and lk.tie:
                continue
            ctx.arc(bx, by, 4, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.fill()
        if lk.badge:
            bx = lerp(top[0], b[0], 0.3) - px * 22 * face
            by = lerp(top[1], b[1], 0.3) - py * 22 * face
            _star(ctx, bx, by, 13, 6)
            ctx.set_source_rgb(*hexc("#f2c84b"))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(2.5)
            ctx.stroke()

    def _head(self, ctx, hc, P, t, face, mouth_open):
        lk = self.look
        r = HEAD_R
        ex = EXPRESSIONS.get(P["expr"], EXPRESSIONS["neutral"])
        eye_s, pupil_s, lid, (brow_a, brow_r), mouth = ex
        if P["eyes"] if "eyes" in P else False:
            pass
        ctx.save()
        ctx.translate(*hc)
        ctx.rotate(math.radians(P["tilt"] + P["lean"] * 0.3) * face)
        ctx.scale(face, 1)
        # head
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc(lk.skin))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(OUTLINE)
        ctx.stroke()
        # hair
        if lk.hair == "tuft":
            ctx.set_line_width(5)
            for a in (-14, 0, 14):
                ctx.move_to(a * 0.8, -r + 2)
                ctx.curve_to(a, -r - 20, a + 10, -r - 26, a + 18, -r - 22)
            ctx.stroke()
        elif lk.hair == "side":
            ctx.set_line_width(5)
            for a in (-60, -70, -80):
                ctx.arc(0, 0, r - 2, math.radians(a - 150), math.radians(a - 120))
                ctx.stroke()
        elif lk.hair == "curl":
            ctx.set_line_width(5)
            ctx.arc(10, -r - 8, 12, math.radians(90), math.radians(400))
            ctx.stroke()

        # blink
        blink = 0.0
        if P["blink"]:
            period = 3.1 + (self.seed % 1.0) * 1.7
            ph = (t + self.seed * 1.37) % period
            if ph < 0.13:
                blink = math.sin(ph / 0.13 * math.pi)
        lid_amt = clamp(max(lid, blink))
        # eyes
        off = 10
        pos = [(-23 + off, -8), (25 + off, -8)]
        er = 19 * eye_s
        lookx = P["look"] * 7 + 3
        looky = P["lookY"] * 6
        for i, (x, y) in enumerate(pos):
            if P["expr"] == "wink" and i == 1:
                ctx.set_line_width(5)
                ctx.set_source_rgb(*INK)
                ctx.arc(x, y + 4, er * 0.8, math.radians(200), math.radians(340))
                ctx.stroke()
                continue
            ctx.arc(x, y, er, 0, 2 * math.pi)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(4.5)
            ctx.stroke()
            if P["expr"] == "greedy":
                ctx.save()
                ctx.translate(x + lookx * 0.5, y + looky)
                ctx.rotate(t * 3)
                _star(ctx, 0, 0, 13, 5.5)
                ctx.set_source_rgb(*hexc("#f2b632"))
                ctx.fill_preserve()
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(2)
                ctx.stroke()
                ctx.restore()
            else:
                ctx.arc(x + lookx, y + looky, 8 * pupil_s, 0, 2 * math.pi)
                ctx.set_source_rgb(*INK)
                ctx.fill()
                ctx.arc(x + lookx + 2.5, y + looky - 3, 2.4 * pupil_s, 0, 2 * math.pi)
                ctx.set_source_rgb(1, 1, 1)
                ctx.fill()
            if lid_amt > 0.01:
                ctx.save()
                ctx.arc(x, y, er + 1, 0, 2 * math.pi)
                ctx.clip()
                ctx.rectangle(x - er - 2, y - er - 2, 2 * er + 4, (2 * er + 4) * lid_amt)
                ctx.set_source_rgb(*hexc(lk.skin))
                ctx.fill()
                ctx.restore()
                if lid_amt > 0.05:
                    ly = y - er + 2 * er * lid_amt
                    half = math.sqrt(max(0.0, er * er - (ly - y) ** 2))
                    ctx.move_to(x - half, ly)
                    ctx.line_to(x + half, ly)
                    ctx.set_source_rgb(*INK)
                    ctx.set_line_width(4.5)
                    ctx.stroke()
        if lk.glasses:
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(5)
            for (x, y) in pos:
                ctx.arc(x, y, er + 7, 0, 2 * math.pi)
                ctx.stroke()
            ctx.move_to(pos[0][0] + er + 7, -10)
            ctx.line_to(pos[1][0] - er - 7, -10)
            ctx.stroke()
        if lk.monocle:
            x, y = pos[1]
            ctx.arc(x, y, er + 6, 0, 2 * math.pi)
            ctx.set_source_rgb(*hexc("#d9a628"))
            ctx.set_line_width(5)
            ctx.stroke()
            ctx.move_to(x + er + 4, y + 8)
            ctx.curve_to(x + er + 18, y + 50, x + 10, y + 70, x - 6, y + 92)
            ctx.set_line_width(2.5)
            ctx.stroke()
        # brows
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5.5)
        for i, (x, y) in enumerate(pos):
            by = y - er - 10 - brow_r
            sign = 1 if i == 0 else -1  # inner end is toward the middle
            a = math.radians(brow_a) * sign
            dx, dy = math.cos(a) * 14, math.sin(a) * 14
            ctx.move_to(x - dx, by - dy)
            ctx.line_to(x + dx, by + dy)
            ctx.stroke()
        # blush
        b = max(P["blush"], 1.0 if P["expr"] == "embarrassed" else 0.0)
        if b > 0:
            for x in (-36 + off, 44 + off):
                ctx.save()
                ctx.translate(x, 22)
                ctx.scale(1, 0.55)
                ctx.arc(0, 0, 15, 0, 2 * math.pi)
                ctx.restore()
                ctx.set_source_rgba(*hexc("#ff6f7d"), 0.55 * b)
                ctx.fill()
        # mouth
        mx, my = 6 + off * 0.6, 38
        m = mouth_open if P["mouth"] is None else P["mouth"]
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        if m > 0.06 or mouth == "o":
            h = 6 + 24 * clamp(m) if mouth != "o" else 13 + 8 * clamp(m)
            w = 17 if mouth != "o" else 12
            ctx.save()
            ctx.translate(mx, my)
            ctx.scale(w, h)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(*hexc("#5a1e24"))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(4.5)
            ctx.stroke()
            if h > 14:
                ctx.save()
                ctx.translate(mx, my + h * 0.5)
                ctx.scale(10, 5)
                ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
                ctx.restore()
                ctx.set_source_rgb(*hexc("#e2626f"))
                ctx.fill()
        elif mouth == "smile":
            ctx.arc(mx, my - 12, 18, math.radians(25), math.radians(155))
            ctx.stroke()
        elif mouth == "soft":
            ctx.arc(mx, my - 20, 16, math.radians(55), math.radians(125))
            ctx.stroke()
        elif mouth == "grin":
            ctx.move_to(mx - 22, my - 6)
            ctx.curve_to(mx - 14, my + 22, mx + 14, my + 22, mx + 22, my - 6)
            ctx.close_path()
            ctx.set_source_rgb(*hexc("#5a1e24"))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.stroke()
            ctx.rectangle(mx - 15, my - 5, 30, 6)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        elif mouth == "smirk":
            ctx.move_to(mx - 14, my + 2)
            ctx.curve_to(mx - 2, my + 8, mx + 12, my + 4, mx + 20, my - 8)
            ctx.stroke()
        elif mouth == "frown":
            ctx.arc(mx, my + 20, 16, math.radians(215), math.radians(325))
            ctx.stroke()
        elif mouth == "wobble":
            ctx.move_to(mx - 16, my + 4)
            for i in range(1, 5):
                ctx.line_to(mx - 16 + i * 8, my + (-4 if i % 2 else 4))
            ctx.stroke()
        else:  # flat
            ctx.move_to(mx - 13, my)
            ctx.line_to(mx + 13, my)
            ctx.stroke()
        # mustache (drawn over the mouth area)
        if lk.mustache == "curly":
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(5)
            for sgn in (-1, 1):
                ctx.move_to(mx, my - 17)
                ctx.curve_to(mx + sgn * 12, my - 24, mx + sgn * 22, my - 14, mx + sgn * 27, my - 26)
                ctx.stroke()
                ctx.arc(mx + sgn * 24, my - 28, 3.5, 0, 2 * math.pi)
                ctx.stroke()
        elif lk.mustache == "thick":
            ctx.save()
            ctx.translate(mx, my - 14)
            ctx.scale(30, 9)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(*hexc("#5b3a26"))
            ctx.fill()
        # sweat
        if P["sweat"] > 0:
            yy = -30 + (t * 60) % 40
            ctx.move_to(-r + 4, yy - 16)
            ctx.curve_to(-r - 10, yy + 4, -r + 18, yy + 4, -r + 4, yy - 16)
            ctx.set_source_rgba(*hexc("#7fc8ff"), P["sweat"])
            ctx.fill_preserve()
            ctx.set_source_rgba(*INK, P["sweat"])
            ctx.set_line_width(2.5)
            ctx.stroke()
        # hat
        if lk.hat:
            ho = P["hat_off"]
            ctx.save()
            ctx.translate(0, -ho * 70)
            ctx.rotate(math.radians(-ho * 18))
            _hat(ctx, lk, r)
            ctx.restore()
        ctx.restore()


def _star(ctx, x, y, R, r, n=5):
    for i in range(2 * n):
        rad = R if i % 2 == 0 else r
        a = -math.pi / 2 + i * math.pi / n
        px, py = x + math.cos(a) * rad, y + math.sin(a) * rad
        if i == 0:
            ctx.move_to(px, py)
        else:
            ctx.line_to(px, py)
    ctx.close_path()


def _hat(ctx, lk, r):
    c = hexc(lk.hat_color)
    ctx.set_line_width(5)
    ctx.set_line_join(1)
    if lk.hat == "tophat":
        ctx.save()
        ctx.rotate(math.radians(-6))
        top, base = -r - 108, -r * 0.62
        ctx.rectangle(-46, top, 92, base - top)
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-46, base - 30, 92, 18)
        ctx.set_source_rgb(*hexc(lk.hat_band))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.save()
        ctx.translate(0, base)
        ctx.scale(88, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.restore()
    elif lk.hat == "bowler":
        ctx.arc(0, -r * 0.55, 58, math.pi, 2 * math.pi)
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.save()
        ctx.translate(0, -r * 0.55)
        ctx.scale(80, 12)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
    elif lk.hat == "flatcap":
        ctx.move_to(-r * 0.95, -r * 0.35)
        ctx.curve_to(-r * 0.9, -r * 1.25, r * 0.7, -r * 1.3, r * 0.95, -r * 0.5)
        ctx.curve_to(r * 1.35, -r * 0.45, r * 1.45, -r * 0.3, r * 1.2, -r * 0.22)
        ctx.line_to(-r * 0.95, -r * 0.35)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
    elif lk.hat == "kepi":
        ctx.move_to(-r * 0.7, -r * 0.55)
        ctx.line_to(-r * 0.62, -r * 1.45)
        ctx.line_to(r * 0.62, -r * 1.45)
        ctx.line_to(r * 0.7, -r * 0.55)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-r * 0.62, -r * 1.45, r * 1.24, 18)
        ctx.set_source_rgb(*hexc(lk.hat_band))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.move_to(r * 0.2, -r * 0.6)
        ctx.curve_to(r * 0.8, -r * 0.65, r * 1.2, -r * 0.5, r * 1.15, -r * 0.42)
        ctx.line_to(r * 0.2, -r * 0.5)
        ctx.close_path()
        ctx.set_source_rgb(*INK)
        ctx.fill()


# ---------------------------------------------------------------- props
def draw_prop(ctx, name, hand, face, angle, t):
    x, y = hand
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(face, 1)
    ctx.rotate(math.radians(angle))
    ctx.set_line_join(1)
    ctx.set_line_width(4.5)
    if name in ("paper", "contract"):
        ctx.rotate(math.radians(-12))
        ctx.rectangle(-8, -88, 66, 90)
        ctx.set_source_rgb(0.99, 0.98, 0.94)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.set_line_width(3)
        for i in range(5):
            ctx.move_to(2, -74 + i * 13)
            ctx.line_to(48 - (i % 2) * 12, -74 + i * 13)
        ctx.stroke()
        if name == "contract":
            ctx.arc(40, -12, 9, 0, 2 * math.pi)
            ctx.set_source_rgb(*hexc("#c8313a"))
            ctx.fill()
    elif name == "newspaper":
        ctx.rectangle(-20, -120, 150, 110)
        ctx.set_source_rgb(*hexc("#ebe6d8"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-8, -108, 126, 20)
        ctx.fill()
        ctx.set_line_width(3)
        for i in range(4):
            ctx.move_to(-8, -76 + i * 15)
            ctx.line_to(55, -76 + i * 15)
            ctx.move_to(64, -76 + i * 15)
            ctx.line_to(118, -76 + i * 15)
        ctx.stroke()
    elif name == "moneybag":
        ctx.translate(0, 40)
        ctx.move_to(-14, -38)
        ctx.curve_to(-60, -20, -58, 46, 0, 46)
        ctx.curve_to(58, 46, 60, -20, 14, -38)
        ctx.close_path()
        ctx.set_source_rgb(*hexc("#c9a46a"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.move_to(-16, -38)
        ctx.line_to(-24, -54)
        ctx.line_to(24, -54)
        ctx.line_to(16, -38)
        ctx.close_path()
        ctx.set_source_rgb(*hexc("#c9a46a"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.scale(face, 1)  # keep lettering readable when mirrored
        _text_center(ctx, "F", 0, 18, 44, "#3c6d2f")
    elif name == "stamp":
        ctx.rectangle(-12, -70, 24, 50)
        ctx.set_source_rgb(*hexc("#8a5a35"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-30, -20, 60, 22)
        ctx.set_source_rgb(*hexc("#c8313a"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
    elif name == "whistle":
        ctx.rectangle(-4, -14, 34, 16)
        ctx.set_source_rgb(*hexc("#c0c4cc"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
    elif name == "magnifier":
        ctx.move_to(0, 0)
        ctx.line_to(0, -50)
        ctx.set_line_width(9)
        ctx.stroke()
        ctx.arc(0, -78, 28, 0, 2 * math.pi)
        ctx.set_source_rgba(0.8, 0.95, 1, 0.5)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6)
        ctx.stroke()
    ctx.restore()


def _text_center(ctx, txt, x, y, size, color, font="Inter Display Black"):
    ctx.select_font_face(font, 0, 1)
    ctx.set_font_size(size)
    ext = ctx.text_extents(txt)
    ctx.move_to(x - ext.width / 2 - ext.x_bearing, y - ext.height / 2 - ext.y_bearing)
    ctx.set_source_rgb(*hexc(color))
    ctx.show_text(txt)
