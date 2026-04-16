# Final Render Provider Floor Decision

Recommendation: **switch_default_to_google_veo31**

Google Veo 3.1 Render beat the current default by 0.138 quality points, stayed within 0.63x of the current total runtime, and preserved more direct image conditioning on average. That is a defensible provider-floor improvement instead of noisy churn.

| Candidate | Quality | Python | Rubric | Mean Total ms | Mean Render ms | Mean Cost | Direct Inputs | Prompt Context | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Google Veo 3.1 Render | 0.750 | 0.764 | 0.735 | 245735 | 46554 | $0.0120 | 3 | 2 | 1 |
| OpenAI Sora 2 Render | 0.611 | 0.638 | 0.585 | 390476.500 | 184615 | $0.0120 | 1 | 4 | 1 |
| Google Veo 3.1 Fast Render | 0.606 | 0.618 | 0.595 | 245715 | 46782.500 | $0.0120 | 3 | 2 | 1 |
