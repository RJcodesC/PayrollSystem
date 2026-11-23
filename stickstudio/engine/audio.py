"""Narration (Kokoro TTS, offline), lip-sync envelopes, word timing estimates,
procedurally synthesised sound effects and music, and the final mix."""
import hashlib
import math
import os
import re

import numpy as np
import soundfile as sf

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "tts")
_kokoro = None


def _tts_engine():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(ROOT, "voices", "kokoro-v1.0.onnx"),
                         os.path.join(ROOT, "voices", "voices-v1.0.bin"))
    return _kokoro


def resample(x, sr_in, sr_out=SR):
    if sr_in == sr_out:
        return x.astype(np.float32)
    n = int(len(x) * sr_out / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def trim(x, thr=0.01, pad=0.03):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def tts(text, voice, speed=1.0, lang="en-us", pronounce=None):
    """pronounce: {word: ipa} overrides for names the phonemizer gets wrong."""
    os.makedirs(CACHE, exist_ok=True)
    pr = sorted((pronounce or {}).items())
    key = hashlib.sha1(f"{voice}|{speed}|{lang}|{text}|{pr}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(path):
        k = _tts_engine()
        used = [(w, ipa) for w, ipa in pr if w.lower() in text.lower()]
        if used:
            ph = k.tokenizer.phonemize(text, lang)
            for w, ipa in used:
                ph = ph.replace(k.tokenizer.phonemize(w, lang).strip(".!? "), ipa)
            samples, sr = k.create(ph, voice=voice, speed=speed, lang=lang, is_phonemes=True)
        else:
            samples, sr = k.create(text, voice=voice, speed=speed, lang=lang)
        sf.write(path, resample(np.asarray(samples), sr), SR)
    x, _ = sf.read(path, dtype="float32")
    return trim(x)


def envelope(x, fps=30):
    """Per-video-frame mouth openness 0..1 from speech amplitude."""
    hop = SR // fps
    n = int(math.ceil(len(x) / hop))
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    if env.max() > 0:
        env = env / (np.percentile(env, 95) + 1e-9)
    env = np.clip((env - 0.12) * 1.4, 0, 1)
    # quick open, slower close, plus slight chatter so held vowels don't freeze
    out = np.zeros_like(env)
    v = 0.0
    for i, e in enumerate(env):
        v = e if e > v else v * 0.55 + e * 0.45
        out[i] = v * (0.85 + 0.15 * math.sin(i * 2.1))
    return out


def word_times(text, x):
    """Estimate (word, start, end) inside a clip by distributing speech by syllable weight,
    with extra weight for punctuation pauses."""
    words = text.split()
    dur = len(x) / SR

    def syl(w):
        w2 = re.sub(r"[^a-z0-9]", "", w.lower())
        if w2.isdigit():
            return 2.5 * len(w2) / 2
        groups = re.findall(r"[aeiouy]+", w2)
        n = max(1, len(groups) - (1 if w2.endswith("e") and len(groups) > 1 else 0))
        return n + 0.35

    def pause(w):
        if w.endswith(("...", "…")):
            return 2.2
        if w.endswith((".", "!", "?")):
            return 1.2
        if w.endswith((",", ";", ":", "—")):
            return 0.8
        return 0.0

    weights = [syl(w) for w in words]
    pauses = [pause(w) for w in words]
    total = sum(weights) + sum(pauses[:-1])
    t = 0.0
    out = []
    for i, w in enumerate(words):
        d = weights[i] / total * dur
        out.append((w, t, t + d))
        t += d + (pauses[i] / total * dur if i < len(words) - 1 else 0)
    return out


# ------------------------------------------------------------------ SFX synthesis
def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def _noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def _lp(x, a):
    """one-pole low-pass (a in 0..1, smaller = darker), vectorised via lfilter-free cumulative trick"""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def sfx_whoosh(d=0.45):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = _noise(n, 1)
    # sweep the filter by mixing differently smoothed copies
    k = np.convolve(x, np.ones(30) / 30, mode="same")
    k2 = np.convolve(x, np.ones(6) / 6, mode="same")
    sweep = np.sin(np.pi * t / d) ** 2
    return ((k * (1 - t / d) + k2 * (t / d) * 0.6) * sweep * 1.6).astype(np.float32)


def sfx_pop():
    t = _t(0.12)
    f = 900 * np.exp(-t * 30) + 300
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.001, 0.035)).astype(np.float32)


