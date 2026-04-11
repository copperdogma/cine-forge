# Full Script Throughput Eval

- Measured at: 2026-04-11T18:19:49.181744+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 2 / 2
- Median total runtime: 239590 ms
- Median total cost: $0.3472
- Boundary current budget: 155193.329 ms / 1k input words
- Boundary climb target: 91822.598 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (65442.187 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (8428.378 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| open_frequency_short | 601 | 131357 | 0.169092 | 54715 | 23297 | 570388 | yes | Short control to expose fixed overhead and avoid inferring budgets from long-form scripts alone. |
| last_birthday_card_medium | 3788 | 347824 | 0.525358 | 214265 | 62009 | 2502750 | yes | Medium-length screenplay to anchor realistic story-lane throughput between trivial and full-length extremes. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 155193.329 | 91822.598 | 27566.789 | 16369.852 | 804884.874 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 131843.343 | 84114.308 | 24604.048 | 14931.890 | 730094.288 | 86.9% | 89.8% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 23349.985 | 7708.289 | 2962.742 | 1437.962 | 74790.587 | 13.1% | 10.2% |  |
| world_building.continuity_tracking | 65442.187 | 39703.010 | 8428.378 | 5568.902 | 347915.094 | 42.5% | 31.6% | Dominant runtime hotspot in the current boundary. |
| world_building.analyze_scenes | 35843.995 | 31039.071 | 2319.787 | 2168.691 | 44014.712 | 26.2% | 9.8% |  |
| mvp_ingest.project_config | 16664.408 | 4704.857 | 856.757 | 247.624 | 7802.629 | 9.1% | 2.6% |  |
| world_building.refresh_project_config | 15647.048 | 5096.093 | 853.889 | 256.864 | 7842.760 | 8.8% | 2.7% |  |
| world_building.prop_bible | 13893.356 | 6335.797 | 3247.966 | 1673.970 | 192634.649 | 8.4% | 11.3% |  |
| world_building.character_bible | 13526.591 | 8259.504 | 7674.109 | 4260.032 | 54987.291 | 8.8% | 27.3% |  |
| world_building.entity_graph | 9973.158 | 2508.712 | 522.817 | 128.828 | 60299.425 | 5.4% | 1.6% |  |
| mvp_ingest.script_bible | 6092.610 | 1945.618 | 1409.092 | 415.523 | 7551.222 | 3.4% | 4.4% |  |
| world_building.location_bible | 4935.826 | 1625.396 | 1281.552 | 601.373 | 19996.718 | 2.8% | 4.4% |  |
| world_building.entity_discovery | 2996.651 | 2445.882 | 275.550 | 273.231 | 2403.638 | 2.1% | 1.2% |  |
| mvp_ingest.breakdown_scenes | 1975.360 | 877.508 | 490.054 | 361.140 | 42941.584 | 1.2% | 1.9% |  |
| mvp_ingest.normalize | 530.495 | 16.639 | 206.838 | 0.000 | 8366.025 | 0.6% | 1.3% |  |
| mvp_ingest.ingest | 3.988 | 1.320 | 0.000 | 0.000 | 8129.124 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Dominant runtime hotspot in the current boundary. (runtime 65442.187 ms / 1k, output 8428.378 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 35843.995 ms / 1k, output 2319.787 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 13526.591 ms / 1k, output 7674.109 tok / 1k).

## Per-Case Recipe Detail

### open_frequency_short

- Runtime: 131357 ms total, $0.169092, 23297 output tokens, 570388 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 23434 | 0.025940 | 9996 | 2697 | 53200 | yes |
| world_building | 107923 | 0.143151 | 44719 | 20600 | 517188 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 4 | 0.000000 | 0 | 0 | 1 | 5849 | 79 | code |
| mvp_ingest.normalize | done | 10 | 0.000000 | 0 | 0 | 1 | 5802 | 72 | code |
| mvp_ingest.breakdown_scenes | done | 1847 | 0.004351 | 3579 | 372 | 5 | 25752 | 983 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 6154 | 0.000530 | 1292 | 1444 | 1 | 7800 | 110 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 17203 | 0.021059 | 5125 | 881 | 1 | 7997 | 228 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 24430 | 0.022281 | 2 | 1485 | 5 | 26713 | 919 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 15745 | 0.020353 | 4759 | 872 | 1 | 8007 | 230 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 2132 | 0.000240 | 2530 | 167 | 1 | 2318 | 86 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 11295 | 0.038590 | 14917 | 6664 | 12 | 46461 | 1355 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 4956 | 0.006858 | 2677 | 1179 | 6 | 16135 | 462 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 12892 | 0.020238 | 10807 | 2898 | 18 | 153645 | 3543 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 10480 | 0.000353 | 148 | 551 | 1 | 55343 | 1913 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 54800 | 0.034239 | 8879 | 6784 | 22 | 208566 | 6746 | claude-haiku-4-5-20251001 |

### last_birthday_card_medium

- Runtime: 347824 ms total, $0.525358, 62009 output tokens, 2502750 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 29199 | 0.069309 | 46109 | 5447 | 231303 | yes |
| world_building | 318625 | 0.456048 | 168156 | 56562 | 2271447 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 5 | 0.000000 | 0 | 0 | 1 | 24721 | 79 | code |
| mvp_ingest.normalize | done | 3956 | 0.008786 | 3147 | 1567 | 1 | 26812 | 143 | claude-haiku-4-5-20251001 |
| mvp_ingest.breakdown_scenes | done | 3324 | 0.024596 | 23905 | 1368 | 29 | 163015 | 6066 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 7370 | 0.000950 | 6369 | 1574 | 1 | 8046 | 115 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 17822 | 0.034978 | 12688 | 938 | 1 | 8709 | 254 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 117576 | 0.129165 | 1980 | 8215 | 29 | 165088 | 5740 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 19304 | 0.034523 | 12340 | 973 | 1 | 8950 | 250 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 9265 | 0.001813 | 20034 | 1035 | 1 | 3600 | 134 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 31287 | 0.094210 | 37077 | 16137 | 36 | 123748 | 3646 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 6157 | 0.015693 | 8226 | 2278 | 22 | 49799 | 1590 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 24000 | 0.052377 | 33766 | 6341 | 42 | 491002 | 11820 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 9503 | 0.000337 | 294 | 488 | 1 | 108011 | 3707 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 150395 | 0.127931 | 54439 | 21095 | 60 | 1321249 | 41711 | claude-haiku-4-5-20251001 |
