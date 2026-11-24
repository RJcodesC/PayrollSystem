"""Build an episode: python build.py episodes/eiffel_tower"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from engine.render import qc  # noqa: E402


def load(ep_path):
    """ep_path: an episode .py file, or a folder containing episode.py"""
    path = ep_path if ep_path.endswith(".py") else os.path.join(ep_path, "episode.py")
    spec = importlib.util.spec_from_file_location("episode", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EPISODE


if __name__ == "__main__":
    ep = load(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "episodes", "eiffel_tower"))
    ep.build()
    out = ep.render()
    rep = qc(ep, out)
    print(json.dumps(rep, indent=2))
    # thumbnail frame: just after the second sign lands in scene 2
    sc = ep.scenes[1]
    ep.chunks = []  # no captions on the thumbnail still
    ep.still(sc.start + sc.dur - 0.05, os.path.join(ep.outdir, "thumbnail_frame.png"))