def sfx_boing():
    t = _t(0.5)
    f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 200 * t
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.18) * 0.8).astype(np.float32)


def sfx_stamp():
    t = _t(0.35)
    thud = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 12) + 45) / SR) * _env(len(t), 0.001, 0.09)
    click = np.convolve(_noise(len(t), 3), np.ones(8) / 8, "same") * _env(len(t), 0.0005, 0.02)
    return (thud * 1.2 + click * 1.5).astype(np.float32)


def sfx_ding():
    t = _t(1.2)
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1568, 1), (3136, 0.4), (4700, 0.2), (2349, 0.3)))
    return (x * _env(len(t), 0.002, 0.35) * 0.35).astype(np.float32)


def sfx_chaching():
    a = sfx_stamp() * 0.5
    b = sfx_ding()
    c = np.zeros(int(0.08 * SR) + len(b), np.float32)
    c[:len(a)] += a[:len(c)]
    c[int(0.08 * SR):] += b
    t = _t(0.25)
    rattle = _noise(len(t), 5) * _env(len(t), 0.001, 0.08) * 0.3
    c[:len(rattle)] += np.convolve(rattle, np.ones(3) / 3, "same")
    return c


def sfx_crickets(d=1.6):
    t = _t(d)
    x = np.zeros_like(t)
    for start in np.arange(0.05, d - 0.2, 0.42):
        for k in range(3):
            s = start + k * 0.045
            m = (t >= s) & (t < s + 0.03)
            x[m] += np.sin(2 * np.pi * 4600 * t[m]) * np.sin(np.pi * (t[m] - s) / 0.03)
    return (x * 0.25).astype(np.float32)


def sfx_whistle(d=0.9):
    t = _t(d)
    f = 2900 + 180 * np.sign(np.sin(2 * np.pi * 26 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.05)
    return (x * e * 0.28).astype(np.float32)


def sfx_footsteps(d=1.0, rate=4.0):
    t = _t(d)
    x = np.zeros_like(t)
    tap = np.convolve(_noise(int(0.05 * SR), 9), np.ones(12) / 12, "same") * _env(int(0.05 * SR), 0.001, 0.012)
    for s in np.arange(0, d - 0.05, 1 / rate):
        i = int(s * SR)
        x[i:i + len(tap)] += tap[:len(x) - i]
    return (x * 1.8).astype(np.float32)


def sfx_gasp():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = np.convolve(_noise(n, 11), np.ones(4) / 4, "same")
    e = np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.12) / 0.12)
    return (x * e * 0.35).astype(np.float32)


def sfx_sting(kind="dun"):
    """Short musical stinger: 'dun' (dramatic), 'reveal' (bright), 'fail' (sad trombone-ish)."""
    if kind == "fail":
        notes = [(466, 0.25), (440, 0.25), (415, 0.25), (392, 0.7)]
    elif kind == "reveal":
        notes = [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.5)]
    else:
        notes = [(147, 0.18), (139, 0.18), (131, 0.7)]
    out = []
    for f, d in notes:
        t = _t(d)
        x = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 6))
        if kind == "fail":
            x = x * (1 + 0.15 * np.sin(2 * np.pi * 6 * t))
        out.append(x * _env(len(t), 0.01, d * 0.8))
    return (np.concatenate(out) * 0.3).astype(np.float32)


def sfx_zip():
    t = _t(0.22)
    f = 400 + 3000 * t / 0.22
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * _env(len(t), 0.002, 0.1) * 0.12).astype(np.float32)


