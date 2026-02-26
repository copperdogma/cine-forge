---
name: setup-evals
description: Build eval harness and run baseline measurements — can the simplest approach already achieve this?
user-invocable: true
---

# /setup-evals

Build the eval harness and run the first baseline measurement. This is the
moment of truth: test the simplest possible approach for each capability and
measure the gap against golden references. That gap IS the architecture you
need to build.

For AI-powered capabilities, the simplest approach is a single SOTA model call.
For deterministic capabilities, it's the most straightforward implementation.
For interactive capabilities, it's the simplest user flow. The eval harness
must accommodate all three — not every capability is tested via promptfoo.

## What This Skill Produces

- Configured promptfoo eval suite in `evals/`
- Baseline results: single-shot AI attempt against every golden reference
- Documented failure modes for each capability where AI falls short
- Updated CHANGELOG.md with results

## Philosophy

Every eval serves dual purpose:
1. **Today**: acceptance test. Does the system (however implemented) meet the Ideal?
2. **Tomorrow**: simplification detector. Can a new model replace the current
   implementation with a simpler one?

The Ideal evals are permanent — they test the experience, not the implementation.
The compromise tests (written later, during `/setup-spec`) are temporary — they
die with the compromise.

## Evals Are Iterative, Not One-Shot

The baseline (step 3) is a first pass, not the final word. The eval process
loops with `/setup-spec`:

1. Run baseline at toy scale → discover failure modes
2. Create goldens at standard scale → run again → discover NEW failure modes
3. Feed results to `/setup-spec` → spec compromises
4. If spec raises questions ("does chunking fix this?") → prototype, re-eval
5. Create aspirational goldens → run again → establish the ceiling

Each scale tier may reveal completely different failure modes. Don't try to
spec all the compromises from a single toy-scale eval. The gradient discovery
IS the architecture discovery. This means Phase 4 and Phase 5 aren't strictly
sequential — they iterate until the capability boundary is fully mapped and
the user has made scoping decisions for v1.

## CRITICAL: For AI Capabilities, Baseline Uses Best Available Model Only

**For AI-powered capabilities, the baseline answers ONE question: "Can the best
AI do this in one shot?"**

Run the baseline with the best available SOTA model ONLY (currently `claude-opus-4-6`
or equivalent). Do NOT include cheaper models in the baseline run. If the best
model fails, you have a confirmed limitation that needs a compromise. If the best
model succeeds, there is NOTHING TO BUILD — the capability exists.

**Cheaper models are tested LATER, AFTER the capability ceiling is established,
and ONLY to answer the cost optimization question: "Can a cheaper model also do
this?"** Model tiering is a cost compromise, not a capability discovery. Never
confuse the two.

**The catastrophic mistake:** Running the baseline with Haiku, seeing it fail,
concluding "AI can't do this," and spending weeks building a pipeline — only to
discover Opus could do it in a single call. This wastes weeks of work and creates
unnecessary architectural complexity. The baseline MUST use the best model to
establish the true capability ceiling first.

## For Non-AI Capabilities, Baseline Means Simplest Implementation

Not every capability is an AI transformation. For deterministic logic,
infrastructure integration, or interaction design, the baseline is:

1. Write the most straightforward implementation possible
2. Test it against the golden reference (expected correct output)
3. If it works: that's the implementation. No additional architecture.
4. If it fails: analyze the specific failure modes and add complexity
   only where the failure demands it.

The eval for non-AI capabilities uses standard testing tools (pytest,
integration tests, playwright, etc.) — not promptfoo. The principle is the
same: test the simplest approach first, build only what the gap requires.

## Steps — AI Capability Evaluation (promptfoo)

The following steps focus on AI capability evaluation via promptfoo. For non-AI
capabilities, use standard testing tools with the same "simplest approach first"
principle described above.

### 1. Configure the Eval Suite

In `evals/promptfooconfig.yaml`:

**Provider** — The best available model ONLY for the baseline:
- `claude-opus-4-6` (or current best equivalent)
- Maximum `max_tokens` (16384+). Silent truncation produces invalid JSON and
  looks like a model failure when it's actually an output budget failure.

**Test cases** — One per golden reference pair from `/setup-golden`:
- Input: the golden input
- Expected: the golden output
- Variables: any relevant context from ideal.md

