#!/usr/bin/env python
"""
check-cover-sheet.py — hard gate for cover sheet quality.

Fails (exit 2) if the cover sheet:
  - Contains banned internal labels ("Suggested opening line", TBD, etc.)
  - Is missing required fixed sections (songs, articles, upstream issues)

Usage:
    python tools/check-cover-sheet.py --cover applications/FOLDER/cover-sheet.md
    python tools/check-cover-sheet.py --cover <file> --config tools/cover-sheet-lint.yaml

Exit codes: 0 = clean, 2 = violations found, 1 = bad input.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: python -m pip install pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent


def lint(text: str, cfg: dict) -> list:
    violations = []
    low = text.lower()

    for pat in cfg.get("banned", []) or []:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            snippet = text[max(0, m.start() - 30): m.end() + 30].replace("\n", " ")
            violations.append(f"BANNED  /{pat}/  ...{snippet.strip()}...")
            break

    for req in cfg.get("required", []) or []:
        if req.lower() not in low:
            violations.append(f"MISSING (required)  '{req}'")

    return violations


def main():
    ap = argparse.ArgumentParser(description="Hard gate for cover sheet quality")
    ap.add_argument("--cover", required=True, help="Path to cover-sheet.md")
    ap.add_argument("--config", default=str(SCRIPT_DIR / "cover-sheet-lint.yaml"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cp = Path(args.cover)
    if not cp.exists():
        print(f"ERROR: cover sheet not found: {cp}")
        sys.exit(1)

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: lint config not found: {cfg_path}")
        sys.exit(1)

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    violations = lint(cp.read_text(encoding="utf-8"), cfg)
    name = cp.parent.name

    if violations:
        print(f"[FAIL] cover-sheet-lint: {name}")
        for v in violations:
            print(f"   - {v}")
        print(f"cover-sheet-lint: {len(violations)} violation(s). Fix before shipping.")
        sys.exit(2)

    print(f"[OK] cover-sheet-lint: {name} clean")
    sys.exit(0)


if __name__ == "__main__":
    main()
