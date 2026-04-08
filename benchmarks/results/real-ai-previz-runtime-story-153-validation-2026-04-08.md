# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T20:56:56.108558+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Successful cases: 8 / 8
- Fastest scene-ready case: `veo31_4_scene_ready`
- Fastest scene-ready total runtime: 166188 ms
- Fastest scene-ready prerequisites: 68803 ms
- Fastest scene-ready AI-previz recipe: 97385 ms
- Fastest total case: `fast_4_mvp_ingest_only`
- Fastest total elapsed: 100956 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Success | Notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| shipped_lite_4_scene_ready | shipped | google_veo31_lite / 4s 720p | scene_ready | 111914 | 221845 | yes | Current shipped recipe and honest scene-ready prerequisite chain after Story 153. |
| shipped_lite_4_mvp_ingest_only | shipped | google_veo31_lite / 4s 720p | mvp_ingest_only | 80056 | 150641 | yes | Separates creative-direction overhead from the shipped AI-previz runtime after Story 153. |
| lite_8_scene_ready_control | patched | google_veo31_lite / 8s 1280x720 | scene_ready | 118234 | 188707 | yes | Pre-Story-153 shipped Lite control retained for regression comparison. |
| lite_8_mvp_ingest_only_control | patched | google_veo31_lite / 8s 1280x720 | mvp_ingest_only | 80838 | 153584 | yes | Pre-Story-153 shipped Lite ingest-only control retained for regression comparison. |
| fast_4_scene_ready | patched | google_veo31_fast / 4s 720p | scene_ready | 95434 | 180362 | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| fast_4_mvp_ingest_only | patched | google_veo31_fast / 4s 720p | mvp_ingest_only | 81725 | 100956 | yes | Best-case Fast runtime with minimal prerequisites. |
| veo31_4_scene_ready | patched | google_veo31 / 4s 720p | scene_ready | 97385 | 166188 | yes | Full Veo pack retained as a control for reachability, not as the favored fast path. |
| veo31_4_mvp_ingest_only | patched | google_veo31 / 4s 720p | mvp_ingest_only | 81397 | 153607 | yes | Best-case full Veo runtime with minimal prerequisites. |
