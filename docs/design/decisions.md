# CineForge UI Design Decisions

Living document capturing reviewed and approved design decisions. These drive implementation.

**Status**: Active — updated through Story 011e (UX Golden Path).

---

## Source of Truth Hierarchy

The script is the **source of truth** for names, structure, and dialogue. Derived artifacts (character bibles, scene breakdowns, location details) flow FROM the script. Derived artifacts can be *enriched* (add backstory, motivations, arc notes) but cannot rename or restructure upstream. Renaming a character means editing the script, which propagates downstream.

If a derived artifact is edited and then the script is re-processed, conflicts surface in the **inbox** for user resolution — never silently overwritten.

---

## Mental Model

### Story-centric, not pipeline-centric
The UI is organized around the user's *story* — scenes, characters, locations, shots — not around pipeline stages or module names. The pipeline is invisible plumbing. Users should feel like they're working with their screenplay, not watching a DAG execute.

### The screenplay is always the home page
The screenplay is the center of gravity for every project state. It is never replaced by a dashboard, stats view, or admin panel. At every stage of development — freshly imported, being processed, fully analyzed — the screenplay remains the primary content on the home page.

This is the foundational design decision. The user imported a screenplay because they care about their story. The moment we replace it with a grid of numbers, we've told them "the system matters more than your story."

Everything else — scenes detected, artifacts produced, run history, artifact health — is secondary information accessible via the chat panel, nav pages, or the inspector. None of it displaces the script.

### Scene strips / index cards
Scenes are the universal structural unit. Scene strips or index cards are the primary navigation and organization metaphor. They appear in the chat panel as materialized results and on dedicated Scenes pages, but do not replace the screenplay on the home page.

### Artifacts as first-class objects
Everything the system produces is a browsable, inspectable artifact with version history, provenance, health status, and type-appropriate rendering.

---

## Primary Workflow

### MVP intake: screenplay only
The primary workflow is importing a finished screenplay. Story-to-screenplay conversion is out of scope for MVP (captured in `docs/ideas.md`).

### Intake flow
Drag-and-drop script file → AI parses and extracts → review draft → confirm. Under 60 seconds of user attention for the happy path.

### The golden path (implemented)
1. Upload screenplay on New Project page
2. LLM extracts the title, generates a clean slug (e.g., `the-mariner`)
3. User confirms name → lands on the screenplay, beautifully rendered in CodeMirror
4. Chat panel suggests "Ready to bring your story to life?" with one-click Start Analysis
5. Click → processing begins. **The screenplay stays visible.** Progress appears in the chat panel.
6. Stage-by-stage updates: "Converting to standard format..." → "Finding scene boundaries..." → "Working on project config..."
7. On completion: "Analysis complete! I found 17 artifacts." with [View Results] and [Run Details] buttons
8. User clicks through at their own pace. System suggests next steps. No dead ends.

### Processing stays on the screenplay
Clicking "Start Analysis" does NOT navigate away. The screenplay remains visible while the chat panel shows real-time progress. A subtle processing banner appears at the top. Power users can click "View Run Details" to see the pipeline stage view, but this is never forced.

### Progressive depth with user control
Analysis recipes (extraction of scenes, characters, locations) fire automatically or with one click. Creative recipes (character bibles, world-building, visual style) are suggested via the chat panel after extraction completes. The user decides how far to go — different personas exit at different depths. No recipe names are ever shown to the user.

### Analysis vs creative: the clean line
Anything that extracts what's already in the script runs automatically — the app is useless without it. Anything that adds something new requiring creative judgment pauses and suggests.

**Automatic (analysis):** Scene boundaries, character identification, prop detection, location identification, relationship mapping, dialogue attribution, format/structure analysis.

**Pause and suggest (creative):** Character backstories/bibles, visual style, tone/mood, shot planning, storyboard generation, music/sound, casting suggestions.

The line: **extracting = automatic. Creating = suggest first.**

---

## Project Identity

