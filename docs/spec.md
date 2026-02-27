CineForge Project Specification

AI-Driven Film Reasoning, Pre-Production, and Generation Pipeline

> **This spec is a set of compromises against the Ideal (`docs/ideal.md`).**
> Every section that exists because of a limitation is annotated with its limitation
> type and detection mechanism. AI compromises have deletion evals — when they pass,
> the compromise is deleted. World compromises have evolution paths — they transform
> toward the Ideal over time. This document should shrink and simplify over time.
> That is the goal.
>
> Sections not annotated are **Ideal requirements** — they describe what the system
> should do regardless of implementation and are mirrored in `docs/ideal.md`.

⸻

1. Purpose & Scope

This system is a film reasoning and production compiler that transforms a story (script or prose) into a complete, production-ready set of film artifacts.

It supports:
	•	AI-generated films
	•	Real-world (IRL) film production
	•	Hybrid workflows
	•	Education and film pedagogy

Video generation is optional, not mandatory. The system is equally valuable when stopped before rendering.

⸻

2. Core Design Principles (Non-Negotiable)

2.1 Artifact Immutability
	•	All generated artifacts are read-only.
	•	No artifact is ever modified in place.
	•	All changes produce new artifacts with lineage.
	•	Full auditability is mandatory.

2.2 Version History (Snapshot Model)

Every versioned artifact (scripts, scenes, bibles, timelines, etc.) is stored as a complete immutable snapshot: script_v1, script_v2, script_v3, etc.

	•	Any version can be loaded directly — no reconstruction required.
	•	Diffs between any two versions are computed on demand (not stored as diff-chains).
	•	The full version history of any artifact is navigable ("time walking").
	•	Each version records its lineage: what it was derived from, what changed, and why.

Storage is cheap. Reconstruction complexity is not. Prefer snapshots over diff-chains.

2.3 Revision and Change Propagation

The pipeline is iterative, not one-shot. Users and roles revise artifacts throughout the creative process. Revisions propagate through the dependency graph in two layers:

Layer 1 — Structural Invalidation (automatic, instant, free):
	•	The system maintains a dependency graph: every artifact records what it was built from.
	•	When a new version of an artifact is created (e.g., scene_7_v2), all downstream artifacts that transitively depend on the previous version (scene_7_v1) are automatically marked as stale.
	•	This is deterministic graph traversal — no AI call required.

Layer 2 — Semantic Impact Assessment (AI, on-demand):
	•	An AI call diffs the old and new versions, examines the stale artifacts, and triages them.
	•	Each stale artifact is assessed and annotated: does it actually need revision given what changed, or is it still valid?
	•	The assessment produces "needs work" annotations with rationale and provenance (why does it need work? what specifically changed? which role flagged it?).

Artifact health status:
	•	valid — current, no upstream changes
	•	stale — structurally invalidated by an upstream revision, not yet assessed
	•	needs_revision — AI assessed, confirmed affected, with notes on what needs to change
	•	confirmed_valid — AI assessed, still correct despite upstream change

The user or Director may also manually decide which stale artifacts to revise without running the AI assessment.

2.4 AI-Driven at Every Stage
	•	Every processing step is performed by AI roles.
	•	Non-AI logic is limited to:
	•	artifact storage
	•	versioning
	•	dependency resolution
	•	scheduling / queueing
	•	No rule-based “business logic” replaces AI reasoning.

2.5 Human Control Is Optional and Configurable
	•	The pipeline may run:
	•	fully autonomously
	•	with human checkpoints
	•	fully manually with AI as advisor
	•	Humans participate through three modes: approve/reject proposals, collaborative creative sessions with agents, and direct artifact editing. All produce new artifact versions, never in-place mutations. (See 8.7 for full details.)

2.6 Explanation Is Mandatory
	•	Any AI role proposing a decision must explain:
	•	what is proposed
	•	why
	•	tradeoffs
	•	confidence
	•	Teaching and pedagogy are first-class features.

2.7 Cost Transparency
	•	Every AI call's cost is tracked and surfaced.
	•	Per-stage and per-run cost summaries are available.
	•	The system supports cost-quality tradeoffs: cheaper models for initial passes, stronger models for refinement.
	•	Budget caps may be configured per-project or per-run to prevent runaway costs.
	•	Cost data is recorded in run artifacts for auditability.

> **⚙️ Compromise C1 — Cost Transparency** [Ecosystem/Infrastructure]
> **The Ideal:** AI inference is free. No cost tracking needed.
> **The Limitation:** AI inference has non-trivial, variable monetary costs across providers.
> **Detection:** Monitor inference pricing trends. When cost per 1M tokens drops below $0.001 across all providers used.
> **When It Resolves:** Delete cost tracking per call, budget cap system, and cost-quality tiering UI. Keep aggregate cost reporting for business purposes only.

2.8 Quality Validation (QA)
... (existing content) ...
artifact's audit metadata.

2.9 Subsumption-based Model Strategy

The pipeline supports a tiered model assignment strategy to balance cost, speed, and intelligence.

Model Tiers (Slots):
	•	work: The primary model for task execution (e.g., gpt-4o-mini).
	•	verify: The model responsible for QA/validation passes.
	•	escalate: A high-intelligence model (SOTA) used only when the work model fails verification.

