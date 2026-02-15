# CineForge UI Design Decisions

Living document capturing reviewed and approved design decisions. These drive implementation.

**Status**: In progress — landscape and UI stack decisions captured.

---

## Source of Truth Hierarchy

The script is the **source of truth** for names, structure, and dialogue. Derived artifacts (character bibles, scene breakdowns, location details) flow FROM the script. Derived artifacts can be *enriched* (add backstory, motivations, arc notes) but cannot rename or restructure upstream. Renaming a character means editing the script, which propagates downstream.

If a derived artifact is edited and then the script is re-processed, conflicts surface in the **inbox** for user resolution — never silently overwritten.

---

## Mental Model

### Story-centric, not pipeline-centric
The UI is organized around the user's *story* — scenes, characters, locations, shots — not around pipeline stages or module names. The pipeline is invisible plumbing. Users should feel like they're working with their screenplay, not watching a DAG execute.

### Scene strips / index cards
Scenes are the universal structural unit. Scene strips or index cards are the primary navigation and organization metaphor.

### Artifacts as first-class objects
Everything the system produces is a browsable, inspectable artifact with version history, provenance, health status, and type-appropriate rendering.

---

## Primary Workflow

### MVP intake: screenplay only
The primary workflow is importing a finished screenplay. Story-to-screenplay conversion is out of scope for MVP (captured in `docs/ideas.md`).

### Intake flow
Drag-and-drop script file → AI parses and extracts → review draft → confirm. Under 60 seconds of user attention for the happy path.

---

## AI Interaction Patterns

### Implicit acceptance for objective extractions
Scene boundaries, character names, location identification — these are presented as done, editable in-place. No approval step required. The user fixes what's wrong and moves on.

### Variational presentation for subjective decisions
For creative/subjective outputs (character backstory, visual style, tone descriptions), present 2–4 variants. The user can:
1. **Choose one** and accept it (done).
2. **Select one or more** and click "generate more like this" (single click, new variants appear).
3. **Select one or more**, add comments on what they like/dislike, and regenerate with feedback.

This loops indefinitely until the user is satisfied. If generation is long-running, results land in the **inbox** for later review.

### Evidence and rationale
Every AI-generated value carries visible provenance (which model, which prompt, confidence level). Rationale is accessible on demand — not displayed by default, but always one click away. This builds trust.

### The preview IS the artifact
No separate "preview" vs "final" — what you see is what you get. Editing happens in-place on the real artifact. (ElevenLabs pattern.)

---

## Inbox / Review Queue

An inbox/task queue serves as the user's "what do I do next?" surface. Items that land in the inbox:
- AI needs user input (variant selection, low-confidence decisions)
- Downstream artifacts flagged stale after upstream changes
- Re-render notifications after edits
- Consistency issues detected
- Errors or warnings from pipeline stages
- Completed long-running generations ready for review

This is a known paradigm (email inbox, todo list) that helps users manage the complexity of a system with many moving parts.

---

## Staleness and Re-run

When something upstream changes (script edit, re-extraction, user override), downstream artifacts are flagged as **potentially stale** in the inbox. The user decides:
1. **Re-generate** (accepts that manual edits to that artifact will be lost)
2. **Keep manual version** (dismisses the staleness warning)
3. **Merge** (review what changed and integrate)

No silent overwrites. The existing immutable artifact versioning system supports this naturally.

### Inline stale indicators
Any stale artifact shows a visible icon wherever it appears in the UI (artifact lists, scene strips, inspector, etc.). Hover reveals why it's stale. Clicking the icon navigates to the relevant inbox item (or resolution action) so the user can deal with it immediately. This prevents users from accidentally working on stale artifacts without noticing.

---

## Visual Design

### Dark, warm, cinematic personality
Reference points: Arc Studio Pro, Frame.io, Linear. Professional creative tool aesthetic, not a developer dashboard or admin panel.

### Color-coding by artifact type
Consistent colors for each artifact type (scripts, scenes, characters, locations, props, etc.) across the entire UI. **Include icons alongside colors** for colorblind accessibility and faster visual scanning.

### User edits are visually distinct
Field-level marking distinguishes AI-generated values from user overrides. User input is highly preserved and visually prominent — losing user edits destroys trust instantly.

---

## Layout and Navigation

### Three-panel workspace
- **Navigator** (left): Project structure, scene list, artifact collections
- **Content Canvas** (center): Primary working area — artifact viewer, script reader, variant selector
- **Inspector** (right): Metadata, provenance, version history, properties of selected item

### Slide-over detail pattern
Drilling into an artifact opens a slide-over panel rather than a full page navigation. Maintains context of where you came from.

### Keyboard-first navigation
Support keyboard shortcuts for common actions. Power users should be able to move through the review queue, approve/reject, navigate scenes, and switch views without touching the mouse.

---

## Pipeline Visualization

### Hidden by default
The pipeline DAG is not shown to users. Instead, the UI presents artifacts as things that "exist or don't yet."

### Vertical phase list for progress
When a pipeline is running, show a simple vertical list of phases with completion status. Not a full DAG — just "what's done, what's running, what's next."

### Progressive materialization (skeleton UI)
While the pipeline runs, show skeleton placeholders that fill in with real content as artifacts are produced. The UI comes alive incrementally rather than appearing all at once.

