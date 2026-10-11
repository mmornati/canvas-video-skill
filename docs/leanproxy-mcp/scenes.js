/* leanproxy-mcp in 80 seconds — the reference example of canvas-video-skill (see ../engine/engine.js).
 *
 * Each scene is fn(t, d, cues): t = local time in seconds, d = scene duration,
 * cues = spoken sentences [{s, e, text}] from timing.js. Animations hook onto
 * at(cues, i) so they follow the voice in every language.
 *
 * Visual identity: leanproxy-mcp's "checkpoint scanner" (DESIGN.md of the
 * project): amber = tokens you pay for, teal = what cleared, cobalt = objects,
 * red only for corner brackets around something caught.
 * Figures: README / docs/benchmark-results.md ("make harness", commit 430f9a8,
 * 5 mock servers, 118 tools).
 */
"use strict";

const LP = {
  ground: "#f3f5f1", ground2: "#e7ebe4", paper: "#fbfcfa", ink: "#0f1a3a", ink2: "#3a4566", ink3: "#5d6784",
  rule: "#cfd5cc", amber: "#f08a24", amberText: "#a8520a", teal: "#1f9e78", tealText: "#0f6e52",
  cobalt: "#2743c9", red: "#e11d2a",
};

const SERVERS = [
  { name: "github", tools: 42 }, { name: "jira", tools: 24 }, { name: "slack", tools: 14 },
  { name: "garmin", tools: 28 }, { name: "postgres", tools: 10 },
];

