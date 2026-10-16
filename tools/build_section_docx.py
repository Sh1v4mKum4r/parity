"""Regenerate the Word drop-in for section 7.8 of the Word report.

    python3 tools/build_section_docx.py [outfile.docx] [--teammate]

--teammate emits the co-author's framing: the experiment credited to the
teammate who owns the model and evaluation, and the closing paragraph written
as self-assessment of the facility generator rather than as an outside view.

The 86-page report is maintained in Word and only its PDF export is on disk, so
this emits the one new section as a standalone .docx matching that document's
conventions (Times New Roman 12, 1.5 spacing, justified with a first-line indent,
table captions above and figure captions below). Numbers are read from
out/metrics.json, so re-running evaluate.py and then this keeps the prose, the
table and the figure in agreement.
"""
import json, sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "out" / "metrics.json").read_text())["e13_across_sessions"]
sk, sw = M["same-facility/remembers"], M["same-facility/control-wiped"]
nk, nw = M["new-facility/remembers"], M["new-facility/control-wiped"]
MATE = "--teammate" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(args[0]) if args else ROOT / "docs" / "PARITY-section-7.8-across-sessions.docx"

doc = Document()
s = doc.styles["Normal"]
s.font.name = "Times New Roman"; s.font.size = Pt(12)
s.paragraph_format.space_after = Pt(0); s.paragraph_format.line_spacing = 1.5

def head(num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18); p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"{num}\t{text.upper()}"); r.bold = True
    r.font.name = "Times New Roman"; r.font.size = Pt(12)

def body(text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Inches(0.4)
    p.paragraph_format.space_after = Pt(6)

def caption(text, before=6, after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text); r.font.name = "Times New Roman"; r.font.size = Pt(11)

head("7.8", "Does the antagonist improve across sessions?")
body("Section 7.3 notes that the antagonist's memory of its last prediction is cleared on "
     "re-entry, because that prediction was about a building that no longer exists. That "
     "observation is correct, and it raises a question the baseline never answered. The game "
     "tells the player on every death screen that their pages survive and so does its model "
     "of them. Nothing in the project had tested whether retaining that model makes the "
     "antagonist measurably better at catching the same player.")
body(("Experiment E13, added to the baseline evaluation suite by my teammate, measures it "
      "directly. " if MATE else "Experiment E13 measures it directly. ") +
     "One scripted player is run through twelve "
     "consecutive sessions. Everything is reset between sessions except the predictor, which "
     "keeps the counts it has accumulated. Each condition is paired with a control in which "
     "the predictor is wiped between sessions. The control is necessary rather than "
     "decorative: a trend on its own would prove nothing, because a scripted player settling "
     "into a stable route would produce the same curve without any learning at all. With the "
     "control in place, retained learning is the only difference between the two lines.")
body("Two worlds are measured, because the answer differs between them and the difference is "
     "the substantive finding. In the first the player returns to the same facility each "
     "session. In the second the facility is regenerated between sessions, which is what the "
     "build described in Chapter 6 actually does.")

caption("Table 7.3: Captures per 1000 moves across twelve consecutive sessions "
        "(mean of 12 seeds, 400 moves per session)", before=12)
rows = [("Condition", "First 3 sessions", "Last 3 sessions", "Change"),
        ("Same facility, model retained", f"{sk['first_3']:.0f}", f"{sk['last_3']:.0f}", f"{sk['change_pct']:+.1f}%"),
        ("Same facility, model wiped (control)", f"{sw['first_3']:.0f}", f"{sw['last_3']:.0f}", f"{sw['change_pct']:+.1f}%"),
        ("Regenerated facility, model retained", f"{nk['first_3']:.0f}", f"{nk['last_3']:.0f}", f"{nk['change_pct']:+.1f}%"),
        ("Regenerated facility, model wiped (control)", f"{nw['first_3']:.0f}", f"{nw['last_3']:.0f}", f"{nw['change_pct']:+.1f}%")]
tbl = doc.add_table(rows=len(rows), cols=4); tbl.style = "Table Grid"
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        c = tbl.cell(i, j); c.text = ""
        p = c.paragraphs[0]; p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
        if j: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(11)
        if i == 0 or (j == 3 and i in (1, 3)): r.bold = True
doc.add_paragraph()

body(f"The antagonist does improve, but only when the building stays put. Returning to the "
     f"same facility, captures rise {sk['change_pct']:+.1f} per cent from the first three sessions to the last "
     f"three, while the control stays flat within noise at {sw['change_pct']:+.1f} per cent. The predictor is "
     f"accumulating a usable model of this particular player across runs, and the player is "
     f"measurably worse off on their twelfth visit than on their first.")
body(f"Carrying that model into a regenerated facility is worse than forgetting it. Captures "
     f"fall {abs(nk['change_pct']):.1f} per cent against a control that is flat at {nw['change_pct']:+.1f} per cent. The cause is "
     f"structural rather than statistical. The predictor is keyed on room indices, and "
     f"regeneration changes what an index refers to, so its contexts are not so much wrong as "
     f"about a building that no longer exists. It spends the better part of a session "
     f"unlearning them.")

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(12)
p.add_run().add_picture(str(ROOT / "out" / "fig_sessions.png"), width=Inches(6.0))
caption("Figure 7.3: Captures per 1000 moves across consecutive sessions. The grey line is the "
        "control, which forgets between sessions. Retained learning helps in a fixed building "
        "and hurts in a regenerated one.", after=12)

body(("This is a finding about my own extension as much as about the model, and it cuts "
      "against the extension described in Section 6.3. " if MATE else
      "This is a finding about the design as much as about the model, and it cuts against "
      "the build described in Chapter 6. ") +
     "A new facility on every run was introduced so that the "
     "layout could not be memorised by the player, which it achieves. The measurement here "
     "shows that it also places the antagonist in the one condition where its retained model "
     "is a liability, so the sentence the game delivers at its most dramatic moment is, as "
     "shipped, not true. Two routes close the gap. The facility can be held fixed across a run "
     "of sessions, so that the retained model refers to a building that still exists; or the "
     "predictor can be re-keyed on features that do not depend on the layout, such as door "
     "degree, distance to the current objective and turn direction, so that what it learns "
     "about a player transfers between buildings. The second is the more interesting question "
     "and is recorded in Section 8.2 as future work.")

OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(f"{OUT}  ({OUT.stat().st_size // 1024} KB)")
