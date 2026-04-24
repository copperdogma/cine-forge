# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T05:41:05.660721+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: imagen_4_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Imagen 4 Storyboards | 2/2 | 391283 | 213616.500 | 147876.500 | $0.7990 | 14 | 2 | 0 | 0 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | Imagen 4 Storyboards | yes | 389727 | 210564 | 160844 | $0.8450 | 15 | 0 | 0 | 0 | Baseline storyboard case with recurring ARIA and NOAH but no attached character/location reference images. |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | Imagen 4 Storyboards | yes | 392839 | 216669 | 134909 | $0.7536 | 13 | 4 | 0 | 0 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
