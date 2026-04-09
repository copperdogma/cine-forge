CineForge Project Specification

AI-Driven Film Reasoning, Pre-Production, and Generation Pipeline

> **This spec is a set of active compromises against the Ideal (`docs/ideal.md`).**
> It now covers both product constraints and execution constraints. Categories are
> organized as `spec:1` through `spec:11`, matching the methodology state and
> generated planning dashboards. Each category may contain product constraints,
> build constraints, or both.
> Hierarchical section IDs (for example `spec:4.10.2`) are the stable
> cross-reference surface across stories, ADRs, build-map entries, and triage
> guidance.
>
> Every active compromise should name:
> - the ideal behavior
> - the limitation forcing the compromise
> - the limitation type
> - the detection mechanism for when the limitation changes
> - what gets deleted, simplified, or transformed when it resolves
>
> **Compromise-level preferences** on individual compromises (UX decisions, config
> options, tuning parameters) are legitimate engineering investments, but they are
> tied to their compromise and die when it is eliminated or transformed. They are
> the counterpart to the **vision-level preferences** in `docs/ideal.md`, which
> persist across all implementations regardless of what compromises exist.

---

## Purpose & Scope

This system is a film reasoning and production compiler that transforms a story
(script or prose) into a complete, production-ready set of film artifacts.

It supports:
- AI-generated films
- Real-world (IRL) film production
- Hybrid workflows
- Education and film pedagogy

Video generation is optional, not mandatory. The system is equally valuable when
stopped before rendering.

## spec:1 — Foundation & Artifact Runtime

> **Product need:** Every artifact, decision, and transformation must be durable,
> auditable, and safe to revise without losing history.
> **Tech substrate:** Immutable artifacts, snapshot versioning, dependency-aware
> invalidation, and a clear runtime boundary between AI reasoning and non-AI
> orchestration.

### spec:1.1 — Artifact Immutability

- All generated artifacts are read-only.
- No artifact is ever modified in place.
- All changes produce new artifacts with lineage.
- Full auditability is mandatory.

### spec:1.2 — Version History (Snapshot Model)

Every versioned artifact (scripts, scenes, bibles, timelines, and so on) is
stored as a complete immutable snapshot: `script_v1`, `script_v2`, `script_v3`,
and so on.

- Any version can be loaded directly. No reconstruction required.
- Diffs between any two versions are computed on demand, not stored as
  diff-chains.
- The full version history of any artifact is navigable ("time walking").
- Each version records its lineage: what it was derived from, what changed, and
  why.

Storage is cheap. Reconstruction complexity is not. Prefer snapshots over
diff-chains.

### spec:1.3 — Revision and Change Propagation

The pipeline is iterative, not one-shot. Users and roles revise artifacts
throughout the creative process. Revisions propagate through the dependency graph
in two layers:

**Layer 1 — Structural Invalidation** (automatic, instant, free):
- The system maintains a dependency graph: every artifact records what it was
  built from.
- When a new version of an artifact is created (for example `scene_7_v2`), all
  downstream artifacts that transitively depend on the previous version
  (`scene_7_v1`) are automatically marked as stale.
- This is deterministic graph traversal. No AI call required.

**Layer 2 — Semantic Impact Assessment** (AI, on demand):
- An AI call diffs the old and new versions, examines the stale artifacts, and
  triages them.
- Each stale artifact is assessed and annotated: does it actually need revision
  given what changed, or is it still valid?
- The assessment produces `needs work` annotations with rationale and
  provenance: why does it need work, what specifically changed, and which role
  flagged it.

Artifact health status:
- `valid` — current, no upstream changes
- `stale` — structurally invalidated by an upstream revision, not yet assessed
- `needs_revision` — AI assessed, confirmed affected, with notes on what needs to
  change
- `confirmed_valid` — AI assessed, still correct despite upstream change

The user or Director may also manually decide which stale artifacts to revise
without running the AI assessment.

**Additional compromise element:** Layer 2 existing as a separate on-demand step
is itself an AI-capability compromise. With instant, free semantic reasoning,
Layer 1 and Layer 2 collapse into one semantic invalidation pass.

### spec:1.4 — AI-Driven Runtime Boundary

- Every processing step is performed by AI roles.
- Non-AI logic is limited to:
  - artifact storage
  - versioning
  - dependency resolution
  - scheduling / queueing
- No rule-based "business logic" replaces AI reasoning.

### spec:1.5 — Pipeline Overview

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
- stop
- inject assets
- lock artifacts

All artifacts for a project live in a single project folder. If a user wants to
explore an alternative direction ("branching"), they can copy the entire project
folder and continue from that snapshot. No formal branching mechanism is
required in the MVP.

### spec:1.6 — Metadata & Auditing

Every artifact and decision must include:
- intent
- rationale
- alternatives considered
- confidence
- source (AI / human / hybrid)

## spec:2 — Story Intake & Understanding

> **Product need:** CineForge must accept story inputs in multiple forms and turn
> them into a coherent, browsable understanding of the screenplay quickly enough
> to start creative work.
> **Tech substrate:** Ingestion, normalization, canonical script handling,
> project-config inference, script-bible extraction, and scene understanding.

### spec:2.1 — Accepted Inputs

- Proper screenplay (standard format)
- Prose fiction
- Radio play / audio drama
- Notes, outlines, hybrid formats

### spec:2.2 — Script Normalization (Required)

- AI determines whether input is already a screenplay.
- If not, AI converts it into screenplay form.
- Conversion must:
  - preserve intent
  - explicitly label inventions
  - emit confidence and assumptions

**Additional compromise element:** Script normalization existing as a visibly
distinct pipeline stage is itself an AI-capability compromise. With perfect
multi-format reasoning, normalization becomes invisible.

### spec:2.3 — Canonical Script Rule

- Once `script_vN` exists, it is immutable canon.
- All downstream artifacts reference script spans.

### spec:2.4 — Project Configuration (Auto-Initialized)

> **ADR-003 decision.** The project is the story. The project is a technical
> container (API config, cost budgets, format preferences) around the script. All
> creative artifacts (characters, locations, props, scenes, direction, design)
> are story-derived. The UI shows them at top level because the story is the top
> level. Script revision triggers entity reconciliation via R15 change
> propagation: AI categorizes entities as unchanged (stay valid), minor changes
> (targeted bible update, preserve accumulated design work like reference
> images/voice/costume), removed (flagged, never auto-deleted), or added (fresh
> extraction). The system never auto-destroys accumulated creative work.

