#!/usr/bin/env python3
"""Narrate a canvas video: script.json -> voice track, scene timing, subtitles.

Part of canvas-video-skill (https://github.com/mmornati/canvas-video-skill).

A video is a folder (next to the shared `engine/` folder) holding a `script.json`,
the single source of the scene breakdown and of what is said:

    {
      "langs": ["en", "fr"],
      "engine": "kokoro",                                   # optional, default kokoro
      "voices": {"kokoro": {"en": {"voice": "am_michael"}}}, # optional overrides
      "scenes": [
        {"id": "hook", "min": 6, "chapter": {"en": "The problem", "fr": "Le problème"},
         "en": ["First sentence.", {"text": "Second one, not before 3 s.", "at": 3.0}],
         "fr": ["Première phrase.", "Deuxième."]}
      ]
    }

For each language the script:
  1. synthesises every cue (sentence), after applying the pronunciation lexicon
     `lexicon.json` next to script.json — subtitles keep the original text;
     a `[[…]]` value is a raw IPA phoneme string (Kokoro and Azure only);
  2. computes each scene's duration: max(min, lead + speech + tail).
     The voice sets the pace; the animation adapts to it;
  3. writes `audio/<lang>.m4a` (AAC mono, loudness-normalised) and `timing.js`
     (`window.VIDEO_TIMING`, read by engine/engine.js).

Engines (`--engine`, or "engine" in script.json):
  - `kokoro`  Kokoro-82M, Apache-2.0 weights, local ONNX, CPU is enough (default).
              Model files: `--download-model` fetches them into ~/.cache/kokoro-onnx.
  - `azure`   Azure AI Speech, official free tier F0 (500k characters/month);
              env AZURE_SPEECH_KEY and AZURE_SPEECH_REGION. Licensed for publishing.
  - `espeak`  espeak-ng: robotic, but no licence on your audio — the zero-cost
              fallback you may publish (Linux, macOS, Windows).
  - `say`     macOS voices: perfect for drafts and timing passes, but Apple's
              licence (macOS SLA §2F) forbids publishing system-voice recordings.

Synthesised cues are cached in ~/.cache/canvas-video/tts: re-running only redoes
what changed. Nothing gets installed in your project:

    uv run --with kokoro-onnx --with soundfile narrate.py videos/my-video
    uv run --with kokoro-onnx --with soundfile narrate.py videos/my-video --lang fr
    python3 narrate.py videos/my-video --engine say          # draft voice, stdlib only
    python3 narrate.py --check videos                        # CI: is every timing.js up to date?
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import wave
from array import array
from pathlib import Path

MODEL_DIR = Path.home() / ".cache" / "kokoro-onnx"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
CACHE = Path.home() / ".cache" / "canvas-video" / "tts"
SR = 24000
LEAD, GAP, TAIL = 0.5, 0.35, 0.6

# Default voice per language and engine. Override per video with "voices" in script.json.
ENGINES = {
    "kokoro": {  # grades from hexgrad/Kokoro-82M VOICES.md: English is excellent, others are weaker
        "en": {"voice": "af_heart", "lang": "en-us", "speed": 1.0},
        "en-gb": {"voice": "bm_george", "lang": "en-gb", "speed": 1.0},
        "fr": {"voice": "ff_siwis", "lang": "fr-fr", "speed": 1.0},
        "it": {"voice": "im_nicola", "lang": "it", "speed": 1.0},
        "es": {"voice": "em_alex", "lang": "es", "speed": 1.0},
        "pt": {"voice": "pm_alex", "lang": "pt-br", "speed": 1.0},
        "hi": {"voice": "hf_alpha", "lang": "hi", "speed": 1.0},
        "ja": {"voice": "jf_alpha", "lang": "ja", "speed": 1.0},
        "zh": {"voice": "zf_xiaoxiao", "lang": "cmn", "speed": 1.0},
    },
    "azure": {  # the multilingual neural voices: they also pronounce English words in a French sentence
        "en": {"voice": "en-US-AndrewMultilingualNeural", "lang": "en-US", "rate": "+0%"},
        "fr": {"voice": "fr-FR-RemyMultilingualNeural", "lang": "fr-FR", "rate": "+0%"},
        "it": {"voice": "it-IT-GiuseppeMultilingualNeural", "lang": "it-IT", "rate": "+0%"},
        "es": {"voice": "es-ES-TristanMultilingualNeural", "lang": "es-ES", "rate": "+0%"},
        "de": {"voice": "de-DE-FlorianMultilingualNeural", "lang": "de-DE", "rate": "+0%"},
        "pt": {"voice": "pt-BR-MacerioMultilingualNeural", "lang": "pt-BR", "rate": "+0%"},
    },
    "espeak": {
        "en": {"voice": "en-us", "speed": 165}, "fr": {"voice": "fr-fr", "speed": 160},
        "it": {"voice": "it", "speed": 160}, "es": {"voice": "es", "speed": 160},
        "de": {"voice": "de", "speed": 160}, "pt": {"voice": "pt-br", "speed": 160},
    },
    "say": {
        "en": {"voice": "Samantha", "rate": 185}, "fr": {"voice": "Thomas", "rate": 185},
        "it": {"voice": "Alice", "rate": 185}, "es": {"voice": "Mónica", "rate": 185},
        "de": {"voice": "Anna", "rate": 185}, "pt": {"voice": "Luciana", "rate": 185},
    },
}
IPA_ENGINES = {"kokoro", "azure"}


def load_script(video: Path) -> dict:
    data = json.loads((video / "script.json").read_text(encoding="utf-8"))
    ids = [s["id"] for s in data["scenes"]]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{video}/script.json: duplicate scene ids")
    return data


def langs_of(data: dict) -> list[str]:
    return data.get("langs") or ["en"]


def voice_cfg(data: dict, engine: str, lang: str) -> dict:
    cfg = dict(ENGINES[engine].get(lang) or {})
    cfg.update(data.get("voices", {}).get(engine, {}).get(lang, {}))
    if not cfg.get("voice"):
        raise SystemExit(f"No default {engine} voice for '{lang}': set \"voices\": "
                         f"{{\"{engine}\": {{\"{lang}\": {{...}}}}}} in script.json")
    return cfg


def cues_of(scene: dict, lang: str) -> list[dict]:
    return [{"text": c, "at": None} if isinstance(c, str) else {"text": c["text"], "at": c.get("at")}
            for c in scene.get(lang, [])]


def lexicon(video: Path, lang: str, engine: str) -> dict:
    """`<lang>` entries, overridden by `<lang>@<engine>` ones; `_doc` keys are notes."""
    f = video / "lexicon.json"
    if not f.exists():
        return {}
    raw = json.loads(f.read_text(encoding="utf-8"))
    lex = {**raw.get(lang, {}), **raw.get(f"{lang}@{engine}", {})}
    return {k: v for k, v in lex.items() if not k.startswith("_")}


def pronounce(s: str, lex: dict, engine: str) -> str:
    """Whole-word, case-sensitive substitution, longest first, in a single pass.

    Kokoro receives `[[ipa]]`, Azure `[[ipa|word]]` (SSML <phoneme> keeps the word),
    engines without IPA read the original word."""
    out = {}
    for src, val in lex.items():
        m = re.fullmatch(r"\[\[(.+)\]\]", val)
        out[src] = (f"[[{m.group(1)}|{src}]]" if engine == "azure" else val if engine in IPA_ENGINES else src) if m else val
    if not out:
        return s
    alt = "|".join(re.escape(k) for k in sorted(out, key=len, reverse=True))
    return re.sub(rf"(?<![\w/])(?:{alt})(?!\w)", lambda m: out[m.group(0)], s)


def digest(video: Path, data: dict, lang: str, engine: str) -> str:
    """Fingerprint of everything that determines a language's timing."""
    payload = {"engine": engine, "voice": voice_cfg(data, engine, lang), "lex": lexicon(video, lang, engine),
               "lead": LEAD, "gap": GAP, "tail": TAIL,
               "scenes": [{"id": s["id"], "min": s.get("min"), "lead": s.get("lead"), "tail": s.get("tail"),
                           "cues": cues_of(s, lang)} for s in data["scenes"]]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def ffmpeg_to_pcm(src: Path, dst: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", str(SR), "-ac", "1",
                    "-sample_fmt", "s16", str(dst)], check=True)


