/* Scenes of a canvas video (see ../engine/engine.js and the canvas-video skill).
 *
 * Each scene is fn(t, d, cues): t = local time in seconds, d = scene duration,
 * cues = the spoken sentences [{s, e, text}] from timing.js. Hook animations onto
 * at(cues, i) — the start of sentence i — so they follow the voice in every language.
 * Rule: a pure function of t. No Math.random() (use rng(seed)), no Date.now().
 */
"use strict";

/* On-screen strings per language, available as S.<key> in scenes (English is the fallback). */
const STR = {
  en: { k1: "CANVAS VIDEO", h1: "This is not a video file.", sub: "Every frame is drawn from t alone.", k2: "YOUR TURN", h2: "Edit script.json, narrate, watch." },
};

function sIntro(t, d, cues) {
  kicker(S.k1, seg(t, 0.1, 0.6));
  headline(S.h1, seg(t, 0.2, 0.9), 150, 52);
  const a1 = at(cues, 1, 2.5);                       // second sentence starts here
  text(S.sub, 80, 200, { size: 22, color: C.soft, alpha: seg(t, a1, a1 + 0.5) });
  // a clock that only depends on t: scrub the player and it follows
  const cx = 900, cy = 420, r = 130, k = outBack(seg(t, a1, a1 + 0.8));
  ring(cx, cy, r * k, C.accent, 3);
  const a = -Math.PI / 2 + (t - a1) * 1.2;
  if (k > 0) line([[cx, cy], [cx + Math.cos(a) * r * 0.8 * k, cy + Math.sin(a) * r * 0.8 * k]], C.ink, 4);
  text(`t = ${t.toFixed(2)} s`, cx, cy + r + 50, { size: 18, font: MONO, color: C.faint, align: "center", alpha: k });
}

function sOutro(t, d, cues) {
  kicker(S.k2, seg(t, 0.1, 0.6));
  headline(S.h2, seg(t, 0.2, 0.9), 150, 52);
  terminal(80, 260, 760, 200, t, [
    { p: "$ ", s: "uv run --with kokoro-onnx --with soundfile narrate.py .", a: 0.6, b: 1.8 },
    { p: "", s: "intro [en] 6.1 s (kokoro/af_heart)", a: 2.0, c: C.good },
    { p: "$ ", s: "uv run --with playwright render.py . --sheet", a: 2.6, b: 3.6 },
  ], { title: "zsh" });
}

VIDEO.create({
  title: { en: "Hello, canvas video" },
  kicker: { en: "A canvas video" },
  langs: ["en"],
  // theme: { bg: "#…", accent: "#…" },   // override engine colours here
  strings: STR,
  poster: "intro",
  scenes: { intro: sIntro, outro: sOutro },
});
