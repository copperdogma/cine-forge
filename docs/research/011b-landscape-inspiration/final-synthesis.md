---
type: synthesis-report
topic: 011b-landscape-inspiration
synthesis-model: claude-opus-4-6
source-reports:
- claude-opus-4-6-report.md
- gemini-report.md
- gpt-5-2-report.md
synthesized: '2026-02-15T04:25:16.119441+00:00'
---



---
canonical-model-name: "claude"
report-date: "2025-01-31"
research-topic: "011b-landscape-inspiration"
report-type: "synthesis"
---

# CineForge Operator Console: UX/UI Landscape Research — Final Synthesis

## 1. Executive Summary

- **Artifact-centric, not pipeline-centric, is the unanimous design principle.** All three reports converge on organizing the UI around what was produced (scenes, characters, locations, continuity reports), not how it was produced (DAG stages, module names). Dagster's asset-centric pivot is the most-cited analog. High confidence.
- **Three-panel workspace is the consensus layout:** persistent navigator (left), living content canvas (center), collapsible inspector (right)—mirroring Apple Pro apps, Figma, and Highland. All three reports independently arrive at this architecture.
- **The "drag in script → see results" flow must produce a visible, meaningful result within 10–15 seconds.** Skeleton UI with progressive materialization (not spinners) is the agreed-upon progress pattern. Partial results should unlock browsing immediately.
- **AI approval should be implicit (edit-in-place) for objective extractions and variational (2–4 options) for subjective interpretations.** Midjourney's grid-selection pattern adapted for character interpretations; GitHub Copilot's ghost-text pattern for inline suggestions. Never present a binary Accept/Reject gate on large artifacts.
- **Every AI-generated value must carry visible provenance**—a clickable link to the source script line(s) that produced it. This "Glass Box" principle builds trust and is the single most important factor in making AI feel safe vs. scary.
- **Field-level override with visual marking** ("human-edited" badge) is the correct granularity for user corrections. Overrides persist across re-runs. This is the "override anywhere, return to autopilot" principle made concrete.
- **Dark, warm, cinematic visual personality**—not developer-gray, not corporate-white, not toy-colorful. Arc Studio Pro's dark mode + Frame.io's content-centric layout + Linear's precision are the three reference points. Screenplay text must render in proper Courier formatting.
- **Top 3 anti-patterns:** (1) Exposing pipeline DAG as primary UI (Airflow), (2) AI overwrites without diff/rollback (early Jasper, Firefly), (3) Data-dense dashboards treating all fields as equally important (Jira defaults, ShotGrid tables).
- **Consistent color-coding by artifact type** (scenes, characters, locations) must persist across every view—cards, lists, stripboards, inspector, entity graph.
- **Keyboard-first navigation** (arrow keys to scan, Enter to open, Escape to close, shortcuts for view-switching) is critical for reviewing large artifact sets efficiently.
- **Version history should use visual snapshots + semantic diffs**, not raw text diffs. Show "what changed and why" (script edit triggered bible update), not just "lines added/removed."
- **Scene strips/index cards are the universal mental model** for story structure in film. CineForge's scene browser should default to a card/strip view, with list and stripboard as switchable alternatives.

---

## 2. Source Quality Review

| Criterion | Report 1 (Claude Opus 4) | Report 2 (Gemini) | Report 3 (GPT-5) |
|---|---|---|---|
| **Evidence Density** | 5 | 3 | 4 |
| **Practical Applicability** | 5 | 3 | 5 |
| **Specificity** | 5 | 3 | 4 |
| **Internal Consistency** | 5 | 4 | 5 |
| **Overall** | **5.0** | **3.25** | **4.5** |

**Report 1 (Claude Opus 4) — Critique:**
Exceptional. This is a remarkably specific, implementation-ready document. Every tool cited includes the *exact mechanism* (not just the tool name), with direct mapping to CineForge's needs. The five-phase "drag-in → results" interaction specification is production-ready design documentation. Color palette, typography, and keyboard shortcuts are specified. The anti-patterns section includes both the bad tool *and* the specific failure mode. The artifact browser specification reads like a PRD. This report should carry the heaviest weight in synthesis.

