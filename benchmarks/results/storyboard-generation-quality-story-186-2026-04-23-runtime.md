# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T13:49:50.937096+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: imagen_4_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Imagen 4 Storyboards | 2/2 | 485361 | 310121.500 | 216543.500 | $0.6410 | 14.500 | 2 | 7.500 | 15.500 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | Imagen 4 Storyboards | yes | 409422 | 248317 | 151806 | $0.8019 | 14 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | Imagen 4 Storyboards | yes | 561300 | 371926 | 281281 | $0.4798 | 15 | 4 | 15 | 31 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