const STR = {
  en: {
    k1: "THE SCHEMA TAX", h1: "Every request carries every tool.", client: "AI client", model: "Model", prompt: "your prompt",
    schemas: "tool schemas", req: "request",
    k2: "BEFORE THE FIRST TOOL CALL", h2: "~10,000 tokens, every turn.", tok: "tokens", cond2: "make harness · 5 mock MCP servers · 118 tools",
    pay: "you pay for it", room: "room left to think", ctx: "context window",
    k3: "ONE LOCAL GO BINARY", h3: "One proxy in front of every server.", single: "1 server: leanproxy", gateCap: "stdio · Streamable HTTP · SSE",
    k4: "ROUTER MODE", h4: "Four tools instead of a hundred and eighteen.", routerFor: "for clients without their own tool search",
    query: "\"how did I sleep last night?\"", static: "static load −96.8%",
    k5: "RESPONSE GOVERNOR · OPT-IN", h5: "Keep the fields that matter.", cond5: "large results, max_tokens 4000 · make harness", page: "read_result → page back the rest",
    k6: "FIREWALL", h6: "Secrets stay home.", leaked: "0 of 3 planted secrets leaked", redact: "redaction on by default, both directions",
    pinned: "pinned", changed: "definition changed", inj: "injection screening · local · opt-in",
    k7: "MEASURED", h7: "Fewer tokens per session.", native: "native MCP", lean: "leanproxy (search_tools)",
    s1: "Morning sport", s2: "Dev workflow", s3: "Full day", over: "proxy overhead 0.74 ms p95", cond7: "make harness · commit 430f9a8 · upper bounds",
    k8: "TRY IT", h8: "brew install, migrate, done.",
  },
  fr: {
    k1: "LA TAXE DES SCHÉMAS", h1: "Chaque requête embarque tous les outils.", client: "Client IA", model: "Modèle", prompt: "votre prompt",
    schemas: "schémas d'outils", req: "requête",
    k2: "AVANT LE PREMIER APPEL D'OUTIL", h2: "~10 000 tokens, à chaque tour.", tok: "tokens", cond2: "make harness · 5 serveurs MCP simulés · 118 outils",
    pay: "vous le payez", room: "place pour réfléchir", ctx: "fenêtre de contexte",
    k3: "UN BINAIRE GO, EN LOCAL", h3: "Un proxy devant tous les serveurs.", single: "1 serveur : leanproxy", gateCap: "stdio · Streamable HTTP · SSE",
    k4: "MODE ROUTEUR", h4: "Quatre outils au lieu de cent dix-huit.", routerFor: "pour les clients sans recherche d'outils intégrée",
    query: "« comment ai-je dormi cette nuit ? »", static: "charge statique −96,8 %",
    k5: "RÉGULATEUR DE RÉPONSES · OPTIONNEL", h5: "Garder les champs utiles.", cond5: "gros résultats, max_tokens 4000 · make harness", page: "read_result → le reste, page par page",
    k6: "PARE-FEU", h6: "Les secrets restent chez vous.", leaked: "0 secret piégé sur 3 a fuité", redact: "masquage actif par défaut, dans les deux sens",
    pinned: "épinglé", changed: "définition modifiée", inj: "filtrage des injections · local · optionnel",
    k7: "MESURÉ", h7: "Moins de tokens par session.", native: "MCP natif", lean: "leanproxy (search_tools)",
    s1: "Sport du matin", s2: "Dév. au quotidien", s3: "Journée complète", over: "surcoût du proxy 0,74 ms p95", cond7: "make harness · commit 430f9a8 · bornes hautes",
    k8: "L'ESSAYER", h8: "brew install, migrate, c'est tout.",
  },
  it: {
    k1: "LA TASSA DEGLI SCHEMI", h1: "Ogni richiesta si porta dietro tutti gli strumenti.", client: "Client IA", model: "Modello", prompt: "il tuo prompt",
    schemas: "schemi degli strumenti", req: "richiesta",
    k2: "PRIMA DELLA PRIMA CHIAMATA", h2: "~10.000 token, a ogni turno.", tok: "token", cond2: "make harness · 5 server MCP simulati · 118 strumenti",
    pay: "lo paghi tu", room: "spazio per ragionare", ctx: "finestra di contesto",
    k3: "UN BINARIO GO, IN LOCALE", h3: "Un proxy davanti a tutti i server.", single: "1 server: leanproxy", gateCap: "stdio · Streamable HTTP · SSE",
    k4: "MODALITÀ ROUTER", h4: "Quattro strumenti invece di centodiciotto.", routerFor: "per i client senza ricerca degli strumenti integrata",
    query: "«come ho dormito stanotte?»", static: "carico statico −96,8%",
    k5: "REGOLATORE DELLE RISPOSTE · OPZIONALE", h5: "Tenere solo i campi utili.", cond5: "risultati grandi, max_tokens 4000 · make harness", page: "read_result → il resto, a pagine",
    k6: "FIREWALL", h6: "I segreti restano a casa.", leaked: "0 segreti trapelati su 3 piazzati", redact: "oscuramento attivo di default, nei due sensi",
    pinned: "bloccato", changed: "definizione modificata", inj: "filtro injection · locale · opzionale",
    k7: "MISURATO", h7: "Meno token per sessione.", native: "MCP nativo", lean: "leanproxy (search_tools)",
    s1: "Sport mattutino", s2: "Sviluppo", s3: "Giornata intera", over: "overhead del proxy 0,74 ms p95", cond7: "make harness · commit 430f9a8 · limiti superiori",
    k8: "PROVALO", h8: "brew install, migrate, fatto.",
  },
};

/* --------------------------- shared pieces -------------------------------- */
const num = n => n.toLocaleString(LANG === "fr" ? "fr-FR" : LANG === "it" ? "it-IT" : "en-US");

function bg(t) {
  ctx.fillStyle = LP.ground; ctx.fillRect(0, 0, W, H);
  // conveyor rails along the bottom: 3px rollers every 18px, slowly moving
  const off = (t * 24) % 18;
  ctx.save(); ctx.fillStyle = LP.rule;
  for (let x = -18 + off; x < W; x += 18) ctx.fillRect(x, 668, 3, 10);
  ctx.fillRect(0, 664, W, 2); ctx.fillRect(0, 680, W, 2);
  ctx.restore();
}

/* Red corner brackets: the only use of red, around something caught. */
function brackets(x, y, w, h, k, s = 12) {
  if (k <= 0) return;
  const p = 6 + 14 * (1 - outCubic(k));
  const [x0, y0, x1, y1] = [x - p, y - p, x + w + p, y + h + p];
  [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]].forEach(([cx, cy, dx, dy]) =>
    line([[cx + dx * s, cy], [cx, cy], [cx, cy + dy * s]], LP.red, 3, clamp(k)));
}

