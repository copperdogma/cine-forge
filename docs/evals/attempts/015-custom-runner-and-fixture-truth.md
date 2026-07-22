# Eval Attempt 015 - Custom Runner and Fixture Truth

**Status:** Succeeded
**Eval:** repository-custom-runner-fixture-truth
**Date:** 2026-07-22
**Worker Model:** GPT-5.6
**Subject Model(s):** No subject, judge, image, video, or paid provider call

## Mission

Audit the maintained non-Promptfoo runners, runtime roots, browser probes, and
non-golden fixture classes that can be mistaken for semantic or adoption-grade
evidence. Repair deterministic contracts where possible, preserve historical
measurements without overstating their authority, and make every deferred live
confirmation explicit.

## Prior Evidence

Attempts 007 through 014 established that aggregate passage, schema validity,
retained result filenames, and old registry scores are not semantic proof. This
pass therefore inspected runner behavior, fixture intent, source linkage,
partial-success semantics, live-call boundaries, and retained-result
reproducibility directly. It did not reinterpret any historical score as clean.

## Baseline Reproduction and Classification

- Runtime media clips printed the expected answer into the pixels; quiet
  coherent stillness had an incorrect `needs_review` expectation; and the
  prop-swap prompt disclosed the color change it asked the validator to detect.
  **Classification:** fixture/golden-wrong and harness-wrong; old scores
  contaminated and default-decision-blocking.
- Final-output validation repeated one synthetic clip while its surrounding
  prose could be read as project-level creative-coherence evidence.
  **Classification:** scope/provenance-wrong; non-runtime-blocking but
  decision-blocking for creative-quality claims.
- Real-AI-previz aggregation could use partial-repeat timing as if it were a
  fully successful provider result, and old result files point to generated
  project directories that are no longer retained. **Classification:**
  harness/evidence-wrong; provider-decision-blocking.
- Full-script throughput summaries did not fingerprint the manifest, runner,
  support code, or fixtures; six retained summaries point to absent generated
  projects and three registry rows point to missing ignored run-state files.
  **Classification:** evidence-provenance-wrong; historical context only.
- The Story 141 probe used a stale prompt-compiler import and made a paid judge
  part of the default path. Browser probes tolerated too many transport/UI
  failures or silently selected local projects. **Classification:** local-code
  harness-wrong; no historical creative or UX claim promoted.
- Two fixture directories contained six files with no maintained test
  references. The Liberty Church production capture was stored below test
  fixtures despite intentionally preserving known semantic contamination.
  **Classification:** dead-fixture authority and scope-wrong.
- A broad integration rerun exposed a product heuristic defect: `.pdf` and
  `.docx` received a `0.35` screenplay prior even without screenplay structure,
  allowing harmless OCR variation to flip a public-domain patent from prose to
  screenplay. **Classification:** local-code/model-selection-wrong at ingest;
  fixed from the source-backed regression fixture.

## Repair and Evidence

- Runtime media/final-output v2 manifests now declare matching, deliberate
  mismatch, or structural-only intent and hash the selected clip and target.
  Future results also hash the manifest, runner, and support code. Every pre-v2
  score is marked contaminated and non-decision-grade.
- Real-AI-previz summaries now separate full from partial success, disclose the
  timing basis, score any incomplete selected matrix at zero, and block provider decisions
  unless every selected aggregate fully succeeds. All old score rows are marked
  superseded and non-decision-grade.
- Full-script throughput now fails on missing fixtures or recipes, fingerprints every
  fixture and recipe contract, and records successful/failed project retention. Old
  rows remain explicitly non-decision-grade; missing paths are classified
  unavailable rather than silently accepted.
- The post-rollout breakdown runner retrieves normal API artifacts and pins the
  Open Frequency title, ordered headings, scene count, named-character facts,
  radio/storm/shelter facts, and minimum character/location coverage.
- Live capability smoke refuses to call providers without `--run-live`, labels
  results access/callability evidence only, and probes the shipped
  `gemini-3.5-flash-lite` text default without deprecated sampling controls.
- Story 141 judge execution is opt-in, uses current prompt compilation, and has
  a sidecar that prevents the one synthetic historical result from being used
  as current creative-quality evidence.
- The generic UI probe covers desktop/mobile modes and fails on console, page,
  request, and HTTP errors. Story 157/180 require explicit project inputs.
  Story 099 remains documented as historical and nonportable.
- All direct ingest fixtures are source-registered. The six orphan files were
  deleted. Small normalization/lightweight fixtures disclose their scope. The
  Liberty Church snapshot is explicitly quarantined as historical forensics.
- PDF/DOCX receive a screenplay prior only when actual screenplay structure is
  present; a technical-prose adversarial unit case and the real scanned patent
  integration case cover the boundary.
