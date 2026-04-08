# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T18:53:37.592114+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Successful cases: 3 / 3
- Fastest scene-ready case: `shipped_lite_8_scene_ready`
- Fastest scene-ready total runtime: 153528 ms
- Fastest scene-ready prerequisites: 54880 ms
- Fastest scene-ready AI-previz recipe: 98648 ms
- Fastest total case: `fast_4_mvp_ingest_only`
- Fastest total elapsed: 143510 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Success | Notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| shipped_lite_8_scene_ready | shipped | google_veo31_lite / 8s 1280x720 | scene_ready | 98648 | 153528 | yes | Current shipped recipe and honest scene-ready prerequisite chain. |
| fast_4_scene_ready | patched | google_veo31_fast / 4s 720p | scene_ready | 74638 | 182138 | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| fast_4_mvp_ingest_only | patched | google_veo31_fast / 4s 720p | mvp_ingest_only | 68159 | 143510 | yes | Best-case Fast runtime with minimal prerequisites. |
