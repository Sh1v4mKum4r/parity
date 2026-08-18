"""Review deck. Structured to the four marking rubrics:
   Domain/Problem (5) · Literature Review (5) · Methodology (5) · System Design (5)
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches as In, Pt
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).parent.parent
M = json.loads((ROOT / "out" / "metrics.json").read_text())
E4 = M["e4_pursuit"]; E5 = M["e5_disruption"]
E6U, E6S = M["e6_sabotage"], M["e6_sabotage_skewed"]
E7 = M["e7_scaling"]; E8 = M["e8_waiting"]
E9 = M["e9_dwell"]; E10 = M["e10_dwell_learned"]
R_CTL = E4["vomm-intercept"]["per_1000"] / E4["random-walk"]["per_1000"]
R_HUB = E4["vomm-intercept"]["per_1000"] / E4["hub-camp"]["per_1000"]
SIZES = sorted(int(k) for k in E7)

INK, MUT, ACC, LINE, BG = C(0x16,0x18,0x1a), C(0x6b,0x71,0x78), C(0x2a,0x78,0xd6), C(0xd8,0xdc,0xe0), C(0xfc,0xfc,0xfb)
GRN, ORG = C(0x1b,0xaf,0x7a), C(0xeb,0x68,0x34)
FONT = "Arial"

prs = Presentation(); prs.slide_width, prs.slide_height = In(13.333), In(7.5)
BLANK = prs.slide_layouts[6]
W = 13.333


def slide(bg=BG):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = bg
    return s


def tb(s, x, y, w, h, text, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT,
       space=6, line=1.25, font=FONT):
    box = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space); p.line_spacing = line
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = font
    return box


def header(s, kicker, title):
    tb(s, 0.72, 0.46, 11.9, 0.3, kicker.upper(), size=10.5, bold=True, color=ACC)
    tb(s, 0.72, 0.82, 11.9, 0.9, title, size=28, bold=True)
    ln = s.shapes.add_shape(1, In(0.72), In(1.62), In(11.9), In(0.02))
    ln.fill.solid(); ln.fill.fore_color.rgb = LINE; ln.line.fill.background(); ln.shadow.inherit = False


def bullets(s, items, x=0.72, y=1.95, w=11.9, size=15, gap=13):
    box = s.shapes.add_textbox(In(x), In(y), In(w), In(4.9))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        head, body = (it if isinstance(it, tuple) else (None, it))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap); p.line_spacing = 1.3
        if head:
            r = p.add_run(); r.text = head + "  "
            r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = INK; r.font.name = FONT
        r = p.add_run(); r.text = body
        r.font.size = Pt(size); r.font.color.rgb = MUT if head else INK; r.font.name = FONT
    return box


def table(s, rows, x=0.72, y=1.95, w=11.9, h=None, col_w=None, size=11.5, head_size=9.5):
    nr, nc = len(rows), len(rows[0])
    h = h or min(0.42 * nr, 4.9)
    shp = s.shapes.add_table(nr, nc, In(x), In(y), In(w), In(h))
    t = shp.table
    if col_w:
        for i, cw in enumerate(col_w): t.columns[i].width = In(cw)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci)
            cell.text = str(val)
            cell.margin_left = In(0.08); cell.margin_right = In(0.08)
            cell.margin_top = In(0.04); cell.margin_bottom = In(0.04)
            cell.fill.solid(); cell.fill.fore_color.rgb = C(0xf4,0xf6,0xf8) if ri == 0 else BG
            p = cell.text_frame.paragraphs[0]
            p.line_spacing = 1.15
            for r in p.runs:
                r.font.size = Pt(head_size if ri == 0 else size)
                r.font.bold = ri == 0
                r.font.color.rgb = MUT if ri == 0 else INK
                r.font.name = FONT
    return t


def picture(s, name, x, y, w):
    return s.shapes.add_picture(str(ROOT / "out" / name), In(x), In(y), width=In(w))


def rubric_chip(s, text):
    tb(s, 0.72, 6.86, 11.9, 0.3, text, size=9.5, color=MUT)


# ---------------------------------------------------------------- 1 title
s = slide()
bar = s.shapes.add_shape(1, In(0), In(0), In(0.18), In(7.5))
bar.fill.solid(); bar.fill.fore_color.rgb = ACC; bar.line.fill.background(); bar.shadow.inherit = False
tb(s, 0.95, 2.05, 11.5, 1.0, "PARITY", size=58, bold=True)
tb(s, 0.95, 3.15, 11.0, 0.9, "An Adaptive Horror Game Driven by\nOnline Player-Trajectory Prediction",
   size=21, color=MUT, line=1.35)
ln = s.shapes.add_shape(1, In(0.98), In(4.35), In(2.4), In(0.03))
ln.fill.solid(); ln.fill.fore_color.rgb = ACC; ln.line.fill.background(); ln.shadow.inherit = False
tb(s, 0.95, 4.66, 11.0, 0.9, "Shivam Kumar\nVellore Institute of Technology  ·  Project Review  ·  18 August 2026",
   size=13, color=MUT, line=1.5)

# ---------------------------------------------------------------- 2 coverage
s = slide(); header(s, "What this review covers", "Mapped to the marking rubric")
table(s, [
    ["Rubric", "Where it is answered", "Evidence"],
    ["Knowledge on domain / problem statement", "Sections 1–3 of this deck", "Gap analysis over 22 works"],
    ["Literature review (min. 15 recent papers)", "Sections 4–7", "22 works, 20 from 2023 or later"],
    ["Design of proposed methodology", "Sections 8–11", "Formal model + evaluation protocol"],
    ["Module description / system design", "Sections 12–13", "8 modules, implemented and tested"],
    ["Beyond the rubric", "Sections 14–24", "Ten experiments, 9 invariants, a live demo"],
], col_w=[4.3, 4.0, 3.6], size=12.5)

# ---------------------------------------------------------------- 3 domain
s = slide(); header(s, "1 · Domain", "Game AI has optimised for competence, not adaptation")
bullets(s, [
    ("Player modelling —", "inferring player intent and state from behavioural telemetry."),
    ("Adaptive AI and DDA —", "acting on that inference to reshape the experience."),
    ("Procedural generation —", "changing the world itself, not only the agents in it."),
    ("", ""),
    ("Horror is where this matters most, and is least explored.", ""),
    ("", "Horror depends on uncertainty. Every horror game degrades as the player learns it: routes get memorised, spawns get learned, the monster becomes a timing puzzle."),
    ("", "The genre's central failure mode is that mastery destroys the product."),
], size=15)

# ---------------------------------------------------------------- 4 problem
s = slide(); header(s, "2 · Problem statement", "Static AI is learnable. Random AI is unfair.")
box = s.shapes.add_shape(1, In(0.72), In(2.0), In(0.05), In(2.35))
box.fill.solid(); box.fill.fore_color.rgb = ACC; box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.05, 2.02, 11.4, 2.35,
   "Existing horror antagonists are static or randomised. Static AI is learnable and stops being frightening. "
   "Randomised AI is unlearnable and therefore reads as unfair rather than intelligent. Neither adapts to the "
   "specific player.\n"
   "PARITY proposes a third option: an antagonist that builds an online behavioural model of the individual "
   "player and acts on its predictions — intercepting where the player is going rather than chasing where they "
   "are, and degrading the information the player has come to depend on.",
   size=14, line=1.35, space=10)
table(s, [
    ["Challenge", "Why it is hard here"],
    ["Cold start", "Must be interesting in the first two minutes, with no prior data on this player"],
    ["Legibility", "A model the player cannot perceive is, to the player, no model at all"],
    ["Fairness", "An antagonist that is merely stronger is not scarier — it is unfair"],
    ["Evaluation", "'Is it scary?' does not scale to the playtesting a solo project can do"],
], y=4.72, col_w=[2.6, 9.3], size=12.5)

# ---------------------------------------------------------------- 5 objectives
s = slide(); header(s, "3 · Aim and objectives", "Demonstrate that the model both learns and matters")
tb(s, 0.72, 1.95, 11.9, 0.6,
   "Aim — build a first-person horror game whose antagonist is driven by a live, per-player predictive "
   "model, and demonstrate quantitatively that the model both learns and changes the game.", size=15, color=MUT, line=1.35)
table(s, [
    ["#", "Objective", "Status"],
    ["O1", "Formalise the facility as a mutable room graph with runtime topology edits", "Done"],
    ["O2", "Online next-room predictor that learns from the first move", "Done"],
    ["O3", "Beat a no-model control and an order-1 Markov baseline", "Done"],
    ["O4", "Learn nothing from a random player (no leakage)", "Done"],
    ["O5", "Show better prediction yields a more dangerous antagonist", "Done"],
    ["O6", "Implement and measure all four Director counter-moves", "Done"],
    ["O7", "Make the model legible to the player in-game", "Demo built"],
    ["O8", "Ship the first-person Godot vertical slice", "In progress"],
], y=2.95, col_w=[0.65, 9.05, 2.2], size=12.5)

# ---------------------------------------------------------------- 6-9 literature
s = slide(); header(s, "4 · Literature review", "22 works · 20 published 2023 or later")
table(s, [
    ["Theme", "Works", "What it settles for this project"],
    ["Player modelling & behaviour prediction", "5", "Behavioural signals alone suffice; models should be inspectable"],
    ["Adaptive game AI & dynamic difficulty", "7", "State of the art adapts parameters, rarely placement"],
    ["Procedural generation of mutable levels", "3", "Graph-based generation with connectivity guarantees"],
    ["Sequence & next-location prediction", "5", "The methodological core — VOMM and its successors"],
    ["Fear as a measurable experience", "2", "Unfairness destroys fear; behaviour reveals fear"],
], col_w=[4.5, 1.1, 6.3], size=13)
tb(s, 0.72, 5.2, 11.9, 1.4,
   "Selection criteria — peer-reviewed or arXiv-indexed work addressing player behaviour prediction, "
   "runtime game adaptation, or discrete-trajectory prediction. Priority given to 2023-2026 publications; "
   "one foundational 2004 work is retained because it is the formal basis of the proposed model.",
   size=12.5, color=MUT, line=1.35)

s = slide(); header(s, "5 · Literature review", "Player modelling and adaptive game AI")
table(s, [
    ["Work", "Yr", "Relevance"],
    ["Lin et al., Open Player Modeling (2603.26915)", "26", "Player models should be inspectable — motivates our overlay"],
    ["Halina et al., Playtrace Reconstructive Partitioning (2607.12097)", "26", "Playtraces as the level's primary representation"],
    ["Carlier et al., Personalization in Serious Games (2411.18500)", "24", "Model/method/adaptation split mirrors our architecture"],
    ["Dehpanah et al., Player Modeling from Behavioral Signals (2112.04379)", "21", "Raw behaviour suffices — no biometrics needed"],
    ["Romeo et al., NTRL: RL for DDA in D&D (2506.19530)", "25", "Closest analogue — adapts encounters, not stats"],
    ["Lopes et al., Affect-Driven Game Adaptation review (2505.01351)", "25", "Identifies evaluation as the field's weak point"],
    ["Fuchs et al., Personalized DDA (2408.06818)", "24", "Imitation + RL personalisation; far heavier to train"],
    ["Cafri et al., DDA with Brain Waves (2504.13965)", "25", "Biometric branch — we deliberately avoid extra hardware"],
], col_w=[6.4, 0.6, 4.9], size=11.5, head_size=9)

s = slide(); header(s, "6 · Literature review", "Level generation and trajectory prediction")
table(s, [
    ["Work", "Yr", "Relevance"],
    ["Fiuza Vieira et al., Mansions and Dungeons generation (2606.03857)", "26", "Graph generation of exactly our building type"],
    ["Earle et al., Level Design as Multi-Agent RL (2510.04862)", "25", "Framing for a Director that edits the level at runtime"],
    ["Özkan, Procedural Level Design with Deep RL (2510.15120)", "25", "Contrast to our constraint-checked mutation"],
    ["Begleiter, El-Yaniv & Yona, Variable Order Markov Models, JAIR 22", "04", "FOUNDATIONAL — the formal basis of our predictor"],
    ["Wu et al., Beyond Regularity: chaotic mobility (2509.11713)", "25", "Same task shape; handles irregular trajectories"],
    ["Deng et al., STRelay location prediction (2508.16620)", "25", "The natural upgrade path from VOMM"],
    ["Liu et al., MoE Personalized Next-Location (2505.24597)", "25", "Per-individual personalisation of prediction"],
    ["Soni et al., Predicting Your Next Move & Privacy (2507.08843)", "25", "Privacy framing for a persisted per-player model"],
    ["Zhang et al., VRMN-bD fear-response dataset (2401.12133)", "24", "Fear is detectable in ordinary behavioural signals"],
    ["Zhang et al., Decoding Fear in VR horror (2312.15582)", "23", "Sources the constraint that unfairness destroys fear"],
], col_w=[6.4, 0.6, 4.9], size=11, head_size=9)

s = slide(); header(s, "7 · Research gap", "Three gaps, consistent across the literature")
bullets(s, [
    ("1 · DDA adapts parameters, not position.",
     "The literature overwhelmingly tunes difficulty magnitude — enemy health, encounter budget, puzzle complexity. Almost none adapt where the antagonist chooses to be, from a model of the individual player."),
    ("2 · Next-location prediction is never used adversarially.",
     "Trajectory prediction is mature, but is applied to service delivery and urban analytics. Its use as a real-time adversary against the person being predicted is unexplored."),
    ("3 · Adaptation is invisible, and therefore unevaluated.",
     "Lopes et al. (2025) identify evaluation as the weak point. Adaptive systems are rarely surfaced to the player or measured against a no-model control."),
], size=14.5, gap=15)
box = s.shapes.add_shape(1, In(0.72), In(5.75), In(11.9), In(1.0))
box.fill.solid(); box.fill.fore_color.rgb = C(0xf1,0xf6,0xfc); box.line.color.rgb = ACC
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.0, 5.98, 11.3, 0.7,
   "PARITY addresses all three: online trajectory prediction applied adversarially, adapting antagonist "
   "placement and world state rather than parameters, evaluated against explicit controls with the model on screen.",
   size=13.5, line=1.3)

# ---------------------------------------------------------------- 10-13 methodology
s = slide(); header(s, "8 · Methodology — formalisation", "Prediction over a room graph")
bullets(s, [
    ("", "The facility is an undirected graph G = (V, E): rooms are vertices, doors are edges. The player produces a trajectory h = (v₁, v₂, …, vₜ)."),
    ("The clock —", "lockdown, then a short window when every door unlocks, then lockdown. Decisions happen only at windows. Sealed in between, the player draws, copies codebooks and stages the register — in real time."),
    ("Prediction task —", "at each window the player takes a door OR declines to move. Estimate P(v(t+1) = c | h) over N(vₜ) ∪ {vₜ}."),
    ("Staying is a first-class action —", "not the absence of one. Players linger where there is something to record, so dwell is informative. The antagonist obeys the same clock, so lockdown is safe and all danger is at the window."),
], size=15)
box = s.shapes.add_shape(1, In(0.72), In(3.45), In(11.9), In(2.05))
box.fill.solid(); box.fill.fore_color.rgb = C(0xf4,0xf6,0xf8); box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.05, 3.66, 11.3, 1.7,
   "Why an order-1 Markov model is structurally insufficient\n\n"
   "Real players run routes, so the same room has different successors depending on how it was entered. "
   "In our test facility, one room appears five times in a habitual circuit with four different successors. "
   "Order-1 cannot separate them. Longer context resolves it — but long contexts are sparse.",
   size=13.5, line=1.32, space=8)
tb(s, 0.72, 5.72, 11.9, 0.8,
   "A variable-order Markov model with back-off resolves both pressures at once.", size=16, bold=True, color=ACC)

s = slide(); header(s, "9 · Methodology — the model", "Variable-order Markov with Witten-Bell back-off")
box = s.shapes.add_shape(1, In(0.72), In(2.0), In(11.9), In(1.5))
box.fill.solid(); box.fill.fore_color.rgb = C(0x16,0x18,0x1a); box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.1, 2.25, 11.2, 1.1,
   "P_o(x | ctx)  =  w · f_o(x | ctx)  +  (1 − w) · P_(o−1)(x | ctx[1:])\n"
   "w  =  C(ctx) / (C(ctx) + α)                    α = 1.6,  k = 4",
   size=16, color=C(0xff,0xff,0xff), font="Consolas", line=1.6, space=4)
tb(s, 0.72, 3.72, 11.9, 0.4,
   "Interpolate from the longest available context down to uniform. Long contexts dominate once "
   "well-supported, and decay gracefully when they are not.", size=13.5, color=MUT, line=1.3)
table(s, [
    ["Property", "Why it matters for this application"],
    ["Learns online from the first move", "No pre-training corpus — solves the cold-start problem"],
    ["Persists across runs", "The antagonist remembers you between deaths, as your notebook does"],
    ["Inspectable", "Every prediction decomposes to 'context → outcome, n observations'"],
    ["Cheap", "Hash-map counter updates; negligible per-frame cost"],
], y=4.5, col_w=[3.9, 8.0], size=13)

s = slide(); header(s, "10 · Methodology — belief vs. behaviour", "The Director is separate from the Predictor")
tb(s, 0.72, 1.95, 11.9, 0.5,
   "The Predictor outputs beliefs. The Director decides what to do with them, scoring each counter-move "
   "by expected disruption × confidence. The model can be upgraded without re-tuning game feel.",
   size=14.5, color=MUT, line=1.3)
table(s, [
    ["Counter-move", "Trigger", "Status"],
    ["Intercept", "Rolls the model forward; meets the player where they will be", "Measured (§16, 17)"],
    ["Rewire a room ahead", "High confidence on a route — change it before they arrive", "Measured (§18)"],
    ["Seal a shortcut", "An edge with high traversal frequency", "Measured (§18)"],
    ["Poison a codebook", "A recorded entry the player is predicted to need again", "Measured (§19)"],
], y=2.85, col_w=[2.8, 6.9, 2.2], size=12.5)
tb(s, 0.72, 4.95, 11.9, 0.35, "FAIRNESS CONSTRAINTS", size=10.5, bold=True, color=ORG)
bullets(s, [
    ("1", "No mutation is ever applied to anything currently visible to the player."),
    ("2", "Confidence gating — below threshold it hunts conventionally, exploiting only what it knows."),
    ("3", "Solvability invariant — every mutation is checked for reachability and reverted if it would soft-lock the run."),
], y=5.35, size=13.5, gap=6)

s = slide(); header(s, "11 · Methodology — evaluation protocol", "Headless, bot-driven, prequential")
bullets(s, [
    ("", "Human playtesting does not scale to a solo project. Three scripted players stand in for humans, so thousands of games run headlessly:"),
], size=14.5)
table(s, [
    ["Scripted player", "Models", "Expected result"],
    ["HabitualBot", "A player who has learned the level and runs routes", "Model should win decisively"],
    ["ExplorerBot", "A first-time player sweeping systematically", "Model should win"],
    ["EvasiveBot", "Declines 35% of windows on purpose to break the pattern", "The player's counter-play"],
    ["RandomBot", "Uniform over doors and staying — no habit at all", "Model MUST NOT beat baseline"],
], y=2.75, col_w=[2.6, 5.9, 3.4], size=12.5)
box = s.shapes.add_shape(1, In(0.72), In(4.55), In(11.9), In(1.45))
box.fill.solid(); box.fill.fore_color.rgb = C(0xf1,0xf6,0xfc); box.line.color.rgb = ACC
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 4.78, 11.3, 1.1,
   "The control is the most important experiment.\n"
   "Against a random player the model must FAIL to beat baseline. A model that appears to predict a random "
   "walk is measuring something it should not have access to. All accuracy is prequential — every prediction "
   "is made before its outcome is observed, so there is no train/test leakage by construction.",
   size=13.5, line=1.32, space=3)

# ---------------------------------------------------------------- 14-15 system design
s = slide(); header(s, "12 · System design", "Eight modules across three layers")
picture(s, "fig_arch.png", 1.47, 1.9, 10.4)

s = slide(); header(s, "13 · Module description", "Responsibilities and dependencies")
table(s, [
    ["Module", "Responsibility", "Depends on"],
    ["Facility", "Room graph; generation; rewire / seal; connectivity and reachability queries", "—"],
    ["Cipher", "Per-room lookup tables, inbound sequences, 9-cell register, transmit validation", "—"],
    ["Sabotage", "The single choke point for all world mutation — every lie is logged and replayable", "Facility, Cipher"],
    ["Telemetry", "Room dwell, edge traversals, route repeats, verify duration, flee direction", "—"],
    ["Predictor", "VOMM: predict / observe / top_habit / confidence. Persists across runs", "Telemetry"],
    ["Director", "Scores and selects counter-moves from beliefs. Confidence-gated", "Predictor"],
    ["Entity", "Perception, navigation, patrol / hunt / ambush. Contains no learning", "Director, Facility"],
    ["Notebook", "In-world vector editor and serialisation. Reads no game state", "—"],
], col_w=[1.85, 7.65, 2.4], size=12, head_size=9)
tb(s, 0.72, 5.95, 11.9, 0.9,
   "Two decisions worth defending — Sabotage as sole mutator makes 'did the AI cheat or did I misread my notes?' "
   "a tractable question. The Notebook sits outside the data loop: it is the only channel the Director cannot touch, "
   "which is what makes it the player's counter-move rather than decoration.",
   size=12.5, color=MUT, line=1.3)

# ---------------------------------------------------------------- 16-19 results
s = slide(); header(s, "14 · Results — prediction accuracy", "10-room facility · 1200 steps × 12 seeds")
picture(s, "fig_accuracy.png", 2.27, 1.85, 8.8)
tb(s, 0.72, 6.6, 11.9, 0.6,
   "Read the control first: against a random player the model performs identically to no model at all. "
   "The gains against structured players are therefore learned habit, not leakage.",
   size=13, color=MUT, line=1.3)

s = slide(); header(s, "15 · Results — learning speed", "Cold start solved empirically")
picture(s, "fig_learning.png", 2.27, 1.85, 8.8)
_c = M["e2_learning"]["curves"]["vomm"]; _w = M["e2_learning"]["window"]
_plateau = sum(_c[5:15]) / len(_c[5:15])
tb(s, 0.72, 6.6, 11.9, 0.6,
   f"Rolling top-1 accuracy rises from {_c[0]*100:.0f}% to {_plateau*100:.0f}% within roughly {_w*3} observed "
   "moves — under a minute of play.", size=13, color=MUT, line=1.3)

s = slide(); header(s, "16 · Results — does prediction matter?", "Embodied pursuit: the entity must intercept, not teleport")
picture(s, "fig_capture.png", 2.37, 1.88, 8.6)
tb(s, 0.72, 6.22, 11.9, 1.05,
   f"Any model-driven antagonist beats the non-learning ones — {R_CTL:.1f}× the random control and {R_HUB:.1f}× hub-camping. "
   "But the models are within noise of each other, and five-step lookahead is now slightly WORSE than one-step: at "
   "61% single-step accuracy, rollout error compounds faster than the extra foresight pays. Lookahead helps an "
   "accurate model and hurts an uncertain one.", size=12, color=MUT, line=1.28)


# ---------------------------------------------------------------- scaling
s = slide(); header(s, "17 · Results — does the advantage hold at scale?", "Hub-camping only looks good on a small map")
picture(s, "fig_scaling.png", 2.5, 1.85, 8.4)
tb(s, 0.72, 6.15, 11.9, 1.0,
   f"On {SIZES[0]} rooms with one dominant junction the player has nowhere else to go, so a naive heuristic looks "
   f"competitive for reasons unrelated to intelligence. As the facility grows, hub-camping decays fastest and the "
   f"interceptor's advantage widens from {E7[str(SIZES[0])]['advantage_vs_hub']:.2f}× to {E7[str(SIZES[-1])]['advantage_vs_hub']:.2f}×. "
   "The small-facility result understates the value of prediction.", size=12.5, color=MUT, line=1.3)


# ---------------------------------------------------------------- world edits
s = slide(); header(s, "18 · Results — do the world edits matter?", "Interception is only one of four counter-moves")
picture(s, "fig_disruption.png", 2.5, 1.9, 8.4)
tb(s, 0.72, 6.05, 11.9, 1.1,
   f"The entity is removed entirely here, isolating topology mutation. Sealing and rewiring ahead of the player "
   f"raises the cost of completing an objective by {E5['full-director']['overhead_pct']:.0f}% "
   f"({E5['no-director']['moves_per_lap']:.1f} to {E5['full-director']['moves_per_lap']:.1f} moves per lap). Every one of the "
   f"{E5['full-director']['actions']['rewire']} rewires and {E5['full-director']['actions']['seal']} seals passed the reachability "
   "check — no run was ever soft-locked.", size=13, color=MUT, line=1.3)

# ---------------------------------------------------------------- conditional result
s = slide(); header(s, "19 · Results — is the sabotage aimed?", "A conditional result, reported as such")
tb(s, 0.72, 1.95, 11.9, 0.6,
   "A poisoned codebook only costs the player if they return to it, and costs more the sooner they do. "
   "Lower is better-aimed. Control: poison a recorded room at random.", size=14, color=MUT, line=1.3)
table(s, [
    ["Player's reliance on rooms", "Random targeting", "Model targeting", "Advantage"],
    ["Uniform — visits every codebook each lap",
     f"{E6U['random-target']['moves_until_revisit']:.1f}", f"{E6U['model-target']['moves_until_revisit']:.1f}",
     f"none ({E6U['model-target']['faster_pct']:+.1f}%)"],
    ["Uneven — leans on some rooms harder",
     f"{E6S['random-target']['moves_until_revisit']:.1f}", f"{E6S['model-target']['moves_until_revisit']:.1f}",
     f"{E6S['model-target']['faster_pct']:.0f}% faster"],
], y=2.85, col_w=[5.0, 2.4, 2.3, 2.2], size=13)
box = s.shapes.add_shape(1, In(0.72), In(4.3), In(11.9), In(1.75))
box.fill.solid(); box.fill.fore_color.rgb = C(0xff,0xf6,0xf0); box.line.color.rgb = ORG
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 4.55, 11.3, 1.35,
   "Reported as a negative result under the first condition.\n"
   "When the player relies on every room equally there is nothing for targeted sabotage to exploit, and model "
   "targeting performs no better than random. The counter-move earns its place only against a player with uneven "
   "habits. That is the realistic case — but the claim is conditional and is not overstated.",
   size=13.5, line=1.32, space=4)

# ---------------------------------------------------------------- waiting
s = slide(); header(s, "20 · Results — can the player fight back?", "A negative result, and the most useful one")
tb(s, 0.72, 1.95, 11.9, 0.55,
   "Waiting is the natural counter-play: if it moves to where you are going, do not go. A fair adaptive "
   "antagonist must be beatable this way. It is not.", size=14, color=MUT, line=1.3)
table(s, [
    ["Player", "Windows declined", "Model accuracy against them", "Captures / 1000"],
    ["Habitual", f"{E8['habitual']['windows_declined_pct']:.0f}%",
     f"{E8['habitual']['top1_accuracy']*100:.1f}%", f"{E8['habitual']['per_1000']:.0f}"],
    ["Evasive", f"{E8['evasive']['windows_declined_pct']:.0f}%",
     f"{E8['evasive']['top1_accuracy']*100:.1f}%", f"{E8['evasive']['per_1000']:.0f}"],
], y=2.75, col_w=[2.6, 3.0, 3.6, 2.7], size=13)
box = s.shapes.add_shape(1, In(0.72), In(4.15), In(11.9), In(2.15))
box.fill.solid(); box.fill.fore_color.rgb = C(0xff,0xf6,0xf0); box.line.color.rgb = ORG
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 4.40, 11.3, 1.75,
   "Evasion beats the model and loses to the outcome.\n"
   f"Declining a third of all windows costs the predictor {(E8['habitual']['top1_accuracy']-E8['evasive']['top1_accuracy'])*100:.1f} points of accuracy but reduces capture "
   f"risk by only {E8['evasive']['risk_reduction_pct']:.1f}%. The cause is the observation model, not the algorithm: the antagonist currently "
   "sees the player perfectly at every window, and under perfect observation standing still cannot conceal you — "
   "it only makes you a stationary target.\n"
   "Next iteration: sense the player through motion detectors on the doors instead of omniscience, turning this "
   "into a partially-observed prediction problem. This experiment is what identified that.",
   size=13, line=1.3, space=5)


# ---------------------------------------------------------------- dwell
s = slide(); header(s, "21 · Results — what it learns about your notebook", "Dwell is behaviour, not a parameter")
picture(s, "fig_dwell.png", 2.5, 1.82, 8.4)
tb(s, 0.72, 5.95, 11.9, 1.25,
   f"How long you linger is one of the most individual things you do — and it is the actionable signal: "
   f"'they will be in room D for three more windows' tells the antagonist how long it has to walk there. "
   f"A {E10['lift_points']:.0f}-point lift over the majority class. It is never wrong in rooms with nothing to record, and "
   f"right two thirds of the time where a codebook is — the uncertainty sits exactly where the real variation is. "
   f"An explicit dwell model adds nothing ({E9['dwell-aware']['improvement_pct']:+.1f}%): once staying is a legal action, the sequence "
   "model already represents it.", size=12, color=MUT, line=1.28)


# ---------------------------------------------------------------- verification
s = slide(); header(s, "22 · Verification", "Nine invariants, asserted over 25 generated facilities")
table(s, [
    ["Invariant", "Guards against"],
    ["Facility connected on construction", "Unplayable generated levels"],
    ["seal_door never disconnects", "The Director cutting the map in half"],
    ["rewire never disconnects", "The same, via door relocation"],
    ["Uplink reachable from every room after mutation", "Soft-locked, unwinnable runs"],
    ["Bots only move to adjacent rooms", "Silent teleportation corrupting telemetry"],
    ["Predictor output is a proper distribution", "Malformed probabilities"],
    ["VOMM approximates uniform on a random player", "Leakage in the evaluation"],
    ["Director never mutates a visible room", "Fairness rule 1"],
    ["Director never edits below its confidence gate", "Fairness rule 2"],
], col_w=[6.4, 5.5], size=12.5, head_size=9)
tb(s, 0.72, 6.35, 11.9, 0.5, "9 / 9 passing  ·  python3 model/test_invariants.py",
   size=14, bold=True, color=GRN)

# ---------------------------------------------------------------- 20 demo
s = slide(); header(s, "23 · Live demonstration", "The full loop, running")
bullets(s, [
    ("Room graph —", "live per-room predicted probabilities drawn on the facility."),
    ("Entity —", "moves to intercept where the model points, gated on confidence."),
    ("Codebooks and notebook —", "record entries; the Director silently poisons what you rely on."),
    ("All four counter-moves —", "intercept, seal, rewire and poison, with a live counter for each."),
    ("Hold position —", "decline the window and stay put, exactly as the model expects you might."),
    ("Live scoreboard —", "running VOMM accuracy against a no-model control, side by side."),
    ("Learned-rule readout —", "in plain language: 'from E you go to B, 100% of the time, 13 observations'."),
], size=15)
box = s.shapes.add_shape(1, In(0.72), In(5.0), In(11.9), In(1.5))
box.fill.solid(); box.fill.fore_color.rgb = C(0xf1,0xf6,0xfc); box.line.color.rgb = ACC
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 5.24, 11.3, 1.1,
   "Observed in a 102-window automated session\n"
   "The player declined 32 windows (31%) to finish pages. VOMM 47% vs. no-model 36%, 22 interceptions, and 2 of "
   "13 signals corrupted. The confidence gate is visible live: 'too unsure to intercept; hunting conventionally'.",
   size=15, line=1.4, space=4)


# ---------------------------------------------------------------- 21 roadmap
s = slide(); header(s, "24 · Roadmap", "Three of nine milestones complete")
table(s, [
    ["Milestone", "Deliverable", "State"],
    ["M0", "Headless simulation core, telemetry, bot harness", "Complete"],
    ["M1", "Predictor, baselines, controls, offline metrics and figures", "Complete"],
    ["M2", "Director and counter-moves, validated headless", "Complete"],
    ["M3", "Godot greybox first-person build + live prediction overlay", "Next"],
    ["M4", "Notebook vector editor and persistence", "Planned"],
    ["M5", "Entity polish, atmosphere, audio, human playtest", "Planned"],
    ["M6", "Door motion-sensors — partial observation, so waiting conceals", "Specified"],
    ["M7", "Polygonal room tiles; side count is the difficulty setting", "Specified"],
    ["M8", "Outbound register with pre-send tampering; sensor blackouts", "Specified"],
], col_w=[1.3, 8.4, 2.2], size=12.5)
tb(s, 0.72, 5.1, 11.9, 1.2,
   "Art direction for M3 is settled: a low-poly modular brutalist kit instantiated from the room graph, "
   "near-total darkness with a flashlight, heavy fog, and a retro post-processing pass — chosen because it "
   "minimises modelling cost while staying coherent. Modularity is not a style choice: rooms are rotated, "
   "added and removed at runtime, so they must be prefab-instantiated regardless.",
   size=13, color=MUT, line=1.35)

# ---------------------------------------------------------------- 22-23 references
refs = [
 "Lin, Z. et al. (2026). Unlocking Open-Player-Modeling-enhanced Game-Based Learning. arXiv:2603.26915",
 "Dehpanah, A. et al. (2021). Player Modeling using Behavioral Signals in Competitive Online Games. arXiv:2112.04379",
 "Carlier, S. et al. (2024). Personalization in Serious Games and Gamification for Healthcare. arXiv:2411.18500",
 "Halina, E. et al. (2026). Representing and Generating Levels Over Time through Playtrace Reconstructive Partitioning. arXiv:2607.12097",
 "Bazzaz, M. (2026). Player Perceptions of Generative AI in Games: A Steam Review Analysis. arXiv:2608.11539",
 "Romeo, C. et al. (2025). NTRL: Encounter Generation via RL for DDA in Dungeons and Dragons. arXiv:2506.19530",
 "Lopes, P. et al. (2025). Closing the Loop in Affect-Driven Game Adaptation: A Systematic Review. arXiv:2505.01351",
 "Cafri, N. et al. (2025). Dynamic Difficulty Adjustment With Brain Waves. arXiv:2504.13965",
 "Fuchs, R. et al. (2024). Personalized Dynamic Difficulty Adjustment. arXiv:2408.06818",
 "McConnell, M. et al. (2025). From Frustration to Fun: An Adaptive Puzzle Game Powered by Genetic Algorithm. arXiv:2509.23796",
 "Jarma Montoya, O. et al. (2026). Atari Games Challenge: Multimodal Player Experience Assessment. arXiv:2605.27261",
]
refs2 = [
 "Tripathi, P. et al. (2026). AI-Enabled Serious Games: Integrating Intelligence and Adaptivity. arXiv:2605.21962",
 "Fiuza Vieira, I. et al. (2026). A Novel Procedural Generation for Level Design of Mansions and Dungeons. arXiv:2606.03857",
 "Özkan, M. B. (2025). Procedural Game Level Design with Deep Reinforcement Learning. arXiv:2510.15120",
 "Earle, S. et al. (2025). Video Game Level Design as a Multi-Agent Reinforcement Learning Problem. arXiv:2510.04862",
 "Begleiter, R., El-Yaniv, R. & Yona, G. (2004). On Prediction Using Variable Order Markov Models. JAIR 22, 385–421. arXiv:1107.0051",
 "Wu, Y. et al. (2025). Beyond Regularity: Modeling Chaotic Mobility Patterns for Next Location Prediction. arXiv:2509.11713",
 "Deng, B. et al. (2025). STRelay: A Universal Spatio-Temporal Relaying Framework for Location Prediction. arXiv:2508.16620",
 "Liu, S. et al. (2025). Mixture-of-Experts for Personalized and Semantic-Aware Next Location Prediction. arXiv:2505.24597",
 "Soni, A. et al. (2025). Can We Predict Your Next Move Without Breaking Your Privacy? arXiv:2507.08843",
 "Zhang, H. et al. (2024). VRMN-bD: A Multi-modal Natural Behavior Dataset of Immersive Human Fear Responses. arXiv:2401.12133",
 "Zhang, H. et al. (2023). Decoding Fear: Exploring User Experiences in Virtual Reality Horror Games. arXiv:2312.15582",
]
for i, chunk in enumerate([refs, refs2]):
    s = slide(); header(s, "References", f"{i+1} of 2")
    box = s.shapes.add_textbox(In(0.72), In(1.95), In(11.9), In(5.0))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for j, r in enumerate(chunk):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.space_after = Pt(7); p.line_spacing = 1.2
        run = p.add_run(); run.text = f"{i*11 + j + 1}.  {r}"
        run.font.size = Pt(12); run.font.color.rgb = INK; run.font.name = FONT


# ---------------------------------------------------------------- speaker notes
NOTES = {
 1: "Pitch: a horror antagonist that builds a live behavioural model of the individual "
    "player and acts on its predictions. The model is the project; the game makes it legible.",
 2: "Point the panel at where each rubric item is answered. Do not linger.",
 3: "Game AI optimises for agents that PLAY well. Adapting to the specific person is a "
    "different, less-solved problem. Horror is where it matters most because the genre dies "
    "when the player learns it.",
 4: "Static AI is learnable and stops scaring. Random AI feels unfair. Neither adapts to you. "
    "If asked 'isn't this DDA?' — no: DDA tunes difficulty magnitude, this changes WHERE the "
    "antagonist chooses to be.",
 5: "Be explicit that the Godot build is NOT done. Do not let them think a 3D game exists.",
 6: "22 works, 20 from 2023 or later. State the selection criteria out loud.",
 7: "Do not read the table. Name two: Romeo (closest analogue) and Lopes (review that names "
    "evaluation as the field's weak point — the gap the bot harness addresses).",
 8: "Name Begleiter aloud — it is the formal basis of the model. If challenged on a 2004 paper "
    "in a 'recent' review: it is the foundational treatment, and four 2025 trajectory-prediction "
    "papers beside it are the modern line.",
 9: "Three gaps: DDA adapts parameters not position; trajectory prediction is never used "
    "adversarially; adaptation is invisible so it is never evaluated against a control.",
 10: "The clock is the thing to explain well. Lockdown, window, lockdown. You act only when the "
     "doors open — and STAYING is one of the choices. That matters: the model must predict "
     "whether you move at all, not just where. The antagonist obeys the same clock.",
 11: "Walk the equation slowly. w is a confidence weight: the more a context has been seen, the "
     "more the model trusts it; otherwise it backs off to shorter context.",
 12: "Predictor outputs beliefs, Director decides what to do. All four counter-moves are "
     "implemented AND measured — say so explicitly.",
 13: "The control is the strongest thing here. Against a random player the model MUST NOT beat "
     "baseline. Prequential evaluation means every prediction precedes its outcome — no leakage "
     "possible by construction. Note EvasiveBot: I built a bot specifically to try to beat my "
     "own AI.",
 14: "Two decisions to defend: Sabotage is the single mutator so every lie is logged and "
     "replayable; the Notebook sits outside the loop, which is what makes it the player's "
     "counter-move rather than decoration.",
 15: "Skim. It is here as module-level design evidence, not to be read aloud.",
 16: "Lead with the CONTROL column (27/26/27), not the 61%. Explain why the control matters "
     "before showing the win. If asked why accuracy is 61% and not higher: because staying is a "
     "legal move, and predicting whether someone moves at all is harder than predicting where. "
     "An earlier version of this work forbade waiting and scored 90% — that number was inflated "
     "and I corrected it.",
 17: "Cold start: the model is useful within about a minute of play, with no prior data on "
     "this player.",
 18: "Be straight here. Every model-driven antagonist beats the non-learning baselines, but the "
     "models are within noise of each other, and five-step lookahead is now slightly worse than "
     "one-step. That is expected: rollout error compounds, so lookahead helps an accurate model "
     "and hurts an uncertain one. Volunteer this before they find it.",
 19: "The answer to 'hub-camping is nearly as good'. It is only nearly as good on a small map. "
     "The advantage widens as the facility grows.",
 20: "The entity is REMOVED here — this isolates world editing from hunting. About 60% more "
     "moves per objective lap, and every mutation passed a reachability check, so no run was "
     "ever soft-locked.",
 21: "Volunteer this. Targeted sabotage gives NO advantage when the player relies on every room "
     "equally; it only pays off against uneven habits. Reporting a null is a strength.",
 22: "The most valuable slide in the deck, and it is a negative result. I built a bot to beat my "
     "own AI by waiting. It degrades the model's accuracy but barely reduces capture risk — "
     "because the antagonist currently sees everything, so standing still just makes you a "
     "stationary target. That diagnosis is what set the next milestone: sense the player through "
     "door motion-detectors instead of omniscience, which turns this into partially-observed "
     "prediction. If you only defend one slide well, defend this one.",
 23: "This slide exists because someone asked whether the time a player spends in their "
     "notebook is itself something to learn. It is — and the model already had. Lead with the "
     "plain-rooms bar: 100%, because it learned you never linger where there is nothing to "
     "record. The codebook bar at 67% is the honest one: it knows you may be writing, not when "
     "you will finish. Also say that an explicit dwell model made things slightly WORSE, because "
     "the sequence model already captures dwell once staying is a legal action.",
 24: "Nine invariants, 25 facilities, all passing. The two that matter: uplink reachable after "
     "mutation (the AI can never soft-lock you) and VOMM approximating uniform on a random "
     "player (no leakage). Offer to run it live — it takes seconds.",
 25: "Run the demo. Press auto-play and talk over it. Point at the belief panel, then the live "
     "accuracy comparison, then the learned-rule readout, then the counter-move counters.",
 26: "M0 to M2 done, M3 next; the 3D game does not exist yet. M6 to M8 are specified from the "
     "design work: door sensors and partial observation, polygonal room tiles where side count "
     "IS the difficulty setting, and the outbound register the AI can tamper with before you "
     "send. Say that the negative result on slide 22 is what prioritised M6.",
 27: "References 1 to 11.",
 28: "References 12 to 22.",
}

for idx, sl in enumerate(prs.slides, start=1):
    if idx in NOTES:
        tf = sl.notes_slide.notes_text_frame
        tf.text = NOTES[idx]

out = ROOT / "docs" / "PARITY-review-deck.pptx"
prs.save(out)
print("slides:", len(prs.slides.__iter__.__self__._sldIdLst), "->", out)
