# Storyboard Generation Quality Decision

Recommendation: **lane_drops_references_before_generation**

The default storyboard lane had reference images available on the project state, but the measured prompt-reference and direct-reference counts stayed at zero. That is a structural failure before any subjective image judging.

| Candidate | Quality | Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | Frames | Available Refs | Prompt Ref Frames | Direct Refs | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Imagen 4 Storyboards | 0.538 | 0.541 | 0.535 | 391283 | 147876.500 | $0.7990 | 14 | 2 | 0 | 0 | 1 |
