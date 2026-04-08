# Real AI Previz Runtime Eval

- Measured at: 2026-04-08T18:16:32.928091+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Successful cases: 3 / 3
- Fastest scene-ready case: `shipped_lite_8_scene_ready`
- Fastest scene-ready total runtime: 270922 ms
- Fastest scene-ready prerequisites: 97846 ms
- Fastest scene-ready AI-previz recipe: 173076 ms
- Fastest total case: `fast_4_mvp_ingest_only`
- Fastest total elapsed: 124929 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Success | Notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| shipped_lite_8_scene_ready | shipped | google_veo31_lite / 8s 1280x720 | scene_ready | 173076 | 270922 | yes | Current shipped recipe and honest scene-ready prerequisite chain. Recovered from completed run states after summary-write path bug. |
| fast_4_scene_ready | patched | google_veo31_fast / 4s 720p | scene_ready | 248767 | 353687 | yes | Low-latency Fast pack candidate on the honest scene-ready path. Recovered from completed run states after summary-write path bug. |
| fast_4_mvp_ingest_only | patched | google_veo31_fast / 4s 720p | mvp_ingest_only | 102791 | 124929 | yes | Best-case Fast runtime with minimal prerequisites. Recovered from completed run states after summary-write path bug. |
