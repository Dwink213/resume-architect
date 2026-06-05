#!/usr/bin/env python
"""
docx-to-html.py — convert a resume .docx to a clean, browser-viewable .html

Why this exists: the workflow outputs an ATS-safe .docx, but a machine without Office can't open
it. This renders the ACTUAL .docx (via mammoth, no Office needed) to styled HTML so the resume can
be reviewed in any browser — and the browser's Print -> Save as PDF gives a text-based PDF if one
is needed. This is the human-review companion to the ATS .docx.

Usage:
    python tools/docx-to-html.py --docx applications/FOLDER/exports/dustin-winkler-resume.docx
    python tools/docx-to-html.py --docx PATH --out PATH.html
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import mammoth
except ImportError:
    print("ERROR: mammoth not installed. Run: python -m pip install mammoth")
    sys.exit(1)

# All-caps strong-only paragraphs are our section headers (the .docx uses direct bold formatting,
# not named styles, so mammoth can't map them — we promote them here).
_HEADER = re.compile(r"<p><strong>([A-Z0-9 ./&|:'\-]+)</strong></p>")

CSS = """
body { font-family: Calibri, 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #1a1a1a;
       max-width: 8.5in; margin: 0.5in auto; line-height: 1.32; padding: 0 0.4in; }
h1 { font-size: 19pt; margin: 0 0 2px 0; letter-spacing: 0.5px; }
h2 { font-size: 11.5pt; text-transform: uppercase; border-bottom: 1px solid #888;
     padding-bottom: 2px; margin: 14px 0 6px 0; }
p  { margin: 3px 0; }
ul { margin: 3px 0 8px 0; padding-left: 20px; }
li { margin: 2px 0; }
.contact { color: #444; font-size: 9.5pt; margin-bottom: 8px; }
@media print { body { margin: 0; } }
"""


def convert(docx_path: Path, out_path: Path) -> Path:
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f)
    body = result.value

    # Promote the name (first all-caps strong line) to <h1>, the rest to <h2> section headers.
    headers = _HEADER.findall(body)
    if headers:
        first = headers[0]
        body = body.replace(f"<p><strong>{first}</strong></p>", f"<h1>{first}</h1>", 1)
    body = _HEADER.sub(r"<h2>\1</h2>", body)

    # Tag the contact line (the paragraph right after the name) for lighter styling.
    body = body.replace("<h1>", "<h1>", 1)  # no-op anchor; contact styling handled by first <p> rule below
    body = re.sub(r"(</h1>\s*)<p>", r"\1<p class='contact'>", body, count=1)

    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Resume preview</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Convert resume .docx to browser-viewable .html")
    ap.add_argument("--docx", required=True, help="Path to the .docx")
    ap.add_argument("--out", help="Output .html (default: alongside the .docx)")
    args = ap.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"ERROR: .docx not found: {docx_path}")
        sys.exit(1)
    out_path = Path(args.out) if args.out else docx_path.with_suffix(".html")

    result = convert(docx_path, out_path)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"[OK] Viewable HTML: {result}")


if __name__ == "__main__":
    main()
