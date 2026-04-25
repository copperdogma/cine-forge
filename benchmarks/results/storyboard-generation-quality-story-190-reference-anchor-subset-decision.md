# Storyboard Generation Quality Decision

Recommendation: **quality_below_initial_floor**

The current default storyboard lane scored 0.700, below the initial 0.75 usefulness floor. The eval is doing its job by making that failure repeatable instead of anecdotal.

| Candidate | Quality | Story | Style | Identity | Reference | Text | Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 2 Template Grid Storyboards | 0.700 | 0.750 | 1 | 0.500 | 0.500 | 1 | 0.750 | 0.650 | 331391 | 84651 | $0.2730 | 15 | 4 | 15 | 35 | 1 |
| GPT Image 2 Template Grid Reference Anchors | 0.685 | 0.750 | 1 | 0.500 | 0.500 | 1 | 0.750 | 0.620 | 373819 | 82554 | $0.2760 | 15 | 4 | 15 | 31 | 1 |