SFX = {
    "whoosh": sfx_whoosh, "pop": sfx_pop, "boing": sfx_boing, "stamp": sfx_stamp, "ding": sfx_ding,
    "chaching": sfx_chaching, "crickets": sfx_crickets, "whistle": sfx_whistle, "steps": sfx_footsteps,
    "run": lambda: sfx_footsteps(1.2, 9), "gasp": sfx_gasp, "dun": lambda: sfx_sting("dun"),
    "reveal": lambda: sfx_sting("reveal"), "fail": lambda: sfx_sting("fail"), "zip": sfx_zip,
}


# ------------------------------------------------------------------ music
def _pluck(f, d, bright=0.5):
    t = _t(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * (bright ** (k - 1)) / k for k in range(1, 7))
    return x * _env(len(t), 0.003, d * 0.35)


def music_caper(total, bpm=112, seed=0):
    """Original sneaky 'caper' groove: pizzicato bass + plucked melody + light percussion."""
    beat = 60 / bpm
    n = int(total * SR) + SR
    out = np.zeros(n, np.float32)

    def put(x, at, g):
        i = int(at * SR)
        if i >= n:
            return
        x = x[: n - i]
        out[i:i + len(x)] += (x * g).astype(np.float32)

    # D minor, chromatic sneaky bassline (two bars, 8 eighth notes each)
    bass = [73.4, 0, 87.3, 0, 98.0, 0, 103.8, 98.0, 73.4, 0, 87.3, 0, 110.0, 0, 103.8, 98.0]
    mel = [0, 587, 0, 0, 698, 0, 659, 0, 0, 587, 0, 554, 0, 0, 440, 0,
           0, 587, 0, 0, 698, 0, 784, 0, 880, 0, 784, 698, 659, 0, 587, 0]
    eighth = beat / 2
    i = 0
    t = 0.0
    while t < total:
        f = bass[i % len(bass)]
        if f:
            put(_pluck(f, eighth * 1.6, 0.35), t, 0.55)
        m = mel[i % len(mel)]
        if m and (i // 32) % 2 == 0 or (m and i % 3 == 0):
            put(_pluck(m, eighth * 1.2, 0.55), t, 0.16)
        # percussion: soft shaker on off-beats, finger snap on 2 and 4
        if i % 2 == 1:
            sh = _noise(int(0.04 * SR), i) * _env(int(0.04 * SR), 0.002, 0.012)
            put(np.convolve(sh, [1, -1], "same"), t, 0.05)
        if i % 4 == 2:
            sn = _noise(int(0.08 * SR), i + 99) * _env(int(0.08 * SR), 0.001, 0.025)
            put(sn, t, 0.08)
        i += 1
        t += eighth
    return out[: int(total * SR)]


# ------------------------------------------------------------------ mix
def mix(total, voice_clips, sfx_events, music=None, music_gain=0.32, duck=0.65):
    """voice_clips: [(start, samples)], sfx_events: [(start, name, gain)]"""
    n = int(total * SR) + 1
    voice = np.zeros(n, np.float32)
    for st, x in voice_clips:
        i = int(st * SR)
        x = x[: max(0, n - i)]
        voice[i:i + len(x)] += x
    fx = np.zeros(n, np.float32)
    cache = {}
    for st, name, g in sfx_events:
        if name not in cache:
            cache[name] = SFX[name]()
        x = cache[name]
        i = int(max(0, st) * SR)
        x = x[: max(0, n - i)]
        fx[i:i + len(x)] += x * g
    out = voice * 1.0 + fx * 0.5
    if music is not None:
        m = np.zeros(n, np.float32)
        m[: min(n, len(music))] = music[:n]
        # sidechain duck under the voice
        ve = np.abs(voice)
        win = int(0.15 * SR)
        ve = np.convolve(ve, np.ones(win) / win, "same")
        ve = np.clip(ve / (ve.max() + 1e-9) * 4, 0, 1)
        fade = np.ones(n, np.float32)
        fl = int(0.6 * SR)
        fade[-fl:] = np.linspace(1, 0, fl)
        out += m * music_gain * (1 - duck * ve) * fade
    peak = np.max(np.abs(out)) + 1e-9
    return (out / peak * 0.89).astype(np.float32)


# ------------------------------------------------------------------ horror kit
def sfx_heartbeat(n=2):
    out = []
    for _ in range(n):
        for f0, g in ((55, 1.0), (48, 0.7)):
            t = _t(0.16)
            out.append(np.sin(2 * np.pi * np.cumsum(f0 + 40 * np.exp(-t * 30)) / SR) * _env(len(t), 0.003, 0.05) * g)
            out.append(np.zeros(int(0.09 * SR)))
        out.append(np.zeros(int(0.35 * SR)))
    return (np.concatenate(out) * 0.9).astype(np.float32)


def sfx_buzz(d=0.5):
    t = _t(d)
    x = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.5 + np.sin(2 * np.pi * 240 * t) * 0.3
    gate = (np.random.default_rng(3).random(int(d * 40) + 1) > 0.35).repeat(int(SR / 40) + 1)[: len(t)]
    return (x * gate * 0.12).astype(np.float32)


def sfx_hit():
    """Scare hit: low boom + dissonant cluster + noise burst."""
    t = _t(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 3) + 30) / SR) * _env(len(t), 0.002, 0.5)
    clus = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((311, 329.6, 349.2, 466, 493.9))) / 5
    clus = clus * _env(len(t), 0.01, 0.6)
    nz = np.convolve(_noise(len(t), 21), np.ones(5) / 5, "same") * _env(len(t), 0.001, 0.15)
    return (boom * 0.9 + clus * 0.35 + nz * 0.5).astype(np.float32)


