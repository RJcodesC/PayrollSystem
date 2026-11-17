# StickStudio — stick-figure Shorts engine

Original 2D stick-figure story videos (1080×1920, 30 fps, 35–60 s) rendered fully locally with
free tools: **Python + pycairo** (vector rig & drawing), **Kokoro** (offline neural TTS),
**numpy** (synthesised SFX + music), **FFmpeg** (encode, loudness, QC).

```
engine/
  core.py     easing, keyframe Tracks, tween helpers
  rig.py      rigged characters: limbs, faces, expressions, blink, lip-sync, walk/run, props, hats
  cast.py     recurring characters (keep looks consistent)
  bg.py       backgrounds (Paris, hotel, newspaper, Alps, police) + effects (dust, sparkles, speed lines)
  audio.py    TTS + pronunciation overrides, mouth envelopes, word timing, SFX & music synth, mixing
  render.py   timeline, camera/transitions, captions, parallel render, QC report
episodes/<slug>/
  episode.py  script + storyboard as code (scenes keyed to narration words)
  sources.md  fact-check / source list
  metadata.md title, description, hashtags, thumbnail concept
build.py      python build.py episodes/<slug>
```

## Setup
```
pip install pycairo numpy soundfile kokoro-onnx
# voices/: kokoro-v1.0.onnx + voices-v1.0.bin from
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
# ffmpeg on PATH
python build.py episodes/eiffel_tower
```
Outputs land in `output/<slug>/`: the MP4, `qc.json`, `contact_sheet.png`, `thumbnail_frame.png`.

Windows: everything above is pip-installable; rendering falls back to a single process where `fork`
is unavailable (slower but identical output).

## Making a new episode
Copy `episodes/eiffel_tower`, rewrite `SCENES`. Each `Scene` has narration `Line`s (`N(...)` for the
narrator, `Say(CHAR, ...)` for dialogue with lip-sync), a `draw(f)` function, optional `camera`,
`overlay`, `cues` (SFX) and a transition (`cut`, `whip`, `punch`, `fade`, `flash`). Use
`f.T.word(line, "word")` to land animation and sound effects exactly on a spoken word.
