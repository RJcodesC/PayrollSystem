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
    "rage":     (1.0, 0.8, 0.3, (26, -8), "frown"),
}

DEFAULT_POSE = dict(
    x=540.0, y=1560.0, s=1.0, face=1, lean=0.0, tilt=0.0, bob=0.0, jump=0.0,
    # back arm / front arm (shoulder, elbow); back leg / front leg (hip, knee)
    ba=-10.0, bb=12.0, fa=10.0, fb=12.0,
    bl=-5.0, bk=4.0, fl=5.0, fk=4.0,
    expr="neutral", look=0.0, lookY=0.0, walk=0.0, run=0.0, alpha=1.0,
    hold=None, hold_back=None, blush=0.0, sweat=0.0, mouth=None, hat_off=0.0,
    idle=1.0, blink=1.0, squash=0.0, prop_angle=0.0, patch=0.0,
    # IK targets: None, a named spot ("chin", "hip", "face", "head_top", "chest"), (fwd, up) in rig units
    # from the ground point, or {"world": (X, Y)} in screen pixels. Elbows/knees always bend the natural way.
    hand_f_at=None, hand_b_at=None, foot_f_at=None, foot_b_at=None,
    crouch=0.0,
)

# joint limits (degrees). Anything outside is clamped and logged in LIMB_ISSUES (checked before render).
LIMITS = {"shoulder": (-80.0, 215.0), "elbow": (0.0, 158.0), "hip": (-75.0, 115.0), "knee": (0.0, 150.0)}
LIMB_ISSUES = []


def _clampj(name, joint, val, t, log=True):
    lo, hi = LIMITS[joint]
    if val < lo - 1.5 or val > hi + 1.5:
        if log:
            LIMB_ISSUES.append((name, round(t, 2), joint, round(val, 1)))
        return min(hi, max(lo, val))
    return val


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
    patch: bool = False      # pirate eye patch (pose param "patch": 0 = front eye covered ... 1 = back eye)
    beard: str = None        # hex colour for a full beard
    outfit: str = None       # ricks style: None | "vest" | "stripes" | "labcoat" | "coat"
    vest: str = "#3a2a20"    # vest / coat-panel colour
    stripe: str = "#f4f1e8"  # stripe colour for "stripes"
    belt: str = None         # belt colour (gold buckle)
    sash: str = None         # diagonal sash colour
    sleeve: str = None       # short-sleeve colour on the upper arms
    boots: str = None        # boot colour (lower legs)
    stubble: bool = False
    style: str = "classic"   # "ricks": white head, solid black oval eyes, thin limbs, nub hands, capsule torso


def _v(angle_deg, face):
    a = math.radians(angle_deg)
    return math.sin(a) * face, math.cos(a)