### Provenance on the artifact, not in a separate diagram
Lineage information (what produced this, what it depends on) is a property of each artifact, accessible from the artifact inspector. No separate "lineage view" needed for MVP.

---

## Artifact Browsing

### Three levels of information density
1. **Summary**: Title, status badge, confidence indicator, one-line description
2. **Detail**: Full content in type-appropriate viewer, metadata, QA results
3. **Raw**: JSON, cost data, agent reasoning transcripts

### Type-appropriate viewers
- Screenplay text → proper screenplay format rendering
- Structured data (bibles, configs) → collapsible structured viewer
- Scene breakdowns → scene strip / index card view

### Filterable collections
Artifact lists can be filtered by type, health status, staleness, etc.

---

## Film-Specific Patterns

### StudioBinder color-coded element tagging
Adopt StudioBinder's approach to tagging script elements (characters, props, locations, wardrobe, etc.) with consistent colors. This is the gold standard for script breakdown visualization.

### Screenplay format rendering
Scripts must render in proper screenplay format (character names centered, dialogue indented, scene headings in caps). Never show screenplay as plain text or raw markdown.

### Contextual annotations (Frame.io pattern)
Allow annotations and comments attached to specific elements within an artifact — a specific line of dialogue, a specific character trait, a specific scene beat.

---

## Anti-Patterns to Avoid

1. **"Processing..." with no context**: Always show what's happening, what's been produced so far, and estimated progress.
2. **Modal approval workflows**: Don't block the entire UI for a single approval. Use the inbox pattern instead.
3. **Separate "AI settings" panels**: AI configuration should be contextual to what the user is looking at, not buried in a settings menu.
4. **Silent overwrites**: Never replace user work without explicit consent.
5. **Pipeline-centric navigation**: Never organize the UI around stage names (ingest, normalize, extract). Always use story concepts (scenes, characters, locations).

---

## Scope Boundaries (MVP)

### In scope
- Screenplay import (primary workflow)
- Artifact browsing and inspection with type-appropriate viewers
- AI review with variational presentation
- Inbox/review queue
- Pipeline progress (simple vertical list)
- Override/edit with staleness tracking
- Dark cinematic theme
- Desktop-first, keyboard-friendly

### Out of scope for MVP
- Story-to-screenplay conversion (see `docs/ideas.md`)
- Ghost-text inline suggestions (see `docs/ideas.md`)
- Collaborative review / multi-user
- Authentication
- Mobile-optimized layout (should work but not optimized)
- Full entity graph visualization (see `docs/ideas.md`)
- Timeline/track editing (Stories 012-013)

---

## UI Technology Stack

### Core stack
- **React 19** + **Vite** + **TypeScript**
- **shadcn/ui** (component library) with custom design tokens
- **Tailwind CSS** (styling)
- **Zustand** (state management)
- **TanStack Query** (server state / API caching)

### Specialized viewers
- **CodeMirror** — screenplay format rendering
- **ReactFlow** — entity/dependency graphs (if needed post-MVP)
- **Recharts** — statistics and cost visualizations

### Design system
A `DESIGN_SYSTEM.md` document defines all design tokens (colors, spacing, typography, artifact type colors/icons) as CSS variables + Tailwind config. This is the critical bridge between design intent and AI-generated code — keeps output consistent across sessions.

---

## Build Approach

### Fresh build, not migration
The existing Operator Console Lite (`ui/operator-console-lite/`) is a throwaway prototype. The new UI is built from scratch. The old UI is preserved as reference only — take specific patterns (URL layout, API client setup) if they provide clear value, but do not attempt to migrate or evolve the existing code.

### AI development workflow
1. **Primary build tool**: Claude Code + Chrome MCP (screenshot → inspect DOM → read console → iterate). This closes the visual feedback loop — no blind CSS tweaking.
2. **Component prototyping via v0.dev**: Use v0 to generate component variations using the same stack (React + shadcn/ui + Tailwind). The generated code is directly usable — copy it into the codebase and adapt to the real data model and app architecture. v0 components are standalone demos that need wiring up, but the markup, styling, and component composition transfer directly. Code is far better reference than screenshots.
3. **Visual identity bootstrap (AI-driven, human-steered)**: AI generates 3–4 theme variations based on the established design direction (dark, warm, cinematic). Cam reacts with gut feedback ("too cold", "more like this one", "warmer"). AI iterates. Once a direction is chosen, extract the color palette, typography, and spacing into `DESIGN_SYSTEM.md` as design tokens. Cam's job is taste and gut reaction, not design skill. This is the same variational pattern we're building into CineForge itself.
4. **Anti-pattern**: Do NOT let AI generate large amounts of UI code without visual verification. Every significant component must be screenshot-verified before moving on.

---

## Open Questions

1. **Script format detection**: Best effort with warnings in the inbox for issues encountered? *(Leaning yes.)*
2. **Mobile/tablet**: Ideally works on mobile devices. How much effort to invest? *(Defer detailed mobile design to post-MVP but don't make choices that prevent it.)*
3. **Re-run blast radius**: When a user has done extensive manual editing and then regenerates something large upstream, the inbox-based staleness approach handles notification — but the UX of "merge" for complex artifacts needs design work. *(Defer detailed merge UX to implementation phase.)*
