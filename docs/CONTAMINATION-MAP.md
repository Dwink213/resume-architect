# Worked-Example Data — what's seeded and why it's safe to publish

This repo ships as a public template, pre-populated with **worked-example data** so a new user can see a
fully-loaded engine before they make it their own. This note explains what that seeded data is, what is
deliberately kept out, and how it all gets replaced.

## What's seeded

- A complete `profile.yaml`, `tools/resume-source.yaml`, and a testimony KB
  (`tools/knowledge/testimonies/*.yaml`) for one example candidate.
- Two rendered example applications under `applications/_examples/`.

All of it is **public-record portfolio content** (the kind of thing already on a public résumé,
LinkedIn, or GitHub). Employer names in the worked example are generic placeholders
(e.g. `Enterprise Health-Tech Co.`), not a real current/former employer's identity.

## What must NEVER ship (leak definition)

The following are treated as leaks and are kept out of the repo entirely:

- A real W-2 employer's **enterprise email domain** or `<user>@<employer-domain>` address.
- **Internal product names / codenames** not on the public record.
- **Employee usernames** / internal handles.
- Any private case material, `SUBMITTED.md`, tracker rows, or `exports/` from real submissions.

Commit metadata (author/committer email) is also kept to a public address — enterprise emails baked into
git history are the most common leak vector, and there are none here.

## Everything is replaceable

Running `/onboard` rewrites all three data layers (`profile.yaml`, `resume-source.yaml`, and the
testimony KB) from scratch with the new user's own data. `profile.example-jane.yaml` is a leak-free
reference profile you can diff against.

The `tests/test_smoke_jane.py` guard builds a résumé from the leak-free Jane profile and asserts the
output contains **none** of the worked-example candidate's tokens — proving the engine carries no seeded
personal data into a fresh user's output.
