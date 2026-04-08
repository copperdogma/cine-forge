# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T21:45:06.602662+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_shot_planning_substrate`
- Repeat count: 1
- Successful cases: 4 / 4
- Fully successful cases: 4 / 4
- Fastest scene-ready case: `shipped_lite_4_scene_ready`
- Fastest scene-ready total runtime: 125714 ms
- Fastest scene-ready prerequisites: 88099 ms
- Fastest scene-ready AI-previz recipe: 37615 ms
- Fastest isolated scene-ready AI-previz case: `shipped_lite_4_scene_ready`
- Fastest isolated scene-ready AI-previz median: 37615 ms
- Fastest total case: `shipped_lite_4_scene_ready`
- Fastest total elapsed: 125714 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Total range | Success | Notes |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| fast_4_scene_ready | 1/1 | patched | google_veo31_fast / 4s 720p | scene_ready (88099 ms) | 57186 | 145285 | 145285-145285 ms | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| lite_8_scene_ready_control | 1/1 | patched | google_veo31_lite / 8s 1280x720 | scene_ready (88099 ms) | 60857 | 148956 | 148956-148956 ms | yes | Pre-Story-153 shipped Lite control retained for regression comparison. |
| shipped_lite_4_scene_ready | 1/1 | shipped | google_veo31_lite / 4s 720p | scene_ready (88099 ms) | 37615 | 125714 | 125714-125714 ms | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
| veo31_4_scene_ready | 1/1 | patched | google_veo31 / 4s 720p | scene_ready (88099 ms) | 50828 | 138927 | 138927-138927 ms | yes | Full Veo pack retained as a control for reachability, not as the favored fast path. |
