# Previz Usefulness Report v2

Recommendation: **hold**

Veo 3.1 Lite Previz is the best AI lane at 0.828, but Annotated Animatic still leads or remains within the noise band at 0.803. Keep the deterministic default.

| Candidate | Overall | Gen Latency | Gen Cost | Resolution | Consistency | Analysis Latency | Analysis Cost |
|---|---:|---:|---:|---|---|---:|---:|
| Veo 3.1 Lite Previz | 0.828 | 39273 ms | n/a | 720p | prompt_only | 8121 ms | $0.02093 |
| Annotated Animatic | 0.803 | 0 ms | $0.0000 | 640x360 | deterministic | 6588 ms | $0.01024 |
| Veo 3.1 Fast Previz | 0.778 | 32366 ms | $0.4000 | 720p | prompt_only | 7595 ms | $0.02139 |
| Sora 2 Previz | 0.659 | 106736 ms | $0.8000 | 1280x720 | prompt_only | 7357 ms | $0.02159 |
| Symbolic Animatic | 0.655 | 0 ms | $0.0000 | 640x360 | deterministic | 6311 ms | $0.01012 |

## Candidate Notes

### Veo 3.1 Lite Previz
- variant: google_veo31_lite_previz
- engine pack: google_veo31_lite
- target model: veo-3.1-lite-generate-preview
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 1.000
- continuity: 0.800
- emotion: 0.500
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.778
- tone: 0.667

### Annotated Animatic
- variant: annotated_symbolic
- engine pack: n/a
- target model: n/a
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 0.833
- continuity: 0.800
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.667
- tone: 0.667

### Veo 3.1 Fast Previz
- variant: google_veo31_fast_previz
- engine pack: google_veo31_fast
- target model: veo-3.1-fast-generate-preview
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 0.833
- color: 1.000
- continuity: 0.800
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.667
- tone: 0.667

### Sora 2 Previz
- variant: openai_sora2_previz
- engine pack: openai_sora2
- target model: sora-2
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 0.667
- continuity: 0.800
- emotion: 0.833
- evidence: 1.000
- hard_constraints: 0.000
- motion: 1.000
- summary: 0.889
- tone: 1.000

### Symbolic Animatic
- variant: symbolic
- engine pack: n/a
- target model: n/a
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
