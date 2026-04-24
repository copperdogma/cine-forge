# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T13:32:06.193342+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: imagen_4_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Imagen 4 Storyboards | 1/1 | 561492 | 371962 | 281281 | $0.4800 | 15 | 4 | 15 | 31 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | Imagen 4 Storyboards | yes | 561492 | 371962 | 281281 | $0.4798 | 15 | 4 | 15 | 31 | Same two-scene sequence, but with canonical character and location reference images attached before storyboard generation. |
