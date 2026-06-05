#!/usr/bin/env python
"""
generate-resume.py, ATS-optimized resume generator

Usage:
    python tools/generate-resume.py --jd applications/FOLDER/job-posting.md
    python tools/generate-resume.py --jd applications/FOLDER/job-posting.md --role-type fde
    python tools/generate-resume.py --jd applications/FOLDER/job-posting.md --dry-run

Outputs:
    applications/FOLDER/resume.md    (overwrites existing)
    Prints ATS density report to stdout

Role types (auto-detected or override with --role-type):
    fde, agentic_lead, applied_ai_engineer, research_engineer,
    tech_lead_manager, trust_and_safety, govcon
"""

import argparse
import functools
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCE_FILE = SCRIPT_DIR / "resume-source.yaml"
KB_DIR = SCRIPT_DIR / "knowledge"
TESTIMONIES_DIR = KB_DIR / "testimonies"


# ---------------------------------------------------------------------------
# Knowledge base loading
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def load_kb_testimonies() -> list[dict]:
    """Load all testimony YAML files from tools/knowledge/testimonies/.

    Memoized: the KB is immutable within one process run, so repeated callers pay the
    glob+parse exactly once (the cache is process-scoped, so determinism is preserved)."""
    if not TESTIMONIES_DIR.exists():
        return []
    entries = []
    for f in sorted(TESTIMONIES_DIR.glob("*.yaml")):
        try:
            with open(f, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
                if data and "id" in data:
                    entries.append(data)
        except yaml.YAMLError:
            pass
    return entries


def score_kb_testimony(entry: dict, jd_terms: list[str], role_tags: list[str]) -> float:
    """Score a KB testimony entry against JD terms and role tags (two-pass)."""
    tags = set(t.lower().replace("-", "_") for t in entry.get("tags", []))
    jd_set = set(t.lower().replace("-", "_") for t in jd_terms)
    role_set = set(t.lower().replace("-", "_") for t in role_tags)

    # Pass 1: tag overlap
    jd_overlap = len(tags & jd_set)
    role_overlap = len(tags & role_set)
    score = jd_overlap * 2.0 + role_overlap * 1.5

    # Pass 2: testimony full-text match
    testimony_text = (entry.get("testimony", "") or "").lower()
    for term in jd_terms:
        count = testimony_text.count(term.lower())
        if count > 0:
            score += min(count * 0.5, 2.0)

    # Pass 2b: ats_keywords match
    ats_kws = [k.lower() for k in entry.get("ats_keywords", [])]
    for term in jd_terms:
        for kw in ats_kws:
            if term.lower() in kw or kw in term.lower():
                score += 0.5
                break

    return score


def kb_testimony_to_engagement(entry: dict) -> dict:
    """Convert a KB testimony entry to the format expected by build_resume()."""
    featured_prose = (entry.get("bullet_variants") or {}).get("featured", "")
    if not featured_prose:
        featured_prose = entry.get("testimony", "")
    return {
        "id": entry["id"],
        "title": entry.get("title", ""),
        "prose": featured_prose.strip() if isinstance(featured_prose, str) else str(featured_prose).strip(),
        "tags": entry.get("tags", []),
        "includes": entry.get("includes", []),
        "_source": "kb",
    }

# ---------------------------------------------------------------------------
# Role-type detection keywords
# ---------------------------------------------------------------------------
ROLE_TYPE_SIGNALS = {
    "fde": [
        "forward deployed", "fde", "zora", "playbook", "engagement model",
        "customer deployment", "solutions engineering", "quality gates",
    ],
    "tech_lead_manager": [
        "tech lead manager", "tlm", "player-coach", "sandbox", "canvas",
        "tooling", "prototyping", "demos", "high-fidelity", "mcp server",
    ],
    "agentic_lead": [
        "agentic", "orchestration", "multi-agent", "langchain", "langgraph",
        "autogen", "crewai", "agent workflows", "tool use",
    ],
    "applied_ai_engineer": [
        "applied ai", "genai", "rag", "llm application", "inference",
        "fine-tuning", "production ai", "ai platform",
    ],
    "research_engineer": [
        "research engineer", "research scientist", "evals", "evaluation",
        "red-teaming", "safety", "alignment", "reinforcement",
    ],
    "trust_and_safety": [
        "trust and safety", "adversarial", "prompt injection", "guardrails",
        "safety guardrails", "secure orchestration", "monitoring",
    ],
    "govcon": [
        "govcon", "federal", "clearance", "itar", "cmmc", "nist", "fedramp",
        "dod", "government", "classified",
    ],
}


def detect_role_type(jd_text: str) -> str:
    jd_lower = jd_text.lower()
    scores = {}
    for role_type, signals in ROLE_TYPE_SIGNALS.items():
        scores[role_type] = sum(1 for s in signals if s in jd_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "applied_ai_engineer"


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------
AI_TERMS = {
    "agentic", "agent", "llm", "genai", "orchestration", "multi-agent",
    "rag", "fine-tuning", "inference", "prompt", "tool-use", "mcp",
    "sandbox", "evaluation", "evals", "governance", "enforcement",
    "quality gate", "playbook", "fde", "forward deployed", "claude",
    "openai", "azure openai", "langchain", "langgraph", "autogen",
    "crewai", "hookup", "hook", "circuit breaker", "trust tier",
    "admission gate", "knowledge base", "ai platform", "llm-ops",
    "generative ai", "agentic system", "agentic pipeline",
}

INFRA_TERMS = {
    "rubrik", "commvault", "veeam", "avamar", "vmware", "vsphere",
    "nutanix", "kvm", "hyper-v", "backup", "data protection",
    "azure local", "hci", "cluster", "san", "nas", "replication",
}


def extract_jd_keywords(jd_text: str) -> list[tuple[str, int]]:
    """Return (keyword, frequency) pairs from JD, ranked by frequency."""
    # Strip markdown headers/bullets
    text = re.sub(r"^#+\s*", "", jd_text, flags=re.MULTILINE)
    text = re.sub(r"^[-*]\s*", "", text, flags=re.MULTILINE)
    text = text.lower()

    # Extract meaningful n-grams (1-3 words, no stopwords)
    stopwords = {
        "the", "a", "an", "and", "or", "in", "of", "to", "for", "with",
        "on", "at", "by", "as", "is", "are", "be", "that", "this", "we",
        "you", "our", "your", "their", "have", "has", "will", "can", "may",
        "must", "should", "not", "from", "into", "across", "about", "more",
        "such", "each", "both", "its", "who", "which", "how", "what",
        "when", "where", "if", "do", "does", "was", "were", "been", "being",
        "than", "also", "within", "through", "between", "during", "after",
        "before", "including", "including", "including",
    }
    words = re.findall(r"[a-z][a-z\-/+#]{1,}", text)
    words = [w for w in words if w not in stopwords and len(w) > 2]

    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    # Boost multi-word technical phrases found verbatim
    for phrase in [
        "multi-agent", "agent workflows", "quality gates", "forward deployed",
        "tech lead", "player-coach", "agentic system", "llm application",
        "prompt engineering", "tool use", "mcp server", "azure openai",
        "generative ai", "ai platform", "llm ops", "engagement model",
        "playbook", "trust tier", "admission gate", "circuit breaker",
        "rapid prototyping", "high-fidelity", "sandbox", "shadow testing",
    ]:
        if phrase in text:
            key = phrase.replace(" ", "-")
            freq[key] = freq.get(key, 0) + 3  # boost

    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ranked[:60]  # top 60 terms


def score_tags(item_tags: list[str], jd_terms: list[str], role_tags: list[str]) -> float:
    """Score an item's tags against JD terms and role-type tags."""
    jd_set = set(t.lower().replace("-", "_") for t in jd_terms)
    role_set = set(t.lower().replace("-", "_") for t in role_tags)
    item_set = set(t.lower().replace("-", "_") for t in item_tags)
    jd_overlap = len(item_set & jd_set)
    role_overlap = len(item_set & role_set)
    return jd_overlap * 2.0 + role_overlap * 1.5


# ---------------------------------------------------------------------------
# ATS density report
# ---------------------------------------------------------------------------
def ats_density_report(resume_text: str, jd_keywords: list[tuple[str, int]]) -> str:
    text_lower = resume_text.lower()
    ai_hits = sum(1 for t in AI_TERMS if t in text_lower)
    infra_hits = sum(1 for t in INFRA_TERMS if t in text_lower)
    total = ai_hits + infra_hits
    ai_pct = round(ai_hits / total * 100) if total else 0
    infra_pct = 100 - ai_pct if total else 0

    # JD keyword coverage
    top_jd = [kw for kw, _ in jd_keywords[:20]]
    hits = [kw for kw in top_jd if kw.replace("-", " ") in text_lower]
    coverage = round(len(hits) / len(top_jd) * 100) if top_jd else 0

    missing = [kw for kw in top_jd if kw.replace("-", " ") not in text_lower]

    ai_flag = "[OK] AI-dominant" if ai_pct >= 60 else "[WARN] Infra-heavy -- consider collapsing data protection block"
    lines = [
        "",
        "===========================================",
        "ATS DENSITY REPORT",
        "===========================================",
        f"AI vocabulary:    {ai_hits} terms ({ai_pct}%)",
        f"Infra vocabulary: {infra_hits} terms ({infra_pct}%)",
        f"AI/Infra ratio:   {ai_flag}",
        "",
        f"Top-20 JD keyword coverage: {len(hits)}/20 ({coverage}%)",
    ]
    if missing:
        lines.append(f"Missing JD keywords: {', '.join(missing[:10])}")
    lines += [
        "===========================================",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Resume assembly
# ---------------------------------------------------------------------------
# NOTE: featured-engagement selection lives in select_top_engagements() below — it scores the
# static featured_engagements pool and the KB testimonies together and dedups by id. (A former
# select_featured_engagement() helper was dead code with a second uncached KB load; removed.)
def select_top_engagements(source: dict, role_tags: list, jd_terms: list, n: int = 3) -> list:
    """Top N engagements (static + KB), deduped by normalized id, each carrying its includes list."""
    pool = []
    for eng in source.get("featured_engagements", []):
        pool.append((
            score_tags(eng["tags"], jd_terms, role_tags),
            eng.get("id", eng["title"]),
            {"id": eng.get("id"), "title": eng["title"], "prose": eng["prose"],
             "tags": eng["tags"], "includes": eng.get("includes", [])},
        ))
    for entry in load_kb_testimonies():
        if not (entry.get("bullet_variants") or {}).get("featured"):
            continue
        pool.append((score_kb_testimony(entry, jd_terms, role_tags), entry["id"],
                     kb_testimony_to_engagement(entry)))
    best = {}
    for score, _id, eng in pool:
        key = str(_id).replace("-", "_").lower()
        if key not in best or score > best[key][0]:
            best[key] = (score, eng)
    ranked = sorted(best.values(), key=lambda x: x[0], reverse=True)
    return [eng for _score, eng in ranked[:n]]


def select_experience_bullets(
    bullets: list[dict], role_tags: list[str], jd_terms: list[str], max_bullets: int = 4
) -> list[dict]:
    scored = []
    for b in bullets:
        score = score_tags(b["tags"], jd_terms, role_tags)
        scored.append((score, b))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:max_bullets]]


def select_competency_blocks(
    blocks: list[dict], role_tags: list[str], jd_terms: list[str], max_blocks: int = 3
) -> list[dict]:
    scored = []
    for b in blocks:
        score = score_tags(b["tags"], jd_terms, role_tags) + b.get("weight", 0)
        scored.append((score, b))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:max_blocks]]


