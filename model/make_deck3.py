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



E1, E4, E5 = M["e1_accuracy"], M["e4_pursuit"], M["e5_disruption"]
E7, E10 = M["e7_scaling"], M["e10_dwell_learned"]
E11, E12 = M["e11_localisation"], M["e12_counterplay"]
E10 = M["e10_dwell_learned"]
SIZES = sorted(int(k) for k in E7)
COVS = sorted(E12, key=float, reverse=True)
pc = lambda k: f"{E1[k]['top1']*100:.1f}%"
cp = lambda cov, k: E12[cov][k]["per_lap"]
chg = lambda cov, k: E12[cov][k]["risk_change_pct"]

# ---------------------------------------------------------------- 1 title
s = slide()
bar = s.shapes.add_shape(1, In(0), In(0), In(0.18), In(7.5))
bar.fill.solid(); bar.fill.fore_color.rgb = ACC; bar.line.fill.background(); bar.shadow.inherit = False
tb(s, 0.95, 1.95, 11.5, 1.0, "PARITY", size=56, bold=True)
tb(s, 0.95, 3.02, 11.0, 0.9, "An Adaptive Horror Game Driven by\nOnline Player-Trajectory Prediction",
   size=20, color=MUT, line=1.35)
ln = s.shapes.add_shape(1, In(0.98), In(4.20), In(2.4), In(0.03))
ln.fill.solid(); ln.fill.fore_color.rgb = ACC; ln.line.fill.background(); ln.shadow.inherit = False
tb(s, 0.95, 4.52, 11.0, 1.2,
   "BCSE497J  ·  Project Review III  ·  Panel Review\n"
   "Shivam Kumar  ·  Vellore Institute of Technology  ·  16 September 2026",
   size=13, color=MUT, line=1.5)

# ---------------------------------------------------------------- 2 recap
s = slide(); header(s, "Where this stands", "One minute of context, then evidence")
tb(s, 0.72, 1.92, 11.9, 0.34, "WHAT THIS PANEL ASKED FOR LAST TIME", size=10.5, bold=True, color=ORG)
table(s, [
    ["You said", "What changed"],
    ["Show the AI functioning, not just described",
     "The game now narrates its own reasoning on screen, in English, every turn"],
    ["The game should BE the implementation",
     "The four separate prototypes are merged into one playable build"],
    ["Get to about half the game",
     "The complete core loop runs; the 3D presentation layer is what remains"],
    ["Explain the AI in plain view",
     "An AI view shows its belief on the map and why it moves where it moves"],
], y=2.28, col_w=[4.6, 7.3], size=12.5, head_size=9)
tb(s, 0.72, 4.5, 11.9, 0.9,
   "The problem it solves — horror antagonists are static (learnable, stop being frightening) or random "
   "(unlearnable, feel unfair). Neither adapts to the individual. PARITY builds an online behavioural model "
   "of this player and acts on it.", size=13.5, color=MUT, line=1.3)
box = s.shapes.add_shape(1, In(0.72), In(5.5), In(11.9), In(1.4))
box.fill.solid(); box.fill.fore_color.rgb = C(0xf1,0xf6,0xfc); box.line.color.rgb = ACC
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 5.74, 11.3, 1.05,
   "Everything in this deck is executable.\n"
   "12 experiments and 9 invariant tests run from the command line in minutes; four prototypes run in a "
   "browser with no install. Figures and tables are generated from one metrics file, so nothing here is "
   "typed by hand.", size=14, line=1.35, space=4)

# ---------------------------------------------------------------- first person
s = slide(); header(s, "The game", "First-person, and the AI is in it")
picture(s, "fig_3d.png", 2.05, 1.82, 9.2)
tb(s, 0.72, 6.88, 11.9, 0.5,
   "Eight cells of the facility in a hand-written WebGL build. Record three codebooks, reach the uplink, and "
   "survive a thing that hears the doors you use. Here it has just found the player \u2014 and the panel on the "
   "right shows exactly how.", size=12, color=MUT, line=1.28)

