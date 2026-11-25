"""Build a film-grammar episode: plan -> rule checks -> 3D shots (Blender) -> checks again -> composite -> QC.
python build_film.py episodes/pirate/film.py [--checks-only] [--preview]"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from build import load  # noqa: E402
from engine.filmplan import render_shots, run_checks  # noqa: E402
from engine.render import qc  # noqa: E402

if __name__ == "__main__":
    path = sys.argv[1]
    ep = load(path)
    ep.build()
    print(f"plan: {len(ep.scenes)} shots, {ep.total:.1f} s")
    print("checks (before render):")
    ok, res = run_checks(ep)
    hard_fail = [r for r in res if not r[1] and not r[0].startswith("R5")]
    if hard_fail:
        print("STOP: fix the failing rules before rendering.")
        sys.exit(1)
    if "--checks-only" in sys.argv:
        sys.exit(0)
    prev = "--preview" in sys.argv
    render_shots(ep, os.path.join(ROOT, "cache", "shots", ep.slug + ("_prev" if prev else "")),
                 fps=8 if prev else 15, w=270 if prev else 540, h=480 if prev else 960, samples=4 if prev else 8)
    print("checks (after render):")
    ok, res = run_checks(ep)
    if not ok:
        print("STOP: render-time checks failed.")
        sys.exit(1)
    out = ep.render()
    print(json.dumps({k: v[0] for k, v in qc(ep, out)["checks"].items()}))
