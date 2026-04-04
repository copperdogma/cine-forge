# Runtime Media Validation Eval

Measured at: `2026-04-04T05:47:45.748947+00:00`
Fixture manifest: `benchmarks/fixtures/runtime_media_validation_cases.json`
Frontier model: `gpt-5.4`

| Approach | Overall | Semantic | Structural | Avg latency | Avg cost |
|---|---:|---:|---:|---:|---:|
| Deterministic Only | 0.750 | 0.500 | 1.000 | 465 ms | $0.000000 |
| AI-Only (gpt-5.4) | 0.500 | 1.000 | 0.000 | 2736 ms | $0.003520 |
| Hybrid (gpt-5.4) | 1.000 | 1.000 | 1.000 | 2281 ms | $0.003313 |

## Case Results

### Deterministic Only
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`skipped`; latency=`861 ms`; cost=`$0.000000`
- `prop-swap-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`797 ms`; cost=`$0.000000`
- `missing-file-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`201 ms`; cost=`$0.000000`

### AI-Only (gpt-5.4)
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`needs_review`; latency=`6758 ms`; cost=`$0.007910`
- `prop-swap-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`fail`; latency=`3979 ms`; cost=`$0.006168`
- `missing-file-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`207 ms`; cost=`$0.000000`

### Hybrid (gpt-5.4)
- `quiet-bedside-review`: expected `needs_review`, got `needs_review` (match); semantic=`needs_review`; latency=`5345 ms`; cost=`$0.007085`
- `prop-swap-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`fail`; latency=`3569 ms`; cost=`$0.006168`
- `missing-file-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`1 ms`; cost=`$0.000000`
- `corrupt-decode-revision`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`208 ms`; cost=`$0.000000`
