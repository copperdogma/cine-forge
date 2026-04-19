# Real AI Previz Runtime Eval

- Measured at: 2026-04-19T16:40:21.837877+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Fastest scene-ready case: `shipped_lite_4_scene_ready`
- Fastest scene-ready time to first playable: 209021 ms
- Fastest scene-ready prerequisites: 156144 ms
- Fastest scene-ready AI-previz recipe: 52877 ms
- Fastest scene-ready full completion: 213747 ms
- Fastest scene-ready post-playable overhead: 4726 ms
- Fastest isolated scene-ready AI-previz case: `shipped_lite_4_scene_ready`
- Fastest isolated scene-ready AI-previz median: 52877 ms
- Fastest total case: `shipped_lite_4_mvp_ingest_only`
- Fastest total elapsed: 105702 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Strategy | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| shipped_lite_4_mvp_ingest_only | 1/1 | shipped | one_pass_previz_prep | google_veo31_lite / 4s 720p | standard | mvp_ingest_only (44048 ms) | 52773 | 96821 | 105702 | 8881 | yes | Story 175 simplification baseline: MVP ingest plus a single on-demand shot-planning pass, without the full creative_direction chain. |
| shipped_lite_4_scene_ready | 1/1 | shipped | full_scene_ready_chain | google_veo31_lite / 4s 720p | standard | scene_ready (156144 ms) | 52877 | 209021 | 213747 | 4726 | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
