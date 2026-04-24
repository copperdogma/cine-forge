# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T20:11:57.817614+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Storyboards | 2/2 | 672297 | 505102 | 410166 | $0.4470 | 15 | 2 | 7 | 15 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Storyboards | yes | 711045 | 540264 | 442356 | $0.4636 | 16 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Storyboards | yes | 633549 | 469940 | 377976 | $0.4300 | 14 | 4 | 14 | 30 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
