"""Film layer: animated 3D background shots (rendered by engine3d/shot.py) + projected 2D characters.

A shot directory holds frame_XXXXX.png (+ _depth.png) at BG_FPS and proj.json with per-frame screen
projections of 3D character anchors. This module turns that into cairo backgrounds for any time t,
adds depth haze, and tells the compositor where (and how big) to draw each character."""
import json
import math
import os

import cairo
import numpy as np
from PIL import Image

W, H = 1080, 1920
RIG_HEIGHT = 520.0  # rig height in pixels at scale 1 (feet to top of head)


SMOOTH_FPS = 30
SATURATION = 1.35
CONTRAST = 0.18


def grade(img):
    """Final colour pass: boost saturation around luminance, then a soft S-curve for punch."""
    lum = (img * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    img = lum + (img - lum) * SATURATION
    img = np.clip(img, 0, 1)
    return img + CONTRAST * (img - 0.5) * (1 - np.abs(2 * img - 1))


class Shot:
    def __init__(self, directory, t0=0.0):
        self.dir = directory
        self.t0 = t0  # global time of the shot's first frame
        self.proj = json.load(open(os.path.join(directory, "proj.json")))
        self.frames = self.proj["frames"]
        self.haze = self.proj.get("haze", {"amount": 0.0, "color": (1, 1, 1)})
        self._cache = {}
        self.smooth_dir = os.path.join(directory, "smooth")
        self.smooth = sorted(f for f in os.listdir(self.smooth_dir)) if os.path.isdir(self.smooth_dir) else []
        self._scache = {}

    def _surface(self, fname):
        if fname in self._cache:
            return self._cache[fname]
        img = np.asarray(Image.open(os.path.join(self.dir, fname)).convert("RGB")).astype(np.float32) / 255
        dpath = os.path.join(self.dir, fname.replace(".png", "_depth.png"))
        if os.path.exists(dpath) and self.haze["amount"] > 0:
            d = np.asarray(Image.open(dpath).convert("RGBA")).astype(np.float32) / 255
            depth = d[..., 0] * 200.0
            depth = np.where(d[..., 3] < 0.5, 400.0, depth)  # sky = far away
            f = np.clip((depth - 6.0) / 140.0, 0, 1) ** 1.6 * self.haze["amount"]
            f = np.where(d[..., 3] < 0.5, f * 0.3, f)  # sky: only a light veil, keep it blue
            col = np.array(self.haze["color"], np.float32)
            img = img * (1 - f[..., None]) + col * f[..., None]
        img = grade(img)
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        h, w = img.shape[:2]
        rgba = np.dstack([img[..., 2], img[..., 1], img[..., 0], np.full((h, w), 255, np.uint8)])  # cairo BGRA
        surf = cairo.ImageSurface.create_for_data(bytearray(rgba.tobytes()), cairo.FORMAT_ARGB32, w, h, w * 4)
        if len(self._cache) > 6:
            self._cache.pop(next(iter(self._cache)))
        self._cache[fname] = surf
        return surf

    def _index(self, t):
        ts = [f["t"] for f in self.frames]
        lt = t - self.t0
        if lt <= ts[0]:
            return 0, 0, 0.0
        if lt >= ts[-1]:
            n = len(ts) - 1
            return n, n, 0.0
        for i in range(len(ts) - 1):
            if ts[i] <= lt <= ts[i + 1]:
                return i, i + 1, (lt - ts[i]) / (ts[i + 1] - ts[i])
        return 0, 0, 0.0

    def _smooth_surface(self, i):
        if i not in self._scache:
            if len(self._scache) > 4:
                self._scache.pop(next(iter(self._scache)))
            self._scache[i] = cairo.ImageSurface.create_from_png(os.path.join(self.smooth_dir, self.smooth[i]))
        return self._scache[i]

    def draw_bg(self, ctx, t):
        """Paint the background for global time t: smooth 30 fps frames if baked, else blend 15 fps frames."""
        if self.smooth:
            i = min(len(self.smooth) - 1, max(0, int(round((t - self.t0) * SMOOTH_FPS))))
            sf = self._smooth_surface(i)
            ctx.save()
            ctx.scale(W / sf.get_width(), H / sf.get_height())
            ctx.set_source_surface(sf, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_GOOD)
            ctx.paint()
            ctx.restore()
            return
        a, b, p = self._index(t)
        fa, fb = self.frames[a]["file"], self.frames[b]["file"]
        sa = self._surface(fa)
        ctx.save()
        ctx.scale(W / sa.get_width(), H / sa.get_height())
        ctx.set_source_surface(sa, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()
        if fb != fa and p > 0.01:
            sb = self._surface(fb)
            ctx.set_source_surface(sb, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_GOOD)
            ctx.paint_with_alpha(p)
        ctx.restore()

    def anchor(self, name, t):
        """Screen position (feet), and rig scale for a character anchored in 3D."""
        a, b, p = self._index(t)
        A, B = self.frames[a]["anchors"][name], self.frames[b]["anchors"][name]
        lerp = lambda k: A[k] + (B[k] - A[k]) * p  # noqa: E731
        x, y, hy = lerp("x") * W, lerp("y") * H, lerp("hy") * H
        scale = max(0.05, (y - hy) / RIG_HEIGHT)
        return x, y, scale


def bake_smooth(directory, src_fps=15):
    """Grade/haze every background frame once, then motion-interpolate (optical flow) to 30 fps."""
    import subprocess
    sh = Shot(directory)
    seq = os.path.join(directory, "seq")
    out = os.path.join(directory, "smooth")
    os.makedirs(seq, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    for i, fr in enumerate(sh.frames):
        surf = sh._surface(fr["file"])
        surf.write_to_png(os.path.join(seq, f"{i:05d}.png"))
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(src_fps), "-i",
                    os.path.join(seq, "%05d.png"), "-vf",
                    f"minterpolate=fps={SMOOTH_FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    os.path.join(out, "%05d.png")], check=True)
    return len(os.listdir(out))