Story ingestion automatically extracts project-level parameters from the input.
These are presented to the user as a draft project configuration that may be
confirmed or modified before the pipeline proceeds.

Auto-detected parameters include:
- Project title
- Format: short film, feature, series episode, music video, and so on
- Genre: horror, comedy, drama, thriller, and so on
- Tone: dark and grounded, whimsical, surreal, and so on
- Estimated duration or duration range
- Cast size and primary characters
- Number and nature of locations
- Target audience (if inferable)

User-specified parameters (not auto-detected):
- Aspect ratio
- Production mode: AI-generated, IRL, hybrid
- Human control mode: autonomous, checkpoint, advisory
- Style pack selections per role
- Budget / cost cap preferences

The confirmed project configuration becomes a canonical artifact that every role
consults. All roles should read and respect project-level parameters when making
creative decisions.

**Additional compromise element:** Manual project-config fields are themselves an
AI-capability compromise. With fully context-aware AI, more of this becomes
auto-inferrable.

### spec:2.5 — Script Bible (Story-Lane, Always Runs)

> **ADR-003 decision.** The script bible is the first artifact derived from the
> script, sitting between ingestion and entity extraction.

After the script is ingested and normalized, the system automatically extracts a
script bible:

- Logline: one-sentence summary
- Synopsis: 1-3 paragraph summary
- Act structure: identified acts and turning points
- Themes: major thematic concerns
- Narrative arc: overall story shape (setup → confrontation → resolution)
- Genre/tone confirmation: validated against auto-detected project configuration

The script bible is a story-lane artifact: cheap to produce and always generated
on import. It provides the high-level story context that all downstream roles
and concern groups reference.

### spec:2.6 — Two-Lane Architecture

> **ADR-003 decision.** The pipeline has two lanes with different
> cost/trigger characteristics.

**Story Lane** (always runs on import): extraction and understanding — script →
script bible → scene extraction → entity extraction → bibles → continuity →
entity graph. These are cheap LLM operations that produce the foundational
understanding of the story. Always runs automatically because the output is
always useful and the cost is low.

**Film Lane** (runs on demand): creative interpretation and generation —
intent/mood → concern groups (look, sound, rhythm, character, world) → shot
planning → storyboards → animatics → video generation. These are expensive
operations (multi-model, image/video generation). They run only when the user
enters the Scene Workspace or explicitly requests generation. Missing upstream
artifacts are generated or flagged at that point.

The two lanes share the same artifact store and dependency graph. Story-lane
artifacts are inputs to film-lane operations.

**Per-element generation actions (ADR-003).** Every generatable artifact has an
explicit "let AI fill this" action. Users can:
- let AI generate (default intent for film-lane)
- generate-then-tweak
- skip AI and specify manually
- leave empty (AI improvises at render time, red readiness)

Generation also doubles as teaching — even users who plan to specify everything
manually benefit from seeing what AI produces, because it shows what the element
is and what good looks like.

### spec:2.7 — Scene Breakdown & Analysis (Required)

Scene processing is split into two tiers:

**Tier 1 — Scene Breakdown** (structural, fast, mostly deterministic):
- Splits canonical script into individual scene artifacts
- Parses headings (INT/EXT, location, time of day)
- Classifies elements (dialogue, action, transitions)
- Collects character names from dialogue cues and action mentions
- Produces `scene` artifacts with `narrative_beats=[]`, `tone_mood="neutral"`
- Produces `scene_index` with `discovery_tier: "structural"` annotation
- Runs in seconds, giving users a browsable scene index immediately

**Tier 2 — Scene Analysis** (narrative, LLM-heavy, user-triggered):
- Enriches scenes with narrative beats, tone/mood, and tone shifts
- Uses Macro-Analysis: processes 5-10 scenes per LLM call for arc consistency
- Gap-fills structural unknowns (`UNKNOWN` location, `UNSPECIFIED` time)
- Produces updated `scene` artifact versions and enriched `scene_index`
- Updates `discovery_tier` to `"llm_enriched"`

### spec:2.7.1 — Scene Definition

A scene is the atomic narrative unit and must be extracted even if already
explicit.

Each scene includes:
- source script span
- inferred or explicit location
- time of day
- characters present
- narrative beats (empty after Breakdown, populated after Analysis)
- tone and mood (neutral after Breakdown, enriched after Analysis)
- confidence markers
- field provenance (`method: rule/parser/ai`)

### spec:2.7.2 — Creative Inference

- When scenes are inferred (for example from prose), inference must be labeled.
- Confidence scores are mandatory.
- `discovery_tier` tracks completeness: `structural` → `llm_enriched` →
  `llm_verified`.

**Additional compromise element:** Discovery-tier annotations are themselves an
AI-capability compromise. With single-pass scene understanding, the tier labels
become unnecessary.

### Constraints

**C4: Two-Tier Scene Architecture** [AI capability -> deletion]
*Ideal:* Scene analysis is instant and complete in a single pass: structural
parsing, narrative beats, tone, and gap-filling all happen together.
*Compromise:* Keep a fast structural breakdown plus a slower, user-triggered
narrative enrichment pass so users get a browsable scene index immediately.
*Detection:* Run `compromise-C4-two-tier-scenes`. Pass when full screenplay scene
analysis reaches high quality and returns in under `5000ms` per scene-equivalent
batch.
*Resolves:* Merge `scene_breakdown_v1` and `scene_analysis_v1`, delete placeholder
values (`narrative_beats=[]`, `tone_mood="neutral"`), remove `discovery_tier`,
and delete the separate "Analyze Scenes" action.
*Preferences:* "Analyze Scenes" button, discovery-tier UI indicator, macro-analysis
batch size.

## spec:3 — World Building & Continuity

> **Product need:** CineForge must turn screenplay understanding into persistent,
> queryable world artifacts that preserve continuity across the story.
> **Tech substrate:** Entity masters, bible folders, typed relationship edges, and
> state snapshots over story time.

### spec:3.1 — Asset Masters

