"""Speech-to-text helpers shared by verify.py and try_words.py (faster-whisper, local)."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

SR = 16000
_MODEL = {}


def model(size: str = "small"):
    if size not in _MODEL:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise SystemExit("faster-whisper missing: uv run --with faster-whisper --with num2words <script> …")
        _MODEL[size] = WhisperModel(size, device="cpu", compute_type="int8")
    return _MODEL[size]


def load_audio(path: Path):
    """Any audio file -> float32 mono 16 kHz numpy array (decoded by ffmpeg, not PyAV)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(audio, lang: str, size: str = "small") -> str:
    segs, _ = model(size).transcribe(audio, language=lang.split("-")[0], beam_size=5, condition_on_previous_text=False,
                                     vad_filter=False)
    return " ".join(s.text.strip() for s in segs).strip()


def _num_words(tok: str, lang: str) -> str:
    try:
        from num2words import num2words
    except ImportError:
        return tok
    clean = tok.replace(",", "").replace(" ", "").replace(" ", "")
    if lang.startswith(("fr", "it", "es", "de", "pt")):
        clean = tok.replace(".", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        val = float(clean) if "." in clean else int(clean)
        return num2words(val, lang=lang.split("-")[0])
    except (ValueError, NotImplementedError, OverflowError):
        return tok


def words(s: str, lang: str) -> list[str]:
    """Normalise for comparison: numbers to words, lowercase, no punctuation or accents, % -> percent."""
    s = s.replace("’", "'").replace("%", " percent ")
    s = re.sub(r"\d[\d.,  ]*\d|\d", lambda m: " " + _num_words(m.group(0).strip(), lang) + " ", s)
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[-'’]", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return s.split()


def compare(expected: str, heard: str, lang: str) -> tuple[float, list[tuple[str, str]]]:
    """Similarity 0..1 and the word-level differences [(expected words, heard words)]."""
    a, b = words(expected, lang), words(heard, lang)
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    diffs = [(" ".join(a[i1:i2]), " ".join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    return sm.ratio(), diffs


def read_timing(video: Path) -> dict:
    txt = (video / "timing.js").read_text(encoding="utf-8")
    return json.loads(txt.split("window.VIDEO_TIMING = ", 1)[1].rstrip().rstrip(";"))


def load_narrate(path: Path | None = None):
    """canvas-video's narrate.py (same plugin), for its engines, voices and lexicon logic."""
    path = path or Path(__file__).resolve().parents[2] / "canvas-video" / "scripts" / "narrate.py"
    if not path.exists():
        raise SystemExit(f"narrate.py not found at {path}: pass --narrate /path/to/canvas-video/scripts/narrate.py")
    spec = importlib.util.spec_from_file_location("narrate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def spoken_text(narrate, video: Path, text: str, lang: str, engine: str) -> str:
    """The text as respelled by the lexicon (IPA entries left as the original word)."""
    lex = {k: v for k, v in narrate.lexicon(video, lang, engine).items() if not v.startswith("[[")}
    return narrate.pronounce(text, lex, "espeak")
