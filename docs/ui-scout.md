# UI Scout Runs

Internal product-truth scouting log for CineForge's own surfaced UI.

This lane is intentionally separate from `docs/scout/`, which is reserved for
external-source research. Use this lane when the work is: "walk the shipped
product like a real operator, record where the surfaced path feels excellent,
and record where it does not."

Companion runbook: `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`

Machine-readable freshness source: `docs/methodology/state.yaml` `ui_scout`

## Canonical Scenario Coverage

| Scenario | Goal | Last Checked | Notes |
|---|---|---|---|
| FP1 — Full Pipeline Canonical Fixture | A fresh project on the canonical short screenplay should reach the current honest downstream boundary through surfaced navigation and still feel polished, obvious, and honest | 2026-04-10 | Latest rerun passed. Story 157's completed-path CTA honesty fix remains verified, and Story 158 removed the fresh-run `/api/runs/{id}/events` startup noise plus the stale fresh-import `Upload Screenplay` CTA regression on the surfaced Home path. |

## Run Index

| Date | Scenario | Project | Follow-Up | Status |
|---|---|---|---|---|
| [2026-04-10 local validation](ui-scout/2026-04-10-open-frequency-local-validation.md) | FP1 | `open-frequency-3` | — | Pass |
| [2026-04-10 local recheck](ui-scout/2026-04-10-open-frequency-local-recheck.md) | FP1 | `open-frequency` | [158](stories/story-158-fresh-run-event-polling-stops-racing-missing-event-logs.md) | Issues Found |
| [2026-04-10 local walkthrough](ui-scout/2026-04-10-open-frequency-local.md) | FP1 | `open-frequency` | [157](stories/story-157-chat-suggestions-stop-advertising-completed-paths.md) | Recheck Due |

## Operating Notes

- Keep this markdown lane and `state.ui_scout` in sync on every run so the
  compiled graph can flag stale or awaiting-recheck coverage automatically.
- Keep CineForge on one canonical scenario until repeated real use proves that a
  second scenario is needed. Do not invent taxonomy for its own sake.
- If a run finds a product defect, keep the failed report and link the focused
  follow-up story instead of rewriting history into a green-only log.