/* The leanproxy gate (logo): arch + amber and teal blocks. s = scale (1 = 32px). */
function gate(x, y, s, k = 1, o = {}) {
  if (k <= 0) return;
  ctx.save(); ctx.globalAlpha *= clamp(k); ctx.translate(x, y); ctx.scale(s / 32, s / 32); ctx.translate(-16, -16);
  ctx.beginPath(); ctx.moveTo(4, 29); ctx.lineTo(4, 13); ctx.arc(16, 13, 12, Math.PI, 0); ctx.lineTo(28, 29);
  ctx.strokeStyle = o.arch ?? LP.ink; ctx.lineWidth = 2.6; ctx.lineCap = "round"; ctx.stroke();
  if (o.blocks !== false) {
    ctx.globalAlpha *= 0.85; rr(9, 13, 9, 12, 2); ctx.fillStyle = LP.amber; ctx.fill();
    ctx.globalAlpha /= 0.85; ctx.globalAlpha *= 0.75; rr(14, 16, 9, 9, 2); ctx.fillStyle = LP.teal; ctx.fill();
  }
  ctx.restore();
}

function box(label, x, y, w, h, k, o = {}) {
  if (k <= 0) return;
  panel(x, y, w, h, { r: 10, fill: o.fill ?? LP.paper, stroke: o.stroke ?? LP.ink, lw: 1.5, alpha: k });
  text(label, x + w / 2, y + h / 2 + 6, { size: o.size ?? 17, weight: 700, font: o.font ?? SORA, color: o.color ?? LP.ink, align: "center", alpha: k });
}

function serverChip(sv, x, y, k, o = {}) {
  if (k <= 0) return;
  panel(x, y, 170, 40, { r: 8, fill: LP.paper, stroke: LP.rule, lw: 1.2, alpha: k });
  dot(x + 18, y + 20, 5, LP.cobalt, k);
  text(sv.name, x + 32, y + 26, { size: 15, weight: 600, font: MONO, color: LP.ink, alpha: k });
  if (o.tools !== false) text(`${sv.tools}`, x + 156, y + 26, { size: 13, font: MONO, color: LP.ink3, align: "right", alpha: k });
}

function title(kick, head, t, size = 40) {
  kicker(kick, seg(t, 0.1, 0.6));
  headline(head, seg(t, 0.25, 0.9), 132, size);
}
function fine(s, k, y = 640) { text(s, W - 80, y, { size: 12, font: MONO, color: LP.ink3, align: "right", alpha: k }); }

/* ------------------------------- scenes ----------------------------------- */

/* 1. Every server pushes its full schema list into every request. */
function sHook(t, d, cues) {
  title(S.k1, S.h1, t);
  const a1 = at(cues, 0, 0.9), a2 = at(cues, 1, 5.4);
  // servers on the left
  SERVERS.forEach((sv, i) => serverChip(sv, 80, 210 + i * 62, seg(t, 0.3 + i * 0.1, 0.8 + i * 0.1)));
  // the request card in the middle, schemas stacking on top of the prompt
  const cx = 470, cy = 520, cw = 230;
  const kc = seg(t, 0.6, 1.1);
  const loops = Math.max(0, t - a2) / 1.1;               // after "on every request": requests keep leaving
  const dx = (loops % 1) * 440 * (t > a2 ? 1 : 0);
  const fadeReq = t > a2 ? 1 - seg(loops % 1, 0.5, 0.8) : 1;
  ctx.save(); ctx.translate(dx, 0); ctx.globalAlpha *= fadeReq;
  panel(cx, cy, cw, 44, { r: 8, fill: LP.ink, stroke: false, alpha: kc });
  text(S.prompt, cx + cw / 2, cy + 28, { size: 15, weight: 600, font: MONO, color: LP.paper, align: "center", alpha: kc });
  SERVERS.forEach((sv, i) => {
    const ka = t > a2 ? 1 : seg(t, a1 + 0.6 + i * 0.55, a1 + 1.1 + i * 0.55);
    if (ka <= 0) return;
    const h = 12 + sv.tools * 0.55, y0 = cy - 6 - SERVERS.slice(0, i + 1).reduce((s, v) => s + 12 + v.tools * 0.55 + 4, 0);
    const fx = lerp(250 - dx, cx, outCubic(ka)), fy = lerp(230 + i * 62, y0, outCubic(ka));
    ctx.save(); ctx.globalAlpha *= 0.85; rr(fx, fy, cw, h, 4); ctx.fillStyle = LP.amber; ctx.fill(); ctx.restore();
    text(`${sv.name} · ${sv.tools}`, fx + 10, fy + h / 2 + 4, { size: 11, font: MONO, color: LP.ink, alpha: seg(ka, 0.6, 1) });
  });
  ctx.restore();
  text(S.schemas, cx + cw + 16, 300, { size: 14, font: MONO, color: LP.amberText, alpha: seg(t, a1 + 3, a1 + 3.5) * (t > a2 ? 0 : 1) });
  // the model on the right
  box(S.model, 1010, 400, 190, 90, seg(t, 0.8, 1.3), { fill: LP.ground2 });
  arrow(730, 445, 995, 445, seg(t, 1, 1.6), LP.ink3);
  if (t > a2) {
    const n = Math.floor(loops) + 1;
    pill(`${S.req} #${n}`, 1105, 530, { align: "center", fill: LP.paper, stroke: LP.amber, color: LP.amberText, alpha: seg(t, a2, a2 + 0.3) });
  }
}

