---
id: "223"
title: "Use pnpm for root and UI dependency installs"
status: "Done"
priority: "Medium"
ideal_refs: []
spec_refs:
  - "spec:11.4"
adr_refs: []
depends_on: []
category_refs:
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags:
  - "tooling"
  - "dependency-management"
legacy_system: ""
---

# Story 223 — Use pnpm for root and UI dependency installs

## Goal

Make one pinned pnpm version the dependency installer for both Node projects, while preserving their independent lockfiles and the seven-day package release-age policy. The root's `afterwriting` dependency and the UI build must continue to work at the versions already selected by npm.

## Decision context

This is execution infrastructure under `spec:11.4` and the execution ideal. The ADR search found no package-manager decision in ADR-001 through ADR-003. A unified workspace would restructure two existing independent projects without an observed need, so each retains its own lock and `pnpm-workspace.yaml`. No model or scored eval is involved.

## Acceptance

- [x] Both manifests pin pnpm 10.34.5 and frozen installs succeed independently.
- [x] pnpm locks contain the same package name/version sets as the prior npm locks, with all direct versions unchanged.
- [x] Setup, Docker frontend build, local launch actions, current documentation, and current skill commands use pnpm for project installs and scripts.
- [x] The local launcher passes host and port flags through to Vite.
- [x] The existing `afterwriting` PDF export path works after the root pnpm install.
- [x] Required UI checks and focused PDF export tests pass.
- [x] The changed Docker frontend stage builds in an available Docker daemon.
- [x] Review and land through the normal validation/close-out flow when authorized.

## Workflow gates

- [x] Build complete.
- [x] Validation complete: prior frozen installs/UI checks reused; changed provider checks, full unit suite, and actual Docker frontend build pass.
- [x] Tenet verification: preserved independent project ownership, locked versions, freshness policy, and provider evidence boundaries.
- [x] Documentation updated: current setup/runbooks, changelog, and generated views.
- [x] Story marked done via `/mark-story-done` after remote implementation landing verification.

## Work Log

20260927-1802 — Pinned pnpm migration is implemented in an isolated worktree; root and UI frozen installs and focused consumers pass. Docker execution awaits a daemon, and five unrelated provider-floor unit tests failed in a broad run.

- Built from `origin/main` at `f69909d` in isolated branch `codex/pnpm-migration-20260927`. The primary checkout had unrelated dirty files and was not edited.
- `pnpm import` converted the current npm locks. A name/version set comparison found exact parity: root 115/115 package entries and UI 802/802; all 1 root and 43 UI direct dependency versions match. The older UI pnpm lock had nine direct-version differences from npm, so it was refreshed from npm before removing both npm locks.
- Added package-manager pins and separate release-age policies. Frozen installs passed with pnpm 10.34.5. pnpm ignored `snyk`'s root build script and `core-js`, `esbuild`, and `msw` UI scripts. No allowlist was added: the UI build and root `afterwriting` CLI work with those scripts blocked. A later package need should justify a narrow allowlist entry.
- `pnpm --dir ui run lint`, `pnpm --dir ui exec tsc -b`, and `pnpm --dir ui run build` passed. Build retained its existing large-chunk warning. `node --test ui/tests/*.test.ts` passed 21/21; duplication check reported 2.87%. `make skills-check` and `pnpm methodology:check` passed; methodology reported existing architecture/UI-scout freshness warnings.
- `pnpm --dir ui run dev --host 127.0.0.1 --port 5188` bound to the requested host and port, and HTTP HEAD returned 200. The existing Python PDF export produced a valid 12,189-byte PDF from synthetic Fountain text with backend `afterwriting-npx`; focused `tests/unit/test_fdx.py` passed 4/4. The `npx` runtime call remains as an existing product behavior and resolves the pnpm-installed local binary from the repository root.
- A broad `make test-unit` run reported 2,189 passing and five failing tests, all in untouched final-render provider-floor contract test files. That broader failure has not been investigated or claimed as a baseline result; the migration's affected paths passed their focused checks.
- Docker CLI is present, but the daemon is unavailable in this environment. The Dockerfile was reviewed statically for pinned pnpm bootstrap, UI lock/workspace copy, frozen install, and build order; image execution remains unverified.

20260927-1900 — Close-out validation repaired five existing provider-floor unit failures and exercised the changed Docker stage. No provider evaluation or model-quality measurement was run.

- The Docker frontend stage built successfully with a daemon as image `sha256:a611b306e91540a6cb162d2c807853eb18072a0004ab8491ab2937d666795720` (`docker build --target frontend -t pnpm-cineforge-validation:20260927 .`). This proves the pinned pnpm bootstrap, frozen UI install, and frontend build in the changed stage. The unchanged Python final stage was not rebuilt; no deployment was performed.
- A broad unit run before repair reproduced exactly five failures in untouched provider-floor contract tests. Four positive fixtures were rejected because the source target omitted the schema's empty `excluded_dimensions` default and macOS resolved temporary `/var` paths to `/private/var` for one side of a file-set comparison. The validator now compares that one empty default semantically after retaining its source-byte/hash checks, and canonicalizes the dataset root before comparing snapshot paths. Historical generator files and evidence hashes remain unchanged.
- The fifth failure was an existing size gate: `video_understanding_provider_vision.py` was 466 lines with a 140-line OpenAI function. Moved its Gemini transport and the OpenAI frame builder and token/cost calculation into the already fingerprinted provider-support module. The public vision callable remains available. Moved request and cost logic preserves the prior behavior; the changed subject implementation fingerprint identifies the new source layout for future runs, while historical model evidence remains historical.
- `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python PYTEST_ADDOPTS='-q --tb=short'` passed after the provider-floor repairs. Standalone `test_video_understanding_gpt6_contract.py`, `test_video_understanding_benchmark.py`, and `test_non_gemini_token_metrics.py` passed after moving provider imports below path setup, exercising strict request shape, retained raw response, and cost reconciliation. Ruff on the four changed Python files and `git diff --check` passed. No scored eval was run, so the eval registry has no new result to record.

2026-09-27 — Closed via `/mark-story-done` under the approved `/finish-and-push` flow.
Implementation commit `3e0e16a62207f624abafcf70504df714e5297520` was pushed and
verified at remote `main`. Every acceptance criterion is met. No model-quality
eval or deployment was performed. Only closure metadata changes after validation;
applicable source/build evidence is reused under the proportional policy.

## Where to verify

Review implementation commit `3e0e16a` and this work log. Conductor Alignment 048
records cross-repo storage measurements and final landing identities. Primary
checkouts and existing npm installations remain untouched.
