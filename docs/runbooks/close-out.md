# Close-Out

Use this runbook with `/finish-and-push`. The shared skill owns authorization,
coordination, Git integration, landing, recovery, and optional cleanup. This
runbook supplies CineForge's local completion evidence.

## Story closure

When a story is in scope, use `/mark-story-done` and preserve its status,
workflow-gate, work-log, dependency, tenet, acceptance-criterion, and
mismatch-classification checks. Refresh generated planning surfaces with
`pnpm methodology:compile`. Update `CHANGELOG.md` once using the repo's
`YYYY-MM-DD-NN` CalVer format. If `/mark-story-done` was called by
`/finish-and-push`, return control to the invoking skill after closure instead
of recommending a new close-out invocation.

## Required evidence

Choose the smallest sufficient checks under the shared skill's `Validation
proportional to the change` policy. Reuse applicable evidence when its tested
content, environment, and check configuration still match the candidate. Keep
`PYTHONPATH=src` so the shared environment cannot import CineForge from a
sibling checkout.

- evidence or documentation only: inspect affected claims, links, schemas,
  provenance, and generated records; do not run product suites
- isolated eval or development tooling: run focused pytest and Ruff checks for
  the changed tooling and affected shared interfaces
- runtime, dependency, build, shared-library, or cross-pipeline changes: broaden
  from focused checks to `make test-unit PYTHON=.venv/bin/python`, full relevant
  Ruff paths, integration checks, and affected consumers when warranted
- agent skill changes: `make skills-check`
- UI changes: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
  `pnpm --dir ui run build`; behavior changes also require desktop and mobile
  browser verification with clean console output or a documented blocker
- pipeline or artifact changes: run the narrowest real driver/API path, validate
  schemas, and manually inspect the produced artifacts for semantic correctness
- eval work: classify every significant mismatch, update
  `docs/evals/registry.yaml` with the verified score and required provenance,
  and preserve required attempt evidence

A passing command does not replace artifact inspection where project rules
require semantic or visual evidence. Record skipped or unavailable checks
honestly. Follow the shared skill for authorization, Git handling, landing,
recovery, and cleanup.
