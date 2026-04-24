# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T22:24:08.672423+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 2/2 | 354492 | 187301 | 91184.500 | $0.2790 | 15.500 | 2 | 7.500 | 17 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | yes | 361013 | 193169 | 93242 | $0.2816 | 16 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | yes | 347971 | 181433 | 89127 | $0.2761 | 15 | 4 | 15 | 34 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
