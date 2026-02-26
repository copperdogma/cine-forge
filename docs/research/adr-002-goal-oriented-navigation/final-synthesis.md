---
type: synthesis-report
topic: adr-002-goal-oriented-navigation
synthesis-model: claude-opus-4-6
source-reports:
- ai-google-deep-research.md
- ai-openai-deep-research.md
- claude-opus-4-6-report.md
- grok-4-1-report.md
synthesized: '2026-02-25T23:39:03.129731+00:00'
---



---
canonical-model-name: "claude"
report-date: "2025-07-09"
research-topic: "adr-002-goal-oriented-navigation"
report-type: "synthesis"
---

# Synthesis: Goal-Oriented Navigation for AI-Powered Creative Pipelines

## 1. Executive Summary

- **All three reports converge strongly** on a hybrid architecture: a persistent pipeline bar (DaVinci Resolve-style) for ambient progress awareness + an on-demand DAG graph view (CI/CD-style) for dependency inspection + conversational AI as the primary interaction layer that reasons over the graph.
- **The three-state node model is universal and validated**: completed (green), available/ready (highlighted), blocked/locked (dimmed). Every successful dependency visualization—from Civilization tech trees to GitHub Actions to Houdini PDG—independently converges on this pattern.
- **Hard blocking is wrong for creative tools; silent failure is worse.** The right model is a tiered response: warn with diagnosis + offer fix path + allow "proceed anyway" with visual placeholders (the "pink texture" pattern). Hard blocks reserved only for truly meaningless output (e.g., no script uploaded at all).
- **AI should reason over a hybrid graph representation**: structured JSON internally (for programmatic queries), natural-language subgraph descriptions for LLM context (scoped to 2-3 hops from current focus), Mermaid for rendering in chat. Full-graph prompting is both token-wasteful and empirically degrades LLM reasoning.
- **Onboarding should be a single question, not a wizard**: "I'm a [Screenwriter / Director / Producer / Explorer]" — one click that configures the default view, foregrounded stages, and AI personality. Skippable, changeable at any time.
- **Goal evolution is a first-class requirement**, not an edge case. Users who start with "just analyze my script" and later want storyboards must experience seamless expansion, not a restart. The pipeline graph naturally supports this—new stages simply become visible and available.
- **Proactive AI guidance works only at workflow boundaries** (stage completion moments), not mid-task. Mid-task interruptions are dismissed 62% of the time per field study evidence (Report 3). The AI should flag issues when a user attempts a downstream action, not while they're working upstream.
- **The "pre-flight check" pattern before expensive operations** (rendering, export) is endorsed by all three reports and drawn from 3D printing slicers, CI/CD, and InDesign's live preflight system. This is the highest-leverage single UX intervention for the "skipped upstream" problem.
- **Per-feature AI autonomy levels** (from "do everything" to "I'll handle it myself") prevent the all-or-nothing trap that frustrates both novices and experts. This is better than a global "AI assistance level" toggle.
- **Template-first entry calibrated by persona** reduces blank-canvas paralysis for beginners without constraining experts. Explorers get a pre-populated demo project that IS the tutorial (Notion pattern).
- **Scalability to 30+ nodes requires semantic zoom and collapsible phase clusters**, not flat graph rendering. CircleCI's "rat's nest" problem with 30+ parallel jobs confirms that hover-to-trace (highlight upstream/downstream, dim everything else) is essential.

## 2. Source Quality Review

| Criterion | Report 1 (Gemini) | Report 2 (OpenAI) | Report 3 (Claude Opus) | Report 4 (Grok) |
|---|---|---|---|---|
| Evidence Density | 3.5 | 3.5 | 4.5 | 3.0 |
| Practical Applicability | 4.0 | 3.5 | 5.0 | 4.0 |
| Specificity | 3.5 | 3.0 | 5.0 | 3.5 |
| Internal Consistency | 4.0 | 3.5 | 5.0 | 3.5 |
| **Overall** | **3.8** | **3.4** | **4.9** | **3.5** |