# ---------------------------------------------------------------- the game
s = slide(); header(s, "The same AI, in plain view", "The systems view: belief, sensors, and its reasoning")
picture(s, "fig_game.png", 2.05, 1.82, 9.2)
tb(s, 0.72, 6.88, 11.9, 0.5,
   "Live capture after 22 windows. The AI has ringed room A — 'IT THINKS YOU ARE HERE' — while the player "
   "stands in H. It is confidently wrong, because the player has been using doors with no sensor on them.",
   size=12, color=MUT, line=1.28)

# ---------------------------------------------------------------- AI in plain view
s = slide(); header(s, "The AI in plain view", "It narrates every decision, in English")
tb(s, 0.72, 1.9, 11.9, 0.32, "VERBATIM FROM THE RUNNING BUILD", size=10.5, bold=True, color=ACC)
box = s.shapes.add_shape(1, In(0.72), In(2.26), In(11.9), In(2.5))
box.fill.solid(); box.fill.fore_color.rgb = C(0x16,0x18,0x1a); box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.05, 2.46, 11.3, 2.1,
   "\u203a  A sensor tripped on the door between B and C. You are in B.\n"
   "\u203a  From there I expect you to stay put (51%). Moving to intercept.\n"
   "\u203a  Nothing tripped, but I do not think you stayed. You must have used an unwired\n"
   "    door. Down to 25% sure.\n"
   "\u203a  Only 25% sure \u2014 not enough to commit. Sweeping A, which I have not checked in a while.\n"
   "\u203a  You cannot see the register right now, so I turned over cell 4. I will not be telling you.",
   size=12.5, color=C(0xe8,0xdc,0xc4), font="Consolas", line=1.5, space=2)
table(s, [
    ["On screen", "What it exposes"],
    ["Belief heat on every room", "Where it thinks you are, and how wrong that is"],
    ["Dashed vs solid doors", "Which doors can hear you"],
    ["'Strongest rule learned'", "The habit it has picked up, in counts: 'after A\u2192A you go to A, 10 of 10'"],
    ["Confidence percentage", "Why it commits to an intercept, or sweeps instead"],
], y=5.0, col_w=[3.5, 8.4], size=12, head_size=9)


# ---------------------------------------------------------------- 3 scope
s = slide(); header(s, "Implementation", "How much of the game is built")
table(s, [
    ["System (approved design)", "Responsibility", "Status", "Where it runs"],
    ["Facility", "Room graph, mutation, connectivity invariants", "Complete", "facility.py · 4 tests"],
    ["Predictor", "Variable-order Markov model, online, persists", "Complete", "predictors.py · E1-E3"],
    ["Director", "Scores and selects counter-moves, gated", "Complete", "director.py · E4-E7"],
    ["Sabotage", "Sole mutator of world state, logged", "Complete", "director.py · E5-E6"],
    ["Telemetry", "Routes, dwell, edge traversals", "Complete", "director.py · E10"],
    ["Entity", "Perception, pursuit, interception", "Complete", "director.py · E4"],
    ["Sensors + belief", "Partial observation (NEW this cycle)", "Complete", "sensors.py · E11-E12"],
    ["Notebook", "Freehand editor, strokes, undo, pages", "In game", "parity-game.html"],
    ["Cipher", "Codebooks, register, transmit validation", "In game", "parity-game.html"],
    ["Door clock", "Lockdown / window cycle, the whole rhythm", "In game", "parity-game.html"],
    ["First-person build", "Walkable facility, clock, entity, AI narration", "Playable", "parity-3d.html"],
    ["Godot port", "Engine build, lighting, animation", "Not started", "\u2014"],
    ["Audio, content, progression", "Atmosphere, multiple floors, persistence", "Not started", "\u2014"],
], col_w=[2.3, 4.4, 1.6, 3.6], size=10, head_size=8.5)
tb(s, 0.72, 6.92, 11.9, 0.5,
   "The whole core loop is playable: move on the clock, read codebooks, write pages, stage and send a byte, "
   "evade an AI that models you. What remains is presentation and content, not mechanism — roughly half "
   "the game.", size=11.5, color=MUT, line=1.25)
