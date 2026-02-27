# ADR-003 — Comment Review Decisions Log

Tracking decisions from Cam's comments on the final synthesis.

## Status

| # | Topic | Status |
|---|-------|--------|
| 1 | 90/10 rule | Done |
| 2 | Competitors | Done |
| 3 | Silence, blocking, motifs | Done |
| 4 | Progressive disclosure + AI edits | Done |
| 5 | Continuity just happens | Done |
| 6 | Personal resonance | Done |
| 7 | Models improve | Done |
| 8 | Model upgrade problem | Done |
| 9 | Real filmmaker assets | Done |
| 10 | "Love this" | Done |
| 11 | AI auto-generates everything | Done |
| 12 | Script bible + hierarchy | Done |
| 13 | Intent layer = biggest knobs | Done |
| 14 | Pre-generate all artifacts | Done |

## Decisions

### #2 — Competitors (Affirmation)
CineForge is a fun project regardless of competitive landscape. No design decision needed.

### #6 — Personal resonance (Affirmation)
Non-filmmaker awareness tiers validated against real user experience. Confirms "beginners first" design priority.

### #10 — "Love this" (Affirmation)
Dual organizational system in filmmaking confirmed: logistical by department, creative by intent. CineForge follows the creative organization model.

### #13 — Intent layer = biggest knobs (Affirmation)
Three-layer architecture confirmed. Intent/Mood is the primary interaction surface. Most users may only need this layer + character design to satisfy their vision.

### #12 — Script bible + project hierarchy
**Decision:**
1. **Add script bible artifact** — logline, synopsis, act structure, themes, narrative arc. First artifact derived from the script.
2. **Project = Story.** The project is a technical container (meta-settings: API config, cost budgets, format preferences) around the script. All creative artifacts (characters, locations, props, scenes, direction, design) are story-derived. The UI shows them at top level because the story IS the top level.
3. **Script revision triggers entity reconciliation** via change propagation (R15). AI categorizes entities as: unchanged (stay valid), minor changes (targeted bible update, preserve accumulated design work), removed (flagged, never auto-deleted), added (fresh extraction). Never auto-destroys accumulated creative work like reference images, voice, or costume design.

**Key insight:** "Project-level vs. script-level" is a false distinction. The project IS the story. Characters belong to the story. Only a madman drops in a 100% different script (just start a new project). The real use case is script revisions, which change propagation already handles.

### #4 — Progressive disclosure + AI editing artifacts
**Decision:**
1. **Progressive disclosure is the UX principle** — all 87 elements exist in the system, none required from the user, depth is always optional. The AI considers all of them when generating; the user only touches what they care about.
2. **Prompts are read-only compiled artifacts** — viewable for transparency (R12), but NOT directly editable. The prompt is a projection of upstream artifacts, like compiled assembly output. Changes go upstream (via chat or direct edit), prompt recompiles automatically. This avoids the sync nightmare of hand-edited prompts that can never be re-generated.
3. **"Chat about this" interaction** — user highlights any part of any artifact, drops it into chat with the appropriate AI role pre-tagged. New interaction pattern, needs a story.
4. **AI artifact editing** — roles can propose AND execute artifact edits with user permission (per autonomy settings from Story 089). When the user says "give the Mariner a moustache," the AI updates the character bible upstream, change propagation fires, and the prompt recompiles with the moustache. This is how the Ideal's conversational iteration actually works mechanically.

**Key insight:** The user wants to edit the final prompt (natural instinct), but allowing it breaks single-source-of-truth. Instead: full transparency (read the prompt), full control (change anything upstream), and AI as the editing agent (tell it what to change, it changes the right artifact). The prompt is a window, not a door.

### #1 + #11 + #14 — 90/10 rule, AI auto-generates, pre-generate for repeatability
**Decision:**
1. **"Script in → everything generated → user reacts" is the golden path**, not an advanced feature. The AI reads the script, generates all 87 elements with its best creative judgment, and produces a watchable result. Every decision is captured in artifacts for repeatability.
2. **Two lanes: Story and Film.** Story lane (extraction/understanding: script → bible → scenes → entities → continuity) is cheap, always runs on import. Film lane (creative interpretation: mood → look → sound → direction → shots → video) is expensive, runs on demand — only when the user signals they want visual output.
3. **Per-element "let AI fill this" buttons.** Every generatable artifact has an explicit generation action. Users can: let AI generate, generate-then-tweak, skip AI and specify manually, or leave empty (AI improvises at render, red readiness). This maps to R5's full spectrum.
4. **Generation doubles as teaching.** Even users who plan to specify everything manually benefit from seeing what AI produces — it shows what the element IS and what good looks like. Aligns with the Ideal's "teaching in context" vision preference.

