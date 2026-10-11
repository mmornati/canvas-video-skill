# Engine API (`engine/engine.js`)

Everything below is a global in `scenes.js`. Canvas: **1280×720 logical units**
(`W`, `H`), scaled for the output resolution. `ctx` is the raw 2D context when you
need more than the helpers.

## Entry point

```js
VIDEO.create({
  title:   { en: "…", fr: "…" },        // page title / aria-label
  kicker:  { en: "…" },                 // small line above the title (full-page mode)
  langs:   ["en", "fr"],                // must match script.json
  theme:   { bg, bg2, panel, panel2, line, ink, soft, faint, accent, accent2,
             good, warn, bad, deep, term, termInk },   // any subset of colours
  strings: { en: { key: "…" }, fr: { … } },          // exposed as S.key, English fallback
  background: t => { … },               // optional, replaces the default gradient + grid
  poster:  "scene-id",                  // frame shown before Play (last second of that scene)
  fonts:   ['700 20px "My Font"'],      // extra fonts to wait for before the first frame
  scenes:  { "scene-id": fn, … },       // fn(t, d, cues)
});
```

A scene function receives `t` (seconds since the scene started), `d` (its duration)
and `cues` (`[{s, e, text}]`, sentence start/end in scene time). Scenes cross-fade
over 0.45 s; you don't handle that.

Other globals: `LANG` (current language), `S` (strings), `C` (colours),
`SORA`, `INTER`, `MONO` (font stacks), `VIDEO.plan` (timeline of the current language).

## Time and easing

| Helper | Returns |
|---|---|
| `seg(t, a, b)` | progress 0→1 of `t` between `a` and `b`, clamped — the workhorse |
| `at(cues, i, fallback)` / `atEnd(cues, i, fallback)` | start / end of sentence `i` |
| `outCubic(k)`, `inOut(k)`, `outBack(k)` | easings (outBack overshoots: pops) |
| `clamp(v, a=0, b=1)`, `lerp(a, b, k)` | the usual |
| `typed(s, k)` | the first `k` (0–1) of string `s` — typewriter |
| `rng(seed)` | deterministic random generator (mulberry32): `const R = rng(42); R()` |
| `hash(s)` | 32-bit hash of a string, handy as a seed |
| `fmt(seconds)` | `m:ss` |

## Drawing

All take an optional `o` object; `o.alpha` multiplies opacity.

| Helper | Notes |
|---|---|
| `text(s, x, y, {size, weight, font, color, align, base, spacing, alpha})` | monospace text never gets ligatures |
| `para(s, x, y, maxW, {size, lh, k, …})` | wrapped paragraph, returns its height; `k` = typewriter |
| `measure(s, size, weight, font)`, `wrap(s, maxW, size, …)` | text metrics |
| `kicker(s, k, x=80, y=86)` | small uppercase mono label in the accent colour |
| `headline(s, k, y=132, size=42, x=80)` | big title sliding up as `k` goes 0→1 |
| `panel(x, y, w, h, {r, fill, stroke, lw, shadow})` | rounded box (`stroke: false` for none) |
| `pill(s, x, y, {align, size, fill, stroke, color, font})` | badge, returns its width |
| `terminal(x, y, w, h, t, lines, {title, size, lh})` | lines `[{p: "$ ", s: "cmd", a, b, c}]` appear at `a`, typed until `b`, colour `c` |
| `line(points, color, lw, alpha, dash)`, `partial(points, k)` | polyline; `partial` cuts it at `k` of its length (draw-on effect) |
| `arrow(x1, y1, x2, y2, k, color)` | grows with `k`, head appears at the end |
| `packets(x1, y1, x2, y2, t, {n, period, color, r})` | dots flowing along a wire |
| `dot(x, y, r, color, alpha)`, `ring(x, y, r, color, lw, alpha)` | circles |
| `check(x, y, size, color, k)`, `cross(x, y, size, color, k)` | animated ✓ / ✗ |
| `highlight(x, y, w, h, k, color)` | glowing frame closing in on an area |
| `callout(s, x, y, tx, ty, k)` | label with a leader line to `(tx, ty)` |
| `rr(x, y, w, h, r)` | rounded-rect path (then `ctx.fill()` / `ctx.clip()`) |
| `background(t)` | the default background, if you want to draw over it |

## Player and export hooks

- `window.renderFrame(t)` draws frame `t`; `window.videoReady` resolves when fonts
  are loaded; `window.DURATION` is the length in the current language. `render.py`
  uses them; you can too (`?capture=1` hides the UI).
- The audio element is the master clock while it plays: no drift.
- Keyboard: Space play/pause, ←/→ ±5 s, `c` subtitles.
