# Previz Usefulness Report v2

Recommendation: **hold**

Veo 3.1 Lite Previz cleared the quality bar, but generation cost could not be verified from the candidate metadata. Keep the deterministic default until cost evidence is available.

| Candidate | Overall | Gen Latency | Gen Cost | Resolution | Consistency | Analysis Latency | Analysis Cost |
|---|---:|---:|---:|---|---|---:|---:|
| Veo 3.1 Lite Previz | 0.903 | 39112 ms | n/a | 720p | prompt_only | 7975 ms | $0.02091 |
| Annotated Animatic | 0.813 | 0 ms | $0.0000 | 640x360 | deterministic | 6682 ms | $0.01019 |
| Veo 3.1 Fast Previz | 0.800 | 35948 ms | $0.4000 | 720p | prompt_only | 7152 ms | $0.02114 |
| Symbolic Animatic | 0.679 | 0 ms | $0.0000 | 640x360 | deterministic | 6257 ms | $0.01031 |
| Sora 2 Previz | 0.660 | 138540 ms | $0.8000 | 1280x720 | prompt_only | 6775 ms | $0.02047 |

## Candidate Notes

### Veo 3.1 Lite Previz
- variant: google_veo31_lite_previz
- engine pack: google_veo31_lite
- target model: veo-3.1-lite-generate-preview
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 0.667
- continuity: 0.600
- emotion: 1.000
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 1.000
- tone: 1.000

### Annotated Animatic
- variant: annotated_symbolic
- engine pack: n/a
- target model: n/a
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

### Veo 3.1 Fast Previz
- variant: google_veo31_fast_previz
- engine pack: google_veo31_fast
- target model: veo-3.1-fast-generate-preview
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 1.000
- color: 1.000
- continuity: 0.533
- emotion: 0.667
- evidence: 1.000
- hard_constraints: 1.000
- motion: 1.000
- summary: 0.889
- tone: 0.667

### Symbolic Animatic
- variant: symbolic
- engine pack: n/a
- target model: n/a
- style profile: CineForge Low-Fidelity Previz
- audio: 1.000
- camera: 0.500
- color: 0.667
- continuity: 0.867
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
- color: 0.833
- continuity: 0.800
- emotion: 1.000
- evidence: 1.000
- hard_constraints: 0.000
- motion: 1.000
- summary: 0.778
- tone: 1.000