**Key insight:** Auto-generation is the default intent but not the default action for film-lane artifacts. The system is always ready to generate everything, but waits for the user to ask. Story-lane extraction runs immediately because it's cheap and always useful. Film-lane generation fires when the user enters the Scene Workspace or hits generate — at which point missing upstream artifacts are generated or flagged.

### #5 — Continuity just happens
**Decision:** Continuity is automatic, always-on, story-lane infrastructure. The system tracks costume state, injury state, prop state, location state, and character consistency across scenes without user intervention. Users CAN override continuity decisions, but 99.999% never will. This is a "just works" feature — the user shouldn't even think about it unless they want to deliberately break continuity for creative reasons (e.g., a dream sequence where props teleport).

**Key insight:** Continuity is one of the easiest wins because it's pure infrastructure. The user gets massive value (no continuity errors across scenes) with zero effort. Override capability exists for the rare creative exception, not as a primary interaction.

### #3 — Silence, blocking, motifs
**Decision:** The three most commonly neglected elements in AI generation. Each has a different strategy and confidence level:

1. **Silence** — Compromise territory. Specify correctly in artifacts (sound direction includes explicit silence directives). Actual output quality depends on video gen models — AI video gen tends to be frantic and nonstop even in quiet scenes. Engine packs (Story 028) are where model-specific workarounds live; experiment with what works per model. Detection mechanism: when models respect silence directives natively, remove workarounds.
2. **Blocking** — Acknowledged unknown. The storyboard-as-input hypothesis (deep blocking in storyboard prompts → storyboard images as video gen inputs) is worth testing, but we don't know enough yet to commit to a design decision. Punt to experimentation when we reach that stage.
3. **Visual motifs** — Motifs (not just consistency) tracked as metadata annotations on entity bibles at any scope: character bible, location bible, prop bible, scene-level, or world/project-level. Example: "every time John makes a choice, there's a mirror in frame" → character bible annotation. "Every time we see the sky there's an alien ship looming in the distance" → world-level annotation. Scene planning AI receives these as inputs. Story World concern group tracks them across the project.

**Key insight:** These are three different kinds of problems — a model limitation (silence), an unknown (blocking), and an architecture concern (motifs). Don't treat them as one thing.

### #7 — Models improve
**Decision:** "AI keeps improving" is the mantra. The Ideal-first framework already handles this — compromises carry detection mechanisms, the spec shrinks over time. No new architectural requirement needed beyond what we already have.

The practical implication: how much workaround infrastructure to build for today's limitations will only be known through experimentation and cost/benefit analysis. It may be that a filmmaker simply can't get a certain result right now due to model limitations. We keep driving toward the Ideal and when models improve, things that were blocked start working. Don't over-invest in workarounds for problems that will solve themselves.

**Key insight:** This is a team attitude, not an architectural decision. The Ideal-first methodology already provides the structure (compromises tagged, detection mechanisms in place). What this comment adds is the confidence: these limitations are temporary, keep moving.

### #8 — Model upgrade problem
**Decision:** Two concerns:

1. **Prompt workaround decay.** Old projects may accumulate prompt hacks for older model weaknesses. New models given those crazy-specific prompts may produce unexpected artifacts. **Solution: Decision #4 already handles this.** Prompts are compiled from upstream artifacts. The compilation layer can be updated for new models without touching user-facing artifacts. Creative intent is preserved upstream; downstream prompt format adapts. This is a key reason prompts-as-compiled-artifacts matters.

2. **Round-trip decomposition.** Added to ideal.md as a vision preference: take an existing film → decompose into CineForge artifacts → modify any element → re-render. If the round-trip works, the artifact model is complete. The film decomposition/remix feature itself (take Pulp Fiction, recast, re-render) is far-future — captured in inbox, not a near-term requirement.

**Key insight:** The prompt-as-compiled-artifact decision (#4) is the technical solution to model upgrade pain. The round-trip test is the north star for artifact model completeness.

### #9 — Real filmmaker assets
**Decision:** Real-world asset support is a **core design principle, not a feature**. CineForge is for anyone doing any part of a film production process, including people who want to use CineForge for only a SINGLE aspect (previz, sound design, storyboards) and do the rest IRL. This means deep ability to take real-world assets into CineForge.

**New Ideal requirement (R17):** "The system must accept real-world production assets as first-class inputs at any point in the workflow." Uploaded assets (photos, videos, audio, documents) are treated identically to AI-generated artifacts. The system doesn't care whether an asset was generated or uploaded.

**Three deferred capabilities (→ inbox):**
1. **AI enhancement of minimal inputs** — headshot → full reference set, phone video → clean stills
2. **Location lookup from web** — "Sydney Opera House" → fetch public images for reference
3. **Mood-board synthesis** — multiple inspiration images → synthesized character/location/prop designs

**Key insight:** This isn't "you can upload a photo." It's that CineForge works for partial workflows. The entire pipeline must be agnostic about asset origin.
