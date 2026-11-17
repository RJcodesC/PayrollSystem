"""Recurring cast. Keep looks consistent across episodes."""
from .rig import Character, Look

# The channel's recurring narrator-host could be added here later.
LUSTIG = Character("lustig", Look(coat="#6b4fa8", coat_dark="#4b3580", tie="#d63c46", hat="tophat",
                                  hat_band="#d63c46", mustache="curly", monocle=True), seed=0.3)
POISSON = Character("poisson", Look(coat="#d9822b", coat_dark="#a95f17", hat="flatcap", hat_color="#7a5634",
                                    glasses=True, mustache="thick", belly=1.0, width=1.05), seed=1.7)
DEALER_A = Character("dealer_a", Look(coat="#4f8f5c", coat_dark="#356b41", hat="bowler", hat_color="#3b3b44",
                                      tie="#e8c547"), seed=2.9)
DEALER_B = Character("dealer_b", Look(coat="#4f7fbf", coat_dark="#365d94", hair="tuft", tie="#e85d5d"), seed=4.1)
BUYER2 = Character("buyer2", Look(coat="#2f9e9a", coat_dark="#1f7270", hat="bowler", hat_color="#5a3d2b",
                                  mustache="thick", tie="#f2c84b"), seed=5.3)
POLICE = Character("police", Look(coat="#2b4a9b", coat_dark="#1d3373", hat="kepi", hat_color="#2b4a9b",
                                  hat_band="#c8313a", badge=True, mustache="thick"), seed=6.6)
