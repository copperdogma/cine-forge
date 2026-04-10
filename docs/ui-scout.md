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
| FP1 — Full Pipeline Canonical Fixture | A fresh project on the canonical short screenplay should reach the current honest downstream boundary through surfaced navigation and still feel polished, obvious, and honest | 2026-04-10 | Last run found stale completed-path chat CTAs after world building. Follow-up [Story 157](stories/story-157-chat-suggestions-stop-advertising-completed-paths.md) landed, so FP1 is now awaiting recheck. |

## Run Index

| Date | Scenario | Project | Follow-Up | Status |
|---|---|---|---|---|
| [2026-04-10 local walkthrough](ui-scout/2026-04-10-open-frequency-local.md) | FP1 | `open-frequency` | [157](stories/story-157-chat-suggestions-stop-advertising-completed-paths.md) | Recheck Due |

## Operating Notes

- Keep this markdown lane and `state.ui_scout` in sync on every run so the
  compiled graph can flag stale or awaiting-recheck coverage automatically.
- Keep CineForge on one canonical scenario until repeated real use proves that a
  second scenario is needed. Do not invent taxonomy for its own sake.
- If a run finds a product defect, keep the failed report and link the focused
  follow-up story instead of rewriting history into a green-only log.
