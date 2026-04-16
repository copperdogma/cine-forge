# Final Render Provider Floor Runtime Matrix

- Measured at: 2026-04-16T19:28:57.081542+00:00
- Fixture manifest: `benchmarks/fixtures/final_render_provider_floor_cases.json`
- Candidate packs: openai_sora2, google_veo31, google_veo31_fast
- Comparison settings: 8s / 720p / 16:9

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Render Run ms | Mean Render Stage ms | Mean Cost | Active Inputs | Prompt Context | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI Sora 2 Render | 2/2 | 436078 | 217469.500 | 199249 | $0.0100 | 1 | 4 | 0 |
| Google Veo 3.1 Fast Render | 0/2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Google Veo 3.1 Render | 0/2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Case Runs

| Case | Candidate | Success | Total ms | Render Run ms | Render Stage ms | Cost | Direct Inputs | Prompt Context | Unsupported | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| open_frequency_scene_001_studio_night | OpenAI Sora 2 Render | yes | 486853 | 242355 | 223018 | $0.0092 | 1 | 4 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_001_studio_night | Google Veo 3.1 Render | no | 256262 | 11764 | 11702 | $0.0000 | 0 | 0 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_001_studio_night | Google Veo 3.1 Fast Render | no | 255785 | 11287 | 11222 | $0.0000 | 0 | 0 | 0 | Interior ensemble control case with storm pressure, project taste refs, one hard-locked scene image, and canonical character/location visuals. |
| open_frequency_scene_002_water_tower_night | OpenAI Sora 2 Render | yes | 385303 | 192584 | 175480 | $0.0115 | 1 | 4 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
| open_frequency_scene_002_water_tower_night | Google Veo 3.1 Render | no | 201253 | 8534 | 8478 | $0.0000 | 0 | 0 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
| open_frequency_scene_002_water_tower_night | Google Veo 3.1 Fast Render | no | 201571 | 8852 | 8798 | $0.0000 | 0 | 0 | 0 | Exterior contrast case with wind, height, lantern warmth against a dark town, and the same multi-reference conditioning pattern. |
