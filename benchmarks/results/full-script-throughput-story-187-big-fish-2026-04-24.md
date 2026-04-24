# Full Script Throughput Eval

- Measured at: 2026-04-24T17:21:31.908624+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 1 / 1
- Median total runtime: 3263471 ms
- Median total cost: $3.5857
- Boundary current budget: 125532.6 ms / 1k input words
- Boundary climb target: 125532.6 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (69648.075 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (8438.974 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| big_fish_long | 25997 | 3263471 | 3.585747 | 1215389 | 463283 | 81731991 | yes | Long screenplay case to expose stage scaling, output-volume drift, and honest story-lane wall-clock cost. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 125532.600 | 125532.600 | 17820.633 | 17820.633 | 3143900.873 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 123026.580 | 123026.580 | 16976.190 | 16976.190 | 3091081.471 | 98.0% | 95.3% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 2506.020 | 2506.020 | 844.444 | 844.444 | 52819.402 | 2.0% | 4.7% |  |
| world_building.continuity_tracking | 69648.075 | 69648.075 | 8438.974 | 8438.974 | 2942755.741 | 55.5% | 47.4% | Dominant runtime and output-volume hotspot in the current boundary. |
| world_building.analyze_scenes | 40898.527 | 40898.527 | 2453.706 | 2453.706 | 42242.605 | 32.6% | 13.8% |  |
| world_building.entity_discovery | 6365.773 | 6365.773 | 767.242 | 767.242 | 419.202 | 5.1% | 4.3% |  |
| world_building.character_bible | 6107.782 | 6107.782 | 3330.192 | 3330.192 | 28747.163 | 4.9% | 18.7% |  |
| world_building.location_bible | 4020.233 | 4020.233 | 1622.610 | 1622.610 | 25685.233 | 3.2% | 9.1% |  |
| mvp_ingest.script_bible | 1262.338 | 1262.338 | 112.205 | 112.205 | 535.023 | 1.0% | 0.6% |  |
| world_building.prop_bible | 1088.318 | 1088.318 | 284.648 | 284.648 | 24265.838 | 0.9% | 1.6% |  |
| world_building.refresh_project_config | 1045.274 | 1045.274 | 43.890 | 43.890 | 523.291 | 0.8% | 0.2% |  |
| mvp_ingest.project_config | 923.684 | 923.684 | 42.390 | 42.390 | 516.790 | 0.7% | 0.2% |  |
| mvp_ingest.breakdown_scenes | 846.636 | 846.636 | 390.007 | 390.007 | 39684.964 | 0.7% | 2.2% |  |
| mvp_ingest.normalize | 313.459 | 313.459 | 299.842 | 299.842 | 6187.714 | 0.2% | 1.7% |  |
| world_building.entity_graph | 249.798 | 249.798 | 34.927 | 34.927 | 26442.397 | 0.2% | 0.2% |  |
| mvp_ingest.ingest | 0.923 | 0.923 | 0.000 | 0.000 | 5894.911 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime and output-volume hotspot in the current boundary. (runtime 69648.075 ms / 1k, output 8438.974 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 40898.527 ms / 1k, output 2453.706 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 6107.782 ms / 1k, output 3330.192 tok / 1k).

## Per-Case Recipe Detail

### big_fish_long

- Runtime: 3263471 ms total, $3.585747, 463283 output tokens, 81731991 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 65149 | 0.309987 | 244318 | 21953 | 1373146 | yes |
| world_building | 3198322 | 3.275760 | 971071 | 441330 | 80358845 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 24 | 0.000000 | 0 | 0 | 1 | 153250 | 79 | code |
| mvp_ingest.normalize | done | 8149 | 0.041164 | 12480 | 7795 | 1 | 160862 | 291 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 22010 | 0.175040 | 168105 | 10139 | 193 | 1031690 | 37974 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 32817 | 0.047206 | 44422 | 2917 | 1 | 13909 | 140 | claude-haiku-4-5-20251001 |
| mvp_ingest.project_config | done | 24013 | 0.046578 | 19311 | 1102 | 1 | 13435 | 440 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 1063239 | 0.963018 | 2061 | 63789 | 193 | 1098181 | 35926 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 27174 | 0.047320 | 19233 | 1141 | 1 | 13604 | 438 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 165491 | 0.176214 | 120537 | 19946 | 1 | 10898 | 436 | claude-haiku-4-5-20251001 |
| world_building.character_bible | done | 158784 | 0.534726 | 235533 | 86575 | 240 | 747340 | 22658 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 104514 | 0.292477 | 154681 | 42183 | 266 | 667739 | 19954 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 28293 | 0.056538 | 33673 | 7400 | 48 | 630839 | 15820 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 6494 | 0.005298 | 2083 | 908 | 1 | 687423 | 24388 | claude-haiku-4-5-20251001 |
| world_building.continuity_tracking | done | 1810641 | 1.200168 | 403270 | 219388 | 691 | 76502821 | 2363255 | claude-haiku-4-5-20251001 |