**Report 2 (Gemini) — Critique:**
Conceptually sound but significantly less specific than the other two. Introduces useful framing ("The Living Script," "Glass Box AI," "Trust Toggle") but often stays at the philosophical level rather than descending to mechanism. The Tesla/automotive metaphor for autopilot/manual is interesting but underdeveloped. Some claims are generic UX principles restated (the 80/20 rule, cognitive load theory) rather than specific tool analysis. The Kanban board suggestion for pipeline stages is questionable—it implies manual stage transitions, which contradicts the "AI does everything" model. Several tool analyses are thin (Frame.io comparison modes are mentioned but not deeply examined). The "Teenage Engineering" reference is novel but insufficiently justified for CineForge's context. Weakest of the three on actionable specifics.

**Report 3 (GPT-5) — Critique:**
Strong, practical, and well-structured. The "Artifact Review Queue" concept as the single most important interaction is a valuable contribution that the other reports approach but don't name as crisply. Good specificity on most tools (especially the Postman multi-view tabs adapted for artifacts, and the GitHub blame model for provenance). Slightly less detailed than Report 1 on visual design specifics and the upload-to-results flow, but compensates with a cleaner organizational structure and the "Feels good when / Feels scary when" framework for AI acceptance. The anti-patterns section is actionable. The "modal hell" anti-pattern is a useful addition not emphasized in the other reports.

---

## 3. Consolidated Findings by Topic

### 3.1 Creative Tool UX Patterns — Progressive Disclosure

**Proven / High Confidence:**

**Figma: Selection-drives-context inspector.** (All three reports) The right-hand panel shows controls relevant to the current selection; properties are collapsed by default with summary lines. CineForge adaptation: the Inspector panel shows metadata for whichever artifact is selected—scene detail when a scene is selected, character bible when a character is selected. Empty or minimal when nothing is selected. *(Source: R1 primary, R2 and R3 confirming)*

**Linear: Slide-over detail panel maintaining list context.** (All three reports) Clicking an item opens a ~60% viewport slide-over; the list remains visible; Escape returns to list. Keyboard navigation (arrow keys) enables rapid scanning. CineForge adaptation: this is the primary artifact inspection pattern—scene list remains visible while scene detail opens in slide-over. *(Source: R1 primary with specific viewport percentages, R3 confirming with keyboard emphasis)*

**Arc Studio Pro: Synchronized multi-view at different zoom levels.** (All three reports) Beat Board (10,000-foot), Outline (1,000-foot), Script (ground level) are three views of the same data. Selection in one view syncs to all others. Color-coding by storyline/character persists across views. CineForge adaptation: Project Overview (card grid), Scene List (scrollable list), Script View (full text) as three synchronized zoom levels. *(Source: R1 most detailed, R2 adds bi-directional sync specification, R3 confirms)*

**Highland 2: Inspector as "something you consult," not permanent chrome.** (R1, R3) Default state is the content; metadata is a toggled overlay. CineForge adaptation: artifact content is the primary view; analytical metadata (provenance, confidence, continuity warnings) lives in a toggleable Inspector panel (⌘I). *(Source: R1)*

**Notion: Toggle blocks + database views for structural disclosure.** (All three reports) Toggle blocks create in-page disclosure hierarchies. Database views (table, board, gallery, timeline) provide different lenses on the same data. CineForge adaptation: artifact detail pages use collapsible toggle sections; artifact collections support view switching (card grid, list/table, stripboard). *(Source: R1 most detailed, R2 adds "infinite nesting" concept, R3 confirms)*

### 3.2 AI Output Review and Approval

**Proven / High Confidence:**

**Variational presentation for subjective decisions (Midjourney grid pattern).** (All three reports) When the AI makes subjective interpretations (character personality, scene mood, relationship inference), present 2–4 options as a selection grid. User acts as curator, not binary approver. Reduces "take it or leave it" anxiety with "choose the best fit" abundance. *(Source: All three, R1 most detailed on when to use single vs. variational)*

