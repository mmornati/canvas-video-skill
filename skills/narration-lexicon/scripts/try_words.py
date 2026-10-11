#!/usr/bin/env python3
"""A/B pronunciation variants: synthesise each candidate with the video's voice, transcribe it back.

Part of canvas-video-skill (https://github.com/mmornati/canvas-video-skill).

Before adding an entry to lexicon.json, try a few spellings in a short carrier
sentence and keep the one that comes back right. Each variant is spoken with the
same engine and voice as the video (script.json "engine"/"voices", or --engine),
saved as a WAV you can listen to, and transcribed with faster-whisper.

    uv run --with kokoro-onnx --with soundfile --with faster-whisper --with num2words \\
        try_words.py videos/my-video --lang it \\
        "Si chiama LeanProxy." "Si chiama Lin Proxi." "Si chiama [[lˈin prˈɔksi]]."

`[[…]]` is raw IPA, honoured by Kokoro and Azure only. The WAVs land in
./build/lexicon-trials/ (or --out).
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _stt  # noqa: E402



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path, help="the video folder (for its engine, voices and language list)")
    ap.add_argument("variants", nargs="+", help="spoken-text candidates (use a short carrier sentence)")
    ap.add_argument("--lang", required=True)
    ap.add_argument("--engine", help="default: the video's engine")
    ap.add_argument("--model", default="small", help="Whisper model size")
    ap.add_argument("--out", type=Path, default=Path("build/lexicon-trials"))
    ap.add_argument("--narrate", type=Path, help="path to canvas-video's narrate.py (auto-detected in the plugin)")
    args = ap.parse_args()

    n = _stt.load_narrate(args.narrate)
    data = json.loads((args.video / "script.json").read_text(encoding="utf-8"))
    name = args.engine or data.get("engine", "kokoro")
    engine, cfg = n.ENGINE_CLASSES[name](), n.voice_cfg(data, name, args.lang)
    args.out.mkdir(parents=True, exist_ok=True)
    for i, text in enumerate(args.variants):
        pcm = n.speak(engine, text, cfg)
        wav = args.out / f"{args.lang}-{i + 1:02d}.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(n.SR); w.writeframes(pcm.tobytes())
        heard = _stt.transcribe(_stt.load_audio(wav), args.lang, args.model)
        print(f"{i + 1}. {text}\n   heard: {heard}\n   file : {wav}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
