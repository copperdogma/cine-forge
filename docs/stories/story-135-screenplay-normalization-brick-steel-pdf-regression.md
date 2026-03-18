# Story 135: Brick & Steel PDF Normalization Regression

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story input understanding quality bar)
**Spec Refs**: spec:2.2 (Script Normalization), spec:2.3 (Canonical Script Rule), spec:8.2 (Quality Validation)
**ADR Refs**: None found after search
**Depends On**: Story 004 (Script Normalization), Story 064 (Screenplay Format Round-Trip)

## Goal

Turn the reported Brick & Steel PDF import failure into a deterministic regression fix. Today the normalization path can claim the screenplay is formatted while collapsing dialogue and following action into a single block, which corrupts the canonical script and every downstream artifact built from it. This story captures the Brick & Steel PDF as an explicit regression test, identifies whether the failure lives in PDF extraction, normalization, or validation, and fixes the pipeline so the canonical script preserves the original dialogue/action boundaries.

## Acceptance Criteria

- [x] A deterministic regression test covers the existing Brick & Steel PDF golden (`tests/fixtures/round_trip/brick-and-steel/Brick-&-Steel.pdf`) and asserts the known bad passage keeps BRICK's dialogue separate from the following action lines.
- [x] Running the normalization path on the Brick & Steel PDF produces parser-valid screenplay text with the affected dialogue/action boundary preserved in the resulting `canonical_script`.
- [x] The fix is verified through the module or service boundary, not only with a helper-level unit test.
- [x] Existing normalization and round-trip tests for non-regression paths continue to pass, including the existing Brick & Steel golden fixtures.
- [x] Manual artifact inspection is recorded in the work log with the exact evidence checked and the root-cause classification (extraction-wrong, normalization-wrong, validation-wrong, or mixed).

## Out of Scope

- A general rewrite of the normalization architecture or long-document strategy
- OCR/scanned-PDF support beyond the existing Brick & Steel digital PDF path
- Broad screenplay-format cleanup unrelated to the reproduced regression
- Editing the Brick & Steel golden files unless the source files themselves are proven wrong

## Approach Evaluation

- **Simplification baseline**: A stronger single LLM normalization call is not enough by itself. The current pipeline already uses AI and still shipped a golden regression, so the baseline must be measured against the reproduced Brick & Steel fixture rather than assumed.
- **AI-only**: Prompt or QA-repair changes could fix the boundary if the PDF text is already recoverable, but AI-only is risky because the current failure mode is a silent structural corruption that needs deterministic detection.
- **Hybrid**: Likely strongest. Use deterministic reproduction and structural checks to detect collapsed dialogue/action boundaries, then let the existing AI normalization or repair path resolve only the ambiguous cases.
- **Pure code**: Viable only if the root cause is strictly in PDF text extraction or Fountain normalization rules. If the extracted text is ambiguous, pure code will not be sufficient.
- **Repo constraints / ADRs**: AGENTS requires regression fixes to start with fixtures. `script_normalize_v1` is already 1080 lines, so this story must extract focused logic before deepening that file further. Headless module/API verification is mandatory; no UI path is required.
- **Existing patterns to reuse**: Story 004 normalization tests and parser-backed validation, Story 064 Brick & Steel round-trip fixtures, `fountain_validate.py`, `fountain_parser.py`, `tests/unit/test_script_normalize_module.py`, and `tests/integration/test_script_normalize_integration.py`.
- **Eval**: The distinguishing test is deterministic: normalize the Brick & Steel PDF and compare the affected excerpt and structural validity against the known-good Fountain source. No promptfoo eval exists or is needed unless implementation changes force a golden update.

## Tasks

