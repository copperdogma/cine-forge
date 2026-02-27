# ADR-003: Film Elements — The Creative Gap Between Screenplay and Film

**Status:** PENDING — Needs deep research

## Context

A screenplay provides dialogue, action descriptions, scene headings, and character presence. A finished film requires hundreds of additional creative decisions: how the scene is lit, where the camera goes, what the audience hears, how actors deliver their lines, what the color palette feels like, when to cut.

CineForge must help users specify (or let AI generate) every one of these elements. The current spec (§9-12) organizes these elements by **professional film role**: Editorial Architect produces editorial direction, Visual Architect produces visual direction, Sound Designer produces sound direction, Actor Agents produce performance direction. This maps to how real film crews are organized.

But is this the right organizing principle for the **user experience**?

The Ideal says CineForge should feel like a creative conversation, not like operating a pipeline. Users think "I want this scene darker and more tense" — that's simultaneously a visual note (lighting), a sound note (ambient), an editorial note (pacing), and a performance note (restraint). Forcing users to think in terms of professional roles may be the wrong abstraction.

**The core questions:**
1. What is the **complete set** of creative elements between a screenplay and a generated film?
2. How should those elements be **grouped** for intuitive user understanding?
3. How do users **explore, specify, generate, and iterate** on them — informed by the Ideal?

**What prompted this:** During the `/retrofit-ideal` alignment review, we realized the four-direction architecture (editorial, visual, sound, performance) with a required convergence step (Story 024) may be over-structured. Direction types feel more like **advice** than **required pipeline stages**. The AI video generator will make all these decisions regardless — the question is whether the user has specified them (intentionally) or left them to AI improvisation.

This connects directly to the Scene Workspace concept (Ideal R11) — a per-scene control surface showing what's specified vs. AI-inferred, with red/yellow/green readiness per element.

## The Ideal (No Technology Constraints)

You tell CineForge your story. It understands everything. You start exploring — "make this scene darker," "John should be more vulnerable here," "I want silence after the gunshot, then slowly build ambient sound." Each instruction touches whatever elements it touches. You never think about which "direction type" you're adjusting. You're just describing what you want.

The Scene Workspace shows you, for any scene: here's what you've specified, here's what the AI is improvising, here's what it would look like if you generated now. Click any element to explore, refine, or lock it down. Or ignore it all and let AI fill everything — that works too.

The element groupings exist to make the workspace navigable, not to impose a workflow. They're like sections of a form, not stages of a pipeline.

## Options

### Option A: Role-Organized (Current Spec)

Elements organized by which professional film role traditionally owns them.

**Groups:** Editorial Direction, Visual Direction, Sound Direction, Performance Direction

**Pros:**
- Maps to real filmmaking workflow — educational value
- Clear ownership per AI role — each role knows its scope
- Proven in spec (§12.1-12.4), partially implemented (Story 020 Done)

**Cons:**
- Users don't think in roles ("make it darker" is visual + sound + editorial)
- Requires convergence step (Story 024) to reconcile cross-role conflicts
- Performance direction (Story 023) is deferred — the model already feels incomplete
- Four rigid categories may not map to how users naturally describe their vision

### Option B: Perceptual Modality

Elements organized by what the audience perceives.

**Groups:** Visual (what you see), Audio (what you hear), Temporal (how it flows), Emotional (what you feel)

**Pros:**
- Intuitive for non-filmmakers — sensory-based grouping
- Aligns with how users describe intent ("I want it to feel tense")

**Cons:**
- Blurs professional boundaries (camera work and costume are both "visual" but very different decisions)
- "Emotional" is a meta-category that touches everything — hard to scope
- May be too abstract for users who DO have filmmaking knowledge

### Option C: Element Scope

Elements organized by what they apply to.

**Groups:** Project-Wide (visual style, character design), Per-Scene (lighting, camera, pacing), Per-Shot (framing, movement, angle)

**Pros:**
- Clear hierarchy — set broad style, then per-scene, then per-shot
- Matches the natural refinement flow

**Cons:**
- Some elements span scopes (character wardrobe is project-wide but may change per scene)
- Doesn't help users find what to specify — "pacing" and "lighting" are both per-scene but totally different

### Option D: Creative Concern (Hybrid)

Elements organized by what the user is trying to accomplish creatively.

**Possible groups:**
- **Look & Feel:** Lighting, color, composition, camera, set dressing, costume, visual motifs
- **Sound & Music:** Ambient, effects, music, silence, sound transitions, diegetic/non-diegetic
- **Rhythm & Flow:** Pacing, transitions, coverage strategy, scene function, edit intent
- **Character & Performance:** Emotional state, motivation, subtext, blocking, delivery, voice
- **Story World:** Character design, location design, prop design, continuity tracking

**Pros:**
- Groups match how users naturally think about creative intent
- Each group is a coherent "thing to explore" in the Scene Workspace
- A single user instruction ("make it darker and tenser") maps to Look & Feel + Sound & Music — clear, not confusing
- Compatible with role system (roles contribute to multiple groups)

**Cons:**
- Novel taxonomy — no film industry precedent to lean on
- Boundaries may be debatable (is "blocking" performance or visual?)
- Need to validate against real user mental models

## Research Needed

- [ ] **Complete element inventory:** What is the exhaustive set of creative decisions between screenplay and generated film? Include elements from pre-production (design), production (shooting), and post-production (editing, color, sound mix). Don't forget edge cases: VFX, titles, aspect ratio, frame rate.
- [ ] **How do existing AI film tools organize these?** LTX Studio, Runway, Kling, Pika, Sora — what elements do they expose to users? How are they grouped? What do users praise or complain about?
- [ ] **How do real filmmakers organize creative decisions?** What does pre-production paperwork look like (breakdown sheets, shot lists, mood boards, lookbooks, sound design docs)? How do directors communicate vision to department heads?
- [ ] **User mental model validation:** When non-filmmakers describe what they want in a scene, what vocabulary and groupings do they naturally use? Research from UX studies, film education, or consumer video tools.
- [ ] **Interaction patterns for element specification:** How should users specify elements — per-scene forms, conversation, visual comparison, reference images, sliders, presets? What works best for iterative refinement (the core creative loop)?
- [ ] **How do elements interact?** Which elements constrain or influence each other? (e.g., high-key lighting constrains color palette; fast pacing constrains shot duration). This informs whether groupings should reflect these dependencies.

## Decision

TBD — pending research.

## Legacy Context

The current spec (§9-12) implements Option A (role-organized). Story 020 (Editorial Architect) is Done and produces editorial direction artifacts. Stories 021 (Visual), 022 (Sound), 023 (Performance) are To Do/Draft. Story 024 (Direction Convergence) requires all four direction types before shot planning.

The Ideal-first retrofit flagged this architecture as potentially over-structured. The "convergence" step in particular feels like it's solving a problem (cross-role consistency) that exists because we organized by role in the first place.

Whatever this ADR decides will reshape Stories 021-024 and inform the Scene Workspace design (Ideal R11).

## Dependencies

- **Depends on:** `docs/ideal.md` (R7 iterative refinement, R8 production artifacts, R11 production readiness, R12 transparency)
- **Informs:** Stories 021-024 (direction architecture), Scene Workspace story (R11), Stories 025-028 (shot planning through render — consume direction output)
- **Related:** ADR-002 (Goal-Oriented Navigation) — the two-view architecture (Story Explorer + Scene Workspace) is the presentation layer for whatever element structure this ADR decides
