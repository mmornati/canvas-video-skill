#!/usr/bin/env python3
"""Export a canvas video to PNG stills, a contact sheet, or an MP4 file.

Part of canvas-video-skill (https://github.com/mmornati/canvas-video-skill).

On a website the page itself *is* the video. You only need this to:
  - LOOK at what you built: `--sheet` renders the last second of every scene into
    one contact sheet image, per language — the fastest way to catch overlaps,
    overflowing translations and empty frames (an agent can read the PNG back);
  - publish where JavaScript can't run (YouTube, LinkedIn, a release asset): MP4;
  - make a cover or a poster: `--still T`.

Each page draws every frame from elapsed time alone and exposes
`window.renderFrame(t)`. This script opens it in headless Chrome, calls
`renderFrame` frame by frame — never in real time, so no frame is ever dropped,
whatever the machine — and pipes each PNG into ffmpeg. The narration track
(`audio/<lang>.m4a`, from narrate.py) is then muxed in, untouched.

Prerequisites: ffmpeg, uv, and Google Chrome or Playwright's Chromium
(`uvx playwright install chromium`). Nothing is installed in your project:

    uv run --with playwright render.py videos/my-video --sheet                 # every language
    uv run --with playwright render.py videos/my-video --still 12.5 --res 1080
    uv run --with playwright render.py videos/my-video --lang en               # MP4
    uv run --with playwright render.py videos/my-video --lang en --burn-subs   # social media

Output: ./build/video/ by default (-o to change).
"""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import json
import math
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    """Serve the videos folder on 127.0.0.1 (ephemeral port): fonts and audio stay local."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def grab_png(page, t: float) -> bytes:
    url = page.evaluate("t => { window.renderFrame(t); return document.getElementById('c').toDataURL('image/png'); }", t)
    return base64.b64decode(url.split(",", 1)[1])


def langs_of(video: Path) -> list[str]:
    return json.loads((video / "script.json").read_text(encoding="utf-8")).get("langs") or ["en"]


def open_page(browser, port: int, video: Path, lang: str, res: str, subs: bool):
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(f"http://127.0.0.1:{port}/{video.name}/index.html?capture=1&lang={lang}&res={res}&subs={int(subs)}")
    page.evaluate("window.videoReady")
    if not float(page.evaluate("window.DURATION")):
        raise SystemExit(f"{video.name} [{lang}]: zero duration — run narrate.py first")
    return page


def contact_sheet(page, out: Path) -> None:
    """Last second of every scene (when it is fully built), 4 per row, 640×360 each, in scene order."""
    plan = page.evaluate("window.VIDEO.plan")
    times = [max(sc["start"], sc["start"] + sc["d"] - 1.0) for sc in plan["scenes"]]
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, t in enumerate(times):
            f = Path(tmp) / f"{i:02d}.png"
            f.write_bytes(grab_png(page, t))
            files.append(f)
        cols = min(4, len(files))
        rows = math.ceil(len(files) / cols)
        while len(files) < rows * cols:  # pad the last row with the last frame dimmed out
            files.append(files[-1])
        inputs = sum((["-i", str(f)] for f in files), [])
        scale = "".join(f"[{i}]scale=640:360[s{i}];" for i in range(len(files)))
        stacks = "".join("".join(f"[s{r * cols + c}]" for c in range(cols)) + (f"hstack={cols}[r{r}];" if cols > 1 else f"copy[r{r}];")
                         for r in range(rows))
        final = "".join(f"[r{r}]" for r in range(rows)) + (f"vstack={rows}" if rows > 1 else "copy")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", scale + stacks + final, str(out)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path, help="the video folder (its parent must hold engine/)")
    ap.add_argument("--lang", action="append", help="language(s); default: all for --sheet, the first one otherwise")
    ap.add_argument("--res", choices=("720", "1080", "1440", "2160"), default=None, help="default 720 for stills/sheets, 1080 for MP4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crf", type=int, default=18, help="x264 quality, lower = better")
    ap.add_argument("--still", type=float, action="append", help="only write a PNG at this time (s), repeatable")
    ap.add_argument("--sheet", action="store_true", help="contact sheet of every scene (per language)")
    ap.add_argument("--burn-subs", action="store_true", help="burn subtitles into the image")
    ap.add_argument("-o", "--out-dir", type=Path, default=Path("build/video"))
    args = ap.parse_args()

    video = args.video.resolve()
    if not (video / "index.html").exists() or not (video.parent / "engine" / "engine.js").exists():
        raise SystemExit(f"{video} must contain index.html, and its parent folder engine/engine.js")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright missing: uv run --with playwright render.py …")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found in PATH (brew install ffmpeg / apt install ffmpeg).")
    still_mode = bool(args.still or args.sheet)
    res = args.res or ("720" if still_mode else "1080")
    langs = args.lang or (langs_of(video) if args.sheet else langs_of(video)[:1])
    args.out_dir.mkdir(parents=True, exist_ok=True)

    server, port = serve(video.parent)
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(channel="chrome")
            except Exception:  # noqa: BLE001 - fall back to Playwright's Chromium
                browser = pw.chromium.launch()
            for lang in langs:
                base = args.out_dir / f"{video.name}-{lang}-{res}p"
                page = open_page(browser, port, video, lang, res, args.burn_subs)
                if args.sheet:
                    out = Path(f"{base}-sheet.png")
                    contact_sheet(page, out)
                    print(out)
                for t in args.still or []:
                    out = Path(f"{base}-{t:g}s.png")
                    out.write_bytes(grab_png(page, t))
                    print(out)
                if still_mode:
                    page.close()
                    continue
                duration = float(page.evaluate("window.DURATION"))
                frames = int(round(duration * args.fps)) + 1
                silent = Path(f"{base}.video.mp4")
                ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png",
                                       "-framerate", str(args.fps), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                                       "-crf", str(args.crf), "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
                started = time.monotonic()
                for i in range(frames):
                    ff.stdin.write(grab_png(page, i / args.fps))
                    if i % args.fps == 0 or i == frames - 1:
                        print(f"\r{video.name} [{lang}] {i + 1}/{frames} frames", end="", file=sys.stderr, flush=True)
                ff.stdin.close()
                if ff.wait():
                    raise SystemExit("ffmpeg failed")
                print(f"\n{frames} frames in {time.monotonic() - started:.0f} s", file=sys.stderr)
                out = Path(f"{base}.mp4")
                audio = video / "audio" / f"{lang}.m4a"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(audio),
                                "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart", str(out)], check=True)
                silent.unlink(missing_ok=True)
                page.close()
                print(out)
            browser.close()
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
