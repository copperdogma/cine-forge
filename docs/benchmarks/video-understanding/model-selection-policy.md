# Video Understanding Model Selection Policy

## Decision Outputs

The benchmark report emits one of:

- `adopt`
- `hold`
- `retest`

## Adopt

Recommend `adopt` only when all of these are true:

- leader is at or above `0.80` overall on the verified run
- leader beats the next model by at least `0.03`, or by `0.02` with a clear latency/cost advantage
- run covers more than the anchor subset, or the anchor result is so dominant that a hold would just waste time
- no significant scorer mismatch remains unclassified

## Hold

Recommend `hold` when:

- current leader is still below `0.80`
- leader is meaningfully better than peers, but not good enough to drive a default switch
- quality win exists only on cost/latency terms that are unacceptable for normal reruns

## Retest

Recommend `retest` when:

- top models are within `0.02`
- only the anchor subset has run and the result is not decisive
- scorer or rubric behavior still looks unstable
- a better candidate model becomes available and the current recommendation is close

## Cost / Latency Guardrail

Do not switch on a tiny quality win if it creates a bad operator loop.

As a default rule:

- quality lead under `0.02` is not enough by itself
- a slower or more expensive model must justify itself with a clearly better director-facing read
- if two models are functionally tied, prefer the cheaper/faster one

## Registry Rule

Every real eval run must update `docs/evals/registry.yaml` with:

- measured date
- git sha
- result file
- latency
- cost
- verified overall score

Stale model-selection evidence is worse than no evidence.
