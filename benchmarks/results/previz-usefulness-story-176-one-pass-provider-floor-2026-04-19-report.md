# Previz Usefulness Report v2

Recommendation: **hold_ai_primary_blocked**

Deterministic baseline measured 616 ms and stays inside the 6000 ms control bar, but it does not satisfy the product previz requirement. Veo 3.1 Lite Previz is the strongest current AI lane at 0.898 overall and 39361 ms generation latency, so AI previz remains the intended primary lane while runtime work stays blocked.

| Candidate | Lane | Overall | Gen Latency | Budget | Gen Cost | Resolution | Consistency | Prompt | Analysis Latency | Analysis Cost |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|
| Veo 3.1 Lite Previz | ai_previz | 0.898 | 39361 ms | 180000 ms | n/a | 720p | prompt_only | standard | 6629 ms | $0.02037 |
| Veo 3.1 Fast Previz | ai_previz | 0.863 | 52765 ms | 180000 ms | $0.4000 | 720p | prompt_only | standard | 6811 ms | $0.02048 |
| Grok Imagine Previz | ai_previz | 0.842 | 16009 ms | 180000 ms | n/a | 480p | prompt_only | standard | 7655 ms | $0.01336 |
| Annotated Animatic | deterministic_baseline | 0.820 | 616 ms | 6000 ms | $0.0000 | 640x360 | deterministic | n/a | 5807 ms | $0.00998 |
| Symbolic Animatic | deterministic_baseline | 0.665 | 446 ms | n/a | $0.0000 | 640x360 | deterministic | n/a | 7105 ms | $0.01059 |

## Candidate Notes

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
- emotion: 1.000
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.778
- tone: 0.667

### Veo 3.1 Fast Previz
- lane: ai_previz
- variant: google_veo31_fast_previz
- latency budget: 180000
- engine pack: google_veo31_fast
- target model: veo-3.1-fast-generate-preview
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
- summary: 0.778
- tone: 1.000

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
- continuity: 0.867
- emotion: 0.500
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
- color: 0.833
- continuity: 0.800
- emotion: 0.500
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.889
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
