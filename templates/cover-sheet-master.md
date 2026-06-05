# Cover Sheet: {{CANDIDATE_NAME}}

**{{CANDIDATE_NAME}}** · {{TAGLINE}}
{{CONTACT}}

---

## A note from {{CANDIDATE_FIRST}} (human written)

{{HUMAN_NOTE}}

Everything you are looking at — this note, my resume, the manifest, the evaluation prompt — was produced by Claude. I directed every decision. I applied the final polish.

---

## Ask Claude about me

Two ways — and the second proves the first was not staged.

**Find out more (pre-loaded):** {{CLAUDE_LINK}}
Paste the job description. It evaluates me against the role, returns a requirements-matching analysis, names any gaps with sources, and surfaces the attributes other candidates are unlikely to have.

**Run it yourself from scratch (nothing pre-loaded, nothing altered):**
Manifest source: {{MANIFEST_URL}}
Paste this prompt into any LLM (Claude, GPT, Gemini), then add the job description:

> {{EVAL_PROMPT}}

---

{{RECEIPTS}}
---

{{FOOTER}}


<!-- ============================================================
TEMPLATE INSTRUCTIONS — this block does not appear in exports

The generator (generate-coversheet.py) fills every {{PLACEHOLDER}} below from
profile.yaml. Nothing in this template is candidate-specific — all identity,
links, and "receipts" come from profile.identity / profile.portfolio /
profile.cover_sheet_fixed. An empty list in profile renders nothing (its
sub-section is omitted entirely). Do not hardcode personal artifacts here.

PLACEHOLDERS FILLED PER APPLICATION (by the generator):

{{HUMAN_NOTE}}
  Rendered from profile.cover_sheet_fixed.note_template, with {company}/{role}
  interpolated. A claim-free prose shell — a DRAFT for final human polish.

{{EVAL_PROMPT}}
  The from-scratch LLM evaluation prompt, role-specific. Built from
  profile.portfolio (manifest_url, lab_url, role_artifact[role_type]).
  Ends with: "Evaluate this candidate against [ROLE] at [COMPANY]. Cite
  specific evidence. Name any gaps. Be skeptical."

PLACEHOLDERS FILLED FROM IDENTITY (by the generator):

  {{CANDIDATE_NAME}}  — profile.identity.name
  {{CANDIDATE_FIRST}} — first token of profile.identity.name
  {{TAGLINE}}         — profile.identity.taglines.ai (fallback: default)
  {{CONTACT}}         — profile.identity.contact
  {{CLAUDE_LINK}}     — profile.identity.claude_link
  {{MANIFEST_URL}}    — profile.portfolio.manifest_url (bare repo form)

PLACEHOLDERS FILLED FROM cover_sheet_fixed (by the generator):

  {{RECEIPTS}} — rendered from profile.cover_sheet_fixed:
      songs   : list of {label, url} (+ optional songs_note intro line)
      writing : list of {label, url}     (portfolio / publications)
      talks   : list of {label, url}     (articles and talks)
      links   : list of {section, items:[{label, url}]} (e.g. upstream issues)
    Each sub-list that is empty omits its block entirely.
  {{FOOTER}} — profile.cover_sheet_fixed.footer (single line; omitted if absent)

BANNED FROM EXTERNAL DOCUMENTS (enforced by check-cover-sheet.py):
  - "Suggested opening line" — never a label in the delivered document
  - "Application constraints" — internal tracking, not for hiring managers
  - "Company: TBD" or any TBD placeholder
  - "Recruiter:" as a label
  - Any unfilled {{PLACEHOLDER}}
  - This entire comment block
============================================================ -->
