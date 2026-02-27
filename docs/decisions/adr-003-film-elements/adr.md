# ADR-003: Film Elements — The Creative Gap Between Screenplay and Film

**Status:** DECIDED — Option E (Three-Layer Director's Vision Model)

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

**Option E — Three-Layer "Director's Vision" Model.** An intent-first interface layered over creative concern groups, with scope as the underlying data model.

All four research reports (Google, OpenAI, Claude, Grok) unanimously rejected Option A (role-organized) and converged on Option D (creative concern) as the strongest grouping. Three of four independently proposed the same enhancement: layer an emotional/mood-first intent interface on top of concern groups, with scope as the implementation substrate. This became Option E. See `research/film-elements/final-synthesis.md` for the full analysis and `decisions-log.md` for all 14 comment decisions.

### The Architecture

**Layer 1 — The Mood Board (Intent Layer).** The primary interaction surface for all users. Mood/tone selectors (tense, warm, chaotic, dreamy). Reference input (films, directors, aesthetic subcultures). Style presets / "vibe" packages. Natural language ("make this scene darker and tenser"). Changes here auto-propagate to all five concern groups.

**Layer 2 — The Creative Concerns (Detail Layer).** Five groups containing tightly coupled elements:
- **Look & Feel:** Lighting, color, camera composition, set design, costume, visual motifs, aspect ratio
- **Sound & Music:** Ambient/room tone, SFX, music, Foley, silence (deliberate), mixing, audio motifs
- **Rhythm & Flow** (labeled "Pace & Energy" for non-filmmakers): Pacing, camera movement dynamics, editing transitions, coverage pattern, scene function
- **Character & Performance:** Emotional intensity, vocal delivery, physical performance, blocking, motivation
- **Story World:** Character/location/prop design baselines, continuity tracking, behavioral consistency, narrative rhythm

**Layer 3 — The Scope Substrate (Implementation Layer).** Not user-facing navigation. Project-wide settings are global constraints. Per-scene settings override project-wide. Per-shot settings are granular control signals. Expert users can access scope directly; beginners never see it.

### Key Design Decisions

1. **87 elements total** across five domains (pre-production 27, per-scene 19, per-shot 14, post-production 14, cross-cutting 13). All exist in the system, none required from the user.

2. **Progressive disclosure.** The AI considers all 87 elements when generating; the user only touches what they care about. Depth is always optional, never required.

3. **Prompts are read-only compiled artifacts.** Viewable for transparency (R12), NOT directly editable. The prompt is a projection of upstream artifacts. Changes go upstream (via chat or direct edit), prompt recompiles automatically. "The prompt is a window, not a door."

4. **Two lanes: Story and Film.** Story lane (extraction/understanding) is cheap, always runs on import. Film lane (creative interpretation/generation) is expensive, runs on demand when the user enters the Scene Workspace or hits generate.

5. **Per-element "let AI fill this" buttons.** Every generatable artifact has an explicit generation action. Users can: let AI generate, generate-then-tweak, skip AI and specify manually, or leave empty (AI improvises at render, red readiness).

6. **Project = Story.** The project is a technical container (API config, cost budgets, format preferences) around the script. All creative artifacts are story-derived. Script revision triggers entity reconciliation via R15 change propagation.

7. **Script bible artifact.** Logline, synopsis, act structure, themes, narrative arc. First artifact derived from the script, sits between script and entity extraction.

8. **Continuity as automatic infrastructure.** Always-on, story-lane. Tracks costume/injury/prop/location state across scenes without user intervention. Override available for deliberate creative breaks.

9. **Templates beat parameters.** Curated starting points (mood presets, style references, "vibe" packages) outperform blank parameter spaces for both beginners and experts.

10. **"Chat about this" interaction.** User highlights any part of any artifact → drops into chat with the appropriate AI role pre-tagged. New interaction pattern.

11. **AI artifact editing.** Roles can propose AND execute artifact edits with user permission (per autonomy settings). "Give the Mariner a moustache" → AI updates character bible → change propagation fires → prompt recompiles.

12. **Neglected elements handled through existing architecture.** Silence via role emphasis (sound roles actively recommend silence). Blocking via storyboard pipeline (deep blocking in storyboard prompts → visual inputs to video gen). Visual motifs via global style/mood settings.

13. **"Models improve" as design principle.** Current compromises are tagged as temporary with detection mechanisms. Architecture designed so model improvements automatically reduce complexity and improve quality. Don't over-engineer solutions for today's limitations.

14. **Prompt compilation handles model upgrades.** Because prompts are compiled from upstream artifacts, the compilation layer can be updated for new models without touching user-facing artifacts. Creative intent is preserved upstream; downstream prompt format adapts.

15. **Real-world assets as first-class inputs.** Upload photos/videos as reference images. AI enhancement of minimal inputs (headshot → full reference set). Location lookup from web. Mood-board input for design synthesis.

16. **Round-trip decomposition (Ideal).** The ultimate validation: take an existing film → decompose into CineForge artifacts → modify any element → re-render. Added to ideal.md as a vision requirement.

### Readiness Indicators

Red/yellow/green at the creative concern group level per scene:
- **Red:** No user input. AI guesses everything using project defaults.
- **Yellow:** Some guidance (mood propagated, or partial specification). AI fills gaps.
- **Green:** User reviewed and approved all key elements for this group.

Summary dashboard: for each scene, five concern-group indicators showing exactly where attention is needed.

### Propagation Checklist

Tracking everything updated (or needing update) as a result of this ADR.

#### Ideal
- [x] R17 added — real-world assets as first-class inputs
- [x] Round-trip decomposition added as vision preference
- [x] Inbox items added — film decomposition/remix, AI asset enhancement, location lookup, mood-board synthesis

#### Spec
- [x] Rewrite §12 (Creative Direction Artifacts) — four direction types → five concern groups + Intent/Mood layer
- [x] Add section: Script Bible — §4.5
- [x] Add section: Two-Lane Architecture — §4.6
- [x] Add section: Prompt Compilation Model — §12.8
- [x] Update §4.4 (Project Configuration) — project = story (technical container around the script)
- [x] Update §9 (Combined Roles) — roles contribute to concern groups, not produce standalone direction artifacts
- [x] Update §13 (Shot Planning) — consumes concern group artifacts, not converged direction set
- [x] Expand §18 (User Asset Injection) — flesh out for R17 (origin-agnostic asset system)
- [x] Resolve untriaged item "Prompt transparency / direct prompt editing" — now decided (read-only, Decision #4)
- [x] Update Compromise Index — role consolidation note at §9.1-9.2 needs context update

#### Stories — Cancel
- [x] Cancel Story 024 (Direction Convergence) — eliminated by ADR-003

#### Stories — Reshape
- [x] Story 021 (Visual Architect) — visual direction → "Look & Feel" concern group
- [x] Story 022 (Sound Designer) — sound direction → "Sound & Music" concern group
- [x] Story 023 (Performance Direction) — resolve "prove your worth"; performance lives in Character & Performance concern group, Actor Agents contribute, Story 084 may already cover
- [x] Story 025 (Shot Planning) — remove dependency on 024, consumes concern group artifacts
- [x] Story 028 (Render Adapter) — prompt construction ACs: direction refs → concern group refs

#### Stories — Check for Impact
- [x] Story 026 (Storyboard Generation) — minor rewording for concern group refs
- [x] Story 027 (Animatics/Previz) — similar to 026
- [x] Story 029 (User Asset Injection) — R17 expansion added
- [x] Story 030 (Generated Output QA) — dependency refs updated
- [x] Story 056 (Entity Design / Reference Images) — dependency note updated (inputs TO Look & Feel)
- [x] Story 082 (Creative Direction UX) — ADR-003 impact note added to work log (Done story, code updates deferred)
- [x] Story 085 (Pipeline Capability Graph) — ADR-003 impact note added to work log (Done story, graph.py updates deferred)

#### Stories — New (skeletons, no implementation detail)
- [x] Story 093: Script bible artifact — schema + extraction from script, first story-lane artifact after ingestion
- [x] Story 094: Concern group artifact schemas — the data model replacing four direction types
- [x] Story 095: Intent/Mood layer — style presets, mood selectors, reference input, auto-propagation to concern groups
- [x] Story 096: "Chat about this" interaction — highlight artifact text → chat with pre-tagged role
- [x] Story 097: AI artifact editing — roles edit artifacts with user permission (per autonomy settings)
- [x] Story 098: Real-asset upload pipeline — R17: upload, manage, slot into reference systems
- [x] Story 099: Scene Workspace — R11 Layer 2 interface with five concern tabs per scene
- [x] Story 100: Motif tracking — annotations at any scope (character, location, world-level)

#### Stories Index
- [x] Update `docs/stories.md` to reflect all cancellations, reshapes, and new stories

#### Evals
- No existing evals invalidated (eval catalog tests extraction, not direction)
- Future evals: script bible extraction quality, concern group completeness (when stories are built)

## Legacy Context

The current spec (§9-12) implements Option A (role-organized). Story 020 (Editorial Architect) is Done and produces editorial direction artifacts. Stories 021 (Visual), 022 (Sound), 023 (Performance) are To Do/Draft. Story 024 (Direction Convergence) requires all four direction types before shot planning.

The Ideal-first retrofit flagged this architecture as potentially over-structured. The "convergence" step in particular feels like it's solving a problem (cross-role consistency) that exists because we organized by role in the first place.

Whatever this ADR decides will reshape Stories 021-024 and inform the Scene Workspace design (Ideal R11).

## Dependencies

- **Depends on:** `docs/ideal.md` (R7 iterative refinement, R8 production artifacts, R11 production readiness, R12 transparency)
- **Informs:** Stories 021-024 (direction architecture), Scene Workspace story (R11), Stories 025-028 (shot planning through render — consume direction output)
- **Related:** ADR-002 (Goal-Oriented Navigation) — the two-view architecture (Story Explorer + Scene Workspace) is the presentation layer for whatever element structure this ADR decides
