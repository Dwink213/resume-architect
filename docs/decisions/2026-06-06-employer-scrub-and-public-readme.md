**Decision:** Scrub the recent W-2 employer's real name from the entire public repo, replacing it with
the generic placeholder "Enterprise Health-Tech Co."; keep the candidate's own name;
replace the detailed CONTAMINATION-MAP with a generic, name-free worked-example note; and add a root
README.md as the public landing page.

**Why:** User (away) said: "This is supposed to not be showing anything related to my old employer ...
this is too much information about my old employer for me to make this publicly. ... This would be
something that could be productized or a portfolio piece. I don't really care [about my name being in
it]." The recent W-2 employer's testimony `proof:` lines named specific internal deployments ("still
running", "CI/CD pipeline logs") — too much detail tied to a named recent employer for a public artifact.
The candidate's own name is acceptable to them and makes it a credible portfolio piece.

**Alternatives considered:**
- Keep the employer name as "public record" (the repo's original doctrine) — rejected; user explicitly
  wants it gone for public publishing.
- Scrub ALL past employers (National Cloud Provider, Raleigh/County 911, Federal Proposal Consultancy) — deferred; these are
  decade-old / public-sector / side work, standard résumé history with no IP risk, and erasing them
  removes genuine portfolio substance. Flagged to user for a later call.
- Rewrite git history (filter-repo + force push) to remove the name from prior commits — deferred;
  destructive and irreversible, requires explicit approval. Left to the user with the exact command.

**Audit result before scrub:** Zero hits for the enterprise email domain, product names, username, or
commit-metadata emails (all commits = dustin@awacs.ai). The company *name* was the only employer trace.

**Verification:** `pytest -v` green (12/12); end-to-end generation against a generic JD produced clean
`resume.md` + `.docx` (zero "Align", placeholder present); content gate executed and passed.

**Date:** 2026-06-06