# ---------------------------------------------------------------- 4 evidence
s = slide(); header(s, "Implementation", "Executable, and attributable")
table(s, [
    ["Artefact", "Scale", "How the panel can verify it"],
    ["Simulation core and model", "1,850 lines of Python, 10 modules", "python3 model/evaluate.py"],
    ["Invariant test suite", "9 properties over 25 generated facilities", "python3 model/test_invariants.py"],
    ["Experiment suite", "12 experiments, all seeded and reproducible", "writes out/metrics.json"],
    ["Browser prototypes", "1,818 lines of JavaScript, 4 apps", "open the .html — no install"],
    ["Version history", "12 commits, single author", "git log"],
], col_w=[3.2, 4.3, 4.4], size=12, head_size=9)
tb(s, 0.72, 4.5, 11.9, 0.35, "THE FOUR PROTOTYPES", size=10.5, bold=True, color=ACC)
bullets(s, [
    ("Model monitor —", "the predictor running live, with its belief and accuracy on screen."),
    ("Vertical slice —", "the game loop: door clock, notebook, register, and the AI tampering with a staged byte."),
    ("Notebook —", "freehand editor with stroke-level erase and pages."),
    ("Room study —", "walkable first-person art direction, hand-written WebGL."),
], y=4.9, size=13, gap=5)

# ---------------------------------------------------------------- 5 architecture
s = slide(); header(s, "Implementation", "Eight modules across three layers")
picture(s, "fig_arch.png", 1.47, 1.9, 10.4)

# ---------------------------------------------------------------- 6 new work
s = slide(); header(s, "New this cycle", "Partial observation — and why it was the right next thing")
box = s.shapes.add_shape(1, In(0.72), In(1.95), In(11.9), In(1.45))
box.fill.solid(); box.fill.fore_color.rgb = C(0xff,0xf6,0xf0); box.line.color.rgb = ORG
box.line.width = Pt(1); box.shadow.inherit = False
tb(s, 1.05, 2.18, 11.3, 1.1,
   "The last review ended on a negative result.\n"
   "An evasive player who declined a third of all windows cut their capture risk by only 1.7%. Waiting was "
   "not a defence — and the diagnosis was the observation model, not the algorithm: an antagonist that "
   "already knows your room is not denied anything when you stand still.", size=13.5, line=1.32, space=4)
bullets(s, [
    ("What was built —", "door motion-detectors, and a Bayes forward filter so the antagonist tracks a "
     "BELIEF over rooms instead of the truth. Coverage is tunable: some doors are unwired, and the player "
     "can spend a dangerous task to silence one."),
    ("Why it matters —", "silence becomes ambiguous between 'they stayed' and 'they used an unwired door'. "
     "That ambiguity is what gives the player something to exploit."),
    ("What it produced —", "two new experiments, one confirming the old negative result and one identifying "
     "the counter-play that actually works."),
], y=3.65, size=14)

# ---------------------------------------------------------------- 7 vomm
s = slide(); header(s, "Technical accuracy", "The predictor: variable-order Markov with back-off")
box = s.shapes.add_shape(1, In(0.72), In(1.95), In(11.9), In(1.35))
box.fill.solid(); box.fill.fore_color.rgb = C(0x16,0x18,0x1a); box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.1, 2.18, 11.2, 1.0,
   "P_o(x | ctx)  =  w · f_o(x | ctx)  +  (1 − w) · P_(o−1)(x | ctx[1:])\n"
   "w  =  C(ctx) / (C(ctx) + α)                    α = 1.6,  k = 4",
   size=15, color=C(0xff,0xff,0xff), font="Consolas", line=1.6, space=4)