**Report 1 (Gemini):** Well-structured with clear per-category breakdowns and a good synthesis section. Strongest on the DaVinci Resolve analogy and the Rust compiler error model. Cites 58 sources but many are YouTube/Reddit links of unclear authority. The "Project Atlas" concept is well-articulated. Weakness: recommendations sometimes feel like a feature list rather than a design system with coherent principles. Treats Mermaid as "the standard" for LLM graph representation without acknowledging trade-offs.

**Report 2 (OpenAI):** Solid survey with good specific citations (Linear dependency line colors, Monday.com strict mode, Material Design stepper spec). Weaker on synthesis—reads more like a literature review than a design recommendation. The AI reasoning section references Claude Code and Copilot plan modes well but doesn't connect them to CineForge's specific challenge as tightly. Misses the timing question for proactive guidance entirely. Some sections are thin (onboarding gets less than half the depth of other reports).

**Report 3 (Claude Opus):** Clearly the strongest report. Distinguishes itself through: (a) the "Talk like a Graph" paper citation with specific performance data (4.8%–61.8% swing), which no other report provides; (b) the developer field study on proactive AI timing (52% engagement at boundaries, 62% dismissal mid-task), which directly answers a key design question; (c) the cost-of-failure spectrum table that provides a principled framework rather than ad hoc recommendations; (d) the DALL-E 3 prompt rewriting cautionary tale, directly relevant to auto-generating missing upstream data; (e) the five-layer AI autonomy model; (f) Path of Exile's 1,384-node tree as a scalability proof point. The unified four-layer architecture at the end is the most implementation-ready output of any report.

**Report 4 (Grok):** Covers all five categories competently and provides useful comparison tables. Good breadth—mentions Ableton's Session/Arrangement duality, Cursor's Plan mode, and CrewAI. But largely agrees with the other reports without adding unique insights or evidence. The "Pipeline Canvas" concept is essentially the same as Report 1's "Project Atlas" and Report 3's "DAG view." Weakest on the AI reasoning section—mentions JSON adjacency lists and Mermaid but doesn't cite the "Talk like a Graph" research or provide empirical guidance on representation choices.

**Weighting decision:** Report 3 is weighted most heavily throughout this synthesis due to superior evidence quality, unique empirical findings, and the most coherent architectural recommendation. Reports 1 and 4 provide useful supporting details and analogies. Report 2 contributes specific UI implementation details (Linear dependency colors, Material Design stepper specs) that complement Report 3's architectural framework.

## 3. Consolidated Findings by Topic

### 3.1 Pipeline Visualization Architecture

**High confidence (all reports agree):**

