#!/usr/bin/env python3
"""Scaffold a canvas video: copy the engine (once) and a ready-to-play template.

Part of canvas-video-skill (https://github.com/mmornati/canvas-video-skill).

    python3 new_video.py docs/videos/intro --title "My project in 60 seconds" --langs en,fr

creates

    docs/videos/engine/        engine.js, player.css, fonts/ (shared by every video)
    docs/videos/intro/         index.html, script.json, scenes.js, lexicon.json

The template plays as-is once narrated (two placeholder scenes), so you can check
the whole pipeline before writing a single scene. `--update-engine` refreshes
an existing engine/ folder from the skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", type=Path, help="the new video folder, e.g. docs/videos/intro")
    ap.add_argument("--title", default="", help="video title (all languages, translate later in scenes.js)")
    ap.add_argument("--langs", default="en", help="comma-separated languages, e.g. en,fr,it")
    ap.add_argument("--update-engine", action="store_true", help="overwrite the shared engine/ with the skill's version")
    args = ap.parse_args()

    video, engine = args.folder.resolve(), args.folder.resolve().parent / "engine"
    if video.name == "engine":
        raise SystemExit("'engine' is reserved for the shared engine folder")
    if not engine.exists() or args.update_engine:
        shutil.copytree(SKILL / "engine", engine, dirs_exist_ok=True)
        print(f"engine  -> {engine}")
    if video.exists() and any(video.iterdir()):
        if args.update_engine:
            return 0
        raise SystemExit(f"{video} already exists and is not empty")
    shutil.copytree(SKILL / "template", video, dirs_exist_ok=True)

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    title = args.title or video.name.replace("-", " ").title()
    script = json.loads((video / "script.json").read_text(encoding="utf-8"))
    script["langs"] = langs
    for sc in script["scenes"]:
        en = sc.get("en", [])
        for l in langs:
            sc.setdefault(l, en)  # placeholder: the English text, to translate
        for l in list(sc):
            if len(l) <= 5 and l not in langs and l not in ("id", "min", "lead", "tail") and isinstance(sc[l], list):
                del sc[l]
        if isinstance(sc.get("chapter"), dict):
            sc["chapter"] = {l: sc["chapter"].get(l, sc["chapter"].get("en", "")) for l in langs}
    (video / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for f in ("index.html", "scenes.js"):
        p = video / f
        p.write_text(p.read_text(encoding="utf-8").replace("__TITLE__", title.replace('"', '\\"'))
                     .replace("__LANGS__", json.dumps(langs)), encoding="utf-8")
    print(f"video   -> {video}")
    print("next    -> narrate:", f"uv run --with kokoro-onnx --with soundfile {SKILL / 'scripts' / 'narrate.py'} {args.folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