def generate_summary(role_type: str, jd_text: str, source: dict) -> str:
    """Return the candidate's role-targeted summary from data (source['summaries']).

    Summaries are CONTENT, not engine logic — they live in resume-source.yaml so the
    engine is identity-agnostic. Falls back to applied_ai_engineer, then to any summary,
    then to a minimal generic line if none are defined.
    """
    summaries = source.get("summaries", {}) or {}
    if role_type in summaries:
        return summaries[role_type].strip()
    if "applied_ai_engineer" in summaries:
        return summaries["applied_ai_engineer"].strip()
    if summaries:
        return next(iter(summaries.values())).strip()
    name = source.get("header", {}).get("name", "This candidate")
    return f"{name} — see selected projects and experience below."


def _render_experience_entry(entry: dict, role_tags: list, jd_terms: list) -> list:
    """Render one experience/founder entry. Supports bullets-format and prose-format."""
    out = []
    header = f"**{entry['company']}**" if "company" in entry else f"**{entry['name']}**"
    loc = entry.get("location", "")
    dates = entry.get("dates", "")
    meta = " | ".join(x for x in [header, loc, dates] if x)
    out.append(meta)
    if entry.get("title"):
        out.append(f"*{entry['title']}*")
    if entry.get("role"):
        out.append(f"*{entry['role']}*")
    out.append("")
    if entry.get("format") == "prose" or ("text" in entry and "bullets" not in entry):
        out.append((entry.get("text") or "").strip())
    else:
        selected = select_experience_bullets(entry.get("bullets", []), role_tags, jd_terms, max_bullets=4)
        for b in selected:
            out.append(f"- {b['text']}")
    out.append("")
    return out


