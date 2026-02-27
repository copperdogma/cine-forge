---
name: setup-spec
description: Build the spec from confirmed compromises — informed by eval results, not speculation
user-invocable: true
---

# /setup-spec

Build the full project spec. This is NOT a creative exercise — it's an
engineering response to measured limitations. Every section of this spec
exists because an eval or analysis proved the Ideal can't be achieved directly.

Each compromise may carry **compromise-level preferences** — UX decisions,
config options, and tuning parameters that exist only because the compromise
exists. These are legitimate engineering investments (the product needs to
ship), but they are explicitly tied to their compromise and die when it is
eliminated. They are the counterpart to **vision-level preferences** in
`docs/ideal.md`, which persist across all implementations.

## What This Skill Produces

1. **`docs/spec.md`** — Organized spec with confirmed compromises, each carrying
   its limitation type, detection mechanism, and resolution criteria.
2. **Updated `docs/ideal.md`** — New ideals discovered during spec work.
3. **Decomposition trees** for the top compromises.

## Inputs Required

- `docs/ideal.md` — The Ideal and requirements (from `/setup-ideal`)
- `docs/spec.md` — Raw implementation ideas (from `/setup-ideal`)
- `evals/baseline-results.md` — What AI can and can't do (from `/setup-evals`)

If any of these are missing, stop and tell the user which phase they need to
run first.

**Phase 4 and Phase 5 iterate.** The spec is not written from a single eval
run. As you map failures to compromises, you'll discover you need evals at
larger scale, or that a proposed compromise raises testable questions. Loop
back to `/setup-evals` as needed:

- Baseline at toy scale → preliminary failure modes → draft compromises
- "Would chunking fix this?" → prototype, run eval at standard scale
- Standard scale reveals new failure modes → revise compromises
- Aspirational scale establishes the ceiling → finalize scope boundaries

The spec stabilizes when the capability boundary is fully mapped and the user
has made scoping decisions for v1. Don't try to finalize the spec from a
single eval run.

## Limitation Types

Not all compromises come from AI limitations. Each limitation type has a
different lifecycle and detection mechanism:

| Source | Example | Detection Mechanism | Lifecycle |
|---|---|---|---|
| **AI capability** | Can't hold 300 pages of context | Run eval on new SOTA model | **Deletion** — compromise disappears |
| **Ecosystem / infrastructure** | No universal identity layer | Monitor standards, APIs, adoption | **Transformation** — changes form |
| **Legal / regulatory** | GDPR requires explicit consent | Legal review, regulatory changes | **Transformation** — evolves with law |
| **Physics / math** | Network latency, computational cost | Permanent | **Permanent** — optimize, never eliminate |
| **Human nature** | Users need trust signals | Permanent (mostly) | **Permanent** — form changes, need doesn't |

AI compromises have deletion evals: when the eval passes, delete the code.
World compromises have evolution paths: the form changes, the need persists.
For permanent limitations, the Ideal still tells you which direction to optimize.

## Steps

### 1. Map Failures to Compromises

Read `evals/baseline-results.md`.

**For AI capabilities:** Verify the baseline was run with the best available SOTA
model. If the baseline only tested cheap models, STOP — re-run with the best
model first. A failure on Haiku that passes on Opus is NOT a confirmed
limitation; it's a cost optimization opportunity. Only failures on the best
model are confirmed limitations that justify building compromises.

**For non-AI capabilities:** Verify the baseline used the simplest reasonable
implementation, not an over-engineered one. A failure caused by premature
abstraction is not a confirmed limitation.

For each confirmed failure:

- What capability does this block?
- What's the simplest possible workaround?
- Is there a raw idea from the user (in spec.md) that addresses this?

Also identify compromises that don't come from eval failures — world limitations
like security, legal compliance, infrastructure constraints. These won't show up
in AI evals but are still compromises against the Ideal.

**Scale gradient input.** The baseline results include a scale gradient
conversation (from `/setup-evals` step 6). This is critical input:

- **What scale did the user commit to for v1?** Capabilities that work at v1
  scale need no compromise, even if they fail at aspirational scale.
- **Where does the SOTA boundary fall?** If the best model handles standard
  scale but fails at aspirational, the compromise is scope-capping, not a
  pipeline stage. Document the boundary explicitly.
- **Is the failure intelligence or output budget?** Output budget failures
  (truncated JSON, incomplete output) have simple workarounds (chunked output,
  two-pass). Intelligence failures (wrong entities, hallucinated facts) need
  real pipeline stages. These are DIFFERENT compromises with different costs.
- **What aspirational goldens exist as detection evals?** Each scale boundary
  should have an aspirational golden. When a future SOTA model passes it, the
  scope cap or pipeline stage can be deleted.

For scale-related failures, the compromise should include the explicit
boundary: "Works for inputs up to X. Inputs beyond X require {workaround}.
Detection eval: aspirational golden at scale Y. When this passes, delete
the workaround."

Group related failures into compromises. A single compromise may address
multiple failure modes. Don't create one compromise per failure — create
one per coherent engineering solution.

### 2. Write Each Compromise

For each confirmed compromise, write:

> **The Ideal:** {what the system should do — one sentence, from ideal.md}
>
> **The Compromise:** {what we build instead, and why}
>
> **The Limitation:** {the specific failure or constraint}
>
> **Limitation Type:** AI capability | Ecosystem | Legal | Physics | Human
>
> **Compromise-Level Preferences:** {UX decisions, config options, tuning
> parameters that exist only because this compromise exists. These are
> legitimate investments — the product needs to ship — but they're explicitly
> tied to this compromise.}
>
> **Detection:** {How we know this limitation has changed.
> For AI: the specific eval from Phase 4 that tests this capability.
> For Ecosystem: the standard, API, or milestone to monitor.
> For Legal: the regulatory change to watch for.
> For Physics/Human: "Permanent — optimize toward Ideal."}
>
> **When It Resolves:** {For AI: exactly what code/stages/config/preferences
> we delete. For world limitations: what the compromise transforms into —
> the next, simpler form closer to the Ideal.}

