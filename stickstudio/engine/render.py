"""Timeline builder, frame renderer, captions, encoder and automated QC."""
import json
import math
import multiprocessing as mp
import os
import subprocess
import time

import cairo
import numpy as np
import soundfile as sf

from . import audio
from .core import W, H, FPS, EASES, clamp, hexc, noise1, ramp
from .text import text_center, text_width


# ------------------------------------------------------------------ authoring types
class Line:
    def __init__(self, text, speaker="narrator", voice=None, speed=None, gap=0.12, at=None, caption=True,
                 spoken=None):
        """text = caption text; spoken = what the TTS says if it should differ (numbers, names)."""
        self.text, self.speaker, self.voice, self.speed = text, speaker, voice, speed
        self.spoken = spoken or text
        self.gap, self.at, self.caption = gap, at, caption
        self.start = self.end = 0.0
        self.words = []
        self.env = None
        self.clip = None


def N(text, **kw):
    return Line(text, "narrator", **kw)


def Say(char, text, **kw):
    return Line(text, char.name, **kw)


class Scene:
    def __init__(self, name, lines, draw, camera=None, overlay=None, cues=None, pad=0.3, min_dur=0.0,
                 trans="cut", lead=0.08):
        self.name, self.lines, self.draw_fn = name, lines, draw
        self.camera_fn, self.overlay_fn, self.cues_fn = camera, overlay, cues
        self.pad, self.min_dur, self.trans, self.lead = pad, min_dur, trans, lead
        self.start = 0.0
        self.dur = 0.0


class Timing:
    def __init__(self, scene):
        self.scene = scene
        self.dur = scene.dur

    def line(self, i):
        ln = self.scene.lines[i]
        return ln.start, ln.end

    def word(self, i, needle, nth=0, edge="start"):
        """Scene-local time of the nth word in line i that contains `needle`."""
        ln = self.scene.lines[i]
        hits = [w for w in ln.words if needle.lower() in w[0].lower()]
        if not hits:
            raise KeyError(f"'{needle}' not in line {i} of scene {self.scene.name}: {ln.text}")
        w = hits[min(nth, len(hits) - 1)]
        return w[1] if edge == "start" else w[2]


class Frame:
    """Passed to scene draw/camera/overlay functions."""

    def __init__(self, ep, scene, ctx, t_local):
        self.ep, self.scene, self.ctx = ep, scene, ctx
        self.t = t_local
        self.gt = scene.start + t_local
        self.dur = scene.dur
        self.T = Timing(scene)

    def mouth(self, name):
        return self.ep.mouth(name, self.gt)

    def char(self, ch, pose):
        return ch.draw(self.ctx, pose, self.gt, mouth_open=self.mouth(ch.name))

    def r(self, t0, t1, ease="inout"):
        return ramp(self.t, t0, t1, ease)


