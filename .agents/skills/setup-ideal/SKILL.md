---
name: setup-ideal
description: Socratic conversation to build the Ideal doc — what the system should be with zero limitations
user-invocable: true
---

# /setup-ideal [project-name]

Build the project's Ideal through guided conversation with the user. This is the
most important document in the project. Everything else — the spec, the architecture,
the evals — derives from it.

## What This Skill Produces

1. **`docs/ideal.md`** — The Ideal. Requirements, quality bar, vision-level
   preferences. What the system SHOULD be. Short, vivid, memorable.
2. **`docs/spec.md`** — Raw ideas holding pen. Implementation thoughts the user
   had during the conversation. NOT yet organized as compromises — that happens
   in `/setup-spec` after evals reveal what's actually needed.

## The Conversation

Use `docs/prompts/ideal-app.md` as the structural template for the output.
The conversation itself follows this approach:

### Opening

Explain to the user what you're about to do:

> We're going to build the Ideal for this project — a description of what the
> system should be if there were zero limitations of any kind. Perfect
> infrastructure, zero cost, instant everything, and where AI is involved,
> perfect AI. No configuration, no workarounds, no unnecessary complexity.
> Just the pure experience.
>
> I'm going to be annoyingly persistent about asking "but why?" because you'll
> naturally describe solutions and I need the underlying want. "I need a notification
> queue" is a solution. "I want to feel like the system noticed something important
> happened" is the Ideal. I'll keep drilling until we hit bedrock.
>
> When you have implementation ideas — and you will, they're valuable — I'll
> capture them separately. We're not throwing them away. But right now we're
> building the Ideal, not the architecture.

### The Drill-Down

For everything the user says, relentlessly ask:

- **"Why does this exist?"** — Is this a genuine user need or a technical workaround?
- **"What deeper need does this serve?"** — Keep going until you hit something
  that would be true even with zero limitations.
- **"Would this exist in the ideal?"** — If the answer is "no, but we need it
  because...", that's an implementation idea. Capture it in spec.md and move on.
- **"What would this feel like?"** — Push past features into experience. Not
  "a search bar" but "I ask for something and it's just there."

Be aggressive about this. The user asked for it. Don't hedge, don't soften. If
they describe a database schema, stop them: "That's an implementation. What's the
experience you're trying to create?" Probe with limitation-appropriate questions:
- For AI-facing features: "Would this button exist if AI could just know what you meant?"
- For infrastructure: "Would this step exist if the data were already where it needed to be?"
- For interaction design: "Would this screen exist if the user could just say what they want?"

### Surfacing Implicit Ideals

Some ideals are so obvious the user won't think to say them. Probe for these:

- **Security / privacy**: "What does 'secure' mean for this system?" The ideal
  might be "I never think about authentication — the system just knows it's me
  and my data is completely private." The user won't volunteer this because it
  feels obvious, but it needs to be explicit in ideal.md.
- **Trust / reliability**: "What happens when something goes wrong?" The ideal
  might be "nothing ever goes wrong" or "I'm told immediately and clearly."
- **Performance**: "How fast should this feel?" The ideal is always "instant."
  But articulating it makes it a measurable requirement.
- **Accessibility**: "Who uses this? Can they all use it equally?"

These produce ideals that face world limitations (security, physics, human
nature) rather than AI limitations. They're still ideals — they still guide
decisions toward the best possible experience. The compromises they generate
are world compromises with evolution paths, not AI compromises with deletion
evals. But they belong in ideal.md just the same.

### Minimum Viable Floor

After the Ideal is established, probe for the minimum viable floor — the
threshold below which the product doesn't solve anyone's problem:

- **"What's the smallest input where this is actually useful?"** A text
  extraction tool that only works on 12-page documents is a toy. What's the
  real use case size?
- **"What quality level is the bare minimum?"** Partial extraction that
  misses major entities? Or must it be complete?
- **"Which requirements are non-negotiable?"** Provenance might be the whole
  point. Without it, is the product even worth building?

This is NOT the Ideal (which is "any scale, perfect output"). It's the floor
below which you don't ship. It belongs in the Requirements section of ideal.md
under a "Minimum Viable Floor" heading. It gates everything downstream:

- Golden references MUST exist at minimum viable scale
- Evals below this scale are diagnostic, not acceptance tests
- The acceptance test is at minimum viable scale, regardless of implementation

### Capturing Ideas

When the user describes something that's clearly implementation (a specific
technology, a pipeline stage, a UI pattern that exists because of limitations):

1. Acknowledge it: "That's a good implementation idea."
2. Capture it in spec.md with their exact words and enough context.
3. Steer back: "Now, what's the ideal version of what that's trying to achieve?"

Never dismiss their ideas. Never say "that's just a compromise." They may have
brilliant solutions that survive evaluation. Just separate them from the Ideal.

### Library/Module Framing

If the project is a library or module (not an end-user application):

> The ideal for a library is that it doesn't exist. The consuming application
> handles everything directly. So let's describe what the end user of the
> consuming app experiences — they never know this module was involved.

Frame all ideals from the consuming app's perspective.

### Closing

When the conversation feels complete:

1. Read back the Ideal document to the user.
2. Ask: "Is this the system you'd build if you could wave a magic wand?"
3. Revise based on their response.
4. Confirm spec.md has captured all their implementation ideas.
5. Update `docs/setup-checklist.md` — check off Phase 1 items.

## Document Structure for ideal.md

Follow the template in `docs/prompts/ideal-app.md`, sections 1-2 only
(The Ideal + Requirements and Quality Bar). Vision-level preferences go in
Section 1. Do NOT write Compromises, Decomposition, or Human Review Points
yet — those come from `/setup-spec` after evals.

**Vision-level preferences** are qualities that persist regardless of
implementation — they survive even when every compromise is eliminated.
"The interaction should feel like collaborating with talented people" is a
vision-level preference. Contrast with **compromise-level preferences** (added
later by `/setup-spec`), which attach to specific compromises and die when the
compromise is eliminated. "Engine pack selection UI" is a compromise-level
preference tied to a render adapter compromise — if a single model handled all
video gen, that UI would be deleted. During `/setup-ideal`, only capture
vision-level preferences. Compromise-level preferences emerge during spec work.

## Document Structure for spec.md (initial)

Just a flat list under a heading:

```markdown
# Spec — Raw Ideas

Collected during Ideal conversation. These are implementation ideas, not yet
validated against eval results. They'll be organized into confirmed compromises
in Phase 5 (`/setup-spec`).

## Ideas

- {idea with context, attributed to user}
- ...
```

## Guardrails

- Never write compromises or architecture in ideal.md. That document is purely the Ideal.
- Never dismiss or lose the user's implementation ideas. Capture everything in spec.md.
- Never let the user settle for "good enough" on the Ideal. Push for bedrock.
- Never call implementation ideas "compromises" at this stage — we don't know
  they're needed yet.
- The Ideal section of ideal.md should be ≤1 page. If it's longer, you're
  including implementation details.
- Always update the setup checklist when done.