bullets(s, [
    ("Why not order-1 —", "a route means the same room has different successors depending on how it was "
     "entered. Order-1 conditions only on the current room and cannot represent that."),
    ("Why not fixed high order —", "10 rooms and order 4 is 10,000 contexts; almost all are never seen."),
    ("Variable order resolves both —", "use the longest context with enough support, back off when there "
     "is not. Witten-Bell interpolation, following Begleiter et al., JAIR 22 (2004)."),
    ("Action space —", "at each window the player takes a door OR declines to move, so the candidate set "
     "is N(v) ∪ {v}. Dwell is predicted, not assumed."),
], y=3.55, size=13.5, gap=9)

# ---------------------------------------------------------------- 8 filter
s = slide(); header(s, "Technical accuracy", "The belief filter over door events")
box = s.shapes.add_shape(1, In(0.72), In(1.95), In(11.9), In(1.35))
box.fill.solid(); box.fill.fore_color.rgb = C(0x16,0x18,0x1a); box.line.fill.background(); box.shadow.inherit = False
tb(s, 1.1, 2.16, 11.2, 1.0,
   "predict    b'(c)  =  Σ_r  b(r) · T(r → c)\n"
   "update     zero any state inconsistent with the evidence, renormalise",
   size=15, color=C(0xff,0xff,0xff), font="Consolas", line=1.6, space=4)
table(s, [
    ["Evidence", "What it rules out", "Effect on the belief"],
    ["Door (a,b) tripped", "Everything except a crossing of that door", "Collapses to near-certainty"],
    ["Silence", "Any crossing of a WIRED door", "Keeps staying put and unwired crossings"],
    ["Co-location", "Everything else", "Collapses to certainty"],
], y=3.5, col_w=[2.9, 5.0, 4.0], size=12.5)
tb(s, 0.72, 5.2, 11.9, 1.3,
   "Two transition priors are compared: a uniform prior that assumes nothing about habits, and one that "
   "learns an order-1 model from the antagonist's own track. A detail worth stating plainly — if EVERY door "
   "is wired, silence proves the player stayed, so full coverage is still perfect tracking. Partial "
   "observation only exists because coverage is incomplete.", size=13, color=MUT, line=1.32)

# ---------------------------------------------------------------- 9 protocol
s = slide(); header(s, "Technical accuracy", "Evaluation protocol and controls")
table(s, [
    ["Guard", "What it prevents", "Result"],
    ["Prequential evaluation", "Train/test leakage — every prediction precedes its outcome", "By construction"],
    ["Random-player control", "A model that appears to predict noise", f"{pc('random|vomm')} vs {pc('random|uniform')} baseline"],
    ["Non-learning baselines", "Complexity that has not earned itself", "Hub-camping, order-1 Markov"],
    ["Per-objective metric", "Strategies that look safe by achieving less", "Captures per completed lap"],
    ["Matched player cost", "Comparing players who pay different prices", "All strategies write pages"],
    ["9 invariant tests", "Soft-locks, leakage, unfair mutation", "9/9 passing"],
], col_w=[2.9, 5.6, 3.4], size=11.5, head_size=9)
tb(s, 0.72, 5.5, 11.9, 1.0,
   "The control is the load-bearing one. Against a random player the model must NOT beat baseline — and it "
   "does not. Two of this cycle's findings came from noticing that a strategy looked good only because it "
   "was measured per window rather than per objective.", size=13, color=MUT, line=1.3)

