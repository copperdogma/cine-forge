# Story 030: Generated Output QA (Video Understanding Benchmark)

**Status**: In Progress
**Created**: 2026-02-12
**Spec Refs**: 2.4 (AI-Driven), 2.7 (Cost Transparency), 2.8 (QA), 19 (Memory Model), Phase 7 Story 030 (Generated Output QA)
**Depends On**: Story 005 (scene extraction artifacts), Story 012 (timeline artifacts), Story 021 (visual direction), Story 022 (sound direction), Story 028 (render adapter), Story 032 (cost tracking)

---

## Goal

Define and implement a repeatable benchmark that measures how well candidate multimodal models understand film/video at director-level depth, then use it to pick the best cost/quality model over time.

The benchmark should cover tone, emotion, detail fidelity, continuity, color grading, motion, shot language, audio intent, and lip-sync alignment. It should support periodic reruns so CineForge can switch to a better model when the measured quality gain justifies cost.

## Acceptance Criteria

### Benchmark Discovery and Gap Analysis
- [ ] Survey existing public benchmarks for video understanding and film-language understanding, including at least: Video-MME, MVBench, TempCompass, MLVU, LongVideoBench, and one film-critic or cinematic-analysis oriented dataset if available.
- [ ] Produce a comparison matrix at `docs/benchmarks/video-understanding/landscape.md` with:
  - [ ] What each benchmark measures.
  - [ ] Modalities covered (visual-only, audiovisual, temporal, dialogue-aware).
  - [ ] Whether it captures director-level dimensions (tone, continuity, cinematography, color, lip-sync).
  - [ ] Licensing and feasibility for internal evaluation use.
  - [ ] Identified gaps vs CineForge needs.
- [ ] Explicitly conclude one of:
  - [ ] Existing benchmark is sufficient and should be adopted directly, or
  - [ ] Existing benchmark is insufficient and a CineForge benchmark is required.

### CineForge Benchmark Spec (if new benchmark is required)
- [ ] Create `docs/benchmarks/video-understanding/spec.md` defining:
  - [ ] Target dimensions and scoring rubrics.
  - [ ] Clip duration constraints and allowed codecs.
  - [ ] Ground-truth format schema (markdown + JSON sidecar).
  - [ ] Evaluation protocol (single-pass, multi-pass, chain-of-thought policy, deterministic settings).
  - [ ] Judge policy for artistic variance and non-exact matches.
- [ ] Add schema definitions:
  - [ ] `src/cine_forge/schemas/video_analysis_target.py`
  - [ ] `src/cine_forge/schemas/video_analysis_prediction.py`
  - [ ] `src/cine_forge/schemas/video_analysis_score.py`
- [ ] Register schemas in `src/cine_forge/schemas/registry.py`.

### Dataset and Gold Annotations
- [ ] Create dataset scaffold at `benchmarks/video_understanding/`.
- [ ] Define standardized per-clip files:
  - [ ] `clip.mp4` (source segment)
  - [ ] `target.md` (human-authored analysis)
  - [ ] `target.json` (schema-valid normalized form)
  - [ ] `meta.json` (source, rights, duration, tags)
- [ ] Create at least 20 seed clips spanning:
  - [ ] Dialogue-heavy scenes.
  - [ ] Action/motion-heavy scenes.
  - [ ] Quiet emotional scenes.
  - [ ] High continuity complexity scenes.
  - [ ] Stylized color-grade scenes.
- [ ] Add an annotation guideline at `docs/benchmarks/video-understanding/annotation-guide.md`.

### Model Runner and Prompt Contracts
- [ ] Implement benchmark runner module at `src/cine_forge/modules/qa/video_understanding_benchmark_v1/`.
- [ ] Support model adapters for at least 3 candidate multimodal models.
- [ ] Define stable prompt contract at `prompts/video_analysis_v1.md`.
- [ ] Persist each model output as immutable artifacts with cost and latency metadata.
- [ ] Ensure run fingerprints include model id/version and prompt version to avoid stale reuse.

