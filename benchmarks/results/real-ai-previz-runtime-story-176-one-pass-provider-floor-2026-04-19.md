# Real AI Previz Runtime Eval

- Measured at: 2026-04-19T18:02:25.818260+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 3 / 3
- Fully successful cases: 3 / 3
- Focus prerequisite mode: `mvp_ingest_only`
- Fastest mvp ingest only case: `shipped_xai_4_480p_mvp_ingest_only`
- Fastest mvp ingest only time to first playable: 65514 ms
- Fastest mvp ingest only prerequisites: 47865 ms
- Fastest mvp ingest only AI-previz recipe: 17649 ms
- Fastest mvp ingest only full completion: 82137 ms
- Fastest mvp ingest only post-playable overhead: 16623 ms
- Fastest isolated mvp ingest only AI-previz case: `shipped_xai_4_480p_mvp_ingest_only`
- Fastest isolated mvp ingest only AI-previz median: 17649 ms
- Fastest total case: `shipped_xai_4_480p_mvp_ingest_only`
- Fastest total elapsed: 82137 ms
- Fast target: <= 6000 ms to first real mvp ingest only `ai_previz_video`

## Cases

| Case | Attempts | Mode | Strategy | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| fast_4_mvp_ingest_only | 1/1 | patched | one_pass_previz_prep | google_veo31_fast / 4s 720p | standard | mvp_ingest_only (47865 ms) | 52788 | 100653 | 107667 | 7014 | yes | Best-case Fast runtime with minimal prerequisites. |
| lite_4_mvp_ingest_only_control | 1/1 | patched | one_pass_previz_prep | google_veo31_lite / 4s 720p | standard | mvp_ingest_only (47865 ms) | 53064 | 100929 | 105506 | 4577 | yes | Former shipped Lite 4 one-pass lane retained as a post-Story-176 control after the xAI ship switch. |
| shipped_xai_4_480p_mvp_ingest_only | 1/1 | shipped | one_pass_previz_prep | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (47865 ms) | 17649 | 65514 | 82137 | 16623 | yes | Story 176 shipped baseline: MVP ingest plus a single on-demand shot-planning pass routed through xAI Grok Imagine without the full creative_direction chain. |
