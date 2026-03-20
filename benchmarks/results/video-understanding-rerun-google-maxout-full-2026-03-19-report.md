# Video Benchmark Report v1

Recommendation: **hold**

GPT-5.4 is the current leader at 0.792, but the pilot quality bar is still too low for a switch recommendation.

| Model | Overall | Python | Rubric | Latency | Cost/call | Value |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.4 | 0.792 | 0.861 | 0.723 | 5492 ms | $0.01006 | 78.76 |
| Claude Sonnet 4.6 | 0.697 | 0.804 | 0.590 | 13192 ms | $0.01397 | 49.89 |
| Gemini 2.5 Flash | 0.652 | 0.750 | 0.555 | 8706 ms | $0.00055 | 1183.85 |
| Gemini 3.1 Pro Preview | 0.634 | 0.707 | 0.562 | 14711 ms | $0.01261 | 50.29 |
| Gemini 2.5 Pro | 0.566 | 0.662 | 0.470 | 16244 ms | $0.00630 | 89.94 |
| Gemini 3 Flash Preview | 0.547 | 0.653 | 0.442 | 10566 ms | $0.00111 | 493.24 |

## Dimension Means

### GPT-5.4
- audio: 1.000
- camera: 0.750
- color: 1.000
- continuity: 0.867
- emotion: 1.000
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.722
- summary: 0.833
- tone: 0.750

### Claude Sonnet 4.6
- audio: 1.000
- camera: 0.667
- color: 0.917
- continuity: 0.700
- emotion: 0.583
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.833
- summary: 0.944
- tone: 0.750

### Gemini 2.5 Flash
- audio: 0.883
- camera: 0.583
- color: 0.778
- continuity: 0.833
- emotion: 0.583
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.778
- summary: 0.833
- tone: 0.667

### Gemini 3.1 Pro Preview
- audio: 1.000
- camera: 0.583
- color: 0.861
- continuity: 0.833
- emotion: 0.417
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.556
- summary: 0.667
- tone: 0.750

### Gemini 2.5 Pro
- audio: 1.000
- camera: 0.583
- color: 0.778
- continuity: 0.700
- emotion: 0.417
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.556
- summary: 0.556
- tone: 0.750

### Gemini 3 Flash Preview
- audio: 1.000
- camera: 0.417
- color: 0.806
- continuity: 0.867
- emotion: 0.417
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.556
- summary: 0.556
- tone: 0.667