### Slug-based naming
Projects are identified by human-readable slugs derived from the screenplay content (e.g., `the-mariner`), not SHA-256 hashes. On screenplay upload, a fast LLM call (Haiku) extracts the title and generates a URL-friendly slug. The slug becomes the folder name (`output/the-mariner/`), URL path (`/the-mariner/runs`), and internal project ID.

### LLM-powered title extraction
The system reads the first ~2000 characters of the screenplay and extracts the title via LLM. This produces clean, meaningful names without requiring the user to type anything. Fallback: filename-based slug if LLM fails.

### Collision handling
If a slug already exists (e.g., uploading a second screenplay called "The Mariner"), the system appends `-2`, `-3`, etc. Uniqueness is enforced by scanning the output directory.

### Display name is editable
The display name (shown in the header, breadcrumbs, and landing page) is editable inline — click the project title to rename it. The slug/folder name does not change after creation.

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

## Chat Panel — Primary Control Surface

The chat panel is the primary way users interact with the app. It is not a secondary "copilot" or hint banner — it is the main interaction surface.

### Architecture
Suggestions are AI messages with action buttons. User clicks are logged as user messages. The full history is the project journal. Scroll back to see every decision, every approval, every override — lineage tracking made human-readable.

### Message types
- **AI status**: Progress updates during processing ("Converting to standard screenplay format...")
- **AI suggestion**: Rich messages with context + action buttons ("Analysis complete! [View Results] [Go Deeper]")
- **User action**: Logged when user clicks a button ("Start Analysis ✓")
- **User override**: Logged when user edits an artifact (future)

### Three personas, one interface
- **Autopilot users** click through suggestions: yes, yes, yes
- **Learning users** read the detail in each message
- **Directing users** click "configure" or "choose" options

Same messages, three personas served.

### Chat history IS the project journal
Every project action is a message. The chat panel doubles as a complete audit trail of decisions. This is intentional — no separate "activity log" or "history" page needed.

### Inbox is a filtered view of chat
The inbox shows only chat messages that need user action (stale artifacts, pending approvals, AI questions, errors). Resolving an inbox item updates the corresponding chat message. One source of truth (the chat), inbox is just a lens on it.

### Future: conversational AI (Story 011f)
Enable the text input so users can ask questions, discuss story ideas, and request actions. The chat architecture is already in place — just add an LLM behind the input field with tool use for project operations.

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
- **Navigator** (left): Project-level navigation. Story-centric items (Home, Runs, Artifacts, Inbox). Eventually: Script, Scenes, Characters, Locations, World.
- **Content Canvas** (center): Primary working area — the screenplay is always the home view. Other pages (Runs, Artifacts) use the same canvas.
- **Right Panel** (right): Tabbed — **Chat** (primary interaction surface, always default) and **Inspector** (metadata, provenance, version history when viewing artifacts). Chat is the default tab; Inspector activates contextually.

### Current navigation (implemented)
Primary: **Home** (screenplay), **Runs**, **Artifacts**, **Inbox**

"Pipeline" was removed from primary nav — a pipeline is just a run detail, accessible from the Runs page or chat links. The word "pipeline" is never shown to the Storyteller persona.

### Target navigation (Phase 4)
Primary: **Script**, **Scenes**, **Characters**, **Locations**, **World**, **Inbox**
Advanced (collapsed): Runs, raw Artifacts

Nav items that have no content yet are grayed with hint text or hidden until artifacts exist.

### Props are contextual, not a nav item
Props exist at the intersection of characters, locations, and scenes. A sidearm shows up on the character's page. A macguffin appears everywhere it's relevant. "All props" is a filtered view, not a primary nav concern.

### Slide-over detail pattern
Drilling into an artifact opens a slide-over panel rather than a full page navigation. Maintains context of where you came from.

### Keyboard-first navigation
Support keyboard shortcuts for common actions (⌘B toggle sidebar, ⌘I toggle right panel, ⌘0-3 nav items, ⌘K command palette). Power users should be able to move through the review queue, approve/reject, navigate scenes, and switch views without touching the mouse.

---

## Pipeline and Processing

