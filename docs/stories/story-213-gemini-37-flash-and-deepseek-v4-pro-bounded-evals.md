---
id: "213"
title: "Gemini 3.7 Flash and DeepSeek V4 Pro bounded evals"
status: "Done"
priority: "High"
ideal_refs:
  - "R1"
  - "R3"
  - "R8"
  - "R12"
spec_refs:
  - "spec:2"
  - "spec:8"
adr_refs:
  - "ADR-003"
depends_on:
  - "208"
  - "211"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
  - "C5"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "gemini-3.7"
  - "deepseek-v4-pro"
legacy_system: ""
---

# Story 213 — Gemini 3.7 Flash and DeepSeek V4 Pro bounded evals

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R3, R8, R12
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-003
**Depends On**: Stories 208 and 211

## Goal

Determine whether Gemini 3.7 Flash repairs Gemini 3.6 Flash's source-backed QA and ordered-frame failures, and whether DeepSeek V4 Pro can complete CineForge's exact `script_bible_v1` contract inside the maintained quality, latency, cost, reliability, and privacy gates. Preserve exact transport and scoring evidence without changing production defaults.

## Eval Ladder Context

- **Gemini ladder**: repaired `qa-pass` known-good case first; if its exact source-grounding hard gate passes, run the repaired six-case `video-understanding` ordered-JPEG lane. These are the clean successors to Story 208's Gemini 3.6 failures and test C2/C5 evidence without claiming native video/audio coverage. Expand to `script-bible` only if both diagnostic lanes pass and a runtime-value question remains.
- **DeepSeek ladder**: one tiny strict-schema OpenRouter probe, then exactly one complete synthetic Open Frequency `script_bible_v1` runtime-shaped call. Story 211's V4 Flash route qualified transport but failed full-script latency/reliability. Stop immediately on any `>=0.90` quality, `<=30,000 ms`, or `<=US$0.01` hard-gate failure; do not run the private Mariner fixture or incumbent comparator after an absolute failure.

## Acceptance Criteria

- [x] Exact requested/served model identity, provider route, structured-output contract, terminal status, usage, cost, and retention controls are captured for every completed paid candidate call; the interrupted Baidu call explicitly records missing terminal usage/cost.
- [x] Gemini 3.7 is progressively evaluated on only the source-backed repaired lane(s), with significant mismatches classified as model-wrong, golden-wrong, or ambiguous.
- [x] DeepSeek V4 Pro is evaluated on the exact runtime-shaped public/synthetic transport boundary and stopped before the full screenplay when route qualification failed the absolute latency/value ladder.
- [x] Registry and attempt evidence preserve every executed result, including inconclusive or stopped runs, without changing defaults.
- [x] Focused tests, methodology compilation, lint/diff checks, and relevant unit validation pass.
- [x] QA source/golden truth, production prompt/scorer agreement, selection contamination, runtime identity/parity, semantic quality, and latency/cost are independently classified after the invalid first verdict.
- [x] The repaired scorer rejects generic, adjective-stuffed, negated, and anchor-stuffed positive summaries without requiring hidden source-anchor recitation; sparse family-keyword findings also fail.
- [x] Frozen Gemini output is regraded and the actual GPT-4.1 Mini incumbent plus Gemini 3.7 are compared on an identical two-case prompt/schema snapshot; the later final prompt/scorer contract is explicitly unmeasured and both frozen outputs fail its regrade.

## Out of Scope

- Dossier, private payloads, native-video/audio claims, broad provider matrices, production defaults, commits, pushes, deployments, or adding a direct DeepSeek credential.

## Approach Evaluation

- **Simplification baseline**: both questions are already single-call model slots; the issue is candidate capability/value, not new application logic.
- **AI-only**: use the existing strict-schema provider seams and maintained semantic rubrics.
- **Hybrid**: deterministic source-grounding scorers plus a frozen cross-provider Opus 4.6 rubric protect against schema-only or judge-only false positives.
- **Pure code**: limited to benchmark transport declaration, provenance, and validation; it cannot answer semantic quality.
- **Repo constraints / ADRs**: ADR-003 makes script bible the first story-derived identity artifact. Current C2/C3/C5 phases are `hold`; new evidence must not erase justified specialist lanes without all gates passing.
- **Existing patterns to reuse**: Stories 208/211, repaired QA/frame contracts, `script_bible_runtime_provider.py`, the provider-env wrapper, exact-identity validation, and registry provenance contracts.
- **Eval**: maintained `qa-pass`, `video-understanding`, and runtime variant of `script-bible`; no new eval is needed.

## Predeclared Decision Contract

