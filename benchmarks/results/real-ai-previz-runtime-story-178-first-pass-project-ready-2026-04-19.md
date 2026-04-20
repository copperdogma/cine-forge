# Real AI Previz Runtime Eval

- Measured at: 2026-04-20T04:17:01.518607+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 4 / 4
- Fully successful cases: 4 / 4
- Focus prerequisite mode: `mvp_ingest_only`
- Focus route kind: `imported_project_first_pass`
- Fastest mvp ingest only case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest mvp ingest only time to first playable: 37186 ms
- Fastest mvp ingest only prerequisites: 19161 ms
- Fastest mvp ingest only AI-previz recipe: 18025 ms
- Fastest mvp ingest only full completion: 40198 ms
- Fastest mvp ingest only post-playable overhead: 3012 ms
- Fastest isolated mvp ingest only AI-previz case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest isolated mvp ingest only AI-previz median: 18025 ms
- Fastest imported-project first-pass case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest imported-project first-pass time to first playable: 37186 ms
- Fastest imported-project first-pass prerequisites: 19161 ms
- Fastest raw-input first-pass case: `shipped_xai_4_480p_mvp_ingest_only`
- Fastest raw-input first-pass time to first playable: 109868 ms
- Fastest raw-input first-pass prerequisites: 92216 ms
- Fastest regenerate reuse case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest regenerate reuse time to first playable: 18152 ms
- Fastest regenerate reuse AI-previz recipe: 18152 ms
- Fastest regenerate reuse full completion: 23446 ms
- Fastest regenerate full-control case: `shipped_xai_4_480p_regenerate_full`
- Fastest regenerate full-control time to first playable: 39062 ms
- Fastest total case: `shipped_xai_4_480p_regenerate_reuse`
- Fastest total elapsed: 23446 ms
- Fast target: <= 6000 ms to first real mvp ingest only `ai_previz_video`

## Cases

| Case | Attempts | Substrate | Mode | Strategy | Start | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| shipped_xai_4_480p_mvp_ingest_only | 1/1 | raw input | shipped | one_pass_previz_prep | ai_previz | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (92216 ms) | 17652 | 109868 | 113614 | 3746 | yes | Story 176 shipped baseline: MVP ingest plus a single on-demand shot-planning pass routed through xAI Grok Imagine without the full creative_direction chain. |
| shipped_xai_4_480p_project_ready_first_pass | 1/1 | imported project | shipped | project_ready_first_pass | recipe_start | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (19161 ms) | 18025 | 37186 | 40198 | 3012 | yes | Current Scene Workspace first clip on an already imported project: reuse healthy ingest artifacts, then auto-build shot planning before xAI previz. |
| shipped_xai_4_480p_regenerate_full | 1/1 | existing clip | shipped | existing_clip_full_regenerate | recipe_start | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (21043 ms) | 18019 | 39062 | 42523 | 3461 | yes | Current shipped xAI lane with a healthy shot plan and prior AI previz clip already present, but measured from recipe start to capture the full-regenerate penalty during same-scene iteration. |
| shipped_xai_4_480p_regenerate_reuse | 1/1 | existing clip | shipped | existing_clip_reuse_regenerate | ai_previz | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (0 ms) | 18152 | 18152 | 23446 | 5294 | yes | Current shipped xAI lane with a healthy shot plan and prior AI previz clip already present, reusing start_from=ai_previz to measure the honest regenerate loop. |
