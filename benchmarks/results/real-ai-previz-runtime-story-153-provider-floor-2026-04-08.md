# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T20:21:19.474657+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Successful cases: 8 / 8
- Fastest scene-ready case: `lite_4_scene_ready`
- Fastest scene-ready total runtime: 146281 ms
- Fastest scene-ready prerequisites: 59734 ms
- Fastest scene-ready AI-previz recipe: 86547 ms
- Fastest total case: `lite_4_mvp_ingest_only`
- Fastest total elapsed: 112143 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Success | Notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| shipped_lite_8_scene_ready | shipped | google_veo31_lite / 8s 1280x720 | scene_ready | 132375 | 184926 | yes | Current shipped recipe and honest scene-ready prerequisite chain. |
| shipped_lite_8_mvp_ingest_only | shipped | google_veo31_lite / 8s 1280x720 | mvp_ingest_only | 88963 | 123202 | yes | Separates creative-direction overhead from the shipped AI-previz runtime. |
| lite_4_scene_ready | patched | google_veo31_lite / 4s 720p | scene_ready | 86547 | 146281 | yes | Fastest reachable Lite settings while preserving the scene-ready path. |
| lite_4_mvp_ingest_only | patched | google_veo31_lite / 4s 720p | mvp_ingest_only | 68434 | 112143 | yes | Best-case Lite runtime with minimal prerequisites. |
| fast_4_scene_ready | patched | google_veo31_fast / 4s 720p | scene_ready | 123054 | 182737 | yes | Low-latency Fast pack candidate on the honest scene-ready path. |
| fast_4_mvp_ingest_only | patched | google_veo31_fast / 4s 720p | mvp_ingest_only | 67118 | 141052 | yes | Best-case Fast runtime with minimal prerequisites. |
| veo31_4_scene_ready | patched | google_veo31 / 4s 720p | scene_ready | 83005 | 191178 | yes | Full Veo pack retained as a control for reachability, not as the favored fast path. |
| veo31_4_mvp_ingest_only | patched | google_veo31 / 4s 720p | mvp_ingest_only | 78340 | 155492 | yes | Best-case full Veo runtime with minimal prerequisites. |
