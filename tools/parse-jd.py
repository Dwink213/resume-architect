#!/usr/bin/env python
"""
parse-jd.py — deterministic JD section parser.

Reads job-posting.md, detects section boundaries, assigns each requirement
line to its section (required / preferred / other), and flags ambiguous
section-boundary lines.

WHY THIS EXISTS: LLMs misread section boundaries when line breaks collapse
during copy-paste. Classic failure: "Bachelor's degree in CS Nice to Have"
where "Nice to Have" is a section header glued onto the previous requirement.
The LLM reads the degree as Required; it was actually Nice to Have. This
parser is deterministic — section detection does not depend on LLM judgment.

INTEGRATION: Call from job-hunt-architect Phase 0, after writing job-posting.md.
Pass the JSON output to Phase 1 as the authoritative section map. The LLM
uses this map, not raw JD text, for all knockout classification.

Usage:
    python tools/parse-jd.py applications/FOLDER/job-posting.md
    python tools/parse-jd.py applications/FOLDER/job-posting.md --json

Exit codes:
    0 = parsed successfully
    1 = file not found or unreadable
    2 = flags found (ambiguous boundaries detected) — still outputs; use for attention
"""

import re
import sys
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Section header patterns — case-insensitive, matched against stripped lines
# ---------------------------------------------------------------------------

REQUIRED_PATTERNS = [
    r"required\s+background",
    r"minimum\s+qualifications?",
    r"must\s+have",
    r"required\s+qualifications?",
    r"basic\s+qualifications?",
    r"^requirements?$",
    r"^required$",
    r"what\s+you\s+(bring|need|must\s+have)",
    r"you\s+(must|will)\s+have",
    r"hard\s+requirements?",
    r"qualifications?\s+required",
]

PREFERRED_PATTERNS = [
    r"nice\s+to\s+have",
    r"preferred\s+qualifications?",
    r"preferred\s+background",
    r"bonus\s+points?",
    r"good\s+to\s+have",
    r"plus(?:es)?$",
    r"ideal\s+candidate",
    r"additional\s+qualifications?",
    r"^preferred$",
]

OTHER_SECTION_PATTERNS = [
    r"what\s+(we|you)\s+(offer|get|do)",
    r"what.s\s+offered",
    r"what\s+we\s+offer",
    r"responsibilities",
    r"about\s+(the\s+)?(role|company|team)",
    r"what\s+makes\s+this\s+role",
    r"the\s+role",
    r"^overview$",
    r"^summary$",
    r"compensation",
    r"benefits",
    r"who\s+we\s+are",
    r"drive\s+ai",
    r"design\s+&?\s+deploy",
    r"mentor.*elevate",
    r"shape\s+responsible",
]

ALL_SECTION_PATTERNS = {
    "required": REQUIRED_PATTERNS,
    "preferred": PREFERRED_PATTERNS,
    "other": OTHER_SECTION_PATTERNS,
}

# Phrases that appear inline to re-classify a single item (e.g. "(required)" appended)
INLINE_REQUIRED = [r"\(required\)", r"\[required\]", r"–\s*required$", r"-\s*required$"]
INLINE_PREFERRED = [r"\(preferred\)", r"\(optional\)", r"\[nice.to.have\]", r"–\s*preferred$"]


def classify_header(line: str):
    """Return ('required'|'preferred'|'other'|None, matched_pattern) for a header line.

    Only classifies a line as a section header if:
    - It starts with '#' (markdown header), OR
    - It is a bare non-bullet line shorter than 60 chars (standalone header phrase)

    This prevents bullet lines that happen to CONTAIN a section-header phrase
    at the end (e.g. 'Bachelor's degree ... Nice to Have') from being
    misclassified as section headers — the key failure mode this parser exists to fix.
    """
    stripped = line.strip()
    is_md_header = stripped.startswith("#")
    is_bare_short = (
        not stripped.startswith("-")
        and not stripped.startswith("*")
        and not stripped.startswith("•")
        and len(stripped) < 70
    )
    if not (is_md_header or is_bare_short):
        return None, None

    clean = stripped.lstrip("#").strip().lower()
    for section_type, patterns in ALL_SECTION_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, clean):
                return section_type, pat
    return None, None


def ends_with_section_header(line: str):
    """
    Detect the key failure mode: a requirement line that ENDS with a section
    header phrase (copy-paste line-break collapse).

    Returns (section_type, matched_phrase) if found, else (None, None).
    """
    clean = line.strip().lower()
    for section_type, patterns in ALL_SECTION_PATTERNS.items():
        for pat in patterns:
            # Check if the pattern appears at the END of the line (last 40 chars)
            tail = clean[-50:] if len(clean) > 50 else clean
            # Don't flag if the entire line IS the header (already caught above)
            if re.search(pat, tail) and len(clean) > len(tail) - 5:
                # Confirm the pattern is in the tail but not at the very start
                if not re.match(r"^\s*" + pat, clean):
                    return section_type, re.search(pat, tail).group(0)
    return None, None


def is_markdown_header(line: str) -> bool:
    return line.strip().startswith("#")


def is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[-*•]\s+", line))


def strip_bullet(line: str) -> str:
    return re.sub(r"^\s*[-*•]\s+", "", line).strip()


