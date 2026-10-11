# Scene recipes

Patterns that worked across ~25 videos. Copy, adapt, keep them pure functions of `t`.

## Title that follows the voice

```js
function sIntro(t, d, cues) {
  kicker(S.k1, seg(t, 0.1, 0.6));
  headline(S.h1, seg(t, 0.25, 0.9));
  const a1 = at(cues, 1, 3);                         // 2nd sentence
  para(S.lead, 80, 200, 700, { size: 22, color: C.soft, alpha: seg(t, a1, a1 + 0.5) });
}
```

## Staggered list (items appear one after another)

```js
ITEMS.forEach((it, i) => {
  const k = seg(t, 0.4 + i * 0.15, 0.9 + i * 0.15);
  pill(it, 80, 260 + i * 56, { alpha: k });
});
```

## Counter rolling up to a real number

```js
const k = outCubic(seg(t, a1 + 0.3, a1 + 3));
text(Math.round(10049 * k).toLocaleString(LANG), 1040, 330, { size: 96, weight: 800, font: SORA, align: "right" });
```

Print the test condition next to it (`text(S.cond, …, { size: 12, font: MONO, color: C.faint })`).

## Before / after bars

```js
rows.forEach(([name, before, after], i) => {
  const y = 220 + i * 120, kb = seg(t, 0.4 + i * 0.5, 1.4 + i * 0.5), ka = seg(t, 1.6 + i * 0.5, 2.6 + i * 0.5);
  panel(300, y, 660 * before / max * outCubic(kb), 28, { r: 4, fill: C.warn, stroke: false });
  panel(300, y + 36, 660 * after / max * outCubic(ka), 28, { r: 4, fill: C.good, stroke: false });
});
```

Keep bar max width so the longest bar's label never reaches the right-hand column.

## Something moving through a gate / proxy (clipped)

```js
ctx.save(); ctx.beginPath(); ctx.rect(gateX + 44, 0, W, H); ctx.clip();   // visible right of the gate only
panel(lerp(1220, gateX - 160, inOut(k)), y, 180, 140, { fill: C.warn });
ctx.restore();
drawGate(gateX, y);                                                       // drawn AFTER: on top
```

## Terminal session

```js
terminal(170, 360, 940, 210, t, [
  { p: "$ ", s: "brew install my-tool", a: a0 + 0.2, b: a0 + 1.0 },
  { p: "", s: "✓ installed", a: a0 + 1.2, c: C.good },
  { p: "$ ", s: "my-tool init", a: a0 + 1.6, b: a0 + 2.2 },
], { title: "zsh" });
```

## Looping motion that is still deterministic

```js
const loops = Math.max(0, t - a2) / 1.1;    // a request leaves every 1.1 s after sentence 2
const dx = (loops % 1) * 440;
const n = Math.floor(loops) + 1;            // "request #n"
```

## Caught / highlighted

`highlight(x, y, w, h, k, color)` for "look here"; for "caught" (a secret, an error),
corner brackets in a red used for nothing else read instantly.

## Screenshots of the real product

Load images once and draw them with `ctx.drawImage`; wait for them before the first
frame by adding a promise to `window.videoReady` in your scenes file, or keep
screenshots out and redraw the UI schematically (lighter, translatable, always sharp).
If you show real UI, use **fictional demo data** and say so on screen.

## Checklist before showing the user

- [ ] Every number comes from the project, with its condition on screen
- [ ] Opt-in / experimental features are labelled as such
- [ ] `render.py --sheet` reviewed in **every** language (longest strings!)
- [ ] `narration-lexicon` verify passes (or remaining diffs are Whisper's, not the voice's)
- [ ] `narrate.py --check` passes
