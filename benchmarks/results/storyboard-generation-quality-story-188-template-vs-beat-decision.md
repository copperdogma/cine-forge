# Storyboard Generation Quality Decision

Recommendation: **quality_below_initial_floor**

The current default storyboard lane scored 0.675, below the initial 0.75 usefulness floor. The eval is doing its job by making that failure repeatable instead of anecdotal.

| Candidate | Quality | Story | Style | Identity | Reference | Text | Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 0.675 | 0.625 | 1 | 0.750 | 0.750 | 1 | 0.825 | 0.525 | 307561 | 91312.500 | $0.2750 | 14.500 | 2 | 7 | 15.500 | 1 |
| GPT Image 2 Beat Grid Storyboards | 0.579 | 0.625 | 1 | 0.375 | 0.750 | 1 | 0.708 | 0.450 | 341317.500 | 89242 | $0.2750 | 15 | 2 | 7.500 | 16.500 | 1 |
