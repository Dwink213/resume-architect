# CONTAMINATION-MAP

**Purpose.** This repo ships as a public GitHub template, but it is seeded with *one real person's* data
(Dustin Winkler) as a worked example so a new user can see a fully-populated engine before they run
`/onboard` and overwrite it with their own. That means the repo intentionally contains personal,
identifying strings. This document inventories every retained personal/identifying string, with
`file:line` and a one-line justification, so that **worked-example data is auditable and clearly
distinguishable from a leak.**

**Audit date:** 2026-06-05
**Audit method:** Grep over the entire repo for `example | user@ | @example | Enterprise Health-Tech Co.`,
the enterprise email domain, plausible internal product/codenames
(`redacted-product | redacted-product | redacted-product | redacted-product | redacted-product`), and employee usernames.

## Leak definition (what must NEVER ship)

- The W-2 employer's **enterprise email domain** (e.g. `example.com`, `user@exampletech.com`)
- **Internal product names / codenames** not on the public record
- **Employee usernames** / internal handles
- Any private DES/unemployment-case material, `SUBMITTED.md`, tracker rows, or `exports/`

## Audit result

**No leaks found.** Zero hits for the enterprise email domain, internal product/codenames, or employee
usernames anywhere in the repo. Nothing was removed because nothing leaked. Every personal string that
remains is intentional public-record worked-example content, inventoried below.

---

## Retained personal strings — intentional worked examples

### 1. Identity: name, public contact, portfolio handles

| String | Representative location | Justification |
|---|---|---|
| `Dustin Winkler` | `profile.yaml:5`; `tools/resume-source.yaml:6`; example resumes | Worked-example user identity. Public on his resume/LinkedIn/GitHub. Replaced wholesale by `/onboard`. |
| `dustin@awacs.ai` | `profile.yaml:10`; `tools/resume-source.yaml:10` | Public business email (his own company AWACS). Not an enterprise/W-2 domain. |
| `awacs.ai`, `github.com/Dwink213`, `linkedin.com/in/dustin-winkler-nc` | `profile.yaml:6,10,14–24`; testimonies; `templates/` | Public portfolio/social URLs. Intentional — they are the artifacts the engine showcases. |
| `claude.ai/share/...` workspace link | `profile.yaml:7` | Public shared Claude workspace. Intentional portfolio artifact. |

### 2. Employer line: "Enterprise Health-Tech Co."

| Location | Justification |
|---|---|
| `tools/resume-source.yaml:143` (`company: "Enterprise Health-Tech Co."`) | The employer line on Dustin's **public** resume. Intentional worked example — exactly the data `/onboard` overwrites for a new user. NOT a leak: company name on a public resume is public record. |
| `tools/knowledge/index.yaml:46,55,64,73` (`employer:` fields) | Testimony provenance pointing at the same public employer. Worked example. |
| `tools/knowledge/testimonies/*.yaml` (`employer:` + `proof:` lines) | Same — public employer attribution on worked-example testimonies. The testimony *content* describes only generic technical work (WDAC, Azure, Rubrik/ServiceNow third-party tools); no internal product names. |
| `applications/_examples/*/resume.md` (experience header) | Rendered worked-example resumes; carry the same public employer line. |
| `tools/knowledge/schema.yaml:12` | A comment giving `employer` field examples. Documentation worked example. |
| `tests/test_smoke_jane.py:34`; `IMPLEMENTATION-PLAN.md` (multiple) | "Enterprise Health-Tech Co." used as a **forbidden-token guard** in the Jane smoke test and described in the plan — i.e. the test that *proves* a fresh non-Dustin clone produces zero Dustin/employer leakage. Intentional and protective, not a leak. |

> Note on the worked example vs. leak distinction for "Enterprise Health-Tech Co.": the **company name** is on
> Dustin's public resume and is therefore worked-example data. The **leak** concern was always the
> enterprise *email domain*, internal *product/codenames*, and *usernames* — none of which appear
> anywhere in this repo.

### 3. Public portfolio artifacts referenced throughout

| String(s) | Locations | Justification |
|---|---|---|
| `github.com/Dwink213/manifest`, `/api-observability-framework`, `/AI-supplychainmonitor-v2` | `profile.yaml`, testimonies, example index.md | Public GitHub repos. Intentional portfolio links. |
| `awacs.ai/case-studies/...`, `awacs.ai/methodology`, `awacs.ai/lab`, `awacs.ai/talks/...` | `profile.yaml`, testimonies, templates | Public case studies / methodology pages. Intentional. |
| `suno.com/s/...`, `awacsai.gumroad.com`, `notebooklm.google.com`, `linkedin.com/pulse/...` | `profile.yaml` cover-sheet block | Public published songs/eBook/notebook/articles. Intentional portfolio. |
| Upstream issue refs `#44707 / #57946 / #44711` | `profile.yaml`, testimonies | Public `anthropics/claude-code` GitHub issues filed under his account. Intentional. |

### 4. Example applications

| Path | Justification |
|---|---|
| `applications/_examples/Palantir_Forward-Deployed-AI-Engineer/` | Real, strong application (FDE). Only `resume.md`, `cover-sheet.md`, `index.md`, `job-posting.md` copied. NO `SUBMITTED.md`, NO `exports/`, NO private notes. Re-audited: clean (only the public "Enterprise Health-Tech Co." employer line). |
| `applications/_examples/Anthropic_Technical-Enablement-Lead-Claude-Code/` | Real, strong application (Technical Enablement). Same four-file subset, same exclusions. Re-audited: clean. |

---

## Replaceability guarantee

Every string in this map is overwritten when a new user runs `/onboard`, which rewrites `profile.yaml`,
`resume-source.yaml`, and the testimony KB from scratch. `profile.example-jane.yaml` is the leak-free
reference a new user can diff against. The `tests/test_smoke_jane.py` guard asserts that a Jane-profile
build emits **none** of these worked-example tokens — proving the engine carries no Dustin data into a
fresh user's output.
