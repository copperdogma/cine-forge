# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T22:02:28.987330+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_shot_planning_substrate`
- Repeat count: 1
- Successful cases: 4 / 4
- Fully successful cases: 4 / 4
- Fastest scene-ready case: `fast_4_scene_ready`
- Fastest scene-ready total runtime: 184313 ms
- Fastest scene-ready prerequisites: 137106 ms
- Fastest scene-ready AI-previz recipe: 47207 ms
- Fastest isolated scene-ready AI-previz case: `fast_4_scene_ready`
- Fastest isolated scene-ready AI-previz median: 47207 ms
- Fastest total case: `fast_4_scene_ready`
- Fastest total elapsed: 184313 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Total range | Success | Notes |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| fast_4_scene_ready | 1/1 | patched | google_veo31_fast / 4s 720p | scene_ready (137106 ms) | 47207 | 184313 | 184313-184313 ms | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| lite_8_scene_ready_control | 1/1 | patched | google_veo31_lite / 8s 1280x720 | scene_ready (137106 ms) | 71019 | 208125 | 208125-208125 ms | yes | Pre-Story-153 shipped Lite control retained for regression comparison. |
| shipped_lite_4_scene_ready | 1/1 | shipped | google_veo31_lite / 4s 720p | scene_ready (137106 ms) | 62274 | 199380 | 199380-199380 ms | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
| veo31_4_scene_ready | 1/1 | patched | google_veo31 / 4s 720p | scene_ready (137106 ms) | 47964 | 185070 | 185070-185070 ms | yes | Full Veo pack retained as a control for reachability, not as the favored fast path. |
