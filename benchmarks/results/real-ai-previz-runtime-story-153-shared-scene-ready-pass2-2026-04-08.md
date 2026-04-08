# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T21:40:04.423214+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_shot_planning_substrate`
- Repeat count: 1
- Successful cases: 4 / 4
- Fully successful cases: 4 / 4
- Fastest scene-ready case: `fast_4_scene_ready`
- Fastest scene-ready total runtime: 132510 ms
- Fastest scene-ready prerequisites: 92314 ms
- Fastest scene-ready AI-previz recipe: 40196 ms
- Fastest isolated scene-ready AI-previz case: `fast_4_scene_ready`
- Fastest isolated scene-ready AI-previz median: 40196 ms
- Fastest total case: `fast_4_scene_ready`
- Fastest total elapsed: 132510 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Total range | Success | Notes |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| fast_4_scene_ready | 1/1 | patched | google_veo31_fast / 4s 720p | scene_ready (92314 ms) | 40196 | 132510 | 132510-132510 ms | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| lite_8_scene_ready_control | 1/1 | patched | google_veo31_lite / 8s 1280x720 | scene_ready (92314 ms) | 63187 | 155501 | 155501-155501 ms | yes | Pre-Story-153 shipped Lite control retained for regression comparison. |
| shipped_lite_4_scene_ready | 1/1 | shipped | google_veo31_lite / 4s 720p | scene_ready (92314 ms) | 50320 | 142634 | 142634-142634 ms | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
| veo31_4_scene_ready | 1/1 | patched | google_veo31 / 4s 720p | scene_ready (92314 ms) | 58533 | 150847 | 150847-150847 ms | yes | Full Veo pack retained as a control for reachability, not as the favored fast path. |
