# Real AI Previz Runtime Eval

- Measured at: 2026-04-09T05:16:29.760709+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_shot_planning_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Fastest scene-ready case: `xai_4_480p_scene_ready`
- Fastest scene-ready total runtime: 130399 ms
- Fastest scene-ready prerequisites: 107764 ms
- Fastest scene-ready AI-previz recipe: 22635 ms
- Fastest isolated scene-ready AI-previz case: `xai_4_480p_scene_ready`
- Fastest isolated scene-ready AI-previz median: 22635 ms
- Fastest total case: `xai_4_480p_mvp_ingest_only`
- Fastest total elapsed: 65552 ms
- Fast target: <= 6000 ms to first real scene-ready `ai_previz_video`

## Cases

| Case | Attempts | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Total range | Success | Notes |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| xai_4_480p_mvp_ingest_only | 1/1 | patched | xai_grok_imagine_video / 4s 480p | mvp_ingest_only (43865 ms) | 21687 | 65552 | 65552-65552 ms | yes | Benchmark-first xAI Grok Imagine candidate with minimal prerequisites. |
| xai_4_480p_scene_ready | 1/1 | patched | xai_grok_imagine_video / 4s 480p | scene_ready (107764 ms) | 22635 | 130399 | 130399-130399 ms | yes | Benchmark-first xAI Grok Imagine candidate on the honest scene-ready path. |
