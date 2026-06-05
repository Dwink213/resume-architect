# Resume Architect — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carve the resume/cover-sheet engine out of Dustin's private job-hunt repo into a standalone, shareable GitHub template repo that any user can run via a conversational `/onboard` wizard — with all identity-specific data, logic, and prose driven by a single `profile.yaml`.

**Architecture:** Three-layer separation. (1) An identity-agnostic Python **engine** that assembles a resume/cover-sheet from data. (2) A single **`profile.yaml`** holding every identity constant (name, URLs, cover-sheet fixed sections, differentiator terms, identity-bound gate strings, knockout facts) plus `resume-source.yaml` + a testimony KB holding the candidate's content. (3) Conversational **skills** (`/onboard`, `/s add-source`) that produce those data files. Dustin's real data ships as the worked example; a fictional "Jane Developer" fixture proves the engine works on a non-Dustin profile.

**Tech Stack:** Python 3.10+ (stdlib + PyYAML, python-docx, mammoth), LibreOffice headless for PDF, Claude Code skills (Markdown), pytest for the smoke test, Git/GitHub template repo.

**Source repo (read-only reference):** `C:\Users\Dustin\OneDrive\Documents\Job-Hunt\`
**Target repo (this folder, becomes its own GitHub project):** `C:\Users\Dustin\OneDrive\Documents\resume-architect\`

**Spec:** `Job-Hunt/docs/superpowers/specs/2026-06-05-resume-architect-export-design.md`

---

## File Structure (target repo)

```
resume-architect/
├── profile.yaml                       # NEW — identity constants (the wizard's target)
├── profile.example-jane.yaml          # NEW — fictional fixture (genericization proof)
├── tools/
│   ├── generate-resume.py             # COPY + de-hardcode (summaries→data, generic loops, profile header)
│   ├── generate-coversheet.py         # COPY + de-hardcode (URLs/note→profile)
│   ├── parse-jd.py                    # COPY as-is
│   ├── check-resume.py                # COPY + merge profile.gate_overrides
│   ├── check-cover-sheet.py           # COPY as-is (verify no Dustin constants inside — Task 4b)
│   ├── evidence-check.py              # COPY as-is (already generic)
│   ├── render-docx.py / render-pdf.py / docx-to-html.py / sign-exports.py  # COPY as-is
│   ├── profile_loader.py              # NEW — single load_profile() helper, shared by engine + gates
│   ├── resume-lint.yaml               # COPY, split: universal AI-tells only
│   ├── cover-sheet-lint.yaml          # COPY (verify generic — Task 4b)
│   ├── resume-source.yaml             # COPY (Dustin worked example) + NEW summaries: block
│   └── knowledge/
│       ├── schema.yaml                # COPY + document summaries + new profile cross-refs
│       └── testimonies/*.yaml          # COPY (Dustin worked examples)
├── templates/
│   └── cover-sheet-master.md          # COPY (de-Dustin'd: fixed sections become profile-driven — Task 4)
├── .claude/skills/
│   ├── onboard/SKILL.md               # NEW — conversational first-run wizard
│   ├── add-source/SKILL.md            # NEW — /s add-one-testimony
│   ├── job-hunt-architect/SKILL.md    # COPY + de-hardcode (manifest/AWACS/Suno/NC-State → profile refs)
│   ├── filter-forecaster/SKILL.md     # COPY + de-hardcode (knockouts → profile.knockouts)
│   └── resume-summary-humanizer/SKILL.md  # COPY (verify generic)
├── applications/_examples/            # 1–2 of Dustin's real apps, end-to-end (sanitized of employer refs)
├── tests/
│   ├── conftest.py
│   └── test_smoke_jane.py             # NEW — fresh-profile → working-resume e2e
├── docs/
│   ├── README.md                      # generic-user quickstart
│   └── CONTAMINATION-MAP.md           # inventory of intentionally-retained personal data
├── IMPLEMENTATION-PLAN.md             # this file
├── requirements.txt
├── .gitignore
└── CLAUDE.md                          # rewritten for a generic user
```

**Decomposition note:** Phases are sequentially dependent (the wizard cannot be tested until the engine is generic). Execute in order. Phase 2 (de-hardcoding `generate-resume.py`) is the riskiest and largest — it is split into small TDD tasks.

---

## Phase 0 — Scaffold the standalone repo

### Task 0.1: Initialize the repo skeleton

**Files:**
- Create: `resume-architect/.gitignore`
- Create: `resume-architect/requirements.txt`

- [ ] **Step 1: Write `.gitignore`**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
node_modules/
*.tmp
# Per-application generated artifacts are disposable
applications/**/exports/
!applications/_examples/**/exports/
# Never ship a personal profile by accident when others fork
# (the worked-example profile.yaml IS intentionally committed; see CONTAMINATION-MAP.md)
```

- [ ] **Step 2: Write `requirements.txt`**

```
pyyaml>=6.0
python-docx>=1.1.0
mammoth>=1.6.0
pytest>=8.0
```

- [ ] **Step 3: Initialize git and set identity**

Run:
```bash
cd "C:/Users/Dustin/OneDrive/Documents/resume-architect"
git init
git config user.name "Dustin Winkler"
git config user.email "dustin@awacs.ai"
git add .gitignore requirements.txt IMPLEMENTATION-PLAN.md
git commit -m "chore: scaffold resume-architect standalone repo"
```
Expected: a new repo with one commit, `git log --oneline` shows the scaffold commit.

### Task 0.2: Copy the as-is engine scripts

These files are identity-agnostic and copy verbatim. **Do not edit them in this task.**

- [ ] **Step 1: Copy the render/parse/evidence scripts**

Run (PowerShell):
```powershell
$src = "C:\Users\Dustin\OneDrive\Documents\Job-Hunt\tools"
$dst = "C:\Users\Dustin\OneDrive\Documents\resume-architect\tools"
New-Item -ItemType Directory -Force $dst | Out-Null
foreach ($f in @("parse-jd.py","evidence-check.py","render-docx.py","render-pdf.py","docx-to-html.py","sign-exports.py","check-cover-sheet.py","cover-sheet-lint.yaml")) {
  Copy-Item "$src\$f" "$dst\$f"
}
```
Expected: 8 files present in `resume-architect/tools/`.

- [ ] **Step 2: Copy the KB and data files (worked examples)**

Run (PowerShell):
```powershell
$src = "C:\Users\Dustin\OneDrive\Documents\Job-Hunt\tools"
$dst = "C:\Users\Dustin\OneDrive\Documents\resume-architect\tools"
Copy-Item "$src\resume-source.yaml" "$dst\resume-source.yaml"
Copy-Item "$src\resume-lint.yaml"   "$dst\resume-lint.yaml"
Copy-Item "$src\knowledge" "$dst\knowledge" -Recurse
```
Expected: `resume-source.yaml`, `resume-lint.yaml`, and `knowledge/testimonies/*.yaml` present.

- [ ] **Step 3: Copy templates and the three resume skills**

Run (PowerShell):
```powershell
$srcRoot = "C:\Users\Dustin\OneDrive\Documents\Job-Hunt"
$dstRoot = "C:\Users\Dustin\OneDrive\Documents\resume-architect"
Copy-Item "$srcRoot\templates" "$dstRoot\templates" -Recurse
New-Item -ItemType Directory -Force "$dstRoot\.claude\skills" | Out-Null
foreach ($s in @("job-hunt-architect","filter-forecaster","resume-summary-humanizer")) {
  Copy-Item "$srcRoot\.claude\skills\$s" "$dstRoot\.claude\skills\$s" -Recurse
}
```
Expected: `templates/cover-sheet-master.md` and three skill folders present.

- [ ] **Step 4: Commit the copied baseline**

Run:
```bash
git add tools templates .claude
git commit -m "chore: import engine, KB, templates, skills from job-hunt (pre-genericization baseline)"
```
Expected: commit succeeds; this is the "before" state for genericization.

---

## Phase 1 — The profile.yaml seam

### Task 1.1: Write `profile_loader.py` (TDD)

A single helper every script uses to find and load `profile.yaml`. Centralizing avoids each script re-implementing path logic.

**Files:**
- Create: `tools/profile_loader.py`
- Test: `tests/test_profile_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_profile_loader.py
import importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"

def _load():
    spec = importlib.util.spec_from_file_location("profile_loader", TOOLS / "profile_loader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_loads_named_profile(tmp_path):
    pl = _load()
    p = tmp_path / "profile.yaml"
    p.write_text("identity:\n  name: Jane Developer\n", encoding="utf-8")
    prof = pl.load_profile(p)
    assert prof["identity"]["name"] == "Jane Developer"

def test_missing_profile_raises(tmp_path):
    pl = _load()
    import pytest
    with pytest.raises(FileNotFoundError):
        pl.load_profile(tmp_path / "nope.yaml")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_profile_loader.py -v`
Expected: FAIL (`profile_loader.py` does not exist).

- [ ] **Step 3: Write minimal implementation**

```python
# tools/profile_loader.py
"""Single source of truth for loading profile.yaml (identity constants).

Every engine script and gate calls load_profile() so path logic + the
'profile missing' error message live in exactly one place.
"""
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_PROFILE = REPO_ROOT / "profile.yaml"


def load_profile(path: Path | str = DEFAULT_PROFILE) -> dict:
    """Load and return the profile dict. Raises FileNotFoundError with an
    actionable message if it is missing (tells the user to run /onboard)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"profile.yaml not found at {p}. Run the /onboard wizard to create it, "
            f"or copy profile.example-jane.yaml to profile.yaml to try the engine."
        )
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_profile_loader.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add tools/profile_loader.py tests/test_profile_loader.py
git commit -m "feat: add profile_loader.py — single load_profile() helper"
```

### Task 1.2: Author Dustin's `profile.yaml` (worked example)

**Files:**
- Create: `profile.yaml`

- [ ] **Step 1: Write `profile.yaml` with Dustin's real values**

Pull values from the source repo: header (`resume-source.yaml` lines 5-13), manifest/lab URLs (`generate-coversheet.py` lines 39-53), open-source PRs (`resume-source.yaml` lines 159-170), identity-bound lint strings (`resume-lint.yaml` lines 11-39), education knockout (`resume-source.yaml` lines 226-227).

```yaml
# profile.yaml — the ONE file that makes this engine "you."
# The /onboard wizard writes this. Engine + skills + gates read it.

identity:
  name: "Dustin Winkler"
  contact: "dustin@awacs.ai · awacs.ai · github.com/Dwink213 · linkedin.com/in/dustin-winkler-nc"
  claude_link: "https://claude.ai/share/f19e5a2d-de9d-45df-8082-640f6a352dc5"
  taglines:
    default: "Forward Deployed AI Engineer · 25 years of infrastructure scar tissue"
    ai:      "Founder & Principal AI Engineer, AWACS · I direct AI to ship production systems"
    govcon:  "AI Systems Engineer · Federal GOVCON · Governance Architecture"

portfolio:
  manifest_url: "https://github.com/Dwink213/manifest/blob/main/README.md"
  lab_url: "https://awacs.ai/lab"
  default_artifact: "https://awacs.ai/methodology"
  role_artifact:                       # role_type -> the one artifact spotlighted in the eval prompt
    tech_lead_manager:   "https://awacs.ai/methodology"
    research_engineer:   "https://awacs.ai/case-studies/doctrine-enforcement.html"
    trust_and_safety:    "https://awacs.ai/case-studies/doctrine-enforcement.html"
    applied_ai_engineer: "https://github.com/Dwink213/api-observability-framework"
    agentic_lead:        "https://github.com/Dwink213/api-observability-framework"
    fde:                 "https://awacs.ai/case-studies/api-voyager.html"
    govcon:              "https://awacs.ai/case-studies/doctrine-enforcement.html"

upstream:                              # renders the "UPSTREAM" resume section; omit block to skip section
  section_title: "UPSTREAM · ANTHROPICS/CLAUDE-CODE"
  intro: "My agentic system studied the Claude Code release notes, surfaced these issues, validated them under my direction, and filed them under my account:"

cover_sheet_fixed:                     # copied verbatim into every cover sheet; empty sub-lists omit their section
  note_template: "When a team needs production AI that survives contact with reality - not a prototype - that's the work I do, and it's why I'm a fit for {role} at {company}. I direct AI to build and ship, and I catch it when it's wrong. The artifacts below are the proof; the evaluation prompt lets you verify it yourself, from scratch, with nothing staged."

differentiators:
  - "exit(2)"
  - "31-hour"
  - "gated KB"
  - "zero-trust"

gate_overrides:                        # merged with universal lists in resume-lint.yaml
  required:  ["AWACS", "awacs.ai", "#44707", "#57946", "#44711"]
  banned:    ["#37550"]
  max_occurrences: { "11,000": 1, "11k": 1 }

knockouts:
  education: "NC State, Computer Engineering coursework 1998–2000 — no completed bachelor's"
  clearances: []
```

- [ ] **Step 2: Validate it loads**

Run: `python -c "import sys; sys.path.insert(0,'tools'); from profile_loader import load_profile; print(load_profile()['identity']['name'])"`
Expected: prints `Dustin Winkler`.

- [ ] **Step 3: Commit**

```bash
git add profile.yaml
git commit -m "feat: add Dustin's profile.yaml (worked example)"
```

### Task 1.3: Author the Jane fixture

**Files:**
- Create: `profile.example-jane.yaml`
- Create: `tools/knowledge/testimonies/jane-rag-pipeline.example.yaml`
- Create: `tools/knowledge/testimonies/jane-eval-harness.example.yaml`
- Create: a Jane variant of `resume-source.yaml` referenced by the smoke test: `tests/fixtures/jane-resume-source.yaml`

- [ ] **Step 1: Write `profile.example-jane.yaml`**

```yaml
identity:
  name: "Jane Developer"
  contact: "jane@example.com · github.com/janedev · linkedin.com/in/janedev"
  claude_link: "https://claude.ai/share/EXAMPLE"
  taglines:
    default: "Applied AI Engineer · 8 years building data products"
    ai:      "Applied AI Engineer · I ship LLM features to production"
    govcon:  "AI Engineer · Public-sector data systems"
portfolio:
  manifest_url: "https://github.com/janedev/portfolio"
  lab_url: "https://janedev.example.com"
  default_artifact: "https://github.com/janedev/rag-pipeline"
  role_artifact:
    applied_ai_engineer: "https://github.com/janedev/rag-pipeline"
    agentic_lead:        "https://github.com/janedev/eval-harness"
upstream: null                          # Jane has no upstream PRs — section is omitted
cover_sheet_fixed:
  note_template: "I build LLM features that survive production, and I'm a fit for {role} at {company}. The artifacts below are the proof."
differentiators:
  - "RAG"
  - "eval harness"
gate_overrides:
  required:  ["janedev"]
  banned:    []
  max_occurrences: {}
knockouts:
  education: "B.S. Computer Science, State University (2016)"
  clearances: []
```

- [ ] **Step 2: Write two Jane testimony YAMLs**

Follow `tools/knowledge/schema.yaml`. Minimal but valid:

```yaml
# tools/knowledge/testimonies/jane-rag-pipeline.example.yaml
id: jane-rag-pipeline
title: "PRODUCTION RAG PIPELINE OVER SUPPORT TICKETS"
type: case-study
date: "2024-03 to 2024-09"
employer: "Acme Data Co"
role_types: [applied_ai_engineer, agentic_lead]
tags: [llm, rag, production, python, pipeline, evaluation]
ats_keywords: ["vector database", "retrieval augmented generation", "embeddings"]
testimony: >
  I built a retrieval-augmented generation pipeline answering support questions over
  60k historical tickets. I owned the architecture: chunking, embeddings, a re-ranking
  stage, and an eval harness that gated every prompt change before it shipped.
metrics:
  - "60,000 tickets indexed"
  - "12-point answer-accuracy lift over keyword search"
claims:
  - { verified: true, text: "Shipped to production", proof: "https://github.com/janedev/rag-pipeline" }
evidence_urls:
  - "https://github.com/janedev/rag-pipeline"
bullet_variants:
  featured: >
    Built and shipped a production RAG pipeline over 60k support tickets — chunking,
    embeddings, re-ranking, and an eval harness gating every prompt change. 12-point
    accuracy lift over keyword search.
  long: "Shipped a production RAG pipeline over 60k tickets with an eval gate; 12-point accuracy lift."
  short: "Production RAG pipeline over 60k tickets."
  ats_dense: "Retrieval augmented generation (RAG) pipeline, embeddings, vector database, re-ranking, LLM evaluation harness, production Python."
```

```yaml
# tools/knowledge/testimonies/jane-eval-harness.example.yaml
id: jane-eval-harness
title: "LLM EVAL HARNESS AS A SHIP GATE"
type: tool
date: "2024-06"
employer: "Acme Data Co"
role_types: [applied_ai_engineer, research_engineer]
tags: [llm, evaluation, evals, python, quality-gates]
ats_keywords: ["regression testing", "golden dataset", "llm-as-judge"]
testimony: >
  I built the eval harness that became the merge gate for every prompt change: a golden
  dataset, an LLM-as-judge scorer, and a CI step that blocked regressions.
metrics:
  - "180-example golden set"
  - "0 prompt regressions shipped after adoption"
claims:
  - { verified: true, text: "Used as CI merge gate", proof: "https://github.com/janedev/eval-harness" }
evidence_urls:
  - "https://github.com/janedev/eval-harness"
bullet_variants:
  featured: >
    Built the LLM eval harness that gates every prompt change — golden dataset,
    LLM-as-judge scoring, CI regression block. Zero prompt regressions shipped after adoption.
  long: "Built an LLM eval harness used as the CI merge gate; zero prompt regressions after adoption."
  short: "LLM eval harness used as a CI ship gate."
  ats_dense: "LLM evaluation harness, golden dataset, llm-as-judge, regression testing, CI quality gate."
```

- [ ] **Step 3: Write `tests/fixtures/jane-resume-source.yaml`**

A trimmed `resume-source.yaml` with Jane's experience, NO Dustin company names, including a `summaries:` block (the new data field Phase 2 introduces) and `role_type_tags`. Keep two experience entries (one bullets-format, one prose-format) and one founder/none.

```yaml
header:
  name: "Jane Developer"
  tagline_default: "Applied AI Engineer · 8 years building data products"
  tagline_ai: "Applied AI Engineer · I ship LLM features to production"
  tagline_govcon: "AI Engineer · Public-sector data systems"
  contact: "jane@example.com · github.com/janedev"
  claude_link: "https://claude.ai/share/EXAMPLE"

summaries:
  applied_ai_engineer: >
    I build and ship LLM features that survive production. I owned a RAG pipeline over
    60k support tickets and the eval harness that gates every prompt change. Eight years
    turning messy data into products teams rely on.
  agentic_lead: >
    I design agentic and retrieval systems end to end and gate them with evals before
    they ship. RAG over 60k tickets, an LLM-as-judge merge gate, zero regressions after adoption.

featured_engagements: []   # Jane uses KB testimonies only

experience:
  - company: "Acme Data Co"
    location: "Remote"
    dates: "2019 – Present"
    title: "Senior Applied AI Engineer"
    bullets:
      - id: jane_rag
        text: "**Shipped a production RAG pipeline** over 60k support tickets with an eval gate; 12-point accuracy lift."
        tags: [llm, rag, production, python]
      - id: jane_eval
        text: "**Built the LLM eval harness** used as the CI merge gate; zero prompt regressions after adoption."
        tags: [llm, evaluation, quality-gates]
  - company: "Early Startup Inc"
    location: "Austin, TX"
    dates: "2016 – 2019"
    title: "Data Engineer"
    format: prose
    text: >
      Built batch and streaming data pipelines feeding the analytics platform; owned the
      ETL that the whole product reported off of.
    tags: [python, pipeline, data]

founder_work: []

open_source: []

competency_blocks:
  - id: llm_systems
    label: "LLM & retrieval"
    terms: "RAG, embeddings, vector databases, re-ranking, LLM-as-judge evaluation, prompt engineering"
    tags: [llm, rag, evaluation]
    weight: 9
  - id: languages
    label: "Languages"
    terms: "Python, SQL, TypeScript"
    tags: [python, languages]
    weight: 5

certifications:
  - "AWS Solutions Architect Associate (2022)"

education:
  - "B.S. Computer Science, State University (2016)"

role_type_tags:
  applied_ai_engineer: [llm, rag, production, python, evaluation]
  agentic_lead: [llm, rag, evaluation, quality-gates]
```

- [ ] **Step 4: Commit**

```bash
git add profile.example-jane.yaml tools/knowledge/testimonies/jane-*.example.yaml tests/fixtures/jane-resume-source.yaml
git commit -m "feat: add Jane Developer fixture (genericization proof data)"
```

---

## Phase 2 — De-hardcode `generate-resume.py`

This is the core genericization. Copy the file first, then transform it in small, tested steps.

### Task 2.1: Copy and add the failing genericization test

**Files:**
- Create: `tools/generate-resume.py` (copy)
- Test: `tests/test_smoke_jane.py`

- [ ] **Step 1: Copy the engine file verbatim**

Run (PowerShell):
```powershell
Copy-Item "C:\Users\Dustin\OneDrive\Documents\Job-Hunt\tools\generate-resume.py" "C:\Users\Dustin\OneDrive\Documents\resume-architect\tools\generate-resume.py"
```

- [ ] **Step 2: Write the failing end-to-end test (drives all of Phase 2)**

```python
# tests/test_smoke_jane.py
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SAMPLE_JD = """# Applied AI Engineer
We need someone to build production RAG and LLM evaluation systems in Python.
Required: retrieval augmented generation, embeddings, evals, production ai.
"""

def test_jane_resume_builds_without_dustin_data(tmp_path):
    gen = _load_module("generate_resume", "generate-resume.py")
    source = yaml.safe_load((FIXTURES / "jane-resume-source.yaml").read_text(encoding="utf-8"))

    app_folder = tmp_path / "applications" / "2026-06-05_Acme_Applied-AI-Engineer"
    app_folder.mkdir(parents=True)
    (app_folder / "job-posting.md").write_text(SAMPLE_JD, encoding="utf-8")

    role_type = gen.detect_role_type(SAMPLE_JD)
    resume_text, report = gen.build_resume(source, SAMPLE_JD, role_type, app_folder, dry_run=True)

    # Genericization assertions: NO Dustin facts leak from hardcoded logic
    for forbidden in ["AWACS", "Enterprise Health-Tech Co.", "National Cloud Provider", "#44707", "31-hour"]:
        assert forbidden not in resume_text, f"Dustin fact leaked: {forbidden}"
    # Jane's real content is present
    assert "Jane Developer" in resume_text
    assert "RAG" in resume_text
    assert "Acme Data Co" in resume_text
    assert "EDUCATION" in resume_text
```

- [ ] **Step 3: Run it and confirm it fails for the right reasons**

Run: `pytest tests/test_smoke_jane.py -v`
Expected: FAIL — either `StopIteration` (hardcoded `company == "Enterprise Health-Tech Co."` lookup) or assertion failure on `AWACS`/`31-hour` (hardcoded summaries). Both confirm the hardcoding the next tasks remove.

### Task 2.2: Move summaries from Python literals into data

**Files:**
- Modify: `tools/generate-resume.py:315-392` (`generate_summary`)
- Modify: `tools/resume-source.yaml` (add `summaries:` block)

- [ ] **Step 1: Replace `generate_summary()` body to read from `source`**

Replace the entire function (lines 315-392) with:

```python
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
```

- [ ] **Step 2: Add Dustin's seven summaries to `resume-source.yaml`**

Add a top-level `summaries:` block to `tools/resume-source.yaml` containing the seven role-type strings that were previously hardcoded in `generate_summary()` (copy them verbatim from the source repo's `generate-resume.py` lines 320-391, keys: `fde`, `tech_lead_manager`, `agentic_lead`, `applied_ai_engineer`, `trust_and_safety`, `govcon`, `research_engineer`). Use YAML block scalars (`>`).

- [ ] **Step 3: Run the smoke test**

Run: `pytest tests/test_smoke_jane.py -v`
Expected: still FAIL, but now on the company-lookup `StopIteration` (summaries no longer leak Dustin facts). Confirms Step 1 worked.

- [ ] **Step 4: Commit**

```bash
git add tools/generate-resume.py tools/resume-source.yaml
git commit -m "refactor: move resume summaries from Python literals to resume-source.yaml data"
```

### Task 2.3: Generic experience + founder rendering

**Files:**
- Modify: `tools/generate-resume.py:395-545` (`build_resume`)

- [ ] **Step 1: Replace the hardcoded company lookups with a generic loop**

In `build_resume()`, DELETE the hardcoded lookups (source lines 425-438):
```python
align_exp = next(e for e in source["experience"] if e["company"] == "Enterprise Health-Tech Co.")
cloud_provider_exp = next(...)
public_safety_exp = next(...)
align_bullets = ...
cloud_provider_bullets = ...
founder_awacs = next(...)
founder_blue = next(...)
include_federal_proposal = ...
```
and the corresponding hardcoded render blocks (source lines 476-507).

Replace the EXPERIENCE assembly with a generic renderer that handles both `bullets` and `format: prose` entries, and renders `founder_work` generically (newest-first, gated by optional `role_gate`):

```python
def _render_experience_entry(entry: dict, role_tags: list, jd_terms: list) -> list[str]:
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
```

Then in `build_resume`, build the EXPERIENCE section by iterating data in order — founder_work first (it is current), then employer experience:

```python
    # --- EXPERIENCE (generic; founder_work first as current role) ---
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
```

Note: the `role_gate` field replaces the hardcoded "Federal Proposal Consultancy only if govcon" rule. Add `role_gate: [govcon]` to the `federal_proposal` entry in `resume-source.yaml`; AWACS gets no gate (always renders).

- [ ] **Step 2: Add `role_gate` to Dustin's federal_proposal entry**

In `tools/resume-source.yaml`, add `role_gate: [govcon]` under the `federal_proposal` founder entry (id `federal_proposal`).

- [ ] **Step 3: Run the smoke test**

Run: `pytest tests/test_smoke_jane.py -v`
Expected: still FAIL — now on the hardcoded UPSTREAM section (Task 2.4) or the `claude_link`/header. Closer. Run `-x` to see the next failure.

- [ ] **Step 4: Commit**

```bash
git add tools/generate-resume.py tools/resume-source.yaml
git commit -m "refactor: render experience + founder_work generically (no hardcoded company names)"
```

### Task 2.4: Profile-drive the header link and UPSTREAM section

**Files:**
- Modify: `tools/generate-resume.py` (header block ~lines 451-462; UPSTREAM block ~lines 510-518)

- [ ] **Step 1: Make the UPSTREAM section data-driven and omittable**

Replace the hardcoded UPSTREAM block (source lines 510-518) with:

```python
    prs = source.get("open_source", [])
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
```

This reads `source["_profile"]["upstream"]` — Task 2.5 injects the profile into `source` under `_profile`. If `open_source` is empty (Jane), the whole section is skipped.

- [ ] **Step 2: Keep header using `header['claude_link']`** (already data-driven via YAML — no change needed beyond confirming Jane's header has `claude_link`).

- [ ] **Step 3: Commit**

```bash
git add tools/generate-resume.py
git commit -m "refactor: data-drive UPSTREAM section; omit when no open_source entries"
```

### Task 2.5: Inject profile into the engine entrypoint

**Files:**
- Modify: `tools/generate-resume.py:558-623` (`main`) and `build_resume` signature use

- [ ] **Step 1: Load profile in `main()` and attach to `source`**

In `main()`, after `source = yaml.safe_load(...)` (source line 617), add:

```python
    # Attach identity profile so build_resume can read profile-driven sections (UPSTREAM title, etc.)
    import importlib.util as _il
    _spec = _il.spec_from_file_location("profile_loader", SCRIPT_DIR / "profile_loader.py")
    _pl = _il.module_from_spec(_spec); _spec.loader.exec_module(_pl)
    try:
        source["_profile"] = _pl.load_profile()
    except FileNotFoundError:
        source["_profile"] = {}   # engine still runs with resume-source.yaml alone
```

- [ ] **Step 2: Run the full smoke test**

Run: `pytest tests/test_smoke_jane.py -v`
Expected: PASS. Jane's resume builds, no Dustin facts leak, Jane's content present.

- [ ] **Step 3: Regression check — Dustin still builds**

Run (PowerShell, against a throwaway JD):
```powershell
"# FDE`nForward deployed engineer, agentic, quality gates, playbook." | Set-Content -Encoding utf8 $env:TEMP\jd.md
python tools/generate-resume.py --jd $env:TEMP\jd.md --dry-run --no-pdf
```
Expected: prints a resume containing `AWACS`, `#44707`, the FDE summary — Dustin's worked example is unbroken.

- [ ] **Step 4: Commit**

```bash
git add tools/generate-resume.py
git commit -m "feat: inject profile.yaml into resume engine; Jane smoke test passes"
```

---

## Phase 3 — Lint split + gate merge

### Task 3.1: Split `resume-lint.yaml` and merge `profile.gate_overrides` in `check-resume.py`

**Files:**
- Modify: `tools/resume-lint.yaml` (remove identity-bound entries)
- Modify: `tools/check-resume.py` (merge profile overrides)
- Test: `tests/test_gate_merge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gate_merge.py
import importlib.util
from pathlib import Path
TOOLS = Path(__file__).resolve().parent.parent / "tools"

def _load():
    spec = importlib.util.spec_from_file_location("check_resume", TOOLS / "check-resume.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_merge_adds_profile_required():
    cr = _load()
    base = {"required": ["EDUCATION"], "banned": [], "max_occurrences": {}}
    profile = {"gate_overrides": {"required": ["AWACS"], "banned": ["#37550"], "max_occurrences": {"11k": 1}}}
    merged = cr.merge_overrides(base, profile)
    assert "EDUCATION" in merged["required"] and "AWACS" in merged["required"]
    assert "#37550" in merged["banned"]
    assert merged["max_occurrences"]["11k"] == 1

def test_merge_handles_missing_overrides():
    cr = _load()
    base = {"required": ["EDUCATION"], "banned": [], "max_occurrences": {}}
    merged = cr.merge_overrides(base, {})
    assert merged["required"] == ["EDUCATION"]
```

- [ ] **Step 2: Run it — fails (no `merge_overrides`)**

Run: `pytest tests/test_gate_merge.py -v`
Expected: FAIL (`AttributeError: merge_overrides`).

- [ ] **Step 3: Add `merge_overrides` and wire it into `main()`**

Add to `tools/check-resume.py`:

```python
def merge_overrides(cfg: dict, profile: dict) -> dict:
    """Merge profile.gate_overrides into the universal lint cfg (profile adds, never removes)."""
    ov = (profile or {}).get("gate_overrides", {}) or {}
    out = {
        "required": list(cfg.get("required", []) or []) + list(ov.get("required", []) or []),
        "banned": list(cfg.get("banned", []) or []) + list(ov.get("banned", []) or []),
        "max_occurrences": {**(cfg.get("max_occurrences") or {}), **(ov.get("max_occurrences") or {})},
    }
    return out
```

In `main()`, after loading `cfg`, load the profile and merge:

```python
    import importlib.util as _il
    _spec = _il.spec_from_file_location("profile_loader", SCRIPT_DIR / "profile_loader.py")
    _pl = _il.module_from_spec(_spec); _spec.loader.exec_module(_pl)
    try:
        profile = _pl.load_profile()
    except FileNotFoundError:
        profile = {}
    cfg = merge_overrides(cfg, profile)
```

- [ ] **Step 4: Remove identity-bound entries from `resume-lint.yaml`**

Edit `tools/resume-lint.yaml`: from `required` remove `#44707`, `#57946`, `#44711`, `AWACS`, `awacs.ai` (keep `EDUCATION`). From `banned` remove `#37550` and the `11,000`-specific `max_occurrences`. Keep all universal AI-tells (`delve`, `tapestry`, em-dash, `self-drafted`, `underscore`, `heterogeneity tax`, `prose`, `refinement-of-self`). Leave a comment pointing to `profile.gate_overrides`.

- [ ] **Step 5: Run both the gate test and a Jane lint**

Run: `pytest tests/test_gate_merge.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add tools/check-resume.py tools/resume-lint.yaml tests/test_gate_merge.py
git commit -m "feat: split resume-lint (universal) from profile.gate_overrides (identity); merge at gate time"
```

### Task 3.2: Update the in-process lint call in `generate-resume.py`

**Files:**
- Modify: `tools/generate-resume.py:699-712` (the in-process content gate)

- [ ] **Step 1: Apply the same merge in the engine's inline gate**

Replace the `lint_cfg = yaml.safe_load(...)` line (source line 702) so it merges profile overrides before calling `check_resume.lint`:

```python
            check_resume = _load("check_resume", "check-resume.py")
            lint_cfg = yaml.safe_load((SCRIPT_DIR / "resume-lint.yaml").read_text(encoding="utf-8")) or {}
            lint_cfg = check_resume.merge_overrides(lint_cfg, source.get("_profile", {}))
            extra_required = check_resume.load_must_include(jd_folder)
            violations = check_resume.lint(out_path.read_text(encoding="utf-8"), lint_cfg, extra_required)
```

- [ ] **Step 2: Regression — Dustin build still lint-clean**

Run: `python tools/generate-resume.py --jd $env:TEMP\jd.md --dry-run --no-pdf` (reuse the FDE jd)
Expected: no `[FAIL] resume-lint` (the merged profile still requires AWACS, which Dustin's resume contains).

- [ ] **Step 3: Commit**

```bash
git add tools/generate-resume.py
git commit -m "fix: engine inline lint also merges profile.gate_overrides"
```

---

## Phase 4 — De-hardcode `generate-coversheet.py` + template

### Task 4.1: Profile-drive the cover-sheet generator

**Files:**
- Modify: `tools/generate-coversheet.py:38-62` (module constants) and `build_eval_prompt`/`build_cover_md`

- [ ] **Step 1: Copy the file**

Run (PowerShell):
```powershell
Copy-Item "C:\Users\Dustin\OneDrive\Documents\Job-Hunt\tools\generate-coversheet.py" "C:\Users\Dustin\OneDrive\Documents\resume-architect\tools\generate-coversheet.py"
```

- [ ] **Step 2: Replace the hardcoded constants with profile reads**

Delete `MANIFEST_URL`, `LAB_URL`, `ROLE_ARTIFACT`, `DEFAULT_ARTIFACT`, `NOTE_TEMPLATE` (lines 38-62). Load them from profile at call time:

```python
def _profile():
    spec = importlib.util.spec_from_file_location("profile_loader", SCRIPT_DIR / "profile_loader.py")
    pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
    try:
        return pl.load_profile()
    except FileNotFoundError:
        return {}

def build_eval_prompt(company: str, role: str, role_type: str, prof: dict) -> str:
    pf = prof.get("portfolio", {})
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
```

In `build_cover_md`, load `prof = _profile()`, pass it to `build_eval_prompt`, and pull the note template from `prof["cover_sheet_fixed"]["note_template"]` (fallback to a generic line):

```python
    note_tpl = (prof.get("cover_sheet_fixed", {}) or {}).get(
        "note_template",
        "I'm a strong fit for {role} at {company}. The artifacts below are the proof.",
    )
    tpl = tpl.replace("{{HUMAN_NOTE}}", note_tpl.format(company=company, role=role))
```

- [ ] **Step 3: Regression — Dustin cover sheet still generates**

Run: build a throwaway application folder named `applications/2026-06-05_Acme_FDE/` with a `job-posting.md`, then `python tools/generate-coversheet.py --jd applications/2026-06-05_Acme_FDE/job-posting.md --no-pdf`.
Expected: `cover-sheet.md` written; eval prompt contains the manifest + lab URLs from `profile.yaml`.

- [ ] **Step 4: Commit**

```bash
git add tools/generate-coversheet.py
git commit -m "refactor: cover-sheet generator reads URLs + note template from profile.yaml"
```

### Task 4.2: De-Dustin the cover-sheet template fixed sections

**Files:**
- Modify: `templates/cover-sheet-master.md`

- [ ] **Step 1: Audit the template for hardcoded personal artifacts**

Run: `grep -nE "suno|gumroad|awacs|notebooklm|Hooking|Chicken|#447|#579" templates/cover-sheet-master.md` (use the Grep tool).
Expected: a list of every hardcoded Suno/article/eBook/talk/issue line.

- [ ] **Step 2: Replace hardcoded fixed sections with profile placeholders**

For each fixed block (songs, writing, talks, links, footer), replace Dustin's literal URLs with a templated section the generator fills from `profile.cover_sheet_fixed`. Where Dustin's worked-example values should remain, they now come from `profile.yaml` (add `songs`, `writing`, `talks`, `links`, `footer` keys to Dustin's `profile.yaml.cover_sheet_fixed` — populate from the source template). Empty lists render nothing.

> **Note:** This couples to `check-cover-sheet.py`, which currently requires the Suno/article/issue strings. Task 4.3 makes that gate profile-aware so it does not force Dustin's specific artifacts on Jane.

- [ ] **Step 3: Commit**

```bash
git add templates/cover-sheet-master.md profile.yaml
git commit -m "refactor: cover-sheet template fixed sections are profile-driven"
```

### Task 4.3: Make `check-cover-sheet.py` profile-aware

**Files:**
- Read first: `tools/check-cover-sheet.py` and `tools/cover-sheet-lint.yaml` (confirm what they hardcode)
- Modify: whichever of the two holds the required Suno/article/issue strings

- [ ] **Step 1: Inspect the cover-sheet gate**

Read `tools/check-cover-sheet.py` and `tools/cover-sheet-lint.yaml`. Identify required strings that are Dustin-specific (song titles, article names, issue numbers).

- [ ] **Step 2: Move identity-bound required strings into `profile.gate_overrides` (cover variant)**

Add a `cover_required` list to `profile.yaml.gate_overrides`, and edit the cover-sheet gate to merge it the same way `check-resume.py` does (reuse the `merge_overrides` pattern; required-list only). Remove Dustin-specific required strings from `cover-sheet-lint.yaml`, leaving only universal checks (no leaked internal labels, no raw `{{PLACEHOLDER}}`).

- [ ] **Step 3: Verify both candidates pass their own gate**

Run the Dustin cover gen (Task 4.1 Step 3) and confirm `[OK] cover-sheet-lint: clean`. Then temporarily point the generator at the Jane profile (copy `profile.example-jane.yaml` to `profile.yaml` in a scratch checkout) and confirm Jane's cover sheet is also clean — proving no Dustin artifact is forced.

- [ ] **Step 4: Commit**

```bash
git add tools/check-cover-sheet.py tools/cover-sheet-lint.yaml profile.yaml
git commit -m "feat: cover-sheet gate merges profile cover_required (no forced Dustin artifacts)"
```

---

## Phase 5 — De-hardcode the skills

### Task 5.1: `filter-forecaster` reads knockouts from profile

**Files:**
- Modify: `.claude/skills/filter-forecaster/SKILL.md`

- [ ] **Step 1: Find the hardcoded knockout facts**

Run: `grep -nE "NC State|bachelor|degree|clearance|Dustin" .claude/skills/filter-forecaster/SKILL.md` (Grep tool).

- [ ] **Step 2: Replace literal facts with a profile read instruction**

Edit the skill so it loads `profile.yaml.knockouts` and treats those as the UNFIXABLE facts, instead of the hardcoded "NC State, no bachelor's." Add an explicit step: "Read `profile.yaml`; treat each entry under `knockouts` as a fact the resume cannot edit away. Report honestly." Remove every literal "Dustin"/"NC State"/"AWACS" reference, replacing with `{{candidate from profile.identity.name}}` phrasing.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/filter-forecaster/SKILL.md
git commit -m "refactor: filter-forecaster reads knockouts from profile.yaml (no hardcoded NC State)"
```

### Task 5.2: `job-hunt-architect` reads identity from profile

**Files:**
- Modify: `.claude/skills/job-hunt-architect/SKILL.md`

- [ ] **Step 1: Inventory the Dustin literals**

Run: `grep -nE "Dwink213|manifest|AWACS|awacs|Suno|#447|#579|NC State|Dustin" .claude/skills/job-hunt-architect/SKILL.md` (Grep tool). Expect many hits (Identity section, manifest URL, cover-sheet fixed sections, differentiator list, knockout reality check).

- [ ] **Step 2: Replace each literal with a profile reference**

Rewrite the skill so:
- "You know one candidate: Dustin Winkler … manifest at github.com/Dwink213/manifest" becomes "You know one candidate, defined in `profile.yaml`. Fetch `profile.portfolio.manifest_url` as the routing table."
- The cover-sheet "Fixed sections — copy verbatim" list (Suno songs, articles, issues) becomes "copy the fixed sections from `profile.cover_sheet_fixed`."
- The differentiator allow-list (`gated KB, exit(2), 31-hour`) becomes "from `profile.differentiators`."
- The degree knockout note becomes "from `profile.knockouts`."
- Replace the hardcoded `model: sonnet` description's Dustin phrasing with generic candidate phrasing.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/job-hunt-architect/SKILL.md
git commit -m "refactor: job-hunt-architect reads identity/manifest/fixed-sections/knockouts from profile.yaml"
```

### Task 5.3: Verify `resume-summary-humanizer` is generic

**Files:**
- Read: `.claude/skills/resume-summary-humanizer/SKILL.md`

- [ ] **Step 1: Scan for Dustin literals**

Run: `grep -nE "Dustin|AWACS|awacs|NC State|31-hour" .claude/skills/resume-summary-humanizer/SKILL.md` (Grep tool).

- [ ] **Step 2: If hits found, replace with `profile.identity.name` phrasing; if none, leave as-is and note in CONTAMINATION-MAP that it was verified clean.**

- [ ] **Step 3: Commit (only if changed)**

```bash
git add .claude/skills/resume-summary-humanizer/SKILL.md
git commit -m "refactor: confirm resume-summary-humanizer is identity-agnostic"
```

---

## Phase 6 — The `/onboard` wizard skill

### Task 6.1: Author `.claude/skills/onboard/SKILL.md`

**Files:**
- Create: `.claude/skills/onboard/SKILL.md`

- [ ] **Step 1: Write the skill**

Author a conversational skill with this contract (full prose, no placeholders — the engineer writes the complete instructions):

- **Frontmatter:** `name: onboard`, `description: "First-run wizard. Interviews a new user and writes profile.yaml + resume-source.yaml + testimony KB, then proves the engine works."`, `user_invocable: true`.
- **Stage 0 — Detect/resume:** read `profile.yaml` if present. If complete, tell the user they are onboarded and to use `/s`. If partial (some keys missing), summarize what exists and resume at the first unfilled stage. If absent, start at Stage 1.
- **Stage 1 — Identity:** ask name, contact, and the three taglines (default/ai/govcon). Write `profile.yaml.identity` immediately.
- **Stage 2 — Portfolio:** ask manifest URL, lab URL, default artifact, and per-role artifacts. Write `profile.yaml.portfolio`. If the user has no portfolio site, set `upstream: null` and use a GitHub profile as `manifest_url`.
- **Stage 3 — Experience:** walk job history; for each job, capture company/location/dates/title and 2-4 bullets (or prose). Write `resume-source.yaml.experience[]`. Also collect `summaries` per target role type (or generate a draft and confirm with the user — invoke `resume-summary-humanizer` to keep them in the user's voice).
- **Stage 4 — Projects:** repeat "tell me about a project you shipped." For each, write a testimony YAML per `tools/knowledge/schema.yaml`, then run `python tools/evidence-check.py --file <temp>` on its key claims; surface any UNBACKED claim and ask the user to either add proof or soften the claim. Never save an unbacked claim as a verified one.
- **Stage 5 — Differentiators + knockouts:** collect standout backed terms (`profile.differentiators`) and honest unfixables (`profile.knockouts` — degree, clearances). Be explicit that knockouts are facts the resume will NOT fake away.
- **Stage 6 — Cover-sheet fixed sections:** collect songs/writing/talks/links/footer the user has; skip any they lack. Write `profile.cover_sheet_fixed`.
- **Stage 7 — Dry run:** generate a resume against a bundled sample JD (`tests/fixtures/sample-jd.md`), show the output and the gate result, and confirm `resume-lint` is clean. This is the "it works" moment.
- **Plus — starter manifest:** offer to generate a `manifest/README.md` routing table from `profile` + testimonies (the external routing artifact), ready for the user to push to their own GitHub.
- **Honesty + circuit breaker:** mirror `job-hunt-architect` — if 3 consecutive evidence/write failures or 20 min without finishing a stage, stop and ask the user how to proceed.

- [ ] **Step 2: Add the bundled sample JD the dry-run uses**

Create `tests/fixtures/sample-jd.md` — a short generic Applied AI Engineer JD (reuse the SAMPLE_JD text from `test_smoke_jane.py`).

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/onboard/SKILL.md tests/fixtures/sample-jd.md
git commit -m "feat: add /onboard conversational wizard skill (resume-on-restart, evidence-gated)"
```

---

## Phase 7 — The `/s` add-source skill

### Task 7.1: Author `.claude/skills/add-source/SKILL.md`

**Files:**
- Create: `.claude/skills/add-source/SKILL.md`

- [ ] **Step 1: Write the skill**

Contract (full prose):
- **Frontmatter:** `name: add-source`, `description: "Add one new project/testimony to the KB. Invoke with /s or /add-source. Interviews, writes the testimony YAML, evidence-gates it."`, `user_invocable: true`. Document that `/s` is the short alias.
- **Behavior:** take the user's one-line description of a project. Interview for the schema fields (title, type, date, employer, role_types, tags, ats_keywords, testimony prose, metrics, claims with proof, evidence_urls, the four bullet_variants). Write `tools/knowledge/testimonies/<slug>.yaml`. Run `python tools/evidence-check.py` on the key claims; reject/soften anything unbacked before saving. Confirm: "Added <slug>. It will be auto-selected when a JD's keywords overlap its tags." Do NOT edit `profile.yaml` or `experience` — `/s` only grows the KB.

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/add-source/SKILL.md
git commit -m "feat: add /s (add-source) skill — incremental evidence-gated testimony add"
```

---

## Phase 8 — Full smoke test + CI

### Task 8.1: Round out the test suite

**Files:**
- Create: `tests/conftest.py`
- Modify: `tests/test_smoke_jane.py` (add a gate-passing assertion)

- [ ] **Step 1: Add `conftest.py` (path setup)**

```python
# tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
```

- [ ] **Step 2: Extend the smoke test to assert the gate passes on Jane**

Add to `tests/test_smoke_jane.py`:

```python
def test_jane_resume_passes_lint(tmp_path):
    gen = _load_module("generate_resume", "generate-resume.py")
    chk = _load_module("check_resume", "check-resume.py")
    source = yaml.safe_load((FIXTURES / "jane-resume-source.yaml").read_text(encoding="utf-8"))
    source["_profile"] = yaml.safe_load((ROOT / "profile.example-jane.yaml").read_text(encoding="utf-8"))
    role_type = gen.detect_role_type(SAMPLE_JD)
    resume_text, _ = gen.build_resume(source, SAMPLE_JD, role_type, tmp_path, dry_run=True)
    cfg = yaml.safe_load((TOOLS / "resume-lint.yaml").read_text(encoding="utf-8")) or {}
    cfg = chk.merge_overrides(cfg, source["_profile"])
    violations = chk.lint(resume_text, cfg, [])
    assert violations == [], f"Jane resume failed lint: {violations}"
```

- [ ] **Step 3: Run the whole suite**

Run: `pytest -v`
Expected: all tests pass (profile_loader, gate_merge, smoke_jane ×3).

- [ ] **Step 4: Add a minimal CI workflow**

Create `.github/workflows/ci.yml` running `pip install -r requirements.txt` then `pytest -v` on push/PR (ubuntu-latest, python 3.11). Skip the LibreOffice PDF path in CI (tests use `dry_run=True`, so no rendering needed).

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_smoke_jane.py .github/workflows/ci.yml
git commit -m "test: full Jane smoke suite + CI (proves engine works on non-Dustin profile)"
```

---

## Phase 9 — Safety gate, docs, and publish

### Task 9.1: Run the employer-sanitizer audit

**Files:**
- Create: `docs/CONTAMINATION-MAP.md`

- [ ] **Step 1: Run the sanitizer over the new repo**

Invoke the `employer-sanitizer` skill against `C:\Users\Dustin\OneDrive\Documents\resume-architect`. It audits for W-2 employer references (e.g. "Enterprise Health-Tech Co.", the enterprise email domain, internal product names, employee usernames).

- [ ] **Step 2: Triage every hit**

For each hit decide: (a) **intentional worked-example** (e.g. "Enterprise Health-Tech Co." in Dustin's `resume-source.yaml` experience — this is legitimately on his public resume) → record in CONTAMINATION-MAP; or (b) **leak** (an internal product name, an enterprise domain that should never ship) → remove it.

- [ ] **Step 3: Write `docs/CONTAMINATION-MAP.md`**

Inventory every remaining personal/identifying string with file:line and a one-line justification ("Dustin's public resume content — intentional worked example"). This is the document that makes "worked-example data" auditable and distinguishable from a leak.

- [ ] **Step 4: Commit**

```bash
git add docs/CONTAMINATION-MAP.md
git commit -m "docs: contamination map — every retained personal string is accounted for"
```

### Task 9.2: Sample applications + README + CLAUDE.md

**Files:**
- Create: `applications/_examples/` (1–2 sanitized real apps)
- Create: `docs/README.md`
- Create: `CLAUDE.md`

- [ ] **Step 1: Copy 1–2 example applications, sanitized**

Pick 1–2 of Dustin's strongest applications from the source repo. Copy only `resume.md`, `cover-sheet.md`, `index.md`, `job-posting.md` into `applications/_examples/<name>/`. Run the sanitizer over them. Do NOT copy `SUBMITTED.md`, tracker rows, or any DES/case material.

- [ ] **Step 2: Write `docs/README.md`**

Quickstart for a generic user: prerequisites (Python, LibreOffice), "Use this template" → clone → `pip install -r requirements.txt` → open in Claude Code → `/onboard`. Explain the three data layers, the gate philosophy, and `/s`. Link the spec and CONTAMINATION-MAP.

- [ ] **Step 3: Write `CLAUDE.md`**

A generic-user version of the project instructions: what the repo is, the trigger skills (`/onboard`, `/s`, `/job-hunt-architect`, `/filter-forecaster`), the template-awareness rule, the evidence-gate doctrine. Strip all Dustin-specific operational sections (NC DES weekly certs, application-locking-by-tag, the Stop hook) unless the user wants them — note they are optional add-ons.

- [ ] **Step 4: Final full-suite run + commit**

Run: `pytest -v`
Expected: all green.
```bash
git add applications/_examples docs/README.md CLAUDE.md
git commit -m "docs: README, generic CLAUDE.md, and sanitized example applications"
```

### Task 9.3: Publish as a GitHub template repo

- [ ] **Step 1: Create the remote and push**

Run:
```bash
gh repo create Dwink213/resume-architect --public --source . --remote origin --push
```
Expected: repo created, initial history pushed.

- [ ] **Step 2: Mark it a template repo**

Run: `gh repo edit Dwink213/resume-architect --template`
Expected: "Use this template" button appears on GitHub.

- [ ] **Step 3: Final manual verification (the colleague's path)**

Per the `superpowers:verification-before-completion` skill: clone the template fresh into a scratch dir, copy `profile.example-jane.yaml` → `profile.yaml`, point `generate-resume.py` at `tests/fixtures/sample-jd.md`, and confirm a Jane resume renders and lints clean — proving a fresh clone works for someone who is not Dustin.

---

## Self-Review (completed against the spec)

- **Spec coverage:** repo structure (Phase 0/9), profile.yaml schema (Phase 1), resume-lint split (Phase 3), /onboard with resume-on-restart + starter manifest (Phase 6), /s add-source (Phase 7), template-repo distribution + employer-sanitizer + CONTAMINATION-MAP (Phase 9), Jane-fixture smoke test (Phase 1/2/8). All spec sections map to tasks. **Gap found and added during review:** the spec did not anticipate the hardcoded `generate_summary()` templates or the company-name `build_resume` lookups — Phase 2 now covers both (the genericization that "edit to read profile.yaml" undersold). The cover-sheet gate's forced-Dustin-artifacts coupling was also not in the spec — added as Task 4.3.
- **Placeholder scan:** no TBD/TODO; every code step shows complete code; skill tasks specify full contracts.
- **Type consistency:** `load_profile()`, `merge_overrides(cfg, profile)`, `_render_experience_entry(entry, role_tags, jd_terms)`, and `source["_profile"]` are used consistently across Phases 1-8.
