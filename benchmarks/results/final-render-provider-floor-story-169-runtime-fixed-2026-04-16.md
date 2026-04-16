# Final Render Provider Floor Runtime Matrix

- Measured at: 2026-04-16T20:08:58.357593+00:00
- Fixture manifest: `benchmarks/fixtures/final_render_provider_floor_cases.json`
- Candidate packs: openai_sora2, google_veo31, google_veo31_fast
- Comparison settings: 8s / 720p / 16:9

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Render Run ms | Mean Render Stage ms | Mean Cost | Active Inputs | Prompt Context | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Google Veo 3.1 Fast Render | 2/2 | 245715 | 52730 | 46782.500 | $0.0120 | 3 | 2 | 0 |
| Google Veo 3.1 Render | 2/2 | 245735 | 52750 | 46554 | $0.0120 | 3 | 2 | 0 |
| OpenAI Sora 2 Render | 2/2 | 390476.500 | 197491.500 | 184615 | $0.0120 | 1 | 4 | 0 |

## Case Runs

| Case | Candidate | Success | Total ms | Render Run ms | Render Stage ms | Cost | Direct Inputs | Prompt Context | Unsupported | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| open_frequency_scene_001_studio_night | OpenAI Sora 2 Render | yes | 391160 | 200152 | 182955 | $0.0125 | 1 | 4 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_001_studio_night | Google Veo 3.1 Render | yes | 250933 | 59925 | 52537 | $0.0133 | 3 | 2 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_001_studio_night | Google Veo 3.1 Fast Render | yes | 240283 | 49275 | 42399 | $0.0134 | 3 | 2 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_002_water_tower_night | OpenAI Sora 2 Render | yes | 389793 | 194831 | 186275 | $0.0112 | 1 | 4 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
| open_frequency_scene_002_water_tower_night | Google Veo 3.1 Render | yes | 240537 | 45575 | 40571 | $0.0109 | 3 | 2 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
| open_frequency_scene_002_water_tower_night | Google Veo 3.1 Fast Render | yes | 251147 | 56185 | 51166 | $0.0111 | 3 | 2 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
