# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-24T20:10:29.716803+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards, gpt_image_2_beat_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 2/2 | 307561 | 136142 | 91312.500 | $0.2750 | 14.500 | 2 | 7 | 15.500 |
| GPT Image 2 Beat Grid Storyboards | 2/2 | 341317.500 | 180064 | 89242 | $0.2750 | 15 | 2 | 7.500 | 16.500 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | yes | 310958 | 134906 | 89280 | $0.2774 | 15 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Beat Grid Storyboards | yes | 336501 | 174806 | 84127 | $0.2774 | 15 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | yes | 304164 | 137378 | 93345 | $0.2721 | 14 | 4 | 14 | 31 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Beat Grid Storyboards | yes | 346134 | 185322 | 94357 | $0.2733 | 15 | 4 | 15 | 33 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
