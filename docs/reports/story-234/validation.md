# Validation report — Story 234 — 2026-10-25

## Findings and disposition

No remaining material finding in the bounded implementation. Two independent code reviews found seven defects; all were accepted and fixed. Parent review also fixed readiness bypass and concurrent output-version collisions. A final bounded find-only review of the three second-review repairs found no material issue. See review-findings.md for the retained failures and dispositions.

One inherited broad-suite failure remains: `test_gpt61_video_verification::test_tracked_verification_needs_no_local_receipts_or_provider_calls` rejects frozen bytes for `benchmarks/providers/video_understanding_provider.py`. Its SHA256 is f59f5c670c1e966db8526ec04f41bf68dd509cefca2dbeedf4dd17790c012362 both at baseb6fe8319 and in this candidate. This is a pre-existing historical-evidence mismatch, non-runtime-blocking for234. It was not repaired by rewriting immutable evidence. The full unit suite is therefore not claimed all-green.

## Checks and evidence reuse

- Broad credential-isolated unit run:2432passes/3failures. The dotenv fixture failure came from deliberately disabling dotenv; corrected fake-env configuration passed7tests. Missing ownership for the new UI test was repaired and the final45manifest/ledger tests pass. The third failure is the inherited mismatch above.
- Final focused backend/driver/CLI/API boundary run:76passes. Two additional parametrized current-run validation-target cases pass (the5-test regression file includes3overlapping tests). These checks cover all later executable fixes, including ref-only real worker→driver→adapter→media validation→artifact persistence, one-use claims, stale source mutations, concurrent approval exclusion, recovery boundary retention, synchronous recovery rejection and retained costs. The final formatting-only line wrap does not change tested behavior.
- Relevant offline integration suite:23passes across10files; retained command/config in backend-integration-summary.md. Reused for unchanged ordinary consumers. Later approved-only validation is additionally covered through the real API/worker test and exact selected-output collector cases. No blanket suite rerun was needed.
- Ruff over `src/`, `tests/` and new CLI helper:PASS.
- Final UI:35/35Node tests; TypeScript, ESLint and production build PASS. Existing chunk-size warning remains. Exact commands, dependency identity and240UIfile hashes:ui-validation.json.
- Manifest/ledger focused tests:45passes. `make check-evals PYTHON=.venv/bin/python` and terminal ledger check PASS. Final manifestv33:1088files, bundle5c0276fc093c61341387dedb0629138223a29e002c3325591c5584730c414a07. Earlier manifests remain byte-identical; v32 preserves the pre-lint snapshot rather than being overwritten. UI sources remain outside the established manifest prefix policy and have their separate full hash receipt.
- Representative normal-workflow desktop1440×1000/mobile390×844:PASS for preparation, automatic inspection, all/subset work, cost exclusions, provider blockers, empty selection and paused preparation. Original two browser crashes retained; official narrow Slot fix survived fresh completion. Final browser console has zero warnings/errors; viewport reset.
- Agent skills unchanged; sync gate N/A. Methodology compile/check required after closure.
- No Promptfoo or scored AI-quality eval ran. Unit/integration tests are mechanical contract validation, not a new registry quality score or provider qualification.

## Acceptance criteria

All seven criteria met within the stated control boundary:

1. Both surfaces prepare through render_clip_planning without video and disclose text-AI cost. Recovery retains this stop.
2. Immutable typed no-call plans show actual normalized units, canonical video-only subtotal, sourced price, exclusions and blockers; total remains unknown.
3. Scene/clip entry points share inspection/confirmation; empty, stale or blocked work cannot confirm. Single-clip saved/historical consumers retain explicit test coverage; representative project has no playable video, so live playback is not claimed.
4. API derives scope from saved approval; worker validates and consumes the source snapshot. Inputs, absences, mutable selections, bytes, effective runtime, recipe and pack are bound.
5. Retired/unpriced provider and reference/replay guards remain active. No automatic new reference backfill after approval. Known incurred costs survive failure; a project media lock protects output allocation through validation/persistence.
6. API/CLI preparation, inspection and execution are available; confirmed runs retain selected downstream media validation. Unsupported approval recovery rejects synchronously and requires fresh inspection.
7. Focused tests, schema/API boundaries, lint/build and representative responsive browser evidence pass; inherited unrelated failure is explicit.

## Fit and closure

ADR002's expensive-operation review and ADR003's on-demand generation remain intact. Shared renderer shaping and ArtifactStore contracts are reused; large UI responsibilities were extracted. No compatibility layer, duplicate pricing owner or general reservation/recovery platform was introduced. This advances R7/R8/R10/R11/R12 and active spec6/7climb with cost transparency under spec8hold.

Grade:B (bounded acceptance met; inherited broad-suite evidence failure and live-provider limitations remain explicit). Disposition:**Close now**. The current user has authorized check-in and push, then stop; proceed through mark-story-done and finish-and-push without another confirmation.

Optional verification: `/open-frequency/scenes/scene_003?tab=previz` → Inspect existing clip plan → select one clip → inspect selection. Scene4's paused preparation links to the run's Resume UI. No live video success or FP1 pass is asserted; blocked232 retains full-pipeline ownership.

Raw pytest failure transcripts intentionally retain their original trailing whitespace; exclude backend-unit.txt/.xml from whitespace-only diff checking. Two UI EOF blank lines were removed at closeout and their UI hash receipt refreshed; this is formatting only and does not invalidate behavior/build evidence.
