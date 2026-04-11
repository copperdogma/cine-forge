# Full Script Throughput Eval

- Measured at: 2026-04-11T03:47:30.320194+00:00
- Fixture manifest: `benchmarks/fixtures/full_script_throughput_cases.json`
- Honest boundary: `Break Down Script -> Deep Breakdown`
- Scope truth: Current surfaced story-lane path only: run `mvp_ingest` (Break Down Script) followed by `world_building` (Deep Breakdown) on a fresh screenplay project. Excludes unfinished film-lane generation, export, and any pretend full-pipeline runtime claim.
- Recipe chain: `mvp_ingest, world_building`
- Successful cases: 1 / 1
- Median total runtime: 126404 ms
- Median total cost: $0.1790
- Boundary current budget: 210322.795 ms / 1k input words
- Boundary climb target: 210322.795 ms / 1k input words
- Top runtime hotspot: `world_building.continuity_tracking` (70432.612 ms / 1k words)
- Top output hotspot: `world_building.continuity_tracking` (12888.519 tokens / 1k words)

## Budget Basis

- `current_observed`: median normalized rate across successful cases.
- `climb_target`: best observed normalized rate across successful cases.
- These are climb aids for detector-backed optimization, not stop-ship thresholds.

## Cases

| Case | Words | Total ms | Cost USD | Input tok | Output tok | Output bytes | Success | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| open_frequency_short | 601 | 126404 | 0.178968 | 56535 | 24858 | 576390 | yes | Short control to expose fixed overhead and avoid inferring budgets from long-form scripts alone. |

## Stage Efficiency Budgets

| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | Climb out tok / 1k | Current out bytes / 1k | Median dur share | Median out share | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| story_lane_workspace_ready | 210322.795 | 210322.795 | 41361.065 | 41361.065 | 959051.581 | n/a | n/a | Median is the current budget; best observed normalized rate is the next climb target. |
| world_building | 169886.855 | 169886.855 | 36890.183 | 36890.183 | 870777.038 | 80.8% | 89.2% | Dominant runtime and output-volume hotspot in the current boundary. |
| mvp_ingest | 40435.940 | 40435.940 | 4470.882 | 4470.882 | 88274.542 | 19.2% | 10.8% |  |
| world_building.continuity_tracking | 70432.612 | 70432.612 | 12888.519 | 12888.519 | 309166.389 | 33.5% | 31.2% |  |
| world_building.analyze_scenes | 47640.599 | 47640.599 | 2826.955 | 2826.955 | 46123.128 | 22.7% | 6.8% |  |
| mvp_ingest.project_config | 30287.854 | 30287.854 | 1447.587 | 1447.587 | 13114.809 | 14.4% | 3.5% |  |
| world_building.refresh_project_config | 26742.097 | 26742.097 | 1399.334 | 1399.334 | 13138.103 | 12.7% | 3.4% |  |
| world_building.character_bible | 24991.681 | 24991.681 | 11427.621 | 11427.621 | 127439.268 | 11.9% | 27.6% |  |
| world_building.prop_bible | 19552.413 | 19552.413 | 4712.146 | 4712.146 | 235871.880 | 9.3% | 11.4% |  |
| world_building.entity_graph | 16322.795 | 16322.795 | 853.577 | 853.577 | 90495.840 | 7.8% | 2.1% |  |
| world_building.location_bible | 13773.710 | 13773.710 | 2504.160 | 2504.160 | 44685.524 | 6.6% | 6.0% |  |
| mvp_ingest.script_bible | 10043.261 | 10043.261 | 2402.662 | 2402.662 | 12978.369 | 4.8% | 5.8% |  |
| world_building.entity_discovery | 4009.983 | 4009.983 | 277.870 | 277.870 | 3856.905 | 1.9% | 0.7% |  |
| mvp_ingest.breakdown_scenes | 2088.186 | 2088.186 | 620.632 | 620.632 | 42795.341 | 1.0% | 1.5% |  |
| mvp_ingest.normalize | 28.286 | 28.286 | 0.000 | 0.000 | 9653.910 | 0.0% | 0.0% |  |
| mvp_ingest.ingest | 9.983 | 9.983 | 0.000 | 0.000 | 9732.113 | 0.0% | 0.0% |  |

## Follow-Up Candidates

- `world_building.continuity_tracking` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 70432.612 ms / 1k, output 12888.519 tok / 1k).
- `world_building.analyze_scenes` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 47640.599 ms / 1k, output 2826.955 tok / 1k).
- `world_building.character_bible` — Measured hotspot: promote into a stage-specific throughput follow-up. (runtime 24991.681 ms / 1k, output 11427.621 tok / 1k).

## Per-Case Recipe Detail

### open_frequency_short

- Runtime: 126404 ms total, $0.178968, 24858 output tokens, 576390 output bytes.

| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | Output bytes | Success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest | 24302 | 0.025840 | 9973 | 2687 | 53053 | yes |
| world_building | 102102 | 0.153128 | 46562 | 22171 | 523337 | yes |

| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | Artifacts | Output bytes | Output lines | Model |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mvp_ingest.ingest | done | 6 | 0.000000 | 0 | 0 | 1 | 5849 | 79 | code |
| mvp_ingest.normalize | done | 17 | 0.000000 | 0 | 0 | 1 | 5802 | 72 | code |
| mvp_ingest.breakdown_scenes | done | 1255 | 0.004355 | 3579 | 373 | 5 | 25720 | 981 | mixed:claude-haiku-4-5-20251001 |
| mvp_ingest.script_bible | done | 6036 | 0.000530 | 1292 | 1444 | 1 | 7800 | 110 | gemini-2.5-flash-lite |
| mvp_ingest.project_config | done | 18203 | 0.020955 | 5102 | 870 | 1 | 7882 | 228 | claude-sonnet-4-6 |
| world_building.analyze_scenes | done | 28632 | 0.025491 | 2 | 1699 | 5 | 27720 | 927 | mixed:claude-sonnet-4-6 |
| world_building.refresh_project_config | done | 16072 | 0.019973 | 4773 | 841 | 1 | 7896 | 234 | claude-sonnet-4-6 |
| world_building.entity_discovery | done | 2410 | 0.000240 | 2530 | 167 | 1 | 2318 | 86 | gemini-2.5-flash-lite |
| world_building.character_bible | done | 15020 | 0.039641 | 15211 | 6868 | 10 | 76591 | 1941 | claude-haiku-4-5-20251001 |
| world_building.location_bible | done | 8278 | 0.009789 | 4711 | 1505 | 6 | 26856 | 650 | claude-haiku-4-5-20251001 |
| world_building.prop_bible | done | 11751 | 0.019974 | 10807 | 2832 | 18 | 141759 | 3543 | claude-haiku-4-5-20251001 |
| world_building.entity_graph | done | 9810 | 0.000329 | 143 | 513 | 1 | 54388 | 1888 | gemini-2.5-flash |
| world_building.continuity_tracking | done | 42330 | 0.037692 | 8385 | 7746 | 20 | 185809 | 5981 | claude-haiku-4-5-20251001 |
