# Runtime Media Validation Eval

Measured at: `2026-03-21T02:04:30.894509+00:00`
Fixture manifest: `benchmarks/fixtures/runtime_media_validation_cases.json`
Frontier model: `gpt-5.4`

| Approach | Overall | Semantic | Structural | Avg latency | Avg cost |
|---|---:|---:|---:|---:|---:|
| Deterministic Only | 0.750 | 0.500 | 1.000 | 428 ms | $0.000000 |
| AI-Only (gpt-5.4) | 0.500 | 1.000 | 0.000 | 2594 ms | $0.003478 |
| Hybrid (gpt-5.4) | 1.000 | 1.000 | 1.000 | 2547 ms | $0.003530 |

## Case Results

### Deterministic Only
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`skipped`; latency=`811 ms`; cost=`$0.000000`
- `prop-swap-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`730 ms`; cost=`$0.000000`
- `missing-file-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`172 ms`; cost=`$0.000000`

### AI-Only (gpt-5.4)
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`needs_review`; latency=`6170 ms`; cost=`$0.008015`
- `prop-swap-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`fail`; latency=`4030 ms`; cost=`$0.005897`
- `missing-file-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`174 ms`; cost=`$0.000000`

### Hybrid (gpt-5.4)
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`needs_review`; latency=`5437 ms`; cost=`$0.007925`
- `prop-swap-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`fail`; latency=`4568 ms`; cost=`$0.006197`
- `missing-file-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`1 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`182 ms`; cost=`$0.000000`
