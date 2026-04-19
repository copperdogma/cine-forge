# Real AI Previz Runtime Eval

- Measured at: 2026-04-19T04:48:21.672546+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_shot_planning_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Fastest scene-ready case: `lite_4_compact_scene_ready`
- Fastest scene-ready time to first playable: 186659 ms
- Fastest scene-ready prerequisites: 133291 ms
- Fastest scene-ready AI-previz recipe: 53368 ms
- Fastest scene-ready full completion: 190622 ms
- Fastest scene-ready post-playable overhead: 3963 ms
- Fastest isolated scene-ready AI-previz case: `lite_4_compact_scene_ready`
- Fastest isolated scene-ready AI-previz median: 53368 ms
- Fastest total case: `lite_4_compact_scene_ready`
- Fastest total elapsed: 190622 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| lite_4_compact_scene_ready | 1/1 | patched | google_veo31_lite / 4s 720p | compact | scene_ready (133291 ms) | 53368 | 186659 | 190622 | 3963 | yes | Bounded Story 174 candidate that keeps the shipped Lite lane but compacts the previz prompt contract. |
| shipped_lite_4_scene_ready | 1/1 | shipped | google_veo31_lite / 4s 720p | standard | scene_ready (133291 ms) | 53973 | 187264 | 192474 | 5210 | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
