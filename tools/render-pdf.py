#!/usr/bin/env python
"""
render-pdf.py — convert any .docx export to a PDF via LibreOffice headless

Usage:
    python tools/render-pdf.py --docx applications/FOLDER/exports/dustin-winkler-resume.docx
    python tools/render-pdf.py --docx PATH.docx --out PATH.pdf

Why this exists: LibreOffice headless produces a print-ready PDF directly from .docx without
a browser or GUI. The -env:UserInstallation flag is required on Windows for headless mode.
Called automatically by generate-resume.py; also callable standalone for cover sheets and
any other .docx export.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOFFICE_DEFAULT = r"C:\Program Files\LibreOffice\program\soffice.exe"


def find_soffice() -> str | None:
    found = shutil.which("soffice") or (SOFFICE_DEFAULT if Path(SOFFICE_DEFAULT).exists() else None)
    return found


def render_pdf(docx_path: Path, out_path: Path | None = None) -> Path:
    """Convert docx_path to PDF. Returns the output path on success, raises on failure."""
    soffice = find_soffice()
    if not soffice:
        raise FileNotFoundError(
            f"LibreOffice not found. Expected: {SOFFICE_DEFAULT}\n"
            "Install: winget install TheDocumentFoundation.LibreOffice"
        )

    out_dir = out_path.parent if out_path else docx_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    default_pdf = out_dir / docx_path.with_suffix(".pdf").name

    # Reuse a STABLE warm profile dir. A fresh per-run profile makes LibreOffice rebuild its
    # entire user profile on every call (~8s of bootstrap — measured), which dwarfs the convert
    # itself. The trade-off a stable profile reintroduces — a resident soffice instance can
    # forward the request and skip the write — is caught by the explicit existence/mtime check
    # below, which raises loudly instead of reporting a phantom success. We capture the docx
    # mtime first so we can prove THIS run actually wrote the PDF.
    docx_mtime = docx_path.stat().st_mtime
    profile_uri = (Path(tempfile.gettempdir()) / "lo-profile").as_uri()
    result = subprocess.run(
        [soffice, "--headless",
         f"-env:UserInstallation={profile_uri}",
         "--convert-to", "pdf",
         "--outdir", str(out_dir),
         str(docx_path)],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr.strip()[:300]}")

    # rc==0 is NOT proof of output. Verify the file exists, is non-empty, and is no older
    # than the source .docx (a stale file means the convert silently no-op'd).
    if not default_pdf.exists() or default_pdf.stat().st_size == 0:
        raise RuntimeError(
            f"PDF not produced despite exit 0 — likely a resident soffice instance forwarded "
            f"the request to a different profile. Close other LibreOffice windows and retry: {default_pdf}")
    if default_pdf.stat().st_mtime + 1 < docx_mtime:
        raise RuntimeError(f"PDF is older than its .docx (stale, not regenerated): {default_pdf}")

    if out_path and out_path != default_pdf:
        default_pdf.replace(out_path)
        return out_path
    return default_pdf


def main():
    ap = argparse.ArgumentParser(description="Convert a .docx export to PDF via LibreOffice headless")
    ap.add_argument("--docx", required=True, help="Path to the .docx file")
    ap.add_argument("--out", help="Output .pdf path (default: alongside the .docx)")
    args = ap.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"ERROR: .docx not found: {docx_path}")
        sys.exit(1)

    out_path = Path(args.out) if args.out else None
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        pdf = render_pdf(docx_path, out_path)
        print(f"[OK] Rendered PDF: {pdf}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
