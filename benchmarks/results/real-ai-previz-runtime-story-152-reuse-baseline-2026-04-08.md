# Real AI Previz Runtime Reuse Baseline

- Measured at: 2026-04-08T19:13:49Z
- Story: `152`
- Baseline project: `output/eval-real-ai-previz-fast_4_mvp_ingest_only-fe36ed`
- Comparison: full AI-previz regeneration versus regeneration sliced to `start_from=ai_previz`

## Result

- Full regen (`story152-regen-full-baseline`): `81545 ms`
- Reuse regen (`story152-regen-start-baseline`): `75337 ms`
- Wall-clock delta: `6208 ms` faster with reuse
- Removed stage cost: `shot_planning=20964 ms`

## Stage Detail

| Run | Stage order | Stage durations |
| --- | --- | --- |
| `story152-regen-full-baseline` | `timeline -> tracks -> shot_planning -> ai_previz -> validate_media` | `timeline=5 ms`, `tracks=4 ms`, `shot_planning=20964 ms`, `ai_previz=53838 ms`, `validate_media=6704 ms` |
| `story152-regen-start-baseline` | `ai_previz -> validate_media` | `ai_previz=53618 ms`, `validate_media=21693 ms` |

## Interpretation

The reuse path is structurally correct: it skips `shot_planning` entirely and goes straight to provider video generation plus validation. On this sampled honest project state, that translated into a modest `6208 ms` wall-clock gain rather than the full `20964 ms` shot-planning cost because `validate_media` was noisier on the sliced run. This is still useful substrate evidence for Story 152, but it does not remove Story 149's runtime blocker on its own.
