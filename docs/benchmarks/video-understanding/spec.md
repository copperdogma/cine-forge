# Video Understanding Benchmark Spec

## Purpose

Story 030 measures how well candidate multimodal models can read **generated scene outputs** at a director-facing level. The benchmark is not trying to replace public general-video benchmarks. It is deliberately tuned to CineForge's generated-output QA path.

## V1 Boundary

V1 uses a **clip packet**:

- `clip.mp4` for operator inspection
- five evenly spaced sampled frames under `frames/`
- technical metadata from `meta.json`
- optional transcript and audio-description fields from `meta.json`

This is a conscious compromise. It gives OpenAI, Anthropic, and Gemini a fair, comparable input surface today. It also keeps the benchmark reproducible without depending on whichever provider exposes the best raw-video API first.

Audio intent is in scope in v1. **True lip-sync validation is not.** That needs licensed human-footage clips or a trustworthy face-animation fixture, not synthetic previz abstractions.

## Files

- Dataset root: `benchmarks/video_understanding/`
- Task config: `benchmarks/tasks/video-understanding.yaml`
- Prompt: `benchmarks/prompts/video-understanding.txt`
- Provider: `benchmarks/providers/video_understanding_provider.py`
- Scorer: `benchmarks/scorers/video_understanding_scorer.py`
- Report generator: `benchmarks/scripts/video_understanding_report.py`
- Schemas: `src/cine_forge/schemas/video_analysis.py`

## Schema Contract

The benchmark uses three grouped schemas:

- `VideoAnalysisTarget`
  - normalized gold reference per clip
  - weighted scoring profile
  - continuity state, audio intent, and required summary keywords
- `VideoAnalysisPrediction`
  - model output contract returned by the prompt
  - controlled vocab for tone, emotion, color, camera, motion, and audio
  - timestamped evidence snippets
- `VideoAnalysisScore`
  - deterministic comparison record
  - per-dimension scores, weighted overall score, hard-constraint status, and uncertainty

## Scoring Dimensions

Deterministic scorer dimensions:

- `summary`
- `tone`
- `emotion`
- `color`
- `camera`
- `motion`
- `continuity`
- `audio`
- `evidence`
- `hard_constraints` as a non-weighted gate

Default weights sum to 1.0:

- `summary`: 0.18
- `tone`: 0.14
- `emotion`: 0.12
- `color`: 0.10
- `camera`: 0.12
- `motion`: 0.10
- `continuity`: 0.12
- `audio`: 0.08
- `evidence`: 0.04

## Prompt / Output Policy

The prompt requires one strict JSON object with:

- short summary
- controlled-vocabulary tags
- continuity state plus notes
- audio notes
- 2-4 timestamped evidence items
- overall confidence

No chain-of-thought is requested or persisted.

## Evaluation Protocol

1. Run deterministic scorer on every response.
2. Run Opus 4.6 semantic rubric judging against `target.md`.
3. Average deterministic + rubric scores for the headline quality number.
4. Generate a report artifact from the promptfoo result file.
5. Update `docs/evals/registry.yaml` after every actual eval run.

## Optional Pairwise Ranking Mode

If two candidate models land within `0.02` overall on the anchor subset, rerun the
saved outputs through a pairwise judge prompt before flipping defaults. This is an
optional tiebreaker, not the default v1 path.

## Pilot-First Rule

Before a full 20-clip matrix rerun:

1. Run the anchor subset first.
2. Confirm the scorer separates obvious wins from obvious misses.
3. Tighten the rubric or target data if it does not.
4. Only then scale to the full 20-clip run.

## Current Candidate Models

V1 task config currently ships with:

- `GPT-5.4`
- `Claude Sonnet 4.6`
- `Gemini 2.5 Pro`
- `Gemini 2.5 Flash`
- `Gemini 3.1 Pro Preview`
- `Gemini 3 Flash Preview`

The core comparison set remains one current OpenAI frontier multimodal model, one
Anthropic vision model, and the Google 2.5 video-capable tiers. The extra Google 3.x
slots are challenge controls added after the 2.5 rerun underperformed and a user
requested a direct check of the newer Gemini line on the same frame-packet harness.

## Output Artifacts

Primary durable outputs:

- promptfoo result JSON under `benchmarks/results/`
- derived benchmark report (`*-report.json` and `*-report.md`)
- eval registry entry under `docs/evals/registry.yaml`

The benchmark does **not** write into the runtime artifact store in v1.