**Implicit acceptance with inline editing for objective extractions.** (R1, R3) For factual extractions (scene headings, character names, location identification), present a single result with inline-edit capability. Acceptance is implicit—the user edits what's wrong and moves on. No explicit "Accept" button needed. *(Source: R1, with Runway's implicit approval model as reference)*

**The preview IS the artifact (ElevenLabs pattern).** (R1, R3) Don't show a description of what was generated—show the artifact itself in its natural format. Character bibles should read as documents, not JSON. Scene breakdowns should look like production notes, not data records. *(Source: R1)*

**Ghost-text suggestions for inline creative additions (Copilot pattern).** (R1, R2) Visually subordinate suggestions appear in context; Tab to accept, any other key to ignore. User's existing content remains visually dominant. *(Source: R1 detailed, R2 confirms with script-writing scenario)*

**Evidence + rationale builds trust (Grammarly model).** (R1, R3) Every AI decision should include a brief explanation: "Character identified as PROTAGONIST based on scene presence (14/14), dialogue proportion (38%), narrative agency." Provenance tooltips linking back to specific script lines are essential. *(Source: R1 for Grammarly model, R2 for "Glass Box" framing, R3 for "evidence is visible and local" principle)*

**What makes AI feel scary—consolidated anti-patterns:**
- Bulk generation disconnected from context (early Jasper): large text blocks in a separate output box, all-or-nothing decision *(R1)*
- Visual destruction of the original (Firefly Generative Fill): replacing the user's content before they've approved *(R1, R3)*
- Hidden confidence levels: presenting uncertain inferences as definitive facts *(R3)*
- No rollback/undo: any AI action that can't be reversed creates anxiety *(R1, R3)*

**CineForge AI Approval Model (synthesized):**
1. **Objective extractions** (scene boundaries, character names, locations): Single result, inline-editable, implicit acceptance
2. **Subjective interpretations** (character motivation, scene mood, relationship type): 2–4 variations with confidence indicators, user selects
3. **All values**: Field-level provenance (clickable link to source script lines), field-level override with visual "human-edited" badge
4. **Notion AI's Keep/Replace/Discard buttons** as the reference for the approval control pattern: generated content shown in context, explicit options, original preserved

### 3.3 Onboarding: "I Have a File, Transform It"

**Proven / High Confidence:**

**Five-phase intake flow (synthesized from all reports, R1 most detailed):**

| Phase | Duration | What the User Sees |
|---|---|---|
| 1. Drop Zone | 0s | Full-viewport target: "Drop your screenplay here" with supported format list. Amber highlight on drag-over. |
| 2. Ingestion | 0–5s | File thumbnail animates into a card; progress shimmer across top; "Reading your screenplay..." |
| 3. Instant Preview | 5–15s | "First Look" summary: title, page count, scene count, character count, location count, genre/tone tags. Script first page visible. Skeleton UI already showing the shape of the artifact workspace. |
| 4. User Decision | 15s | CTA: "Begin Full Analysis" (primary) + "Review details first" (secondary). This is the one moment of user agency before autopilot engages. |
| 5. Progressive Materialization | 15s–5min | Artifact tree fills in progressively. Skeleton cards → populated cards. Script gains clickable annotations. Completed artifacts unlock browsing while later stages run. |

**Key principle (Canva):** The first interaction post-upload is evaluating a result, not configuring a process. *(R1)*

**Key principle (Descript):** The transformation recontextualizes the file—the screenplay becomes a structured production asset with the original text still visible and unmodified. *(R1, R3)*

**Key principle (Google Docs import):** The import should feel lossless. "Your screenplay, exactly as you wrote it, but now enhanced with structural metadata." *(R1)*

### 3.4 Pipeline & Workflow Visualization

**Proven / High Confidence:**

