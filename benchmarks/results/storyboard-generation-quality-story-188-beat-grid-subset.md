# Storyboard Generation Quality Runtime Matrix

- Measured at: 2026-04-24T18:43:17.693600+00:00
- Fixture manifest: `benchmarks/fixtures/storyboard_generation_quality_cases.json`
- Candidates: gpt_image_2_beat_grid_storyboards

## Candidate Summary

| Candidate | Success | Mean Total ms | Mean Storyboard ms | Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | Prompt Ref Frames | Direct Refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Beat Grid Storyboards | 0/1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Case Runs

| Case | Candidate | Success | Total ms | Storyboard ms | Storyboard Stage ms | Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Open Frequency scenes 001-002 — prompt-only storyboard identity | GPT Image 2 Beat Grid Storyboards | no | 277769 | 114300 | 18159 | $0.2402 | 0 | 0 | 0 | 0 | storyboard grid generation failed after retries: OpenAI Images API returned HTTP 400: {
  "error": {
    "message": "Invalid value: 'gpt-image-2'. Value must be 'dall-e-2'.",
    "type": "invalid_request_error",
    "param": "model",
    "code": "invalid_value"
  }
} |
