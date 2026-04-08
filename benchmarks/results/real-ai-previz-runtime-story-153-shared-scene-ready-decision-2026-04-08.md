# Real AI Previz Runtime Decision Summary

- Generated at: 2026-04-08T22:37:02.471728+00:00
- Base summary: `/Users/cam/.codex/worktrees/7723/cine-forge/benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-summary-2026-04-08.json`
- Additional result files: 1
- Current shipped case: `shipped_lite_4_scene_ready`
- Runtime winner: `fast_4_scene_ready` (164799 ms)
- Isolated AI-previz runtime winner: `fast_4_scene_ready` (52196 ms)
- Usefulness leader: `shipped_lite_4_scene_ready` (0.828)
- Leaders diverge: yes
- Note: Runtime leader (fast_4_scene_ready) and usefulness leader (shipped_lite_4_scene_ready) diverge. Current shipped case is shipped_lite_4_scene_ready. No dominant winner is proven by the combined evidence alone.

## Cases

| Case | Samples | Engine Pack | Usefulness | Median AI Previz ms | Median Total ms | Delta vs Runtime Winner | Notes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| fast_4_scene_ready | 4 | google_veo31_fast / 4s 720p | 0.778 | 52196 | 164799 | +0 ms total / +0 ms ai | Existing previz-usefulness runner-up among AI lanes. |
| veo31_4_scene_ready | 4 | google_veo31 / 4s 720p | n/a | 54226 | 167958 | +3159 ms total / +2030 ms ai | Runtime control only; no stronger usefulness case than Lite 4. |
| shipped_lite_4_scene_ready | 4 | google_veo31_lite / 4s 720p | 0.828 | 55428 | 171007 | +6208 ms total / +3232 ms ai | Existing previz-usefulness leader among current AI lanes. |
| lite_8_scene_ready_control | 4 | google_veo31_lite / 8s 1280x720 | n/a | 62022 | 181813 | +17014 ms total / +9826 ms ai | Control only; same engine family as Lite 4 but slower. |