**Dagster's asset-centric model is the correct mental model.** (All three reports) Reframe the pipeline not as "stages that run" but as "artifacts that exist (or don't yet)." Status indicators live on the artifacts themselves, not on a separate pipeline diagram. *(Source: All three, R1 and R2 most detailed)*

**Pipeline DAG should be hidden by default.** (All three reports) Never show a raw node graph as the primary UI. Technical stage names ("ingest_script," "extract_scenes_v2") are forbidden in the user-facing interface. Stages should have storyteller-friendly names: "Reading your script," "Identifying characters," "Mapping relationships," "Checking continuity." *(Source: R1 for specific naming recommendations, R2 and R3 confirming)*

**Vertical phase list as the pipeline progress indicator** (R1, R3) — like Vercel's build log or GitHub Actions step list. Auto-collapse completed stages (summary line); auto-expand running/failed stages. Self-summarizing: detail during execution, compressed summary after completion. *(Source: R1 for Vercel/Stripe hybrid pattern, R3 for GitHub Actions adaptation)*

**Skeleton UI with progressive fill for long-running tasks** (R1, R2, R3) — show the shape of results immediately, populate as data arrives. Dramatically better than spinners. Combine with chunked milestones ("42/42 scenes extracted") and early partial results (unlock scene browsing while character bibles still generate). *(Source: All three)*

**Provenance as a property of the artifact, not a separate diagram.** (R1, R3) Each artifact has a "Sources" indicator (chain-link icon + count) expandable to show upstream dependencies. Each source is clickable. Field-level provenance on demand (which specific script lines produced this specific field). *(Source: R1 for the chain-link icon pattern, R2 for "provenance tooltip" concept, R3 for "Made from" breadcrumb)*

**Error framing as "creative conflict," not technical failure.** (R2) Continuity violations should be presented as "Conflict Badges" with resolution options (Option A / Option B / Ignore with reason), not error logs. *(Source: R2 — unique contribution, practical and well-reasoned)*

### 3.5 Artifact Browsing & Inspection

**Proven / High Confidence:**

**Multi-representation viewer (Postman-inspired).** (R1, R3) Each artifact should have multiple view modes:
- **Readable**: Human-friendly document (character bible as a narrative document, scene breakdown as production notes)
- **Structured**: Fields in a table/tree with inline editing (MongoDB Compass-style)
- **Source**: Original script excerpts that generated this artifact
- **Export**: JSON/CSV/FDX-compatible download

*(Source: R1 for Pretty/Raw/Source triptych, R3 for the four-tab specification)*

**Three levels of information density per artifact type.** (R1 — unique contribution, critical)
1. **Card/Thumbnail** (2–3 lines): Name + key attribute + visual indicator. Used in lists, grids, search results.
2. **Summary/Inspector** (5–8 fields): Key fields in a well-formatted card. Used in slide-over panel.
3. **Full Detail** (all fields, sectioned with toggles): Used only on explicit request.

Default to level 1 for lists, level 2 for slide-overs, level 3 on "View Full Detail." *(Source: R1)*

**Slide-over as primary detail pattern.** (All three reports) Master-detail with slide-over panel. Maintains spatial context (list visible behind), provides enough space for rich content, Escape returns to list. Deep drilling handled by replacing slide-over content with back button (not nested slide-overs beyond one level). *(Source: R1 most detailed, R3 confirming with "avoid modal stacks")*

**Version history with visual snapshots + semantic diffs.** (R1, R2, R3) Combine Figma's visual thumbnail per version, Google Docs' timeline sidebar, and GitHub's split-view diffs. For CineForge: artifact versions show "what changed and why" (e.g., "Character age changed from 30 to 50 — user override" with consequence warnings). *(Source: R1 for the visual snapshot approach, R2 for "semantic diffing," R3 for "changed because" provenance in diffs)*

**Filterable artifact collections.** (R1) Filter bar above artifact lists with predefined facets (character, location, time of day, scene type) and free-text search. Not a query language—a search-like experience. *(Source: R1, from jq playground adaptation)*

