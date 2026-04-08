# Real AI Previz Runtime Shared-Substrate Summary

- Measured at: 2026-04-08T21:47:44.243828+00:00
- Comparison method: `shared_shot_planning_substrate_manual_repeats`
- Scope: four `scene_ready` AI-previz pack candidates compared from identical precomputed `shot_planning` state
- Shared prerequisite median: 92314 ms
- Recommended shipped case: `shipped_lite_4_scene_ready`
- Recommended median total runtime: 142634 ms
- Recommended median AI-previz runtime: 50320 ms
- Recorded eval cost (excluding provider video cost when unavailable): $0.18958
- Note: Three shared-shot-planning scene-ready passes keep Veo 3.1 Lite 4s as the best median runtime lane. A direct repeat-count run later stalled on a provider-side hang during repeat 2, so the repeated evidence is preserved as sequential one-repeat runs plus the salvaged first pass.

## Median Ranking

| Case | Engine Pack | Usefulness | Median AI Previz ms | Median Total ms | AI Range | Total Range |
| --- | --- | ---: | ---: | ---: | --- | --- |
| shipped_lite_4_scene_ready | google_veo31_lite / 4s 720p | 0.828 | 50320 | 142634 | 37615-60536 ms | 125714-229550 ms |
| fast_4_scene_ready | google_veo31_fast / 4s 720p | 0.778 | 57186 | 145285 | 40196-72490 ms | 132510-241504 ms |
| veo31_4_scene_ready | google_veo31 / 4s 720p | n/a | 57623 | 150847 | 50828-58533 ms | 138927-226637 ms |
| lite_8_scene_ready_control | google_veo31_lite / 8s 1280x720 | n/a | 60857 | 155501 | 59370-63187 ms | 148956-228384 ms |

## Decision

- Keep `google_veo31_lite` at `4s / 720p` as the shipped slower AI-previz lane.
- It beats the old Lite 8s control on median total runtime and median isolated AI-previz runtime.
- It also beats the Fast 4s candidate on both median runtime and existing usefulness evidence (`0.828` vs `0.778`).
- One direct `--repeat-count 3` attempt stalled on a provider-side hang during `shipped_lite_4_scene_ready-ai-previz-r2-0443`, so the repeated evidence is recorded as sequential one-repeat passes plus the salvaged first pass instead of a single monolithic run artifact.

## Passes

| Pass | Shared Prereq ms | Shipped Lite 4 | Lite 8 Control | Fast 4 | Veo 3.1 4s |
| --- | ---: | ---: | ---: | ---: | ---: |
| pass1_salvaged_from_run_state | 169014 | 229550 | 228384 | 241504 | 226637 |
| pass2 | 92314 | 142634 | 155501 | 132510 | 150847 |
| pass3 | 88099 | 125714 | 148956 | 145285 | 138927 |
