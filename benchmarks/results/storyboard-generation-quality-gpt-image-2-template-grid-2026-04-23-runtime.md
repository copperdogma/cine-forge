# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-23T21:28:45.302951+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_template_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 0/2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Template Grid Storyboards | no | 283929 | 112307 | 14446 | $0.2533 | 0 | 0 | 0 | 0 | storyboard grid generation failed after retries: OpenAI Images API returned HTTP 400: {
  "error": {
    "message": "Unknown parameter: 'quality'.",
    "type": "invalid_request_error",
    "param": "quality",
    "code": "unknown_parameter"
  }
} |
| Open Frequency scenes 001-002 — reference-conditioned storyboard sequence | GPT Image 2 Template Grid Storyboards | no | 271302 | 99611 | 15145 | $0.2403 | 0 | 0 | 0 | 0 | storyboard grid generation failed after retries: OpenAI Images API returned HTTP 400: {
  "error": {
    "message": "Unknown parameter: 'quality'.",
    "type": "invalid_request_error",
    "param": "quality",
    "code": "unknown_parameter"
  }
} |
