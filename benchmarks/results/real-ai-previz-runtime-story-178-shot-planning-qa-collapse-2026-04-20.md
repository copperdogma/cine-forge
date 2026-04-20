# Real AI Previz Runtime Eval

- Measured at: 2026-04-20T14:52:32.203044+00:00
- Fixture manifest: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
- Comparison method: `shared_prerequisite_strategy_substrate`
- Repeat count: 1
- Successful cases: 2 / 2
- Fully successful cases: 2 / 2
- Focus prerequisite mode: `mvp_ingest_only`
- Focus route kind: `imported_project_first_pass`
- Fastest mvp ingest only case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest mvp ingest only time to first playable: 31369 ms
- Fastest mvp ingest only prerequisites: 13194 ms
- Fastest mvp ingest only AI-previz recipe: 18175 ms
- Fastest mvp ingest only full completion: 35639 ms
- Fastest mvp ingest only post-playable overhead: 4270 ms
- Fastest isolated mvp ingest only AI-previz case: `xai_4_480p_project_ready_first_pass_with_qa_control`
- Fastest isolated mvp ingest only AI-previz median: 17831 ms
- Fastest imported-project first-pass case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest imported-project first-pass time to first playable: 31369 ms
- Fastest imported-project first-pass prerequisites: 13194 ms
- Fastest total case: `shipped_xai_4_480p_project_ready_first_pass`
- Fastest total elapsed: 35639 ms
- Fast target: <= 6000 ms to first real mvp ingest only `ai_previz_video`

## Cases

| Case | Attempts | Substrate | Mode | Strategy | Start | Engine Pack | Prompt | Prereqs | AI Previz ms | First playable ms | Full completion ms | Post-playable overhead | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| shipped_xai_4_480p_project_ready_first_pass | 1/1 | imported project | shipped | project_ready_first_pass | recipe_start | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (13194 ms) | 18175 | 31369 | 35639 | 4270 | yes | Current Scene Workspace first clip on an already imported project: reuse healthy ingest artifacts, then auto-build shot planning before xAI previz. |
| xai_4_480p_project_ready_first_pass_with_qa_control | 1/1 | imported project | patched | project_ready_first_pass | recipe_start | xai_grok_imagine_video / 4s 480p | standard | mvp_ingest_only (23844 ms) | 17831 | 41675 | 45959 | 4284 | yes | Explicit old-behavior control for Story 178 after the shipped previz-fast route stops paying for the extra shot-planning QA pass. |