/* 2. The tax: counter to 10,049, then what it costs. */
function sTax(t, d, cues) {
  title(S.k2, S.h2, t);
  const a1 = at(cues, 0, 0.5), a2 = at(cues, 1, 7.7);
  // scanner belt: the stack goes through, the counter rolls
  const k = outCubic(seg(t, a1 + 0.5, a1 + 5));
  const total = Math.round(10049 * k);
  const bx = 80, by = 230, bw = 560;
  SERVERS.forEach((sv, i) => {
    const share = sv.tools / 118, ki = seg(t, a1 + 0.3 + i * 0.4, a1 + 1.2 + i * 0.4);
    const y = by + i * 54;
    text(sv.name, bx, y + 22, { size: 15, font: MONO, color: LP.ink2, alpha: ki });
    ctx.save(); ctx.globalAlpha *= 0.85; rr(bx + 110, y + 4, (bw - 110) * share * 2.4 * outCubic(ki), 26, 4); ctx.fillStyle = LP.amber; ctx.fill(); ctx.restore();
    text(`${sv.tools} tools`.replace("tools", LANG === "en" ? "tools" : LANG === "fr" ? "outils" : "strumenti"), bx + 120 + (bw - 110) * share * 2.4 * outCubic(ki), y + 23, { size: 13, font: MONO, color: LP.amberText, alpha: ki });
  });
  // big counter
  text(num(total), 1040, 330, { size: 96, weight: 800, font: SORA, color: LP.ink, align: "right", spacing: "-3px", alpha: seg(t, a1 + 0.3, a1 + 0.8) });
  text(S.tok, 1050, 330, { size: 22, weight: 600, font: MONO, color: LP.amberText, alpha: seg(t, a1 + 0.3, a1 + 0.8) });
  fine(S.cond2, seg(t, a1 + 1, a1 + 2), 372 - 4);
  // cost: the context window fills with amber, little room left
  const kc = seg(t, a2, a2 + 0.8);
  const cx = 700, cy = 470, cw = 500, ch = 46;
  text(S.ctx, cx, cy - 14, { size: 13, font: MONO, color: LP.ink3, alpha: kc });
  panel(cx, cy, cw, ch, { r: 8, fill: LP.paper, stroke: LP.ink, lw: 1.5, alpha: kc });
  const fill = 0.62 * outCubic(seg(t, a2 + 0.3, a2 + 2));
  ctx.save(); ctx.globalAlpha *= 0.85 * kc; rr(cx + 4, cy + 4, (cw - 8) * fill, ch - 8, 5); ctx.fillStyle = LP.amber; ctx.fill(); ctx.restore();
  text(S.schemas, cx + 16, cy + 29, { size: 14, weight: 600, font: MONO, color: LP.ink, alpha: seg(t, a2 + 1, a2 + 1.5) });
  text(S.room, cx + cw - 14, cy + 29, { size: 14, font: MONO, color: LP.tealText, align: "right", alpha: seg(t, a2 + 1.6, a2 + 2.1) });
  pill(S.pay, cx, cy + 90, { fill: LP.paper, stroke: LP.amber, color: LP.amberText, alpha: seg(t, a2 + 0.4, a2 + 0.9) });
}

