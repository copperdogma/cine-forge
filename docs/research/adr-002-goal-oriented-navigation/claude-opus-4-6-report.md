---
type: research-report
topic: adr-002-goal-oriented-navigation
canonical-model-name: claude-opus-4-6
research-mode: standard
collected: '2026-02-25T23:03:55.946975+00:00'
---

# Goal-oriented navigation for AI creative pipelines

**CineForge should combine a visual DAG with adaptive conversational AI to guide users through its deep pipeline—drawing on patterns from CI/CD visualizations, game tech trees, creative tool preflight systems, and multi-persona onboarding.** The most effective navigation system won't be a single pattern but a layered architecture: an always-visible pipeline map inspired by DaVinci Resolve's page bar, dependency-aware node states borrowed from GitHub Actions, the goal-backward planning of Civilization's tech trees, InDesign-style live preflight monitoring, and Canva's single-question persona routing. Together, these patterns solve the fundamental tension in CineForge's design: users need freedom to explore a non-linear creative process while the system quietly ensures upstream dependencies produce high-quality downstream outputs.

This report synthesizes research across creative tools (Runway, Houdini, DaVinci Resolve, Nuke), dependency visualization systems (CI/CD pipelines, game tech trees, project management tools), AI reasoning architectures (LangGraph, CrewAI, HTN planning), multi-persona onboarding (Canva, Figma, Notion, Linear), and upstream-skip handling (render engines, build systems, 3D printing slicers). Each section delivers recommended patterns, anti-patterns, concrete examples, and evidence—culminating in a unified design recommendation for CineForge.

---

## 1. Multi-stage creative tool UX: what works, what breaks

### The two models that matter most for CineForge

Creative production tools follow two distinct paradigms for multi-stage workflows, and CineForge needs elements of both.

**The "page bar" model** (DaVinci Resolve) places all pipeline stages as persistent tabs along the bottom of the screen: Media → Cut → Edit → Fusion → Color → Fairlight → Deliver. This communicates the full workflow at a glance and implies a recommended order without enforcing it. Users can jump freely between pages, and each operates on the same shared data model (the Media Pool and timeline). Crucially, **DaVinci Resolve never blocks skipping**—opening the Color page with no clips simply shows an empty state. This permissive approach works because every page gracefully handles the absence of upstream work.

**The node graph model** (Runway Workflows, Houdini PDG, Nuke) makes dependencies explicit through visual connections between processing nodes. Runway's 2024-2025 Workflows feature is the closest analog to CineForge: text input → LLM prompt enhancement → image generation → video generation → output, all visible as a node graph with typed connections. Per-node execution lets users test individual stages, while "Run All" processes the full pipeline. **Houdini's PDG adds the most sophisticated dependency awareness**: work items on each node display color-coded status (pending, cooking, complete, failed), dirty propagation marks downstream nodes as stale when upstream changes, and a two-phase generate/cook model lets users preview what will happen before committing resources.

**Recommended patterns for CineForge:**