- A final worktree-bound rerun exposed an import-truth false green: the shared
  virtualenv's editable install could import the canonical checkout instead of
  this branch. Required closeout commands now force `PYTHONPATH=src`, and the
  repaired modules pass through that exact boundary.
- ScriptBible fixture provenance now pins both the raw source hash and the
  canonical normalized prompt-source hash. Fixture selection compares the exact
  screenplay slice passed to the prompt, rejects appended source, and remains
  valid when normal normalization reorders title metadata or blank lines.
- PDF reflow now rejects sentence-case two-column tables as well as uppercase
  tables, requires screenplay-shaped preceding context, and stops dialogue at
  unspaced transitions or scene headings. Direct regressions cover both table
  and boundary cases.
- The relationship capability/runtime schema separation remains sound, but the
  name-only runtime still forces 3-5 links without source evidence. That is a
  documented semantic/runtime-selection limitation, not a fixed quality lane.
- `docs/evals/story-208-contract-manifest-v1.json` freezes the final selected
  runner, fixture, source, scorer, registry, and ledger contracts by bytes and
  SHA-256; it remains explicitly provisional while uncommitted.

## Evidence Identity

- Runtime media manifest SHA-256:
  `2d376e9ef6b61df3cfa11d73ac34173fefe7b4581008146cc36fdb5e903c2503`
- Runtime final-output manifest SHA-256:
  `8b0e3fa2901ea1de12b51dfbc687942a545dfef6f28e739e088628c0ef07ebd4`
- Full-script manifest SHA-256:
  `66b859011fcf9ef2d9772c0df93bf73c32bc898e142a772327ee9351f0f92ef9`
- Real-AI-previz manifest SHA-256:
  `12c58344d0bdd38621c2a6088f7cd61aaf5a666394eefc6f7b2089df0d18e78e`
- Open Frequency source SHA-256:
  `81508ec3a2be376efbc8f8d720dea2784eec5dba3664372df3f65123f8684d95`
- Patent PDF source SHA-256:
  `76fae677e64a18b51903b6a320ec16f6324475f2cdfd9e3a6ef3321053794c56`
- Current Story 141 runner SHA-256:
  `b9d71a28b140ebc8347218db85e7d8e7339c3c063a27cf96003bcaade62ea58f`
- Current generic UI probe SHA-256:
  `143e33d3edce96268143baa67d8d1efec8cc2a8e39fd801adf39bc7928abd774`

These are dirty-worktree identities for audit reproduction, not substitutes for
the final landed commit SHA. Future runtime result payloads compute their own
contract hashes at execution time.

## Validation

- Combined focused regression: 59 tests passed.
- Integration suite: 70 selected, 66 passed, 4 explicit skips (three
  `CINE_FORGE_LIVE_TESTS`, one `CINE_FORGE_PDF_EXPORT_TESTS`).
- Advertised path-scoped smoke suite: 1 passed.
- UI Node suite: 21 passed.
- Registry consistency and truth-ledger structural checks passed.
- Ruff, JavaScript syntax checking, and `git diff --check` passed for this slice.
- No paid/live/provider call was made.

## Conclusion

**Result:** succeeded
**Score before:** N/A - this pass repaired evidence authority, not model output
**Score after:** N/A - contaminated history was not rescored
**Latency before:** N/A
**Latency after:** N/A
**Cost before:** $0 new provider spend
**Cost after:** $0 new provider spend

**What worked:** Source-bound fixtures, fail-closed partial-success semantics,
runtime contract hashes, explicit live-call flags, and terminal
non-decision-grade classifications removed false authority without buying new
model evidence.

**What failed:** Historical generated project roots were not retained, so old
previz and throughput decisions cannot be reconstructed from their summaries.

**What NOT to retry:** Do not rerun paid lanes merely to replace an invalid old
number before the repaired contract and retention path are the actual execution
surface. Do not use synthetic answer overlays, repeated clips, mocked response
packs, browser smoke success, or production forensic snapshots as model-quality
evidence.

**Retry state:** open

**Retry when:** Run each live lane only when its owning story needs a current
decision and can retain the complete source-bound evidence packet. Real-AI
previz requires a fully successful matrix; runtime media/final-output require v2
clips and targets; throughput requires retained project roots; Story 141
creative claims require a focused AI-as-tester conversation rather than the old
single synthetic judge.

## Definition of Done Checklist

- [x] Read the prior repository-truth attempts relevant to this surface
- [x] Classified every significant mismatch and its runtime/default impact
- [x] Preserved invalid historical measurements with explicit evidence status
- [x] Added deterministic adversarial and provenance regressions
- [x] Recorded exact dirty-worktree fixture/runner identities
- [x] Updated the eval registry and repository truth ledger
- [x] Ran offline validation without provider calls
- [x] Did not change a production model default from contaminated evidence
