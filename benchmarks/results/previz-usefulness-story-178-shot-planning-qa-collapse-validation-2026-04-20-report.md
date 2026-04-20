# Previz Usefulness Report v2

Recommendation: **hold_ai_primary_blocked**

Deterministic baseline measured 618 ms and stays inside the 6000 ms control bar, but it does not satisfy the product previz requirement. Grok Imagine Previz is the strongest current AI lane at 0.900 overall and 17935 ms generation latency, so AI previz remains the intended primary lane while runtime work stays blocked.

| Candidate | Lane | Overall | Gen Latency | Budget | Gen Cost | Resolution | Consistency | Prompt | Analysis Latency | Analysis Cost |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|
| Grok Imagine Previz | ai_previz | 0.900 | 17935 ms | 180000 ms | n/a | 480p | prompt_only | standard | 7539 ms | $0.01287 |
| Annotated Animatic | deterministic_baseline | 0.838 | 618 ms | 6000 ms | $0.0000 | 640x360 | deterministic | n/a | 8030 ms | $0.01104 |
| Symbolic Animatic | deterministic_baseline | 0.665 | 445 ms | n/a | $0.0000 | 640x360 | deterministic | n/a | 7727 ms | $0.01062 |

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
- color: 0.833
- continuity: 0.800
- emotion: 0.833
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.778
- tone: 1.000

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
- color: 0.833
- continuity: 0.800
- emotion: 0.667
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
- summary: 0.778
- tone: 0.667
