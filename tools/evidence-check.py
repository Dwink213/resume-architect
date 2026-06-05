#!/usr/bin/env python
"""
evidence-check.py — structural honesty gate for must-include terms.

A phrase may be REQUIRED in a resume only if real evidence backs it. This script
answers, for one or more candidate terms, whether the testimony KB or resume-source
backs the term, and names the backing source. job-hunt-architect calls it when it
auto-generates a per-application must-include list (evidence-gated selection), so a
required phrase can never outrun the evidence (the supply-chain "production"-vs-POC
class of error, structurally prevented).

Usage:
    python tools/evidence-check.py "multi-tenant cloud provider" "production data platform"
    python tools/evidence-check.py --file candidate-terms.txt
    python tools/evidence-check.py --json "zero-trust"
    python tools/evidence-check.py --quiet --file candidates.txt   # print only backed terms

Exit codes: 0 = every given term is backed, 3 = at least one is unbacked, 1 = bad input.
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: python -m pip install pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
TESTIMONIES_DIR = SCRIPT_DIR / "knowledge" / "testimonies"
SOURCE_FILE = SCRIPT_DIR / "resume-source.yaml"


def _flatten(obj):
    """Yield every string scalar from a nested dict/list structure."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _flatten(v)


def load_evidence(testimonies_dir: Path = TESTIMONIES_DIR, source_file: Path = SOURCE_FILE):
    """Return [(source_label, lowercased_text_blob)] over the local evidence corpus:
    every testimony YAML plus resume-source.yaml. The blob includes ats_keywords,
    claims, tags, titles, testimony prose, metrics, and bullet variants."""
    corpus = []
    if testimonies_dir.exists():
        for f in sorted(testimonies_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            corpus.append((f"testimony:{data.get('id', f.stem)}", " ".join(_flatten(data)).lower()))
    if source_file.exists():
        try:
            src = yaml.safe_load(source_file.read_text(encoding="utf-8")) or {}
            corpus.append(("resume-source.yaml", " ".join(_flatten(src)).lower()))
        except yaml.YAMLError:
            pass
    return corpus


def check_term(term: str, corpus) -> list:
    """Return the source labels that back `term` (case-insensitive substring match)."""
    t = term.strip().lower()
    if not t:
        return []
    return [label for label, blob in corpus if t in blob]


def main():
    ap = argparse.ArgumentParser(description="Evidence gate for must-include terms")
    ap.add_argument("terms", nargs="*", help="Candidate terms to check")
    ap.add_argument("--file", help="File with one candidate term per line")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    ap.add_argument("--quiet", action="store_true", help="Print only the backed terms (plain)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    terms = list(args.terms)
    if args.file:
        fp = Path(args.file)
        if not fp.exists():
            print(f"ERROR: term file not found: {fp}")
            sys.exit(1)
        for ln in fp.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                terms.append(ln)
    if not terms:
        print("ERROR: provide one or more terms (positional or --file).")
        sys.exit(1)

    corpus = load_evidence()
    results, all_backed = [], True
    for term in terms:
        sources = check_term(term, corpus)
        backed = bool(sources)
        all_backed = all_backed and backed
        results.append({"term": term, "backed": backed, "sources": sources})

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.quiet:
        for r in results:
            if r["backed"]:
                print(r["term"])
    else:
        for r in results:
            if r["backed"]:
                print(f"BACKED    {r['term']}  <- {', '.join(r['sources'][:3])}")
            else:
                print(f"UNBACKED  {r['term']}  (no testimony/resume-source backs it; cannot be required)")

    sys.exit(0 if all_backed else 3)


if __name__ == "__main__":
    main()