- [x] Add failing regression coverage first using the existing Brick & Steel PDF/Fountain golden pair, with an assertion focused on the reported dialogue/action merge.
- [x] Extract smart-chunk routing out of `script_normalize_v1/main.py` into a focused helper before changing behavior in the oversized module.
- [x] Diagnose the failure at the correct layer (PDF extraction, normalization, validation, or repair) and implement the narrowest fix that makes the regression pass.
- [x] Route screenplay PDFs away from the failing `smart_chunk_skip` optimization and through the existing single-pass cleanup path if the baseline evidence still holds during implementation.
- [x] Add or tighten deterministic coverage so screenplay PDF regressions do not silently take the wrong normalization path again.
- [x] Manually inspect the repaired Brick & Steel `canonical_script` artifact and record the evidence in this work log.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` not required
- [x] Agent tooling and project instructions not touched; `make skills-check` not required
- [x] Evals and golden fixtures unchanged; `/improve-eval` and `docs/evals/registry.yaml` update not required
- [x] UI not touched; browser verification not required
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py` owns the normalization orchestration, but because it is already oversized this story should extract PDF-specific cleanup or validation into a focused helper under the same module or adjacent AI utility instead of adding another large inline branch.
- **Data contracts**: Existing `CanonicalScript`, `NormalizationMetadata`, and `QAResult` schemas remain the inter-layer contracts. This story should not introduce a new boundary model unless the repair path needs typed annotations beyond the current metadata envelope.
- **File sizes**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py` (1071, oversized), `src/cine_forge/modules/ingest/script_normalize_v1/routing.py` (70), `src/cine_forge/ai/fountain_validate.py` (367), `tests/unit/test_script_normalize_module.py` (475), `tests/unit/test_script_normalize_pdf_regressions.py` (108), `tests/unit/test_fountain_validate.py` (36), `tests/integration/test_script_normalize_integration.py` (210). The extraction-first plan landed: routing moved out of the oversized module before behavior changed.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, Story 004, and Story 064. No ADR directly governs this specific regression; it is a correctness bug within an already-decided normalization architecture.

## Files to Modify

- `src/cine_forge/modules/ingest/script_normalize_v1/main.py` — narrow orchestration changes after helper extraction (1071)
- `src/cine_forge/modules/ingest/script_normalize_v1/routing.py` — extracted smart-chunk eligibility/routing logic (70)
- `src/cine_forge/ai/fountain_validate.py` — preserve blank-line-separated action after dialogue during deterministic cleanup (367)
- `tests/unit/test_script_normalize_module.py` — existing normalization coverage kept below 500 lines after test extraction (475)
- `tests/unit/test_script_normalize_pdf_regressions.py` — targeted Brick & Steel PDF regression coverage via real ingest fixture (108)
- `tests/unit/test_fountain_validate.py` — direct deterministic normalizer regression coverage (36)

## Redundancy / Removal Targets

- Any ad hoc smart-chunk eligibility branch embedded directly in `script_normalize_v1/main.py` once a focused helper exists
- Any one-off Brick & Steel regression assertions that duplicate a shared fixture helper or excerpt matcher

## Notes

- Existing golden sources already live at `tests/fixtures/round_trip/brick-and-steel/Brick-&-Steel.pdf` and `tests/fixtures/round_trip/brick-and-steel/Brick-&-Steel.fountain`; this story should reuse them instead of inventing a second Brick & Steel fixture path.
- Reported bad output from `docs/inbox.md`: BRICK's `To retirement.` dialogue is followed immediately by action (`They drink long and well from the beers...`) with no separating blank line, even though the source PDF contains the separation.
- Because this bug affects canonical-script correctness, success requires semantic inspection of the emitted screenplay artifact, not just schema validity.

## Plan

### Eval-First Gate

- **Deterministic regression eval**: add a test that ingests `tests/fixtures/round_trip/brick-and-steel/Brick-&-Steel.pdf` through `story_ingest_v1`, then runs `script_normalize_v1.run_module` with a stubbed `call_llm`. The stub should intentionally preserve the bad merge when invoked through the scene-level `smart_chunk_skip` prompt (`Chunk to fix:`) but return the corrected excerpt when invoked through the existing single-pass normalization prompt (`Source content:`). Pass condition: the resulting `canonical_script` contains `BRICK` → `To retirement.` → blank line → `They drink long and well from the beers.`.
- **Baseline on current code (measured during exploration)**:
  - `story_ingest_v1` already extracts the Brick PDF with the dialogue/action boundary merged in the raw text.
  - Current `run_module` with `claude-haiku-4-5-20251001` returns `normalization_tier=2`, `long_doc_strategy=smart_chunk_skip`, and still ships the merged passage. Cost: `$0.0051792`.
  - Current `run_module` with `gpt-5.4` still fails on the same `smart_chunk_skip` path. Cost: `$0.014065`.
  - The existing single-pass normalization prompt repairs the passage on the same extracted text with `claude-haiku-4-5-20251001`. Cost: `$0.0046792`.
  - The same single-pass prompt also repairs it with `gpt-5.4`. Cost: `$0.014135`.
- **Conclusion**: the current live failure is primarily the `smart_chunk_skip` strategy, not a raw model-capability limit. Upgrading the model inside `smart_chunk_skip` does not solve the bug; reusing the existing single-pass path does.

### Repo-Fit / Optimality Gate

- **Chosen approach**: keep the existing PDF ingest path and route screenplay PDFs away from `smart_chunk_skip` into the already-implemented single-pass cleanup path.
- **Why this fits CineForge better than the alternatives**:
  - It reuses code already proven against the Brick excerpt instead of inventing new PDF heuristics.
  - It keeps the current value-optimized work model; no default model escalation is required to fix the regression.
  - It aligns with AGENTS methodology: test the simplest working path first, and do not build deterministic machinery for a problem an existing AI call already solves.
- **Rejected alternatives**:
  - **Stronger model inside `smart_chunk_skip`**: rejected because `gpt-5.4` still failed on the current scene-splitting path.
  - **Pure ingest/layout repair**: rejected for this story because even feeding raw indented `pdfplumber` output into the current deterministic normalizer still misclassified the excerpt. That is a broader extraction/normalization redesign, not the narrowest fix.
  - **New suspicious-scene heuristics**: rejected unless the routing change proves insufficient. It adds complexity to a module that already has a working single-pass cleanup path.

### Structural Health Check

- `src/cine_forge/modules/ingest/script_normalize_v1/main.py` is **1080 lines** and `run_module()` spans roughly lines `65-302`, so the first implementation step must extract smart-chunk eligibility/routing into a focused helper before adding new conditions.
- `tests/unit/test_script_normalize_module.py` is **478 lines** and can absorb targeted regression coverage without tripping the 500-line rule, but it should stay focused on boundary-level behavior rather than accumulating more generic fixtures.
- `tests/integration/test_script_normalize_integration.py` is **210 lines** and is available if a broader module-boundary or live-gated regression check becomes necessary.
- No new schema, event, or API contract changes are expected.

### Implementation Order

1. **Extract routing helper**
   - Files: `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, new helper module under `src/cine_forge/modules/ingest/script_normalize_v1/`.
   - Change: move the “should this input try `smart_chunk_skip`?” decision out of `run_module`.
   - Risk: unintentionally changing non-PDF screenplay behavior.
   - Done looks like: `run_module` delegates routing to a focused helper and no longer grows more inline branching.

