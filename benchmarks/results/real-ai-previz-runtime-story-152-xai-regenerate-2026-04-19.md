# Real AI Previz Runtime Eval

- Measured at: 2026-04-19T20:10:38.875626+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Focus prerequisite mode: `mvp_ingest_only`
- Fastest mvp ingest only case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest mvp ingest only time to first playable: 17869 ms
- Fastest mvp ingest only prerequisites: 0 ms
- Fastest mvp ingest only AI-previz recipe: 17869 ms
- Fastest mvp ingest only full completion: 20976 ms
- Fastest mvp ingest only post-playable overhead: 3107 ms
- Fastest isolated mvp ingest only AI-previz case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest isolated mvp ingest only AI-previz median: 17869 ms
- Fastest regenerate reuse case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest regenerate reuse time to first playable: 17869 ms
- Fastest regenerate reuse AI-previz recipe: 17869 ms
- Fastest regenerate reuse full completion: 20976 ms
- Fastest regenerate full-control case: `shipped_xai_4_480p_regenerate_full`
- Fastest regenerate full-control time to first playable: 39325 ms
- Fastest total case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest total elapsed: 20976 ms
- Fast target: <= 6000 ms to first real mvp ingest only `ai_previz_video`

## Cases

| Case | Attempts | Mode | Strategy | Start | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| shipped_xai_4_480p_regenerate_full | 1/1 | shipped | existing_clip_full_regenerate | recipe_start | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (21363 ms) | 17962 | 39325 | 43952 | 4627 | yes | Current shipped xAI lane with a healthy shot plan and prior AI previz clip already present, but measured from recipe start to capture the full-regenerate penalty during same-scene iteration. |
| shipped_xai_4_480p_regenerate_reuse | 1/1 | shipped | existing_clip_reuse_regenerate | ai_previz | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (0 ms) | 17869 | 17869 | 20976 | 3107 | yes | Current shipped xAI lane with a healthy shot plan and prior AI previz clip already present, reusing start_from=ai_previz to measure the honest regenerate loop. |