Order by architectural significance — which compromise, if resolved, would
eliminate the most downstream complexity?

### 3. Recursive Decomposition

For the top 2-3 compromises, apply the decomposition:

1. The compromise says "we need to do X because of limitation Y."
2. Can we do a simpler version of X? Test it (AI eval for AI limitations,
   research/prototype for world limitations).
3. If yes: that simpler version is the implementation. The gap between the
   simple version and the full capability is a sub-compromise.
4. If no: decompose further. What sub-steps does X require?
5. For each sub-step: can we do it simply? Test.
6. Repeat until you hit things that work — AI calls that succeed, deterministic
   code, existing services, deployable infrastructure.

Draw the tree:

```
Compromise: Full-text extraction [AI capability]
├── AI can't hold 300 pages → Chunking strategy (deterministic)
│   ├── Overlap handling (deterministic)
│   └── Cross-chunk context → Entity roster injection (AI can do this)
├── AI misses entities in long text → Multi-pass extraction
│   └── AI can do single-chunk extraction well → Use it as the leaf
└── Eval: full-text golden reference, F1 ≥ 0.95

Compromise: User authentication [Ecosystem]
├── No universal identity layer → SSO with major providers
│   ├── OAuth integration (deterministic code + external APIs)
│   └── Session management (deterministic)
├── Compromise prefs: which providers, session timeout, remember-me
└── Monitor: passkeys adoption, device-bound credentials, WebAuthn maturity
    └── Evolution: SSO → passkeys → ambient auth (asymptotic toward Ideal)
```

This tree IS the architecture. Build the leaves. The detection mechanisms
at each node signal when branches can be pruned or simplified.

### 4. Discover New Ideals

The spec process WILL surface ideals nobody thought to articulate. When you
realize "oh, the system also needs to feel X" or "the output must have property
Y that we didn't think of" — update `docs/ideal.md` immediately.

Common triggers:
- Seeing a bad output makes you realize what "good" actually means
- A compromise creates a UX that reveals what the ideal UX should be
- Testing edge cases reveals requirements that weren't obvious
- World limitations reveal assumptions about the Ideal that need to be explicit
  (e.g., "my data is private" was always implicit — make it an explicit ideal)

### 5. Organize the Spec

`docs/spec.md` already contains raw ideas from `/setup-ideal`. Do NOT overwrite
them. Instead, add structure around them:

1. Move all existing raw ideas under an `## Untriaged Ideas` section at the top.
2. As you work through compromises, pull relevant ideas from Untriaged into
   the appropriate compromise section. Reference the original idea.
3. Ideas that don't apply to any confirmed compromise stay in Untriaged —
   they may become relevant later as the project evolves.
4. Only remove an idea from Untriaged when it's been explicitly incorporated
   into a compromise OR explicitly discarded (with a note about why).

The organized spec should have this structure:

```markdown
# {Project Name} — Spec

> **This spec is a set of compromises against the Ideal (`docs/ideal.md`).**
> Every section exists because a limitation prevents achieving the Ideal
> directly. Each compromise carries a detection mechanism for when its
> limitation changes. AI compromises have deletion evals — when they pass,
> the compromise is deleted. World compromises have evolution paths — they
> transform toward the Ideal over time. This document shrinks and simplifies
> over time. That's the goal.

## Untriaged Ideas
{Raw ideas from the Ideal conversation that haven't been incorporated yet.
Work through these as compromises are confirmed. Don't delete — incorporate
or explicitly discard with rationale.}

## AI Compromises
{Ordered by architectural significance. These have deletion evals.}

### 1. {Most significant AI compromise}
{full compromise template}

### 2. {Next most significant}
...

## World Compromises
{Grouped by limitation type: Ecosystem, Legal, Physics, Human.
These have evolution paths, not deletion evals.}

### 1. {Compromise} [Ecosystem]
{full compromise template}

### 2. {Compromise} [Human]
...

## Decomposition Trees

### {Compromise 1} — Decomposition
{tree}

## Architecture Summary

{Brief description of what the system looks like given ALL compromises —
both AI and world. This is the "what we're actually building" section.
It should feel like an inevitable consequence of the compromises, not an
independent design.}
```

### 6. Update Tracking

- Check off Phase 5 items in `docs/setup-checklist.md`.
- Log to CHANGELOG.md.
- At this point, the project is set up. The next step is building — use
  `/setup-stories` to decompose the spec into buildable stories.

## Guardrails

- Never write an AI compromise without a corresponding eval. If you can't
  test it, you can't delete it later.
- Never write a world compromise without a concrete evolution path. "Someday
  this will be better" is not a path. "When passkeys reach 60% browser adoption,
  replace SSO with passkey-first auth" is.
- Never invent AI compromises for failures that weren't demonstrated in evals.
  Speculation about what might fail is not architecture.
- World compromises don't need evals to justify their existence — they're
  driven by real-world constraints, not AI failure modes. But they DO need
  explicit evolution paths.
- The spec must reference ideal.md at the very top, prominently. Not buried,
  not optional.
- When the spec work reveals new ideals, update ideal.md immediately. Don't
  defer it.
- Compromise-level preferences are legitimate engineering investments. Don't
  under-invest in them just because they're tied to a compromise — the product
  still needs to ship and be usable. But DO tag them explicitly.
- For permanent limitations (physics, human nature): the Ideal still matters.
  It tells you which direction to optimize. Every iteration should get
  asymptotically closer.
- Update the setup checklist when done.
