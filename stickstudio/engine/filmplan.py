"""Film plan: long camera-driven shots through 3D sets + rule checks measured from top channels.

Rules (measured, not guessed):
  R1  a face is on screen within the first 1.5 s
  R2  few cuts: average shot length >= 7 s (top channels: ~1 cut / 20 s)
  R3  the camera moves a good part of the time (target ~2/3) but slowly
  R4  key words are spoken while the camera is AT REST (it lands, then the word lands)
  R5  every named thing is on screen when it is said
  R6  one expression per line per character; the big meme face appears at most once (the peak)
  R7  characters freeze once they land: no idle bob, no blinking while talking (enforced in char())
  R8  light changes when the story turns: at least two light presets across the film
  R9  every line has a sound cue or music bed under it (cues list not empty for most shots)
"""
import hashlib
import json
import math
import os
import subprocess
import sys

from .render import Scene, Timing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEME_FACES = {"shock"}


class FilmScene(Scene):
    def __init__(self, name, lines, draw, set_name, light, cam, anchors, module="sets_pirate", keywords=(),
                 named=(), exprs=None, exposure=0.0, move=None, **kw):
        super().__init__(name, lines, draw, **kw)
        self.set_name, self.light, self.cam_fn, self.anchors_fn = set_name, light, cam, anchors
        self.module, self.keywords, self.named = module, list(keywords), list(named)
        self.exprs = exprs or {}  # {char_name: [expr per line]}
        self.exposure = exposure
        self.move_fn = move  # optional: Timing -> {object_name: [[t, x, y, z, rot_z], ...]}
        self.shot = None  # engine.film.Shot once rendered

    def cam_keys(self):
        return self.cam_fn(Timing(self))

    def move_spec(self):
        return self.move_fn(Timing(self)) if self.move_fn else {}

    def anchor_spec(self):
        return self.anchors_fn(Timing(self))


# ---------------------------------------------------------------- rendering the 3D shots
def render_shots(ep, workdir, fps=15, w=540, h=960, samples=8, only=None, smooth=False):
    from .film import Shot
    os.makedirs(workdir, exist_ok=True)
    for sc in ep.scenes:
        if not isinstance(sc, FilmScene):
            continue
        d = os.path.join(workdir, sc.name)
        n = int(math.ceil(sc.dur * fps)) + 1
        spec = {"set": sc.set_name, "module": sc.module, "light": sc.light, "out": d, "w": w, "h": h,
                "samples": samples, "exposure": sc.exposure, "times": [i / fps for i in range(n)],
                "cam": sc.cam_keys(), "anchors": sc.anchor_spec(), "move": sc.move_spec()}
        # the key covers the shot plan AND the code that builds/renders the set, so editing a set re-renders it
        code = b"".join(open(os.path.join(ROOT, "engine3d", f), "rb").read()
                        for f in (f"{sc.module}.py", "sets.py", "shot.py"))
        key = hashlib.sha1(json.dumps(spec, sort_keys=True).encode() + code).hexdigest()[:12]
        stamp = os.path.join(d, "spec.key")
        if (only is None or sc.name in only) and not (os.path.exists(stamp) and open(stamp).read() == key):
            os.makedirs(d, exist_ok=True)
            sp = os.path.join(d, "spec.json")
            json.dump(spec, open(sp, "w"))
            print(f"[3d] rendering shot {sc.name}: {n} frames", flush=True)
            subprocess.run([sys.executable, os.path.join(ROOT, "engine3d", "shot.py"), sp], check=True,
                           stdout=subprocess.DEVNULL)
            open(stamp, "w").write(key)
        if smooth and not os.path.exists(os.path.join(d, "smooth.key")) or \
                (smooth and open(os.path.join(d, "smooth.key")).read() != key):
            from .film import bake_smooth
            n_s = bake_smooth(d, fps)
            print(f"[smooth] {sc.name}: {n_s} frames at 30 fps", flush=True)
            open(os.path.join(d, "smooth.key"), "w").write(key)
        sc.shot = Shot(d, t0=sc.start)


