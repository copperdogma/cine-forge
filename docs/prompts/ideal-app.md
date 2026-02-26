# Ideal App — Generator Prompt

You are designing the **Ideal App** document for a software project. This is the
most important document in the project — it defines what the system SHOULD be
if there were no limitations, then maps every current compromise against that ideal.

The Ideal App document serves as:
- The **spirit guide** for all architectural decisions ("does this move us toward the ideal?")
- The **eval generator** (every compromise produces a testable detection mechanism)
- The **simplification radar** (every compromise has a detection mechanism — when the limitation changes, the compromise is simplified or deleted)
- The **self-eliminating architecture** (the goal is to collapse the system into fewer and fewer moving parts)

## Relationship to Other Documents

- **The Ideal** is the permanent north star. It rarely changes. It is the Requirements.
- **The Spec** is the set of Compromises — how we achieve the Ideal given current
  limitations. The spec is a living document that **shrinks over time** as
  limitations are resolved and compromises get eliminated or simplified. The spec
  converges toward the Ideal.
- **Preferences** exist at two levels:
  - **Vision-level preferences** attach to the Ideal. They persist across all
    implementations. ("The interaction should feel gentle and conversational.")
  - **Compromise-level preferences** attach to specific compromises. They die
    when the compromise is eliminated or transformed. ("The notification queue
    should batch updates every 5 minutes.") These are legitimate engineering
    investments — the product still needs to ship and be usable — but knowing
    they're tied to a compromise prevents mistaking them for the Ideal.

## Limitation Types

Not all compromises come from AI limitations. Limitations come from multiple
sources, each with a different lifecycle:

| Source | Example | Detection Mechanism | Lifecycle |
|---|---|---|---|
| **AI capability** | Can't hold 300 pages of context | Run eval on new SOTA model | **Deletion** — compromise disappears entirely |
| **Ecosystem / infrastructure** | No universal identity layer | Monitor standards, APIs, adoption | **Transformation** — compromise changes form, need persists |
| **Legal / regulatory** | GDPR requires explicit consent | Legal review, regulatory changes | **Transformation** — form evolves with law |
| **Physics / math** | Network latency, computational cost | Permanent (optimize, never eliminate) | **Permanent** — asymptotically approach ideal |
| **Human nature** | Users need trust signals, cognitive load limits | Permanent (mostly) | **Permanent** — the form changes, the need doesn't |

AI compromises have deletion evals: when the eval passes, delete the compromise.
World compromises have evolution paths: the form changes, the underlying need
persists. For permanent limitations, the Ideal still matters — it tells you
which direction to evolve. Every iteration gets asymptotically closer.

## Context

Project: {project_name}
One-line purpose: {purpose}
Core input: {what_goes_in}
Core output: {what_comes_out}
Who/what consumes the output: {consumers}
Current architecture summary (if any): {brief_description}

## Generate the following sections:

---

### 1. The Ideal

Describe the system as if there were no limitations — perfect infrastructure,
instant everything, zero cost, complete trust, and (where AI is involved) perfect
AI. Not every system's ideal centers on AI — an interactive app's ideal may center
on the interaction model, while a data extraction library's ideal may center on a
single AI call. Describe the simplest possible system that delivers the full
experience.

**For a library/module:** The ideal is that this component does not exist. The
consuming system handles everything in a single step. Describe what that looks
like from the end user's perspective — they never know this module was involved.

**For an application:** The ideal is the simplest possible interaction. What does
the user say or provide? What do they get back? No configuration, no modes, no
pipeline — unless a choice reflects genuine user intent (not a technical workaround).

Write this as a short, vivid narrative. Make the current architecture feel
over-engineered by comparison. This section should be short enough to read in
60 seconds and memorable enough to guide decisions from recall.

Include **vision-level preferences** here — things about how the system should
feel, behave, or present itself that are part of the Ideal regardless of
implementation. These are not technical requirements; they're the qualities
that survive even when every compromise is eliminated.

---

### 2. Requirements and Quality Bar

**Requirements** are capabilities the system must have regardless of implementation.
They are universal to the Ideal. Write each as "The system must..." followed by
a concrete example of what success looks like.

**Quality Bar** defines "correct" with examples. For each major capability, provide
a concrete input/output pair or before/after that would make a domain expert say
"this is exactly right." These become golden reference seeds.

Rules:
- No placeholders. "UNKNOWN" or "N/A" in output is a failure, not a gap.
- If the text doesn't contain the information, the field doesn't exist — don't invent it.
- Contradictions are surfaced with evidence, not silently resolved.

---

### 3. Compromises (The Architecture You Actually Build)

This is the longest section. It maps every place where limitations force
complexity that the Ideal wouldn't need.

For each compromise, write:

> **The Ideal:** {what the system should do — one sentence}
>
> **The Compromise:** {what we currently must build instead, and why}
>
> **The Limitation:** {the specific limitation that forces this compromise}
>
> **Limitation Type:** AI capability | Ecosystem | Legal | Physics | Human
>
> **Compromise-Level Preferences:** {any preferences that exist only because this
> compromise exists — UX decisions, configuration options, tuning parameters that
> would be irrelevant if the Ideal were achievable. These are legitimate investments
> to make the product usable, but they are explicitly tied to this compromise.}
>
> **Detection:** {How we know this limitation has changed.
> For AI: a concrete, runnable eval with specific input, expected output, and
> pass/fail criteria.
> For Ecosystem: what standard, API, or adoption milestone to monitor.
> For Legal: what regulatory change would enable simplification.
> For Physics/Human: "Permanent — optimize toward Ideal, never fully resolved."
> Include specific metrics where possible.}
>
> **When It Resolves:** {For AI limitations: exactly what code/stages/config/preferences
> we delete. For world limitations: what the compromise transforms into — the next,
> simpler form that's closer to the Ideal.}

Rules:
- Be brutally honest. If complexity exists because of a specific limitation, name
  the limitation explicitly. If a pipeline stage exists because AI isn't good
  enough, say so. If a UI workflow exists because infrastructure can't support
  the ideal interaction, say so. Don't dress up workarounds as principled
  architecture.
- Each compromise should make you slightly uncomfortable. If it doesn't, you're
  not being honest about what's ideal vs. what's expedient.
- For AI compromises, the eval must be runnable — specific input, specific
  expected output, specific pass/fail criteria. No hand-waving.
- For world compromises, the evolution path must be concrete — not "someday
  this will be better" but "when X happens, we replace Y with Z."
- Order compromises from most to least architecturally significant (i.e., which
  one, if resolved, would eliminate the most downstream complexity).

---

### 4. Recursive Decomposition (How to Build It)

For any capability where the Ideal can't yet be achieved directly:

1. Define ideal input → output (golden example)
2. Attempt it with the **simplest possible approach**:
   - For AI-powered transformations: a single call to the best available SOTA
     model. NEVER test with a cheap model first — if the best model succeeds,
     there is nothing to build. Cheaper models are a cost optimization question,
     not a capability question.
   - For deterministic logic: the most straightforward implementation.
   - For infrastructure/integration: the simplest architecture that could work.
   - For interaction design: the most direct user flow with fewest steps.
3. Analyze failure modes — how specifically does the simple approach fail?
4. For each failure mode, define a sub-ideal (a smaller ideal that fixes that failure)
5. Attempt each sub-ideal with the simplest approach (applying the same
   type-matching above)
6. Repeat until you reach something that works — an AI call that succeeds,
   deterministic code, an existing service, a simple UI pattern
7. Build that. Every level above has a detection mechanism waiting for the day
   the limitation changes and the branch can be pruned or simplified.

The architecture you end up with is a tree of "things we can't do simply yet"
with detection mechanisms at every node. When a limitation is resolved, prune
or simplify the subtree below it.

Apply this process to the 2-3 most significant compromises from Section 3.
Show the decomposition tree. This makes the build plan self-evident.

---

### 5. Human Review Points

Do NOT describe where humans "must" be involved. Instead, describe where human
attention has the **highest leverage** — specifically, moments of disagreement.

The operating model: the system is validated against golden references (expected
correct outputs). **Humans review only when system outputs disagree with golden
references** — and the human determines which is correct. If the system output
is better, the golden reference is updated. If the golden reference is correct,
the system is fixed.

For AI-powered components, golden references serve double duty: they validate the
current system AND detect when a simpler approach (e.g., a single SOTA call)
could replace a complex pipeline. For deterministic components, golden references
are standard test fixtures — expected outputs for known inputs.

List the specific disagreement types where human judgment is irreplaceable
(genuinely ambiguous data, subjective quality, contested interpretations) vs.
those where a sufficiently careful automated pass can self-resolve.

---

## Rules for the entire document

- Be concrete, not hand-wavy. Every capability needs an example.
- The Ideal section should be <=1 page. It's a north star, not a spec.
- The Compromises section will be the longest. That's correct — it's where
  the actual engineering guidance lives.
- Don't hedge with "could" or "might." State what the ideal IS, and state
  what the compromise IS.
- Write for an AI agent that will use this document to make implementation
  decisions. Every section should be actionable, not inspirational.
- For modules/libraries: always frame the ideal from the consuming app's
  perspective. The module's ideal is its own non-existence.
- The Ideal is the Requirements. The Spec is the Compromises. Preferences
  attach to both layers — vision-level preferences persist, compromise-level
  preferences are tied to their compromise.
- Not all limitations are AI limitations. Tag each compromise with its
  limitation type. AI compromises have deletion evals. World compromises
  have evolution paths. Permanent limitations get optimized toward, never
  fully resolved.