class Character:
    def __init__(self, name, look: Look, seed=0.0):
        self.name = name
        self.look = look
        self.seed = seed

    # ------------------------------------------------------------------ helpers
    def _limb(self, ctx, p0, a1, l1, a2, l2, face, width, dress=None):
        if self.look.style == "ricks" and width == LIMB_W:
            width = 6.5
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
        if dress == "sleeve" and self.look.sleeve:  # short sleeve over the upper arm
            q = (p0[0] + (p1[0] - p0[0]) * 0.42, p0[1] + (p1[1] - p0[1]) * 0.42)
            for col, w in ((INK, 25), (hexc(self.look.sleeve), 18)):
                ctx.set_source_rgb(*col)
                ctx.set_line_width(w)
                ctx.move_to(*p0)
                ctx.line_to(*q)
                ctx.stroke()
        if dress == "boot" and self.look.boots:  # boot over the lower half of the shin
            q = (p1[0] + (p2[0] - p1[0]) * 0.45, p1[1] + (p2[1] - p1[1]) * 0.45)
            for col, w in ((INK, 24), (hexc(self.look.boots), 17)):
                ctx.set_source_rgb(*col)
                ctx.set_line_width(w)
                ctx.move_to(*q)
                ctx.line_to(*p2)
                ctx.stroke()
        return p1, p2

    def _hand(self, ctx, p, r=12):
        if self.look.style == "ricks":
            ctx.arc(p[0], p[1], 8.5, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.fill()
            return
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
        ctx.arc(face * 11, 0, 18 if self.look.style == "ricks" else 25, 0, 2 * math.pi)
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

    @staticmethod
    def _ik(root, target, l1, l2, face, bend):
        """Two-bone IK. bend=+1: arm (forearm swings forward), -1: leg (knee forward, shin back).
        Returns (a1, a2) absolute limb angles in this rig's convention."""
        fx, dy = (target[0] - root[0]) * face, target[1] - root[1]
        D = max(abs(l1 - l2) + 1.0, min(l1 + l2 - 0.5, math.hypot(fx, dy)))
        th = math.degrees(math.atan2(fx, dy))
        al = math.degrees(math.acos(max(-1.0, min(1.0, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D)))))
        a1 = th - bend * al
        if a1 < -100:  # straight up can be written as -180 or +180: keep arms/legs in one continuous range
            a1 += 360
        ex = root[0] + math.sin(math.radians(a1)) * face * l1
        ey = root[1] + math.cos(math.radians(a1)) * l1
        a2 = math.degrees(math.atan2((target[0] - ex) * face, target[1] - ey))
        while a2 - a1 > 180:
            a2 -= 360
        while a2 - a1 < -180:
            a2 += 360
        return a1, a2

    def _target(self, spec, P, face, hip, neck, hc):
        """Resolve an IK target spec to local (unscaled, unflipped) coordinates."""
        if spec is None:
            return None
        if isinstance(spec, dict) and "world" in spec:
            X, Y = spec["world"]
            return ((X - P["x"]) / P["s"], (Y - (P["y"] - P["jump"])) / P["s"])
        r = HEAD_R
        named = {"chin": (hc[0] + face * r * 0.35, hc[1] + r * 0.95),
                 "face": (hc[0] + face * r * 1.05, hc[1] + r * 0.2),
                 "head_top": (hc[0] + face * r * 0.2, hc[1] - r * 1.05),
                 "hip": (hip[0] + face * 30, hip[1] + 4),
                 "chest": (neck[0] + face * 40, neck[1] + 40)}
        if isinstance(spec, str):
            return named[spec]
        fwd, up = spec
        return (fwd * face, -up)

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
        hip = (0.0, -legs + 6 + P["bob"] + P["crouch"] * legs * 0.42)
        if P["crouch"] > 0 and P["foot_f_at"] is None and P["foot_b_at"] is None:
            P["foot_f_at"], P["foot_b_at"] = (30, 0), (-22, 0)  # keep both feet planted
        lean = P["lean"]
        tdx, tdy = math.sin(math.radians(lean)) * face, -math.cos(math.radians(lean))
        tl = TORSO * lk.height
        neck = (hip[0] + tdx * tl, hip[1] + tdy * tl)
        shoulder = (hip[0] + tdx * (tl - 18), hip[1] + tdy * (tl - 18))

        # legs
        hc0 = (neck[0] + tdx * (HEAD_R - 4), neck[1] + tdy * (HEAD_R - 4))
        for side in ("b", "f"):
            tg = self._target(P[f"foot_{side}_at"], P, face, hip, neck, hc0)
            if tg is not None:
                a1, a2 = self._ik(hip, tg, THIGH * lk.height, SHIN * lk.height, face, -1)
                P[f"{side}l"], P[f"{side}k"] = a1, a1 - a2
            tg = self._target(P[f"hand_{side}_at"], P, face, hip, neck, hc0)
            if tg is not None:
                a1, a2 = self._ik(shoulder, tg, UPPER_ARM, FOREARM, face, 1)
                P[f"{side}a"], P[f"{side}b"] = a1, a2 - a1
        for side in ("b", "f"):
            P[f"{side}a"] = _clampj(self.name, "shoulder", P[f"{side}a"], t)
            P[f"{side}b"] = _clampj(self.name, "elbow", P[f"{side}b"], t)
            P[f"{side}l"] = _clampj(self.name, "hip", P[f"{side}l"], t)
            P[f"{side}k"] = _clampj(self.name, "knee", P[f"{side}k"], t)

        for (a, k) in ((P["bl"], P["bk"]), (P["fl"], P["fk"])):
            knee, foot = self._limb(ctx, hip, a, THIGH * lk.height, a - k, SHIN * lk.height, face, LIMB_W, "boot")
            self._shoe(ctx, foot, face, a - k)

        # back arm (+ prop)
        elbow_b, hand_b = self._limb(ctx, shoulder, P["ba"], UPPER_ARM, P["ba"] + P["bb"], FOREARM, face, LIMB_W,
                                     "sleeve")
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
        elbow_f, hand_f = self._limb(ctx, shoulder, P["fa"], UPPER_ARM, P["fa"] + P["fb"], FOREARM, face, LIMB_W,
                                     "sleeve")
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
        if lk.style == "ricks":
            return self._torso_capsule(ctx, hip, neck, face)
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

    def _torso_capsule(self, ctx, hip, neck, face):
        """Bean/capsule body in flat clothing colour with a bold outline."""
        lk = self.look
        ax = (neck[0] - hip[0], neck[1] - hip[1])
        L = math.hypot(*ax)
        ux, uy = ax[0] / L, ax[1] / L
        w = 40 * lk.width + lk.belly * 14
        a = (hip[0] - ux * 8, hip[1] - uy * 8)
        b = (neck[0] - ux * (w - 4), neck[1] - uy * (w - 4))
        ctx.set_line_cap(1)
        for col, lw in ((INK, 2 * w + 13), (hexc(lk.coat), 2 * w)):
            ctx.set_source_rgb(*col)
            ctx.set_line_width(lw)
            ctx.move_to(*a)
            ctx.line_to(*b)
            ctx.stroke()
        # soft shading on the back half
        ctx.save()
        ctx.set_source_rgba(*hexc(lk.coat_dark), 0.55)
        ctx.set_line_width(w * 0.7)
        px, py = -uy * face, ux * face
        ctx.move_to(a[0] - px * w * 0.55, a[1] - py * w * 0.55)
        ctx.line_to(b[0] - px * w * 0.55, b[1] - py * w * 0.55)
        ctx.stroke()
        ctx.restore()
        dn = (-ux, -uy)
        top = (neck[0] - ux * 6, neck[1] - uy * 6)
        qx, qy = -uy, ux  # across the body
        def seg(p0, p1, col, lw, cap=1):
            ctx.set_line_cap(cap)
            ctx.set_source_rgb(*col)
            ctx.set_line_width(lw)
            ctx.move_to(*p0)
            ctx.line_to(*p1)
            ctx.stroke()
        def along(f, off=0.0):  # point f of the way from hip-end (0) to neck-end (1), offset across
            return (a[0] + (b[0] - a[0]) * f + qx * off, a[1] + (b[1] - a[1]) * f + qy * off)
        if lk.outfit == "stripes":
            for k in range(5):
                f = 0.08 + k * 0.2
                hw = w - 4
                seg(along(f, -hw), along(f, hw), hexc(lk.stripe), 11, 0)
        if lk.outfit in ("vest", "coat", "labcoat"):
            col = hexc("#f4f4f0") if lk.outfit == "labcoat" else hexc(lk.vest)
            for side in (-1, 1):
                seg(along(-0.15, side * w * 0.58), along(1.0, side * w * 0.58), INK, w * 0.84 + 7)
                seg(along(-0.15, side * w * 0.58), along(1.0, side * w * 0.58), col, w * 0.84)
            # lapels
            for side in (-1, 1):
                ctx.move_to(*along(1.02, side * w * 0.12))
                ctx.line_to(*along(0.55, side * w * 0.05))
                ctx.line_to(*along(0.9, side * w * 0.62))
                ctx.close_path()
                ctx.set_source_rgb(*col)
                ctx.fill_preserve()
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(3.5)
                ctx.stroke()
            if lk.outfit == "labcoat":  # breast pocket with pens
                px0, py0 = along(0.62, -w * 0.58)
                ctx.rectangle(px0 - 13, py0 - 10, 26, 22)
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(3)
                ctx.stroke()
                for dx, pc in ((-6, "#2f6fe0"), (4, "#d63c46")):
                    seg((px0 + dx, py0 - 10), (px0 + dx, py0 - 22), hexc(pc), 4)
        if lk.sash:
            seg(along(0.95, -w * 0.9), along(0.15, w * 0.9), INK, 24)
            seg(along(0.95, -w * 0.9), along(0.15, w * 0.9), hexc(lk.sash), 17)
        if lk.belt:
            seg(along(0.1, -w - 1), along(0.1, w + 1), INK, 20, 0)
            seg(along(0.1, -w + 3), along(0.1, w - 3), hexc(lk.belt), 13, 0)
            bx, by = along(0.1, 0)
            ctx.rectangle(bx - 10, by - 9, 20, 18)
            ctx.set_source_rgb(*hexc("#e6c04a"))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(3)
            ctx.stroke()
        # light from the upper front: a soft highlight strip on the lit side
        ctx.save()
        ctx.set_source_rgba(1, 1, 1, 0.16)
        ctx.set_line_width(w * 0.35)
        ctx.move_to(*along(0.1, w * 0.45 * face))
        ctx.line_to(*along(0.95, w * 0.45 * face))
        ctx.stroke()
        ctx.restore()
        if lk.tie:
            px, py = -uy, ux
            ctx.move_to(top[0] - px * 7, top[1] - py * 7)
            ctx.line_to(top[0] + px * 7, top[1] + py * 7)
            ctx.line_to(top[0] + dn[0] * 52 + px * 8, top[1] + dn[1] * 52 + py * 8)
            ctx.line_to(top[0] + dn[0] * 62, top[1] + dn[1] * 62)
            ctx.line_to(top[0] + dn[0] * 52 - px * 8, top[1] + dn[1] * 52 - py * 8)
            ctx.close_path()
            ctx.set_source_rgb(*hexc(lk.tie))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(3.5)
            ctx.stroke()
        for f in (0.45, 0.7):
            bx, by = lerp(a[0], b[0], 1 - f), lerp(a[1], b[1], 1 - f)
            ctx.arc(bx, by, 4.5, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.fill()
        if lk.badge:
            bx, by = lerp(a[0], b[0], 0.75), lerp(a[1], b[1], 0.75)
            _star(ctx, bx - 18 * face, by, 12, 5.5)
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
        ricks = lk.style == "ricks"
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        rage = P["expr"] == "rage"
        ctx.set_source_rgb(*(hexc("#c0396b") if rage else (1, 1, 1) if ricks else hexc(lk.skin)))
        ctx.fill_preserve()
        if ricks:  # cel shade on the side away from the light, so the head sits in the 3D world
            ctx.save()
            ctx.clip()
            ctx.arc(r * 0.35, r * 0.25, r * 1.05, 0, 2 * math.pi)
            ctx.arc_negative(r * 0.55, r * 0.05, r * 0.95, 2 * math.pi, 0)
            ctx.set_source_rgba(0.35, 0.42, 0.62, 0.0)
            ctx.restore()
            ctx.save()
            ctx.arc(0, 0, r, 0, 2 * math.pi)
            ctx.clip()
            ctx.arc(-r * 0.55, r * 0.15, r * 0.9, 0, 2 * math.pi)
            ctx.set_source_rgba(0.38, 0.45, 0.66, 0.16)
            ctx.fill()
            ctx.restore()
            ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(7.5 if ricks else OUTLINE)
        ctx.stroke()
        if rage:  # meme rage: steam puffs from the head
            for k, sx in enumerate((-1, 1)):
                ph = (t * 2 + k * 0.5) % 1
                ctx.arc(sx * (r + 10 + 30 * ph), -r * 0.3 - 40 * ph, 10 + 18 * ph, 0, 2 * math.pi)
                ctx.set_source_rgba(1, 1, 1, 0.9 * (1 - ph))
                ctx.fill()
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
        elif lk.hair == "spiky":
            ctx.move_to(-r * 0.8, -r * 0.55)
            for i in range(6):
                ax_ = -r * 0.8 + i * r * 0.32
                ctx.line_to(ax_ + r * 0.16, -r * 1.22 - (i % 2) * 10)
                ctx.line_to(ax_ + r * 0.32, -r * 0.7)
            ctx.close_path()
            ctx.set_source_rgb(*INK)
            ctx.fill()
        elif lk.hair == "messy":
            ctx.set_source_rgb(*INK)
            ctx.arc(0, -r * 0.15, r * 1.02, math.radians(195), math.radians(345))
            ctx.arc_negative(0, -r * 0.05, r * 0.86, math.radians(330), math.radians(210))
            ctx.close_path()
            ctx.fill()
            for i in range(4):
                ctx.arc(-r * 0.6 + i * r * 0.4, -r * 0.85, r * 0.2, 0, 2 * math.pi)
                ctx.fill()
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
        dot_eyes = ricks and P["expr"] not in ("shock", "excited", "greedy", "worried")
        for i, (x, y) in enumerate(pos if dot_eyes else []):
            ex, ey = x + lookx * 0.9, y + 4 + looky
            if P["expr"] in ("smile", "grin", "wink") or (P["expr"] == "wink" and i == 1):
                ctx.arc(ex, ey + 6, 11, math.radians(200), math.radians(340))  # happy crescent
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(6)
                ctx.stroke()
                continue
            open_h = 15 * eye_s * (1 - clamp(max(lid, blink)))
            ctx.save()
            ctx.translate(ex, ey)
            if open_h < 2.5:
                ctx.move_to(-9, 0)
                ctx.line_to(9, 0)
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(5)
                ctx.stroke()
            else:
                ctx.scale(9.5 * eye_s, open_h)
                ctx.arc(0, 0, 1, 0, 2 * math.pi)
                ctx.restore()
                ctx.save()
                ctx.set_source_rgb(*INK)
                ctx.fill()
            ctx.restore()
        for i, (x, y) in enumerate([] if dot_eyes else pos):
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
            if lid_amt > 0.01 and not dot_eyes:
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
        ctx.set_line_width(7 if ricks else 5.5)
        show_brows = not (ricks and P["expr"] in ("neutral", "smile", "grin"))
        for i, (x, y) in enumerate(pos if show_brows else []):
            by = y - er - 10 - brow_r + (8 if dot_eyes else 0)
            sign = 1 if i == 0 else -1  # inner end is toward the middle
            a = math.radians(brow_a) * sign
            dx, dy = math.cos(a) * 14, math.sin(a) * 14
            ctx.move_to(x - dx, by - dy)
            ctx.line_to(x + dx, by + dy)
            ctx.stroke()
        if lk.beard:
            ctx.move_to(-r * 0.85, 10)
            ctx.curve_to(-r * 0.8, r * 1.25, r * 0.95, r * 1.25, r * 0.95, 10)
            ctx.curve_to(r * 0.5, r * 0.55, -r * 0.4, r * 0.55, -r * 0.85, 10)
            ctx.close_path()
            ctx.set_source_rgb(*hexc(lk.beard))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(4)
            ctx.stroke()
        if lk.patch:
            v = clamp(P.get("patch", 0.0))
            px = lerp(pos[1][0], pos[0][0], v)
            py = lerp(pos[1][1], pos[0][1], v) + (4 if ricks else 0)
            lift = math.sin(math.pi * v) * 22  # the patch lifts as it moves across
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(5)
            ctx.move_to(-r * 0.98, -r * 0.42)
            ctx.line_to(px, py - lift)
            ctx.line_to(r * 0.98, -r * 0.42)
            ctx.stroke()
            ctx.save()
            ctx.translate(px, py - lift)
            ctx.scale(1, 0.9)
            ctx.arc(0, 0, 24, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()
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
            h = 6 + 24 * clamp(m) if mouth != "o" else (22 if ricks else 13) + 8 * clamp(m)
            w = 17 if mouth != "o" else (17 if ricks else 12)
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
        elif mouth == "grin" and ricks:  # wide open grin: top teeth + tongue
            ctx.move_to(mx - 28, my - 8)
            ctx.curve_to(mx - 20, my + 30, mx + 20, my + 30, mx + 28, my - 8)
            ctx.close_path()
            ctx.set_source_rgb(*hexc("#4a1620"))
            ctx.fill_preserve()
            ctx.save()
            ctx.clip_preserve()
            ctx.rectangle(mx - 30, my - 10, 60, 10)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
            ctx.arc(mx, my + 22, 13, 0, 2 * math.pi)
            ctx.set_source_rgb(*hexc("#e2626f"))
            ctx.fill()
            ctx.restore()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(5)
            ctx.stroke()
        elif mouth == "frown" and ricks and P["expr"] in ("angry", "rage"):  # gritted teeth
            ctx.rectangle(mx - 22, my - 6, 44, 18)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(4.5)
            ctx.stroke()
            ctx.move_to(mx - 22, my + 3)
            ctx.line_to(mx + 22, my + 3)
            for k in range(1, 4):
                ctx.move_to(mx - 22 + k * 11, my - 6)
                ctx.line_to(mx - 22 + k * 11, my + 12)
            ctx.set_line_width(2.5)
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
        if lk.stubble:
            ctx.set_source_rgba(*INK, 0.35)
            for k in range(9):
                ang = math.radians(50 + k * 10)
                rr = r * (0.8 + 0.06 * (k % 2))
                ctx.arc(math.cos(ang) * rr + 4, math.sin(ang) * rr, 1.6, 0, 2 * math.pi)
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
    elif lk.hat == "bandana":
        ctx.move_to(-r * 0.98, -r * 0.2)
        ctx.curve_to(-r * 0.95, -r * 1.15, r * 0.95, -r * 1.15, r * 0.98, -r * 0.2)
        ctx.curve_to(r * 0.5, -r * 0.42, -r * 0.5, -r * 0.42, -r * 0.98, -r * 0.2)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.new_path()
        for dx in (0, 1):  # white polka dots
            for k in range(3):
                ctx.new_sub_path()
                ctx.arc(-r * 0.5 + k * r * 0.45 + dx * 18, -r * 0.62 - dx * 14, 6, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        for ang in (200, 225):  # knot tails at the back
            a = math.radians(ang)
            ctx.move_to(-r * 0.9, -r * 0.35)
            ctx.line_to(-r * 0.9 + math.cos(a) * 55, -r * 0.35 - math.sin(a) * 55)
            ctx.line_to(-r * 0.9 + math.cos(a + 0.35) * 45, -r * 0.35 - math.sin(a + 0.35) * 45)
            ctx.close_path()
            ctx.set_source_rgb(*c)
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.stroke()
    elif lk.hat == "tricorn":
        ctx.move_to(-r * 1.35, -r * 0.55)
        ctx.curve_to(-r * 0.6, -r * 1.7, r * 0.6, -r * 1.7, r * 1.35, -r * 0.55)
        ctx.curve_to(r * 0.5, -r * 0.85, -r * 0.5, -r * 0.85, -r * 1.35, -r * 0.55)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*hexc(lk.hat_band))
        ctx.set_line_width(7)
        ctx.stroke_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
        # skull badge
        ctx.arc(0, -r * 1.05, 11, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
    elif lk.hat == "slouch":  # Australian slouch hat: wide brim, left side pinned up, rising-sun badge
        ctx.move_to(-r * 1.45, -r * 0.5)
        ctx.curve_to(-r * 0.6, -r * 0.62, r * 0.6, -r * 0.62, r * 1.45, -r * 0.5)
        ctx.curve_to(r * 1.5, -r * 0.4, r * 0.6, -r * 0.38, 0, -r * 0.4)
        ctx.curve_to(-r * 0.6, -r * 0.38, -r * 1.5, -r * 0.4, -r * 1.45, -r * 0.5)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.move_to(-r * 0.62, -r * 0.55)  # crown with a pinched top
        ctx.curve_to(-r * 0.7, -r * 1.3, -r * 0.25, -r * 1.42, 0, -r * 1.25)
        ctx.curve_to(r * 0.25, -r * 1.42, r * 0.7, -r * 1.3, r * 0.62, -r * 0.55)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-r * 0.64, -r * 0.78, r * 1.28, r * 0.2)  # puggaree band
        ctx.set_source_rgb(*hexc(lk.hat_band))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.move_to(-r * 0.62, -r * 0.55)  # brim pinned up at the back side
        ctx.curve_to(-r * 1.0, -r * 0.8, -r * 1.05, -r * 1.25, -r * 0.8, -r * 1.3)
        ctx.line_to(-r * 0.58, -r * 0.7)
        ctx.close_path()
        ctx.set_source_rgb(*[v * 0.85 for v in c])
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.arc(-r * 0.78, -r * 1.0, 9, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#e2b341"))
        ctx.fill()
    elif lk.hat == "peaked":  # officer's peaked cap
        ctx.move_to(-r * 0.8, -r * 0.6)
        ctx.curve_to(-r * 1.0, -r * 1.15, r * 1.0, -r * 1.25, r * 1.05, -r * 0.85)
        ctx.line_to(r * 0.8, -r * 0.6)
        ctx.close_path()
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-r * 0.8, -r * 0.78, r * 1.6, r * 0.2)
        ctx.set_source_rgb(*hexc(lk.hat_band))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.move_to(r * 0.3, -r * 0.6)  # glossy black peak
        ctx.curve_to(r * 0.8, -r * 0.62, r * 1.25, -r * 0.5, r * 1.3, -r * 0.4)
        ctx.line_to(r * 0.3, -r * 0.48)
        ctx.close_path()
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.arc(r * 0.1, -r * 0.95, 9, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#e2b341"))
        ctx.fill()
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
    elif name == "sword":
        ctx.rotate(math.radians(-60))
        ctx.move_to(0, -16)
        ctx.curve_to(60, -26, 150, -30, 200, -8)
        ctx.curve_to(150, -6, 60, 2, 0, 4)
        ctx.close_path()
        ctx.set_source_rgb(*hexc("#d7dde4"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.arc(-4, -6, 16, math.radians(90), math.radians(270))
        ctx.set_source_rgb(*hexc("#d9b44a"))
        ctx.set_line_width(7)
        ctx.stroke()
        ctx.rectangle(-30, -12, 26, 14)
        ctx.set_source_rgb(*hexc("#5a3320"))
        ctx.fill()
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