# ---------------------------------------------------------------- training
s = slide(); header(s, "Technical accuracy", "How well is the model actually trained?")
picture(s, "fig_training.png", 2.4, 1.8, 8.6)
tb(s, 0.72, 6.28, 11.9, 1.05,
   "A predictor is only as good as the ceiling allows. An oracle that can see the player's own internal "
   "state \u2014 which objective they are walking to, whether they are mid-page \u2014 reaches 70.9%; the rest is "
   "their own coin-flips. Our model reaches 59.9% from behaviour alone, which is 85% of the achievable "
   "signal. Grid-searching the hyperparameters changed nothing, and inferring intent explicitly made it "
   "worse.", size=12, color=MUT, line=1.28)


# ---------------------------------------------------------------- 10-15 results
s = slide(); header(s, "Results", "Next-move prediction")
picture(s, "fig_accuracy.png", 2.27, 1.85, 8.8)
tb(s, 0.72, 6.6, 11.9, 0.6,
   f"Read the control first: on a random player VOMM scores {pc('random|vomm')} against a {pc('random|uniform')} "
   "baseline — identical. The gains on structured players are learned habit, not leakage.",
   size=13, color=MUT, line=1.3)

s = slide(); header(s, "Results", "Knowing when you stop to write is still open")
picture(s, "fig_dwell.png", 2.5, 1.82, 8.4)
tb(s, 0.72, 6.35, 11.9, 0.9,
   f"Once the player writes realistically — a codebook copied once, not re-copied every pass — dwell becomes "
   f"rare ({E10['dwell_rate']*100:.0f}% of windows) and accuracy stops meaning anything: 'they always move' scores 96% "
   f"while learning nothing. On recall, the honest measure, the model catches {E10['vomm_recall']*100:.0f}% of the "
   f"moments you stop, at {E10['vomm_precision']*100:.0f}% precision, against a baseline that catches none. Four "
   "attempts to improve it — including a first-visit feature — all made it worse. This is the open problem.",
   size=11.5, color=MUT, line=1.28)

s = slide(); header(s, "Results", "The advantage grows with the facility")
picture(s, "fig_scaling.png", 2.5, 1.85, 8.4)
tb(s, 0.72, 6.15, 11.9, 1.0,
   f"On {SIZES[0]} rooms with one dominant junction, 'camp the busiest room' is competitive for reasons "
   f"unrelated to intelligence. As the facility grows it decays fastest and the interceptor's advantage widens "
   f"from {E7[str(SIZES[0])]['advantage_vs_hub']:.2f}× to {E7[str(SIZES[-1])]['advantage_vs_hub']:.2f}×.",
   size=12.5, color=MUT, line=1.3)

s = slide(); header(s, "Results", "World editing imposes a real cost")
picture(s, "fig_disruption.png", 2.5, 1.9, 8.4)
tb(s, 0.72, 6.15, 11.9, 1.0,
   f"The entity is removed here, isolating topology mutation from hunting. Sealing and rewiring ahead of the "
   f"player raises the cost of an objective by {E5['full-director']['overhead_pct']:.0f}% "
   f"({E5['no-director']['moves_per_lap']:.1f} to {E5['full-director']['moves_per_lap']:.1f} moves per lap). Every "
   "mutation passed a reachability check, so no run was ever soft-locked.", size=12.5, color=MUT, line=1.3)

s = slide(); header(s, "Results — new", "What the sensors actually buy the antagonist")
picture(s, "fig_localisation.png", 2.5, 1.85, 8.4)
tb(s, 0.72, 6.15, 11.9, 1.0,
   "A fully wired facility leaks everything: with a sensor on every door, silence proves the player stayed, "
   "so tracking is essentially perfect. Localisation falls roughly linearly as coverage drops. The learned "
   "transition prior helps only where there is still evidence to sharpen.", size=12.5, color=MUT, line=1.3)

