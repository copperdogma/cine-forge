# Storyboard Generation Quality Decision

Recommendation: **quality_below_initial_floor**

The current default storyboard lane scored 0.571, below the initial 0.75 usefulness floor. The eval is doing its job by making that failure repeatable instead of anecdotal.

| Candidate | Quality | Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Storyboards | 0.571 | 0.741 | 0.400 | 672297 | 410166 | $0.4470 | 15 | 2 | 7 | 15 | 1 |
