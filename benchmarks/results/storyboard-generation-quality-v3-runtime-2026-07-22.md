# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-07-23T03:08:34.990827+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards, gpt_image_2_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 2/2 | 366968 | 203075 | 110761.500 | $0.2720 | 15 | 2 | 7.500 | 16.500 |
| GPT Image 2 Storyboards | 2/2 | 645751 | 483427.500 | 413651 | $0.4200 | 14.500 | 2 | 7 | 16.500 |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | yes | 364043 | 201842 | 105810 | $0.2689 | 15 | 0 | 0 | 0 | Prompt-only control for source-specific story coverage, medium consistency, and two recurring visual subjects. |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Storyboards | yes | 571471 | 405911 | 359962 | $0.4299 | 15 | 0 | 0 | 0 | Prompt-only control for source-specific story coverage, medium consistency, and two recurring visual subjects. |
| Open Frequency scenes 001-002 — reference-transport control | GPT Image 2 Template Grid Storyboards | yes | 369893 | 204308 | 115713 | $0.2746 | 15 | 4 | 15 | 33 | Same source sequence with four abstract transport-only reference cards. The cards prove transport mechanics, not realistic identity or location fidelity. |
| Open Frequency scenes 001-002 — reference-transport control | GPT Image 2 Storyboards | yes | 720031 | 560944 | 467340 | $0.4091 | 14 | 4 | 14 | 33 | Same source sequence with four abstract transport-only reference cards. The cards prove transport mechanics, not realistic identity or location fidelity. |
