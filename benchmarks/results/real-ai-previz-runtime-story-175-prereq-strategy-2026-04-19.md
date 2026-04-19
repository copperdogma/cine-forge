# Real AI Previz Runtime Eval

- Measured at: 2026-04-19T06:50:09.017556+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Fastest scene-ready case: `shipped_lite_4_scene_ready`
- Fastest scene-ready time to first playable: 194199 ms
- Fastest scene-ready prerequisites: 140342 ms
- Fastest scene-ready AI-previz recipe: 53857 ms
- Fastest scene-ready full completion: 198376 ms
- Fastest scene-ready post-playable overhead: 4177 ms
- Fastest isolated scene-ready AI-previz case: `shipped_lite_4_scene_ready`
- Fastest isolated scene-ready AI-previz median: 53857 ms
- Fastest total case: `shipped_lite_4_mvp_ingest_only`
- Fastest total elapsed: 102968 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Strategy | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| shipped_lite_4_mvp_ingest_only | 1/1 | shipped | one_pass_previz_prep | google_veo31_lite / 4s 720p | standard | mvp_ingest_only (45801 ms) | 53739 | 99540 | 102968 | 3428 | yes | Story 175 simplification baseline: MVP ingest plus a single on-demand shot-planning pass, without the full creative_direction chain. |
| shipped_lite_4_scene_ready | 1/1 | shipped | full_scene_ready_chain | google_veo31_lite / 4s 720p | standard | scene_ready (140342 ms) | 53857 | 194199 | 198376 | 4177 | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