Precedence Hierarchy (Subsumption):
	1.	Module Override: Specific module code defines a mandatory model.
	2.	Recipe Params: The YAML recipe provides specific model overrides for a stage.
	3.	Project Global: The default tiers selected at the project/run level (e.g., via UI Profiles).

Namespacing:
The strategy supports namespaces (e.g., text.work, video.work) to allow specialized models for different media types while maintaining a fallback to generic slots.

Resilient Work Pattern:
Modules should attempt work with the 'work' slot, validate with 'verify', and automatically retry using the 'escalate' slot if validation fails.

> **⚙️ Compromise C2 — QA Validation Passes** [AI Capability]
> **The Ideal:** AI output is reliably correct. No separate verification step needed.
> **The Limitation:** AI outputs are unreliable — hallucinations, structural errors, missed requirements.
> **Detection:** Run eval: submit 10 diverse extraction tasks to SOTA model. If all pass structural + semantic validation on first attempt without QA, this compromise can be simplified.
> **When It Resolves:** Delete dedicated QA pass stages, verify model tier slot, and QA-specific schemas. Keep structural validation as a lightweight assertion (not a separate AI call).

> **⚙️ Compromise C3 — Tiered Model Strategy** [AI Capability + Ecosystem]
> **The Ideal:** One model does everything perfectly.
> **The Limitation:** No single model is reliably capable across all tasks at acceptable cost. Different tasks need different models.
> **Detection:** When a single model achieves top-tier quality on all 9 eval tasks (character/location/prop extraction, scene extraction, normalization, enrichment, QA, config detection, relationship discovery) at acceptable latency.
> **When It Resolves:** Delete model selection infrastructure (work/verify/escalate slots, subsumption hierarchy, namespace routing, escalation logic). Replace with single model config.
> **Compromise-Level Preferences:** Model selection UI, per-stage model override, cost profiles.

⸻

3. High-Level System Overview

Story Input
   ↓
Script Normalization
   ↓
Scene Breakdown (Tier 1 — structural, fast)
   ↓
Scene Analysis (Tier 2 — narrative, LLM-heavy, user-triggered)
   ↓
Bibles & Entity Graph
   ↓
Creative Direction (Editorial, Visual, Sound, Performance)
   ↓
Shot Planning
   ↓
(OPTIONAL) Storyboards
   ↓
(OPTIONAL) Animatics / Previz Video
   ↓
(OPTIONAL) Keyframes
   ↓
(OPTIONAL) AI Video Generation

At any stage, the user may:
	•	stop
	•	inject assets
	•	lock artifacts

All artifacts for a project live in a single project folder. If a user wants to explore an alternative direction ("branching"), they can copy the entire project folder and continue from that snapshot. No formal branching mechanism is required in the MVP.

3.1 Stage Progression (User-Controlled)

The pipeline is not rigidly sequential. Users choose how to move through it:

	•	Breadth-first ("traditional film"): advance all scenes through each stage before moving to the next. Complete the full script breakdown, then all bibles, then all shot plans, etc. This mirrors how real film productions work — lock the script, then prep everything in parallel.
	•	Depth-first ("sizzle reel"): take a single scene (or a handful) all the way through every stage to final output. Use this to lock in look, feel, flow, voices, and music before committing to the full production. Ideal for proof-of-concept and investor pitches.
	•	Hybrid: any combination. Do script breakdown and bibles breadth-first, then go deep on the opening scene to nail the tone, then return to breadth-first for shot planning.

The system does not enforce an ordering. Stage transitions are user- or Director-initiated, not automatic. In autonomous mode, the Director follows the user's chosen strategy.

Completion criteria per stage are role-defined: Canon Guardians must sign off (or be overridden by the Director) before a scene's artifacts at that stage are considered ready. In checkpoint mode, the user must also approve.

⸻

4. Input Handling & Story Ingestion

4.1 Accepted Inputs
	•	Proper screenplay (standard format)
	•	Prose fiction
	•	Radio play / audio drama
	•	Notes, outlines, hybrid formats

4.2 Script Normalization (Required)
	•	AI determines whether input is already a screenplay.
	•	If not, AI converts it into screenplay form.
	•	Conversion must:
	•	preserve intent
	•	explicitly label inventions
	•	emit confidence and assumptions

4.3 Canonical Script Rule
	•	Once script_vN exists, it is immutable canon.
	•	All downstream artifacts reference script spans.

4.4 Project Configuration (Auto-Initialized)

Story ingestion automatically extracts project-level parameters from the input. These are presented to the user as a draft project configuration that may be confirmed or modified before the pipeline proceeds.

Auto-detected parameters include:
	•	Project title
	•	Format: short film, feature, series episode, music video, etc.
	•	Genre: horror, comedy, drama, thriller, etc.
	•	Tone: dark and grounded, whimsical, surreal, etc.
	•	Estimated duration or duration range
	•	Cast size and primary characters
	•	Number and nature of locations
	•	Target audience (if inferable)

User-specified parameters (not auto-detected):
	•	Aspect ratio
	•	Production mode: AI-generated, IRL, hybrid
	•	Human control mode: autonomous, checkpoint, advisory
	•	Style pack selections per role
	•	Budget / cost cap preferences

The confirmed project configuration becomes a canonical artifact that every role consults. All roles should read and respect project-level parameters when making creative decisions.

⸻

5. Scene Breakdown & Analysis (Required)

5.1 Two-Tier Architecture

Scene processing is split into two tiers:

