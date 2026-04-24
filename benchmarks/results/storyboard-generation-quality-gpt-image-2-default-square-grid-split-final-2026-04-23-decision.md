# Storyboard Generation Quality Decision

Recommendation: **quality_below_initial_floor**

The current default storyboard lane scored 0.735, below the initial 0.75 usefulness floor. The eval is doing its job by making that failure repeatable instead of anecdotal.

| Candidate | Quality | Story | Style | Identity | Reference | Text | Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Storyboards | 0.735 | 1 | 1 | 0.500 | 0.750 | 0.500 | 0.785 | 0.685 | 672297 | 410166 | $0.4470 | 15 | 2 | 7 | 15 | 1 |
| GPT Image 2 Square Storyboards | 0.729 | 0.750 | 1 | 0.625 | 0.750 | 1 | 0.823 | 0.635 | 615142.500 | 382345 | $0.3650 | 14.500 | 2 | 7 | 15.500 | 1 |
| GPT Image 2 Template Grid Storyboards | 0.677 | 0.500 | 1 | 0.500 | 0.750 | 1 | 0.745 | 0.610 | 326228 | 94511.500 | $0.2750 | 14 | 2 | 7 | 16 | 1 |