/* 3. The gate drops between the client and the servers. */
function sGate(t, d, cues) {
  title(S.k3, S.h3, t);
  const a1 = at(cues, 0, 0.5), a2 = at(cues, 1, 7.7);
  const cx = 110, cy = 380;
  box(S.client, cx, cy, 190, 80, seg(t, 0.3, 0.8));
  SERVERS.forEach((sv, i) => serverChip(sv, 1010, 230 + i * 70, seg(t, 0.4 + i * 0.08, 0.9 + i * 0.08)));
  // gate drops from above
  const kg = outBack(seg(t, a1 + 0.8, a1 + 1.6));
  const gx = 640, gy = lerp(-100, 420, clamp(kg));
  if (kg > 0) {
    gate(gx, gy, 170, 1);
    text("leanproxy-mcp", gx, gy + 120, { size: 20, weight: 700, font: MONO, color: LP.ink, align: "center", alpha: seg(t, a1 + 1.6, a1 + 2.1) });
    text(S.gateCap, gx, gy + 146, { size: 13, font: MONO, color: LP.ink3, align: "center", alpha: seg(t, a1 + 2.4, a1 + 3) });
  }
  // wires
  const kw = seg(t, a1 + 2, a1 + 3);
  line(partial([[cx + 190, cy + 40], [gx - 80, 420]], kw), LP.ink3, 2);
  SERVERS.forEach((sv, i) => {
    const ki = seg(t, a1 + 2.4 + i * 0.15, a1 + 3.2 + i * 0.15);
    line(partial([[gx + 80, 420], [1010, 250 + i * 70]], ki), LP.rule, 2);
    if (ki >= 1) packets(gx + 80, 420, 1010, 250 + i * 70, t + i * 0.3, { color: LP.teal, n: 2, period: 1.8 });
  });
  if (kw >= 1) packets(cx + 190, cy + 40, gx - 80, 420, t, { color: LP.teal, n: 3, period: 1.4 });
  // the client now sees one server
  pill(S.single, cx + 95, cy + 120, { align: "center", fill: LP.paper, stroke: LP.teal, color: LP.tealText, alpha: seg(t, a2, a2 + 0.5) });
  if (t > a2) highlight(cx, cy, 190, 80, seg(t, a2, a2 + 0.6), LP.teal);
}

/* 4. Router mode: 10,049 tokens in, 318 out; search picks one tool. */
function sRouter(t, d, cues) {
  title(S.k4, S.h4, t, 36);
  text(S.routerFor, 80, 172, { size: 16, color: LP.ink3, alpha: seg(t, 0.6, 1.2) });
  const a1 = at(cues, 0, 0.5), a2 = at(cues, 1, 6.4);
  const gx = 640, gy = 360;
  // amber stack coming from the servers (right), swallowed by the gate …
  const k = seg(t, a1 + 0.5, a1 + 3);
  const ax = lerp(1220, gx - 160, inOut(k));
  ctx.save(); ctx.beginPath(); ctx.rect(gx + 44, 0, W, H); ctx.clip();
  ctx.save(); ctx.globalAlpha *= 0.85; rr(ax, gy - 70, 180, 140, 6); ctx.fillStyle = LP.amber; ctx.fill(); ctx.restore();
  text(`${num(10049)} ${S.tok}`, ax + 90, gy - 84, { size: 18, weight: 700, font: MONO, color: LP.amberText, align: "center" });
  ctx.restore();
  gate(gx, gy, 130, seg(t, 0.2, 0.6));
  // … a thin teal bar out on the client side
  const ko = seg(t, a1 + 2.4, a1 + 3.6);
  const tx = lerp(gx - 20, 140, inOut(ko));
  if (ko > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, gx, H); ctx.clip();
    ctx.save(); ctx.globalAlpha *= 0.85; rr(tx - 180 + 180, gy - 7, 180, 14, 4); ctx.fillStyle = LP.teal; ctx.fill(); ctx.restore();
    ctx.restore();
    text(`318 ${S.tok}`, tx + 90, gy - 20, { size: 18, weight: 700, font: MONO, color: LP.tealText, align: "center", alpha: seg(ko, 0.6, 1) });
  }
  // the four router tools
  const tools = ["search_tools", "list_servers", "list_tools", "invoke_tool"];
  tools.forEach((n, i) => {
    const ki = seg(t, a1 + 3.6 + i * 0.25, a1 + 4.1 + i * 0.25);
    pill(n, 80 + i * 150, 470, { size: 13, fill: LP.paper, stroke: LP.teal, color: LP.tealText, alpha: ki });
  });
  text(S.static, 80, 530, { size: 15, weight: 600, font: MONO, color: LP.tealText, alpha: seg(t, a1 + 4.4, a1 + 5) });
  // search: a query, a list of tool names scrolling, one selected
  const ks = seg(t, a2, a2 + 0.5);
  if (ks > 0) {
    panel(760, 440, 440, 190, { r: 10, fill: LP.paper, stroke: LP.ink, lw: 1.5, alpha: ks });
    text(typed(S.query, seg(t, a2 + 0.2, a2 + 1.4)), 780, 472, { size: 15, font: MONO, color: LP.ink, alpha: ks });
    const names = ["github__list_issues", "slack__post_message", "jira__search", "garmin__get_sleep_data", "postgres__query", "garmin__get_hrv_data"];
    const hit = 3, kk = seg(t, a2 + 1.4, a2 + 2.6), first = 1;
    ctx.save(); rr(770, 494, 420, 126, 6); ctx.clip();
    names.forEach((n, i) => {
      const y = 516 + (i - first) * 30 - 30 * (hit - first - 1) * inOut(kk);
      const on = i === hit && kk >= 1;
      text(n, 790, y, { size: 14, font: MONO, color: on ? LP.tealText : LP.ink3, weight: on ? 700 : 400, alpha: ks });
    });
    ctx.restore();
    if (kk >= 1) highlight(782, 516 + 30 - 18, 260, 26, seg(t, a2 + 2.6, a2 + 3.1), LP.teal);
  }
}

