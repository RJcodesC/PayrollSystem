import math

W, H, FPS = 1080, 1920, 30


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def _back(t, s=1.70158):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def _elastic(t):
    if t in (0, 1):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


EASES = {
    "linear": lambda t: t,
    "in": lambda t: t * t * t,
    "out": lambda t: 1 - (1 - t) ** 3,
    "inout": lambda t: 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2,
    "back": _back,
    "elastic": _elastic,
    "step": lambda t: 1.0 if t >= 1 else 0.0,
}


def tween(t, t0, t1, a, b, ease="inout"):
    """Value going from a to b between times t0..t1 with easing."""
    if t1 <= t0:
        return b if t >= t1 else a
    p = clamp((t - t0) / (t1 - t0))
    return lerp(a, b, EASES[ease](p))


def ramp(t, t0, t1, ease="inout"):
    return tween(t, t0, t1, 0.0, 1.0, ease)


def pulse(t, t0, dur):
    """0 -> 1 -> 0 bump starting at t0."""
    if t < t0 or t > t0 + dur:
        return 0.0
    return math.sin(math.pi * (t - t0) / dur)


class Track:
    """Keyframed pose track. keys: (time, {param: value}, ease?) – each key only lists
    what changes; states accumulate. Numeric params interpolate, others switch."""

    def __init__(self, base, *keys):
        self.keys = []
        state = dict(base)
        for k in sorted(keys, key=lambda k: k[0]):
            t, d = k[0], k[1]
            ease = k[2] if len(k) > 2 else "inout"
            prev = dict(state)
            state = dict(state)
            state.update(d)
            self.keys.append((t, prev, state, ease))
        self.base = dict(base)

    def at(self, t):
        if not self.keys:
            return dict(self.base)
        if t <= self.keys[0][0]:
            return dict(self.keys[0][2])
        out = None
        for i, (kt, prev, state, ease) in enumerate(self.keys):
            nt = self.keys[i + 1][0] if i + 1 < len(self.keys) else None
            if nt is None or t < nt:
                # we are after key i; interpolating from key i's state toward key i+1
                if nt is None:
                    return dict(state)
                _, _, nstate, nease = self.keys[i + 1]
                # tween happens during [kt, nt]
                p = EASES[nease](clamp((t - kt) / (nt - kt)))
                out = {}
                for k, v in nstate.items():
                    a = state.get(k, v)
                    if isinstance(v, (int, float)) and isinstance(a, (int, float)) and not isinstance(v, bool):
                        out[k] = lerp(a, v, p)
                    else:
                        out[k] = a  # discrete values switch exactly at their key time
                return out
        return dict(self.keys[-1][2])


def hexc(h, a=None):
    h = h.lstrip("#")
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else c + (a,)


def noise1(t, seed=0.0):
    """Cheap smooth pseudo-noise in [-1, 1]."""
    return (math.sin(t * 1.7 + seed * 3.1) * 0.5 + math.sin(t * 3.3 + seed * 7.7) * 0.3
            + math.sin(t * 7.1 + seed * 1.3) * 0.2)
