# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-25T01:26:11.095129+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards, gpt_image_2_template_grid_reference_anchors

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 1/1 | 331391 | 169090 | 84651 | $0.2730 | 15 | 4 | 15 | 35 |
| GPT Image 2 Template Grid Reference Anchors | 1/1 | 373819 | 187692 | 82554 | $0.2760 | 15 | 4 | 15 | 31 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | yes | 331391 | 169090 | 84651 | $0.2727 | 15 | 4 | 15 | 35 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Reference Anchors | yes | 373819 | 187692 | 82554 | $0.2762 | 15 | 4 | 15 | 31 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