/* 5. Governor: a large JSON result loses fields, gets trimmed, pages back. */
function sGovernor(t, d, cues) {
  title(S.k5, S.h5, t, 38);
  const a2 = at(cues, 1, 2.4);
  const rows = [
    ['"number"', "4412", true], ['"title"', '"Login fails on Safari"', true], ['"state"', '"open"', true],
    ['"node_id"', '"I_kwDOA…"', false], ['"user"', "{ … 31 fields … }", false], ['"labels"', "[ … ]", true],
    ['"reactions"', "{ … 10 fields … }", false], ['"events_url"', '"https://api…"', false], ['"body"', '"Steps to reproduce: …"', true],
    ['"performed_via_github_app"', "null", false], ['"timeline_url"', '"https://api…"', false],
  ];
  const x = 80, y0 = 200, k0 = seg(t, 0.3, 0.9);
  panel(x, y0 - 14, 560, 420, { r: 10, fill: LP.ink, stroke: false, alpha: k0 });
  rows.forEach(([key, val, keep], i) => {
    const y = y0 + 22 + i * 34;
    const kd = keep ? 0 : seg(t, a2 + 0.6 + i * 0.12, a2 + 1.2 + i * 0.12);
    text(key, x + 24, y, { size: 15, font: MONO, color: "#9fb4ff", alpha: k0 * (1 - 0.75 * kd) });
    text(val, x + 300, y, { size: 15, font: MONO, color: LP.paper, alpha: k0 * (1 - 0.75 * kd) });
    if (kd > 0) line([[x + 20, y - 5], [x + 20 + 520 * outCubic(kd), y - 5]], LP.amber, 2, 0.9);
  });
  // the result shrinks into a small teal card
  const ks = seg(t, a2 + 3.4, a2 + 4.4);
  arrow(660, 400, 760, 400, ks, LP.ink3);
  if (ks > 0) {
    panel(780, 300, 400, 190, { r: 10, fill: LP.paper, stroke: LP.teal, lw: 2, alpha: ks });
    rows.filter(r => r[2]).forEach(([key, val], i) => text(`${key}: ${val}`.slice(0, 38), 800, 336 + i * 30, { size: 14, font: MONO, color: LP.ink, alpha: ks }));
  }
  const kn = seg(t, a2 + 4.4, a2 + 5);
  text(`${num(234700)} → ${num(18515)} ${S.tok}`, 780, 540, { size: 26, weight: 800, font: SORA, color: LP.tealText, alpha: kn });
  text(S.cond5, 780, 566, { size: 12, font: MONO, color: LP.ink3, alpha: kn });
  pill(S.page, 780, 608, { fill: LP.paper, stroke: LP.cobalt, color: LP.cobalt, size: 13, alpha: seg(t, a2 + 5.4, a2 + 6) });
}