### AI-as-Judge Evaluation
- [ ] Implement judge module that compares `prediction` vs `target` and outputs:
  - [ ] Per-dimension score.
  - [ ] Weighted overall score.
  - [ ] Confidence interval or uncertainty signal.
  - [ ] Structured rationale with cited evidence snippets.
- [ ] Add guardrails:
  - [ ] Judge model must be configurable and version-pinned.
  - [ ] Secondary deterministic checks for hard constraints (e.g., lip-sync mismatch obvious cases, continuity conflicts).
  - [ ] Optional pairwise ranking mode to reduce score drift.
- [ ] Validate judge outputs against score schema.

### Reporting and Model Selection
- [ ] Generate report artifact `video_benchmark_report_v1` containing:
  - [ ] Leaderboard by overall quality.
  - [ ] Dimension-level strengths/weaknesses.
  - [ ] Cost-per-point metric.
  - [ ] Recommendation (`adopt`, `hold`, `retest`) with rationale.
- [ ] Add trend tracking to compare current run vs previous runs.
- [ ] Document decision threshold for model switching in `docs/benchmarks/video-understanding/model-selection-policy.md`.

### Tests and Validation
- [ ] Unit tests for schemas and scoring aggregation.
- [ ] Unit tests for runner prompt contract and parser robustness.
- [ ] Integration test with fixture clips and mocked model outputs.
- [ ] `make test-unit` passes.
- [ ] `make lint` passes.

## Design Notes

### Why Existing Benchmarks May Be Insufficient

Most public video benchmarks optimize for question answering, action recognition, or broad temporal reasoning. CineForge needs director-facing understanding quality: emotional arc, cinematographic intent, continuity coherence, and audio-visual alignment. This story validates whether existing datasets cover that depth before building anything new.

### Ground Truth Format

Use a two-layer gold format:
1. Human-readable `target.md` for nuanced reasoning and film language.
2. Normalized `target.json` for deterministic scoring and schema validation.

This keeps authoring practical while preserving machine-verifiable evaluation.

### Judge Strategy

AI-as-judge is acceptable for soft dimensions (tone, emotion, intent) only when combined with explicit rubrics, version pinning, and hard-rule validators for objective constraints (continuity contradictions, timing mismatches, lip-sync checks).

## Tasks

- [ ] Resolve benchmark landscape and licensing feasibility.
- [ ] Decide reuse vs build for CineForge benchmark.
- [ ] Write benchmark spec and scoring rubric.
- [ ] Implement benchmark schemas and register them.
- [ ] Build dataset scaffold and annotation guidelines.
- [ ] Populate first 20 gold clips and analyses.
- [ ] Implement runner module for 3+ models.
- [ ] Implement judge module with hard-rule validators.
- [ ] Add report generation and model-switch recommendation policy.
- [ ] Add unit and integration tests.
- [ ] Run `make test-unit`.
- [ ] Run `make lint`.
- [ ] Execute first benchmark dry run and inspect output artifacts.
- [ ] Update `docs/stories.md` status/details if scope or sequencing changes.

## Notes

- This story should prioritize measurement quality and repeatability over broad benchmark size at first pass.
- Rights/licensing for movie clips must be addressed before scaling dataset size.
- Initial dataset can use short internal clips or licensed/public-domain material for development while legal policy is finalized.

## Work Log

### 20260212-1421 — Created Story 030 document scaffold
- **Result:** Success.
- **Notes:** Added full house-format story file with status, goal, acceptance criteria, design notes, actionable checklist, and initial benchmark scope aligned to generated-output QA.
- **Next:** Confirm benchmark discovery findings and decide whether to adopt an existing benchmark or build CineForge-specific benchmark.

### 20260212-1421 — Checklist verification and expansion
- **Result:** Success.
- **Notes:** Ensured `## Tasks` exists with explicit checkbox items covering research, schema work, runner/judge implementation, reporting, validation, and test execution; no pre-existing tasks were removed because file was newly created.
- **Next:** Begin discovery pass against known video-understanding benchmarks and record gap analysis in `docs/benchmarks/video-understanding/landscape.md`.