2. **Add deterministic Brick PDF regression coverage**
   - Files: `tests/unit/test_script_normalize_module.py`.
   - Change: use the real Brick PDF fixture via `story_ingest_v1`; stub `call_llm` so chunk prompts remain wrong while single-pass prompts repair the excerpt; assert the returned `canonical_script` preserves the boundary.
   - Risk: prompt-shape matching in the stub could become brittle if prompts change drastically.
   - Done looks like: the new test fails on the current `smart_chunk_skip` routing and passes when screenplay PDFs are sent through single-pass cleanup.

3. **Implement the routing change**
   - Files: helper module + `main.py`.
   - Change: screenplay PDFs bypass `smart_chunk_skip` and continue through the existing `_normalize_once` single-pass path with the current work/escalate model behavior intact.
   - Risk: slight latency change for PDF imports.
   - Done looks like: Brick regression test passes and non-PDF screenplay behavior remains unchanged.

4. **Live verification and artifact inspection**
   - Files: none unless additional notes are needed in tests.
   - Change: rerun in-memory ingest → normalize on the Brick PDF with the current Haiku work model, inspect the canonical script excerpt, and record the result plus cost in the work log.
   - Risk: live model drift could require using the configured escalate model for the smoke check, but the deterministic regression test still anchors the code path.
   - Done looks like: the work log includes the repaired excerpt, cost evidence, and a final root-cause classification.

### Impact / Risk Analysis

- **Files at risk of breaking**: `script_normalize_v1/main.py` routing, tests that assert `long_doc_strategy_name`, and any future behavior that implicitly expected PDFs to use `smart_chunk_skip`.
- **Runtime risk**: PDF normalization may become slightly less optimized because it will use the full single-pass cleanup path, but the measured Brick baseline showed similar or lower cost than the failing `smart_chunk_skip` call.
- **No schema or API blast radius**: this is internal module routing only.

### Redundancy Plan

