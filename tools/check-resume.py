#!/usr/bin/env python
"""
check-resume.py — content quality gate for a generated resume.

Governance by code, not by promises. Fails (exit 2) if the resume contains a banned
AI-tell word, an accidental duplicate, or is missing a required must-have. The rules
live in tools/resume-lint.yaml (global) and applications/FOLDER/must-include.txt
(per-application), so the definition of "good content" is data, not buried in code.

Usage:
    python tools/check-resume.py --resume applications/FOLDER/resume.md
    python tools/check-resume.py --resume <file> --config tools/resume-lint.yaml

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


def lint(text: str, cfg: dict, extra_required: list) -> list:
    violations = []
    low = text.lower()

    for pat in cfg.get("banned", []) or []:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            snippet = text[max(0, m.start() - 25): m.end() + 25].replace("\n", " ")
            violations.append(f"BANNED  /{pat}/  ...{snippet.strip()}...")
            break  # one report per pattern is enough

    for phrase, mx in (cfg.get("max_occurrences") or {}).items():
        c = low.count(str(phrase).lower())
        if c > mx:
            violations.append(f"DUPLICATE  '{phrase}' appears {c}x (max {mx})")

    for req in (cfg.get("required", []) or []):
        if req.lower() not in low:
            violations.append(f"MISSING (global required)  '{req}'")

    for req in extra_required:
        if req.lower() not in low:
            violations.append(f"MISSING (must-include)  '{req}'")

    return violations


def _parse_list(path: Path) -> list:
    """One phrase per line; blank lines and # comments ignored; inline ' #...' stripped."""
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        ln = re.split(r"\s+#", ln, maxsplit=1)[0].strip()
        if ln:
            out.append(ln)
    return out


def load_must_include(folder: Path) -> list:
    """Effective per-app required phrases = (auto union pins.add) minus pins.remove.

    - must-include.auto.txt : machine-owned, regenerated each ingestion by job-hunt-architect.
    - must-include.pins.txt : human-owned; '+phrase' force-adds, '-phrase' suppresses.
    Backward compatible: a legacy must-include.txt (with no .auto/.pins) is read as auto.
    """
    auto_f = folder / "must-include.auto.txt"
    pins_f = folder / "must-include.pins.txt"
    legacy_f = folder / "must-include.txt"

    if auto_f.exists():
        auto = _parse_list(auto_f)
    elif not pins_f.exists() and legacy_f.exists():
        auto = _parse_list(legacy_f)
    else:
        auto = []

    adds, removes = [], []
    if pins_f.exists():
        for ln in pins_f.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            ln = re.split(r"\s+#", ln, maxsplit=1)[0].strip()
            if ln.startswith("+"):
                adds.append(ln[1:].strip())
            elif ln.startswith("-"):
                removes.append(ln[1:].strip())
            # a bare line with no +/- directive is ignored

    rem_low = {r.lower() for r in removes if r}
    effective, seen = [], set()
    for term in auto + adds:
        low = term.lower()
        if not term or low in rem_low or low in seen:
            continue
        seen.add(low)
        effective.append(term)
    return effective


def main():
    ap = argparse.ArgumentParser(description="Content quality gate for a generated resume")
    ap.add_argument("--resume", required=True, help="Path to a generated resume.md")
    ap.add_argument("--config", default=str(SCRIPT_DIR / "resume-lint.yaml"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    rp = Path(args.resume)
    if not rp.exists():
        print(f"ERROR: resume not found: {rp}")
        sys.exit(1)

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}

    extra_required = load_must_include(rp.parent)

    violations = lint(rp.read_text(encoding="utf-8"), cfg, extra_required)
    name = rp.parent.name

    if violations:
        print(f"[FAIL] resume-lint: {name}")
        for v in violations:
            print(f"   - {v}")
        print(f"resume-lint: {len(violations)} violation(s). Fix before shipping.")
        sys.exit(2)

    print(f"[OK] resume-lint: {name} clean")
    sys.exit(0)


if __name__ == "__main__":
    main()
