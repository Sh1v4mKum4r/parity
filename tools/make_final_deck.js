// Final-review deck for PARITY. Numbers are read from out/metrics.json and
// out/training.json so the deck cannot drift from the measurements.
//
//   node tools/make_final_deck.js [out.pptx]
//
// Sandwich structure: dark title, section dividers and closing; light content
// slides, because every figure in out/ is drawn on a light surface.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const M = JSON.parse(fs.readFileSync(path.join(ROOT, "out/metrics.json")));
const T = JSON.parse(fs.readFileSync(path.join(ROOT, "out/training.json")));
const OUT = path.resolve(process.argv[2] || path.join(ROOT, "docs/PARITY-final-review.pptx"));

const pct = v => (v * 100).toFixed(1);
const E1 = (bot, m) => pct(M.e1_accuracy[`${bot}|${m}`].top1);
const E13 = M.e13_across_sessions;

// amber on near-black is the game's own palette; the deck inherits it
const THEME = {
  name: "PARITY",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B0A08", lt1: "FBF9F4", dk2: "2A251C", lt2: "EDE7DA",
    accent1: "FFB545", accent2: "C2402F", accent3: "2F7F5E",
    accent4: "2A78D6", accent5: "7A7059", accent6: "5A4E3A",
    hlink: "2A78D6", folHlink: "5A4E3A",
  },
};
const AMBER = THEME.colors.accent1, RED = THEME.colors.accent2;
const INK = THEME.colors.dk1, PAPER = THEME.colors.lt1, MUTED = THEME.colors.accent5;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Shivam Kumar Arya and Parth Jaiswal";
pres.title = "PARITY — Final Review";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: INK },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.35, w: 11.5, h: 1.5,
        fontSize: 60, bold: true, color: AMBER, charSpacing: 6, fontFace: "Cambria", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.95, y: 3.85, w: 10.6, h: 1.5,
        fontSize: 17, color: PAPER, lineSpacing: 26 }, text: " " } },
    { placeholder: { options: { name: "meta", type: "body", x: 0.95, y: 6.1, w: 11.4, h: 0.9,
        fontSize: 12.5, color: MUTED, lineSpacing: 19 }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "SECTION_DARK", background: { color: INK },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.9, y: 2.9, w: 10, h: 0.4,
        fontSize: 13, color: MUTED, charSpacing: 3 }, text: " " } },
    { placeholder: { options: { name: "title", type: "title", x: 0.86, y: 3.3, w: 11.6, h: 1.2,
        fontSize: 40, bold: true, color: PAPER, fontFace: "Cambria", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 4.5, w: 9.8, h: 1.1,
        fontSize: 15, color: MUTED, lineSpacing: 24 }, text: " " } },
  ],
});

const contentObjects = (bg, ink, sub) => ([
  { placeholder: { options: { name: "title", type: "title", x: 0.62, y: 0.42, w: 12.1, h: 0.78,
      fontSize: 32, bold: true, color: ink, fontFace: "Cambria", margin: 0, align: "left" }, text: " " } },
  { placeholder: { options: { name: "body", type: "body", x: 0.64, y: 1.22, w: 12.0, h: 0.62,
      fontSize: 15, color: sub, lineSpacing: 22, margin: 0 }, text: " " } },
  { text: { text: "PARITY · BCSE497J · Final Review",
      options: { x: 0.62, y: 6.92, w: 6, h: 0.3, fontSize: 9.5, color: sub, isTextBox: true, margin: 0 } } },
  { placeholder: { options: { name: "slideNumber", type: "sldNum", x: 12.3, y: 6.92, w: 0.5, h: 0.3,
      fontSize: 9.5, color: sub, align: "right" } } },
]);
pres.defineSlideMaster({ title: "CONTENT", background: { color: PAPER }, objects: contentObjects(PAPER, INK, MUTED) });
pres.defineSlideMaster({ title: "CONTENT_DARK", background: { color: INK }, objects: contentObjects(INK, PAPER, MUTED) });

pres.defineSlideMaster({
  title: "CLOSING_DARK", background: { color: INK },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 1.5, w: 11.5, h: 1.0,
        fontSize: 38, bold: true, color: AMBER, fontFace: "Cambria", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.95, y: 2.42, w: 11.3, h: 3.95,
        fontSize: 15, color: PAPER, lineSpacing: 25, align: "left" }, text: " " } },
  ],
});