- **Freshness**: force-fresh candidate calls on current base `b2f900211a86eec440ac323ffda7ca03bd95fbb6`; no cache; concurrency one.
- **Gemini candidate**: direct Google `gemini-3.7-flash`, low thinking where supported, strict provider-enforced schema, 65,536 output-token ceiling. QA gate `overall >=1.0`, latency `<=10,000 ms`, cost `<=US$0.02`; video gate `overall >=0.80`, latency `<=15,000 ms`, cost `<=US$0.02`. One access/contract retry only; no semantic retry.
- **DeepSeek candidate**: OpenRouter `deepseek/deepseek-v4-pro`, low reasoning, provider-enforced strict `ScriptBible`, no fallbacks, required parameters, and data collection denied. Route calibration may compare at most two provider/privacy arms before the decision fixture: Together/ZDR and the Scout-qualified lower-cost Baidu/non-ZDR route. Only public synthetic content is eligible on the frozen non-ZDR decision arm. Script-bible gates `overall >=0.90`, latency `<=30,000 ms`, cost `<=US$0.01`; one access/contract retry only; no semantic retry.
- **Scoring**: maintained deterministic scorer plus frozen cross-provider Opus 4.6 rubric, reported separately before aggregate. Same-provider judge bias is not present for either subject.
- **Spend cap**: US$5 total including probes, subjects, retries, and judges. Stop before the next call if the ledger cannot stay bounded.
- **Comparators**: use maintained Gemini 3.6 source-backed rejection rows for the exact QA/frame failure question. DeepSeek is screened first against absolute runtime gates; run no fresh incumbent after any absolute failure.
- **Defaults**: no model or transport default changes are authorized.

## Tasks

- [x] Refresh official/provider and authenticated access truth through repo-owned discovery and the provider-env wrapper.
- [x] Add only the minimal candidate declarations and focused transport tests needed to exercise existing maintained lanes.
- [x] Run Gemini progressive QA; stop before ordered frames after the first quality failure and inspect source evidence.
- [x] Run DeepSeek strict-schema route probes; stop before Open Frequency after the tiny Baidu probe exceeded the full lane latency gate.
- [x] Record attempts, result provenance, registry rows, spend ledger, and work log.
- [x] Run focused tests, `make test-unit`, Ruff, methodology compile/check, and `git diff --check`.
- [x] Confirm no production default, private fixture, UI, deployment, commit, or push changed.
- [x] Blindly verify QA source/golden truth and repair only contract-invalid prompt/scorer/golden assumptions.
- [x] Regrade frozen outputs and rerun the incumbent and Gemini challenger on the same two current-contract cases.
- [x] Record the repaired attempt, registry truth, contract manifest, validation, spend, and adoption decision.

## Workflow Gates

- [x] Build complete: bounded executions and durable evidence complete.
- [x] Validation complete.
- [x] Tenet verification complete: progressive stops, exact transport evidence, public/synthetic privacy boundary, mismatch classification, and no-default-change rules are preserved.
- [x] Documentation complete: attempts, registry, truth ledger, manifests, methodology surfaces, scorer contract, and validation evidence are current.
- [x] Story marked done via /mark-story-done.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: existing benchmark providers own transport; `script_bible_v1` remains the production owner and is not changed.
- **Data contracts**: existing `ScriptBible`, QA JSON, and video-analysis v3 schemas.
- **File sizes**: benchmark provider size is acknowledged; changes are narrow candidate configuration extensions, not new responsibilities.
- **Decision context**: ADR-003 reviewed. No other ADR governs provider selection; Stories 208 and 211 supply the eval-truth and OpenRouter constraints.

## Files to Modify

- `benchmarks/tasks/qa-pass.yaml` — declare Gemini 3.7 subject.
- `benchmarks/tasks/video-understanding.yaml` — declare Gemini 3.7 frame subject.
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — declare DeepSeek V4 Pro subject.
- `benchmarks/providers/script_bible_runtime_provider.py` and focused tests — pin/validate the exact OpenRouter route.
- `docs/evals/attempts/` and `docs/evals/registry.yaml` — durable results and classifications.
- generated methodology surfaces — story metadata refresh.

## Redundancy / Removal Targets

- None. This evaluation adds no production path; any later default change is a separate user decision.

## Notes

- Conductor Scout 044 (2026-08-13) supplies current launch/API routing evidence and explicitly excludes Dossier from this execution.
- Public/synthetic fixtures only until route retention is pinned.

## Plan

Execute the predeclared progressive ladders exactly as written. Change only one transport variable at a time, preserve failed attempts, and stop before any later lane once its entry gate fails.