### 3.6 Film & Production Tool Patterns

**Proven / High Confidence:**

**StudioBinder's color-coded element tagging is the gold standard for artifact taxonomy.** (R1, R3) Characters = one color, props = another, wardrobe = another. Colors persist everywhere: script markup, breakdown sheets, stripboards, artifact cards. CineForge should adopt this with its own palette. *(Source: R1 most detailed)*

**Scene strips / index cards as the universal structure metaphor.** (R1, R3) Index cards match the mental model of every storyteller. CineForge's default scene view should be card/strip-based (Highland's index cards, StudioBinder's stripboard). Each strip shows: scene number, heading, key characters, mood/tone indicator. *(Source: R1, R3)*

**Script must render in proper screenplay format.** (R1, R3) Courier font, proper indentation for dialogue blocks, uppercase character names. This signals craft respect and establishes trust. Don't "web-app-ify" the script view. *(Source: R1 for rationale, R3 confirming)*

**Frame.io's contextual annotation pattern.** (R1, R2, R3) Comments/corrections anchored to specific script lines or artifact fields. User feedback becomes a correction instruction for AI reprocessing. *(Source: R1 for the pattern, R2 for comparison modes, R3 confirming)*

**Celtx's asymmetric linking model.** (R1) Script is the source of truth; AI artifacts are derived views. Editing the script updates artifacts; editing an artifact doesn't change the script but creates an override and flags the divergence. *(Source: R1 — important architectural principle)*

**Bi-directional sync between structural views and script text.** (R2) Dragging a scene card in the beat board reorders the script; editing a scene heading in the script updates the card. *(Source: R2, R1 confirms with Arc Studio Pro analysis)*

### 3.7 Design Direction

**Proven / High Confidence:**

