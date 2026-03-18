# CineForge — Retrofit Gap Analysis (Archived)

> Archived on 2026-03-18 by Story 136 during the ADR-021 execution-ideal /
> phase-governance migration.
>
> Original source: `/retrofit-ideal` output generated on 2026-02-26.
> This file is no longer a live planning surface. Its surviving guidance was
> absorbed into the current methodology stack:
> - `docs/spec.md` for active compromise definitions, reconciled detection gates,
>   and execution constraints
> - `docs/build-map.md` for current substrate status, story coverage, and phase
> - `docs/stories.md`, `docs/inbox.md`, and individual stories for backlog ownership
> - `docs/evals/registry.yaml` plus `scripts/check-compromises.py` for current
>   detector state

## Archive Notes

- The original gap-analysis body remains available in git history if the exact
  2026-02-26 diagnostic wording is needed.
- The migration deliberately reconciled thresholds that had drifted between this
  archive and the live docs. The authoritative values now live in `docs/spec.md`
  and `docs/build-map.md`:
  - `C1` cost threshold: `$0.001 / 1M tokens`
  - `C2` first-pass QA detector: `10` diverse tasks
  - `C3` single-model detector: one model meets all current default-driving quality targets
  - `C4` scene-understanding latency bar: `<5000ms`
  - `C7` working-memory detector: `10M` tokens
- Historical Dossier-integration notes in the original document were
  time-specific planning context, not an enduring source of truth. Follow the
  current spec, stories, and ADRs instead of reviving archived assumptions.
