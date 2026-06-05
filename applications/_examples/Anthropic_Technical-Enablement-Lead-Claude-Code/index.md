# index.md — Anthropic / Technical Enablement Lead, Claude Code

**Generated:** 2026-05-30
**Manifest commit:** 336202a
**JD source:** job-posting.md
**Role type:** Developer Relations / Technical Enablement → mapped to `tech_lead_manager` generator profile (the generator has no dedicated dev-rel type; tech_lead_manager's demos/player-coach/communication tags are the honest closest fit). Manifest reverse-map primary attributes for this role: **D4 Technical Writing · Show Don't Tell · Compounding Artifacts · Receipts Culture · B2 Methodology as Product.**

## Files in this folder
| File | Source | Why |
|------|--------|-----|
| resume.md | Dwink213/manifest + generate-resume.py (role_type=tech_lead_manager) | Teaching-first framing; featured project = AI Enablement Sessions (200+ attendees) |
| cover-sheet.md | Manifest cover-letter template | 4-line prompt + "Claude Code as core infrastructure" framing; names GTM gap + travel |
| filter-forecast.md | /filter-forecaster (Phase 4.5) | Greenhouse ATS + keyword scan + values round; pass-through 80/100, 0 HARD knockouts |
| exports/dustin-winkler-resume.docx | render-docx.py | ATS-safe single-column upload artifact |
| exports/dustin-winkler-resume.html | docx-to-html.py | Office-free human preview |
| job-posting.md | Greenhouse API (verified live 2026-05-30) | Original JD |
| notes.md | Template scaffold | Contact log, status history |

## Attributes activated
- **D4 Technical Writing for Varied Audiences** — SVP→engineer enablement; public talks to 250+ live audiences
- **B2 Methodology as Product** — five public frameworks (awacs.ai/methodology) = demo-able working models, not slideware
- **Show Don't Tell / Compounding Artifacts / Receipts Culture** — the methodology page + KB are the proof
- **A3 Self-Monitoring (via upstream Claude Code hooks)** — "uses Claude Code as core infrastructure, not a novelty"

## Artifacts selected
1. AI Enablement Sessions (KB testimony) — satisfies: "deliver Claude Code training / live technical training track record"
2. anthropics/claude-code contributions (#44707/#57946/#37550) — satisfies: "uses AI coding tools as core infrastructure" (deepest possible proof: found bugs in the hook system)
3. Methodology page / five frameworks (awacs.ai/methodology) — satisfies: "create and maintain training content"

## Score at generation
| Metric | Value |
|--------|-------|
| Filter-forecast pass-through | 80/100 (heuristic) |
| HARD knockouts failed | 0 — degree line is "Bachelor's **or equivalent combination**", so NOT a knockout |
| Keyword match | 55% → **80%** (16/20 top-20) after one fix-loop; remaining misses all boilerplate (location/travel/greenhouse/seattle) |
| MET qualifications | 4 (7+ yrs technical, ships real code, Claude Code as core infra, live training/talks) |
| PARTIAL qualifications | 2 (content-creation-at-volume signal; location/travel vs hub preference) |
| NOT MET qualifications | 1 (formal GTM / sales-enablement partnership — battlecards/competitive positioning) |
| Critic score | 5.5/10 |
| Critic flags | talks/frameworks buried; zero GTM/sales-enablement vocabulary; content-creation artifacts not surfaced; education line framing; Claude Code contributions undersold — **RESOLVED via fix-loop:** talks now in top third, Claude Code expanded to "bugs in its own hook system," GTM/curriculum tokens seeded. Remaining (not resume-fixable): actual sales-enablement experience; location/travel |

## Honest assessment
This is the highest role-FIT in the pipeline (engineer-who-teaches + Claude Code depth) but the resume currently **under-sells** its two best cards: the public talks (buried) and the upstream Claude Code contributions (one terse line). Both critic and forecaster independently flag the same fix: surface the talks/frameworks into the top third and expand the Claude Code contributions into a named block. The role's degree gate is open ("or equivalent"). Real gaps are GTM/sales-enablement experience and location/travel — both named honestly in the cover-sheet. **Recommended before submit:** add a `talks`/`content` entry to resume-source.yaml and regenerate (one fix loop) — pending user approval since it edits the shared source file.
