# Full Script Throughput Eval

- Measured at: 2026-04-24T07:15:39.972826+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 1 / 1
- Median total runtime: 3539391 ms
- Median total cost: $3.5153
- Boundary current budget: 136146.132 ms / 1k input words
- Boundary climb target: 136146.132 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (75728.93 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (8126.63 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| big_fish_long | 25997 | 3539391 | 3.515333 | 1208433 | 452327 | 79525699 | yes | Long screenplay case to expose stage scaling, output-volume drift, and honest story-lane wall-clock cost. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 136146.132 | 136146.132 | 17399.200 | 17399.200 | 3059033.696 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 133540.370 | 133540.370 | 16557.257 | 16557.257 | 3006427.280 | 98.1% | 95.2% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 2605.762 | 2605.762 | 841.943 | 841.943 | 52606.416 | 1.9% | 4.8% |  |
| world_building.continuity_tracking | 75728.930 | 75728.930 | 8126.630 | 8126.630 | 2858019.002 | 55.6% | 46.7% | Dominant runtime and output-volume hotspot in the current boundary. |
| world_building.analyze_scenes | 43498.634 | 43498.634 | 2383.698 | 2383.698 | 41955.880 | 31.9% | 13.7% |  |
| world_building.entity_discovery | 7805.401 | 7805.401 | 719.545 | 719.545 | 412.971 | 5.7% | 4.1% |  |
| world_building.character_bible | 6500.635 | 6500.635 | 3405.778 | 3405.778 | 29378.082 | 4.8% | 19.6% |  |
| world_building.location_bible | 4958.803 | 4958.803 | 1553.141 | 1553.141 | 24645.767 | 3.6% | 8.9% |  |
| mvp_ingest.script_bible | 1253.952 | 1253.952 | 112.013 | 112.013 | 544.294 | 0.9% | 0.6% |  |
| world_building.prop_bible | 1157.787 | 1157.787 | 293.072 | 293.072 | 23960.226 | 0.9% | 1.7% |  |
| mvp_ingest.project_config | 963.765 | 963.765 | 43.197 | 43.197 | 531.831 | 0.7% | 0.2% |  |
| world_building.refresh_project_config | 959.842 | 959.842 | 41.697 | 41.697 | 519.060 | 0.7% | 0.2% |  |
| mvp_ingest.breakdown_scenes | 865.946 | 865.946 | 386.583 | 386.583 | 39441.897 | 0.6% | 2.2% |  |
| mvp_ingest.normalize | 381.390 | 381.390 | 300.150 | 300.150 | 6193.484 | 0.3% | 1.7% |  |
| world_building.entity_graph | 280.686 | 280.686 | 33.696 | 33.696 | 27536.293 | 0.2% | 0.2% |  |
| mvp_ingest.ingest | 1.039 | 1.039 | 0.000 | 0.000 | 5894.911 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime and output-volume hotspot in the current boundary. (runtime 75728.93 ms / 1k, output 8126.63 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 43498.634 ms / 1k, output 2383.698 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 6500.635 ms / 1k, output 3405.778 tok / 1k).

## Per-Case Recipe Detail

### big_fish_long

- Runtime: 3539391 ms total, $3.515333, 452327 output tokens, 79525699 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 67742 | 0.309422 | 243124 | 21888 | 1367609 | yes |
| world_building | 3471649 | 3.205911 | 965309 | 430439 | 78158090 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 27 | 0.000000 | 0 | 0 | 1 | 153250 | 79 | code |
| mvp_ingest.normalize | done | 9915 | 0.041196 | 12480 | 7803 | 1 | 161012 | 294 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 22512 | 0.173578 | 166722 | 10050 | 191 | 1025371 | 37726 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 32599 | 0.047192 | 44430 | 2912 | 1 | 14150 | 145 | claude-haiku-4-5-20251001 |
| mvp_ingest.project_config | done | 25055 | 0.047457 | 19492 | 1123 | 1 | 13826 | 448 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 1130834 | 0.934440 | 1635 | 61969 | 191 | 1090727 | 35481 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 24953 | 0.046379 | 19239 | 1084 | 1 | 13494 | 444 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 202917 | 0.170546 | 119653 | 18706 | 1 | 10736 | 438 | claude-haiku-4-5-20251001 |
| world_building.character_bible | done | 168997 | 0.548053 | 242366 | 88540 | 246 | 763742 | 23270 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 128914 | 0.281927 | 150524 | 40377 | 256 | 640716 | 19204 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 30099 | 0.057582 | 33883 | 7619 | 46 | 622894 | 15490 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 7297 | 0.005175 | 2089 | 876 | 1 | 715861 | 25476 | claude-haiku-4-5-20251001 |
| world_building.continuity_tracking | done | 1968725 | 1.161808 | 395920 | 211268 | 678 | 74299920 | 2292288 | claude-haiku-4-5-20251001 |