### Hidden by default
The pipeline DAG is not shown to users. Instead, the UI presents artifacts as things that "exist or don't yet." The word "pipeline" never appears in the primary UI.

### Progress via chat, not a separate page
When processing runs, progress appears as messages in the chat panel: "Converting to standard format...", "Finding scene boundaries...", "Scenes identified." The user stays on the screenplay page. A "View Run Details" link is available for power users who want the stage-by-stage breakdown with costs and durations.

### Run detail page for power users
The Runs page and Run Detail view provide full pipeline visibility: stage status, duration, cost per stage, model used, artifacts produced, event log. This is the "Advanced" view — accessible but never the default experience.

### Live-updating run details
Run duration ticks live (updates every second while running). Event log polls for new entries. Stage statuses update via polling (every 2 seconds). When the run completes, polling stops automatically.

### Progressive materialization (skeleton UI)
While the pipeline runs, show skeleton placeholders that fill in with real content as artifacts are produced. The UI comes alive incrementally rather than appearing all at once. (Phase 3 — not yet implemented.)

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

1. **Dashboard displacing the script**: Never replace the screenplay with a grid of stats, artifact counts, or run summaries. The screenplay is the home page. Stats are secondary.
2. **Navigating away during processing**: Never force the user to a pipeline/progress page when they click "Start Analysis." Stay on the screenplay; show progress in the chat.
3. **"Processing..." with no context**: Always show what's happening, what's been produced so far, and estimated progress — via chat messages, not a loading spinner.
4. **Modal approval workflows**: Don't block the entire UI for a single approval. Use the inbox pattern instead.
5. **Separate "AI settings" panels**: AI configuration should be contextual to what the user is looking at, not buried in a settings menu.
6. **Silent overwrites**: Never replace user work without explicit consent.
7. **Pipeline-centric navigation**: Never organize the UI around stage names (ingest, normalize, extract). Always use story concepts (scenes, characters, locations).
8. **Hash-based or system-generated identifiers in the UI**: Project names, URLs, and breadcrumbs should always be human-readable. Internal IDs stay internal.
9. **Dead-end screens**: Every screen must have an obvious next action. If the user has to wonder "what do I do now?", the UI has failed. The chat panel's suggested next action is the safety net.

---

## Scope Boundaries (MVP)

### In scope
- Screenplay import with LLM-powered title extraction and slug-based identity
- Screenplay-first home page for all project states
- Chat panel as primary interaction surface with state-driven suggestions
- One-click analysis with chat-driven progress (stay on screenplay)
- Artifact browsing and inspection with type-appropriate viewers
- AI review with variational presentation
- Inbox/review queue (filtered chat view)
- Run detail with live-updating duration and event log
- Override/edit with staleness tracking
- Dark cinematic theme (slate with sage/teal accents)
- Desktop-first, keyboard-friendly (⌘B, ⌘I, ⌘K, ⌘0-3)

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

1. ~~**Script format detection**~~: **Resolved.** Best effort with warnings in the inbox for issues encountered.
2. **Mobile/tablet**: Ideally works on mobile devices. How much effort to invest? *(Defer detailed mobile design to post-MVP but don't make choices that prevent it.)*
3. **Re-run blast radius**: When a user has done extensive manual editing and then regenerates something large upstream, the inbox-based staleness approach handles notification — but the UX of "merge" for complex artifacts needs design work. *(Defer detailed merge UX to implementation phase.)*
4. ~~**Chat panel width**~~: **Resolved.** 320px fixed width for the right panel (Chat + Inspector tabs). Screenplay gets center stage.
5. ~~**Chat vs inbox overlap**~~: **Resolved.** Inbox is a filtered view of chat. One source of truth.
6. ~~**Chat input field**~~: **Resolved.** Visible but disabled with "Chat coming in a future update..." placeholder. Signals conversational future without confusing users.
7. **Message density during fast operations**: Many things happen fast during extraction (13 scenes, 7 characters). Currently each stage transition gets its own message. May need batching if it gets noisy.