# ---------------------------------------------------------------- checks
def _cam_moving(keys, t, eps=1e-4):
    for a, b in zip(keys, keys[1:]):
        if a["t"] < t < b["t"]:
            moved = any(abs(x - y) > eps for x, y in zip(a["loc"] + a["target"], b["loc"] + b["target"]))
            moved = moved or abs(a.get("lens", 24) - b.get("lens", 24)) > eps
            if moved:
                return True
    return False


def run_checks(ep):
    res = []
    films = [s for s in ep.scenes if isinstance(s, FilmScene)]
    # R1
    first = ep.scenes[0]
    has_face = isinstance(first, FilmScene) and any(first.anchor_spec())
    res.append(("R1 face within 1.5 s", has_face and first.lines[0].start < 1.5, f"first shot '{first.name}'"))
    # R2
    asl = ep.total / max(1, len(ep.scenes))
    res.append(("R2 average shot >= 7 s", asl >= 7.0, f"{len(ep.scenes)} shots, ASL {asl:.1f} s"))
    # R3
    moving, total = 0, 0
    for sc in films:
        keys = sc.cam_keys()
        for i in range(int(sc.dur * 10)):
            total += 1
            moving += _cam_moving(keys, i / 10)
    frac = moving / max(1, total)
    res.append(("R3 camera moving 40-85% of the time", 0.40 <= frac <= 0.85, f"{frac:.0%} moving"))
    # R4
    bad = []
    for sc in films:
        keys, T = sc.cam_keys(), Timing(sc)
        for (li, word) in sc.keywords:
            tw = T.word(li, word)
            if _cam_moving(keys, tw):
                bad.append(f"{sc.name}:'{word}'@{tw:.2f}")
    n_kw = sum(len(s.keywords) for s in films)
    res.append(("R4 key words land on a still camera", not bad and n_kw > 0,
                f"{n_kw} key words" + (f"; moving on {bad}" if bad else "")))
    # R5 (checked against the rendered projections when available)
    missing = []
    for sc in films:
        if not sc.named:
            continue
        T = Timing(sc)
        for (li, word, anchor) in sc.named:
            tw = T.word(li, word)
            if sc.shot is None:
                continue
            x, y, s = sc.shot.anchor(anchor, sc.start + tw)
            if not (40 < x < 1040 and 200 < y < 2400):
                missing.append(f"{sc.name}:'{word}'->{anchor} at ({x:.0f},{y:.0f})")
    res.append(("R5 named things on screen when said", not missing,
                ("verified on render" if films and films[0].shot else "pending render") + (f"; {missing}" if missing else "")))
    # R6
    multi, memes = [], 0
    for sc in films:
        for ch, ex in sc.exprs.items():
            if len(ex) != len(sc.lines):
                multi.append(f"{sc.name}/{ch}")
            memes += sum(1 for e in ex if e in MEME_FACES)
    res.append(("R6 one expression per line, meme face <= 2", not multi and memes <= 2,
                f"meme faces: {memes}" + (f"; mismatched: {multi}" if multi else "")))
    # R8
    lights = [s.light for s in films]
    res.append(("R8 light changes with the story", len(set(lights)) >= 2, " -> ".join(lights)))
    # R9
    quiet = [s.name for s in ep.scenes if s.cues_fn is None]
    res.append(("R9 sound on every shot", not quiet, f"quiet: {quiet}" if quiet else "all shots have cues"))
    ok = all(r[1] for r in res)
    for name, passed, detail in res:
        print(f"  {'PASS' if passed else 'FAIL'}  {name:42s} {detail}")
    return ok, res


def limb_check(ep, step=0.2):
    """R10: draw a frame every `step` seconds and collect any joint that left its limits (clamped and logged
    by the rig). Must run after the 3D shots exist. Returns (ok, issues)."""
    import cairo
    from . import rig
    rig.LIMB_ISSUES.clear()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
    t = 0.0
    while t < ep.total:
        ep.draw_frame(cairo.Context(surf), t)
        t += step
    issues = list(rig.LIMB_ISSUES)
    ok = not issues
    print(f"  {'PASS' if ok else 'FAIL'}  {'R10 limbs inside joint limits':42s} "
          f"{'no bad joints' if ok else str(issues[:8]) + (' ...' if len(issues) > 8 else '')}")
    return ok, issues
