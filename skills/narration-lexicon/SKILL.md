---
name: narration-lexicon
description: Find and fix mispronounced words in a synthetic voice-over by transcribing the narration with Whisper, diffing it against the script, A/B-testing spellings or IPA, and maintaining the video's lexicon.json — instead of guessing by ear. Use after narrating a canvas-video (or any script.json + timing.js + audio/<lang>.m4a video), when the user says the voice mispronounces a word, acronym, brand or product name, before publishing a narrated video, or when adding a language.
---

# narration-lexicon

After three listens you hear what you expect. A speech-to-text model doesn't. This
skill closes the loop: **transcribe → diff → try variants → add to the lexicon →
re-narrate → transcribe again**, until the transcript matches the script.

It works on canvas-video folders (`script.json`, `timing.js`, `audio/<lang>.m4a`,
`lexicon.json`) and uses the `canvas-video` skill's `narrate.py` (same plugin) for
the voice. Scripts are in this skill's `scripts/` folder; first run downloads the
Whisper `small` model (~470 MB).

## The loop

### 1. Verify

```bash
uv run --with faster-whisper --with num2words scripts/verify.py <video> [--lang fr]
```

Every sentence is cut out of the track with the timestamps in `timing.js`,
transcribed, normalised (numbers → words, case, punctuation, accents) and compared
with the script **and** with the lexicon-respelled text. Output per flagged cue:

```
✗ [en] gate @20.5s  0.86
    script: LeanProxy is one local Go binary that sits between your AI client and …
    heard : Lean Proxy is one local go binary that sits between your iClient and …
      «ai client» → «iclient»
```

Exit code 1 if anything is flagged; `--json` for a machine-readable report;
`--threshold` (default 0.9); `--all` to see passing cues too.

### 2. Triage every diff — voice problem or Whisper's prior?

Not every diff is a mispronunciation. Before changing anything, classify:

- **Real voice problem** → fix it: an acronym read as a word ("AI" → "iClient"),
  letters glued ("binaire Go" → "binergo"), a brand in the wrong language
  ("Homebrew" → "Chromebook" in French), a number read wrongly, a word skipped.
- **Homophone / spelling only** → leave it: "Mesuré" vs "Mesurée", "surcoût" vs
  "sur coût", "qu'ils servent" vs "qu'il serve". Same sound, Whisper picked a spelling.
- **Whisper's language prior** → listen once, usually leave it: a foreign brand
  in an Italian sentence comes back as an Italian-looking word ("LeanProxy" →
  "l'improxi") even when the voice is right. `try_words.py` makes the call easy:
  if no spelling ever comes back "right", it's the prior.

Tell the user which diffs you left and why.

### 3. Try variants on a short carrier sentence

```bash
uv run --with kokoro-onnx --with soundfile --with faster-whisper --with num2words \
  scripts/try_words.py <video> --lang fr \
  "Installez-le avec Homebrew, lancez" "Installez-le avec Home Brew, lancez" "Installez-le avec [[hˈoʊmbɹuː]], lancez"
```

Same engine and voice as the video; each variant is saved as a WAV (to listen) and
transcribed. Keep the variant that comes back closest. Strategies, in order:

1. **Spaces between letters for acronyms**: `"MCP": "M C P"`, `"AI": "A I"`.
   Some languages need the letter names: Italian `"MCP": "emme ci pi"`.
2. **Split compound brands**: `"LeanProxy": "Lean Proxy"`, `"Homebrew": "Home Brew"`.
3. **Respell for the target language's phonetics**: French `"migrate": "maïgrète"`.
4. **Raw IPA** (Kokoro and Azure only): `"AI": "[[ˌeɪˈaɪ]]"`, `"LeanProxy": "[[lˈin prˈɔksi]]"`.
   See `references/ipa-cheatsheet.md`.
5. **Rewrite the sentence** when nothing works: "binaire Go" → "binaire écrit en Go".
   That's a `script.json` change (subtitles change too) — fine, and often the best fix.

### 4. Add the entry to `lexicon.json`

```json
{
  "en": {"MCP": "M C P", "AI": "[[ˌeɪˈaɪ]]"},
  "fr": {"Homebrew": "Home Brew"},
  "en@espeak": {"AI": "A I"}
}
```

- Keys are **whole words, case-sensitive**; longest keys win; one pass (a
  replacement is never re-processed).
- Spoken text only: subtitles keep the original spelling.
- `<lang>@<engine>` overrides `<lang>` for one engine — needed because IPA is
  ignored by engines that can't read it (they fall back to the original word).
- Put a `"_doc"` key to explain non-obvious entries.

### 5. Re-narrate and verify again

```bash
uv run --with kokoro-onnx --with soundfile <canvas-video>/scripts/narrate.py <video> --lang fr
uv run --with faster-whisper --with num2words scripts/verify.py <video> --lang fr
```

Only the changed sentences are re-synthesised (cache). Stop when every remaining
diff is in the "leave it" categories. Then run `narrate.py --check` so CI agrees.

## Tips

- Write numbers in words in `script.json` from the start; verify normalises digits
  in the transcript, so "318" heard vs "three hundred and eighteen" written passes.
- Check every language: Kokoro's English is excellent, its French and Italian voices
  are weaker and need more entries.
- An engine switch (e.g. Kokoro → Azure) needs a fresh verify: lexicons are
  engine-sensitive. Multilingual Azure voices pronounce English words in French
  sentences by themselves, so their lexicon is usually shorter.
- Keep the entries: a project's lexicon is reusable across all its videos.