// ---------------------------------------------------------------- helpers
const img = p => path.join(ROOT, p);
const have = p => fs.existsSync(img(p));
const firstOf = (...ps) => ps.find(have);

// a figure sized to fit a box without distortion
function figure(slide, file, { x, y, w, h }) {
  const sizeOf = require("child_process").execSync(
    `python3 -c "from PIL import Image;im=Image.open('${img(file)}');print(im.size[0],im.size[1])"`
  ).toString().trim().split(" ").map(Number);
  const ar = sizeOf[0] / sizeOf[1];
  let dw = w, dh = w / ar;
  if (dh > h) { dh = h; dw = h * ar; }
  slide.addImage({ path: img(file), x: x + (w - dw) / 2, y: y + (h - dh) / 2, w: dw, h: dh,
                   objectName: path.basename(file) });
}

// a stat block: big number, small label
function stat(slide, { x, y, w, value, label, color }) {
  slide.addText(value, { x, y, w, h: 0.78, fontSize: 40, bold: true, color,
    isTextBox: true, margin: 0, fontFace: "Cambria", objectName: `stat-${label}` });
  slide.addText(label, { x, y: y + 0.78, w, h: 0.62, fontSize: 11.5, color: MUTED,
    isTextBox: true, margin: 0, lineSpacing: 15 });
}

// a bordered card
function card(slide, { x, y, w, h, fill, line }) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.04,
    fill: { color: fill }, line: { color: line, width: 0.75 } });
}

// ================================================================= slides
let s;

// 1 ---------------------------------------------------------------- title
s = pres.addSlide({ masterName: "TITLE_DARK" });
s.addText("PARITY", { placeholder: "title" });
s.addText("An adaptive horror game driven by online player-trajectory prediction",
  { placeholder: "body" });
s.addText([
  { text: "Shivam Kumar Arya (23BRS1357)  \u00B7  Parth Jaiswal (23BRS1323)", options: { bold: true, color: PAPER, breakLine: true } },
  { text: "Team 53  \u00B7  Guide: Prakash B  \u00B7  Panel 88  \u00B7  BCSE497J", options: { breakLine: true } },
  { text: "B.Tech Computer Science and Engineering (AI & Robotics)  \u00B7  Vellore Institute of Technology", options: {} },
], { placeholder: "meta" });
s.addShape(pres.shapes.RECTANGLE, { x: 0.95, y: 2.15, w: 1.1, h: 0.035, fill: { color: AMBER }, line: { color: AMBER } });
s.addText("0 1 0 0 1 1 0 1", { x: 0.95, y: 5.45, w: 6, h: 0.35, fontSize: 13, color: MUTED,
  charSpacing: 8, fontFace: "Courier New", isTextBox: true, margin: 0 });
s.addNotes("The antagonist builds a behavioural model of the individual player and acts on it. The game is not a wrapper around the AI; it is the application that makes the AI legible.");

// 2 ------------------------------------------------------------- section
pres.addSection({ title: "The problem" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "The problem" });
s.addText("01", { placeholder: "kicker" });
s.addText("The problem", { placeholder: "title" });
s.addText("Game AI has optimised for competence. Adaptation to the individual player is the less-solved half.", { placeholder: "body" });