def parse(text: str) -> dict:
    lines = text.splitlines()
    sections = []
    flags = []

    current_section = {"header": "Preamble", "type": "other", "items": []}
    sections.append(current_section)

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # --- Detect section header ---
        section_type, matched_pat = classify_header(line)
        if section_type is not None:
            current_section = {
                "header": line.lstrip("#").strip(),
                "type": section_type,
                "items": [],
            }
            sections.append(current_section)
            continue

        # --- Skip non-bullet, non-content lines (pure decorative markdown) ---
        if line.startswith("---") or line.startswith("==="):
            continue

        # --- Process requirement lines ---
        content = strip_bullet(line) if is_bullet(line) else line
        if not content or len(content) < 4:
            continue

        # Check for inline classifiers (overrides section type for this item)
        override_type = None
        for pat in INLINE_REQUIRED:
            if re.search(pat, content, re.IGNORECASE):
                override_type = "required"
                break
        if override_type is None:
            for pat in INLINE_PREFERRED:
                if re.search(pat, content, re.IGNORECASE):
                    override_type = "preferred"
                    break

        # Check for concatenated section header at end of line
        embedded_section, embedded_phrase = ends_with_section_header(content)
        ambiguous = False
        ambiguity_note = None

        # Only flag if the matched phrase is multi-word (avoids single common words
        # like "benefits" or "compensation" that legitimately appear in content lines)
        if embedded_section is not None and embedded_phrase and len(embedded_phrase.split()) < 2:
            embedded_section, embedded_phrase = None, None

        if embedded_section is not None:
            ambiguous = True
            # Strip the embedded header phrase from the content
            cleaned_content = re.sub(
                re.escape(embedded_phrase), "", content, flags=re.IGNORECASE
            ).strip().rstrip("—–-").strip()

            ambiguity_note = (
                f"Line ends with section-header phrase '{embedded_phrase}' "
                f"(type: {embedded_section}). Likely a copy-paste line-break collapse. "
                f"The item text is probably '{cleaned_content}' and '{embedded_phrase.title()}' "
                f"is the NEXT section header, not part of this requirement."
            )
            flags.append({
                "severity": "WARN",
                "raw_line": content,
                "item_text": cleaned_content,
                "embedded_header": embedded_phrase,
                "likely_section_for_item": current_section["type"],
                "likely_next_section": embedded_section,
                "note": ambiguity_note,
                "action": (
                    f"Verify: is '{cleaned_content}' in the "
                    f"'{current_section['header']}' section or the next section?"
                ),
            })

        effective_type = override_type or current_section["type"]

        item = {
            "text": content,
            "section": current_section["header"],
            "section_type": effective_type,
            "ambiguous": ambiguous,
        }
        if ambiguity_note:
            item["ambiguity_note"] = ambiguity_note
        current_section["items"].append(item)

    # Build flat requirement list for easy consumption
    requirements = []
    for sec in sections:
        for item in sec["items"]:
            requirements.append(item)

    return {
        "sections": [
            {
                "header": s["header"],
                "type": s["type"],
                "item_count": len(s["items"]),
            }
            for s in sections
        ],
        "requirements": requirements,
        "flags": flags,
        "flag_count": len(flags),
        "required_count": sum(1 for r in requirements if r["section_type"] == "required" and not r["ambiguous"]),
        "preferred_count": sum(1 for r in requirements if r["section_type"] == "preferred" and not r["ambiguous"]),
        "ambiguous_count": len(flags),
    }


def render_human(result: dict, jd_path: str) -> str:
    lines = [f"# JD Section Parse — {jd_path}", ""]

    lines.append("## Section Map")
    for s in result["sections"]:
        tag = {"required": "[REQUIRED]", "preferred": "[PREFERRED]", "other": "[OTHER]"}.get(
            s["type"], s["type"].upper()
        )
        lines.append(f"  {tag} | {s['header']} ({s['item_count']} items)")
    lines.append("")

    if result["flags"]:
        lines.append(f"## [WARN] Ambiguity Flags ({result['flag_count']})")
        for f in result["flags"]:
            lines.append(f"  [{f['severity']}] {f['raw_line']}")
            lines.append(f"    ->{f['note']}")
            lines.append(f"    ->ACTION: {f['action']}")
        lines.append("")
    else:
        lines.append("## [OK] No Ambiguity Flags")
        lines.append("")

    lines.append("## Requirements by Section Type")
    for section_type, label in [("required", "REQUIRED"), ("preferred", "PREFERRED"), ("other", "OTHER")]:
        items = [r for r in result["requirements"] if r["section_type"] == section_type]
        if items:
            lines.append(f"\n### {label} ({len(items)})")
            for item in items:
                flag = " [AMBIGUOUS]" if item["ambiguous"] else ""
                lines.append(f"  - {item['text']}{flag}")

    lines.append("")
    lines.append(
        f"Summary: {result['required_count']} required · "
        f"{result['preferred_count']} preferred · "
        f"{result['ambiguous_count']} ambiguous"
    )
    return "\n".join(lines)


def main():
    # Force UTF-8 stdout on Windows (cp1252 chokes on em-dashes, curly quotes, etc.)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    use_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]

    if not paths:
        print("ERROR: No job-posting.md path provided.", file=sys.stderr)
        sys.exit(1)

    jd_path = Path(paths[0])
    if not jd_path.exists():
        print(f"ERROR: File not found: {jd_path}", file=sys.stderr)
        sys.exit(1)

    text = jd_path.read_text(encoding="utf-8")
    result = parse(text)

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_human(result, str(jd_path)))

    # Exit 2 if ambiguous flags found — attention signal, not a failure
    sys.exit(2 if result["flag_count"] > 0 else 0)


if __name__ == "__main__":
    main()
