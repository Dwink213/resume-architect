# resume-architect

**An evidence-gated resume + cover-sheet engine you drive from inside [Claude Code](https://claude.com/claude-code).**

You describe a job. The engine assembles a tailored, ATS-safe resume and cover sheet **from your own
real artifacts**, scores them against the posting, and refuses to ship any claim it can't trace back to a
piece of evidence you provided. The guiding rule: **if it isn't evidenced, it doesn't ship.**

The repo ships pre-populated with worked-example data so you can see a fully-loaded engine before you make
it yours. `/onboard` then overwrites that data with your own. See
[`docs/CONTAMINATION-MAP.md`](docs/CONTAMINATION-MAP.md) for what's seeded and why it's safe to publish.

---

## Prerequisites

1. **Python 3.10+** — runs the generators, gates, and tests.
2. **[Claude Code](https://claude.com/claude-code)** — the skills (`/onboard`, `/s`, `/job-hunt-architect`, `/filter-forecaster`) run here.
3. **[LibreOffice](https://www.libreoffice.org/)** — headless `.docx → .pdf` rendering. Only needed when you render PDFs; tests don't need it.

---

## Quickstart

1. On GitHub, click **Use this template** to create your own copy, then clone it:
   ```bash
   git clone https://github.com/<you>/<your-resume-architect>.git
   cd <your-resume-architect>
   ```
2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Open the folder in Claude Code and run the onboarding wizard:
   ```
   /onboard
   ```

Want to inspect the engine before onboarding? Render a sample from the leak-free reference profile:
```bash
cp profile.example-jane.yaml profile.yaml
python tools/generate-resume.py --jd tests/fixtures/sample-jd.md --dry-run
```

---

## How to onboard

`/onboard` is the first-run wizard. It interviews you and writes your **three data layers** (below), then
proves the engine works by rendering a sample resume against a test job description. It's interruptible —
if you stop partway, run `/onboard` again and it resumes mid-flight.

By the end of onboarding you have:

- **`profile.yaml`** — *who you are.* Name, contact, taglines, portfolio links, cover-sheet boilerplate,
  gate overrides. The one file that makes the engine "you."
- **`tools/resume-source.yaml`** — *your career skeleton.* Experience, skills, education, headline projects.
- **The testimony KB** (`tools/knowledge/testimonies/*.yaml`) — *your evidence.* One YAML per shipped
  project / deployment / talk, carrying metrics, verifiable claims, proof, and pre-written bullet
  variants. **This is the source of truth for every claim in every resume.**

> The engine never invents career facts. If a claim isn't in these three layers, it does not go in a
> document. That's what keeps a tailored resume honest under pressure to keyword-stuff — an unevidenced
> keyword gets dropped, not faked.

---

## What happens after you onboard

Onboarding is a one-time setup. After that, you live in two loops:

### 1. Grow your evidence base — `/s` (alias `/add-source`)

Every time you ship something real (a project, deployment, talk), run `/s`. It interviews you about that
**one** thing, evidence-gates every claim, and writes a single new testimony YAML to the KB. It only
grows the KB — it never touches `profile.yaml` or your experience. Capture it while it's fresh; your next
resume can then draw on it.

### 2. Apply to a job — `/job-hunt-architect`

For each posting, run `/job-hunt-architect` with the job description. It:

1. Reads the manifest routing table + the JD and detects the role type.
2. Assembles an AI-first tailored **resume** and **cover sheet** from your three data layers.
3. Runs the **content gate** (`tools/check-resume.py`) — blocks any claim not traceable to a testimony.
4. Scores ATS keyword density and runs a brutal critic pass.
5. Writes a provenance `index.md` recording where every claim came from.
6. Renders `exports/` artifacts: `.docx` (ATS-safe), `.html` (viewable), `.pdf` (LibreOffice).

### 3. Pressure-test before submitting — `/filter-forecaster`

After generating, run `/filter-forecaster`. It reverse-engineers the screening pipeline the application
will actually hit — ATS parser, AI screener, human recruiter — and forecasts pass/fail with specific fix
recommendations. Fix, regenerate, then submit.

---

## The skills

| Skill | When | What it does |
|---|---|---|
| `/onboard` | First run | Writes your three data layers and proves the engine works against a sample JD. |
| `/s` (`/add-source`) | After shipping something | Adds one evidence-gated testimony to the KB. |
| `/job-hunt-architect` | Per job posting | Assembles the tailored resume + cover sheet, gates and scores them, writes provenance. |
| `/filter-forecaster` | Before submitting | Forecasts whether the application clears ATS + AI + human screening. |

---

## Doing it by hand (without the skills)

The skills wrap a set of Python tools you can also call directly:

```bash
# Generate a resume for one application (writes resume.md + renders exports/)
python tools/generate-resume.py --jd applications/<folder>/job-posting.md

# Search your evidence KB without generating anything
python tools/generate-resume.py --search-kb "azure cost finops"

# Run the content gate by hand
python tools/check-resume.py --resume applications/<folder>/resume.md

# Render a PDF from a .docx (never call soffice directly)
python tools/render-pdf.py --docx <path-to.docx>
```

Useful flags on `generate-resume.py`: `--dry-run` (print, write nothing), `--no-pdf` (skip the PDF step),
`--role-type <type>` (override auto-detection). A folder containing a `SUBMITTED.md` is locked — the
generator refuses to overwrite it without `--force-locked`.

---

## Worked examples

[`applications/_examples/`](applications/_examples/) contains two real, strong applications rendered by
this engine — a Palantir Forward-Deployed AI Engineer application and an Anthropic Technical Enablement
Lead application. Each includes `resume.md`, `cover-sheet.md`, the provenance `index.md`, and the
`job-posting.md` it was tailored against. Read them to see what the engine produces end to end.

---

## Tests

```bash
pytest -v
```

The suite must stay green before committing any change to the engine or gates. It includes
`tests/test_smoke_jane.py`, which builds a resume from the leak-free Jane profile and asserts the output
contains **none** of the worked-example candidate's tokens — proving the engine carries no seeded
personal data into a fresh user's output.

---

## Reference

- Extended guide: [`docs/README.md`](docs/README.md)
- Guidance for Claude Code in this repo: [`CLAUDE.md`](CLAUDE.md)
- Worked-example data, and why it's safe to publish: [`docs/CONTAMINATION-MAP.md`](docs/CONTAMINATION-MAP.md)
- Leak-free reference profile: [`profile.example-jane.yaml`](profile.example-jane.yaml)
