# Video Benchmark Report v1

Recommendation: **hold**

GPT-5.4 is the current leader at 0.792, but the pilot quality bar is still too low for a switch recommendation.

| Model | Overall | Python | Rubric | Latency | Cost/call | Value |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.4 | 0.792 | 0.861 | 0.723 | 5492 ms | $0.01006 | 78.76 |
| Claude Sonnet 4.6 | 0.697 | 0.804 | 0.590 | 13192 ms | $0.01397 | 49.89 |
| Gemini 3 Flash Preview | 0.349 | 0.336 | 0.362 | 7617 ms | $0.00105 | 333.37 |
| Gemini 3.1 Pro Preview | 0.281 | 0.123 | 0.440 | 14175 ms | $0.01155 | 24.35 |
| Gemini 2.5 Flash | 0.156 | 0.079 | 0.233 | 6954 ms | $0.00038 | 405.45 |
| Gemini 2.5 Pro | 0.149 | 0.115 | 0.183 | 13752 ms | $0.00328 | 45.52 |

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

### Gemini 3 Flash Preview
- audio: 0.450
- camera: 0.250
- color: 0.333
- continuity: 0.400
- emotion: 0.250
- evidence: 0.500
- hard_constraints: 0.500
- motion: 0.500
- summary: 0.167
- tone: 0.417

### Gemini 3.1 Pro Preview
- audio: 0.167
- camera: 0.083
- color: 0.167
- continuity: 0.133
- emotion: 0.083
- evidence: 0.167
- hard_constraints: 0.167
- motion: 0.167
- summary: 0.056
- tone: 0.167

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

### Gemini 2.5 Pro
- audio: 0.167
- camera: 0.083
- color: 0.167
- continuity: 0.167
- emotion: 0.000
- evidence: 0.167
- hard_constraints: 0.167
- motion: 0.167
- summary: 0.111
- tone: 0.083