**Assertions** — Dual scoring for every test case:
1. **Python structural scorer**: Deterministic checks — schema validity, field
   completeness, entity matching, provenance chain integrity. This catches
   hard failures.
2. **LLM rubric scorer**: Semantic quality — coherence, accuracy, insight depth,
   evidence grounding. Uses `claude-opus-4-6` as judge (cross-provider when
   testing non-Anthropic models). This catches soft failures.

A test case passes only if BOTH assertions pass.

**Settings**:
- `max_tokens: 16384` minimum. Start high — you can lower it later. Truncation
  masquerades as model failure and leads to building unnecessary pipelines.
- No `---` separators in prompt files (use `==========`)
- Judge model: `claude-opus-4-6`

### 2. Write the Baseline Prompt

The baseline prompt should be dead simple. This is the "dumbest possible
approach" test:

```
You are an expert at {domain}.

Given the following input:
{input}

Produce the following output:
{description of expected output format from ideal.md}

Requirements:
{relevant requirements from ideal.md}
```

No tricks. No chain-of-thought. No multi-step reasoning scaffolds. If this
works, you don't need a pipeline. The point is to find out.

### 3. Run the Baseline

```bash
cd evals && promptfoo eval --no-cache
```

Record results per golden reference. For each:
- **Pass**: The best model can do this. No compromise needed for this capability.
- **Partial**: The best model gets close. Note what's missing — this may be
  fixable with prompt refinement, not architecture.
- **Fail**: The best model can't do this. This is a confirmed limitation.
  Document the specific failure mode.

### 4. Prompt Refinement Loop (2-3 Iterations)

Before concluding something is a model limitation, try refining the prompt.
A prompt fix that turns FAIL into PASS means you DON'T need a pipeline stage.
This is worth the API spend.

**Version your prompts.** Keep every version and its scores:

```
evals/prompts/extract-entities-v1.txt  → baseline (dumb prompt)
evals/prompts/extract-entities-v2.txt  → added relationship type guidance
evals/prompts/extract-entities-v3.txt  → added output structure example
```

Track results per version:

```
| Prompt Version | Change | Score | Notes |
|---|---|---|---|
| v1 (baseline) | None — dumbest possible | 0.81 | Relationship naming mismatch |
| v2 | Added type conventions | 0.74 | Worse — over-constrained |
| v3 | Added output example | 0.91 | Best so far |
```

**Always keep the best-scoring version as your working prompt.** If v2 scores
lower than v1, don't keep v2 — revert to v1 and try a different refinement
for v3. The goal is to find the prompt ceiling, not to iterate linearly.

After 2-3 refinements, whatever still fails is a confirmed model limitation.

### 5. Analyze Confirmed Failure Modes

For each failure that persists after prompt refinement:

- **What specifically went wrong?** (hallucinated facts, missed entities,
  wrong schema, lost provenance, output truncation, etc.)
- **Is this a model limitation or an output budget limitation?** Truncated
  JSON is NOT a model intelligence failure — increase max_tokens first.
- **At what scale does it fail?** (works for small inputs, fails for large ones?)

### 6. Postmortem: Challenge the Golden References

For the most significant deviations between model output and golden reference:

- **Is the model wrong, or is the golden wrong?** Every deviation is a chance
  to discover golden reference errors. If the model output is better, update
  the golden. If the golden is correct, the deviation is a real failure mode.
- **Categorize deviations by type:** missing entity, wrong relationship,
  hallucinated fact, formatting issue, truncation, etc.
- **Deep-dive the top N most significant deviations.** You can't investigate
  every deviation for large outputs — prioritize the ones that would most
  affect the spec.

Store this analysis in `evals/baseline-results.md`.

### 7. Scale Gradient: Run the Boundary Discovery

**The eval gradient IS the architecture discovery process.** You don't run one
eval and then spec the architecture — you run evals at increasing scale, and
the failure modes at each tier tell you what to build. This is iterative.

**Step 6a: Define the gradient with the user.**

Ask: "What are the realistic scale tiers for this project?" For each tier,
you need a golden reference (from `/setup-golden`). Example:

| Scale Tier | Input Size | Golden Exists? | Purpose |
|---|---|---|---|
| Toy | {small} | Yes (from step 3) | Can the model do this at all? |
| Standard | {real-world} | Needed | Can SOTA handle the real use case? |
| Aspirational | {dream scale} | Needed | Where's the ceiling? Detection eval. |