**Tier 1 — Scene Breakdown** (structural, fast, mostly deterministic):
	•	Splits canonical script into individual scene artifacts
	•	Parses headings (INT/EXT, location, time of day)
	•	Classifies elements (dialogue, action, transitions)
	•	Collects character names from dialogue cues and action mentions
	•	Produces `scene` artifacts with `narrative_beats=[]`, `tone_mood="neutral"`
	•	Produces `scene_index` with `discovery_tier: "structural"` annotation
	•	Runs in seconds, giving users a browsable scene index immediately

**Tier 2 — Scene Analysis** (narrative, LLM-heavy, user-triggered):
	•	Enriches scenes with narrative beats, tone/mood, and tone shifts
	•	Uses Macro-Analysis: processes 5-10 scenes per LLM call for arc consistency
	•	Gap-fills structural unknowns (UNKNOWN location, UNSPECIFIED time)
	•	Produces updated `scene` artifact versions and enriched `scene_index`
	•	Updates `discovery_tier` to `"llm_enriched"`

> **⚙️ Compromise C4 — Two-Tier Scene Architecture** [AI Capability]
> **The Ideal:** Scene analysis is instant and complete in a single pass — structural parsing, narrative beats, tone, and gap-filling all happen together.
> **The Limitation:** Full LLM-based scene analysis is slow (~30s+) and expensive. Users need a browsable scene index immediately.
> **Detection:** Run eval: submit full screenplay to SOTA model requesting complete scene analysis (structure + narrative + tone). If results are high-quality AND return in <5 seconds, the two-tier split is unnecessary.
> **When It Resolves:** Merge scene_breakdown_v1 and scene_analysis_v1 into a single module. Delete Tier 1 placeholder values (`narrative_beats=[]`, `tone_mood="neutral"`), discovery_tier annotations, and the separate "Analyze Scenes" user action. Scene extraction becomes one step.
> **Compromise-Level Preferences:** "Analyze Scenes" button, discovery tier indicator in UI, macro-analysis batch size.

5.2 Scene Definition

A scene is the atomic narrative unit and must be extracted even if already explicit.

Each scene includes:
	•	source script span
	•	inferred or explicit location
	•	time of day
	•	characters present
	•	narrative beats (empty after Breakdown, populated after Analysis)
	•	tone and mood (neutral after Breakdown, enriched after Analysis)
	•	confidence markers
	•	field provenance (method: rule/parser/ai)

5.3 Creative Inference
	•	When scenes are inferred (e.g., prose), inference must be labeled.
	•	Confidence scores are mandatory.
	•	`discovery_tier` annotation tracks completeness: "structural" → "llm_enriched" → "llm_verified".

⸻

6. Bibles & Entity Graph

6.1 Asset Masters

The system maintains master definitions for:
	•	Characters
	•	Locations
	•	Props

Each master includes:
	•	explicit evidence (quoted)
	•	inferred traits (flagged)
	•	relationships (see 6.2)

6.2 Entity Graph (Relationships)

Entities do not exist in isolation. The system maintains a queryable graph of typed relationships between entities:

Character ↔ Character:
	•	familial (parent, sibling, spouse)
	•	social (friend, rival, mentor, employer)
	•	narrative (protagonist/antagonist, ally, foil)

Character ↔ Location:
	•	home, workplace, associated location
	•	scene presence (which characters appear at which locations, when)