- **Persistent pipeline bar** (DaVinci Resolve-style) showing all stages with status indicators, always visible regardless of which stage the user is working in
- **Node graph view** available on demand for users who want to see the full DAG structure with dependency arrows, typed connections, and per-node output thumbnails (Nuke's "postage stamp" pattern)
- **Two-phase execution** (Houdini's generate → cook): let users preview what each stage will produce before running expensive AI operations
- **Per-node version history** (Runway): every stage maintains a browsable history of previous outputs, enabling comparison and rollback without re-running the pipeline
- **Dual-perspective architecture** (Ableton Live's Session View vs. Arrangement View): offer both an "exploration mode" where users can experiment freely with any stage and a "pipeline mode" showing the structured sequential flow

### What AI video tools reveal about freeform vs. structured

Most AI video tools (Pika, Kling, Luma) are deliberately **single-step and freeform**—prompt → generate → iterate. They have no pipeline concept, and the workflow is pure iteration. This works for simple generation but collapses for complex multi-shot film production where character consistency, scene coherence, and creative direction need to propagate across dozens of outputs. Sora's Storyboard interface is the notable exception: users create caption cards on a timeline, upload reference images per card, and can auto-generate a storyboard from a scene description. **Sora's auto-storyboarding—AI generates the pipeline stages, user refines them—is directly applicable to CineForge's workflow.**

### Anti-patterns to avoid

- **Rigid stage enforcement** (Unity's approach of blocking saves with broken dependencies): too aggressive for creative work where exploration requires incomplete states
- **Hidden dependencies** (Premiere Pro's workspace model): workspaces reconfigure the interface but give no indication of pipeline progress or data flow relationships
- **Single-step flatness** (Pika/Kling): no pipeline concept means no way to propagate creative decisions consistently across outputs
- **Silent degradation without explanation**: Blender's OSL rendering bug that silently turned textures pink with zero error messages caused users hours of debugging—the worst possible pattern

---

## 2. Dependency-aware progress UI: visualizing a DAG, not a list

### The three-state paradigm is universal

Every successful dependency visualization system converges on the same fundamental pattern: **three visual states for nodes—completed, available now, and locked/blocked**. Civilization 6's tech tree uses teal (researched), dark gray (available), and light gray (locked). GitHub Actions uses green (success), yellow (in-progress), and gray (pending). Path of Exile's passive skill tree distinguishes allocated, allocatable (connected to your path), and unreachable nodes. CineForge should adopt this same three-state model: **completed stages (green), ready-to-start stages (highlighted/pulsing), and blocked stages (dimmed with lock icons showing what prerequisites are missing)**.

### CI/CD pipelines: real-time DAG visualization at scale

GitHub Actions renders workflows as left-to-right DAG graphs with color-coded job nodes and dependency arrows, updating in real-time as jobs progress. GitLab CI supports true DAG mode through its `needs` keyword, where the visualization shows dependency arrows rather than just stage boundaries—a job starts as soon as its specific dependencies finish, not when its entire stage completes. This **fan-out/fan-in pattern** maps naturally to film production: a screenplay fans out into parallel department work (character design, location scouting, shot planning) that converges into storyboards.

CircleCI's experience reveals the **critical scalability problem**: with 30+ parallel jobs, dependency lines cross and overlap, creating what one user called "a rat's nest." CircleCI responded by adding **hover-to-highlight**—mousing over a node dims everything except its upstream and downstream dependencies. This interaction pattern is essential for CineForge's pipeline, which could easily reach 15-30 nodes.

**Azure DevOps' Dependency Tracker** offers the most instructive multi-view approach: the same dependency data rendered as a risk graph, dependency wheel, analytics map, and grid matrix. CineForge should similarly offer multiple views of its pipeline—DAG graph, checklist, and timeline—each serving different user needs and cognitive preferences.

### Game tech trees: making complexity feel empowering

Civilization 6's tech tree provides the strongest model for making a complex prerequisite graph feel motivating rather than gatekeeping. Three design principles stand out:

1. **Visible beacons**: Powerful techs further down the tree serve as aspirational goals, giving players direction. In CineForge, showing the "final storyboard" or "rendered scene" at the end of the pipeline—even locked—creates pull toward completion.
2. **Eureka boosts**: Civ 6 grants a **50% research discount** when players complete an in-game action related to a tech. CineForge could implement analogous "boosts"—uploading reference images accelerates mood board generation, providing a detailed script accelerates entity extraction.
3. **Dual value per node**: Each tech is valuable both for what it immediately provides AND what it unlocks downstream. Every CineForge stage should deliver immediately useful output (a scene breakdown is useful even without storyboards) while clearly showing what becomes possible next.

Path of Exile's passive skill tree at **1,384+ nodes** demonstrates how to handle extreme scale: semantic zoom (zoomed out shows clusters, zoomed in shows individual nodes), search with pulsing glow highlight visible even when zoomed out, and spatial clustering by attribute type. For CineForge, this means grouping pipeline nodes into collapsible phase clusters (Development, Pre-Production, Production, Post) that expand on demand.

**Factorio's tech tree** demonstrates the key failure mode: a non-planar DAG with unavoidable edge crossings and no zoom-out overview. New players reported needing external wikis to understand relationships. This confirms that **CineForge must invest in layout algorithms** (like Sugiyama/layered DAG layout via d3-dag) and provide global search with highlight.

### Recommended patterns for CineForge's pipeline visualization

- **Left-to-right DAG graph** as the primary view, organized into phase columns (echoing Civ 6's era structure), with parallel nodes stacked vertically within each column
- **Three-state color coding**: completed (green/teal), available now (highlighted border, slightly pulsing), blocked (dimmed with prerequisite indicators)
- **Hover-to-trace**: mousing over any node highlights its full upstream prerequisite chain and downstream dependents while dimming everything else
- **Goal-backward navigation**: clicking any locked node shows the shortest path of prerequisites needed to unlock it, with a "Start this path" button
- **Semantic zoom**: phase clusters at overview level, individual nodes at detail level, scaling gracefully from CineForge's ~10 core stages to 30+ when expanded with optional substages
- **Search with highlight**: essential at scale—type a keyword, and matching nodes glow visibly across the entire graph
- **Optional vs. required distinction**: required nodes shown with solid borders and "required" badges; optional nodes shown with dashed borders; optional nodes never block downstream progress

### Anti-patterns to avoid

- **Linear steppers/wizards**: they assume a single path and cannot represent DAGs; PatternFly's "progressive wizard" is the closest wizard pattern to DAGs but still fundamentally sequential
- **Gantt charts as primary view**: they map tasks to time, not to dependency structure—they show WHEN things happen, not WHAT blocks WHAT
- **Showing the full graph on first load**: front-loaded complexity is the #1 complaint about tech trees in games and CI/CD visualizations alike

---

## 3. How the AI should reason about CineForge's pipeline

### Graph representations: what LLMs actually understand

Research from the landmark "Talk like a Graph" paper (Fatemi et al., ICLR 2024) establishes that **the choice of graph encoding can swing LLM performance by 4.8% to 61.8%** depending on the task. No single representation dominates. Natural language descriptions ("Node A connects to Node B") work best for sparse graphs and are most intuitive, but scale poorly for dense graphs. Adjacency lists serve as a reliable baseline. Mermaid diagrams are **up to 24x more token-efficient than JSON** and can be both generated and consumed by LLMs. However, LLMs struggle with graphs beyond a few dozen nodes in any text-based format, and multi-hop reasoning degrades sharply.

**CineForge's optimal strategy is a hybrid representation:**

- **Internal canonical format**: structured JSON with node schemas including prerequisites, outputs, status, and staleness triggers—programmatically queryable and manipulable
- **LLM reasoning context**: natural language descriptions of the **local subgraph** (2-3 hops from the user's current focus), not the entire pipeline—respecting LLM working memory limits
- **User-facing visualization**: Mermaid diagrams for rendering pipeline state in chat, supplemented by the interactive DAG view
- **Adaptive encoding**: following the Graph Theory Agent pattern, select the best representation based on the query type ("what depends on X?" benefits from adjacency lists; "what's the critical path?" benefits from natural language narrative)

### The plan-then-execute pattern from AI coding assistants

AI coding assistants have converged on a powerful pattern directly applicable to CineForge: **explicit plan mode that separates reasoning from execution**. Cursor generates a `.plan.md` with structured phases and numbered steps. Claude Code's Plan Mode (activated via Shift+Tab) gives the AI read-only access—it analyzes and proposes without making changes until the user approves. GitHub Copilot generates task-level breakdowns viewable in a sidebar.

A real-world comparison by Nearform found that both Cursor and Copilot plan modes **outperformed straight-to-code approaches**, producing "better-structured logic, cleaner components, and more thoughtful handling of edge cases." This validates the pattern for CineForge: when a user requests something complex ("create a mood board for my sci-fi film"), the AI should first present a structured plan showing which pipeline steps are needed, what inputs exist, and what's missing—then execute only after approval.

### CineForge's pipeline is an HTN (Hierarchical Task Network)

The most theoretically precise framing for CineForge's DAG is a **Hierarchical Task Network** from AI planning literature. HTN planning decomposes compound tasks (like "film pre-production") into primitive tasks through methods with preconditions and effects. Each CineForge pipeline node maps to an HTN operator: it has preconditions (required inputs from upstream nodes), an operation (the AI generation or user action), and effects (outputs that feed downstream).

**ChatHTN and GPT-HTN-Planner** demonstrate how to hybridize symbolic HTN planning with LLMs: the symbolic planner handles known decompositions while the LLM generates novel decompositions when no predefined method matches. This reduces LLM queries by up to **75%** while maintaining plan soundness. CineForge should implement its pipeline as an HTN where:

- Known pipeline paths (script → scene extraction → storyboards) use deterministic decomposition
- Novel user requests ("I want to skip straight to a trailer") trigger LLM-based adaptive planning
- Verifier tasks validate that each step's outputs satisfy downstream preconditions

### Proactive guidance: timing matters more than content

Research reveals a critical nuance about AI proactiveness. A 2024 Springer study found that proactive AI help **reduces users' competence-based self-esteem**, which in turn **reduces system satisfaction**—and this effect is **stronger for users with higher AI knowledge**. Expert filmmakers will resist unsolicited guidance more than novices.

A 2026 developer field study (Kuo et al.) with 229 AI interventions provides the practical answer: **workflow boundary interventions** (e.g., after completing one step, before starting the next) achieved a **52% engagement rate**, while mid-task interventions were dismissed **62% of the time**. Well-timed proactive suggestions required significantly less interpretation time than reactive suggestions (**45.4 seconds vs. 101.4 seconds**, p=0.0016).

**CineForge's guidance model should be:**

- **At workflow boundaries** (completing one pipeline stage): briefly surface what's now unlocked and what's recommended next—"Your scene extraction is complete. Entity bibles and creative direction are now available."
- **At generation time** (user requests a downstream output): show a pre-flight summary of upstream status—"This storyboard will use 3 characters with entity bibles and 1 placeholder. Quality estimate: ★★★☆☆."
- **Never mid-task**: don't interrupt a user who is actively editing a screenplay or refining a mood board
- **User-controlled verbosity**: three levels—Novice (explain everything proactively), Standard (flag critical issues at boundaries), Expert (respond only when asked)
- **Progressive disclosure of dependency explanations**: brief flag → expand for details → full dependency chain trace on request

---

## 4. Onboarding across personas: one project, four lenses

### One question is enough—then infer the rest

Canva's single onboarding question—"What will you be using Canva for?"—triggers entirely different first-run experiences and contributed to growth past **10 million users** in two years. Notion similarly asks one use-case question and lands users in a personalized workspace in under 50 seconds. Research on 200+ onboarding flows confirms: users want to start doing, not answer questions. Product tours that force reading before doing see up to **80% abandonment**.

**CineForge should ask exactly one question**: "I'm a..." with options for Screenwriter, Director, Producer, and Just Exploring. Make it skippable (defaulting to Explorer). This single signal personalizes the first-run experience—what templates appear, which pipeline stages are foregrounded, what the AI's first message is—without creating friction.

### Same data, different views: the Linear/Figma model

Figma's strategy of creating **distinct product surfaces sharing a common engine** (Figma Design for designers, FigJam for PMs, Dev Mode for engineers, Slides for stakeholders) is the strongest model for CineForge's multi-persona challenge. The key insight: Figma doesn't force all user types through the same interface—it gives them purpose-built surfaces that share the same underlying data. A design change shows up automatically in Dev Mode's code snippets.

Linear takes a lighter approach: **filter-based lenses on a single data model**. IC engineers see My Issues, managers see Project views with cycle analytics, executives see Initiatives spanning multiple projects. Linear's philosophy—"flexible software lets everyone invent their own workflows, which eventually creates chaos as teams scale"—led them to opinionated defaults that reduce decision fatigue.

**CineForge should implement the Figma model at the view layer and the Linear model at the data layer:**

- **One project data model** where screenplay text, entity bibles, creative direction, shot plans, and storyboards all live together
- **Four persona views**: Screenwriter sees script-centric tools (screenplay editor, character arcs, dialogue), Director sees visual tools (storyboard canvas, shot planner, mood boards), Producer sees management tools (timeline, budget estimates, resource allocation), Explorer sees a dashboard with entry points into everything
- **Cross-persona visibility**: a Screenwriter's script change automatically propagates to the Director's shot list and Producer's timeline
- **Easy view switching**: any user can access any persona's view at any time through a global navigation selector

### The Explorer problem: sandbox onboarding

For users who select "Just Exploring" or skip persona selection entirely, the best pattern comes from Notion: create a **sample project that IS the tutorial**. Notion's Getting Started page is itself a Notion page—a checklist within the product that teaches by doing. CineForge should offer a pre-populated demo film project (e.g., a short sci-fi film in mid-pre-production) where Explorers can browse the script, view the storyboard, inspect entity bibles, and check the production timeline. Each interaction becomes a natural discovery point: "Like this storyboard? Try Director mode to create your own."

### Templates as confidence builders, not cages

UserTesting research on Canva revealed that users were "scared to click" and felt "I'm not creative enough; it's too hard." Templates solved this by providing an achievable starting point. But templates constrain when users are experts with established workflows or when the task is inherently creative.

**CineForge should calibrate template usage by persona:**

- **Producers**: heavy template use—budgets, schedules, and call sheets have standard formats
- **Directors**: mixed—shot list templates alongside freeform storyboard/mood board canvases
- **Screenwriters**: light—script format structure (standard screenplay formatting) but never content templates
- **Explorers**: full template gallery as a discovery mechanism

The critical design principle from Jason Lengstorf's Progressive Disclosure of Complexity framework: avoid the **all-or-nothing trap** where users must either accept all defaults or control everything. CineForge should let users opt out of AI assistance **per feature, not globally**—a Director might want AI-generated shot suggestions but manual control over camera angles.

### Five layers of AI autonomy

CineForge should offer a spectrum from full automation to full manual control, selectable per-feature:

- **Layer 1 — "Magic"**: "Generate a complete pre-production package from this logline"—AI handles everything
- **Layer 2 — Guided**: AI proposes each step, user approves/edits before proceeding
- **Layer 3 — Template**: user fills in structured templates, AI assists on request
- **Layer 4 — Copilot**: blank canvas with AI available as conversational assistant
- **Layer 5 — Manual**: full control, AI silent, expert tools exposed

---

## 5. The skipped-upstream problem: block, warn, or let them fail?

### The cost-of-failure spectrum determines the right response

Research across render engines, build systems, AI generators, and 3D printing slicers reveals that the optimal response to missing upstream work correlates directly with **how expensive failure is**:

| Cost of failure | Optimal response | Example |
|---|---|---|
| Seconds + cheap | Let fail, iterate quickly | Midjourney: generate → evaluate → refine prompt |
| Minutes | Warn + proceed with fallback | Blender: render with pink textures for missing files |
| Minutes to hours | Pre-flight check + preview | PrusaSlicer: mesh analysis → visual preview → print |
| Hours + materials | Soft block with fix path | InDesign: live preflight monitoring → fix list → export |
| Irreversible | Hard block | Bazel: compilation stops on missing dependency |

For CineForge, most pipeline stages are **seconds to minutes** (AI generation), making the warn-and-proceed model appropriate for most cases. But final render/export (potentially expensive and the deliverable) warrants stricter preflight checking.

### The Blender "pink texture" pattern: graceful degradation with visual diagnosis

Blender's iconic pink/magenta rendering for missing textures is the gold standard of **fallback with built-in diagnosis**. The render proceeds—you see your full scene—but every surface with a missing texture is immediately identifiable. Blender then provides `File > External Data > Find Missing Files` to systematically locate and reconnect broken references.

**CineForge should implement an analogous "pink texture" pattern for AI generation**: when generating storyboards with missing entity bibles, produce the storyboards anyway but mark gaps visually—placeholder silhouettes labeled "[Character: Detective Chen — no entity bible]" or "[Location: Warehouse — no description]." This teaches users what upstream data improves output while still delivering useful results.

### The InDesign preflight: live monitoring that never blocks

Adobe InDesign's Preflight panel is the most sophisticated implementation of continuous dependency monitoring. A **green/red circle** in the status bar continuously monitors the document—green means no issues, red shows an error count. Errors are categorized (Links, Text, Color, Images), each expandable to show specific instances. Clicking an error navigates directly to the problematic element. An info panel suggests fixes. Critically, **InDesign never blocks the user from working**—it surfaces information and trusts the user to act.

CineForge should implement a similar live pipeline health indicator: a persistent status dot (green/yellow/red) per pipeline stage, expandable to show specific missing dependencies, with click-to-navigate to the upstream stage that needs work.

### Build systems teach the best error messages

Make's classic error format—`No rule to make target 'foo', needed by 'bar'`—names both the missing thing AND what depends on it. TypeScript goes further: `Could not find a declaration file for module 'X'. Try 'npm i --save-dev @types/X'`—it explains the problem AND gives the exact fix command. npm offers an **escape hatch** (`--force`) that lets experienced users proceed despite known dependency conflicts.

**CineForge's dependency error messaging should follow this pattern:**

1. Name the missing thing: "Entity bible for 'Detective Chen' not found"
2. Name what depends on it: "...needed by Storyboard Generation (Scene 4)"
3. Suggest the fix: "[Create Entity Bible] or [Generate from Script]"
4. Offer an escape hatch: "[Proceed Anyway with Placeholder]"

### DALL-E 3's cautionary tale: automatic upstream enhancement backfires

DALL-E 3 automatically rewrites user prompts before generation, expanding "a horse" into "a detailed picture of a wild horse galloping across a vast, grassy plain." A study by Jahani et al. found this **actually reduces performance** when users have specific intentions—the rewriting adds "flowery language but often drops important parts of my prompt." Users reported the system changing "an Indian cricket player" to "a South-Asian cricket player," missing the point entirely.

This is directly relevant to CineForge: if the system auto-generates missing entity bibles or creative direction to fill upstream gaps, it must **always show what was auto-generated** and make it trivially overridable. Expert filmmakers will have specific creative intent that generic AI fill-ins will contradict.

### CineForge's recommended tiered response system

- 🟢 **Green — All upstream complete**: proceed normally, no warnings
- 🟡 **Yellow — Partial upstream, degraded quality**: show what's missing and what will be affected, offer both "Fix First" and "Proceed Anyway with Placeholders" buttons. Example: "No entity bible for 'Detective Chen.' Storyboards will use a generic character placeholder. [Create Bible] [Proceed Anyway]"
- 🔴 **Red — Critical upstream missing, output would be meaningless**: soft block with one-click fix path. Example: "No scenes extracted from screenplay. Scene extraction is required to generate storyboards. [Extract Scenes Now]"

### The preview-before-commit pattern from 3D printing

All major slicers (PrusaSlicer, Cura, Bambu Studio) implement a **mandatory preview between slicing and printing**—the tool generates the full output plan and lets users visually inspect layer by layer before committing to a multi-hour print. CineForge should adopt this for expensive operations: before generating a full storyboard set, show a summary—"12 scenes, 3 characters (2 with bibles, 1 placeholder), 4 locations (1 undescribed). Estimated quality: ★★★☆☆"—and let users choose to fix gaps or proceed.

---

## Unified synthesis: CineForge's goal-oriented navigation system

The patterns across all five research categories combine into a coherent four-layer navigation architecture for CineForge.

### Layer 1: The persistent pipeline bar

Inspired by DaVinci Resolve's page tabs, a **horizontal bar showing all pipeline stages** sits persistently at the bottom or top of the interface. Each stage shows its status through the universal three-state color coding (completed, available, blocked). This bar serves as both navigation (click any stage to enter it) and progress visualization (see the entire pipeline state at a glance). Stage badges show counts: "3 scenes extracted," "2 entity bibles created." The bar adapts to persona: a Screenwriter sees script-centric stages emphasized; a Director sees visual stages foregrounded; all stages remain accessible.

### Layer 2: The expandable DAG view

Available on demand (a "Pipeline Map" button or keyboard shortcut), a full **interactive DAG visualization** renders the pipeline as a left-to-right graph organized into phase columns. This view supports hover-to-trace dependencies, goal-backward planning (click any locked node to see the prerequisite path), semantic zoom (phase clusters at overview, individual nodes at detail), and search with highlight. The DAG view is where power users go to understand relationships, diagnose issues, and plan their workflow. It implements the InDesign-style live preflight indicator on every node.

### Layer 3: The conversational AI navigator

The primary interaction surface. The AI maintains an HTN-style model of the pipeline and reasons about the user's current position, available next steps, and missing prerequisites. It follows the **plan-then-execute pattern** from AI coding assistants: complex requests trigger a visible plan before execution. It uses the **workflow-boundary timing** from the developer field study: proactive suggestions appear when a stage completes, never mid-task. It calibrates verbosity to user expertise (Novice/Standard/Expert modes). When explaining dependency issues, it follows the Make/TypeScript pattern: what's missing → what depends on it → suggested fix → escape hatch.

### Layer 4: The persona-adaptive surface

The default view layer that changes based on the user's selected persona. Each persona sees a purpose-built workspace (Figma model) operating on shared project data (Linear model). Templates are calibrated to persona needs. The five-layer AI autonomy spectrum (Magic → Guided → Template → Copilot → Manual) is selectable per-feature, not globally. Explorer mode offers a pre-populated demo project (Notion sandbox model) that serves as both tutorial and persona discovery mechanism.

### How the layers work together — a scenario

A Director opens CineForge and asks the AI: "I want to create storyboards for the chase scene." The AI checks the pipeline graph and responds: "To generate storyboards for Scene 7 (Chase), I'll need scene extraction (✅ done), entity bibles for Detective Chen (✅ done) and The Phantom (⚠️ not created), creative direction (✅ mood board set), and shot planning (⚠️ not started). I can proceed now with a placeholder for The Phantom and auto-generate a shot plan, or we can fill in the gaps first. What would you like?" The pipeline bar shows Scene 7's storyboard node pulsing yellow. The Director clicks "Proceed anyway"—storyboards generate with The Phantom shown as a labeled silhouette placeholder. Later, when the entity bible is created, the AI notes at the workflow boundary: "The Phantom's entity bible is ready. Your chase scene storyboards can now be regenerated with the full character design. [Regenerate] [Keep Current]."

This scenario demonstrates all four layers working in concert: the conversational AI reasons about the DAG, the pipeline bar shows status, the persona view presents Director-appropriate tools, and the tiered response system (yellow warning, not red block) respects creative workflow while communicating quality trade-offs.

### Three principles that connect everything

**First, never block creative flow—always offer a path forward.** The research consistently shows that hard blocks frustrate creative users. Even when upstream work is missing, CineForge should generate something useful (the Blender pink-texture pattern) while clearly communicating what would improve quality (the Make error-message pattern). The only exception: when output would be truly meaningless (no screenplay uploaded at all), use a soft block with a one-click fix.

**Second, make the invisible visible without making it overwhelming.** The DAG is the backbone of CineForge's intelligence, but most users should never need to see it. The pipeline bar provides ambient awareness. The AI explains dependencies in natural language at appropriate moments. The full DAG view exists for those who want it. This follows the progressive disclosure principle that every successful complex tool—from DaVinci Resolve to Path of Exile to Linear—has independently converged on.

**Third, respect the expertise spectrum in every design decision.** Canva's research showed beginners need templates and confidence; PrusaSlicer's community showed experts want to suppress warnings. CineForge's tiered verbosity (Novice/Standard/Expert), per-feature AI autonomy levels, optional vs. required pipeline stages, and "proceed anyway" escape hatches all serve this principle. The tool should feel like a knowledgeable collaborator to a first-time filmmaker and an efficient production system to an experienced Director—simultaneously, without mode switches.