- A **persistent pipeline bar** (DaVinci Resolve's page tabs) should provide ambient awareness of all stages and their status. It serves as both navigation and progress indicator. [All reports]
- An **on-demand DAG graph view** should be available for users who want to see the full dependency structure. Not forced on anyone by default. [All reports]
- **Color-coded three-state nodes** (completed/available/blocked) are the universal pattern across CI/CD, tech trees, and creative tools. [All reports]
- **Node graph spaghetti as the default view is an anti-pattern.** ComfyUI and raw Nuke are cited as cautionary examples. The graph should be available, not mandatory. [Reports 1, 3]

**Moderate confidence (most reports agree):**

- **Semantic zoom with collapsible phase clusters** is necessary for scaling beyond ~10 nodes. Reports 1 and 3 cite specific evidence (CircleCI's scalability failure, Path of Exile's 1,384-node solution). Report 4 mentions collapsible groups. [Reports 1, 3, 4]
- **Hover-to-trace** (highlighting upstream/downstream while dimming everything else) is essential for complex graphs. [Reports 3, 4; implicit in Report 1's Reference Viewer discussion]
- **Goal-backward navigation** (clicking a locked node shows the shortest prerequisite path) borrows from Civilization's tech tree and is cited explicitly by Reports 1 and 3.

**Implementation specifics (from strongest evidence):**

- Layout: left-to-right DAG organized into phase columns (Development → Pre-Production → Production → Post), with parallel nodes stacked vertically within columns. [Report 3, supported by GitHub Actions' visual layout]
- Interaction: clicking any node navigates to its editor workspace; clicking a locked node shows prerequisite path with "Start this path" button. [Reports 1, 3]
- Status badges on nodes show artifact counts ("3/5 characters defined") and staleness indicators. [Reports 1, 3]
- The full DAG view should be accessible via keyboard shortcut (Tab or M) or a persistent button. [Reports 1, 3]

### 3.2 AI Reasoning Over the Pipeline Graph

**High confidence:**

- The AI should maintain and reason over a **structured representation of the project's dependency graph**, including node status, artifact health, and staleness. [All reports]
- **Plan-then-execute** is the correct pattern: the AI presents a structured plan before executing complex multi-step requests, then proceeds only after user approval. Evidence from Cursor and Claude Code plan modes. [Reports 2, 3, 4]
- **Proactive guidance should occur at workflow boundaries**, not mid-task. Report 3 provides the strongest evidence: 52% engagement at boundaries vs. 62% dismissal mid-task. [Report 3; Reports 1 and 2 agree on the principle without the empirical backing]

**Moderate confidence:**

- **Hybrid graph representation** is optimal: structured JSON internally, natural-language local subgraph for LLM context, Mermaid for chat rendering. Report 3 cites the "Talk like a Graph" paper showing that no single representation dominates and performance swings 4.8%–61.8% depending on task. Report 1 claims Mermaid is "the standard" for LLMs, but Report 3's evidence suggests this is an oversimplification.
- **Local subgraph scoping** (2-3 hops from current focus) for LLM context is preferable to full-graph prompting. Report 3 explicitly recommends this based on LLM working-memory limits; other reports don't address the scoping question.
- The pipeline can be modeled as an **HTN (Hierarchical Task Network)** for formal planning, with deterministic decomposition for known paths and LLM-based planning for novel requests. [Report 3; unique contribution]

**Lower confidence / promising but uncertain:**

- Multi-agent role coordination (AutoGen-style) where AI roles explicitly collaborate is interesting but adds system complexity. Reports 2 and 4 mention it; Report 3 doesn't endorse it. The evidence for this improving outcomes in creative pipelines (vs. engineering pipelines) is thin.

### 3.3 Handling the "Skipped Upstream" Problem

**High confidence (all reports agree):**

- **Never silently fail.** The worst possible pattern is the AI generating generic/random content to fill upstream gaps without telling the user.
- **The "pink texture" pattern** (generate output with visible placeholders for missing upstream data) is the right default for most CineForge operations. All reports cite Blender; Report 3 adds the specific recommendation for labeled placeholder silhouettes.
- **Diagnostic error messages** should follow the What Failed → Why → How to Fix → Escape Hatch pattern. Reports 1 and 3 cite Rust; Report 3 adds TypeScript and Make as additional evidence.
- **Pre-flight checks before expensive operations** are endorsed by all reports, drawn from 3D printing slicers, CI/CD, and InDesign.

**High confidence (specific to CineForge):**

- **Three-tier response system** based on severity:
  - 🟢 All upstream complete → proceed normally
  - 🟡 Partial upstream → warn with specifics, offer "Fix First" and "Proceed Anyway with Placeholders"
  - 🔴 Critical upstream missing (output meaningless) → soft block with one-click fix path
  [Report 3 provides the clearest formulation; Reports 1 and 4 agree with the tiered approach]

**Moderate confidence:**

- **Auto-generated upstream content must always be visibly marked and trivially overridable.** Report 3's DALL-E 3 cautionary tale (prompt rewriting that "drops important parts of my prompt") is the strongest evidence. Report 1's "Silent Fallback" anti-pattern aligns.
- **Cost-of-failure should determine response aggressiveness.** Report 3's spectrum table (seconds/cheap → let fail; hours/irreversible → hard block) provides the principled framework. Other reports agree implicitly but don't formalize it.

### 3.4 Goal-Oriented Onboarding

**High confidence:**

- **One question, not a wizard.** All reports agree that a single persona/goal selection question is sufficient and that multi-step onboarding forms cause abandonment. Report 3 cites Canva's growth to 10M users with a single question and research showing 80% abandonment on forced product tours.
- **The question should be skippable**, defaulting to an Explorer/freeform mode. [Reports 1, 3]
- **Goal changes must be seamless.** The pipeline graph naturally supports this—new stages become visible and available without resetting existing work. [All reports]
- **Templates help beginners; freeform helps experts.** Calibrate template prominence by persona. [Reports 1, 3, 4]

**Moderate confidence:**

- **Explorer mode should offer a pre-populated demo project** that serves as both tutorial and discovery mechanism (Notion's "Getting Started page is a Notion page" pattern). [Report 3; Report 1 mentions "Sample Data"]
- **Same data, different views** (Figma model at the view layer, Linear model at the data layer) is the right architecture for multi-persona support. [Report 3; Reports 1 and 2 describe this less precisely]

**Lower confidence:**

- **Five-layer AI autonomy spectrum** (Magic → Guided → Template → Copilot → Manual), selectable per-feature rather than globally, is a compelling framework from Report 3 but lacks empirical validation. It's theoretically sound and consistent with the "respect the expertise spectrum" principle, but implementation complexity is high. Consider starting with three levels (Automatic / Assisted / Manual) and expanding if user research warrants it.

### 3.5 Staleness and Version Management

**Moderate confidence (Reports 1, 3 agree; others touch on it lightly):**

- When upstream artifacts change, downstream artifacts should be flagged as **stale** (visually distinct state, e.g., yellow badge) but not deleted or auto-regenerated. The user decides when to regenerate. [Report 1 cites Houdini's dirty propagation; Report 3 describes this in the scenario walkthrough]
- The AI should surface staleness at workflow boundaries: "You changed the dialogue in Scene 3, so the storyboard is out of date. [Regenerate] [Keep Current]." [Reports 1, 3]

## 4. Conflict Resolution Ledger

| Claim | Report 1 | Report 2 | Report 3 | Report 4 | Adjudication | Confidence |
|---|---|---|---|---|---|---|
| **Mermaid is the best LLM graph representation** | "Mermaid is the standard" for LLMs; "token-efficient" | Mentions Mermaid alongside JSON, no strong preference | Mermaid is 24x more token-efficient than JSON but no single format dominates; recommends hybrid (JSON internal, NL for LLM context, Mermaid for chat) | JSON adjacency list ranked #1, Mermaid #2 | **Report 3's hybrid approach wins.** Report 1's claim that Mermaid is "the standard" is too strong—the "Talk like a Graph" paper shows representation choice is task-dependent. JSON is better for programmatic queries; NL descriptions work better for sparse graphs and reasoning; Mermaid excels for user-facing chat. Use all three for different purposes. | High |
| **Should the AI proactively surface missing steps?** | Only when user attempts a downstream action that requires the input | Proactively offer help "if it detects a missed prerequisite" but "only when it's obvious" | Proactive at workflow boundaries (52% engagement); never mid-task; user-controlled verbosity levels | "Proactive but dismissible nudges" | **Report 3's timing-based model wins** because it's the only one backed by empirical evidence (229 interventions, p=0.0016 difference). Proactive at workflow boundaries + when user triggers downstream action. Never mid-task. Calibrate to user expertise level. | High |
| **Should users be hard-blocked from skipping?** | Offers options (Auto-Generate, Go Fix, Use Placeholder)—no hard block mentioned | "Either disable a downstream step…or at least warn" | Hard block only when output would be meaningless; otherwise warn + proceed with placeholders | "Non-blocking warnings" | **Report 3's cost-of-failure spectrum is the principled answer.** Hard blocks only for truly meaningless output (no script at all). Yellow warnings + proceed-anyway for degraded quality. Green for complete upstream. Reports 1 and 4 effectively agree; Report 2 leans slightly more toward blocking but doesn't commit strongly. | High |
| **Multi-agent role coordination (AutoGen-style)** | Mentioned but not emphasized | Mentioned as a possibility; "could assign roles" | Not endorsed | Mentioned via CrewAI/LangGraph | **Defer.** Evidence for multi-agent systems improving creative pipeline outcomes (vs. a single AI with access to the graph) is speculative. The pipeline graph itself already encodes the "roles" as stage responsibilities. Start with a single AI assistant that can @-mention roles in responses (as CineForge already supports) and evaluate whether true multi-agent coordination adds value after launch. | Low |
| **Template vs. freeform balance** | Templates at project creation ("Project Goal" modal) | Templates as starting points, "Advanced users often want freeform" | Templates calibrated by persona (heavy for Producers, light for Screenwriters) | "Template gallery segmented by role" | **Report 3's persona-calibrated approach is most nuanced.** Templates should vary in prominence and depth by persona rather than being a one-size-fits-all gallery. Producers need structured templates; Screenwriters need format structure but never content templates; Directors need a mix. | Moderate |
| **Five AI autonomy levels vs. simpler model** | Not addressed | Not addressed | Five levels: Magic → Guided → Template → Copilot → Manual, per-feature | Three levels implied: Auto/Guided/Manual | **Start with three levels (Automatic / Assisted / Manual), per-feature.** Report 3's five-level model is theoretically sound but may over-complicate the UI. Three levels capture the critical distinction (full automation, collaborative, full control) without cognitive overload. Expand to five if user research reveals the middle levels are needed. | Moderate |

## 5. Decision Matrix

Evaluating the three core architectural approaches that emerged across reports:

| Criterion (Weight) | A: Pipeline Bar + On-Demand DAG + Conversational AI (Reports 1, 3, 4) | B: Full Node Graph Primary + Simplified View Toggle (Report 1 alt, ComfyUI model) | C: Linear Stepper + Chat (Simplified) |
|---|---|---|---|
| Serves all 4 personas (25%) | ★★★★★ Pipeline bar for ambient awareness; DAG for power users; chat for everyone | ★★★☆☆ Node graph intimidates Screenwriters/Producers | ★★☆☆☆ Constrains Directors/Explorers |
| Handles DAG (not just linear) (20%) | ★★★★★ DAG view explicitly shows parallel paths and fan-out/fan-in | ★★★★★ Node graph is native DAG | ★☆☆☆☆ Linear by definition |
| Supports goal evolution (15%) | ★★★★★ New stages appear in bar/DAG; no restart needed | ★★★★☆ Can add nodes, but overwhelming for users who started simple | ★★☆☆☆ Changing step order requires redesign |
| Scales to 30+ nodes (15%) | ★★★★☆ Semantic zoom + collapsible clusters + hover-to-trace | ★★★☆☆ Node spaghetti at scale (CircleCI problem) | ★★☆☆☆ 30-step wizard is unusable |
| AI can reason about it (15%) | ★★★★★ Graph representation feeds AI directly; chat is primary surface | ★★★★☆ Graph feeds AI, but AI must also explain visual layout | ★★★☆☆ AI can reason about linear sequence but not parallel options |
| Implementation complexity (10%) | ★★★☆☆ Three coordinated UI layers | ★★★★☆ Mostly one view + toggle | ★★★★★ Simple to build |
| **Weighted Total** | **4.5** | **3.6** | **2.2** |

**Architecture A is the clear winner.** It uniquely serves all personas, handles the DAG structure natively, and positions the conversational AI as the primary interaction surface—which is already CineForge's direction.

## 6. Final Recommendation

### The Four-Layer Navigation Architecture

CineForge should implement a four-layer navigation system, built incrementally:

**Layer 1 — The Persistent Pipeline Bar** (ship first)

A horizontal bar (bottom of screen, DaVinci Resolve-style) showing all pipeline phases as clickable tabs with three-state status indicators (green/highlighted/dimmed). Each tab shows a badge with completion metrics ("3/5 scenes extracted"). Clicking navigates to that phase's workspace. The bar adapts to persona: Screenwriter sees Script, Entities, and Analysis phases prominent; Director sees Visual Direction, Shot Plan, and Storyboard prominent. All phases remain accessible to all users.

**Layer 2 — The Conversational AI Navigator** (ship simultaneously with Layer 1)

The existing chat sidebar becomes the primary navigation intelligence. The AI reads the project's dependency graph (structured JSON) and:
- At **workflow boundaries** (stage completion): surfaces what's now unlocked and recommends 1-2 next steps
- At **downstream action triggers**: runs a preflight check and presents the tiered response (🟢/🟡/🔴)
- At **user request**: follows plan-then-execute pattern—presents structured plan before running expensive operations
- Follows the Make/TypeScript error message pattern: what's missing → what depends on it → suggested fix → escape hatch
- Provides three verbosity levels: Novice (explain everything at boundaries), Standard (flag critical issues), Expert (respond only when asked)

The AI's graph context should be scoped to the local subgraph (2-3 hops from the user's current focus), rendered as natural language in the system prompt, with the full graph available as structured JSON for programmatic tool calls.

**Layer 3 — The On-Demand DAG View** (ship in v2)

Accessible via keyboard shortcut (Tab or M) or a "Pipeline Map" button. Left-to-right DAG organized into phase columns with vertical stacking for parallel nodes. Implements:
- Three-state color coding (completed, available, blocked)
- Hover-to-trace (highlight upstream/downstream, dim everything else)
- Goal-backward navigation (click locked node → see prerequisite path → "Start this path" button)
- Semantic zoom (phase clusters at overview, individual nodes at detail)
- Search with highlight

**Layer 4 — Persona-Adaptive Workspaces** (evolve over time)

Each persona gets a purpose-built default workspace (Figma's multi-surface model) operating on shared project data (Linear's single-model approach):
- **Screenwriter**: script editor + entity browser + dialogue analysis
- **Director**: storyboard canvas + shot planner + mood boards + visual direction
- **Producer**: timeline + progress dashboard + resource overview
- **Explorer**: demo project + entry points into everything + template gallery

Three AI autonomy levels per feature: Automatic (AI handles it), Assisted (AI proposes, user approves), Manual (user does it, AI available on request).

### The Tiered Response System for Skipped Upstream

When a user triggers a downstream action:

1. **System checks the dependency graph** for the required and optional upstream artifacts
2. **Classifies the situation**:
   - 🟢 All required upstream complete → proceed silently
   - 🟡 Some upstream missing but output still meaningful → present warning card: "[Entity Bible for 'Detective Chen' not found. Storyboards will use a generic placeholder. [Create Bible Now] [Proceed with Placeholder]]"
   - 🔴 Critical upstream missing, output would be meaningless → soft block: "[No scenes extracted from screenplay. Scene extraction is required. [Extract Scenes Now]]"
3. **For expensive operations (render/export)**: always show pre-flight summary regardless of status: "12 scenes, 3 characters (2 with bibles, 1 placeholder), 4 locations (1 undescribed). Estimated quality: ★★★☆☆. [Fix Gaps] [Proceed]"
4. **For outputs produced with placeholders**: visibly mark every placeholder in the output (labeled silhouettes, bracketed text, pink-texture equivalent). Never auto-generate upstream content without marking it and making it trivially overridable.

### Onboarding Flow

1. Project creation → single question: "I'm a..." [Screenwriter / Director / Producer / Just Exploring] (skippable, defaults to Explorer)
2. Selection configures: default workspace, pipeline bar emphasis, AI personality and verbosity, template suggestions
3. Explorer gets a pre-populated demo project (the tutorial IS the product)
4. "Switch Role" always available in project settings; switching reconfigures the view without losing any artifacts

## 7. Implementation Plan / Next Steps

### Phase 1: Foundation (4-6 weeks)

1. **Define the canonical pipeline graph schema** as structured JSON: nodes (id, type, status, dependencies, outputs, staleness_timestamp, required_vs_optional), edges (source, target, data_type). This is the single source of truth.
2. **Implement the pipeline bar** with three-state indicators. Start with CineForge's ~10 core stages. Wire it to the graph schema so status updates are automatic.
3. **Build the AI's graph-reading capability**: tool call that queries the graph schema; system prompt template that renders the local subgraph (2-3 hops) as natural language; Mermaid rendering for chat responses.
4. **Implement the tiered response interceptor**: before any AI generation action, check upstream dependencies and classify as 🟢/🟡/🔴.

### Phase 2: Intelligence (4-6 weeks)

5. **Implement plan-then-execute for complex requests**: when a user asks for something requiring multiple pipeline stages, the AI presents a structured plan first.
6. **Build the pre-flight check UI** for expensive operations (render, export).
7. **Implement staleness propagation**: when an upstream artifact changes, mark downstream artifacts as stale with visual indicators and AI notifications at workflow boundaries.
8. **Add placeholder generation with visible marking** for 🟡 scenarios.

### Phase 3: Visualization & Personas (6-8 weeks)

9. **Build the on-demand DAG view** with hover-to-trace, goal-backward navigation, and semantic zoom.
10. **Implement persona-adaptive workspaces** and onboarding flow.
11. **Add per-feature AI autonomy levels** (start with three: Automatic / Assisted / Manual).
12. **Create the Explorer demo project**.

### Phase 4: Refinement (ongoing)

13. **User research on verbosity levels** and autonomy spectrum—expand to five levels if warranted.
14. **A/B test onboarding**: single persona question vs. behavior inference vs. template gallery first.
15. **Graph representation tuning**: measure AI accuracy with different encodings and optimize.

## 8. Open Questions & Confidence Statement

### High Confidence

- The four-layer architecture (pipeline bar, AI navigator, DAG view, persona workspaces) is the right structure. All four reports converge on it, and it's validated by patterns across CI/CD, creative tools, game tech trees, and project management.
- The three-tier response system (🟢/🟡/🔴) for skipped upstream is well-supported by evidence from build systems, render engines, and 3D printing slicers.
- Workflow-boundary timing for proactive AI guidance is empirically validated (Report 3's field study evidence).

### Moderate Confidence

- The specific graph representation strategy (JSON internal, NL for LLM context, Mermaid for chat) is well-reasoned but the "Talk like a Graph" research is from general LLM graph tasks, not creative pipeline navigation specifically. May need tuning.
- Three AI autonomy levels (Automatic / Assisted / Manual) per feature is a pragmatic starting point, but we don't know whether users will actually configure per-feature vs. just picking a global default.
- The persona-calibrated template strategy (heavy for Producers, light for Screenwriters) is logically sound but not empirically tested for creative film tools specifically.

### Open Questions

1. **How many nodes can the pipeline bar show before it needs grouping?** DaVinci Resolve has 7 pages; CineForge may need 10-15 top-level stages. Should the bar be hierarchical (phases → stages)?
2. **What is the right default for "proceed anyway" when upstream is missing?** Should 🟡 scenarios default to "show warning and wait for user action" or "proceed automatically with a toast notification"? This depends on how expensive the generation is and needs A/B testing.
3. **How should the AI explain quality estimates?** The "★★★☆☆" rating system in the pre-flight check is intuitive but arbitrary. What calibration method translates upstream completeness into a meaningful quality prediction?
4. **Will users actually use the DAG view?** It's the most expensive UI component to build. Consider validating demand with a simpler "dependency list" view first, then upgrading to a full graph if usage warrants it.
5. **How should the system handle collaborative multi-user scenarios?** Multiple personas working on the same project simultaneously (Screenwriter editing script while Director works on storyboards) introduces real-time staleness conflicts not addressed by any report.

### What We Don't Know

- No report provides direct user research from AI-powered film production tools (because the category barely exists). All analogies are cross-domain. Early user testing with CineForge prototypes is essential to validate these patterns in the specific creative filmmaking context.
- The five-layer AI autonomy model is theoretically compelling but entirely untested. It may be that users want a simpler binary ("AI helps" / "I do it myself") rather than a fine-grained spectrum.
- The optimal threshold between 🟡 (warn) and 🔴 (soft block) is not defined by any report and will need to be calibrated through iteration and user feedback.