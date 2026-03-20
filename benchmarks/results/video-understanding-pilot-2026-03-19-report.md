# Video Benchmark Report v1

Recommendation: **hold**

Claude Sonnet 4.6 is the current leader at 0.705, but the pilot quality bar is still too low for a switch recommendation.

| Model | Overall | Python | Rubric | Latency | Cost/call | Value |
|---|---:|---:|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 0.705 | 0.802 | 0.608 | 13067 ms | $0.01411 | 49.98 |
| GPT-4.1 | 0.664 | 0.745 | 0.583 | 6524 ms | $0.00798 | 83.25 |
| Gemini 2.5 Flash | 0.163 | 0.079 | 0.247 | 7264 ms | $0.00041 | 397.80 |

## Dimension Means

### Claude Sonnet 4.6
- audio: 1.000
- camera: 0.750
- color: 1.000
- continuity: 0.833
- emotion: 0.583
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.667
- summary: 0.833
- tone: 0.750

### GPT-4.1
- audio: 1.000
- camera: 0.667
- color: 0.861
- continuity: 0.833
- emotion: 0.583
- evidence: 1.000
- hard_constraints: 1.000
- motion: 0.556
- summary: 0.778
- tone: 0.667

### Gemini 2.5 Flash
- audio: 0.167
- camera: 0.000
- color: 0.111
- continuity: 0.133
- emotion: 0.000
- evidence: 0.167
- hard_constraints: 0.167
- motion: 0.000
- summary: 0.111
- tone: 0.083