The system maintains master definitions for:
- Characters
- Locations
- Props

Each master includes:
- explicit evidence (quoted)
- inferred traits (flagged)
- relationships (see `spec:3.2`)

### spec:3.2 — Entity Graph (Relationships)

Entities do not exist in isolation. The system maintains a queryable graph of
typed relationships between entities:

Character ↔ Character:
- familial (parent, sibling, spouse)
- social (friend, rival, mentor, employer)
- narrative (protagonist/antagonist, ally, foil)

Character ↔ Location:
- home, workplace, associated location
- scene presence (which characters appear at which locations, when)

Character ↔ Prop:
- ownership or association (the detective's notebook, the villain's ring)
- narrative significance (Chekhov's gun)

Location ↔ Location:
- spatial containment (the bedroom is inside the house)
- adjacency / proximity (the alley is behind the bar)

Relationships are:
- extracted from the script during ingestion and bible creation (with confidence
  scores)
- stored as explicit typed edges, not buried in free text
- queryable by any role (for example "which characters share scenes?" or "what
  props appear at this location?")
- versioned alongside the bibles they connect; when a bible entry gets a new
  version, affected relationship edges are updated

The entity graph powers continuity checking (Continuity Supervisor), narrative
consistency (Script Supervisor), and shot planning (which assets must be present
in frame).

### spec:3.3 — Bible Artifact Structure

Each entity (character, location, prop) is a folder-based artifact, not a single
file. A bible entry may contain:
- master definition (JSON)
- quoted source evidence
- AI-inferred traits (flagged with confidence)
- continuity state snapshots (per story point)
- reference images, sketches, user-injected photos
- role decisions and notes

Each bible folder includes a manifest that tracks all files, their versions, and
provenance. Individual files within the folder are immutable; "updating" a bible
means adding new files and producing a new manifest version.

### spec:3.4 — Asset States (Continuity)

Assets are stateful over story time.
- State snapshots are immutable artifacts.
- State changes occur via explicit continuity events.
- Shots consume state snapshots, not masters.
- States are stored within each entity's bible folder.

Examples:
- costume change
- injury
- aging
- damage
- set destruction

## spec:4 — Role System & Creative Direction

> **Product need:** CineForge should feel like collaboration with creative roles
> and characters who understand the story deeply and can shape it across all
> production disciplines.
> **Tech substrate:** Role hierarchy, style packs, suggestion tracking,
> inter-role transcripts, creative concern-group artifacts, and compiled prompts.

### spec:4.1 — Role Hierarchy

Canon Authority:
- Director
- Final decision authority
- Oversees taste, intent, tradeoffs
- Can negotiate locks (within user policy)

Canon Guardians:
- Script Supervisor
  - Narrative logic
  - Motivation
  - Knowledge consistency
- Continuity Supervisor
  - Physical and temporal state consistency

Canon Guardians may block progression pending review.

Structural Advisors:
- Editorial Architect
- Visual Architect
- Sound Designer

Structural Advisors propose and design but cannot finalize canon changes.

Performance:
- Actor Agent (one per character)

Actor Agents suggest but cannot modify canon; accepted insights may update
bibles.

Note: The Render Adapter is not a role. It is a stateless module with no
creative agency (see `spec:7.1`).

### spec:4.2 — Capability Gating

Roles must declare perception capability:
- text
- image
- video
- audio+video

Roles must not pretend to evaluate media they cannot truly understand.

### spec:4.3 — Style Packs

Any creative role (Director, Structural Advisors, Actor Agents) may accept an
optional style pack: an externally-authored creative personality profile that
shapes how the role thinks without changing what it does.

Style packs:
- are folder-based artifacts (rich text description + optional reference images,
  frame grabs, palettes)
- are selected per-role in the project or recipe configuration
- do not change a role's permissions, hierarchy position, or structural function
- may be mixed across roles (for example one director style plus a different
  visual style)
- always have a generic default pack per role type

Canon Guardians do not accept style packs. They enforce consistency, not taste.

Examples:
- Director: Tarantino (nonlinear structure, sharp dialogue, chapter-based pacing)
- Visual Architect: Roger Deakins (natural lighting, muted palette, long takes)
- Actor Agent: Daniel Day-Lewis (method immersion, physical expressiveness,
  minimal dialogue)
- Sound Designer: David Lynch (industrial drones, ominous ambient, silence as
  tension)
- Editorial Architect: Thelma Schoonmaker (kinetic cuts, rhythm-based editing)

Style-pack user input may be:
- a single name
- a combination of names or aspects
- a movie, TV show, or book title
- a completely original description of a new style

### spec:4.4 — Style Pack Creation

Each role definition includes a style-pack creation prompt: a role-specific
template that guides a deep-research AI to explore the right creative dimensions
for that role type.

The creation prompt:
- tells the research AI what to look for
- specifies how to format the output for use with CineForge
- accepts any user input as the subject

Deep-research APIs (OpenAI Agents SDK, Google Gemini Interactions API) enable
in-app style-pack creation:
- User selects a role type and provides freeform input
- System loads the role-specific creation prompt template and injects user input
- Deep-research API runs asynchronously (may take minutes) with progress updates
- Result is auto-formatted into a properly structured style-pack folder

If no deep-research API is available, the creation prompt can be used manually
(pasted into ChatGPT, Gemini, and so on).

**Additional compromise element:** Async style-pack creation is an AI-capability
and ecosystem compromise. With capable synchronous AI, it becomes a single call.

### spec:4.5 — Suggestion System

Roles continuously generate insights and proposals. Not all are acted on
immediately. The system must capture, track, and surface suggestions as a
creative backlog.

Every suggestion is an immutable artifact with:
- source role
- related scene, entity, or artifact
- the proposal itself
- confidence and rationale

Suggestion lifecycle status:
- `proposed` — newly generated, not yet reviewed
- `accepted` — folded into canon (produces a new artifact version)
- `rejected` — declined, with reason recorded
- `deferred` — starred for later ("good idea, not now")
- `superseded` — a newer suggestion replaced this one

Deferred suggestions are resurfaced when their related scene or entity comes up
for revision. The user or Director may browse and search all suggestions at any
time.

### spec:4.6 — Inter-Role Communication and Disagreement Protocol

All inter-role communication is recorded. This includes:
- conversations: raw turn-by-turn transcripts between roles, linked to the
  decisions they produced
- decisions: explicit artifacts recording what was decided, by whom, why, and
  what alternatives were considered
- overrides: when a higher-tier role overrides a lower-tier objection, both
  positions are preserved with full rationale

When roles disagree:
- The objection is recorded as an artifact, not silently discarded.
- The higher-authority role may override with explicit justification.
- Both the objection and the override rationale are preserved permanently.
- Example: Continuity Supervisor flags a break; Director overrides with
  "intentional for dramatic effect." Both positions remain linked to the affected
  artifacts.

Conversation transcripts are retained in full. Storage is cheap; forensic,
educational, and creative-archaeological value is high. A Director should be
able to revisit past conversations to understand the chain of thought behind any
decision.

### spec:4.7 — Combined Roles (Intentional Consolidation)

> **ADR-003 note.** Roles still exist as creative personas with distinct
> expertise, but they contribute to concern groups (`spec:4.10`) rather than
> producing standalone direction artifacts. A role may contribute to multiple
> concern groups. The organizational principle for the user is the concern group;
> the role is the creative voice behind it.

**Additional compromise element:** Role consolidation remains an
AI-capability/cost compromise. With negligible per-role overhead, roles could
become more specialized again. Under ADR-003, the question is no longer "how
many direction artifacts exist," but "how many advisory voices are worth keeping
separate."

### spec:4.7.1 — Editorial Architect

Primary contributor to: **Rhythm & Flow** (`spec:4.10.4`)

Combines:
- Editor
- Transitions
- Visual motion reasoning

Responsibilities:
- cut-ability prediction
- coverage adequacy
- pacing
- transition suggestions

### spec:4.7.2 — Visual Architect

Primary contributor to: **Look & Feel** (`spec:4.10.2`)

Combines:
- production design
- costume
- lighting philosophy
- locations
- visual motifs

Ensures global visual cohesion.

### spec:4.8 — Performance System

### spec:4.8.1 — Actor Agents (Required)

- One AI per character.
- Embodies character psychology.
- Analyzes each scene from inside the role.
- Suggests:
  - motivation
  - subtext
  - dialogue alternatives
  - behavioral consistency

### spec:4.8.2 — Governance

- Actor agents cannot modify canon.
- Accepted insights may update character bibles.

### spec:4.9 — Sound Design

### spec:4.9.1 — Early Sound Design (Required)

Sound design begins before shot planning.

Responsibilities:
- sound-driven storytelling
- silence placement
- offscreen cues
- audio-based transitions

### spec:4.9.2 — Output

- sound intent annotations
- optional temp audio
- IRL-ready sound asset lists

### spec:4.10 — Creative Direction — Concern Groups (Required)

> **ADR-003 decision.** Creative direction is organized by creative concern
> (what the user is trying to accomplish), not by professional role (who
> traditionally does it). Five concern groups, layered under an Intent/Mood entry
> point, with scope as the implementation substrate.

All concern-group artifacts are immutable, versioned, and carry standard audit
metadata. Roles contribute to multiple concern groups: they are not 1:1 mapped.
The Intent/Mood layer provides cross-group coherence; there is no separate
convergence step.

**~87 creative elements** exist between screenplay and finished film. All exist
in the system; none are required from the user. Progressive disclosure: the AI
considers all of them when generating; the user only touches what they care
about.

### spec:4.10.1 — Intent / Mood Layer

The primary interaction surface for all users, especially beginners. Changes here
auto-propagate suggested defaults to all five concern groups.

- mood/tone selectors: tense, warm, chaotic, dreamy, epic, intimate, raw,
  unsettling, and so on
- reference input: films, directors, aesthetic subcultures
- style presets / vibe packages: named starting points that set coherent defaults
  across all five concern groups simultaneously
- natural language routing: "make this scene darker and tenser"
- templates beat blank parameter spaces

### spec:4.10.2 — Look & Feel

Everything that shapes what the audience sees. Primary contributor: Visual
Architect role.

- lighting concept: key-light direction, quality, motivated vs stylized,
  practical sources
- color palette: dominant colors, temperature, saturation, contrast
- composition philosophy: symmetry, negative space, depth-of-field intention,
  framing style
- camera personality: static/controlled vs handheld/chaotic, observational vs
  intimate
- reference imagery: style pack, user-injected, or AI-suggested
- costume and production-design notes: what characters and environment look like,
  referencing bible states
- visual motifs: recurring visual elements tied to larger themes
- aspect ratio and format: if scene-specific override of project-wide setting

### spec:4.10.3 — Sound & Music

Everything that shapes what the audience hears. Primary contributor: Sound
Designer role. Sound design begins before shot planning. It is a creative input,
not an afterthought.

- ambient environment: baseline soundscape
- emotional soundscape: how sound supports the emotional arc
- silence placement: intentional absence of sound
- offscreen audio cues: sounds from outside the frame that expand the world or
  foreshadow
- sound-driven transitions: bridges, stingers, or motifs connecting scenes
- music intent: score direction
- diegetic vs non-diegetic
- audio motifs / leitmotifs

### spec:4.10.4 — Rhythm & Flow

Everything that shapes how the film moves. Labeled "Pace & Energy" in the UI for
non-filmmakers. Primary contributor: Editorial Architect role.

- scene function: role in the narrative arc
- pacing intent: fast/slow, building/releasing tension, breathing room
- transition strategy: how to enter and exit the scene and why
- coverage priority: what the editor needs
- camera-movement dynamics: speed, energy, type of movement
- montage / parallel-editing candidates
- act-level notes: pacing arc, turning points, rhythm across scenes

### spec:4.10.5 — Character & Performance

Everything about how characters inhabit the scene. Contributors: Actor Agents per
character, reviewed by Director.

Note: Story 023 defers formal `PerformanceDirection` artifacts pending proof of
need from downstream consumers. Character bibles plus interactive character chat
may cover this concern group adequately. If structured artifacts are needed:

- emotional state entering the scene
- arc through the scene
- motivation
- subtext
- physical notes: posture, energy level, gestures, habits
- key beats: moments of change, realization, decision
- relationship dynamics: how the character relates to others present
- dialogue-delivery notes
- blocking notes: positions and movement

### spec:4.10.6 — Story World

The persistent world: everything that must remain coherent across the entire
project. This is CineForge's primary differentiator; no current AI tool
adequately addresses cross-scene continuity.

- character visual-design baselines
- location design baselines
- prop design baselines
- continuity tracking: costume state, injury state, prop state, location state
  across scenes
- character behavioral consistency
- narrative rhythm across acts
- visual motif tracking
- audio motif tracking

### spec:4.10.7 — Prompt Compilation Model

Prompts sent to generation models are **read-only compiled artifacts**: viewable
for transparency but not directly editable. The prompt is a projection of
upstream concern-group artifacts, like compiled output. Changes go upstream, via
chat or direct artifact edit, and the prompt recompiles automatically.

- The prompt is a window, not a door.
- Users can view the exact prompt that produced any generated output.
- "Chat about this" affordance: highlight any part of the displayed prompt and
  chat with the appropriate AI role.
- Prompt versions are tracked. Upstream changes trigger recompilation and new
  versions.
- Model-upgrade resilience: prompts are compiled so the compilation layer can
  adapt to new models without touching user-facing artifacts.

### Constraints

**C5: Capability Gating** [AI capability -> deletion]
*Ideal:* All AI is universally multimodal. Every role can perceive and reason
about text, images, video, and audio natively.
*Compromise:* Roles declare modality limits and must not pretend to perceive
media they cannot truly understand.
*Detection:* Run `compromise-C5-role-modality`. Pass when one SOTA model reliably
reasons across text, image, video, and audio in a single call with high-quality
results.
*Resolves:* Delete role perception-capability declarations and modality-routing
logic. All roles become universally capable.

## spec:5 — Operator Console & Interactive UX

> **Product need:** Users need a flexible, transparent control surface for moving
> through analysis and creative work without feeling like they are operating a
> pipeline dashboard.
> **Tech substrate:** User-control modes, explanation surfaces, stage-progression
> rules, human interaction workflows, and readiness signals that keep the UI
> honest.

### spec:5.1 — Human Control Is Optional and Configurable

- The pipeline may run:
  - fully autonomously
  - with human checkpoints
  - fully manually with AI as advisor
- Humans participate through three modes: approve/reject proposals, collaborative
  creative sessions with agents, and direct artifact editing. All produce new
  artifact versions, never in-place mutations.

### spec:5.2 — Explanation Is Mandatory

- Any AI role proposing a decision must explain:
  - what is proposed
  - why
  - tradeoffs
  - confidence
- Teaching and pedagogy are first-class features.

### spec:5.3 — Stage Progression (User-Controlled)

The pipeline is not rigidly sequential. Users choose how to move through it:

- **Breadth-first** ("traditional film"): advance all scenes through each stage
  before moving to the next.
- **Depth-first** ("sizzle reel"): take a single scene, or a handful, all the way
  through every stage to final output.
- **Hybrid**: any combination.

The system does not enforce an ordering. Stage transitions are user- or
Director-initiated, not automatic. In autonomous mode, the Director follows the
user's chosen strategy.

Completion criteria per stage are role-defined: Canon Guardians must sign off, or
be overridden by the Director, before a scene's artifacts at that stage are
considered ready. In checkpoint mode, the user must also approve.

### spec:5.4 — Human Interaction Model

The human is the ultimate authority in the system: above even the Director AI.
The spec must define not just that humans can participate, but how.

**Creative Sessions (Collaborative Chat):**

- `@agent` addressing: the human directs remarks to specific roles.
- Auto-inclusion: when the conversation touches another role's domain, that role
  is automatically brought in.
- Selective silence: agents only speak when relevant, directly addressed, or
  within their authority.
- Wandering scope is expected.
- Artifact proposals: actionable conclusions become suggestion-system artifacts.
- All transcripts are recorded as immutable artifacts.

**Direct Artifact Editing:**

- Immutability preserved: a direct edit creates a new artifact version.
- Immediately canon: the human's edit takes effect without AI approval.
- Agent commentary may be attached as suggestions but cannot block a human edit.

The three modes of human participation:
- approve / reject
- collaborate
- direct edit

All three are recorded. All three produce new artifact versions, never in-place
mutations. The human may use any combination at any time regardless of the
project's operating mode.

### spec:5.5 — Readiness Indicators

Red/yellow/green per concern group per scene:
- Red: no user input. AI guesses everything using project-wide defaults.
- Yellow: some guidance (mood propagated, or partial specification). AI fills
  gaps.
- Green: user reviewed and approved all key elements for this group.

Summary dashboard: for each scene, five concern-group indicators showing exactly
where attention is needed.

## spec:6 — Shot Planning & Visualization

> **Product need:** CineForge must turn creative intent into concrete visual
> planning artifacts that are usable both for AI generation and real-world
> production.
> **Tech substrate:** Coverage strategy, shot definitions, storyboard/animatic
> artifacts, and optional keyframes that stay linked to upstream direction.

### spec:6.1 — Shot Planning (Required)

Shot planning is where all upstream creative decisions come together into
concrete, shot-by-shot instructions. It translates "what happens in this scene"
into "what the audience sees and hears." The output mirrors a real-world shot
list but is richer: every shot records the reasoning behind each choice and the
upstream artifacts that informed it.

### spec:6.1.1 — Scene Coverage Strategy

Before individual shots are defined, the system produces a coverage strategy for
each scene:
- coverage approach
- editorial intent
- visual intent
- sound intent
- performance notes
- coverage adequacy check

### spec:6.1.2 — Individual Shot Definition

Each shot in the plan includes:

**Framing and Camera**
- shot size
- camera angle
- camera movement
- lens / focal length

**Content**
- scene reference and shot ID
- characters in frame (and POV, if applicable)
- blocking
- action / description
- dialogue
- duration estimate

**Editorial and Coverage**
- coverage role
- edit intent

**Continuity and References**
- asset state snapshots consumed
- references to upstream artifacts

**Audit**
- standard CineForge metadata: intent, rationale, alternatives considered,
  confidence, source

### spec:6.1.3 — Coverage Patterns (Reference)

Standard coverage patterns the system should understand:
- master
- singles / close-ups
- over-the-shoulder
- two-shot
- reaction shots
- inserts / cutaways

The Editorial Architect is responsible for verifying that planned coverage is
sufficient to assemble the scene in editing.

### spec:6.1.4 — Export Compatibility

Shot-plan artifacts contain all fields present in an industry-standard shot list.
The system should be capable of exporting shot plans in formats usable by real
film crews. Export formatting is a presentation concern, not a pipeline stage.

### spec:6.2 — Storyboards (Optional)

Storyboards are derived from the shot plan. Each storyboard frame corresponds to
one or more shots.

### spec:6.2.1 — Purpose

- cheap visualization
- blocking
- eyelines
- camera intent

### spec:6.2.2 — Styles

- sketch
- clean line
- animation-style
- abstract color-coded
- photoreal (discouraged, gated)

### spec:6.3 — Animatics / Previz Video (Optional, Selective)

### spec:6.3.1 — Granularity

- per project
- per act
- per scene
- per shot

### spec:6.3.2 — Characteristics

- low detail
- accurate timing
- accurate camera motion
- symbolic characters and sets

### spec:6.3.3 — Previz Reel

- mixed storyboard + animatic timeline
- temp dialogue and sound
- used for review and education

### spec:6.3.4 — Serendipity Preservation

- previs never mandatory
- director policy controls rigidity
- divergence from previs explicitly allowed

### spec:6.3.5 — Product Truth

- When CineForge offers operator-facing previz video, the target is low-fidelity
  AI-generated motion suitable for camera, blocking, pacing, and staging review.
- Deterministic storyboard/animatic assemblies are valid baseline, fallback, and
  control artifacts, but they do not satisfy the previz-video requirement by
  themselves.
- If current model/runtime limits keep AI previz slow, CineForge must say so
  explicitly rather than presenting deterministic placeholder output as if the
  previz problem were solved.

### spec:6.4 — Keyframes (Optional)

- start / mid / end frames
- lockable by director
- used to constrain video generators
- derived from storyboards or animatics

## spec:7 — Generation & Export

> **Product need:** CineForge must compile planning artifacts into model-ready
> generation requests while preserving user assets and export viability.
> **Tech substrate:** Render-adapter prompt compilation, engine-pack knowledge,
> error handling, and origin-agnostic asset injection.

### spec:7.1 — Render Adapter Layer (Required for Generation)

The Render Adapter is a stateless module, not a creative role. It has no
opinions, no hierarchy position, and no review gates. It is a prompt compiler
that translates film artifacts into model-ready generation prompts.

### spec:7.1.1 — Two-Part Prompt Architecture

- Part 1 — Generic meta-prompt: expert at producing rich AI video-generation
  prompts from film artifacts
- Part 2 — Model-specific engine pack: adapts the prompt to a specific AI video
  model's strengths, limits, preferred language, and supported inputs
- Synthesis: a single AI call combines both parts with the actual creative inputs
  into one cohesive, model-optimized prompt
- The synthesized prompt is then sent to the target model API along with any
  supported inputs

### spec:7.1.2 — Engine Packs

- per-generator tuning profiles
- known strengths, limits, failure modes
- supported inputs
- preferred prompt language and structure
- retry and mitigation strategies

### spec:7.1.3 — Error Handling

- The Render Adapter reports errors when a request exceeds model capabilities.
- Errors bubble up to the pipeline; the adapter does not negotiate or make
  creative decisions.
- It cannot change creative intent.

### spec:7.2 — User Asset Injection (Required)

> **ADR-003 / R17.** Real-world asset support is a core design principle. The
> system must be origin-agnostic: uploaded and AI-generated assets are treated
> identically throughout the pipeline.

Users may inject assets at any stage:
- actor photos / headshots
- location photos / scout footage
- prop references
- dialogue audio / voice recordings
- style references / mood board images
- any other creative material with user-specified purpose

Injected assets may be:
- soft-locked
- hard-locked

AI may propose relaxing locks but may not override without approval.

Injected assets slot into the same reference-image / audio / document paths as
AI-generated assets. No part of the pipeline should distinguish between uploaded
and AI-generated assets.

### Constraints

**C6: Render Adapter Engine Packs** [Ecosystem / infrastructure -> deletion]
*Ideal:* One universal video-generation API accepts rich film artifacts and
produces high-quality, consistent video.
*Compromise:* Keep model-specific engine packs and synthesis logic because APIs,
prompt formats, supported inputs, and duration limits remain fragmented.
*Detection:* Monitor for a dominant video-generation API standard, or a single
model that handles all required input types through a clean stable API.
*Resolves:* Delete engine-pack profiles, model-specific prompt synthesis, and
per-model capability UI. Simplify the Render Adapter to a single-target client.
*Preferences:* Engine-pack selection UI, per-model capability display, model
comparison view.

## spec:8 — AI Platform, Evaluation & Model Strategy

> **Product need:** CineForge must expose AI cost, quality, and model-selection
> tradeoffs honestly enough that operators can trust what the system is doing.
> **Tech substrate:** Cost tracking, QA patterns, eval discipline, and model-slot
> selection logic.

### spec:8.1 — Cost Transparency

- Every AI call's cost is tracked and surfaced.
- Per-stage and per-run cost summaries are available.
- The system supports cost-quality tradeoffs: cheaper models for initial passes,
  stronger models for refinement.
- Budget caps may be configured per-project or per-run to prevent runaway costs.
- Cost data is recorded in run artifacts for auditability.

### spec:8.2 — Quality Validation (QA)

Quality validation remains an explicit part of the system surface.

... (existing content) ...

artifact's audit metadata.

### spec:8.3 — Subsumption-Based Model Strategy

The pipeline supports a tiered model-assignment strategy to balance cost, speed,
and intelligence.

Model tiers (slots):
- `work`: the primary model for task execution
- `verify`: the model responsible for QA / validation passes
- `escalate`: a high-intelligence model used only when the work model fails
  verification

Precedence hierarchy (subsumption):
1. Module override
2. Recipe params
3. Project global

Namespacing:
The strategy supports namespaces (for example `text.work`, `video.work`) to
allow specialized models for different media types while maintaining a fallback
to generic slots.

Resilient work pattern:
Modules should attempt work with the `work` slot, validate with `verify`, and
automatically retry using the `escalate` slot if validation fails.

### Constraints

**C1: Cost Transparency** [Ecosystem / infrastructure -> partial deletion]
*Ideal:* AI inference is effectively free. No per-call cost tracking is needed.
*Compromise:* Track per-call and per-run cost because inference remains a
material, variable input to product behavior and operator trust.
*Detection:* Monitor inference pricing. Pass when cost drops below
`$0.001 / 1M tokens` across the providers CineForge actively uses.
*Resolves:* Delete per-call cost tracking, budget-cap enforcement, and
cost-quality tiering UI. Keep only lightweight aggregate reporting if it still
has business value.
*Preferences:* Cost-per-call display, budget-cap thresholds, cost-quality tier
selector.

**C2: Dedicated QA Validation Passes** [AI capability -> partial deletion]
*Ideal:* AI output is reliably correct. No separate verification step is needed.
*Compromise:* Keep dedicated QA / validation passes because first-attempt output
is still unreliable.
*Detection:* Run `compromise-C2-qa-validation`. Pass when `10` diverse extraction
tasks succeed on the first attempt with structural and semantic checks and no QA
retry.
*Resolves:* Delete dedicated QA stages, the `verify` model slot, and QA-specific
schemas. Keep only lightweight structural assertions.

**C3: Tiered Model Strategy** [AI capability + ecosystem -> deletion]
*Ideal:* One model does everything well enough that per-stage model strategy is
unnecessary.
*Compromise:* Keep work/verify/escalate slots, namespace routing, and per-stage
selection because no single model wins across CineForge's surface at acceptable
cost and latency.
*Detection:* Run `compromise-C3-tiered-models`. Pass when a single model meets
all current quality targets that drive CineForge defaults at acceptable
latency/cost.
*Resolves:* Delete tiered model selection infrastructure and replace it with one
project-level model config.
*Preferences:* Model selection UI, per-stage override controls, cost profiles.

## spec:9 — Memory & Collaboration

> **Product need:** CineForge must remember enough context, decisions, and
> conversations to support long-running collaboration without losing provenance.
> **Tech substrate:** Canonical artifacts, working-memory caches, transcript
> retention, and explicit operating modes.

### spec:9.1 — Canonical Memory

- artifacts (immutable, versioned)
- policies (project configuration, control mode)
- decisions (explicit decision artifacts with audit metadata)
- suggestions (full backlog with lifecycle status)
- conversation transcripts (raw turn-by-turn records)

### spec:9.2 — Working Memory (Cached)

- Long-running chats allowed only for:
  - Director
  - Script Supervisor (optional)
- Periodically summarized into artifacts.
- Resettable.
- Raw transcripts are always retained even when working memory is summarized or
  reset.

### spec:9.3 — Memory Rule

Chats are accelerators. Artifacts are truth. Transcripts are permanent.

**Additional compromise element:** The distinction in `spec:9.3` is itself an
AI-capability compromise. With persistent, reliable memory, chats can become
truth alongside artifacts.

### spec:9.4 — Valid Operating Modes

- Full autonomy
- Human checkpoints
- Advisory only
- No previs
- Education / coaching mode
- AI generation
- IRL production

All modes use the same pipeline.

### Constraints

**C7: Working Memory Distinction** [AI capability -> deletion]
*Ideal:* AI has unlimited, persistent memory. There is no distinction between
"working" and "canonical" memory.
*Compromise:* Keep working-memory summaries and limits because context windows are
finite and expensive.
*Detection:* Run `compromise-C7-working-memory`. Pass when context windows exceed
`10M` tokens at negligible cost, or when AI models natively support persistent
cross-session memory.
*Resolves:* Delete summarization triggers, compaction logic, memory budgets, and
the working-memory distinction itself.
*Preferences:* Conversation summarization controls, memory-budget indicator,
"context limit approaching" warning.

## spec:10 — Timeline & Playable Assembly

> **Product need:** Users should be able to evaluate structure, pacing, and the
> best available representation of the film throughout the pipeline.
> **Tech substrate:** Independent timeline artifacts, stacked tracks, and
> always-playable fallback rules.

### spec:10.1 — Timeline Artifact

A `timeline_vN` artifact exists independently of final video.

It supports:
- scene order (edit order)
- story order (chronology)
- shot subdivision
- stacked tracks

### spec:10.2 — Tracks (Non-Exhaustive)

- Script
- Dialogue / Audio
- Shots
- Storyboards
- Animatics
- Keyframes
- Generated Video
- Continuity Events
- Music / SFX

### spec:10.3 — Always-Playable Rule

- The timeline must be scrubbable at all times.
- The system displays the best available representation:
  - storyboard if no video
  - animatic if present
  - final render if present

## spec:11 — Planning Infrastructure & Agent Tooling

> **Product need:** While current AI cannot yet build CineForge from the ideal in
> one shot, the repo needs explicit planning artifacts that make work sequence,
> validation, and handoff coherent.
> **Tech substrate:** Story files, methodology state, generated dashboards, triage skills,
> workflow gates, AGENTS instructions, runbooks, and verbose work logs.

### spec:11.1 — Story Lifecycle and Handoff Chain

Stories are tracked implementation artifacts with an honest core progression:
- Draft
- Pending
- In Progress
- Blocked
- Done

Those states mean:
- `Draft` — worth preserving, but still incomplete, underspecified, or not yet
  substrate-verified enough to claim build-readiness
- `Pending` — fully fleshed out and honestly buildable now
- `In Progress` — currently being built
- `Blocked` — concrete enough to preserve, but cannot honestly proceed now
  because of a named blocker with explicit evidence and an unblock condition
- `Done` — built, validated, and formally closed

`Deferred` and `Cancelled` remain valid parking/archive states, but they sit
outside the normal build progression above.

The lifecycle chain is:
- `/create-story` chooses `Draft`, `Pending`, or `Blocked` based on repo reality
- `/build-story` owns implementation and may promote a buildable `Draft` or
  mark a real blocker instead of dead-ending on status paperwork
- `/validate` owns validation
- `/mark-story-done` owns closure and should only split remaining work when it
  is genuinely separate

Work should stay in one story while it remains in the same subsystem, the same
validation boundary, and the same success surface. Split or rescope only when
the remaining work becomes materially distinct, crosses a new runtime or
ownership seam, or would make validation unclear.

Blocked-story truth must live in the canonical story artifact via blocker
summary, blocker evidence, and unblock condition fields. If compiled planning
surfaces consume story truth, they must surface that blocked metadata too.

Workflow gates exist because current AI still benefits from explicit handoff
boundaries and evidence review before closing work.

### spec:11.2 — Methodology State, Generated Dashboards, and Triage

`docs/methodology/state.yaml` is the canonical planning-state substrate.
`docs/build-map.md` and `docs/stories.md` are generated dashboard views.

Together they must make these visible:
- product need
- tech need
- substrate status
- phase (`climb`, `hold`, `converge`, `unplanned`)
- story coverage
- compromise progress

`/triage`, `/triage-stories`, `/triage-evals`, `/triage-architecture`, and
related runbooks consume that state/dashboard layer to decide what should
happen next.

Triage is problem-first, not backlog-first. It should rank:
- movement toward the Ideal
- real problem pressure
- leverage and unblock power
- readiness
- cost
- continuity / momentum

Story existence is packaging context and a tie-breaker, not a primary value
signal by itself.

### spec:11.3 — Verification, Eval Classification, and Registry Discipline

Definition-of-done discipline is part of the execution substrate:
- relevant tests pass
- artifacts are manually inspected
- schema validation passes
- work log is updated
- significant eval mismatches are classified as `model-wrong`,
  `golden-wrong`, or `ambiguous`
- `docs/evals/registry.yaml` stays fresh whenever scored evaluation runs

These are execution constraints, not product ideals. They exist because current
AI is not yet reliable enough to self-verify safely without explicit evidence.

### spec:11.4 — Agent Instructions, Skills, and Runbooks

`AGENTS.md`, skill definitions, and runbooks are part of the repo's execution
surface. They encode conventions, workflow ownership, and recurring process
knowledge so future AI sessions do not have to rediscover them from scratch.

Verbose work logs are required for the same reason: another agent should be able
to pick up a partially completed story safely from the recorded evidence.

### Constraints

| ID | Process Element | Limitation | Residual | Detection | Resolves |
|---|---|---|---|---|---|
| B1 | Story files and tracked checklists | AI cannot yet hold large delivery state coherently across sessions | AI -> deletion | Reliable long-horizon planning and execution continuity without explicit task slicing | Story files collapse into optional provenance rather than managed build inputs |
| B2 | Methodology state and substrate tracking | AI cannot reliably infer architectural readiness from repo state alone during triage | AI -> deletion | Reliable codebase architectural reasoning at triage time | Explicit methodology state becomes optional internal provenance or disappears |
| B3 | Triage skills and routing runbooks | AI still benefits from explicit "what next?" orchestration | AI -> deletion | Reliable autonomous prioritization from repo state without scaffolding | `/triage*` skill scaffolding and companion runbooks disappear |
| B4 | Workflow gates and story-closure chain | Humans still want optional review, and AI is not yet trustworthy enough to close work autonomously by default | Human -> preference | Human trust is high enough that review collapses to the operator's preferred involvement level | `/validate` and `/mark-story-done` shrink to optional review rather than mandatory gates |
| B5 | `AGENTS.md`, skills, and runbooks | AI cannot yet infer project conventions and workflow rules from code plus docs alone | AI -> deletion | Reliable convention inference from the repository state itself | Session instructions and procedural runbooks shrink to lightweight provenance or disappear |

## Explicit Non-Goals

- Replacing human creativity
- Forcing rigid planning
- Guaranteeing aesthetic success
- Eliminating serendipity

## Summary

This system is:
- a film reasoning engine
- a production compiler
- a teaching director
- a generator adapter
- a preproduction backbone

AI generation is optional.
Understanding, structure, and auditability are not.

## Untriaged Ideas

Raw ideas from `docs/inbox.md` and design sessions that relate to the spec but
have not yet been incorporated into an owning category or explicitly discarded.
Work through these as the spec evolves.

### From `docs/inbox.md` (2026-02-26)

- **Voice specification for characters**: users should be able to specify
  character voices: tone, accent, age, reference clips. Feeds into video/audio
  generation. Needs detail under `spec:4.8` or `spec:4.10`.

- **Scene-level vs shot-level video generation**: multi-shot generation is
  shifting the atomic unit from shot toward scene. Affects `spec:6` and
  `spec:7`.

- ~~**Prompt transparency / direct prompt editing**~~: **Resolved by ADR-003
  Decision #4.** Prompts are read-only compiled artifacts. See `spec:4.10.7`.

- **"AI-filled" / skip-ahead state with visible marking**: when users generate
  without completing upstream, AI fills gaps. Each AI-guessed element needs
  visible labeling and quality-degradation indicators. Captured in Ideal R11 but
  needs detail under `spec:5.5`.

- **AI preference learning from user choices**: record every AI suggestion plus
  the user's final choice as training data for better future suggestions.
  Captured in Ideal R13 but needs a spec section under `spec:9`.

- **Ghost-text inline suggestions**: faded AI suggestions inline with user
  content. Good candidate for `spec:5`.

- **Onboarding flow**: "I'm a [Screenwriter/Director/Producer/Explorer]" single
  question, skippable, defaults to Explorer. Affects `spec:5`.

- **Explorer demo project**: pre-populated tutorial project so new users can
  explore capabilities immediately without uploading their own content.

- **Per-feature AI autonomy levels**: more granular than the current three-mode
  control model. Extends `spec:5.1` and `spec:9.4`.

- **Quality estimates in preflight**: "★★★☆☆ estimated quality" based on what
  upstream is complete vs missing. Extends the readiness model in `spec:5.5`.

- **Narrative-aware timeline export**: when exporting to NLE formats, embed scene
  boundaries, beat changes, character entrances, emotional tone shifts, markers,
  color-coded regions, and clip notes. Captured in Ideal R9 but needs detail
  under `spec:10`.

- **Video preview / assembly view**: simple player with scene strip, drag to
  reorder, click to play, basic trim. Not a full NLE. Captured in Ideal R10 and
  belongs under `spec:10`.

---

End of Specification