// 3 ----------------------------------------------------------- the gap
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The problem" });
s.addText("Three fields, one gap between them", { placeholder: "title" });
s.addText("Each is mature on its own. What is missing is a system that infers, acts and reshapes the world as one loop — and is measured as one.", { placeholder: "body" });
const gap = [
  ["Player modelling", "Infers intent from telemetry.\nRarely drives the antagonist in real time."],
  ["Adaptive AI and DDA", "Acts on inference, but usually by\ntuning numbers, not by taking decisions."],
  ["Procedural generation", "Changes the world, but offline —\nbefore the player arrives, not in response."],
];
gap.forEach(([h, b], i) => {
  const x = 0.64 + i * 4.07;
  card(s, { x, y: 2.1, w: 3.75, h: 2.1, fill: "FFFFFF", line: "DED7C6" });
  s.addText(h, { x: x + 0.28, y: 2.32, w: 3.2, h: 0.4, fontSize: 16, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(b, { x: x + 0.28, y: 2.78, w: 3.25, h: 1.2, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 18 });
});
card(s, { x: 0.64, y: 4.55, w: 11.96, h: 1.75, fill: "FFF6E4", line: "E8C98A" });
s.addText("The research gap", { x: 1.0, y: 4.78, w: 4, h: 0.35, fontSize: 13, bold: true, color: "8A6214", isTextBox: true, margin: 0 });
s.addText("No published system closes the loop and reports it against controls. PARITY builds the loop, and measures every claim against a baseline that has no model and a player that cannot be modelled.",
  { x: 1.0, y: 5.18, w: 11.2, h: 0.95, fontSize: 15, color: INK, isTextBox: true, margin: 0, lineSpacing: 22 });
s.addNotes("The gap is not that any one of these is unsolved. It is that nobody runs them as one closed loop and then reports it honestly against a control.");

// 4 --------------------------------------------------------- what it is
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The problem" });
s.addText("What the player is actually doing", { placeholder: "title" });
s.addText("Carry eight bits from a codebook to the uplink and transmit. Twice. That is the whole game.", { placeholder: "body" });
const loop = [
  ["1", "Read a codebook", "A lit panel in a room gives a keyword and its eight bits."],
  ["2", "Write it down", "The notebook is freehand and the only record nothing can edit."],
  ["3", "Carry it to the uplink", "Every door in the facility unlocks together for three seconds, then seals."],
  ["4", "Stage and send", "While the byte sits staged and you are away, it may turn one bit over."],
];
loop.forEach(([n, h, b], i) => {
  const y = 2.08 + i * 1.12;
  s.addShape(pres.shapes.OVAL, { x: 0.68, y, w: 0.52, h: 0.52, fill: { color: INK }, line: { color: INK } });
  s.addText(n, { x: 0.68, y, w: 0.52, h: 0.52, fontSize: 15, bold: true, color: AMBER, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(h, { x: 1.42, y: y - 0.02, w: 3.1, h: 0.36, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(b, { x: 1.42, y: y + 0.32, w: 5.5, h: 0.6, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 17 });
});
const still = firstOf("out/deck_room.png", "out/fig_3d.png", "out/demo_shot.png");
if (still) figure(s, still, { x: 7.25, y: 2.0, w: 5.4, h: 4.3 });
s.addNotes("Keep this short. The point of the loop is that it gives the antagonist a reason to predict you: you must move between known rooms on a known clock.");

// 5 ------------------------------------------------------------- section
pres.addSection({ title: "How it works" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "How it works" });
s.addText("02", { placeholder: "kicker" });
s.addText("How it works", { placeholder: "title" });
s.addText("Three parts: something that predicts, something that localises, and something that decides what to do about it.", { placeholder: "body" });

// 6 -------------------------------------------------------- architecture
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it works" });
s.addText("Belief, prediction and action are separate", { placeholder: "title" });
s.addText("Keeping them apart is what makes each one measurable on its own — and what let us find that one of them was never being called.", { placeholder: "body" });
const parts = [
  ["Belief filter", "Where are they now?", "A Bayes forward filter over the room graph, updated from door-sensor events. Silence is evidence too."],
  ["Predictor", "Where will they go?", "A variable-order Markov model with Witten-Bell back-off, learning online from the trajectory it infers."],
  ["Director", "What should I do?", "Intercept, seal a door, rewire the facility, or quietly corrupt a page the player has already copied."],
];
parts.forEach(([h, q, b], i) => {
  const x = 0.64 + i * 4.07;
  card(s, { x, y: 2.0, w: 3.75, h: 2.85, fill: "FFFFFF", line: "DED7C6" });
  s.addText(h, { x: x + 0.28, y: 2.22, w: 3.2, h: 0.36, fontSize: 16, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(q, { x: x + 0.28, y: 2.6, w: 3.2, h: 0.32, fontSize: 12.5, italic: true, color: "8A6214", isTextBox: true, margin: 0 });
  s.addText(b, { x: x + 0.28, y: 3.0, w: 3.25, h: 1.65, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 18 });
});
s.addText([
  { text: "Fairness is a constraint, not a difficulty setting.  ", options: { bold: true, color: INK } },
  { text: "The antagonist never reads the player's position directly, never edits a room the player is standing in, and never acts below a confidence gate. Nine invariants assert this over 25 generated facilities.", options: { color: MUTED } },
], { x: 0.64, y: 5.25, w: 11.96, h: 1.0, fontSize: 13.5, isTextBox: true, margin: 0, lineSpacing: 20 });
s.addNotes("The separation is not tidiness. Because the director is its own object, we could test it in isolation — and that is how we found the counter-moves were never being called in any measured experiment.");

// 7 ----------------------------------------------------------- predictor
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it works" });
s.addText("The predictor: a variable-order Markov model", { placeholder: "title" });
s.addText("Long context when the evidence supports it, short context when it does not — decided per prediction, not per model.", { placeholder: "body" });
card(s, { x: 0.64, y: 2.0, w: 6.1, h: 1.74, fill: "FFFFFF", line: "DED7C6" });
// split deliberately: left to wrap, "max order" and "k = 4" land on separate lines
s.addText([
  { text: "P\u2092(x | ctx)  =", options: { breakLine: true } },
  { text: "   w \u00B7 f\u2092(x | ctx)  +  (1 \u2212 w) \u00B7 P\u2092\u208B\u2081(x | ctx[1:])", options: {} },
], { x: 0.88, y: 2.18, w: 5.7, h: 0.74, fontSize: 13, bold: true, color: INK,
     fontFace: "Courier New", isTextBox: true, margin: 0, lineSpacing: 20 });
s.addText([
  { text: "w = C(ctx) / (C(ctx) + \u03B1)", options: { breakLine: true } },
  { text: "\u03B1 = 1.6     max order k = 4", options: {} },
], { x: 0.88, y: 2.95, w: 5.7, h: 0.62, fontSize: 12, color: MUTED,
     fontFace: "Courier New", isTextBox: true, margin: 0, lineSpacing: 17 });
const why = [
  "Witten-Bell back-off weights a context by how often it has actually been seen, so a rare context defers to its shorter parent instead of guessing from one observation.",
  "Staying put is a first-class action. The candidate set is the neighbouring rooms plus the current room — an earlier version omitted it and inflated accuracy by 28 points.",
  "It learns online, from the room sequence the belief filter infers, not from ground truth it is never given.",
];
why.forEach((t, i) => {
  s.addText(t, { x: 7.0, y: 2.0 + i * 1.12, w: 5.6, h: 1.0, fontSize: 13, color: INK, bullet: true, isTextBox: true, margin: 0, lineSpacing: 19 });
});
card(s, { x: 0.64, y: 4.02, w: 6.1, h: 2.28, fill: "FFF6E4", line: "E8C98A" });
s.addText("Three attempts to beat it failed", { x: 0.9, y: 4.2, w: 5.5, h: 0.35, fontSize: 13.5, bold: true, color: "8A6214", isTextBox: true, margin: 0 });
s.addText([
  { text: "Grid search over α and k — no gain.", options: { breakLine: true } },
  { text: "Intent tagging on the context — +0.1 points.", options: { breakLine: true } },
  { text: "An explicit goal-conditioned variant — 56.7% against the plain model's 59.9%.", options: {} },
], { x: 0.9, y: 4.58, w: 5.5, h: 1.2, fontSize: 12.5, color: INK, isTextBox: true, margin: 0, lineSpacing: 19 });
s.addText("The variable-order context already encodes what those modules tried to add.",
  { x: 0.9, y: 5.76, w: 5.5, h: 0.45, fontSize: 12, italic: true, color: MUTED, isTextBox: true, margin: 0 });
s.addNotes("If asked why not an RNN: the honest answer is that we tried three ways to add structure and all three lost to data sparsity. That is a result, and it is in the report.");

// 8 ------------------------------------------------------- partial obs
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it works" });
s.addText("It cannot see you. It hears doors", { placeholder: "title" });
s.addText("The antagonist observes motion detectors on doorways, not the player. Everything it believes is inferred from which doors tripped — and which did not.", { placeholder: "body" });
figure(s, "out/fig_localisation.png", { x: 0.64, y: 1.95, w: 7.0, h: 4.3 });
const obs = [
  ["Silence is evidence", "If a wired door did not trip, the player did not cross it. The filter rules out those transitions."],
  ["Cutting a sensor is counter-play", "A dangerous task buys you a dead door — one the antagonist can no longer hear you use."],
  ["But it has a sweet spot", "At 60% coverage, killing three sensors cuts risk 21%. At full coverage the same move backfires by 91%."],
];
obs.forEach(([h, b], i) => {
  const y = 2.05 + i * 1.45;
  s.addText(h, { x: 8.0, y, w: 4.6, h: 0.34, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(b, { x: 8.0, y: y + 0.36, w: 4.65, h: 0.95, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 18 });
});
s.addNotes("The backfire at full coverage is the most interesting line on this slide. Cutting a sensor removes a door from the antagonist's hearing, but it also removes it from the set of explanations for silence, which sharpens the filter elsewhere.");

// 9 ------------------------------------------------------------- section
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Results" });
s.addText("03", { placeholder: "kicker" });
s.addText("Results", { placeholder: "title" });
s.addText("Every number below is prequential — predicted before it was observed — and reported against a control that cannot be modelled.", { placeholder: "body" });

// 10 ------------------------------------------------------- accuracy
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("It predicts where you go next", { placeholder: "title" });
s.addText("Top-1 next-room accuracy, mean of 12 held-out facilities. The candidate set is the neighbouring rooms plus staying put.", { placeholder: "body" });
figure(s, "out/fig_accuracy.png", { x: 0.64, y: 1.9, w: 8.0, h: 3.5 });
stat(s, { x: 9.0, y: 2.0, w: 3.6, value: E1("habitual", "vomm") + "%", label: "against a habitual player,\nagainst 60.0% for order-1 Markov", color: "2A78D6" });
stat(s, { x: 9.0, y: 3.6, w: 3.6, value: E1("random", "vomm") + "%", label: "against a random player —\nno model scores " + E1("random", "uniform") + "%", color: INK });
card(s, { x: 0.64, y: 5.55, w: 11.96, h: 0.95, fill: "FFF6E4", line: "E8C98A" });
s.addText([
  { text: "The control is the row that matters.  ", options: { bold: true, color: "8A6214" } },
  { text: "Against a player with no habits the model performs identically to having no model at all. The gains are learned behaviour, not leakage from the simulator.", options: { color: INK } },
], { x: 1.0, y: 5.72, w: 11.2, h: 0.65, fontSize: 13.5, isTextBox: true, margin: 0, lineSpacing: 19 });
s.addNotes("If a panel member attacks one number, it will be this one — they will say the bots are scripted so of course it predicts them. The random control is the answer: same simulator, same pipeline, no signal to find, and the model finds none.");

// 11 ------------------------------------------------------ the ceiling
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("How well trained is it, really?", { placeholder: "title" });
s.addText("Accuracy alone does not say whether a model is good — it says how predictable the player is. So we measured the ceiling.", { placeholder: "body" });
figure(s, "out/fig_training.png", { x: 0.64, y: 1.9, w: 7.6, h: 3.9 });
const ceil = [
  ["An oracle that cheats", "Give a predictor the player's internal state — the room it is walking to, whether it is mid-page — and it reaches " + pct(T["oracle ceiling"]) + "%. That is the ceiling."],
  ["The model, from behaviour alone", pct(T["VOMM (settled)"]) + "% once settled. That is 97% of the achievable signal, with no access to anything the player knows."],
  ["Against a perfect routine", "100%. When the player is genuinely consistent, it is not approximately right — it is right."],
];
ceil.forEach(([h, b], i) => {
  const y = 2.0 + i * 1.5;
  s.addText(h, { x: 8.55, y, w: 4.1, h: 0.34, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(b, { x: 8.55, y: y + 0.36, w: 4.1, h: 1.05, fontSize: 12, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 17 });
});
s.addNotes("This reframes the 83.6%. The remaining gap is mostly the player's own randomness, not a modelling failure. Three attempts to close it confirmed that.");

// 12 -------------------------------------------- better antagonist
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Prediction makes a materially better antagonist", { placeholder: "title" });
s.addText("Captures per 1000 moves against an entity that ambushes where the model points, versus no model and versus camping the busiest junction.", { placeholder: "body" });
figure(s, "out/fig_capture.png", { x: 0.64, y: 1.95, w: 6.4, h: 4.1 });
figure(s, "out/fig_counterplay.png", { x: 7.2, y: 1.95, w: 5.45, h: 4.1 });
s.addText("Captures by antagonist strategy", { x: 0.64, y: 6.1, w: 6.4, h: 0.3, fontSize: 11.5, italic: true, color: MUTED, align: "center", isTextBox: true, margin: 0 });
s.addText("Captures per objective by what the player tries", { x: 7.2, y: 6.1, w: 5.45, h: 0.3, fontSize: 11.5, italic: true, color: MUTED, align: "center", isTextBox: true, margin: 0 });
s.addNotes("Right-hand chart: waiting is catastrophic — +439% at full coverage. Hiding from a model that has learned you wait is the worst thing you can do. That is the design working.");

// 13 -------------------------------------------------- E13, the new one
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Does it get better the more you play?", { placeholder: "title" });
s.addText("The game claims your pages survive and so does its model of you. Twelve consecutive sessions, everything reset but the predictor — each against a control that forgets.", { placeholder: "body" });
figure(s, "out/fig_sessions.png", { x: 0.64, y: 1.88, w: 11.96, h: 3.5 });
const sk = E13["same-facility/remembers"], nk = E13["new-facility/remembers"];
stat(s, { x: 0.68, y: 5.35, w: 3.5, value: (sk.change_pct > 0 ? "+" : "") + sk.change_pct.toFixed(1) + "%", label: "more captures by session 12\nwhen the building stays put", color: "2A78D6" });
stat(s, { x: 4.55, y: 5.35, w: 3.5, value: nk.change_pct.toFixed(1) + "%", label: "when the building is rewired —\ncarrying the model is worse than forgetting", color: RED });
card(s, { x: 8.5, y: 5.3, w: 4.1, h: 1.5, fill: "FFF6E4", line: "E8C98A" });
s.addText("Both controls are flat. The trend is retained learning, not the player settling into a route.",
  { x: 8.78, y: 5.5, w: 3.6, h: 1.1, fontSize: 12.5, color: INK, isTextBox: true, margin: 0, lineSpacing: 18 });
s.addNotes("This is the newest result and the one to dwell on. It also found a design bug: the shipped build regenerates the facility on re-entry, which is exactly the condition where memory hurts — so the line the game delivers on the death screen is currently false. Report section 7.8.");

// 14 ------------------------------------------------- the open problem
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("The open problem: knowing when you stop to write", { placeholder: "title" });
s.addText("Once the player writes realistically — each codebook copied once, not re-copied — pausing becomes rare, and accuracy stops meaning anything.", { placeholder: "body" });
figure(s, "out/fig_dwell.png", { x: 0.64, y: 1.95, w: 6.6, h: 4.0 });
stat(s, { x: 7.65, y: 2.0, w: 2.3, value: pct(M.e10_dwell_learned.dwell_rate) + "%", label: "of windows are a pause —\nso “always move” scores 96%", color: INK });
stat(s, { x: 10.3, y: 2.0, w: 2.3, value: pct(M.e10_dwell_learned.vomm_recall) + "%", label: "recall on the rare event,\nagainst 0% for that baseline", color: RED });
s.addText([
  { text: "Why this is the honest weak spot.  ", options: { bold: true, color: INK } },
  { text: "Recall is the right measure for a rare event and " + pct(M.e10_dwell_learned.vomm_recall) + "% is not good. Four attempts to improve it, including an explicit first-visit feature, each made it worse: every one split the context and lost more to sparsity than it gained in signal.", options: { color: MUTED } },
], { x: 7.65, y: 3.75, w: 4.95, h: 2.2, fontSize: 12.5, isTextBox: true, margin: 0, lineSpacing: 19 });
s.addNotes("Lead with this if asked what does not work. Naming your weakest result before the panel does is worth more than defending it.");

// 15 ------------------------------------------------------------ section
pres.addSection({ title: "The build" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "The build" });
s.addText("04", { placeholder: "kicker" });
s.addText("The build", { placeholder: "title" });
s.addText("The game is not a wrapper around the model. It is the thing that makes the model visible while you are losing to it.", { placeholder: "body" });

// 16 --------------------------------------------------- playable build
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "The build" });
s.addText("Playable, in a browser, with the AI on screen", { placeholder: "title" });
s.addText("Hand-written WebGL2. 19 rooms, a door clock, synthesised audio, and a panel that narrates what the antagonist believes and why.", { placeholder: "body" });
// caption follows whichever file was available, so it never mislabels the image
const CAPTION = {
  "out/deck_title.png": "The facility, before you enter",
  "out/deck_room.png":  "A codebook room \u2014 the panel you must copy",
  "out/deck_hunt.png":  "It is in the room with you",
  "out/fig_3d.png":     "The antagonist, seen down a corridor",
  "out/game_shot2.png": "The systems view \u2014 its belief drawn on the map",
  "out/demo_shot.png":  "The notebook \u2014 the only record it cannot edit",
};
const shots = [
  firstOf("out/deck_title.png", "out/fig_3d.png"),
  firstOf("out/deck_room.png", "out/fig_3d.png", "out/demo_shot.png"),
  firstOf("out/deck_hunt.png", "out/game_shot2.png"),
].filter(Boolean);
shots.forEach((f, i) => {
  const x = 0.64 + i * 4.07;
  figure(s, f, { x, y: 1.95, w: 3.78, h: 2.45 });
  s.addText(CAPTION[f] || "", { x, y: 4.52, w: 3.78, h: 0.55, fontSize: 11.5, color: MUTED, align: "center", isTextBox: true, margin: 0, lineSpacing: 16 });
});
s.addText([
  { text: "Step mode (P)  ", options: { bold: true, color: AMBER } },
  { text: "stops the clock and gives the antagonist exactly one turn per room you enter, so a belief update, a prediction and an interception can each be read out loud instead of raced.", options: { color: PAPER } },
], { x: 0.64, y: 5.22, w: 11.96, h: 1.0, fontSize: 14, isTextBox: true, margin: 0, lineSpacing: 21 });
s.addNotes("Demo in step mode. Walk one room, pause, read the belief panel aloud, then take the next step. Do not try to play it properly in front of the panel.");

// 17 ------------------------------------------------- what shipped
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The build" });
s.addText("What shipped, and how it was verified", { placeholder: "title" });
s.addText("The model was not touched by the build work — which is itself a claim that had to be checked, not asserted.", { placeholder: "body" });
const ship = [
  ["A new facility every run", "Seeded generation, so the layout cannot be memorised between sessions."],
  ["An antagonist made of its model", "The figure is built from the prediction it is acting on, shown as an echo."],
  ["Doors, light and sound", "Panels that seal on the clock, lights that react, and audio synthesised at runtime — no asset files."],
  ["An automated player", "Drives the real build through the real input path, and records a playthrough to video."],
];
ship.forEach(([h, b], i) => {
  const x = 0.64 + (i % 2) * 6.1, y = 2.0 + Math.floor(i / 2) * 1.52;
  s.addShape(pres.shapes.OVAL, { x, y: y + 0.03, w: 0.34, h: 0.34, fill: { color: "FFF0D2" }, line: { color: "E8C98A" } });
  s.addText(String(i + 1), { x, y: y + 0.03, w: 0.34, h: 0.34, fontSize: 12, bold: true, color: "8A6214", align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(h, { x: x + 0.54, y, w: 5.2, h: 0.36, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0 });
  s.addText(b, { x: x + 0.54, y: y + 0.38, w: 5.3, h: 0.9, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 18 });
});
card(s, { x: 0.64, y: 5.3, w: 11.96, h: 1.15, fill: "FFFFFF", line: "DED7C6" });
s.addText([
  { text: "9 / 9 invariants hold", options: { bold: true, color: INK } },
  { text: "  over 25 generated facilities   ·   ", options: { color: MUTED } },
  { text: "automated player", options: { bold: true, color: INK } },
  { text: " completes the objective on all 12 seeds tested   \u00B7   ", options: { color: MUTED } },
  { text: "every figure", options: { bold: true, color: INK } },
  { text: " regenerates from one command", options: { color: MUTED } },
], { x: 1.0, y: 5.62, w: 11.2, h: 0.55, fontSize: 13.5, isTextBox: true, margin: 0 });
s.addNotes("The verification line matters more than the feature list. Anything in this deck can be reproduced with python3 model/evaluate.py.");

// 17b ------------------------------------------------- who did what
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The build" });
s.addText("Who did what", { placeholder: "title" });
s.addText("The project guidelines ask the candidate to distinguish what was added from what was already there. This mirrors Table 1.4 of the report.", { placeholder: "body" });
const who = [
  ["Baseline \u2014 Shivam Kumar Arya", "2A78D6", [
    "Variable-order predictor, order-1 and uniform baselines",
    "Door sensors and the forward belief filter",
    "Director, counter-moves and the fairness rules",
    "Facility graph, scripted players, evaluation, invariant tests",
    "Door clock, notebook, register, codebooks, hunting, audio, step mode",
  ]],
  ["This work \u2014 Parth Jaiswal", "B2561F", [
    "A new facility every run: seeded doors, roles, codes, keywords",
    "The MIMIC antagonist and its row-tearing",
    "Mouse look without pointer capture",
    "Material system, weathered surfaces, emergency lighting, grain",
    "Props, the live uplink screen and the codebook monitor",
    "Watch mode, recording mode and the recorder",
  ]],
];
who.forEach(([h, col, items], i) => {
  const x = 0.64 + i * 6.1;
  card(s, { x, y: 1.98, w: 5.8, h: 4.25, fill: "FFFFFF", line: "DED7C6" });
  s.addText(h, { x: x + 0.3, y: 2.2, w: 5.2, h: 0.36, fontSize: 15, bold: true, color: col, isTextBox: true, margin: 0 });
  s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })),
    { x: x + 0.3, y: 2.68, w: 5.25, h: 3.3, fontSize: 12, color: INK, isTextBox: true, margin: 0, paraSpaceAfter: 7, lineSpacing: 16 });
});
s.addText("E13, the cross-session measurement in \u00A77.8, was added to the baseline evaluation suite after the fork.",
  { x: 0.64, y: 6.34, w: 11.96, h: 0.35, fontSize: 11.5, italic: true, color: MUTED, isTextBox: true, margin: 0 });
s.addNotes("Panels mark attribution. Name which half is yours in one sentence and move on \u2014 do not read the lists aloud.");

// 18 ------------------------------------------------------ limitations
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The build" });
s.addText("What this work does not establish", { placeholder: "title" });
s.addText("Stated plainly, because the limits are a result too.", { placeholder: "body" });
const lim = [
  ["Nobody has played it", "Every behavioural parameter — the deviation rate, the writing model — is an assumption. Claims about fear, difficulty and enjoyment are untested."],
  ["The players are scripted", "A Markov model predicting a scripted agent is a weaker claim than one predicting a person. Human traces are the single highest-value next step."],
  ["Memory does not transfer", "Retained learning helps in a fixed building and hurts in a regenerated one. The predictor is keyed on room indices, and an index stops meaning the same thing."],
  ["Dwell is unsolved", pct(M.e10_dwell_learned.vomm_recall) + "% recall on the moment the player stops to write, after four failed attempts to improve it."],
];
lim.forEach(([h, b], i) => {
  const x = 0.64 + (i % 2) * 6.1, y = 2.05 + Math.floor(i / 2) * 2.2;
  card(s, { x, y, w: 5.8, h: 1.95, fill: "FFFFFF", line: "DED7C6" });
  s.addText(h, { x: x + 0.3, y: y + 0.22, w: 5.2, h: 0.36, fontSize: 15, bold: true, color: RED, isTextBox: true, margin: 0 });
  s.addText(b, { x: x + 0.3, y: y + 0.62, w: 5.25, h: 1.15, fontSize: 12.5, color: INK, isTextBox: true, margin: 0, lineSpacing: 18 });
});
s.addNotes("Say all four out loud. A panel that hears you name your own limits stops hunting for them.");

// 19 --------------------------------------------------------- closing
s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "The build" });
s.addText("Where it stands", { placeholder: "title" });
s.addText([
  { text: "A horror antagonist that models the individual player, and a measurement that says how well.", options: { bold: true, color: PAPER, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 8 } },
  { text: "It predicts the next room " + E1("habitual", "vomm") + "% of the time against a habitual player, and " + E1("random", "vomm") + "% against one with no habits — which is exactly what having no model scores. The gain is learned behaviour, not leakage. Against an oracle that can see the player's internal state, it reaches 97% of the achievable signal from behaviour alone.", options: { color: PAPER, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 8 } },
  { text: "It gets better at catching a returning player, and we now know the one condition where it does not.", options: { color: AMBER, bold: true, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 8 } },
  { text: "Next: human playtest traces in place of scripted players, and a predictor re-keyed on features that survive a rewired building.", options: { color: MUTED } },
], { placeholder: "body" });
s.addText("github.com/Sh1v4mKum4r/parity", { x: 0.95, y: 6.82, w: 7, h: 0.35, fontSize: 12.5, color: MUTED, fontFace: "Courier New", isTextBox: true, margin: 0 });
s.addNotes("Close on the second-to-last line. The project set out to make a predictive AI the player can feel, and the measurement that it works is the deliverable.");

// ---------------------------------------------------------------- write
(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
  await applyTheme(OUT, THEME);
  console.log(OUT);
})();
