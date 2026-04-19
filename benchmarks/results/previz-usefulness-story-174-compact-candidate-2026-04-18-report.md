# Previz Usefulness Report v2

Recommendation: **hold_ai_primary_blocked**

Deterministic baseline measured 581 ms and stays inside the 6000 ms control bar, but it does not satisfy the product previz requirement. Veo 3.1 Lite Compact Previz is the strongest current AI lane at 0.875 overall and 39357 ms generation latency, so AI previz remains the intended primary lane while runtime work stays blocked.

| Candidate | Lane | Overall | Gen Latency | Budget | Gen Cost | Resolution | Consistency | Prompt | Analysis Latency | Analysis Cost |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|
| Veo 3.1 Lite Compact Previz | ai_previz | 0.875 | 39357 ms | 180000 ms | n/a | 720p | prompt_only | compact | 6489 ms | $0.02025 |
| Veo 3.1 Lite Previz | ai_previz | 0.868 | 46838 ms | 180000 ms | n/a | 720p | prompt_only | standard | 6983 ms | $0.02075 |
| Annotated Animatic | deterministic_baseline | 0.855 | 581 ms | 6000 ms | $0.0000 | 640x360 | deterministic | n/a | 5935 ms | $0.00992 |

## Candidate Notes

### Veo 3.1 Lite Compact Previz
- lane: ai_previz
- variant: google_veo31_lite_compact_previz
- latency budget: 180000
- engine pack: google_veo31_lite
- target model: veo-3.1-lite-generate-preview
- prompt profile: compact
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 1.000
- continuity: 0.533
- emotion: 1.000
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.889
- tone: 0.667

### Veo 3.1 Lite Previz
- lane: ai_previz
- variant: google_veo31_lite_previz
- latency budget: 180000
- engine pack: google_veo31_lite
- target model: veo-3.1-lite-generate-preview
- prompt profile: standard
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 1.000
- continuity: 0.800
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.889
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
- color: 1.000
- continuity: 0.800
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.889
- tone: 0.667