s = slide(); header(s, "Results — new", "What the player can actually do about it")
picture(s, "fig_counterplay.png", 2.4, 1.82, 8.6)
tb(s, 0.72, 6.3, 11.9, 1.0,
   f"Per objective completed, not per window. Waiting at random is catastrophic \u2014 up to "
   f"{chg(COVS[0],'evasive'):+.0f}%. Routing around sensors barely registers. Killing three sensors on your own route "
   f"cuts risk {abs(chg(COVS[1],'disable_3')):.0f}% at {float(COVS[1]):.0%} coverage, but BACKFIRES at full coverage "
   f"({chg(COVS[0],'disable_3'):+.0f}%): nine windows stood still in the open buys too little when every other door "
   "still reports you. The counter-play has a sweet spot.", size=11.5, color=MUT, line=1.28)

# ---------------------------------------------------------------- 16 summary
s = slide(); header(s, "Results", "All twelve experiments at a glance")
table(s, [
    ["#", "Question", "Headline", "Reading"],
    ["E1", "Can it predict the next move?", f"{pc('habitual|vomm')} vs {pc('habitual|markov-1')} vs {pc('habitual|uniform')}", "Learns routes"],
    ["E1c", "Does it learn from a random player?", f"{pc('random|vomm')} vs {pc('random|uniform')}", "No leakage"],
    ["E2", "How fast does it learn?", "Useful inside ~60 moves", "Cold start solved"],
    ["E4", "Does prediction make it deadlier?", f"{E4['vomm']['per_1000']:.0f} vs {E4['random-walk']['per_1000']:.0f} per 1000", "Yes, vs no model"],
    ["E7", "Does that hold at scale?", f"{E7[str(SIZES[0])]['advantage_vs_hub']:.2f}× → {E7[str(SIZES[-1])]['advantage_vs_hub']:.2f}× over hub-camping", "Grows with size"],
    ["E5", "Do world edits cost the player?", f"+{E5['full-director']['overhead_pct']:.0f}% per objective", "Yes"],
    ["E6", "Is sabotage aimed?", "No gain on uniform reliance; 13% on uneven", "Conditional"],
    ["E8", "Does waiting defend? (full obs.)", "1.7% risk cut", "NEGATIVE"],
    ["E9", "Does explicit dwell modelling help?", "2.0% worse than position-only", "NEGATIVE"],
    ["E10", "Can it tell WHEN you stop to write?", f"recall {E10['vomm_recall']*100:.0f}% vs 0% baseline", "OPEN"],
    ["E11", "What do sensors buy? (NEW)", "Full coverage = perfect tracking", "Mechanism"],
    ["E12", "What is the counter-play? (NEW)", f"Disabling sensors: {abs(chg(COVS[1],'disable_3')):.0f}% risk cut", "Design answer"],
], col_w=[0.6, 4.2, 4.5, 2.6], size=10.5, head_size=8.5)

# ---------------------------------------------------------------- 17 interpretation
s = slide(); header(s, "Interpretation", "Three findings changed the design")
bullets(s, [
    ("1 · A negative result set this cycle's work.",
     "Waiting did not defend, and the cause was perfect observation. That diagnosis — not a guess — is why "
     "door sensors were the next milestone. The fix was verified: at 100% coverage the new filter reproduces "
     "the old fully-observed behaviour, which is how we know the re-implementation is sound."),
    ("2 · The metric was hiding the answer, twice.",
     "Measured per window, avoiding sensors looked excellent — measured per objective completed it was worse "
     "than doing nothing, because the player was simply achieving less. And once the player wrote realistically, "
     "dwell became rare enough that accuracy was meaningless: 'they always move' scores 96% and learns nothing."),
    ("3 · The player model was the bottleneck, not the AI.",
     "The bot re-copied codebooks it already held. Fixing that one unrealistic behaviour moved accuracy from "
     "60% to 89%, within three points of the measured ceiling. Against a perfectly consistent player the model "
     "reaches 100%, so the remaining gap is the player's own deviation, not the algorithm."),
], size=13.5, gap=13)