If standard and aspirational goldens don't exist yet, **go create them now**
(use `/setup-golden`). You can't discover the boundary without testing at the
boundary. Aspirational goldens can be AI-generated + spot-checked — they're
detection evals, not hand-curated ground truth.

**Step 6b: Run evals at each scale tier.**

Run the same baseline prompt against each tier. The failure modes will likely
be DIFFERENT at each scale:

- Toy: maybe output budget is the only issue (intelligence is fine)
- Standard: maybe context gets lost, entities get missed, relationships hallucinate
- Aspirational: maybe the model can't even hold the input

Each tier's failures potentially need different compromises. An output budget
failure is a simple workaround (chunked output). An intelligence failure
(missed entities, hallucinated relationships) needs a real pipeline stage.
Don't conflate them.

**Step 6c: Deep-analyze each tier's results.**

For each scale tier, apply steps 4 and 5 (failure mode analysis + postmortem).
The goal is a clear picture:

```
| Scale Tier | Input Size | SOTA Result | Failure Mode | Compromise Type |
|---|---|---|---|---|
| Toy | {size} | PARTIAL | Output truncation | Simple workaround |
| Standard | {size} | FAIL | Lost context + truncation | Pipeline stage |
| Aspirational | {size} | FAIL | Can't hold input | Scope boundary |
```

**Step 6d: Scope conversation with the user.**

Now you have data. Walk the user through:

1. **What scale do your users actually need?** A library for 90-page screenplays
   has different requirements than one for 3,400-page novel series.
2. **Where does the best model's capability boundary fall relative to that need?**
   If SOTA handles your standard use case, you might not need a pipeline at all.
3. **Is the failure at larger scale an intelligence failure or an output budget
   failure?** Output budget is solvable with simple workarounds (two-pass,
   chunked output). Intelligence failure requires real pipeline stages.
4. **What's the v1 scope?** Cap at what works today. Document the boundary
   explicitly in the spec. Keep aspirational goldens as detection evals.
5. **Is it worth building pipeline to push past the boundary?** Building weeks
   of pipeline to replicate what SOTA already does at smaller scale may not be
   worth it. The boundary will move upward with every new model release. Sometimes
   the right answer is "wait."

This conversation feeds directly into Phase 5 (`/setup-spec`). The user's answers
determine which limitations become confirmed compromises and which become scope
boundaries.

### 8. Cost Tier Testing (AI Capabilities Only, AFTER Baseline)

Only after the baseline establishes what the best model CAN do:

Add cheaper models to the eval config and re-run. This answers a DIFFERENT
question: "Can we achieve the same quality at lower cost?"

```markdown
| Capability | Opus (baseline) | Sonnet | Haiku | Notes |
|---|---|---|---|---|
| {cap 1} | PASS | PASS | PARTIAL | Haiku misses edge cases — Sonnet is the cost floor |
| {cap 2} | PASS | PASS | PASS | All tiers work — use Haiku |
| {cap 3} | FAIL | FAIL | FAIL | Confirmed limitation — needs a compromise |
```

If a capability PASSES on Opus but FAILS on cheaper models, the compromise
is model tiering (use the better model), NOT a pipeline stage. If it FAILS
on Opus, it's a real limitation that needs architecture.

### 9. Update Tracking

- Log results to CHANGELOG.md.
- Check off Phase 4 items in `docs/setup-checklist.md`.
- List confirmed failure modes that need compromises — these are the input
  to `/setup-spec`.

## Guardrails

- **For AI capabilities: BASELINE = BEST MODEL ONLY.** Never conclude "AI can't
  do this" from a cheap model's failure. The baseline must use the best available
  SOTA model. This is the single most expensive mistake in eval-first development.
- Run the dumbest prompt first. Don't optimize the prompt before measuring
  the baseline. You need to know the raw capability gap.
- Try 2-3 prompt variations before calling something a model failure. Bad
  prompts look like model limitations.
- Start with maximum max_tokens. Truncation looks like model failure. Lower
  the budget only after confirming the output fits.
- Cross-provider judging: don't let Claude judge Claude if avoidable.
- Update the setup checklist when done.