def build_resume(
    source: dict,
    jd_text: str,
    role_type: str,
    jd_application_folder: Path,
    dry_run: bool = False,
) -> str:
    role_tags = source.get("role_type_tags", {}).get(role_type, [])
    jd_keywords = extract_jd_keywords(jd_text)
    jd_terms = [kw for kw, _ in jd_keywords]

    # Select components
    featured_list = select_top_engagements(source, role_tags, jd_terms, n=2)
    projects_lines = []
    for eng in featured_list:
        projects_lines.append(f"## SELECTED PROJECT · {eng['title']}")
        projects_lines.append("")
        projects_lines.append(eng["prose"].strip())
        for inc in eng.get("includes", []):
            projects_lines.append(f"- {inc}")
        projects_lines += ["", "---", ""]
    role_title_hint = jd_application_folder.name.split("_")[-1].replace("-", " ")

    # Tagline selection
    header = source["header"]
    tagline = header.get("tagline_ai") if role_type != "govcon" else header.get("tagline_govcon")
    if role_type == "fde":
        tagline = header.get("tagline_default")

    # Competency blocks
    comp_blocks = select_competency_blocks(source["competency_blocks"], role_tags, jd_terms, max_blocks=3)

    # Open source
    prs = source.get("open_source", [])

    # Certifications + Education (Education is a HARD parse/knockout signal, always render)
    certs = " · ".join(source["certifications"])
    education = source.get("education", [])

    # Summary
    summary = generate_summary(role_type, jd_text, source)

    # --- Assemble ---
    cand_name = header.get("name", "Candidate")
    lines = [
        f"# {cand_name}, {role_title_hint}",
        f"*Tailored for {jd_application_folder.name} | Role type: {role_type} | Generated by generate-resume.py*",
        "",
        "---",
        "",
        f"**{cand_name.upper()}**",
        f"*{tagline} · {header['contact']}*",
        "",
        f"Curious about more? [{header['claude_link']}]({header['claude_link']})",
        "",
        "---",
        "",
        "## SUMMARY",
        "",
        summary,
        "",
        "---",
        "",
        *projects_lines,
    ]

    # --- EXPERIENCE (generic; founder_work first as current role) ---
    # Founder work is folded into EXPERIENCE under the standard header so Workday/ATS
    # counts the years and reads the current founder role as the *current* role.
    lines += ["## EXPERIENCE", ""]
    for f in source.get("founder_work", []):
        gate = f.get("role_gate")           # optional: only render for these role_types
        if gate and role_type not in gate and not any(g in role_tags for g in gate):
            continue
        # founder entries may carry bullets (list of strings) or prose text
        if f.get("bullets") and all(isinstance(b, str) for b in f["bullets"]):
            lines += [f"**{f['name']}** | {f.get('location','')} | {f.get('dates','')}",
                      f"*{f.get('role','')}*", ""]
            lines += [f"- {b}" for b in f["bullets"]]
            lines += [""]
        else:
            lines += _render_experience_entry(f, role_tags, jd_terms)
    for e in source.get("experience", []):
        lines += _render_experience_entry(e, role_tags, jd_terms)

    # --- UPSTREAM (data-driven; omitted when no open_source) ---
    if prs:
        up_title = "UPSTREAM"
        up_intro = "Open-source contributions:"
        # profile may override the section title/intro (see profile.yaml 'upstream')
        prof_upstream = (source.get("_profile") or {}).get("upstream")
        if isinstance(prof_upstream, dict):
            up_title = prof_upstream.get("section_title", up_title)
            up_intro = prof_upstream.get("intro", up_intro)
        lines += ["", "---", "", f"## {up_title}", "", up_intro, ""]
        for pr in prs:
            lines.append(f"- **{pr['pr']}** {pr['text']}")

    lines += [
        "",
        "---",
        "",
        "## TECHNICAL COMPETENCIES",
        "",
    ]
    for block in comp_blocks:
        lines.append(f"**{block['label']}:** {block['terms']}")
    if education:
        lines += [
            "",
            "---",
            "",
            "## EDUCATION",
            "",
        ]
        for ed in education:
            lines.append(f"- {ed}")
    lines += [
        "",
        "---",
        "",
        "## CERTIFICATIONS",
        "",
        certs,
    ]

    resume_text = "\n".join(lines)

    # ATS report
    report = ats_density_report(resume_text, jd_keywords)

    return resume_text, report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate ATS-optimized resume from JD")
    parser.add_argument("--jd", required=False, help="Path to job-posting.md")
    parser.add_argument("--role-type", help="Override role type detection")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout, don't write file")
    parser.add_argument("--no-pdf", action="store_true",
                        help="Skip the LibreOffice PDF step for fast iteration (docx+html+lint only)")
    parser.add_argument("--force-locked", action="store_true",
                        help="Override the submitted-folder lockout (only to deliberately replace a submission)")
    parser.add_argument("--source", default=str(SOURCE_FILE), help="Path to resume-source.yaml")
    parser.add_argument("--search-kb", metavar="QUERY",
                        help="Search knowledge base testimonies and exit (no resume generated)")
    args = parser.parse_args()

    # KB search mode, no JD required
    if args.search_kb:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        from pathlib import Path as _Path
        entries = load_kb_testimonies()
        if not entries:
            print(f"No testimony files found in {TESTIMONIES_DIR}")
            sys.exit(1)
        query_terms = args.search_kb.lower().split()
        role_tags = []
        if args.role_type:
            source_path = Path(args.source)
            if source_path.exists():
                src = yaml.safe_load(source_path.read_text(encoding="utf-8"))
                role_tags = src.get("role_type_tags", {}).get(args.role_type, [])

        scored = []
        for entry in entries:
            score = score_kb_testimony(entry, query_terms, role_tags)
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        print(f"\nKB search: '{args.search_kb}', top {min(5, len(scored))} results\n")
        for s, entry in scored[:5]:
            print(f"  [{s:.1f}] {entry['id']}: {entry.get('title', '')}")
            long_bullet = (entry.get("bullet_variants") or {}).get("long", "")
            if long_bullet:
                txt = long_bullet.strip() if isinstance(long_bullet, str) else str(long_bullet).strip()
                print(f"       {txt[:200]}")
            print()
        return

    if not args.jd:
        parser.error("--jd is required unless using --search-kb")

    jd_path = Path(args.jd)
    if not jd_path.exists():
        print(f"ERROR: JD file not found: {jd_path}")
        sys.exit(1)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)

    jd_text = jd_path.read_text(encoding="utf-8")
    source = yaml.safe_load(source_path.read_text(encoding="utf-8"))

    # Attach identity profile so build_resume can read profile-driven sections (UPSTREAM title, etc.)
    import importlib.util as _il
    _spec = _il.spec_from_file_location("profile_loader", SCRIPT_DIR / "profile_loader.py")
    _pl = _il.module_from_spec(_spec); _spec.loader.exec_module(_pl)
    try:
        source["_profile"] = _pl.load_profile()
    except FileNotFoundError:
        source["_profile"] = {}   # engine still runs with resume-source.yaml alone

    role_type = args.role_type or detect_role_type(jd_text)
    print(f"Role type: {role_type} {'(auto-detected)' if not args.role_type else '(override)'}")

    jd_folder = jd_path.parent
    resume_text, ats_report = build_resume(source, jd_text, role_type, jd_folder, args.dry_run)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(ats_report)

    if args.dry_run:
        print(resume_text)
    else:
        if (jd_folder / "SUBMITTED.md").exists() and not args.force_locked:
            print(f"[ABORT] {jd_folder.name} is LOCKED (SUBMITTED.md present) — refusing to overwrite a")
            print(f"        submitted application. Its as-submitted record is the applied/* lock tag.")
            print(f"        Use --force-locked only if you intend to replace this submission.")
            sys.exit(3)
        out_path = jd_folder / "resume.md"
        out_path.write_text(resume_text, encoding="utf-8")
        print(f"[OK] Written: {out_path}")
        print(f"   Role type: {role_type}")

        # ----- In-process rendering -----
        # render/convert/pdf/lint/sign all expose importable functions. We import them ONCE
        # (hyphenated filenames -> importlib) and call them directly, instead of spawning a
        # fresh Python interpreter per step. This collapses ~5 process cold-starts into one,
        # eliminating the bulk of the per-resume wall-clock (the assembly above is ~0.25s).
        import importlib.util

        def _load(mod_name: str, file_name: str):
            spec = importlib.util.spec_from_file_location(mod_name, SCRIPT_DIR / file_name)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

        exports_dir = jd_folder / "exports"
        slug = _pl._name_slug(source.get("_profile"))
        docx_out = exports_dir / f"{slug}-resume.docx"
        html_out = docx_out.with_suffix(".html")
        rendered = []
        try:
            render_docx = _load("render_docx", "render-docx.py")
            render_docx.render(out_path, docx_out)          # render() does NOT auto-sign; we sign once below
            rendered.append("docx")
            print(f"[OK] Rendered ATS-safe .docx: {docx_out}")
            docx_to_html = _load("docx_to_html", "docx-to-html.py")
            docx_to_html.convert(docx_out, html_out)
            rendered.append("html")
            print(f"[OK] Rendered viewable .html: {html_out}")
        except ModuleNotFoundError as e:
            print(f"[skip] render dependency missing ({e}); resume.md is still written. "
                  f"Fix: python -m pip install python-docx mammoth")
        except Exception as e:
            print(f"[ERROR] render failed (resume.md is still written): {e}")

        # PDF is the slow step (LibreOffice cold start ~2s). Default ON for the full four-file
        # contract; --no-pdf skips it for fast inner-loop iteration (re-run before submit).
        if "docx" in rendered and not args.no_pdf:
            try:
                render_pdf = _load("render_pdf", "render-pdf.py")
                pdf_out = render_pdf.render_pdf(docx_out)    # verifies the .pdf actually exists
                rendered.append("pdf")
                print(f"[OK] Rendered PDF:           {pdf_out}")
            except Exception as e:
                print(f"[WARN] PDF step failed (.docx/.html still written): {e}")
        elif args.no_pdf and "docx" in rendered:
            stale = docx_out.with_suffix(".pdf")            # drop a now-stale PDF so exports never lie
            if stale.exists():
                stale.unlink()
            print("[skip] PDF deferred (--no-pdf) — re-run with PDF before submitting.")

        # Sign LAST, after every artifact exists, so checksums.sha256 covers the full set
        # (the old flow signed mid-pipeline when only the .docx existed). Governance still runs.
        if rendered:
            try:
                sign_exports = _load("sign_exports", "sign-exports.py")
                sign_exports.sign(jd_folder)
                print(f"[OK] Signed exports/ ({', '.join(rendered)})")
            except Exception as e:
                print(f"[skip] signing unavailable ({e})")

        # ----- Content quality gate (loud: a violation is a [FAIL], never a quiet [skip]) -----
        try:
            check_resume = _load("check_resume", "check-resume.py")
            lint_cfg = yaml.safe_load((SCRIPT_DIR / "resume-lint.yaml").read_text(encoding="utf-8")) or {}
            lint_cfg = check_resume.merge_overrides(lint_cfg, source.get("_profile", {}))
            extra_required = check_resume.load_must_include(jd_folder)
            violations = check_resume.lint(out_path.read_text(encoding="utf-8"), lint_cfg, extra_required)
            if violations:
                print(f"[FAIL] resume-lint: {len(violations)} violation(s) — fix before submitting:")
                for v in violations:
                    print(f"   - {v}")
            else:
                print(f"[OK] resume-lint: {jd_folder.name} clean")
        except Exception as e:
            print(f"[skip] resume-lint unavailable ({e})")

        pdf_hint = "" if "pdf" in rendered else "  (re-run with PDF before submit)"
        print(f"   Next: review exports/ (.docx upload / .html backup){pdf_hint}, run /filter-forecaster, submit")


if __name__ == "__main__":
    main()
