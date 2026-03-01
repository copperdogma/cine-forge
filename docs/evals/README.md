# Eval Registry System

Central tracking for all evaluation metrics, improvement attempts, and compromise gates.

## Structure

```
docs/evals/
├── registry.yaml          # Source of truth — all evals, scores, attempt summaries
├── attempt-template.md    # Template for new improvement attempt stories
├── attempts/              # One markdown file per improvement attempt
│   ├── 001-{eval}-{title}.md
│   └── ...
└── README.md              # This file
```

## Registry Protocol

### When to update `registry.yaml`

**Always** update the registry when you run an eval. This is part of the Definition of Done.

| Situation | Action |
|---|---|
| Ran an eval (any reason) | Update the `scores` section with new measurements + git_sha + date |
| Completed an improvement attempt | Add entry to `attempts` list + update scores |
| New eval created | Add full eval entry to registry |
| New compromise identified | Add compromise eval entry |
| Score is stale (code changed since git_sha) | Re-run and update |

### Staleness

A score is **stale** if the codebase has changed significantly since `git_sha`. The `/improve-eval` skill checks this automatically. When in doubt, re-measure.

## Improvement Attempts

### Creating an attempt

1. Copy `attempt-template.md` to `attempts/{NNN}-{eval-id}-{short-title}.md`
2. Number sequentially across ALL evals (not per-eval)
3. Read ALL previous attempts for the target eval before starting
4. Follow the Definition of Done checklist at the bottom of the template

### Attempt summary in registry

After completing an attempt (success or failure), add a compact summary to the eval's `attempts` list:

```yaml
attempts:
  - id: "001"
    story: attempts/001-character-extraction-prompt-tuning.md
    date: 2026-03-01
    status: failed  # succeeded | failed | inconclusive
    approach: "Multi-layer arc analysis prompt with emotional trajectory"
    worker_model: "Opus 4.6"
    worker_model_date: 2025-12-01
    subject_model: "Sonnet 4.6"
    score_before: 0.880
    score_after: 0.865
    retry_when:
      - condition: new-worker-model
        note: "Approach is valid but needs smarter orchestrator"
```

### Retry conditions

| Condition | Meaning | Recheck trigger |
|---|---|---|
| `new-worker-model` | Smarter AI might execute same approach better | New model release |
| `new-subject-model` | Better pipeline model might pass without code changes | New model release |
| `cheaper-subject-model` | Works on expensive model, need cost parity | Pricing changes |
| `new-approach` | Current approaches exhausted | Fresh thinking / new technique |
| `golden-fix` | Golden reference may be wrong/incomplete | Manual review |
| `architecture-change` | Upstream pipeline needs to change first | Pipeline refactor |
| `dependency-available` | Waiting on a library/tool/API | Ecosystem changes |

## Compromise Evals

Compromise evals test whether a spec compromise can be eliminated. They link to `docs/spec.md` compromise entries and `docs/ideal.md`.

When a compromise eval passes its gate consistently, the compromise can be deleted from `docs/spec.md` and the system moves closer to the Ideal.

Failed attempts on compromise evals are especially valuable to log — they record "the frontier isn't here yet" with evidence, and become easy wins when the frontier advances.

## Scoring

Evals can report any metrics they want. The registry stores whatever the eval produces:

```yaml
scores:
  - model: "Sonnet 4.6"
    metrics:
      overall: 0.942        # headline score
      major_chars: 0.98      # sub-scores if available
      minor_chars: 0.91
    cost_usd: 0.12           # optional: per-run cost
    duration_seconds: 45     # optional: wall-clock time
```

The `target` on the eval specifies what "good enough" means, including optional constraints:

```yaml
target:
  metric: overall
  value: 0.95
  constraints:
    cost_usd_max: 0.50       # improvement that costs $5/run isn't improvement
    duration_seconds_max: 120
```

The AI evaluating whether an attempt "succeeded" uses all of this context — score, cost, time, constraints — to make a holistic judgment.
