# Full Script Throughput Eval

- Measured at: 2026-04-11T04:19:47.903189+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 2 / 3
- Median total runtime: 255740 ms
- Median total cost: $0.3611
- Boundary current budget: 167345.94 ms / 1k input words
- Boundary climb target: 97374.076 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (72295.372 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (9510.535 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| open_frequency_short | 601 | 142628 | 0.174084 | 56476 | 24202 | 582844 | yes | Short control to expose fixed overhead and avoid inferring budgets from long-form scripts alone. |
| last_birthday_card_medium | 3788 | 368853 | 0.548149 | 211574 | 66335 | 2633685 | yes | Medium-length screenplay to anchor realistic story-lane throughput between trivial and full-length extremes. |
| big_fish_long | 25997 | 1087301 | 1.284395 | 396621 | 113790 | 2637941 | no | Long screenplay case to expose stage scaling, output-volume drift, and honest story-lane wall-clock cost. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 167345.940 | 97374.076 | 28890.715 | 17511.880 | 832530.470 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 143295.712 | 89880.940 | 25962.319 | 16081.045 | 756536.558 | 87.6% | 90.4% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 24050.229 | 7493.136 | 2928.396 | 1430.834 | 75993.913 | 12.4% | 9.6% |  |
| world_building.continuity_tracking | 72295.372 | 41449.314 | 9510.535 | 6483.633 | 310149.139 | 43.0% | 34.1% | Dominant runtime hotspot in the current boundary. |
| world_building.analyze_scenes | 38746.739 | 33673.178 | 2443.952 | 2308.870 | 45788.408 | 26.5% | 9.8% |  |
| world_building.character_bible | 16973.427 | 9838.701 | 7740.467 | 4377.772 | 119443.573 | 10.1% | 26.3% |  |
| mvp_ingest.project_config | 16618.046 | 4816.790 | 817.156 | 239.968 | 7631.060 | 8.5% | 2.4% |  |
| world_building.prop_bible | 15869.747 | 5150.475 | 2974.086 | 1257.656 | 168164.596 | 8.2% | 9.4% |  |
| world_building.refresh_project_config | 13997.499 | 4906.811 | 813.947 | 235.216 | 7709.731 | 7.4% | 2.4% |  |
| world_building.location_bible | 8990.341 | 4025.607 | 1675.272 | 961.193 | 44169.633 | 5.0% | 5.7% |  |
| world_building.entity_graph | 8300.948 | 2909.715 | 513.197 | 152.851 | 58706.257 | 4.4% | 1.5% |  |
| mvp_ingest.script_bible | 6914.754 | 1729.673 | 1396.025 | 389.388 | 7479.813 | 3.4% | 4.1% |  |
| world_building.entity_discovery | 2257.322 | 1704.329 | 290.862 | 277.870 | 2405.221 | 1.5% | 1.2% |  |
| mvp_ingest.breakdown_scenes | 1809.961 | 1288.807 | 504.418 | 379.884 | 44375.086 | 1.1% | 1.9% |  |
| mvp_ingest.normalize | 477.209 | 18.303 | 210.798 | 0.000 | 8378.829 | 0.5% | 1.2% |  |
| mvp_ingest.ingest | 3.024 | 1.056 | 0.000 | 0.000 | 8129.124 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime hotspot in the current boundary. (runtime 72295.372 ms / 1k, output 9510.535 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 38746.739 ms / 1k, output 2443.952 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 16973.427 ms / 1k, output 7740.467 tok / 1k).

## Per-Case Recipe Detail

### open_frequency_short

- Runtime: 142628 ms total, $0.174084, 24202 output tokens, 582844 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 24405 | 0.025297 | 9947 | 2660 | 53023 | yes |
| world_building | 118223 | 0.148787 | 46529 | 21542 | 529821 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 3 | 0.000000 | 0 | 0 | 1 | 5849 | 79 | code |
| mvp_ingest.normalize | done | 11 | 0.000000 | 0 | 0 | 1 | 5802 | 72 | code |
| mvp_ingest.breakdown_scenes | done | 1401 | 0.004375 | 3579 | 378 | 5 | 25756 | 983 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 7272 | 0.000530 | 1292 | 1444 | 1 | 7800 | 110 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 17080 | 0.020392 | 5076 | 838 | 1 | 7816 | 228 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 26336 | 0.023256 | 2 | 1550 | 5 | 27177 | 919 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 13876 | 0.019816 | 4746 | 837 | 1 | 7892 | 230 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 1689 | 0.000240 | 2530 | 167 | 1 | 2318 | 86 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 14489 | 0.038861 | 15211 | 6673 | 10 | 76048 | 1917 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 8387 | 0.009513 | 4711 | 1436 | 6 | 26494 | 646 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 15980 | 0.019922 | 10807 | 2819 | 18 | 150950 | 3542 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 8229 | 0.000336 | 143 | 525 | 1 | 53841 | 1875 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 61988 | 0.036843 | 8379 | 7535 | 20 | 185101 | 5952 | claude-haiku-4-5-20251001 |

### last_birthday_card_medium

- Runtime: 368853 ms total, $0.548149, 66335 output tokens, 2633685 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 28384 | 0.070112 | 47439 | 5420 | 241535 | yes |
| world_building | 340469 | 0.478037 | 164135 | 60915 | 2392150 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 4 | 0.000000 | 0 | 0 | 1 | 24721 | 79 | code |
| mvp_ingest.normalize | done | 3546 | 0.008906 | 3147 | 1597 | 1 | 26909 | 143 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 4882 | 0.025990 | 25292 | 1439 | 32 | 173850 | 6480 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 6552 | 0.000922 | 6397 | 1475 | 1 | 7505 | 114 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 18246 | 0.034295 | 12603 | 909 | 1 | 8550 | 254 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 127554 | 0.141939 | 3583 | 8746 | 32 | 175601 | 6132 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 18587 | 0.033391 | 12316 | 891 | 1 | 8667 | 252 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 6456 | 0.001856 | 20146 | 1151 | 1 | 3612 | 137 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 37269 | 0.092798 | 33083 | 16583 | 32 | 425587 | 10409 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 15249 | 0.024597 | 12541 | 3641 | 22 | 167642 | 4266 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 19510 | 0.040783 | 27159 | 4764 | 28 | 322603 | 7385 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 11022 | 0.000384 | 247 | 579 | 1 | 105408 | 3639 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 157010 | 0.142288 | 55060 | 24560 | 64 | 1183030 | 37353 | claude-haiku-4-5-20251001 |

### big_fish_long

- Runtime: 1087301 ms total, $1.284395, 113790 output tokens, 2637941 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 45010 | 0.266116 | 240750 | 21360 | 1369943 | yes |
| world_building | 1042291 | 1.018279 | 155871 | 92430 | 1267998 | no |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 13 | 0.000000 | 0 | 0 | 1 | 153250 | 79 | code |
| mvp_ingest.normalize | done | 5881 | 0.041284 | 12480 | 7825 | 1 | 160786 | 289 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 17390 | 0.174922 | 168153 | 10100 | 193 | 1031199 | 37948 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 11416 | 0.003773 | 40765 | 2386 | 1 | 11476 | 120 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 21685 | 0.046137 | 19352 | 1049 | 1 | 13232 | 436 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 888476 | 0.933645 | 11020 | 60039 | 193 | 1074764 | 36238 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 24642 | 0.046823 | 19024 | 1135 | 1 | 13516 | 438 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 96719 | 0.017105 | 115419 | 28161 | 1 | 15398 | 616 | gemini-2.5-flash-lite |
| world_building.character_bible | failed | 57044 | 0.000000 | 0 | 0 | 0 | 0 | 0 | code |
| world_building.location_bible | failed | 56826 | 0.000000 | 0 | 0 | 0 | 0 | 0 | code |
| world_building.prop_bible | done | 16334 | 0.020706 | 10408 | 3095 | 8 | 164320 | 3755 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | pending | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | code |
| world_building.continuity_tracking | pending | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | code |
