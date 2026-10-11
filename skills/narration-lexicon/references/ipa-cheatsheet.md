# IPA cheat sheet for lexicon entries

Kokoro reads the espeak-ng phoneme set; Azure reads standard IPA in SSML. Wrap the
phonemes in double brackets in `lexicon.json`: `"AI": "[[ˌeɪˈaɪ]]"`.

## Getting a starting point

Let espeak-ng tell you how it would say a word, then edit:

```bash
espeak-ng -q --ipa -v en-us "Homebrew"     # hˈoʊmbɹuː
espeak-ng -q --ipa -v fr-fr "migrate"      # miɡʁˈat  ← French reading, wrong
espeak-ng -q --ipa -v en-us "migrate"      # mˈaɪɡɹeɪt ← take the English one
```

A foreign word in a sentence: take its IPA **from the language it belongs to**
(`-v en-us` for an English brand in a French sentence) and put it in the entry of the
sentence's language (`"fr": {"migrate": "[[mˈaɪɡɹeɪt]]"}`).

## Stress and length

| Mark | Meaning | Example |
|---|---|---|
| `ˈ` | primary stress, before the syllable | `ˈproʊksi` |
| `ˌ` | secondary stress | `ˌeɪˈaɪ` (A-I) |
| `ː` | long vowel | `bɹuː` |

## Sounds that come up in tech names

| Sound | IPA | As in |
|---|---|---|
| "ay" | `eɪ` | **A**I, m**i**grate (2nd syllable) |
| "eye" | `aɪ` | A**I**, m**i**grate (1st syllable) |
| "oh" | `oʊ` | H**o**mebrew |
| "ee" | `i` / `iː` | L**ea**n |
| "oo" | `uː` | brew |
| English r | `ɹ` | b**r**ew |
| French r | `ʁ` | **r**outeur |
| Italian r | `r` | p**r**oxy (it) |
| "sh" / "ch" | `ʃ` / `tʃ` | **sh**ell, **ch**at |
| "j" (jay) | `dʒ` | **J**SON |
| French nasal | `ɑ̃`, `ɔ̃`, `ɛ̃` | en, on, in |

## Entries verified with Whisper (Kokoro)

```json
{
  "en": {"AI": "[[ˌeɪˈaɪ]]"},
  "it": {"LeanProxy": "[[lˈin prˈɔksi]]", "Homebrew": "[[hˈɔmbru]]"}
}
```

If IPA doesn't help after two tries, respell or rewrite the sentence instead (see
SKILL.md, strategies 1–5).
