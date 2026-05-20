# Eval Registry System

Central tracking for all evaluation metrics, improvement attempts, and compromise gates.

Baseline eval/golden setup now belongs to `/setup-methodology`. Once that
package exists, use `/create-eval` to scaffold new evals and `/improve-eval`
to iterate on existing ones.

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

If the question is "which eval should we work on next?" use `/triage-evals` before
running a fresh benchmark. If the question is broader than evals and you need one
cross-system recommendation, use `/triage` and let it route. The eval-specific
workflow diagnoses stale scores, compromise leverage, and likely next actions from
existing registry data.

### When to update `registry.yaml`

**Always** update the registry when you run an eval. This is part of the Definition of Done.

| Situation | Action |
|---|---|
| Ran an eval (any reason) | Update the `scores` section with new measurements + git_sha + date |
| Completed an improvement attempt | Add entry to `attempts` list + update scores |
| New eval created | Add full eval entry to registry |
| New compromise identified | Add compromise eval entry |
| Score is stale (code changed since git_sha) | Re-run and update |

### Required lineage metadata

Every eval entry in `docs/evals/registry.yaml` must carry explicit methodology
lineage. Do not rely on prose scraping or eval ID naming conventions.

Required fields per eval entry:

```yaml
spec_refs:
  - spec:2
story_refs:
  - "154"
category_refs:
  - spec:2
  - spec:8
compromise_refs: []
```

- `spec_refs` — exact owning `spec:N` refs or subsections
- `story_refs` — story IDs that created or materially own this eval
- `category_refs` — methodology categories this eval advances
- `compromise_refs` — linked compromise IDs when this is a detector or deletion gate

### Staleness

A score is **stale** if the codebase has changed significantly since `git_sha`. The `/improve-eval` skill checks this automatically. When in doubt, re-measure.

## Improvement Attempts

### Creating an attempt

1. Copy `attempt-template.md` to `attempts/{NNN}-{eval-id}-{short-title}.md`
2. Number sequentially across ALL evals (not per-eval)
3. Read ALL previous attempts for the target eval before starting
4. Follow the Definition of Done checklist at the bottom of the template

## Creating a New Eval

Use `/create-eval` when the registry needs a new entry, a new benchmark config
or script needs to be scaffolded, or a new compromise gate is being introduced.

Use `/improve-eval` only after the eval already exists.

The registry entry is not complete until those explicit lineage fields are
present.

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
    retry_status: exhausted-until-new-trigger
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
| `faster-subject-model` | Works on slow model, need latency parity | Pricing/release changes |
| `new-approach` | Current approaches exhausted | Fresh thinking / new technique |
| `golden-fix` | Golden reference may be wrong/incomplete | Manual review |
| `architecture-change` | Upstream pipeline needs to change first | Pipeline refactor |
| `dependency-available` | Waiting on a library/tool/API | Ecosystem changes |

### Retry status

`retry_when` names the kind of trigger that would justify another attempt. It
does **not** mean the eval is automatically actionable every time triage reads
the registry.

Use `retry_status` on the latest attempt summary when the distinction matters:

| Status | Meaning |
|---|---|
| omitted | No extra retry state recorded; inspect the notes manually |
| `open` | The next retry is actionable as soon as the named condition is met |
| `exhausted-until-new-trigger` | The same trigger was already checked or consumed; keep this dormant until something materially new appears |
| `retired` | Do not retry this line without rewriting the plan itself |

The note on each `retry_when` item should name the actual missing trigger, not a
generic "try again later" placeholder.

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
    latency_ms: 47185        # REQUIRED: avg per-call latency from result file
    cost_usd: 0.054          # REQUIRED: avg per-call cost (null only for free-tier)
    cost_estimated: true     # present when cost computed from tokens, not promptfoo
```

The `target` on the eval specifies what "good enough" means, including optional constraints:

```yaml
target:
  metric: overall
  value: 0.95
  constraints:
    latency_ms_max: 30000    # per-call max — model must respond within this
    cost_usd_max: 0.10       # per-call max — null means no hard gate
```

The AI evaluating whether an attempt "succeeded" uses all of this context — score, latency, cost, and constraints — to make a holistic judgment that includes speed and cost tradeoffs, not just peak quality.

## Speed and Cost

Speed and cost are first-class optimization targets, not afterthoughts.

### Why they matter
Even small quality improvements that double latency are often wrong choices.
A 22-scene screenplay with 8 pipeline stages at 30s/call = 70 minutes.
The Ideal says "under 5 minutes" for the full iterative loop. Speed matters.

### How to populate
After running a promptfoo eval, extract metrics from the result file:

```
python scripts/extract-eval-metrics.py --result-file benchmarks/results/foo.json
```

Or update all registry entries at once:

```
python scripts/extract-eval-metrics.py --update-registry
```

### Anthropic cost estimation
Promptfoo does not compute cost for `claude-sonnet-4-6` (model IDs without date
suffixes). The extraction script detects this and computes estimated cost from
token counts and pricing data. Entries with estimated cost have `cost_estimated: true`.

### Latency target semantics
`latency_ms_max` in the target block is a per-call maximum. If the eval has
3 test cases, each call should be under this limit — not the total run time.

### The latency/quality/cost tradeoff
The registry now contains the full tradeoff surface for each eval. Before picking
a model for a pipeline stage, check all scores to find the cheapest/fastest model
that still meets the quality target. A model at 0.89 quality in 4 seconds is often
more valuable than 0.94 quality in 50 seconds.

## Reasoning-Effort Model Sweeps

When a new OpenAI reasoning model or Responses-only API path reopens an eval,
measure effort explicitly instead of treating the model name as one result. Use
a bounded `low`, `medium`, and `high` sweep first; record quality, latency,
cost, cached-input tokens, and reasoning tokens when the provider exposes them.
Do not promote a model, provider path, or effort tier to runtime defaults unless
that exact tier beats the maintained winner on the relevant gate.
