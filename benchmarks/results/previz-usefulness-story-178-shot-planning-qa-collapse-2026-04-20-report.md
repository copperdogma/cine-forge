# Previz Usefulness Report v2

Recommendation: **hold_ai_primary_blocked**

Deterministic baseline measured 601 ms and stays inside the 6000 ms control bar, but it does not satisfy the product previz requirement. Grok Imagine Previz is the strongest current AI lane at 0.838 overall and 17549 ms generation latency, so AI previz remains the intended primary lane while runtime work stays blocked.

| Candidate | Lane | Overall | Gen Latency | Budget | Gen Cost | Resolution | Consistency | Prompt | Analysis Latency | Analysis Cost |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|
| Grok Imagine Previz | ai_previz | 0.838 | 17549 ms | 180000 ms | n/a | 480p | prompt_only | standard | 6332 ms | $0.01286 |
| Annotated Animatic | deterministic_baseline | 0.818 | 601 ms | 6000 ms | $0.0000 | 640x360 | deterministic | n/a | 7070 ms | $0.01077 |
| Symbolic Animatic | deterministic_baseline | 0.685 | 480 ms | n/a | $0.0000 | 640x360 | deterministic | n/a | 6714 ms | $0.01047 |

## Candidate Notes

### Grok Imagine Previz
- lane: ai_previz
- variant: xai_grok_imagine_video_previz
- latency budget: 180000
- engine pack: xai_grok_imagine_video
- target model: grok-imagine-video
- prompt profile: standard
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 0.667
- continuity: 0.800
- emotion: 0.500
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 1.000
- tone: 0.667

### Annotated Animatic
- lane: deterministic_baseline
- variant: annotated_symbolic
- latency budget: 6000
- engine pack: n/a
- target model: n/a
- prompt profile: n/a
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 0.667
- continuity: 0.800
- emotion: 0.500
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 1.000
- tone: 0.667

### Symbolic Animatic
- lane: deterministic_baseline
- variant: symbolic
- latency budget: n/a
- engine pack: n/a
- target model: n/a
- prompt profile: n/a
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 0.500
- color: 0.667
- continuity: 0.800
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.667
- tone: 0.667
