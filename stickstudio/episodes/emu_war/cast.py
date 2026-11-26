"""Cast for The Great Emu War (1932). Original designs in the house 'ricks' style.
The soldiers are unnamed cartoon stand-ins (the real unit was Major Meredith + two gunners)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from engine.rig import Character, Look  # noqa: E402
from engine.creatures import Emu  # noqa: E402

KHAKI, KHAKI_D, BROWN = "#b39a62", "#8f7a48", "#6b4423"

MAJOR = Character("major", Look(coat=KHAKI, coat_dark=KHAKI_D, outfit="coat", vest="#a38a55", hat="peaked",
                                hat_color=KHAKI, hat_band="#b8333a", mustache="thick", sash=BROWN, belt=BROWN,
                                sleeve=KHAKI, boots="#3b2614", style="ricks"), seed=0.3)
SGT = Character("sgt", Look(coat=KHAKI, coat_dark=KHAKI_D, outfit="coat", vest="#a38a55", hat="slouch",
                            hat_color="#9a8556", hat_band="#5d4a2a", belt=BROWN, sleeve=KHAKI, boots="#5a4a32",
                            stubble=True, style="ricks"), seed=1.1)
GUNNER = Character("gunner", Look(coat=KHAKI, coat_dark=KHAKI_D, outfit="coat", vest="#a38a55", hat="slouch",
                                  hat_color="#9a8556", hat_band="#5d4a2a", belt=BROWN, sleeve=KHAKI,
                                  boots="#5a4a32", style="ricks", height=0.96), seed=2.2)
FARMER = Character("farmer", Look(coat="#e9e2cf", coat_dark="#c9c0a8", outfit="vest", vest="#3c5f9c",
                                  hat="flatcap", hat_color="#7a5a34", beard="#7a5a3a", sleeve="#e9e2cf",
                                  boots="#3b2614", style="ricks", belly=0.3), seed=3.3)
EMU = Emu("emu", seed=0.4)
EMU2 = Emu("emu2", seed=1.7)

# ---------------------------------------------------------------- vetted pose library (IK targets, rig units)
# Rule for this side-view style: hands stay clear of the torso outline and never cross the face.
REST = dict(ba=-24, bb=10, fa=24, fb=10)                                # arms hang just outside the coat
POINT = dict(hand_f_at=(230, 300), ba=-24, bb=10)                       # straight-arm point forward
HANDS_UP = dict(hand_f_at=(135, 395), hand_b_at=(-125, 395))            # shock: palms up, out to the sides
FACEPALM = dict(hand_f_at="face", ba=-24, bb=10)
SHRUG = dict(hand_f_at=(120, 250), hand_b_at=(-62, 185))               # palms out at waist height