Character ↔ Prop:
	•	ownership or association (the detective's notebook, the villain's ring)
	•	narrative significance (Chekhov's gun)

Location ↔ Location:
	•	spatial containment (the bedroom is inside the house)
	•	adjacency / proximity (the alley is behind the bar)

Relationships are:
	•	Extracted from the script during ingestion and bible creation (with confidence scores)
	•	Stored as explicit typed edges, not buried in free text
	•	Queryable by any role (e.g., "which characters share scenes?", "what props appear at this location?")
	•	Versioned alongside the bibles they connect — when a bible entry gets a new version, affected relationship edges are updated

The entity graph powers continuity checking (Continuity Supervisor), narrative consistency (Script Supervisor), and shot planning (which assets must be present in frame).

6.3 Bible Artifact Structure

Each entity (character, location, prop) is a folder-based artifact, not a single file. A bible entry may contain:
	•	master definition (JSON)
	•	quoted source evidence
	•	AI-inferred traits (flagged with confidence)
	•	continuity state snapshots (per story point)
	•	reference images, sketches, user-injected photos
	•	role decisions and notes

Each bible folder includes a manifest that tracks all files, their versions, and provenance. Individual files within the folder are immutable; "updating" a bible means adding new files and producing a new manifest version.

6.4 Asset States (Continuity)

Assets are stateful over story time.
	•	State snapshots are immutable artifacts.
	•	State changes occur via explicit continuity events.
	•	Shots consume state snapshots, not masters.
	•	States are stored within each entity's bible folder.

Examples:
	•	costume change
	•	injury
	•	aging
	•	damage
	•	set destruction

⸻

7. Timeline (First-Class Requirement)

7.1 Timeline Artifact

A timeline_vN artifact exists independently of final video.

It supports:
	•	scene order (edit order)
	•	story order (chronology)
	•	shot subdivision
	•	stacked tracks

7.2 Tracks (Non-Exhaustive)
	•	Script
	•	Dialogue / Audio
	•	Shots
	•	Storyboards
	•	Animatics
	•	Keyframes
	•	Generated Video
	•	Continuity Events
	•	Music / SFX

7.3 Always-Playable Rule
	•	The timeline must be scrubbable at all times.
	•	The system displays the best available representation:
	•	storyboard if no video
	•	animatic if present
	•	final render if present

⸻

8. Role System

8.1 Role Hierarchy

Canon Authority
	•	Director
	•	Final decision authority
	•	Oversees taste, intent, tradeoffs
	•	Can negotiate locks (within user policy)

Canon Guardians
	•	Script Supervisor
	•	Narrative logic
	•	Motivation
	•	Knowledge consistency
	•	Continuity Supervisor
	•	Physical and temporal state consistency

Canon Guardians may block progression pending review.

Structural Advisors
	•	Editorial Architect
	•	Visual Architect
	•	Sound Designer

Structural Advisors propose and design but cannot finalize canon changes.

Performance
	•	Actor Agent (one per character)

Actor Agents suggest but cannot modify canon; accepted insights may update bibles.

Note: The Render Adapter is not a role. It is a stateless module with no creative agency (see Section 17).

8.2 Capability Gating

Roles must declare perception capability:
	•	text
	•	image
	•	video
	•	audio+video

Roles must not pretend to evaluate media they cannot truly understand.

> **⚙️ Compromise C5 — Capability Gating** [AI Capability]
> **The Ideal:** All AI is universally multimodal — every role can perceive and reason about text, images, video, and audio natively.
> **The Limitation:** Current models have fragmented multimodal support. Some are text-only, some handle images, few handle video+audio reliably.
> **Detection:** When the SOTA model reliably processes text + image + video + audio in a single call with high-quality reasoning across all modalities.
> **When It Resolves:** Delete perception capability declarations from role schemas, delete modality routing logic in runtime.py. All roles become universally capable.

8.3 Style Packs

Any creative role (Director, Structural Advisors, Actor Agents) may accept an optional style pack — an externally-authored creative personality profile that shapes how the role thinks without changing what it does.

Style packs:
	•	Are folder-based artifacts (rich text description + optional reference images, frame grabs, palettes)
	•	Are selected per-role in the project or recipe configuration
	•	Do not change a role's permissions, hierarchy position, or structural function
	•	May be mixed across roles (e.g., one director style + a different visual style)
	•	A "generic" default pack always exists for each role type

Canon Guardians (Script Supervisor, Continuity Supervisor) do not accept style packs. They enforce consistency, not taste.

Examples:
	•	Director: Tarantino (nonlinear structure, sharp dialogue, chapter-based pacing)
	•	Visual Architect: Roger Deakins (natural lighting, muted palette, long takes) + reference frame grabs
	•	Actor Agent: Daniel Day-Lewis (method immersion, physical expressiveness, minimal dialogue)
	•	Sound Designer: David Lynch (industrial drones, ominous ambient, silence as tension)
	•	Editorial Architect: Thelma Schoonmaker (kinetic cuts, rhythm-based editing)

Style pack user input may be:
	•	A single name
	•	A combination of names or aspects
	•	A movie, TV show, or book title
	•	A completely original description of a new style

8.4 Style Pack Creation

Each role definition includes a style pack creation prompt — a role-specific template that guides a deep research AI to explore the right creative dimensions for that role type.

The creation prompt:
	•	Tells the research AI what to look for (e.g., for Director: narrative structure, pacing, thematic obsessions, tonal range, approach to violence/humor/emotion)
	•	Specifies how to format the output for use with CineForge
	•	Accepts any user input as the subject (name, combination, reference work, or original description)

Deep research APIs (OpenAI Agents SDK, Google Gemini Interactions API) enable in-app style pack creation:
	•	User selects a role type and provides freeform input
	•	System loads the role-specific creation prompt template and injects user input
	•	Deep research API runs asynchronously (may take minutes) with progress updates
	•	Result is auto-formatted into a properly structured style pack folder

If no deep research API is available, the creation prompt can be used manually (pasted into ChatGPT, Gemini, etc.).

8.5 Suggestion System

Roles continuously generate insights and proposals. Not all are acted on immediately. The system must capture, track, and surface suggestions as a creative backlog.

Every suggestion is an immutable artifact with:
	•	Source role (who proposed it)
	•	Related scene, entity, or artifact (what it's about)
	•	The proposal itself (what is being suggested)
	•	Confidence and rationale (why, and how confident)

Suggestion lifecycle status:
	•	proposed — newly generated, not yet reviewed
	•	accepted — folded into canon (produces a new artifact version)
	•	rejected — declined, with reason recorded
	•	deferred — starred for later ("good idea, not now")
	•	superseded — a newer suggestion replaced this one

Deferred suggestions are resurfaced when their related scene or entity comes up for revision. The user or Director may browse and search all suggestions at any time.

8.6 Inter-Role Communication and Disagreement Protocol

All inter-role communication is recorded. This includes:
	•	Conversations: raw turn-by-turn transcripts between roles, linked to the decisions they produced
	•	Decisions: explicit artifacts recording what was decided, by whom, why, and what alternatives were considered
	•	Overrides: when a higher-tier role overrides a lower-tier objection, both positions are preserved with full rationale

When roles disagree:
	•	The objection is recorded as an artifact (not silently discarded).
	•	The higher-authority role (per the hierarchy) may override with explicit justification.
	•	Both the objection and the override rationale are preserved permanently.
	•	Example: Continuity Supervisor flags a break; Director overrides with "intentional for dramatic effect" — both positions are recorded and linked to the affected artifacts.

Conversation transcripts are retained in full. Storage is cheap; forensic, educational, and creative-archaeological value is high. A Director should be able to revisit past conversations to understand the chain of thought behind any decision.

8.7 Human Interaction Model

The human is the ultimate authority in the system — above even the Director AI. The spec must define not just that humans can participate, but how.

Creative Sessions (Collaborative Chat):

The human may open a conversation with any role or group of roles. This is the primary brainstorming and direction-giving interface.

	•	@agent addressing: the human directs remarks to specific roles using @director, @visual_architect, @actor_jane, etc. Unaddressed remarks are routed to whichever role is contextually relevant.
	•	Auto-inclusion: when the conversation touches another role's domain, that role is automatically brought in. The Director AI coordinates inclusion. Example: the human starts discussing a scene with an Actor Agent; when lighting comes up, the Visual Architect joins.
	•	Selective silence: agents only speak when they have something relevant to contribute, are directly addressed, or when the topic falls within their authority. Lower-tier agents do not interrupt higher-tier discussions unless asked.
	•	Wandering scope is expected: a conversation may start about acting, shift to backstory, then to lighting, then to pacing. The system adapts by including and releasing agents as topics shift.
	•	Artifact proposals: when a conversation converges on something actionable, the responsible agent(s) propose artifact updates via the suggestion system (8.5). The human can accept, reject, or defer proposals inline during the conversation.
	•	All creative session transcripts are recorded as immutable artifacts per Section 8.6.

Direct Artifact Editing:

The human may directly edit any artifact at any time. This is the authoritative mode — no discussion needed.

	•	Immutability preserved: a direct edit creates a new artifact version, never an in-place mutation.
	•	Immediately canon: the human's edit takes effect without requiring approval from any role.
	•	Agent commentary: the system notifies responsible agents and the Director of the change. They may attach commentary as suggestions (e.g., "this lighting choice may conflict with the continuity established in scene 2") but they cannot block a human edit.
	•	The human is free to incorporate, defer, or ignore agent feedback on their edits.

The three modes of human participation:

	•	Approve / reject: respond to AI-generated proposals (existing workflow)
	•	Collaborate: creative sessions with agents to brainstorm, question, and direct
	•	Direct edit: authoritatively change any artifact, with optional agent feedback

All three are recorded. All three produce new artifact versions, never in-place mutations. The human may use any combination at any time regardless of the project's operating mode.

⸻

9. Combined Roles (Intentional Consolidation)

9.1 Editorial Architect

Combines:
	•	Editor
	•	Transitions
	•	Visual motion reasoning

Responsibilities:
	•	cut-ability prediction
	•	coverage adequacy
	•	pacing
	•	transition suggestions

9.2 Visual Architect

Combines:
	•	production design
	•	costume
	•	lighting philosophy
	•	locations
	•	visual motifs

Ensures global visual cohesion.

⸻

10. Performance System

10.1 Actor Agents (Required)
	•	One AI per character.
	•	Embodies character psychology.
	•	Analyzes each scene from inside the role.
	•	Suggests:
	•	motivation
	•	subtext
	•	dialogue alternatives
	•	behavioral consistency

10.2 Governance
	•	Actor agents cannot modify canon.
	•	Accepted insights may update character bibles.

⸻

11. Sound Design

11.1 Early Sound Design (Required)

Sound design begins before shot planning.

Responsibilities:
	•	sound-driven storytelling
	•	silence placement
	•	offscreen cues
	•	audio-based transitions

11.2 Output
	•	Sound intent annotations
	•	Optional temp audio
	•	IRL-ready sound asset lists

⸻

12. Creative Direction Artifacts (Required)

The pipeline stages "Editorial / Narrative Oversight" and "Visual / Performance / Sound Design" produce structured direction artifacts that are consumed by Shot Planning and all downstream stages. These are the richest AI reasoning outputs in the system — where roles translate raw story material into creative vision.

All direction artifacts are immutable, versioned, and carry standard audit metadata.

12.1 Editorial Direction (per scene or per act)

Produced by: Editorial Architect
Reviewed by: Director, Script Supervisor

	•	Scene function: what role this scene plays in the larger narrative arc (inciting incident, escalation, climax, resolution, transition, etc.)
	•	Pacing intent: fast/slow, building/releasing tension, breathing room
	•	Transition strategy: how to enter and exit this scene (hard cut, dissolve, match cut, sound bridge, smash cut, etc.) and why
	•	Coverage priority: what the editor will need to assemble this scene (e.g., "prioritize close-ups for emotional beats in the first half; wide two-shot for the confrontation")
	•	Montage / parallel editing candidates: if applicable
	•	Act-level notes: when scoped to an act, includes pacing arc, turning points, and rhythm across scenes

12.2 Visual Direction (per scene)

Produced by: Visual Architect
Reviewed by: Director

	•	Lighting concept: key light direction, quality (hard/soft), motivated vs. stylized, practical sources
	•	Color palette: dominant colors, temperature (warm/cool), saturation level, contrast
	•	Composition philosophy: symmetry, negative space, depth of field intention, framing style
	•	Camera personality: static/controlled vs. handheld/chaotic, observational vs. intimate
	•	Reference imagery: visual references (from style pack, user-injected, or AI-suggested)
	•	Costume and production design notes: what characters and the environment should look like in this scene, referencing bible states
	•	Visual motifs: recurring visual elements that connect to larger themes

12.3 Sound Direction (per scene)

Produced by: Sound Designer
Reviewed by: Director

	•	Ambient environment: what the audience should "hear" as the baseline (city noise, wind, silence, machinery hum)
	•	Emotional soundscape: how sound supports the scene's emotional arc
	•	Silence placement: intentional absence of sound and where it falls
	•	Offscreen audio cues: sounds from outside the frame that expand the world or foreshadow
	•	Sound-driven transitions: audio bridges, stingers, or motifs that connect to adjacent scenes
	•	Music intent: score direction (if applicable) — tension, release, theme, absence of score
	•	Diegetic vs. non-diegetic notes: what sounds exist in the story world vs. for the audience only

12.4 Performance Direction (per scene, per character)

Produced by: Actor Agent (for their character)
Reviewed by: Director, Script Supervisor

	•	Emotional state entering the scene: where the character is psychologically at the start
	•	Arc through the scene: how their emotional state changes (or doesn't)
	•	Motivation: what the character wants in this scene
	•	Subtext: what they're not saying, what's beneath the surface
	•	Physical notes: posture, energy level, gestures, habits
	•	Key beats: moments of change, realization, decision
	•	Relationship dynamics: how this character relates to others in the scene (using entity graph)
	•	Dialogue delivery notes: tone, pace, emphasis for specific lines (if applicable)

12.5 Direction Convergence

Before shot planning begins for a scene, all four direction artifacts must exist. The Director reviews the set for internal consistency:
	•	Does the editorial intent align with the visual approach?
	•	Does the sound design support or conflict with the pacing plan?
	•	Do the performance notes fit the visual framing?

Conflicts are resolved through the standard disagreement protocol (8.6). The converged direction set becomes the input to shot planning.

⸻

13. Shot Planning (Required)

Note: Shot planning consumes the creative direction artifacts from Section 12. Every shot references the editorial, visual, sound, and performance direction that informed it.

Shot planning is where all upstream creative decisions converge into concrete, shot-by-shot instructions. It translates "what happens in this scene" into "what the audience sees and hears." The output mirrors a real-world shot list but is richer — every shot also records the reasoning behind each choice and references to the upstream artifacts that informed it.

13.1 Scene Coverage Strategy (one per scene)

Before individual shots are defined, the system produces a coverage strategy for each scene:
	•	Coverage approach: what types of shots are needed and why (e.g., "intimate dialogue — master, OTS pair, close-up singles; no inserts needed")
	•	Editorial intent: how this scene should cut together, pacing targets, transition in/out (from Editorial Architect)
	•	Visual intent: overall lighting, color, mood, composition philosophy for the scene (from Visual Architect)
	•	Sound intent: ambient environment, silence placement, offscreen audio cues (from Sound Designer)
	•	Performance notes: key emotional beats, subtext, motivation for this scene (from Actor Agents)
	•	Coverage adequacy check: does the planned coverage give the editor enough angles to assemble the scene?

13.2 Individual Shot Definition

Each shot in the plan includes:

Framing and Camera:
	•	Shot size: Extreme Wide, Wide/Establishing, Full, Medium, Medium Close-Up, Close-Up, Extreme Close-Up, Insert
	•	Camera angle: Eye level, Low angle, High angle, Dutch/Canted, Bird's eye, Worm's eye
	•	Camera movement: Static, Pan, Tilt, Dolly/Track, Crane/Jib, Steadicam, Handheld, Drone
	•	Lens / focal length: Wide (18-35mm), Normal (40-60mm), Telephoto (85mm+)

Content:
	•	Scene reference and shot ID (e.g., scene 7, shot C)
	•	Characters in frame (and whose POV, if applicable)
	•	Blocking: where characters are positioned, how they move during the shot
	•	Action / description: what happens visually
	•	Dialogue: any lines delivered during this shot
	•	Duration estimate

Editorial and Coverage:
	•	Coverage role: Master, Single, Two-shot, Over-the-Shoulder, Reaction, Insert, Cutaway
	•	Edit intent: why this shot exists from an editing perspective

Continuity and References:
	•	Asset state snapshots consumed (not masters — per Section 6.4)
	•	References to upstream artifacts: scene, bible entries, visual/sound/editorial direction

Audit:
	•	Standard CineForge metadata: intent, rationale, alternatives considered, confidence, source

13.3 Coverage Patterns (Reference)

Standard coverage patterns the system should understand:
	•	Master: wide shot of the entire scene start to finish (safety net for editing)
	•	Singles / Close-ups: individual characters, usually for emotional beats
	•	Over-the-Shoulder (OTS): one character's shoulder in foreground, other character's face in focus (classic dialogue coverage)
	•	Two-shot: both characters in frame together
	•	Reaction shots: a character reacting to something offscreen
	•	Inserts / Cutaways: detail shots (a hand on a glass, a clock, a document)

The Editorial Architect is responsible for verifying that planned coverage is sufficient to assemble the scene in editing.

13.4 Export Compatibility

Shot plan artifacts contain all fields present in an industry-standard shot list. The system should be capable of exporting shot plans in formats usable by real film crews (formatted shot list documents, overhead/blocking diagrams, etc.). Export formatting is a presentation concern, not a pipeline stage.

⸻

14. Storyboards (Optional)

Note: Storyboards are derived from the shot plan (Section 13). Each storyboard frame corresponds to one or more shots.

14.1 Purpose
	•	cheap visualization
	•	blocking
	•	eyelines
	•	camera intent

14.2 Styles
	•	sketch
	•	clean line
	•	animation-style
	•	abstract color-coded
	•	photoreal (discouraged, gated)

⸻

15. Animatics / Previz Video (Optional, Selective)

15.1 Granularity
	•	per project
	•	per act
	•	per scene
	•	per shot

15.2 Characteristics
	•	low detail
	•	accurate timing
	•	accurate camera motion
	•	symbolic characters and sets

15.3 Previz Reel
	•	mixed storyboard + animatic timeline
	•	temp dialogue and sound
	•	used for review and education

15.4 Serendipity Preservation
	•	previs never mandatory
	•	director policy controls rigidity
	•	divergence from previs explicitly allowed

⸻

16. Keyframes (Optional)
	•	start / mid / end frames
	•	lockable by director
	•	used to constrain video generators
	•	derived from storyboards or animatics

⸻

17. Render Adapter Layer (Required for Generation)

The Render Adapter is a stateless module, not a creative role. It has no opinions, no hierarchy position, and no review gates. It is a prompt compiler that translates film artifacts into model-ready generation prompts.

17.1 Two-Part Prompt Architecture
	•	Part 1 — Generic meta-prompt: expert at producing rich AI video generation prompts from film artifacts (shot plan, scene context, character states, visual direction, sound intent). Model-agnostic. Focuses on quality and completeness.
	•	Part 2 — Model-specific engine pack: adapts the prompt to a specific AI video generation model's strengths, limits, preferred language, and supported inputs.
	•	Synthesis: a single AI call combines both parts with the actual creative inputs into one cohesive, model-optimized prompt.
	•	The synthesized prompt is then sent to the target model API along with any supported inputs (keyframes, audio, reference images).

17.2 Engine Packs
	•	Per-generator tuning profiles (swappable configuration files)
	•	Known strengths, limits, failure modes
	•	Supported inputs (number of keyframes, audio support, max duration, etc.)
	•	Preferred prompt language and structure
	•	Retry and mitigation strategies

17.3 Error Handling
	•	The Render Adapter reports errors when a request exceeds model capabilities (e.g., requested duration exceeds model max, required inputs not supported by target model).
	•	Errors bubble up to the pipeline; the adapter does not negotiate or make creative decisions.
	•	It cannot change creative intent.

> **⚙️ Compromise C6 — Render Adapter Engine Packs** [Ecosystem/Infrastructure]
> **The Ideal:** One universal video generation API accepts rich film artifacts and produces high-quality, consistent video.
> **The Limitation:** AI video generation models have wildly different APIs, prompt formats, supported inputs (keyframes, audio, reference images), duration limits, and quality characteristics. No standard exists.
> **Detection:** Monitor for: (1) a dominant video generation API standard, or (2) a single model that handles all input types with a clean, stable API.
> **When It Resolves:** Delete engine pack system (per-model tuning profiles, retry strategies). Simplify Render Adapter to a single-target client. Delete model-specific prompt synthesis step.
> **Compromise-Level Preferences:** Engine pack selection UI, per-model capability display, model comparison view.

⸻

18. User Asset Injection (Required)

Users may inject artifacts at any stage:
	•	actor photos
	•	location photos
	•	prop references
	•	dialogue audio

Injected assets may be:
	•	soft-locked
	•	hard-locked

AI may propose relaxing locks but may not override without approval.

⸻

19. Memory Model

19.1 Canonical Memory
	•	Artifacts (immutable, versioned)
	•	Policies (project configuration, control mode)
	•	Decisions (explicit decision artifacts with audit metadata)
	•	Suggestions (full backlog with lifecycle status; see 8.5)
	•	Conversation transcripts (raw turn-by-turn records; see 8.6)

19.2 Working Memory (Cached)
	•	Long-running chats allowed only for:
	•	Director
	•	Script Supervisor (optional)
	•	Periodically summarized into artifacts.
	•	Resettable.
	•	Raw transcripts are always retained even when working memory is summarized or reset.

> **⚙️ Compromise C7 — Working Memory Distinction** [AI Capability]
> **The Ideal:** AI has unlimited, persistent memory. No distinction between "working" and "canonical" memory — all prior context is always available.
> **The Limitation:** AI context windows are finite (128K-200K tokens) and expensive. Long conversations must be summarized or truncated.
> **Detection:** When context windows exceed 10M tokens at negligible cost, OR when AI models natively support persistent cross-session memory.
> **When It Resolves:** Delete working memory management (summarization triggers, compaction logic, Director/Script Supervisor memory limits). All conversations are fully retained in context. Delete the "Chats are accelerators" principle — chats become truth alongside artifacts.

19.3 Rule

Chats are accelerators. Artifacts are truth. Transcripts are permanent.

⸻

20. Metadata & Auditing (Required)

Every artifact and decision must include:
	•	intent
	•	rationale
	•	alternatives considered
	•	confidence
	•	source (AI / human / hybrid)

⸻

21. Valid Operating Modes
	•	Full autonomy
	•	Human checkpoints
	•	Advisory only
	•	No previs
	•	Education / coaching mode
	•	AI generation
	•	IRL production

All modes use the same pipeline.

⸻

22. Explicit Non-Goals
	•	Replacing human creativity
	•	Forcing rigid planning
	•	Guaranteeing aesthetic success
	•	Eliminating serendipity

⸻

23. Summary

This system is:
	•	a film reasoning engine
	•	a production compiler
	•	a teaching director
	•	a generator adapter
	•	a preproduction backbone

AI generation is optional.
Understanding, structure, and auditability are not.

⸻

## Compromise Index

All compromises in this spec, ordered by architectural significance (which, if resolved, eliminates the most downstream complexity).

| # | Compromise | Spec Ref | Limitation Type | Detection Summary |
|---|-----------|----------|-----------------|-------------------|
| C1 | Cost transparency & budget management | 2.7 | Ecosystem | Inference cost → ~$0 |
| C2 | Dedicated QA validation passes | 2.8 | AI capability | SOTA output reliably correct on first attempt |
| C3 | Tiered model strategy (work/verify/escalate) | 2.9 | AI capability + Ecosystem | Single model handles all tasks at top quality |
| C4 | Two-tier scene architecture | 5.1 | AI capability | Full scene analysis in <5s single pass |
| C5 | Role capability gating (modality) | 8.2 | AI capability | Universal multimodal AI |
| C6 | Render adapter engine packs | 17.1–17.2 | Ecosystem | Universal video generation API standard |
| C7 | Working memory distinction | 19.2 | AI capability | Context windows >10M tokens at negligible cost |

**Additional compromise elements** within otherwise-ideal sections (not separately indexed, but noted):

| Section | Compromise Element | Type | Notes |
|---------|-------------------|------|-------|
| 2.3 | Layer 2 change propagation as separate on-demand step | AI capability | With instant/free AI, Layer 1+2 merge — all invalidation becomes semantic |
| 4.2 | Script normalization as a distinct pipeline stage | AI capability | With perfect multiformat reasoning, normalization becomes invisible |
| 4.4 | Manual project config fields (aspect ratio, production mode) | AI capability | With fully context-aware AI, more fields become auto-inferrable |
| 5.3 | Discovery tier annotations | AI capability | With single-pass analysis, tier tracking is unnecessary |
| 8.4 | Async style pack creation flow | AI capability + Ecosystem | With capable synchronous AI, becomes a single call |
| 9.1–9.2 | Role consolidation (Editorial/Visual Architect) | AI capability | With negligible per-role cost, roles could be more specialized |
| 19.3 | "Chats are accelerators" distinction | AI capability | With persistent memory, chats become truth alongside artifacts |

⸻

## Untriaged Ideas

Raw ideas from `docs/inbox.md` and design sessions that relate to the spec but haven't been
incorporated into a compromise or confirmed as an Ideal requirement. Work through these as
the spec evolves. Don't delete — incorporate or explicitly discard with rationale.

### From docs/inbox.md (2026-02-26)

- **Voice specification for characters**: Users should be able to specify character voices — tone, accent, age, reference clips. Feeds into video/audio generation. Needs a spec section under Section 10 (Performance System) or Section 12 (Creative Direction).

- **Scene-level vs shot-level video generation**: Kling 3.0 generates multi-shot sequences (up to 6 cuts per generation). The atomic unit for video gen is shifting from "shot" toward "scene." Scene Workspace should be scene-first with shot detail as drill-down. Affects Section 13 (Shot Planning) and Section 17 (Render Adapter).

- **Prompt transparency / direct prompt editing**: For any AI-generated output, show the exact prompt and let users edit/re-submit. Captured in Ideal R12 but needs a spec section defining how prompts are stored and versioned as artifacts.

- **"AI-filled" / skip-ahead state with visible marking**: When users generate without completing upstream, AI fills gaps. Each AI-guessed element needs visible labeling and quality degradation indicators. Captured in Ideal R11 but needs spec detail on the "AI-inferred" artifact state beyond the current valid/stale/needs_revision taxonomy.

- **AI preference learning from user choices**: Record every AI suggestion + user's final choice as training data for better future suggestions. Captured in Ideal R13 but needs a spec section on the preference data model and how it feeds back into role behavior.

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Faded AI suggestions inline with user content. Tab to accept, keep typing to dismiss. Good for script editing, bible enrichment, config tuning.

- **Onboarding flow**: "I'm a [Screenwriter/Director/Producer/Explorer]" single question, skippable, defaults to Explorer. Configures default workspace, pipeline bar emphasis, AI verbosity. Partially covered by Story 090.

- **Explorer demo project**: Pre-populated tutorial project (Notion pattern) so new users can explore capabilities immediately without uploading their own content.

- **Per-feature AI autonomy levels**: Auto/assisted/manual per pipeline action — more granular than the three operating modes in Section 2.5. Partially covered by Story 090.

- **Quality estimates in preflight**: "★★★☆☆ estimated quality" based on what upstream is complete vs. missing. Extends the tiered response system from ADR-002.

- **Narrative-aware timeline export**: When exporting to NLE formats, embed scene boundaries, beat changes, character entrances, emotional tone shifts as markers, color-coded regions, and clip notes. Captured in Ideal R9 but needs spec detail under Section 7 (Timeline).

- **Video preview/assembly view**: Simple player with scene strip — drag to reorder, click to play, basic trim. NOT a full NLE. Captured in Ideal R10.

⸻

End of Specification