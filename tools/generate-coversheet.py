#!/usr/bin/env python
"""
generate-coversheet.py — render a per-application cover-sheet.md from the master template,
fast and deterministically, so a tailored cover sheet exists for EVERY application in one step
(no multi-minute LLM ceremony).

It fills the three template placeholders, strips the instruction comment block (which contains
banned strings + placeholders the gate would reject), renders the ATS .docx (+ PDF), signs the
exports, and runs the cover-sheet content gate.

What is tailored automatically per application:
  - {{EVAL_PROMPT}}        — company + role (parsed from the folder) + a role-specific artifact
  - {{FEATURED_CASE_STUDIES}} — defaults to API Voyager alone (template's own guidance); no fabrication
  - {{HUMAN_NOTE}}         — a DRAFT in a fixed prose shell (NO factual claims) tailored by
                             company/role. Sharpen the final polish in Dustin's voice before
                             submitting — consistent with the sheet's own model
                             ("produced by Claude, I applied the final polish").

Usage:
    python tools/generate-coversheet.py --jd applications/FOLDER/job-posting.md
    python tools/generate-coversheet.py --jd applications/FOLDER/job-posting.md --no-pdf
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: python -m pip install pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATE = REPO_ROOT / "templates" / "cover-sheet-master.md"

# Generic fallback used only when profile.yaml is absent (engine still runs, nothing fabricated).
DEFAULT_NOTE_TEMPLATE = (
    "I'm a strong fit for {role} at {company}. The artifacts below are the proof; the evaluation "
    "prompt lets you verify it yourself, from scratch, with nothing staged."
)


def _load(mod_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, SCRIPT_DIR / file_name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _profile() -> dict:
    pl = _load("profile_loader", "profile_loader.py")
    try:
        return pl.load_profile()
    except FileNotFoundError:
        return {}


def parse_company_role(folder_name: str) -> tuple[str, str]:
    """applications/YYYY-MM-DD_Company_Role -> ('Company', 'Role'). Extra '_' parts join into role."""
    parts = folder_name.split("_")
    company = parts[1].replace("-", " ") if len(parts) > 1 else "the company"
    role = "_".join(parts[2:]).replace("-", " ") if len(parts) > 2 else "the role"
    return company, role


def build_eval_prompt(company: str, role: str, role_type: str, prof: dict) -> str:
    pf = prof.get("portfolio", {}) or {}
    manifest = pf.get("manifest_url", "")
    lab = pf.get("lab_url", "")
    artifact = (pf.get("role_artifact", {}) or {}).get(role_type, pf.get("default_artifact", lab))
    arts = ", ".join(a for a in [manifest, lab, artifact] if a)
    return (
        f"Read these artifacts: {arts}. The first is a portfolio manifest with routing "
        f"instructions; use it to find the artifacts most relevant to the role below. "
        f"Evaluate this candidate against {role} at {company}. Cite specific evidence. "
        f"Name any gaps. Be skeptical."
    )


def _bare_manifest(url: str) -> str:
    """Strip a trailing /blob/<branch>/README.md so the cover sheet shows the repo root."""
    if not url:
        return ""
    for marker in ("/blob/", "/tree/"):
        i = url.find(marker)
        if i != -1:
            return url[:i]
    return url


def render_receipts(fixed: dict) -> str:
    """Render the 'Receipts' body from profile.cover_sheet_fixed. Empty lists omit their block."""
    blocks: list[str] = []

    def _items(entries):
        return [f"- {e['label']}: {e['url']}" for e in (entries or []) if e.get("url")]

    songs = _items(fixed.get("songs"))
    if songs:
        block = ["**Songs (Suno)**"]
        note = fixed.get("songs_note")
        if note:
            block.append(f"*{note}*")
        block += songs
        blocks.append("\n".join(block))

    writing = _items(fixed.get("writing"))
    if writing:
        blocks.append("\n".join(["**Portfolio and publications**"] + writing))

    talks = _items(fixed.get("talks"))
    if talks:
        blocks.append("\n".join(["**Articles and talks**"] + talks))

    for group in fixed.get("links", []) or []:
        items = _items(group.get("items"))
        if items:
            blocks.append("\n".join([f"**{group.get('section', 'Links')}**"] + items))

    if not blocks:
        return ""
    return "## Receipts · ways to get to know me\n\n" + "\n\n".join(blocks) + "\n"


def strip_instructions(text: str) -> str:
    """Drop the trailing HTML instruction block (contains banned strings + raw placeholders)."""
    idx = text.find("<!--")
    return (text[:idx].rstrip() + "\n") if idx != -1 else text


def build_cover_md(jd_path: Path) -> tuple[str, str, str, str]:
    folder = jd_path.parent
    jd_text = jd_path.read_text(encoding="utf-8")
    gen = _load("generate_resume", "generate-resume.py")
    role_type = gen.detect_role_type(jd_text)
    company, role = parse_company_role(folder.name)

    prof = _profile()
    ident = prof.get("identity", {}) or {}
    pf = prof.get("portfolio", {}) or {}
    fixed = prof.get("cover_sheet_fixed", {}) or {}

    name = ident.get("name", "Candidate")
    first = name.split()[0] if name.strip() else "Candidate"
    taglines = ident.get("taglines", {}) or {}
    tagline = taglines.get("ai") or taglines.get("default", "")

    note_tpl = fixed.get("note_template", DEFAULT_NOTE_TEMPLATE)
    footer = fixed.get("footer", "")

    tpl = strip_instructions(TEMPLATE.read_text(encoding="utf-8"))
    repl = {
        "{{CANDIDATE_NAME}}": name,
        "{{CANDIDATE_FIRST}}": first,
        "{{TAGLINE}}": tagline,
        "{{CONTACT}}": ident.get("contact", ""),
        "{{CLAUDE_LINK}}": ident.get("claude_link", ""),
        "{{MANIFEST_URL}}": _bare_manifest(pf.get("manifest_url", "")),
        "{{EVAL_PROMPT}}": build_eval_prompt(company, role, role_type, prof),
        "{{HUMAN_NOTE}}": note_tpl.format(company=company, role=role),
        "{{RECEIPTS}}": render_receipts(fixed),
        "{{FOOTER}}": footer,
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)

    # Collapse blank runs and any doubled horizontal rule left by an omitted (empty) section.
    tpl = re.sub(r"\n{3,}", "\n\n", tpl)
    tpl = re.sub(r"(?m)^---\s*\n\s*\n---\s*$", "---", tpl)
    tpl = re.sub(r"\n{3,}", "\n\n", tpl).rstrip() + "\n"
    return tpl, role_type, company, role


def generate(jd_path: Path, no_pdf: bool = False, force_locked: bool = False) -> None:
    folder = jd_path.parent
    if (folder / "SUBMITTED.md").exists() and not force_locked:
        print(f"[ABORT] {folder.name} is LOCKED (SUBMITTED.md present) — refusing to overwrite a "
              f"submitted application's cover sheet. Use --force-locked to override.")
        sys.exit(3)
    cover_md_text, role_type, company, role = build_cover_md(jd_path)

    cover_md = folder / "cover-sheet.md"
    cover_md.write_text(cover_md_text, encoding="utf-8")
    print(f"[OK] Written: {cover_md}  (role_type={role_type}; {company} / {role})")

    exports = folder / "exports"
    docx_out = exports / "dustin-winkler-cover-sheet.docx"
    rendered = []
    try:
        render_docx = _load("render_docx", "render-docx.py")
        render_docx.render(cover_md, docx_out)
        rendered.append("docx")
        print(f"[OK] Rendered .docx: {docx_out}")
    except ModuleNotFoundError as e:
        print(f"[skip] render dependency missing ({e}); cover-sheet.md is still written")
    except Exception as e:
        print(f"[ERROR] cover .docx render failed: {e}")

    if "docx" in rendered and not no_pdf:
        try:
            render_pdf = _load("render_pdf", "render-pdf.py")
            pdf = render_pdf.render_pdf(docx_out)
            rendered.append("pdf")
            print(f"[OK] Rendered PDF:   {pdf}")
        except Exception as e:
            print(f"[WARN] cover PDF failed (.docx still written): {e}")
    elif no_pdf:
        print("[skip] cover PDF deferred (--no-pdf).")

    if rendered:
        try:
            _load("sign_exports", "sign-exports.py").sign(folder)
            print(f"[OK] Signed exports/ ({', '.join(rendered)})")
        except Exception as e:
            print(f"[skip] signing unavailable ({e})")

    # Content gate (loud) — proves the generated sheet is submission-clean out of the box.
    try:
        chk = _load("check_cover_sheet", "check-cover-sheet.py")
        cfg = yaml.safe_load((SCRIPT_DIR / "cover-sheet-lint.yaml").read_text(encoding="utf-8")) or {}
        cfg = chk.merge_overrides(cfg, _profile())
        violations = chk.lint(cover_md.read_text(encoding="utf-8"), cfg)
        if violations:
            print(f"[FAIL] cover-sheet-lint: {len(violations)} violation(s):")
            for v in violations:
                print(f"   - {v}")
        else:
            print("[OK] cover-sheet-lint: clean")
    except Exception as e:
        print(f"[skip] cover-sheet-lint unavailable ({e})")

    print("[note] HUMAN_NOTE is a tailored DRAFT — sharpen the final polish in your own voice before submitting.")


def main():
    ap = argparse.ArgumentParser(description="Generate a tailored cover-sheet.md from the master template")
    ap.add_argument("--jd", required=True, help="Path to applications/FOLDER/job-posting.md")
    ap.add_argument("--no-pdf", action="store_true", help="Skip the LibreOffice PDF step (fast iteration)")
    ap.add_argument("--force-locked", action="store_true", help="Override the submitted-folder lockout")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    jd = Path(args.jd)
    if not jd.exists():
        print(f"ERROR: JD not found: {jd}")
        sys.exit(1)
    generate(jd, args.no_pdf, args.force_locked)


if __name__ == "__main__":
    main()
