# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T22:38:05.545243+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 2/2 | 326228 | 160456.500 | 94511.500 | $0.2750 | 14 | 2 | 7 | 16 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | yes | 303102 | 138020 | 96817 | $0.2738 | 14 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | yes | 349354 | 182893 | 92206 | $0.2765 | 14 | 4 | 14 | 32 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
