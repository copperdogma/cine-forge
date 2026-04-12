# Full Script Throughput Eval

- Measured at: 2026-04-12T00:03:39.351896+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 1 / 1
- Median total runtime: 2808707 ms
- Median total cost: $3.2416
- Boundary current budget: 108039.658 ms / 1k input words
- Boundary climb target: 108039.658 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (66291.303 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (8374.62 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| big_fish_long | 25997 | 2808707 | 3.241632 | 1217391 | 460669 | 84396984 | yes | Long screenplay case to expose stage scaling, output-volume drift, and honest story-lane wall-clock cost. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 108039.658 | 108039.658 | 17720.083 | 17720.083 | 3246412.432 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 106203.831 | 106203.831 | 16904.104 | 16904.104 | 3193618.456 | 98.3% | 95.4% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 1835.827 | 1835.827 | 815.979 | 815.979 | 52793.976 | 1.7% | 4.6% |  |
| world_building.continuity_tracking | 66291.303 | 66291.303 | 8374.620 | 8374.620 | 3050068.816 | 61.4% | 47.3% | Dominant runtime and output-volume hotspot in the current boundary. |
| world_building.analyze_scenes | 31158.903 | 31158.903 | 2074.047 | 2074.047 | 40639.651 | 28.8% | 11.7% |  |
| world_building.character_bible | 5673.578 | 5673.578 | 3353.695 | 3353.695 | 28635.189 | 5.2% | 18.9% |  |
| world_building.location_bible | 4082.240 | 4082.240 | 1802.977 | 1802.977 | 28431.319 | 3.8% | 10.2% |  |
| world_building.entity_discovery | 3075.509 | 3075.509 | 1020.118 | 1020.118 | 569.335 | 2.9% | 5.8% |  |
| mvp_ingest.project_config | 921.953 | 921.953 | 41.620 | 41.620 | 513.098 | 0.9% | 0.2% |  |
| world_building.prop_bible | 894.411 | 894.411 | 222.333 | 222.333 | 18531.792 | 0.8% | 1.2% |  |
| world_building.refresh_project_config | 848.598 | 848.598 | 40.582 | 40.582 | 501.904 | 0.8% | 0.2% |  |
| mvp_ingest.breakdown_scenes | 689.541 | 689.541 | 388.045 | 388.045 | 39787.399 | 0.6% | 2.2% |  |
| mvp_ingest.script_bible | 474.901 | 474.901 | 85.010 | 85.010 | 410.394 | 0.4% | 0.5% |  |
| world_building.entity_graph | 455.553 | 455.553 | 15.733 | 15.733 | 26240.451 | 0.4% | 0.1% |  |
| mvp_ingest.normalize | 221.179 | 221.179 | 301.304 | 301.304 | 6188.176 | 0.2% | 1.7% |  |
| mvp_ingest.ingest | 0.846 | 0.846 | 0.000 | 0.000 | 5894.911 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime and output-volume hotspot in the current boundary. (runtime 66291.303 ms / 1k, output 8374.62 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 31158.903 ms / 1k, output 2074.047 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 5673.578 ms / 1k, output 3353.695 tok / 1k).

## Per-Case Recipe Detail

### big_fish_long

- Runtime: 2808707 ms total, $3.241632, 460669 output tokens, 84396984 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 47726 | 0.267171 | 241468 | 21213 | 1372485 | yes |
| world_building | 2760981 | 2.974461 | 975923 | 439456 | 83024499 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 22 | 0.000000 | 0 | 0 | 1 | 153250 | 79 | code |
| mvp_ingest.normalize | done | 5750 | 0.041316 | 12480 | 7833 | 1 | 160874 | 290 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 17926 | 0.175426 | 168842 | 10088 | 194 | 1034353 | 38070 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 12346 | 0.003721 | 40772 | 2210 | 1 | 10669 | 120 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 23968 | 0.046708 | 19374 | 1082 | 1 | 13339 | 436 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 810038 | 0.808905 | 40 | 53919 | 194 | 1056509 | 35982 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 22061 | 0.045691 | 19036 | 1055 | 1 | 13048 | 434 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 79954 | 0.016560 | 114714 | 26520 | 1 | 14801 | 581 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 147496 | 0.536192 | 234310 | 87186 | 238 | 744429 | 22605 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 106126 | 0.322989 | 169376 | 46872 | 294 | 739129 | 22070 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 23252 | 0.042342 | 24028 | 5780 | 30 | 481771 | 11800 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 11843 | 0.000443 | 1320 | 409 | 1 | 682173 | 24145 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 1723375 | 1.201339 | 413099 | 217715 | 702 | 79292639 | 2436390 | claude-haiku-4-5-20251001 |
