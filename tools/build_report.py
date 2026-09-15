"""docs/PARITY-project-report.md -> docs/PARITY-project-report.pdf

Markdown -> styled HTML -> Chrome headless print-to-PDF. Figure paths in the
markdown are relative to docs/, so the intermediate HTML is written there too.
"""
import re, shutil, subprocess, sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "PARITY-project-report.md"
OUT = ROOT / "docs" / "PARITY-project-report.pdf"
TMP = ROOT / "docs" / ".report.html"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font: 10.5pt/1.55 "Source Serif 4", Georgia, serif; color: #16130f;
       max-width: 100%; margin: 0; }
h1 { font-size: 22pt; margin: 0 0 .1em; letter-spacing: -.01em; }
h2 { font-size: 14pt; margin: 1.7em 0 .5em; padding-top: .3em;
     border-top: 1px solid #ddd6cc; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 1.2em 0 .35em; page-break-after: avoid; }
h1 + h2 { border-top: 0; margin-top: .2em; font-weight: 400; color: #55503f; }
p, li { orphans: 2; widows: 2; }
code { font: 9pt/1.4 "JetBrains Mono", ui-monospace, monospace;
       background: #f2efe9; padding: .1em .3em; border-radius: 3px; }
pre { background: #f2efe9; padding: .7em .9em; border-radius: 5px;
      border-left: 3px solid #2a78d6; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #ddd6cc; padding: .38em .6em; text-align: left; }
th { background: #f2efe9; font-weight: 600; }
img { max-width: 100%; display: block; margin: 1em auto .3em;
      page-break-inside: avoid; }
blockquote { border-left: 3px solid #eb6834; margin: 1em 0; padding: .1em 0 .1em 1em;
             color: #55503f; }
hr { border: 0; border-top: 1px solid #ddd6cc; margin: 1.6em 0; }
a { color: #2a78d6; text-decoration: none; }
"""


def chrome() -> str:
    for name in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return name
    sys.exit("no chrome/chromium on PATH")


def main() -> None:
    body = markdown.markdown(
        SRC.read_text(),
        extensions=["tables", "fenced_code", "attr_list", "sane_lists"],
    )
    # markdown wraps lone images in <p>; let them be blocks so page-break rules apply
    body = re.sub(r"<p>(<img [^>]+>)</p>", r"\1", body)
    TMP.write_text(
        f"<!doctype html><meta charset=utf-8><title>PARITY — Review III report</title>"
        f"<style>{CSS}</style>{body}"
    )
    subprocess.run(
        [chrome(), "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", f"--print-to-pdf={OUT}",
         "--virtual-time-budget=10000", TMP.as_uri()],
        check=True, capture_output=True,
    )
    TMP.unlink()
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
