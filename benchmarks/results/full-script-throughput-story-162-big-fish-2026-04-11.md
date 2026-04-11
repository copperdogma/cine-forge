# Full Script Throughput Eval

- Measured at: 2026-04-11T21:59:06.195520+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 1 / 1
- Median total runtime: 2903127 ms
- Median total cost: $3.3018
- Boundary current budget: 111671.616 ms / 1k input words
- Boundary climb target: 111671.616 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (67257.03 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (8170.866 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| big_fish_long | 25997 | 2903127 | 3.301826 | 1222202 | 456496 | 83010092 | yes | Long screenplay case to expose stage scaling, output-volume drift, and honest story-lane wall-clock cost. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 111671.616 | 111671.616 | 17559.565 | 17559.565 | 3193064.277 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 109855.868 | 109855.868 | 16738.547 | 16738.547 | 3140000.038 | 98.4% | 95.3% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 1815.748 | 1815.748 | 821.018 | 821.018 | 53064.238 | 1.6% | 4.7% |  |
| world_building.continuity_tracking | 67257.030 | 67257.030 | 8170.866 | 8170.866 | 2997113.628 | 60.2% | 46.5% | Dominant runtime and output-volume hotspot in the current boundary. |
| world_building.analyze_scenes | 33032.696 | 33032.696 | 2217.717 | 2217.717 | 41337.154 | 29.6% | 12.6% |  |
| world_building.character_bible | 5411.663 | 5411.663 | 3223.295 | 3223.295 | 27758.549 | 4.9% | 18.4% |  |
| world_building.location_bible | 4161.557 | 4161.557 | 1810.247 | 1810.247 | 28545.717 | 3.7% | 10.3% |  |
| world_building.entity_discovery | 4150.210 | 4150.210 | 1025.041 | 1025.041 | 570.566 | 3.7% | 5.8% |  |
| world_building.prop_bible | 915.913 | 915.913 | 222.256 | 222.256 | 18558.026 | 0.8% | 1.3% |  |
| mvp_ingest.project_config | 865.215 | 865.215 | 39.774 | 39.774 | 508.597 | 0.8% | 0.2% |  |
| world_building.refresh_project_config | 856.330 | 856.330 | 44.159 | 44.159 | 510.559 | 0.8% | 0.2% |  |
| mvp_ingest.breakdown_scenes | 719.852 | 719.852 | 389.122 | 389.122 | 40038.428 | 0.6% | 2.2% |  |
| mvp_ingest.script_bible | 542.101 | 542.101 | 89.780 | 89.780 | 430.934 | 0.5% | 0.5% |  |
| world_building.entity_graph | 406.393 | 406.393 | 24.964 | 24.964 | 25605.839 | 0.4% | 0.1% |  |
| mvp_ingest.normalize | 227.680 | 227.680 | 302.343 | 302.343 | 6191.368 | 0.2% | 1.7% |  |
| mvp_ingest.ingest | 0.808 | 0.808 | 0.000 | 0.000 | 5894.911 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime and output-volume hotspot in the current boundary. (runtime 67257.03 ms / 1k, output 8170.866 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 33032.696 ms / 1k, output 2217.717 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 5411.663 ms / 1k, output 3223.295 tok / 1k).

## Per-Case Recipe Detail

### big_fish_long

- Runtime: 2903127 ms total, $3.301826, 456496 output tokens, 83010092 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 47204 | 0.267680 | 242763 | 21344 | 1379511 | yes |
| world_building | 2855923 | 3.034145 | 979439 | 435152 | 81630581 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 21 | 0.000000 | 0 | 0 | 1 | 153250 | 79 | code |
| mvp_ingest.normalize | done | 5919 | 0.041424 | 12480 | 7860 | 1 | 160957 | 290 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 18714 | 0.176642 | 170222 | 10116 | 196 | 1040879 | 38325 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 14093 | 0.003760 | 40798 | 2334 | 1 | 11203 | 120 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 22493 | 0.045855 | 19263 | 1034 | 1 | 13222 | 436 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 858751 | 0.910608 | 15266 | 57654 | 196 | 1074642 | 36423 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 22262 | 0.046875 | 18958 | 1148 | 1 | 13273 | 432 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 107893 | 0.016608 | 114850 | 26648 | 1 | 14833 | 581 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 140687 | 0.521130 | 232432 | 83796 | 232 | 721639 | 21971 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 108188 | 0.324047 | 169754 | 47061 | 296 | 742103 | 22207 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 23811 | 0.042334 | 24028 | 5778 | 30 | 482453 | 11800 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 10565 | 0.000583 | 1292 | 649 | 1 | 665675 | 23582 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 1748481 | 1.171959 | 402859 | 212418 | 696 | 77915963 | 2398602 | claude-haiku-4-5-20251001 |