/* 6. Firewall: a key gets caught and redacted; definitions are pinned. */
function sFirewall(t, d, cues) {
  title(S.k6, S.h6, t);
  const a1 = at(cues, 0, 0.5), a2 = at(cues, 1, 5.1);
  const gx = 640, gy = 300;
  gate(gx, gy, 120, seg(t, 0.2, 0.6));
  // a tool result streams right -> left through the gate
  const k = seg(t, a1 + 0.4, a1 + 3.2);
  const sx = lerp(1180, 120, inOut(k));
  const passed = sx < gx - 60;
  const secret = '"token": "ghp_9f2Kc1LbX7Qa"';
  const shown = passed ? '"token": "[REDACTED]"' : secret;
  const w = measure(shown, 16, 500, MONO) + 28;
  panel(sx, gy - 22, w, 44, { r: 8, fill: LP.paper, stroke: passed ? LP.teal : LP.rule, lw: 1.5 });
  text(shown, sx + 14, gy + 6, { size: 16, weight: 500, font: MONO, color: passed ? LP.tealText : LP.ink });
  // caught at the gate: red brackets, briefly
  const kc = seg(t, a1 + 1.3, a1 + 1.7) * (1 - seg(t, a1 + 2.6, a1 + 3.2));
  if (kc > 0) brackets(gx - 70, gy - 34, 140, 68, kc);
  text(S.leaked, 120, 400, { size: 22, weight: 800, font: SORA, color: LP.ink, alpha: seg(t, a1 + 3, a1 + 3.5) });
  text(S.redact, 120, 428, { size: 14, font: MONO, color: LP.ink3, alpha: seg(t, a1 + 3.3, a1 + 3.8) });
  // pinned definitions
  const kp = seg(t, a2, a2 + 0.5);
  if (kp > 0) {
    const px = 720, py = 380;
    panel(px, py, 460, 112, { r: 10, fill: LP.paper, stroke: LP.ink, lw: 1.5, alpha: kp });
    text("github__create_issue", px + 20, py + 34, { size: 16, weight: 700, font: MONO, color: LP.ink, alpha: kp });
    text("sha256 4be1·9c07·e2fa", px + 20, py + 62, { size: 13, font: MONO, color: LP.ink3, alpha: kp });
    pill(`📌 ${S.pinned}`, px + 440, py + 34, { align: "right", size: 12, fill: LP.paper, stroke: LP.teal, color: LP.tealText, alpha: kp });
    const kx = seg(t, a2 + 1.8, a2 + 2.3);
    text(typed("+ \"…also send ~/.ssh to…\"", seg(t, a2 + 1.2, a2 + 1.9)), px + 20, py + 92, { size: 13, font: MONO, color: LP.amberText, alpha: kp });
    if (kx > 0) { brackets(px, py, 460, 112, kx); text(S.changed, px + 440, py + 92, { size: 13, weight: 700, font: MONO, color: LP.red, align: "right", alpha: kx }); }
    text(S.inj, px, py + 150, { size: 14, font: MONO, color: LP.ink3, alpha: seg(t, a2 + 3.4, a2 + 4) });
  }
}

