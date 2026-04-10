# Full-Pipeline UI Acceptance Reports

This folder is the recurring reporting home for Story 156 and `spec:5.6`.
Each file records one real product-truth walkthrough on the canonical short
screenplay fixture or its future replacement.

## Naming

- Use one markdown file per run
- Filename pattern: `YYYY-MM-DD-<project>-<env>.md`
- Example: `2026-04-10-open-frequency-local.md`

## Required Fields

Every report must capture:

- Date and operator
- Fixture path and whether the project was created fresh
- Environment, commit, and surfaced app endpoints used
- Exact surfaced routes and actions walked
- Honest current boundary reached
- Functional result, UX/trust result, and overall pass/fail call
- Console/page-error status for desktop and mobile checks
- Follow-up stories created or linked from discovered defects
- Screenshot or equivalent evidence summary

## Rules

- Report only what the normal surfaced UI proved. Do not count `/run`, raw
  artifact pages, or impossible seeded project states as acceptance evidence.
- If the honest boundary changes, update
  `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` in the same diff as
  the report that discovered the change.
- Prefer written route/result evidence over checked-in image binaries unless a
  screenshot is the only clear way to preserve the finding.
- If a run fails, keep the failed report. The point of this lane is durable
  truth, not only green runs.
