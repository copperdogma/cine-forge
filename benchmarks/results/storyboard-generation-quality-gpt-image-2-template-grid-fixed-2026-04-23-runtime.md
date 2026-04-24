# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T21:40:12.135237+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 0/2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | no | 279195 | 101933 | 15991 | $0.2398 | 0 | 0 | 0 | 0 | storyboard grid generation failed after retries: OpenAI Images API returned HTTP 400: {
  "error": {
    "message": "Unknown parameter: 'output_format'.",
    "type": "invalid_request_error",
    "param": "output_format",
    "code": "unknown_parameter"
  }
} |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | no | 237625 | 65462 | 21877 | $0.2389 | 0 | 0 | 0 | 0 | storyboard grid generation failed after retries: OpenAI Images API returned HTTP 400: {
  "error": {
    "message": "Unknown parameter: 'output_format'.",
    "type": "invalid_request_error",
    "param": "output_format",
    "code": "unknown_parameter"
  }
} |