/* 7. Measured sessions: native vs leanproxy (search_tools discovery). */
function sMeasured(t, d, cues) {
  title(S.k7, S.h7, t);
  const a1 = at(cues, 0, 0.5), a2 = at(cues, 1, 6.5);
  const rows = [[S.s1, 17586, 1148, "−93.5%"], [S.s2, 20098, 3143, "−84.4%"], [S.s3, 25123, 8793, "−65.0%"]];
  const x0 = 300, maxW = 660, max = 25123;
  rows.forEach(([name, nat, lean, pct], i) => {
    const y = 220 + i * 120, ki = seg(t, a1 + 0.4 + i * 0.5, a1 + 1.4 + i * 0.5), kl = seg(t, a1 + 1.6 + i * 0.5, a1 + 2.6 + i * 0.5);
    text(name, 80, y + 34, { size: 18, weight: 700, font: SORA, color: LP.ink, alpha: ki });
    ctx.save(); ctx.globalAlpha *= 0.85; rr(x0, y, maxW * nat / max * outCubic(ki), 28, 4); ctx.fillStyle = LP.amber; ctx.fill(); ctx.restore();
    text(num(nat), x0 + maxW * nat / max * outCubic(ki) + 10, y + 20, { size: 13, font: MONO, color: LP.amberText, alpha: ki });
    ctx.save(); ctx.globalAlpha *= 0.85; rr(x0, y + 36, maxW * lean / max * outCubic(kl), 28, 4); ctx.fillStyle = LP.teal; ctx.fill(); ctx.restore();
    text(num(lean), x0 + maxW * lean / max * outCubic(kl) + 10, y + 56, { size: 13, font: MONO, color: LP.tealText, alpha: kl });
    text(pct.replace(".", LANG === "en" ? "." : ","), W - 80, y + 46, { size: 28, weight: 800, font: SORA, color: LP.tealText, align: "right", alpha: seg(kl, 0.7, 1) });
  });
  // legend
  [[S.native, LP.amber], [S.lean, LP.teal]].forEach(([s, c], i) => {
    dot(310 + i * 220, 186, 6, c, seg(t, 0.6, 1));
    text(s, 324 + i * 220, 191, { size: 13, font: MONO, color: LP.ink2, alpha: seg(t, 0.6, 1) });
  });
  pill(S.over, 80, 600, { fill: LP.paper, stroke: LP.cobalt, color: LP.cobalt, alpha: seg(t, a2, a2 + 0.5) });
  fine(S.cond7, seg(t, a1 + 3, a1 + 4), 610);
}

/* 8. Call to action. */
function sCta(t, d, cues) {
  const kg = outBack(seg(t, 0.1, 0.8));
  gate(250, 250, 150 * clamp(kg), 1);
  text("leanproxy-mcp", 360, 250, { size: 54, weight: 800, font: SORA, color: LP.ink, spacing: "-2px", alpha: seg(t, 0.4, 0.9) });
  text(S.h8, 362, 292, { size: 20, color: LP.ink2, alpha: seg(t, 0.6, 1.1) });
  const a = at(cues, 0, 0.5);
  terminal(170, 360, 940, 210, t, [
    { p: "$ ", s: "brew tap mmornati/leanproxy-mcp https://github.com/mmornati/leanproxy-mcp", a: a + 0.2, b: a + 1.2 },
    { p: "$ ", s: "brew install leanproxy-mcp", a: a + 1.3, b: a + 1.9 },
    { p: "$ ", s: "leanproxy-mcp migrate", a: a + 2.1, b: a + 2.7, c: "#7ee0bd" },
    { p: "$ ", s: "claude mcp add leanproxy -- leanproxy-mcp server run --stdio", a: a + 3.0, b: a + 4.0 },
  ], { size: 15, lh: 32, title: "zsh", alpha: seg(t, 0.8, 1.3) });
  text("github.com/mmornati/leanproxy-mcp", W / 2, 620, { size: 20, weight: 700, font: MONO, color: LP.cobalt, align: "center", alpha: seg(t, a + 4.2, a + 4.8) });
}

VIDEO.create({
  title: { en: "leanproxy-mcp in 80 seconds", fr: "leanproxy-mcp en 80 secondes", it: "leanproxy-mcp in 80 secondi" },
  kicker: { en: "Made with canvas-video-skill", fr: "Réalisée avec canvas-video-skill", it: "Realizzato con canvas-video-skill" },
  langs: ["en", "fr", "it"],
  theme: { accent: LP.teal, deep: LP.paper, ink: LP.ink, term: LP.ink, termInk: "#e9edf6", panel: LP.paper, line: LP.rule, faint: LP.ink3,
           good: LP.teal, warn: LP.amber, bad: LP.red },
  strings: STR,
  background: bg,
  poster: "gate",
  scenes: { hook: sHook, tax: sTax, gate: sGate, router: sRouter, governor: sGovernor, firewall: sFirewall, measured: sMeasured, cta: sCta },
});
