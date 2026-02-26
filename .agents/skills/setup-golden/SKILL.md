---
name: setup-golden
description: Create golden reference input/output pairs for eval — the ground truth the system is measured against
user-invocable: true
---

# /setup-golden

Create golden reference input/output pairs that define "correct." These are the
ground truth the system is measured against. If the system disagrees with the
golden reference, one of them is wrong — and it's not always the system.

## What This Skill Produces

- Input samples in `tests/fixtures/golden/` (or project-appropriate location)
- Golden reference outputs alongside each input
- A manifest documenting each golden pair and what it tests

## Philosophy

Golden references follow the same recursive decomposition as everything else.
You don't create a golden reference for the whole system — you create them at
whatever level of the decomposition tree you can actually evaluate.

Start at the **leaves** — the smallest evaluable units:
- A single conversation turn (input → response)
- A single document → extracted entities
- A single set of facts → synthesized narrative
- A single image → extracted metadata

As you build confidence at each layer, compose upward into larger golden
references. Never try to create a golden reference for something you can't
evaluate yet.

### Scale-Tiered Goldens

Scale limitations are a gradient, not binary. The Ideal says "any scale." The
baseline will reveal where the capability boundary falls today. Golden references
should exist at multiple scale tiers so each new SOTA model can be tested against
the next boundary:

- **Leaf / small**: Minimal input, exercises core capability. Fully hand-curated.
  Used for rapid iteration and prompt development.
- **Standard**: Realistic real-world input at the scale users actually need.
  Fully hand-curated. This is the v1 acceptance test.
- **Aspirational**: Input at the scale the Ideal describes but today's AI can't
  handle. Can be AI-generated + human-spot-checked (not fully hand-curated).
  This is the detection eval — when the limitation changes (new SOTA model
  for AI limitations, ecosystem shift for infrastructure limitations) and
  the simple approach passes against this golden, delete or simplify the
  compromise that worked around it.

Don't spend weeks hand-curating an aspirational golden. Its purpose is to
detect capability changes, not to be a perfect reference today. A good-enough
golden at aspirational scale is better than no golden at all.

## Steps

### 1. Identify Key Input/Output Pairs

Read `docs/ideal.md`. For each requirement and quality bar example:

- What's the smallest input that exercises this capability?
- What's the correct output for that input?
- Can a domain expert verify this pair in under 5 minutes?

If the answer to the third question is "no", decompose further.

### 2. Create the Inputs

For each identified pair, create a realistic input sample:

- Use real-world-like data, not toy examples (unless the capability is simple)
- Include edge cases: ambiguous data, contradictions, missing info
- Include at least one "happy path" and one "tricky" input per capability
- Store in `tests/fixtures/golden/{capability}/input.*`

### 3. Generate Draft Golden Outputs

For AI-transformation capabilities, use the **best available SOTA model** to
generate draft outputs. Never use a cheap model for golden reference generation.
For non-AI capabilities, write the expected outputs by hand or derive them from
existing correct behavior. However produced, the golden IS the quality bar:

```
Given this input: {input}
According to this ideal: {relevant section of ideal.md}
Produce the correct output.
```

**Critically:** Do NOT accept the first draft. Run multiple review passes:

1. **Structural pass**: Does it match the expected schema? All required fields present?
2. **Completeness pass**: Is anything missing that the input supports?
3. **Accuracy pass**: Does every fact trace back to the input? Any hallucinations?
4. **Quality pass**: Would a domain expert approve this? Any placeholders or vagueness?

Each pass should be a separate, focused prompt. Don't try to catch everything in
one review.

### 4. The Disagreement Protocol

When the system (later) produces output that differs from the golden reference:

1. Compare the two outputs against the original input.
2. Determine which is correct. It could be either one.
3. If the system output is better: **update the golden reference.** The golden
   file is not sacred — it's the current best understanding of "correct."
4. If the golden reference is correct: the system has a bug. Fix it.
5. Log the disagreement and resolution in CHANGELOG.md.

This protocol means golden references improve over time as the system finds
edge cases the original author missed.

### 5. Create the Manifest

Create `tests/fixtures/golden/MANIFEST.md`:

```markdown
# Golden Reference Manifest

## {capability-name}
- **Input**: `{capability}/input.{ext}` — {brief description}
- **Golden output**: `{capability}/golden.{ext}` — {what correct looks like}
- **Tests**: {which requirement from ideal.md this validates}
- **Reviewed**: {date} by {who/what}
- **Decomposition level**: {leaf | composed from X + Y}
```

### 6. Update Checklist

Check off Phase 3 items in `docs/setup-checklist.md`.

## Operational Playbook

See `docs/runbooks/golden-build.md` for the detailed build methodology, including:
- Phase-by-phase build process (shells → facts → evidence → validation → semantic review)
- Common failure patterns and how to fix them (truncated quotes, wrong-scene evidence, etc.)
- Scale characteristics and time estimates
- Tooling checklist and final sign-off checklist

**Key insight**: Structural validation catches ~20% of issues. Full semantic review
(checking every fact→evidence mapping, not a sample) catches the other ~80%.
Never skip the semantic review pass.

## Guardrails

- Never create a golden reference you can't verify. If it's too complex, decompose.
- Never accept AI-generated golden outputs without multiple review passes.
- Golden references are NOT sacred — they're the current best answer. Update them
  when the system proves them wrong.
- Every golden reference must trace back to a requirement in ideal.md.
- Include at least one adversarial/edge-case input per capability.
- Store golden files in version control — they're test fixtures, not ephemeral.
- Update the setup checklist when done.
