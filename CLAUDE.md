# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

`resume-architect` is an evidence-gated resume + cover-sheet engine you drive from inside Claude Code.
You describe a job; the engine assembles a tailored, ATS-safe resume and cover sheet **from the user's
own real artifacts**, scores them, and refuses to ship any claim that can't be traced back to evidence.

The repo ships pre-populated with one real user's data as a worked example. A new user runs `/onboard`
to overwrite it with their own. See `docs/CONTAMINATION-MAP.md` for what is worked-example data and why
none of it is a leak, and `docs/README.md` for the user-facing quickstart.

## The three data layers

Everything the engine knows about the user lives in exactly three places:

1. **`profile.yaml`** — identity, contact, taglines, portfolio links, cover-sheet boilerplate, gate
   overrides. The one file that makes the engine "you." `profile.example-jane.yaml` is a leak-free
   reference. The engine, the skills, and the gates all read this.
2. **`tools/resume-source.yaml`** — the career skeleton: experience, skills, education, headline projects.
3. **The testimony KB** (`tools/knowledge/testimonies/*.yaml`) — one YAML per shipped project / deployment
   / talk, carrying metrics, verifiable claims, proof, and pre-written bullet variants. **This is the
   source of truth for every claim in every resume.**

Never invent career facts. If a claim isn't in these three layers, it does not go in a document.

## Trigger skills

| Skill | Invoke | Role |
|---|---|---|
| `/onboard` | first run | Interviews a new user, writes all three data layers, proves the engine works against a sample JD. Resumes mid-flight if interrupted. |
| `/s` (`/add-source`) | after shipping something | Interviews the user about ONE project, writes one evidence-gated testimony YAML. Grows the KB only — never touches `profile.yaml` or experience. |
| `/job-hunt-architect` | per job posting | Reads the manifest routing table + a JD, assembles AI-first tailored docs, scores them, runs a brutal critic, writes a provenance `index.md`. |
| `/filter-forecaster` | after each resume generation, before submitting | Reverse-engineers the ATS + AI-screener + human-recruiter pipeline for a specific application and forecasts pass/fail with fix recommendations. |

## Evidence-gate doctrine — MANDATORY

The defining rule of this repo: **if it isn't evidenced, it doesn't ship.**

- `tools/check-resume.py` runs automatically during `generate-resume.py`. It cross-checks every claim
  against the testimony KB and **blocks** anything that can't be traced to a testimony with stated proof.
- The cover sheet has its own gate.
- Under pressure to keyword-stuff, the correct move is to **drop** the unevidenced keyword, not fake it.
  A keyword with no backing testimony is a liability, not an asset.

Do not weaken, bypass, or `--force` past a content gate to make a document "look better." If a claim is
real but the gate blocks it, the fix is to add the evidence via `/s`, not to silence the gate.

## Template awareness — MANDATORY

Repeatable outputs come from templates in `templates/`, not from memory.

- Before writing a per-application document for the first time, check whether a master template exists in
  `templates/` and use it.
- If you are about to write a document that looks like it could be generated from a master template but
  no template exists yet, **say so before writing it** — one sentence: "This type of document doesn't
  have a master template yet — want me to create one before I write this instance?"
- Master templates are authoritative; per-application copies are disposable and regenerable.

## Folder conventions

- Per-application folders hold `job-posting.md`, `resume.md`, `cover-sheet.md`, `index.md` (provenance),
  and an `exports/` folder for rendered `.docx` / `.html` / `.pdf`.
- `applications/_examples/` holds the shipped worked-example applications — these are intentionally
  committed and are safe to read as reference.

## Document export pipeline

After generating or regenerating any document, ensure the `exports/` folder has the rendered artifacts:

| File | How produced |
|---|---|
| `resume.docx` | `generate-resume.py` → `render-docx.py` (auto) |
| `resume.html` | `generate-resume.py` → `docx-to-html.py` (auto) |
| `resume.pdf` | `generate-resume.py` → LibreOffice headless (auto) |
| `cover-sheet.docx` | `/job-hunt-architect` |

LibreOffice is required for PDF rendering. Use `tools/render-pdf.py` — never invoke `soffice` directly;
the script handles the headless-mode flags. After any cover-sheet `.docx` is generated, run
`python tools/render-pdf.py --docx <path-to-cover-sheet.docx>`.

## Tests

`pytest -v` must stay green. The suite includes `tests/test_smoke_jane.py`, which builds a resume from the
leak-free Jane profile and asserts the output contains **none** of the worked-example user's tokens —
proving the engine carries no seeded personal data into a fresh user's output. Run the suite before
committing any change to the engine or gates.

## Optional add-ons (not enabled by default)

The original author runs additional automation on top of this engine. These are **opt-in** and are not
part of the generic template — enable them only if the user asks:

- **Single-source tracker** — a `TRACKER.md` as the one place application status lives, with a defined
  status lifecycle (DRAFT → APPLIED → … → OFFER/REJECTED).
- **Application locking by git tag** — on submission, freeze the exports and `git tag` the as-submitted
  state as the immutable record, with a drift gate that fails if a locked folder no longer byte-matches
  its tag.
- **Stop hook verification** — a `.claude/settings.json` Stop hook that runs verification on every session
  end.
- **Weekly unemployment / job-search certification** workflow (jurisdiction-specific).

If the user wants any of these, treat it as a feature to design with them — do not assume the
author's specific policies.
