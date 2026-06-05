# resume-architect

An evidence-gated resume + cover-sheet engine you drive from inside Claude Code. You describe a job,
the engine assembles a tailored, ATS-safe resume and cover sheet **from your own real artifacts** —
and a content gate refuses to ship any claim it can't trace back to a piece of evidence you provided.

It ships pre-populated with one real user's data (Dustin Winkler) as a worked example so you can see a
fully-loaded engine before you make it yours. The `/onboard` wizard then overwrites that data with
yours. See [`CONTAMINATION-MAP.md`](CONTAMINATION-MAP.md) for exactly which strings are worked-example
placeholders and why none of them are a leak.

---

## Prerequisites

1. **Python 3.10+** — the generators, gates, and tests.
2. **LibreOffice** — headless `.docx → .pdf` rendering. Install from
   [libreoffice.org](https://www.libreoffice.org/). On Windows it lands at
   `C:\Program Files\LibreOffice\program\soffice.exe`.
3. **Claude Code** — the skills (`/onboard`, `/s`, `/job-hunt-architect`, `/filter-forecaster`) run here.

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
   It interviews you and writes your three data layers (below), then proves the engine works by
   rendering a sample resume against a test job description. If you get interrupted, run `/onboard`
   again — it resumes mid-flight.

Prefer to inspect before onboarding? Copy the leak-free reference profile and render a sample:
```bash
cp profile.example-jane.yaml profile.yaml
python tools/generate-resume.py --jd tests/fixtures/sample-jd.md
```

---

## The three data layers

Everything the engine knows about you lives in exactly three places. `/onboard` writes all three; you
edit them by hand or grow them with `/s` afterward.

1. **`profile.yaml`** — *who you are.* Name, contact, taglines, portfolio links, cover-sheet boilerplate,
   gate overrides. The one file that makes the engine "you." Read by the engine, the skills, and the
   gates. `profile.example-jane.yaml` is a complete leak-free example.

2. **`tools/resume-source.yaml`** — *your career skeleton.* Your experience entries, skills, education,
   and the headline projects. This is the structural source the resume is built from.

3. **The testimony KB** — *your evidence.* One YAML per shipped project / deployment / talk in
   `tools/knowledge/testimonies/`, each carrying metrics, verifiable claims, proof, and pre-written
   bullet variants. This is the source of truth for **every claim in every resume.** Grow it one project
   at a time with `/s` (see below).

## The evidence-gate philosophy

The engine will not let you make a claim you can't back up. When `generate-resume.py` selects bullets, a
content gate (`tools/check-resume.py`) cross-checks every claim against the testimony KB and **blocks**
anything that can't be traced to a testimony with stated proof. The cover-sheet has its own gate. The
doctrine is simple: **if it isn't evidenced, it doesn't ship.** This is what keeps a tailored resume
honest under the pressure to keyword-stuff — keywords without evidence get dropped, not faked.

## `/s` — grow your evidence base

`/s` (alias `/add-source`) interviews you about a single shipped project, writes one new testimony YAML
to `tools/knowledge/testimonies/`, and evidence-gates every claim **before** saving it. It only grows the
KB — it never touches `profile.yaml` or your experience. Run it whenever you ship something new, so your
next resume can draw on it. Once is a script; capture it while it's fresh.

## The skills

| Skill | What it does |
|---|---|
| `/onboard` | First-run wizard — writes your three data layers and proves the engine works. |
| `/s` (`/add-source`) | Add one evidence-gated testimony to the KB. |
| `/job-hunt-architect` | Given a JD, assembles the tailored resume + cover sheet, scores them, runs a brutal critic, and writes a provenance `index.md`. |
| `/filter-forecaster` | Reverse-engineers the ATS + AI-screener + human-recruiter pipeline a specific application will hit, and forecasts pass/fail with fix recommendations. |

## Worked examples

`applications/_examples/` contains two real, strong applications rendered by this engine — a Palantir
Forward-Deployed AI Engineer application and an Anthropic Technical Enablement Lead application. Each
includes `resume.md`, `cover-sheet.md`, the provenance `index.md`, and the `job-posting.md` it was
tailored against. Read them to see what the engine produces end to end.

## Reference

- Design / implementation spec: [`../IMPLEMENTATION-PLAN.md`](../IMPLEMENTATION-PLAN.md)
- Worked-example data inventory: [`CONTAMINATION-MAP.md`](CONTAMINATION-MAP.md)
- Leak-free reference profile: [`../profile.example-jane.yaml`](../profile.example-jane.yaml)
