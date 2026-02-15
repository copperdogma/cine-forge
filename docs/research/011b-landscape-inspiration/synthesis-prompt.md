---
type: synthesis-prompt
topic: "011b-landscape-inspiration"
created: "2026-02-15T04:21:30.303853+00:00"
auto-generated: true
---

# Synthesis Prompt

You are acting as lead research editor. Your task is to read multiple independent research reports on the same topic, reconcile them, and produce one final, implementation-ready synthesis.

## Research Context

You are conducting deep UX/UI research for CineForge, an AI-first film production pipeline tool. CineForge takes a user's screenplay, runs it through AI-powered pipeline stages (ingest, normalize, scene extraction, character bibles, entity graphs, continuity tracking), and produces structured, versioned artifacts. The user is a storyteller with no film production background.

We are building the Operator Console — a production-quality UI that must feel like a creative tool, not a developer dashboard. The primary interaction model is:
- Drag in a script → AI does everything → user approves → artifacts appear
- Progressive disclosure: summary by default, infinite depth on demand
- Override anywhere: user can take control of any single decision, then return to autopilot
- Artifact-centric: the UI is organized around what was produced (scripts, scenes, bibles), not how (pipeline stages, module names)

**Your job: survey existing tools and identify specific interaction patterns, visual design approaches, and UX paradigms that CineForge should steal, adapt, or avoid.**

## Research Areas (answer ALL)

### 1. Creative Tool UX Patterns
- How do the best creative tools handle progressive disclosure? Examine specific tools: Figma (layers of detail), Linear (task → detail expansion), Arc Studio Pro (screenplay navigation), Highland (distraction-free writing with inspector), Notion (page nesting, toggles, databases).
- How do AI creative tools present AI-generated output for human review/approval? Examine: Runway (Gen-3/Gen-4 output review), Midjourney (grid → upscale → variation workflow), Pika, Kling, Kaiber, ElevenLabs (voice generation preview).
- What makes "accept this AI suggestion" feel good vs. feel scary? Specific examples of tools that do this well and tools that do it badly.
- What onboarding patterns work for "I have a file, transform it for me"? (Canva upload-and-go, Google Docs import, Descript transcript-first workflow.)

### 2. Pipeline & Workflow Visualization
- How do pipeline/DAG tools visualize stage progress and data flow? Examine: Dagster (asset-centric UI), Prefect (flow runs), n8n (visual workflow builder), Apache Airflow (tree/graph/gantt views), Retool Workflows, Temporal UI.
- What patterns work for showing "this stage produced these artifacts, which fed into this stage"? Lineage/provenance visualization.
- How do CI/CD tools (GitHub Actions, GitLab CI, Vercel) show build progress with expandable logs?
- What works for real-time progress indication during long-running AI tasks (30s–5min per stage)?

### 3. Artifact Browsing & Inspection
- What do structured data browsers do well? Examine: Postman (API response viewer), MongoDB Compass (document viewer), Prisma Studio (database browser), jq playground (JSON drill-down).
- How do document/content management tools present version history with meaningful diffs? Examine: Google Docs (version history sidebar), Notion (page history), GitHub (file diff with blame), Figma (version history with visual snapshots).
- What patterns exist for "show me the summary, let me drill into the detail"? Master-detail views, expandable cards, slide-over panels, modal drill-downs.

### 4. Film & Production Tool Patterns
- How do production management tools organize project assets? Examine: Frame.io (media review + comments), ShotGrid (production tracking), StudioBinder (breakdowns, shot lists, stripboards), Celtx (screenplay + pre-production), ftrack.
- What do screenwriting tools do for script presentation and navigation? Examine: Highland 2 (minimal UI, index cards), Final Draft (industry standard layout), Arc Studio Pro (beat board, outline, script views), WriterSolo, Fade In.
- How do storyboarding tools present sequential visual content? Examine: Storyboarder (sketch + shot flow), Boords (frame grid + animatic), FrameForge (3D previsualization).

### 5. Design Direction Synthesis
Based on all the above, answer:
- What should CineForge's visual personality be? (Warm creative tool? Clean productivity app? Cinematic dark theme? Something else?) Give 2–3 specific reference points.
- What is the single most important interaction pattern to get right for "drag in script → see results"?
- What are the top 3 anti-patterns to avoid? (With specific examples of tools that made these mistakes.)
- How should the artifact browser work — cards, tree, list, or something else? What mental model serves "a project's creative output" best?

## Output Format
Structure your response with clear headings matching the research areas above. For each pattern you recommend, name the specific tool and describe what it does (not just "Figma does progressive disclosure well" — explain the specific mechanism). Include anti-patterns with explanations. End with a concrete "design direction" section.

## Reports to Synthesize

You will receive 3 research reports, each produced by a different AI model. Each report covers the same research question from the instructions above.

## Your Synthesis Goals

1. Grade each source report on quality: evidence density, practical applicability, specificity, and internal consistency (0–5 scale for each, with a one-paragraph critique).
2. Extract key claims by topic area.
3. Identify where reports agree (high confidence) vs. disagree (needs adjudication).
4. Resolve contradictions with explicit reasoning — evaluate the strength of each report's evidence, not majority vote.
5. Separate "proven / high confidence" from "promising but uncertain."
6. Produce one concrete recommendation, not a menu of options.
7. If one report is clearly higher quality, weight it accordingly and say why.

## Required Output Format

Begin your response with:

---
canonical-model-name: "{the product name you are — e.g., chatgpt, claude, gemini, grok — lowercase, no version numbers}"
report-date: "{today's date in ISO 8601}"
research-topic: "011b-landscape-inspiration"
report-type: "synthesis"
---

Then produce the following sections:

1. **Executive Summary** (8–12 bullets)
2. **Source Quality Review** (table with scores + short commentary per report)
3. **Consolidated Findings by Topic**
4. **Conflict Resolution Ledger** (claim, conflicting views, final adjudication, confidence level)
5. **Decision Matrix** (if applicable — weighted, with scoring rationale)
6. **Final Recommendation** (concrete, with rationale)
7. **Implementation Plan / Next Steps** (if applicable)
8. **Open Questions & Confidence Statement**

## Quality Instructions

- Be concrete and specific, not generic.
- Clearly label assumptions and uncertainty.
- Prefer practical reliability over novelty.
- If evidence is weak across all reports, say so — do not manufacture false confidence.
- Do not simply merge or average — adjudicate.
- Note which report(s) contributed each key finding.