- Remove any inline PDF smart-chunk special casing from `run_module` once the extracted helper lands.
- Keep ingest-side layout repair unchanged in this story unless implementation disproves the measured baseline; if further PDF signal preservation is still valuable afterward, capture it as a separate follow-up instead of silently expanding this story.

### UI Verification Plan

- None. This is a backend/module story with headless verification only.

### Human-Approval Blockers

- None found. No new dependencies, schema changes, or public API changes are required for the planned fix.

### Scope Adjustment

- **Small inline adjustment already folded in**: exploration showed the bug is not best solved by changing `story_ingest_v1` in this story, even though PDF extraction already loses the separator. The measured repo-fit fix is normalization routing, so the story now explicitly targets `smart_chunk_skip` eligibility rather than a broader PDF extraction redesign.

## Work Log

20260315-2034 — triage: created from the inbox-reported Brick & Steel PDF normalization failure after verifying no existing story owned it. Evidence: `docs/inbox.md`, Story 004 normalization architecture, Story 064 Brick & Steel golden fixtures. Next=`/build-story` to reproduce the regression with a failing test before implementation.
20260315-2128 — exploration: traced the real Brick PDF path through `story_ingest_v1` and `script_normalize_v1` instead of relying on fabricated `raw_input` tests. Findings: `story_ingest_v1` extracts the PDF with the dialogue/action separator already lost, but the decisive live failure is `smart_chunk_skip`, not model capability. Evidence: current Haiku path (`normalization_tier=2`, `long_doc_strategy=smart_chunk_skip`) still merged `BRICK`'s toast with following action at `$0.0051792`; `gpt-5.4` on the same `smart_chunk_skip` path also failed at `$0.014065`; the existing single-pass normalization prompt repaired the passage with Haiku on the same extracted text at `$0.0046792` and with `gpt-5.4` at `$0.014135`. Additional repo-fit evidence: feeding raw indented `pdfplumber` output into the deterministic normalizer still misclassified the excerpt, so a pure ingest/layout fix is not the narrowest solution. Files likely to change: `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, a new focused helper under that module directory, and `tests/unit/test_script_normalize_module.py`; `tests/integration/test_script_normalize_integration.py` is only at risk if broader verification becomes necessary. ADRs/design docs consulted: none specific beyond `ideal.md`, `spec.md`, Story 004, and Story 064. Cleanup target: remove inline smart-chunk eligibility branching from the oversized `run_module`. Next=present the plan and wait for approval before implementation.
20260315-2206 — implementation: extracted `build_normalization_route()` into new `src/cine_forge/modules/ingest/script_normalize_v1/routing.py`, rewired `script_normalize_v1/main.py` to delegate smart-chunk eligibility there, and added deterministic Brick PDF regression coverage at the module boundary using the real `story_ingest_v1` fixture path. Initial result: the routing change correctly moved the live Brick run from `smart_chunk_skip` to `single_pass`, but the final artifact still merged `BRICK` dialogue with following action. Evidence: targeted regression harness in `tests/unit/test_script_normalize_pdf_regressions.py`, prompt traces showing no `Chunk to fix:` calls on the PDF path, and a live smoke run where the raw `_normalize_once` output preserved the blank line but post-`normalize_fountain_text()` output collapsed it. Decision: the true root cause is narrower than “PDF extraction only” and broader than “smart chunk only” — the story needed a tightly coupled deterministic normalizer fix, so that scope was absorbed inline instead of split out. Next=patch `fountain_validate.py` to preserve blank-line-separated action after dialogue.
20260315-2237 — implementation: fixed deterministic dialogue/action collapse in `src/cine_forge/ai/fountain_validate.py` by making dialogue-block continuation respect whether a blank line separated the previous body element, while still allowing noisy blank lines after character cues and parentheticals to heal into dialogue. Added direct coverage in `tests/unit/test_fountain_validate.py` and kept the Brick fixture regression end-to-end through `story_ingest_v1` + `script_normalize_v1`. Validation evidence: `.venv/bin/python -m pytest tests/unit/test_fountain_validate.py tests/unit/test_script_normalize_module.py tests/unit/test_script_normalize_pdf_regressions.py -q` passed (`21 passed`); `make test-unit PYTHON=.venv/bin/python` passed (`554 passed, 127 deselected`); `.venv/bin/python -m ruff check src/ tests/` passed; `.venv/bin/python -m pytest tests/integration/test_script_normalize_integration.py -q` passed (`4 passed, 2 skipped`); `.venv/bin/python -m pytest tests/round_trip/test_pdf_fountain_pdf.py -q -k brick-and-steel` passed. Manual artifact inspection: live Brick PDF smoke run with `claude-haiku-4-5-20251001`, `skip_qa=True`, and the real ingest payload now returns `long_doc_strategy=single_pass`, `normalization_tier=2`, `parseable=True`, cost `$0.009804`, and the repaired excerpt `BRICK / To retirement. / <blank line> / They drink long and well from the beers.` Root-cause classification=`mixed` — extraction loses helpful layout cues, but the actual shipped corruption came from normalization in two places (`smart_chunk_skip` accepted a structurally wrong scene and `normalize_fountain_text` collapsed an already-correct single-pass output). Residual note: live artifact health remains `needs_review` because of unrelated later-script lint issues (`Character cue without dialogue` at lines 93, 95, and `Malformed transition line` at 152), not because of the Brick passage. Docs search: searched `docs/` for `smart_chunk_skip`, `script_normalize_v1`, `fountain_validate`, and Brick references; no additional docs needed updates beyond this story file. Next=`/validate`.
20260315-2125 — validation: reran the required gate on the current worktree. Results: `make test-unit PYTHON=.venv/bin/python` passed (`553 passed, 128 deselected`, same pre-existing unknown `acceptance` mark warning); `.venv/bin/python -m ruff check src/ tests/` passed; story-targeted tests passed (`tests/unit/test_fountain_validate.py` + `tests/unit/test_script_normalize_pdf_regressions.py` → `4 passed`; `tests/integration/test_script_normalize_integration.py` → `4 passed, 2 skipped`; `tests/round_trip/test_pdf_fountain_pdf.py -k brick-and-steel` → `1 passed`); `pnpm --dir ui run lint` passed with 5 pre-existing `react-refresh/only-export-components` warnings in unrelated UI files; `cd ui && npx tsc -b` passed. Decision review: no directly applicable ADR was found beyond the previously reviewed normalization context, and the routing+normalizer fix still looks repo-fit. Validation finding: the test-file split accidentally removed `@pytest.mark.unit` from `tests/unit/test_script_normalize_module.py::test_run_module_with_mock_model_produces_canonical_script`, so that pre-existing unit test no longer runs under `make test-unit` (visible at line 152 and reflected in the suite dropping from `554/127` to `553/128`). Closure recommendation=`Keep open` until that marker is restored and the full unit suite is rerun. Next=restore the missing unit marker, rerun the mandatory backend checks, then `/mark-story-done` if clean.
20260315-2132 — close-out: restored the missing `@pytest.mark.unit` on `tests/unit/test_script_normalize_module.py::test_run_module_with_mock_model_produces_canonical_script`, reran the closure gate, and marked Story 135 done. Final evidence: `make test-unit PYTHON=.venv/bin/python` passed (`554 passed, 127 deselected, 1 pre-existing warning`); `.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` passed with the same 5 pre-existing fast-refresh warnings in unrelated UI files; `cd ui && npx tsc -b` passed; `.venv/bin/python -m pytest tests/unit/test_fountain_validate.py tests/unit/test_script_normalize_module.py tests/unit/test_script_normalize_pdf_regressions.py tests/integration/test_script_normalize_integration.py tests/round_trip/test_pdf_fountain_pdf.py -q -k brick-and-steel` passed. Result: the Brick & Steel PDF regression fix is closed with the unit gate restored, story status/index updated, and changelog recorded. Next=`/check-in-diff`.
20260315-2143 — post-close validation: reran the full required gate after story closure to verify the final worktree state. Evidence: `make test-unit PYTHON=.venv/bin/python` passed (`554 passed, 127 deselected, 1 pre-existing warning`); `.venv/bin/python -m ruff check src/ tests/` passed; `.venv/bin/python -m pytest tests/unit/test_fountain_validate.py tests/unit/test_script_normalize_module.py tests/unit/test_script_normalize_pdf_regressions.py tests/integration/test_script_normalize_integration.py tests/round_trip/test_pdf_fountain_pdf.py -q -k brick-and-steel` passed; `pnpm --dir ui run lint` passed with the same 5 unrelated fast-refresh warnings; `cd ui && npx tsc -b` passed. Review outcome: no new findings, acceptance criteria still hold, and the Story 135 `Done` closure remains correct. Next=`/check-in-diff`.
