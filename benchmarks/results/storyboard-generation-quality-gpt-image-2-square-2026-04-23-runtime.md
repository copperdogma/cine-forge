# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T20:49:32.166231+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_square_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Square Storyboards | 2/2 | 615142.500 | 445482 | 382345 | $0.3650 | 14.500 | 2 | 7 | 15.500 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Square Storyboards | yes | 602862 | 437984 | 391360 | $0.3707 | 15 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Square Storyboards | yes | 627423 | 452980 | 373330 | $0.3601 | 14 | 4 | 14 | 31 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