def download_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        dst = MODEL_DIR / name
        if dst.exists():
            print(f"{dst} already there")
            continue
        print(f"downloading {MODEL_URL + name} …", file=sys.stderr)
        tmp = dst.with_suffix(".part")
        urllib.request.urlretrieve(MODEL_URL + name, tmp)
        tmp.replace(dst)
        print(dst)


class Kokoro:
    name = "kokoro"

    def __init__(self):
        self._k = None

    def model(self):
        if self._k is None:
            try:
                from kokoro_onnx import Kokoro as K
            except ImportError:
                raise SystemExit("kokoro-onnx missing: uv run --with kokoro-onnx --with soundfile narrate.py …")
            onnx, voices = MODEL_DIR / "kokoro-v1.0.onnx", MODEL_DIR / "voices-v1.0.bin"
            if not onnx.exists() or not voices.exists():
                raise SystemExit(f"Kokoro model missing from {MODEL_DIR}: run narrate.py --download-model")
            self._k = K(str(onnx), str(voices))
        return self._k

    def phonemes(self, text: str, lang: str) -> str:
        """espeak phonemes WITHOUT language-switch flags.

        By default espeak marks foreign words as `(en)kˈoʊtʃ(fr)` and kokoro-onnx only
        strips the brackets: a French voice then literally says "en … fr" around every
        English word. `remove-flags` keeps the foreign pronunciation, drops the flags."""
        import phonemizer
        from kokoro_onnx.tokenizer import Tokenizer, _espeak_lock
        tok, out = self.model().tokenizer, []
        for i, part in enumerate(re.split(r"\[\[(.+?)\]\]", text)):
            if i % 2:
                out.append(part)  # raw IPA from the lexicon
            elif part.strip():
                with _espeak_lock:
                    out.append(phonemizer.phonemize(Tokenizer.normalize_text(part), lang, preserve_punctuation=True,
                                                    with_stress=True, language_switch="remove-flags").strip())
        ph = re.sub(r"\s+", " ", " ".join(out))
        return "".join(p for p in ph if p in tok.vocab).strip()

    def synth(self, text: str, cfg: dict, out: Path) -> None:
        import soundfile as sf
        samples, sr = self.model().create(self.phonemes(text, cfg["lang"]), voice=cfg["voice"],
                                          speed=cfg.get("speed", 1.0), lang=cfg["lang"], is_phonemes=True)
        sf.write(out, samples, sr, subtype="PCM_16")