The follow-up validity repair first separates six questions: source/golden truth; production prompt/scorer agreement; fixture-selection contamination; actual incumbent identity and current-contract parity; semantic capability; and latency/cost adoption. An independent verifier owns fixture truth. The main worker owns the production-consumer trace, scorer/prompt repair, adversarial tests, frozen-output regrade, and an identical two-case exact shared-`qa_check` comparison of `gpt-4.1-mini` and `gemini-3.7-flash`. This narrow provider imports the production prompt builder and schema while leaving defaults/shared runtime unchanged. The old selected-anchor scores remain historical diagnostics, not promotion evidence; no broader sweep follows from two cases.

## Work Log

- 20260813 — intake-and-plan: moved off the dirty primary checkout into an isolated worktree at current `main`; read the repo-local evaluate-model workflow, alignment sources, registry, repaired Story 208 evidence, Story 211/Attempt 022, ADR-003, maintained tasks/scorers/goldens, runtime default, and provider seams. Froze the matrix, privacy boundary, US$5 ledger, retries, and stop conditions before paid calls.
- 20260813 — route-calibration: Together/ZDR qualified strict schema and exact identity on a tiny synthetic probe, but cost `$0.00423516` and latency `19,109 ms` for only 464 input and 985 completion tokens. That consumes 42% of the per-call cost gate before a complete screenplay. Froze Scout 044's already-qualified lower-priced Baidu route for the public/synthetic decision arm, with no fallback and data collection denied; this route is explicitly non-ZDR and ineligible for private payloads.
- 20260813 — gemini-progressive-stop: the initial QA request failed before a response because Google rejects `additionalProperties` in its supported schema subset. The single contract retry removed only that unsupported keyword. Exact `gemini-3.7-flash` then returned terminal `STOP`, valid required-shape JSON, and complete raw usage, but the known-good answer scored only `0.70995` (`0.5999` deterministic, `0.82` Opus) because its summary named no source facts. Subject latency was `1,358 ms` and estimated subject cost `$0.0024825`. Classified model-wrong/runtime-blocking for QA; ordered-frame and script-bible lanes not measured.
- 20260813 — deepseek-progressive-stop: Together/ZDR was callable but implausible under the full cost gate. The frozen lower-cost Baidu/non-ZDR request produced no terminal response beyond 60 seconds and was interrupted after already exceeding the 30-second lane gate by more than 2x. No full Open Frequency call, judge, comparator, or semantic score was run. Capability remains unmeasured; latency/reliability failed.
- 20260813 — spend-ledger: known provider spend is approximately `$0.04770766` (Gemini subject `$0.0024825`, Opus judge approximately `$0.04099`, Together probe `$0.00423516`). The interrupted Baidu call returned no usage; at the configured 4,096-token ceiling and documented route pricing its conservative maximum is about `$0.00658289`, keeping total invocation spend below approximately `$0.05430` and far below the `$5` cap.
- 20260813 — validation: focused provider/video tests passed; full unit suite passed `2,067`; Ruff passed for the whole repo; `pnpm methodology:compile` and `pnpm methodology:check` passed with only pre-existing architecture-audit/UI-scout freshness warnings; `make check-size` reported only acknowledged existing large files; JSON validation and `git diff --check` passed. No UI or production module changed, so browser validation is not applicable.
- 20260813 — qa-validity-audit: traced the executable QA contract and consumers. `QAResult.summary` has no anchor requirement; scene-analysis uses only `passed` on success, while other modules use summary as actionable retry feedback only after failure. The benchmark's good-case scorer nonetheless hard-gated three selected source anchors absent from both production prompt and schema. Classified the prior Gemini rejection as scorer/golden-wrong and selection-contaminated rather than model-wrong. Actual scene-analysis incumbent is `gpt-4.1-mini`, but the retained 1.0 row is old-contract/contaminated and not current parity. The benchmark payload is a useful source-fidelity proxy, not exact scene-analysis payload parity because runtime submits a compact enrichment summary.
- 20260813 — qa-validity-repair: added an isolated exact shared-`qa_check` prompt/schema provider, removed the hidden positive-summary anchor requirement, aligned the semantic rubric, and added generic, negation, anchor-stuffing, identity, prompt, schema, token, and cost regressions. That intermediate scorer regraded the frozen Gemini 3.7 output from deterministic `0.5999` to `1.0` (aggregate `0.91` with its retained Opus `0.82`), proving the original rejection scorer/golden-wrong. A later candidate-blind threshold review superseded the intermediate count scorer with the final six-family contract described below.
- 20260813 — qa-current-contract-results: independent source-first verification ended CLEAN on the task-supplied excerpt and removed the selected-anchor requirement. Fresh exact shared-prompt/schema runs returned correct good/bad verdicts for both models and all four Opus judgments passed. An independent candidate-blind threshold review then proved both numeric thresholds unsafe and froze a six-family contract. Because the production prompt changed after the paid runs, those runs are now pre-final-contract diagnostics. Frozen final-scorer regrades are GPT-4.1 Mini `0.832475`, `3,148 ms/call`, `$0.000955/call`; Gemini 3.7 Flash `0.834975`, `2,340 ms/call`, `$0.003323625/call`. Both fail the final bad-case family gate, so no default change; fresh final-contract semantic parity remains unmeasured.
- 20260813 — qa-followup-validation: candidate-blind reviewer approved the substantive six-family contract after README/spec/validator fail-closed coverage, removal of maintained numeric counts, explicit confidence calibration, and the final EOF cleanup. Focused QA/provider/golden/manifest tests pass; golden validator reports zero errors/warnings; full unit suite passes `2,072`; full Ruff, eval registry/truth ledger/contract manifest, methodology compile/check, and `git diff --check` pass. Existing architecture-audit and UI-scout freshness warnings remain unrelated. No UI or deployed runtime default changed, so browser/runtime UI validation is not applicable.
- 20260813 — qa-final-specificity-closeout: a final adversarial review proved the positive summary still accepted adjective stuffing and the family matcher still accepted sparse two-token overlaps. The frozen source-independent contract now requires a positive judgment across at least three reviewed dimensions and, for every negative family, one field-owned issue containing both candidate-defect and source/correction concepts. Exact sparse probes fail and paraphrased grounded controls pass. All pre-final QA rows are explicitly non-decision-grade, so the regenerated graph has no QA `latestScore`; GPT-4.1 Mini remains default by inertia only. The Story 213 manifest was regenerated after this repair with Attempt 026, QA runtime provider, current result artifacts, and current contract hashes. No provider calls were made.
- 20260813 — qa-systemic-polarity-audit: final review found that unordered concepts still credited six explicitly negated defects and allowed a contrastive positive summary ending in `but its tone is wrong`. Replaced concept bags with per-family affirmative claim contracts: candidate-error terms, defect relations, and source-correction terms must all be present with non-negated polarity in the proper field. Negated, double-negated, correction-only, source-correct, and anchor-stuffed claims fail closed across all six families; affirmative grounded paraphrases pass. Positive summary clauses now reject any affirmative material fault after contrast while permitting explicit no-fault denials. Deterministic scope is intentionally bounded to canonical alternatives and fails closed rather than claiming general entailment. Frozen GPT/Gemini aggregates remain `0.832475`/`0.834975`, both fail, and fresh final-contract capability remains unmeasured. No calls/default changes followed.
- 20260813 — qa-modality-freeze: the same clause contract now rejects uncertainty/hedging (`may`, `might`, `could`, `perhaps`, `possibly`, `appears to`, `seems to`, `suggests`, and maintained equivalents) for either a family defect assertion or failure-summary source anchor. A systematic six-family-by-eight-hedge matrix, one-hedged-family completeness attack, hedged-summary matrix, and direct confidence-calibration control all discriminate. The rule is clause-scoped and does not reject an unhedged `candidate confidence is overconfident` finding. Frozen regrades are unchanged; this is the final explicit negation/contrast/modality boundary, with no broader semantic expansion or provider call.
- 20260813 — qa-clause-role-freeze: structural review found the scorer still unioned all affirmed concepts, allowing an unhedged candidate defect to borrow correction terms from a hedged source clause. Defect and correction roles now match independently within unhedged clauses; both may share one clause only when both explicit relations are present there. Every-family tests cover unhedged defect plus hedged correction, hedged defect plus unhedged correction, two unhedged clauses, one combined unhedged clause, and overlapping-token bridge attacks. No new language category, provider call, or default change followed.
- 20260813 — qa-source-relation-disjointness: final structural review found cast correction vocabulary could still be double-counted because candidate verbs such as `omits` had been admitted as source relations. Removed all candidate-defect verbs from source authority across the six families. Source correction now requires explicit source/script authority, a bounded comparative relation, or a confidence basis. The exact `omits Mariner; source may have Mariner` bridge fails; per-family scorer and validator invariants prohibit a candidate relation from satisfying source relation alone. Legitimate explicit source-relation controls remain green.
- 20260813 — story-closeout: `/mark-story-done` confirmed every acceptance criterion and task, mismatch classification, runtime-blocking status, registry row, documentation surface, and workflow gate. Final required validation passed: `2,171` unit tests, full backend/test and benchmark/script Ruff, QA golden validator with `0` errors/warnings, eval-registry and truth-ledger checks, current methodology outputs, manifest hash regression, and `git diff --check`. Story status is now `Done`. Recommended next step: `/check-in-diff`.