# ---------------------------------------------------------------- 18 limitations
s = slide(); header(s, "Limitations", "Stated before the panel finds them")
table(s, [
    ["Limitation", "Why it stands", "What resolves it"],
    ["No human playtest data", "All evaluation is against scripted players", "M5 playtest; telemetry format exists"],
    ["Writing behaviour is modelled, not observed", "Record-once plus occasional re-verify is a guess at how people write", "Same playtest"],
    ["Predicting WHEN you stop is weak", "17% recall on a rare event; four attempts to improve it failed", "The open problem"],
    ["Models close at interception", "VOMM and order-1 within noise on capture rate", "The clear gap is at prediction, not pursuit"],
    ["First-person build is WebGL, not an engine", "Hand-written; no engine tooling, lighting or animation", "M3, the Godot port"],
], col_w=[3.1, 4.9, 3.9], size=11.5, head_size=9)
tb(s, 0.72, 5.3, 11.9, 1.2,
   "Roadmap — M3 the Godot greybox driven by the room graph; M7 polygonal room tiles where side count is the "
   "difficulty setting; M8 the outbound register with pre-send tampering, already prototyped in the browser "
   "slice. M6 landed this cycle, ahead of M3, because the evidence said it mattered more.",
   size=13, color=MUT, line=1.32)

# ---------------------------------------------------------------- 19 demo
s = slide(); header(s, "Demonstration", "Four things that run right now")
table(s, [
    ["#", "What", "What the panel sees"],
    ["1", "THE GAME — parity-3d.html", "Walk it in first person. Three codebooks, then the uplink, with the thing hunting you and narrating itself top-right"],
    ["2", "Systems view — parity-game.html", "The same AI with its belief drawn on the map, and a sensor you can cut"],
    ["3", "Test suite — test_invariants.py", "9 invariants over 25 generated facilities, in seconds"],
    ["4", "Cut a sensor", "Three windows stood still to kill a door, then watch it lose your trail"],
], col_w=[0.6, 3.6, 7.7], size=11.5, head_size=9)
tb(s, 0.72, 5.0, 11.9, 0.9,
   "Everything runs offline in a browser or from the command line — nothing to install, no network. Turn AI "
   "view OFF to see what the player experiences, then ON to see what the antagonist was actually doing. "
   "That contrast is the demonstration.", size=13, color=MUT, line=1.3)

# ---------------------------------------------------------------- backup
s = slide(); header(s, "Backup", "Learning speed")
picture(s, "fig_learning.png", 2.27, 1.9, 8.8)

s = slide(); header(s, "Backup", "Embodied pursuit")
picture(s, "fig_capture.png", 2.37, 1.88, 8.6)

s = slide(); header(s, "Backup", "Key references")
table(s, [
    ["Work", "Used for"],
    ["Begleiter, El-Yaniv & Yona (2004), JAIR 22:385-421", "Formal basis of the variable-order Markov predictor"],
    ["Romeo et al. (2025), arXiv:2506.19530", "Closest analogue: RL for encounter generation in D&D"],
    ["Lopes et al. (2025), arXiv:2505.01351", "Review naming evaluation as the field's weak point"],
    ["Wu et al. (2025), arXiv:2509.11713", "Next-location prediction over a discrete place graph"],
    ["Deng et al. (2025), arXiv:2508.16620", "Upgrade path from VOMM for trajectory prediction"],
    ["Zhang et al. (2023), arXiv:2312.15582", "Fear in horror games; unfairness destroys it"],
], col_w=[5.6, 6.3], size=12, head_size=9)
tb(s, 0.72, 5.0, 11.9, 0.5, "Full 22-work review in the Review I deck and the project report.",
   size=12.5, color=MUT)

