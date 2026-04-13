# Runtime Media Validation Eval

Measured at: `2026-04-13T05:38:13.840690+00:00`
Fixture manifest: `benchmarks/fixtures/runtime_final_output_validation_cases.json`
Frontier model: `gpt-5.4`

| Approach | Overall | Semantic | Structural | Avg latency | Avg cost |
|---|---:|---:|---:|---:|---:|
| Deterministic Only | 0.500 | 0.000 | 1.000 | 470 ms | $0.000000 |
| AI-Only (gpt-5.4) | 0.500 | 1.000 | 0.000 | 1386 ms | $0.002721 |
| Hybrid (gpt-5.4) | 1.000 | 1.000 | 1.000 | 1450 ms | $0.002700 |

## Case Results

### Deterministic Only
- `partial-project-cut-review`: expected `valid`, got `needs_review` (mismatch); semantic=`skipped`; latency=`880 ms`; cost=`$0.000000`
- `complete-project-cut-review`: expected `valid`, got `needs_review` (mismatch); semantic=`skipped`; latency=`801 ms`; cost=`$0.000000`
- `missing-project-cut-file`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-project-cut-decode`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`198 ms`; cost=`$0.000000`

### AI-Only (gpt-5.4)
- `partial-project-cut-review`: expected `valid`, got `valid` (match); semantic=`pass`; latency=`2738 ms`; cost=`$0.005540`
- `complete-project-cut-review`: expected `valid`, got `valid` (match); semantic=`pass`; latency=`2616 ms`; cost=`$0.005343`
- `missing-project-cut-file`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-project-cut-decode`: expected `needs_revision`, got `needs_review` (mismatch); semantic=`skipped`; latency=`189 ms`; cost=`$0.000000`

### Hybrid (gpt-5.4)
- `partial-project-cut-review`: expected `valid`, got `valid` (match); semantic=`pass`; latency=`2874 ms`; cost=`$0.005367`
- `complete-project-cut-review`: expected `valid`, got `valid` (match); semantic=`pass`; latency=`2735 ms`; cost=`$0.005435`
- `missing-project-cut-file`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`0 ms`; cost=`$0.000000`
- `corrupt-project-cut-decode`: expected `needs_revision`, got `needs_revision` (match); semantic=`skipped`; latency=`193 ms`; cost=`$0.000000`