def sfx_step_stone():
    t = _t(0.18)
    thump = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 25) + 60) / SR) * _env(len(t), 0.001, 0.04)
    scuff = np.convolve(_noise(len(t), 31), np.ones(10) / 10, "same") * _env(len(t), 0.002, 0.03)
    return (thump * 0.9 + scuff * 0.8).astype(np.float32)


def sfx_creak():
    t = _t(0.9)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t) + 30 * np.sin(2 * np.pi * 17 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (np.random.default_rng(5).random(len(t)) > 0.4)
    x = np.convolve(x, np.ones(20) / 20, "same")
    return (x * np.sin(np.pi * t / 0.9) * 0.35).astype(np.float32)


def sfx_glass():
    """Glass smash: sharp noise crack + scattered high tinkles."""
    t = _t(1.3)
    nz = _noise(len(t), 41)
    crack = (nz - np.convolve(nz, np.ones(6) / 6, "same")) * _env(len(t), 0.0005, 0.06) * 1.6
    rng = np.random.default_rng(7)
    tink = np.zeros_like(t)
    for _ in range(26):
        st = rng.uniform(0.02, 0.9)
        f = rng.uniform(2500, 6500)
        m = t >= st
        tt = t[m] - st
        tink[m] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(18, 40)) * rng.uniform(0.2, 0.6)
    return (crack + tink * 0.5).astype(np.float32)


SFX.update({"glass": sfx_glass, "heartbeat": sfx_heartbeat, "buzz": sfx_buzz, "hit": sfx_hit, "step": sfx_step_stone,
            "creak": sfx_creak})


def music_horror(total, seed=0):
    """Original dark ambience: detuned low drone, slow swells, sparse high 'music box' notes."""
    n = int(total * SR)
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 55.7 * t) * 0.8 + np.sin(2 * np.pi * 82.4 * t) * 0.35
             + np.sin(2 * np.pi * 77.8 * t) * 0.25)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.0 - 1.5)
    air = np.convolve(_noise(n, seed + 1), np.ones(200) / 200, "same") * 3.0
    out = drone * 0.22 * swell + air * 0.12
    notes = [1318.5, 1174.7, 1046.5, 987.8, 1046.5, 880.0]
    i = 0
    for st in np.arange(2.0, total - 1, 2.6):
        f = notes[i % len(notes)]
        d = 1.4
        tt = _t(d)
        x = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.01 * tt)) * _env(len(tt), 0.002, 0.4)
        a = int(st * SR)
        x = x[: n - a]
        out[a:a + len(x)] += x * 0.05
        i += 1
    return out.astype(np.float32)