**Visual personality: Dark, warm, cinematic.** (All three reports)
- Not developer-gray (Airflow), not corporate-white (Jira), not toy-colorful
- Three reference points: **Arc Studio Pro** (cinematic dark mode), **Frame.io** (content-centric layout), **Linear** (precision + no visual clutter)
- R1's specific color palette is the strongest recommendation:
  - Background: Dark charcoal (#161618–#1C1C1E)
  - Surfaces: Slightly lighter (#242428) with subtle 1px borders
  - Primary text: Warm off-white (#E8E4DF)
  - Accent colors: Warm amber/gold (scenes/primary), soft coral (characters), muted teal (locations), sage green (success)
  - Typography: Humanist sans-serif (Inter/DM Sans) for UI; Courier Prime for screenplay text

**Three-panel zoned workspace.** (All three reports)
- **Left**: Artifact navigator (persistent tree organized by artifact type)
- **Center**: Living canvas (script view, card grid, or stripboard depending on context)
- **Right**: Inspector (toggleable, context-sensitive metadata/provenance/overrides)
- Panels independently show/hide; zones match Apple Pro app conventions (Final Cut, Logic)

---

## 4. Conflict Resolution Ledger

| Claim | Report 1 | Report 2 | Report 3 | Resolution | Confidence |
|---|---|---|---|---|---|
| **Primary pipeline visualization** | Vertical phase list (Vercel/Stripe) as sidebar + skeleton fill in main panel | Kanban board with drag-and-drop triggering pipeline stages | Step list (GitHub Actions) with expandable detail | **R1's hybrid (vertical phase list + skeleton fill)** wins. R2's Kanban implies manual stage transitions, contradicting the "AI does everything" model. R3's step list is compatible with R1's approach. Kanban should be rejected. | High |
| **Single most important interaction** | "Drag in script → instant preview → progressive materialization" (the intake flow) | "The Living Script" (script-as-database editing model) | "Artifact Review Queue" (trust-building through evidence-backed decisions) | **These are complementary, not contradictory.** R1 describes the intake experience (first 5 minutes); R3 describes the ongoing review interaction (the next hour); R2 describes the underlying editing model. Synthesis: The intake flow (R1) is the *first* most important interaction. The artifact review queue (R3) is the *ongoing* most important interaction. The script-as-database model (R2) is the *architectural* principle underneath both. All three should be implemented. For the survey question "single most important," R1's intake flow is the answer because it determines whether users ever reach the review queue. | High |
| **Autopilot/manual control indicator** | Implicit via "human-edited" field badges; no global mode toggle | Explicit "Global Autopilot Status" indicator; distinct "Draft Mode" vs "Lock Mode" | Scoped accept buttons ("Accept for this scene" vs "Apply to all scenes") | **R1 + R3's approach is better than R2's global toggle.** A global "Draft/Lock Mode" creates a binary state that doesn't match real usage (users want autopilot for most things but manual control for specific decisions). Field-level badges (R1) + scoped accept buttons (R3) provide granular control without forcing the user into a global mode. R2's concept is useful as a *philosophical principle* but shouldn't manifest as a literal UI toggle. | High |
| **Film production scheduling (stripboards, call sheets)** | Mentioned as navigation view; no scheduling recommendations | Detailed: automated stripboards, constraint-based scheduling, live call sheets | Mentioned as visual pattern for scene browsing | **R2's scheduling features are out of scope for v1.** CineForge is a pre-production artifact generation tool, not (yet) a scheduling tool. StudioBinder-style stripboards should be adopted as a *scene navigation/browsing view* (R1, R3), not as a scheduling surface. R2's live call sheets and constraint-based scheduling are future features. | Medium |
| **Teenage Engineering as design reference** | Not mentioned | Cited for tactile quality and artifact "weight" | Not mentioned | **Interesting but insufficient evidence.** R2 doesn't provide specific mechanisms from TE's interfaces that translate to CineForge's needs. The "tactile quality" principle is valid but better served by R1's specific color/typography/spacing recommendations and R1's "designed presentation" principle (character bibles should look like character sheets, not data records). Deprioritize TE as a named reference; absorb the principle. | Low |
| **Light vs dark theme** | Dark only, with specific palette | Not specified | "Offer light and dark, but make dark feel cinematic" | **Ship dark-first with light as a secondary option.** R1's palette is well-specified and cinematically appropriate. R3's recommendation to offer both is pragmatic (accessibility, varying lighting environments). Build dark as the default and primary brand expression; provide a light mode for accessibility. | Medium |
| **Entity graph visualization** | Described as one artifact type among many; uses corkboard metaphor | Mentioned as internal dependency tool | Listed as optional/advanced view | **Entity graph should be a browsable artifact but not a primary navigation surface.** All reports agree it's secondary. Present it as one artifact type in the navigator tree, viewable as a visual relationship map (R1's corkboard metaphor). Not a primary interaction mode. | High |

---

## 5. Decision Matrix — Artifact Browser Layout

| Option | Scanability (×3) | Depth Access (×2) | Spatial Context (×2) | Novice-Friendliness (×2) | Keyboard Nav (×1) | **Weighted Total** |
|---|---|---|---|---|---|---|
| **Card Grid** | 4 (12) | 2 (4) | 3 (6) | 5 (10) | 3 (3) | **35** |
| **List/Table** | 5 (15) | 3 (6) | 2 (4) | 3 (6) | 5 (5) | **36** |
| **Slide-over from List** | 4 (12) | 5 (10) | 4 (8) | 4 (8) | 5 (5) | **43** |
| **Full-page Navigation** | 2 (6) | 5 (10) | 1 (2) | 3 (6) | 4 (4) | **28** |
| **Stripboard** | 5 (15) | 1 (2) | 5 (10) | 4 (8) | 2 (2) | **37** |

**Winner: Slide-over from List**, with **Card Grid as the default collection view** and **Stripboard as a switchable alternative** for story-flow scanning.

Scoring rationale: "Depth Access" scores how easily you can inspect an artifact fully. "Spatial Context" scores whether you maintain awareness of where you are in the collection. Slide-over from list excels because it provides full depth while preserving list context. Card grid wins for novice first impressions. Stripboard wins for cinematic story-flow scanning but has poor depth access (strips are too compact for inline detail).

**Implementation: Switchable collection views (Card Grid / List / Stripboard) → any selection triggers a slide-over panel with full artifact detail.**

---

## 6. Final Recommendation

### The CineForge Operator Console Design Direction

**Visual Identity:** Dark cinematic workspace. Background #161618–#1C1C1E. Warm off-white text (#E8E4DF). Amber/gold primary accent. Semantic color-coding: amber for scenes, coral for characters, teal for locations, sage for success states. Humanist sans-serif (Inter or DM Sans) for UI; Courier Prime for screenplay rendering. Reference Arc Studio Pro + Frame.io + Linear.

**Layout:** Three-panel zoned workspace.
- **Left rail** — Artifact Navigator: collapsible tree organized by type (Script, Scenes, Characters, Locations, Relationships, Continuity). Status indicators per artifact (✓ / ⏳ / ⚠️). During processing, a compact vertical phase indicator shows pipeline progress with auto-collapse for completed stages.
- **Center canvas** — The primary workspace. Switchable between: Script View (formatted screenplay with toggleable AI annotations), Card Grid (artifact collection overview), and Stripboard (scene-flow visualization). All views synchronized—selection in one reflects in all.
- **Right inspector** — Toggleable (⌘I). Context-sensitive: shows Summary → Evidence → Overrides → History → Export tabs for the selected artifact. Includes provenance links ("Made from" with clickable source citations) and version history with semantic diffs.

**The Intake Flow:**
1. Full-viewport drop zone → "Drop your screenplay here"
2. File animates into the workspace; progress shimmer; "Reading your screenplay..."
3. Within 10–15s: "First Look" summary card (title, scene count, character count, genre tags) with skeleton UI showing the shape of the full workspace
4. CTA: "Begin Full Analysis" (primary) / "Review details first" (secondary)
5. Progressive materialization: artifact cards populate one by one; script gains clickable annotations; completed artifacts unlock browsing immediately while later stages continue

**The AI Approval Model:**
- Objective extractions → single result, inline-editable, implicit acceptance
- Subjective interpretations → 2–4 variations with confidence + evidence, user selects
- Every AI value → field-level provenance (clickable to source script lines), field-level override with "human-edited" badge that persists across re-runs
- No binary Accept/Reject gates on whole artifacts. No destructive overwrites. Always show original alongside interpretation.

**The Artifact Browser:**
- Collections default to Card Grid view (Name + key attribute + status indicator, 2–3 lines max)
- Switchable to List/Table (sortable, filterable) or Stripboard (colored scene strips for flow visualization)
- Selecting any artifact opens a Slide-over Panel (~60% viewport) with full summary. List remains visible for context.
- "Full View" toggle expands slide-over to fill viewport for immersive reading
- Deep drilling replaces slide-over content with back button (max one level of nesting)
- Filter bar with predefined facets + free-text search

**The Processing Experience:**
- Vertical phase list in the left rail (compact, auto-collapsing completed stages)
- Skeleton UI in the center canvas that progressively fills with real data
- Chunked milestones: "Extracting scenes... 7/14" with contextual status
- Early partial results: unlock artifact browsing as soon as each stage completes
- Errors framed as "Conflicts" with resolution options, not technical failures

**Keyboard Navigation:**
- ↑↓ navigate artifact lists; Enter opens slide-over; Escape closes
- ⌘I toggles inspector; ⌘1/2/3 switches collection views
- ⌘F searches across all artifacts
- Tab cycles through fields in the inspector for rapid editing

---

## 7. Implementation Plan / Next Steps

### Phase 1: Core Shell (Weeks 1–3)
1. **Three-panel layout** with responsive panel toggling (left navigator, center canvas, right inspector)
2. **Drop zone intake flow** through Phase 3 (instant preview with summary card)
3. **Script view** with proper Courier rendering and scene-heading-based navigation
4. **Dark theme** with the specified color palette

### Phase 2: Artifact System (Weeks 3–6)
5. **Artifact Navigator** tree organized by type with status indicators
6. **Card Grid** default view for artifact collections
7. **Slide-over detail panel** with three information density levels (card → summary → full)
8. **Inline editing** for all AI-generated fields with "human-edited" badge
9. **Provenance links** ("Made from" with clickable source citations)

### Phase 3: Pipeline Experience (Weeks 6–8)
10. **Progressive materialization** during pipeline runs (skeleton → populated)
11. **Vertical phase indicator** in the left rail with auto-collapse
12. **Early partial results** (unlock browsing per completed stage)
13. **Conflict resolution UI** for continuity issues and ambiguous extractions

### Phase 4: Power Features (Weeks 8–12)
14. **View switching** (Card Grid ↔ List/Table ↔ Stripboard)
15. **Version history** with visual snapshots and semantic diffs
16. **Variational presentation** (2–4 options) for subjective AI interpretations
17. **Keyboard navigation** full implementation
18. **Filter bar** with faceted search across artifact collections

### Validation Milestones
- **After Phase 1**: User test the intake flow with 5 screenwriters. Success metric: user uploads a script and understands the summary card within 30 seconds.
- **After Phase 2**: User test artifact browsing. Success metric: user can find a specific character's bible and edit a field within 2 minutes without instruction.
- **After Phase 3**: User test the full pipeline run. Success metric: user does not ask "what is it doing?" during processing—the progress UI answers the question proactively.

---

## 8. Open Questions & Confidence Statement

### Open Questions

1. **Mobile/tablet responsiveness**: None of the reports address how the three-panel layout degrades on smaller screens. The target user (storyteller) may want to review artifacts on an iPad. Needs separate research.

2. **Collaborative review**: Frame.io's annotation pattern is referenced, but the multi-user collaboration model (multiple reviewers on the same project) is unexplored. How do user overrides interact when two people edit the same character bible?

3. **Script format detection and conversion**: The intake flow assumes clean format detection (.fdx, .fountain, .pdf, .docx), but real-world screenplays have wildly inconsistent formatting, especially PDFs. The "instant preview" phase may need a "We couldn't parse this cleanly—review formatting?" fallback path.

4. **Re-run behavior**: When the user edits their script and re-runs the pipeline, how do existing overrides, comments, and manual edits interact with new AI outputs? The "human-edited" badge concept is clear, but the full merge/conflict model needs specification.

5. **Entity graph visualization**: All reports agree it's secondary, but the specific visual treatment (corkboard? force-directed graph? relationship table?) is unresolved. Needs user testing.

6. **Accessibility**: Dark cinematic themes can create contrast challenges. WCAG compliance with the proposed palette needs verification, especially warm gray secondary text (#8A8680) against dark backgrounds.

### Confidence Statement

**High confidence (evidence from all three reports + strong tool precedents):**
- Artifact-centric over pipeline-centric organization
- Three-panel workspace layout
- Slide-over as primary detail pattern
- Implicit acceptance + inline editing as approval model
- Provenance visibility as trust-building mechanism
- Dark warm cinematic visual personality
- Progressive materialization over spinners for long-running tasks
- Card/strip-based scene browsing as default

**Medium confidence (agreement across reports but limited direct precedent in this exact domain):**
- Variational presentation (2–4 options) for subjective AI decisions — well-proven in image generation (Midjourney), untested for text-based production artifacts like character bibles
- The specific five-phase intake flow — logical and well-designed but needs user testing to validate timing and information hierarchy
- Color-coded artifact taxonomy — well-proven in StudioBinder but may create visual noise at scale (100+ entities)

**Lower confidence (single-report contributions or insufficient evidence):**
- R2's "Conflict Badge" resolution UI — good concept but needs interaction design validation
- The specific hex values in the color palette — directionally right but need accessibility testing and iteration
- Keyboard shortcut vocabulary — the shortcuts are logical but need user testing for discoverability and conflict with OS/browser defaults