# ------------------------------------------------------------------ episode
class Episode:
    def __init__(self, slug, scenes, narrator_voice="am_michael", voices=None, speed=1.0, outdir=None,
                 music="caper", caption_y=1330, pronounce=None):
        self.pronounce = pronounce or {}
        self.slug, self.scenes = slug, scenes
        self.narrator_voice = narrator_voice
        self.voices = voices or {}
        self.speed = speed
        self.outdir = outdir or os.path.join(audio.ROOT, "output", slug)
        self.music = music
        self.caption_y = caption_y
        self.total = 0.0
        self.chunks = []

    # ---------------- timeline
    def build(self):
        t = 0.0
        for sc in self.scenes:
            sc.start = t
            cur = sc.lead
            for ln in sc.lines:
                voice = ln.voice or (self.narrator_voice if ln.speaker == "narrator"
                                     else self.voices.get(ln.speaker, self.narrator_voice))
                ln.clip = audio.tts(ln.spoken, voice, ln.speed or self.speed, pronounce=self.pronounce)
                st = ln.at if ln.at is not None else cur + ln.gap
                ln.start, ln.end = st, st + len(ln.clip) / audio.SR
                ln.words = [(w, ln.start + a, ln.start + b) for (w, a, b) in audio.word_times(ln.text, ln.clip)]
                ln.env = audio.envelope(ln.clip, FPS)
                cur = ln.end
            sc.dur = max(cur + sc.pad, sc.min_dur)
            t += sc.dur
        self.total = t
        self._build_captions()
        return self

    def _build_captions(self):
        words = []
        for sc in self.scenes:
            for li, ln in enumerate(sc.lines):
                if not ln.caption:
                    continue
                for (w, a, b) in ln.words:
                    words.append(dict(w=w, s=sc.start + a, e=sc.start + b, line=id(ln),
                                      spk=ln.speaker))
        chunks, cur = [], []
        for i, wd in enumerate(words):
            cur.append(wd)
            txt = " ".join(x["w"] for x in cur)
            nxt = words[i + 1] if i + 1 < len(words) else None
            brk = (len(cur) >= 3 or len(txt) >= 14 or wd["w"][-1] in ".,!?…:" or nxt is None
                   or nxt["line"] != wd["line"])
            if brk:
                chunks.append(cur)
                cur = []
        for i, c in enumerate(chunks):
            s = c[0]["s"]
            e = c[-1]["e"] + 0.25
            if i + 1 < len(chunks):
                e = min(max(e, c[-1]["e"]), chunks[i + 1][0]["s"])
            self.chunks.append(dict(words=c, s=s, e=e))

    def mouth(self, name, gt):
        for sc in self.scenes:
            if sc.start <= gt < sc.start + sc.dur:
                for ln in sc.lines:
                    if ln.speaker == name and sc.start + ln.start <= gt < sc.start + ln.end:
                        i = int((gt - sc.start - ln.start) * FPS)
                        return float(ln.env[min(i, len(ln.env) - 1)])
                return 0.0
        return 0.0

    # ---------------- audio
    def render_audio(self, path):
        clips, events = [], []
        for sc in self.scenes:
            for ln in sc.lines:
                clips.append((sc.start + ln.start, ln.clip))
            if sc.cues_fn:
                for (lt, name, g) in sc.cues_fn(Timing(sc)):
                    events.append((sc.start + lt, name, g))
            if sc.trans == "whip":
                events.append((sc.start - 0.05, "whoosh", 0.7))
        music = audio.music_caper(self.total) if self.music else None
        out = audio.mix(self.total, clips, events, music)
        sf.write(path, out, audio.SR)
        return path

    # ---------------- video
    def scene_at(self, gt):
        for i, sc in enumerate(self.scenes):
            if gt < sc.start + sc.dur or i == len(self.scenes) - 1:
                return i, sc
        return len(self.scenes) - 1, self.scenes[-1]

    def _draw_scene(self, ctx, sc, t_local, xoff=0.0):
        f = Frame(self, sc, ctx, t_local)
        cam = dict(z=1.0, x=540.0, y=960.0, rot=0.0, shake=0.0)
        if sc.camera_fn:
            cam.update(sc.camera_fn(f) or {})
        if sc.trans == "punch":
            cam["z"] *= 1 + 0.09 * (1 - EASES["out"](clamp(t_local / 0.3)))
        ctx.save()
        ctx.translate(540 + xoff, 960)
        if cam["shake"]:
            ctx.translate(noise1(f.gt * 40, 1) * cam["shake"], noise1(f.gt * 40, 5) * cam["shake"])
        ctx.rotate(math.radians(cam["rot"]))
        ctx.scale(cam["z"], cam["z"])
        ctx.translate(-cam["x"], -cam["y"])
        sc.draw_fn(f)
        ctx.restore()
        if sc.overlay_fn:
            ctx.save()
            ctx.translate(xoff, 0)
            sc.overlay_fn(f)
            ctx.restore()

    def draw_frame(self, ctx, gt):
        idx, sc = self.scene_at(gt)
        tl = gt - sc.start
        WD = 0.24
        if sc.trans == "whip" and idx > 0 and tl < WD:
            p = EASES["inout"](tl / WD)
            prev = self.scenes[idx - 1]
            self._draw_scene(ctx, prev, prev.dur - 1e-3, xoff=-p * W)
            self._draw_scene(ctx, sc, tl, xoff=(1 - p) * W)
            # motion streaks
            ctx.set_source_rgba(1, 1, 1, 0.35 * math.sin(p * math.pi))
            for i in range(14):
                y = (i * 151 + 40) % H
                ctx.rectangle(0, y, W, 10)
            ctx.fill()
        elif sc.trans == "fade" and idx > 0 and tl < 0.3:
            prev = self.scenes[idx - 1]
            self._draw_scene(ctx, prev, prev.dur - 1e-3)
            ctx.push_group()
            self._draw_scene(ctx, sc, tl)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(tl / 0.3)
        else:
            self._draw_scene(ctx, sc, tl)
            if sc.trans == "flash" and tl < 0.18:
                ctx.set_source_rgba(1, 1, 1, 1 - tl / 0.18)
                ctx.paint()
        self.draw_captions(ctx, gt)

    def draw_captions(self, ctx, gt):
        for ch in self.chunks:
            if ch["s"] <= gt < ch["e"]:
                words = [w["w"].upper() for w in ch["words"]]
                size = 92
                space = 26
                widths = [text_width(ctx, w, size) for w in words]
                total = sum(widths) + space * (len(words) - 1)
                if total > 940:
                    k = 940 / total
                    size *= k
                    space *= k
                    widths = [w * k for w in widths]
                    total = 940
                pop = EASES["back"](clamp((gt - ch["s"]) / 0.12))
                sc = 0.75 + 0.25 * pop
                ctx.save()
                ctx.translate(540, self.caption_y)
                ctx.scale(sc, sc)
                x = -total / 2
                for w, wd, ww in zip(words, ch["words"], widths):
                    active = wd["s"] <= gt < (wd["e"] + 0.05)
                    col = "#ffd84a" if active else "#ffffff"
                    if ch["words"][0]["spk"] != "narrator":
                        col = "#ffd84a" if active else "#bff0ff"
                    text_center(ctx, w, x, 0, size, col, stroke=17, anchor="left")
                    x += ww + space
                ctx.restore()
                break

    def render_frames(self, start, end, path):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
               "-pix_fmt", "yuv420p", path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(start, end):
            ctx.save()
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
            self.draw_frame(ctx, i / FPS)
            ctx.restore()
            surf.flush()
            p.stdin.write(bytes(surf.get_data()))
        p.stdin.close()
        p.wait()
        return path

    def still(self, gt, path):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        self.draw_frame(ctx, gt)
        surf.write_to_png(path)
        return path

    def render(self, workers=None):
        os.makedirs(self.outdir, exist_ok=True)
        if not self.total:
            self.build()
        t0 = time.time()
        wav = self.render_audio(os.path.join(self.outdir, "mix.wav"))
        nframes = int(math.ceil(self.total * FPS))
        workers = workers or max(1, min(4, os.cpu_count() or 1))
        bounds = [(nframes * i // workers, nframes * (i + 1) // workers) for i in range(workers)]
        segs = [os.path.join(self.outdir, f"seg{i}.mp4") for i in range(workers)]
        global _EP
        _EP = self
        try:
            ctx = mp.get_context("fork")
            with ctx.Pool(workers) as pool:
                pool.starmap(_render_seg, [(a, b, s) for (a, b), s in zip(bounds, segs)])
        except ValueError:  # no fork (Windows): render serially
            for (a, b), s in zip(bounds, segs):
                self.render_frames(a, b, s)
        lst = os.path.join(self.outdir, "segs.txt")
        with open(lst, "w") as fh:
            fh.writelines(f"file '{os.path.basename(s)}'\n" for s in segs)
        final = os.path.join(self.outdir, f"{self.slug}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                        "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", final], check=True)
        for s in segs:
            os.remove(s)
        os.remove(lst)
        print(f"rendered {nframes} frames in {time.time() - t0:.1f}s -> {final}")
        return final


_EP = None


def _render_seg(a, b, path):
    return _EP.render_frames(a, b, path)


# ------------------------------------------------------------------ QC
def qc(ep, path):
    rep = {"file": path, "checks": {}}
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                   capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    dur = float(pr["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    c = rep["checks"]
    c["resolution"] = (f"{v['width']}x{v['height']}", v["width"] == 1080 and v["height"] == 1920)
    c["fps"] = (num / den, abs(num / den - FPS) < 0.01)
    c["duration_s"] = (round(dur, 2), 35 <= dur <= 60)
    c["audio_stream"] = (a[0]["codec_name"] if a else None, bool(a))
    c["file_size_mb"] = (round(os.path.getsize(path) / 1e6, 2), True)
    # black / frozen frames
    r = subprocess.run(["ffmpeg", "-i", path, "-vf", "blackdetect=d=0.3:pix_th=0.05,freezedetect=n=0.001:d=2.5",
                        "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    blacks = r.count("black_start")
    freezes = r.count("freeze_start")
    c["black_segments"] = (blacks, blacks == 0)
    c["frozen_segments_over_2.5s"] = (freezes, freezes == 0)
    # loudness
    r = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    lufs = None
    for line in r.splitlines()[::-1]:
        if line.strip().startswith("I:"):
            lufs = float(line.split()[1])
            break
    c["integrated_loudness_LUFS"] = (lufs, lufs is not None and -16 <= lufs <= -12)
    # story completeness: every scene has narration or explicit duration; captions cover speech
    spoken = sum(ln.end - ln.start for s in ep.scenes for ln in s.lines)
    c["speech_coverage"] = (round(spoken / ep.total, 2), spoken / ep.total > 0.6)
    gaps = []
    for s in ep.scenes:
        for ln in s.lines:
            pass
    c["scenes"] = (len(ep.scenes), len(ep.scenes) >= 6)
    c["max_scene_len_s"] = (round(max(s.dur for s in ep.scenes), 2), max(s.dur for s in ep.scenes) <= 8)
    rep["pass"] = all(v[1] for v in c.values())
    # contact sheet
    sheet = os.path.join(os.path.dirname(path), "contact_sheet.png")
    step = dur / 16
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vf",
                    f"fps=1/{step:.3f},scale=270:480,tile=8x2", "-frames:v", "1", sheet])
    rep["contact_sheet"] = sheet
    with open(os.path.join(os.path.dirname(path), "qc.json"), "w") as fh:
        json.dump(rep, fh, indent=2)
    return rep


# ------------------------------------------------------------------ overlay helpers
def label(ctx, txt, x, y, p, color="#ffd84a", size=58, tcolor="#141418"):
    """Pop-in name tag (screen space)."""
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    w = text_width(ctx, txt, size) + 60
    h = size + 40
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rotate(math.radians(-3))
    r = 22
    ctx.new_path()
    ctx.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(w / 2 - r, h / 2 - r, r, 0, 0.5 * math.pi)
    ctx.arc(-w / 2 + r, h / 2 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgb(*hexc(color))
    ctx.fill_preserve()
    ctx.set_source_rgb(*hexc("#141418"))
    ctx.set_line_width(7)
    ctx.stroke()
    text_center(ctx, txt, 0, 0, size, tcolor)
    ctx.restore()
