#!/usr/bin/env python3
"""Check a canvas video's narration: transcribe every sentence and diff it against the script.

Part of canvas-video-skill (https://github.com/mmornati/canvas-video-skill).

After three listens you hear what you expect. A speech-to-text model doesn't:
each cue (sentence) of `audio/<lang>.m4a` is cut out using the timestamps in
timing.js, transcribed with faster-whisper (locally), normalised (numbers to
words, case, punctuation, accents) and compared with the text in script.json.
Cues below the similarity threshold are listed with their word-level diff — the
words to fix in lexicon.json. Each cue is compared with both the script text and
the text as respelled by lexicon.json, and the better match counts: a word you
respelled on purpose ("LeanProxy" → "Lean Proxy") is not reported again.

    uv run --with faster-whisper --with num2words verify.py videos/my-video
    uv run --with faster-whisper --with num2words verify.py videos/my-video --lang it --threshold 0.95
    uv run --with faster-whisper --with num2words verify.py videos/my-video --json > report.json

Exit code 1 when a cue is flagged, so it can gate a loop or a CI job.
The first run downloads the Whisper model (`small`, ~470 MB) to ~/.cache/huggingface.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _stt  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("--lang", action="append", help="language(s) to check (default: all in timing.js)")
    ap.add_argument("--threshold", type=float, default=0.9, help="flag cues below this similarity (0..1)")
    ap.add_argument("--model", default="small", help="Whisper model size: tiny, base, small, medium, large-v3")
    ap.add_argument("--json", action="store_true", help="machine-readable report on stdout")
    ap.add_argument("--all", action="store_true", help="also list cues that pass")
    ap.add_argument("--narrate", type=Path, help="path to canvas-video's narrate.py (auto-detected in the plugin)")
    args = ap.parse_args()

    timing = _stt.read_timing(args.video)
    narrate = _stt.load_narrate(args.narrate)
    report, flagged = [], 0
    for lang in args.lang or list(timing):
        audio = _stt.load_audio(args.video / "audio" / f"{lang}.m4a")
        for sc in timing[lang]["scenes"]:
            for c in sc["cues"]:
                a = max(0, int((sc["start"] + c["s"] - 0.15) * _stt.SR))
                b = int((sc["start"] + c["e"] + 0.2) * _stt.SR)
                heard = _stt.transcribe(audio[a:b], lang, args.model)
                score, diffs = _stt.compare(c["text"], heard, lang)
                respelled = _stt.spoken_text(narrate, args.video, c["text"], lang, timing[lang].get("engine", "kokoro"))
                if respelled != c["text"]:
                    s2, d2 = _stt.compare(respelled, heard, lang)
                    if s2 > score:
                        score, diffs = s2, d2
                ok = score >= args.threshold
                flagged += not ok
                report.append({"lang": lang, "scene": sc["id"], "at": round(sc["start"] + c["s"], 2), "score": round(score, 3),
                               "ok": ok, "expected": c["text"], "heard": heard,
                               "diff": [{"expected": e, "heard": h} for e, h in diffs]})
                if not args.json and (not ok or args.all):
                    mark = "✓" if ok else "✗"
                    print(f"{mark} [{lang}] {sc['id']} @{sc['start'] + c['s']:.1f}s  {score:.2f}")
                    print(f"    script: {c['text']}")
                    print(f"    heard : {heard}")
                    for e, h in diffs:
                        print(f"      «{e or '∅'}» → «{h or '∅'}»")
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
        print()
    else:
        total = len(report)
        print(f"\n{total - flagged}/{total} cues match (threshold {args.threshold}).", file=sys.stderr)
        if flagged:
            print("Fix: add the words above to lexicon.json (try variants with try_words.py), re-narrate, re-verify.\n"
                  "Not every diff is a voice problem: Whisper has priors too (homophones, brand names) — listen to those.",
                  file=sys.stderr)
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