NOTES = {
 1: "BCSE497J Review III. Keep this short and move to evidence.",
 2: "Thirty seconds of context, then say the sentence that matters: everything in this deck is executable "
    "and the panel can run it. Name the new work: partial observation, built because the last review's "
    "negative result pointed at it.",
 3: "Lead with this. Walk two rooms, let a window open and close, and let them read the panel top-right "
    "while you move. It answers 'where is the game' and 'show the AI functioning' in one go.",
 5: "Open the build and leave it running while you talk. Point at the ring on the map and say it out loud: "
    "it is confidently wrong, because the player has been using doors it cannot hear. That single image "
    "answers 'show us the AI functioning'.",
 5: "Read two of these lines aloud verbatim. This is the answer to 'explain the AI in plain view' — it is "
    "not a diagram of the AI, it is the AI talking. Then say the last line is what the player NEVER sees: "
    "the tampering is silent in normal play, and the AI view is how you inspect it.",
 6: "THE implementation slide. Walk the Status column, not the whole table. Eight of ten modules complete "
    "and measured, two running as prototypes, and be straight that the 3D integration has not started. "
    "Say 'roughly 80% of the approved module list' — do not overclaim a finished game.",
 7: "Offer to run something. 'python3 model/test_invariants.py takes about five seconds' is a strong line. "
    "Attribution is the git history: 12 commits, single author.",
 8: "Two decisions to defend: Sabotage is the only mutator so every change is logged and replayable; the "
    "Notebook sits outside the loop, which is what makes it the player's counter-move.",
 9: "This is the progress slide. Lead with the negative result from last time, then what you built because "
    "of it. Panels reward work that follows from evidence rather than from a plan.",
 10: "Explain the order-1 failure concretely: a route means the same room has different successors depending "
    "on how you entered it. Then say staying is a legal action, which is why accuracy is 61% and not 90% — "
    "an earlier version forbade waiting and that number was inflated.",
 11: "The new method. Predict, then rule out whatever the evidence contradicts. The detail that impresses: "
    "if every door is wired, SILENCE is evidence — it proves they stayed — so full coverage is still perfect "
    "tracking. Partial observation only exists because coverage is incomplete.",
 12: "The rigour slide. The control is the strongest thing in the project. Also mention that two findings "
    "this cycle came from catching a bad metric.",
 13: "The answer to 'is it trained properly'. Measure the ceiling, then show where you sit against it. "
     "Say the three things that did NOT work: hyperparameter search, intent tagging, goal inference. All "
     "three were redundant because the variable-order context already encodes them. That is a finding "
     "about the architecture, not a failure.",
 15: "Lead with the control column, not the 61%.",
 15: "Lead with the 100% bar — it never linger where there is nothing to record. The 67% bar is the honest "
     "one: it knows you may be writing, not when you will finish.",
 16: "The answer to 'hub-camping is nearly as good'. Only on a small map.",
 17: "Note the entity is removed here, isolating world editing from hunting.",
 18: "First new result. The counter-intuitive bit is that full coverage gives perfect tracking, because "
     "silence is informative. That is why the fiction needs unwired doors and disabled sensors.",
 19: "The headline. Three things: waiting is worse than useless, avoidance barely helps, and disabling "
     "sensors on your own route is the real counter-play. Point out this is your design mechanic validated "
     "by measurement, not chosen after the fact.",
 20: "Do not read this. It is here so the panel can see the shape of the work and pick something to ask "
     "about. Note the two rows marked NEGATIVE — volunteer them.",
 21: "If you only defend one slide, defend this one. It shows evidence driving decisions, a corrected metric "
     "overturning two apparent wins, and the design being validated rather than rationalised.",
 22: "Say these before they are asked. The 3D build not being started is the obvious one — own it and point "
     "at the roadmap and at why M6 came first.",
 23: "Run item 1 and item 3 if there is time. Item 3 takes seconds and answers any rigour question.",
}
for idx, sl in enumerate(prs.slides, start=1):
    if idx in NOTES:
        sl.notes_slide.notes_text_frame.text = NOTES[idx]

out = ROOT / "docs" / "PARITY-review3-deck.pptx"
prs.save(out)
print("slides:", len(prs.slides._sldIdLst), "->", out)
