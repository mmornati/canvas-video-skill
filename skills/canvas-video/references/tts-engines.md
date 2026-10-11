# Free text-to-speech for published videos (checked October 2026)

The question is never only "does it sound good?" but **"may I publish the audio?"**
Read the licence of the *weights* (not just the code) and the service terms.

## Built into narrate.py

| `--engine` | Audio licence | Notes |
|---|---|---|
| `kokoro` (default) | Apache-2.0: publish freely, commercial included | 82M params, CPU. English excellent (28 voices); French 1 voice (B-), Italian 2 (C), also es, pt, hi, ja, zh. IPA via `[[…]]` in the lexicon. |
| `azure` | Licensed service, free tier F0: 500,000 characters/month | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`. The Microsoft neural voices (the ones edge-tts used), legally. IPA via SSML `<phoneme>`. ~20 requests/min on F0 (retries built in). |
| `espeak` | GPL engine, no claim on your audio | Robotic, but the zero-cost fallback you may publish. Linux/macOS/Windows. |
| `say` | **Not publishable** (macOS SLA §2F: system voices for "personal, non-commercial use", no publishing) | Drafts and timing passes only. |

Adding an engine = a class with `name` and `synth(text, cfg, out_wav)` in
`scripts/narrate.py`, plus default voices in `ENGINES`.

## Other local, open-weight options

| Model | Audio licence | Languages | Notes |
|---|---|---|---|
| Chatterbox Multilingual (Resemble AI) | MIT; inaudible "Perth" watermark | 23 incl. en/fr/it | Voice cloning; Apple Silicon (MPS). `pip install chatterbox-tts` |
| Kyutai Pocket TTS | CC-BY-4.0: **credit Kyutai**; no cloning without consent | en, fr, it, de, es, pt | 100M, real time on CPU; gated download |
| Kyutai TTS 1.6B | CC-BY-4.0 (credit) | en, fr | Very good French; MLX on Mac (`moshi-mlx`) |
| Qwen3-TTS | Apache-2.0 | 10 incl. en/fr/it | Strong, wants a GPU |
| Piper | Engine GPL-3.0; **each voice has its own dataset licence** | many | Check every voice's model card |
| kokoro-js | Apache-2.0 | English voices | Kokoro in Node / the browser |

**Non-commercial — do not use for product or marketing videos:** Fish Audio S2,
Voxtral TTS, F5-TTS weights, Spark-TTS, XTTS-v2 (Coqui is gone, no licence to buy),
OuteTTS 1B, Breeze TTS 2. VibeVoice is MIT but "research only" per Microsoft.

## Cloud free tiers

| Service | Free allowance | Notes |
|---|---|---|
| Azure AI Speech F0 | 500k chars/month | built in (`--engine azure`) |
| Google Cloud TTS | 1M chars/month Chirp 3 HD, 4M Standard, 4M WaveNet | billing account (card) required |
| Gemini API TTS | free tier on Flash TTS models | prompt-steerable voices; tight rate limits |
| Amazon Polly | credits for new accounts (≤ $200) | "12 months free" only for accounts before July 2025 |
| Cloudflare Workers AI (MeloTTS) | ~9 h of audio/day | fr/en, no it; dated quality |

Not usable for this on their free plans: **ElevenLabs** (no commercial use, must put
"elevenlabs.io" in the title), **Cartesia** (no commercial licence), **OpenAI** (no
free tier).

## Grey zone

- **edge-tts**: unofficial use of Edge's "Read aloud" endpoint, no licence for
  published audio; returns HTTP 403 from the EU since 2026-10-10
  (github.com/rany2/edge-tts/issues/490). Use Azure F0 for the same voices.
- **gTTS**: Google Translate endpoint, no licence, low quality.

## Picking

- English only → Kokoro.
- French/Italian, local → Chatterbox Multilingual, or Pocket TTS with credit.
- Best voices, free, licensed → Azure F0.
- Draft → `say`; final → anything above. Timings re-flow automatically.