class Azure:
    name = "azure"

    def synth(self, text: str, cfg: dict, out: Path) -> None:
        import time
        import urllib.error
        from xml.sax.saxutils import escape, quoteattr
        key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION")
        if not key or not region:
            raise SystemExit("azure engine: set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION (free tier F0).")
        body = []
        for i, part in enumerate(re.split(r"\[\[(.+?)\]\]", text)):
            if i % 2:
                ipa, _, word = part.partition("|")
                body.append(f'<phoneme alphabet="ipa" ph={quoteattr(ipa)}>{escape(word or ipa)}</phoneme>')
            else:
                body.append(escape(part))
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{cfg["lang"]}">'
                f'<voice name="{cfg["voice"]}"><prosody rate="{cfg.get("rate", "+0%")}">{"".join(body)}</prosody></voice></speak>')
        req = urllib.request.Request(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode(),
                                     headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                                              "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm", "User-Agent": "canvas-video"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    out.write_bytes(r.read())
                return
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 5:  # F0 allows ~20 requests/minute
                    time.sleep(float(e.headers.get("Retry-After") or 15))
                    continue
                raise SystemExit(f"Azure: HTTP {e.code} for «{text[:60]}» — {e.read()[:200]!r}")


class Espeak:
    name = "espeak"

    def synth(self, text: str, cfg: dict, out: Path) -> None:
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            raise SystemExit("espeak-ng not found (brew install espeak-ng / apt install espeak-ng).")
        subprocess.run([exe, "-v", cfg["voice"], "-s", str(cfg["speed"]), "-w", str(out), text], check=True)


class Say:
    name = "say"

    def synth(self, text: str, cfg: dict, out: Path) -> None:
        if not shutil.which("say"):
            raise SystemExit("`say` is macOS only — try --engine espeak.")
        with tempfile.TemporaryDirectory() as tmp:
            aiff = Path(tmp) / "a.aiff"
            subprocess.run(["say", "-v", cfg["voice"], "-r", str(cfg["rate"]), "-o", str(aiff), text], check=True)
            ffmpeg_to_pcm(aiff, out)


ENGINE_CLASSES = {c.name: c for c in (Kokoro, Azure, Espeak, Say)}


def speak(engine, text: str, cfg: dict) -> array:
    """One cue -> 24 kHz mono PCM, through the cache."""
    path = CACHE / f"{hashlib.sha256(json.dumps([engine.name, text, cfg], sort_keys=True).encode()).hexdigest()[:24]}.wav"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.wav"
            engine.synth(text, cfg, raw)
            ffmpeg_to_pcm(raw, path)
    with wave.open(str(path), "rb") as w:
        return array("h", w.readframes(w.getnframes()))


def build_lang(video: Path, data: dict, lang: str, engine) -> dict:
    cfg, lex = voice_cfg(data, engine.name, lang), lexicon(video, lang, engine.name)
    plan, start, clips = [], 0.0, []
    for sc in data["scenes"]:
        cur, cues = sc.get("lead", LEAD), []
        for c in cues_of(sc, lang):
            pcm = speak(engine, pronounce(c["text"], lex, engine.name), cfg)
            if c["at"] is not None:
                cur = max(cur, float(c["at"]))
            dur = len(pcm) / SR
            cues.append({"s": round(cur, 3), "e": round(cur + dur, 3), "text": c["text"]})
            clips.append((start + cur, pcm))
            cur += dur + GAP
        speech_end = (cues[-1]["e"] if cues else 0) + sc.get("tail", TAIL)
        d = round(max(float(sc.get("min", 3.0)), speech_end), 3)
        item = {"id": sc["id"], "start": round(start, 3), "d": d, "cues": cues}
        if sc.get("chapter"):
            item["chapter"] = sc["chapter"][lang] if isinstance(sc["chapter"], dict) else sc["chapter"]
        plan.append(item)
        start += d
    duration = round(start, 3)

    # the full track, every clip at its timeline offset
    track = array("h", bytes(2 * (int(duration * SR) + SR)))
    for at, clip in clips:
        i0 = int(at * SR)
        track[i0:i0 + len(clip)] = clip[:max(0, len(track) - i0)]
    (video / "audio").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav, m4a = Path(tmp) / "voice.wav", Path(tmp) / f"{lang}.m4a"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(track.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-t", f"{duration:.3f}",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1",
                        "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(m4a)], check=True)
        shutil.move(str(m4a), str(video / "audio" / f"{lang}.m4a"))  # atomic: never a half-written track
    return {"digest": digest(video, data, lang, engine.name), "engine": engine.name, "voice": cfg["voice"],
            "duration": duration, "scenes": plan}


PREFIX = "/* Generated by canvas-video-skill scripts/narrate.py — do not edit. */\nwindow.VIDEO_TIMING = "


def read_timing(video: Path) -> dict:
    p = video / "timing.js"
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    if "window.VIDEO_TIMING = " not in txt:
        return {}
    return json.loads(txt.split("window.VIDEO_TIMING = ", 1)[1].rstrip().rstrip(";"))


def find_videos(paths: list[str]) -> list[Path]:
    """A path is a video folder (has script.json) or a folder of videos."""
    out = []
    for p in map(Path, paths or ["."]):
        out += [p] if (p / "script.json").exists() else sorted(q.parent for q in p.glob("*/script.json"))
    if not out:
        raise SystemExit(f"No script.json found under {', '.join(paths or ['.'])}")
    return out


def check(videos: list[Path]) -> int:
    bad = []
    for v in videos:
        data, timing = load_script(v), read_timing(v)
        for lang in langs_of(data):
            t = timing.get(lang)
            if not t:
                bad.append(f"{v} [{lang}]: no timing")
            elif t["digest"] != digest(v, data, lang, t["engine"]):
                bad.append(f"{v} [{lang}]: stale timing (script.json, voices or lexicon changed)")
            if not (v / "audio" / f"{lang}.m4a").exists():
                bad.append(f"{v} [{lang}]: audio/{lang}.m4a missing")
    print("\n".join(bad) or f"narration up to date ({len(videos)} video(s))", file=sys.stderr)
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("videos", nargs="*", help="video folders, or folders of videos (default: .)")
    ap.add_argument("--lang", action="append", help="language (repeatable, default: all in script.json)")
    ap.add_argument("--engine", choices=sorted(ENGINE_CLASSES), help="default: \"engine\" in script.json, else kokoro")
    ap.add_argument("--check", action="store_true", help="only verify timing.js and audio are up to date (stdlib only)")
    ap.add_argument("--download-model", action="store_true", help="fetch the Kokoro model files (~340 MB) and exit")
    args = ap.parse_args(argv)
    if args.download_model:
        download_model()
        return 0
    videos = find_videos(args.videos)
    if args.check:
        return check(videos)
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found in PATH (brew install ffmpeg / apt install ffmpeg).")
    engines = {}
    for v in videos:
        data, timing = load_script(v), read_timing(v)
        name = args.engine or data.get("engine", "kokoro")
        engine = engines.setdefault(name, ENGINE_CLASSES[name]())
        for lang in args.lang or langs_of(data):
            timing[lang] = build_lang(v, data, lang, engine)
            print(f"{v.name} [{lang}] {timing[lang]['duration']:.1f} s ({engine.name}/{timing[lang]['voice']})")
        (v / "timing.js").write_text(PREFIX + json.dumps(timing, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
