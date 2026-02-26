---
type: research-prompt
topic: "goal-oriented-navigation"
created: "2026-02-25"
---

# Research Prompt: Goal-Oriented Navigation for AI-Powered Creative Pipelines

## Context

CineForge is a film pre-production and production tool powered by AI. It has a deep pipeline: script ingestion → normalization → scene extraction → entity bibles (characters, locations, props) → creative direction (editorial, visual, sound) → direction convergence → shot planning → storyboards → render → final output.

Each stage produces versioned, immutable artifacts. Downstream stages consume upstream artifacts. The system uses AI roles (Director, Editorial Architect, Visual Architect, Sound Designer, Story Editor) that provide creative input at various stages.

**The design problem:** Different users want different things from this pipeline:
- A screenwriter just wants script analysis (characters, scenes, relationships). They stop after entity extraction.
- A director wants full pre-production: creative direction, shot plans, storyboards.
- A producer wants to upload a script and get a finished film with minimal input.
- An explorer wants to try features, change their mind, and go deeper when something interests them.

Today the app surfaces capabilities as buttons scattered across pages ("Get Editorial Direction" on a scene page). There's no unified view of what's been done, what's next, or what the user's goal is. When a user triggers a downstream capability (e.g., render a scene) without having done upstream work (e.g., visual direction, sound design), the output is bad — and neither the user nor the AI assistant can explain why or how to fix it.

We need a system that:
1. Represents the full pipeline as a navigable structure the user can see and the AI can reason about
2. Adapts to the user's stated or inferred goal
3. Shows progress, surfaces next steps, and diagnoses problems when downstream output is poor
4. Supports goal evolution — users who start with "just analyze" and later want storyboards
5. Doesn't force users through a wizard or block them from jumping ahead

The app has a conversational AI chat as the primary interaction surface. Users can @-mention AI roles and their screenplay's characters. The AI can read project state (which artifacts exist, their health/staleness).

## What I Need

### 1. Multi-Stage Creative Tool UX Patterns

Survey how existing creative production tools handle multi-stage workflows with optional steps:

- **AI video tools** (Runway Gen-3/4, Kling, Pika, Luma, Sora): How do they handle multi-step workflows (text → image → video → editing)? Do they have a pipeline concept? How do users know what to do next? How do they handle "you skipped a step"?
- **Traditional NLEs and VFX tools** (DaVinci Resolve, Adobe Premiere, Nuke, Houdini): How do node-based/stage-based tools surface dependencies and progress? What can we steal from node graph UIs?
- **Game engines** (Unreal Engine, Unity): How do they handle asset pipelines with dependencies (texture → material → mesh → scene)? How do they surface "this asset is missing a dependency"?
- **Music production** (Ableton, Logic Pro): How do multi-track, multi-stage workflows guide users from idea to finished product?

For each, identify:
- How is progress made visible?
- How are dependencies communicated?
- What happens when a user skips ahead?
- How do power users vs. beginners experience the same tool?

### 2. Dependency-Aware Progress UI Patterns

Research the best UX patterns for showing progress through a dependency graph (not a linear sequence):

- **CI/CD pipeline UIs** (GitHub Actions, GitLab CI, CircleCI): How do they visualize parallel stages with dependencies? What works and what doesn't?
- **Tech trees in games** (Civilization, Factorio, skill trees in RPGs): How do they show "you can unlock this if you do these prerequisites first"? What makes a tech tree feel empowering rather than gatekeeping?
- **Project management tools** (Linear, Notion, Asana, Monday): How do they handle dependency-aware task boards? What about "blocked" states?
- **Wizard/stepper UIs** (Stripe onboarding, Vercel deployment, Shopify setup): How do multi-step setup flows handle optional steps, skipping, and revisiting?

I'm specifically interested in patterns that:
- Work for DAGs (directed acyclic graphs), not just linear sequences
- Show both "what's done" and "what's possible"
- Handle optional vs. required steps
- Allow jumping to any node while showing prerequisites
- Scale from 5 nodes to 30+ without becoming overwhelming

### 3. AI Reasoning Over Dependency Graphs

How should an AI assistant reason about a capability graph to provide useful guidance?

- What graph representations are most LLM-friendly? (Adjacency lists, natural language descriptions, structured JSON, Mermaid diagrams?)
- How do AI coding assistants (Cursor, Claude Code, Copilot) handle multi-step task planning? Any patterns for "you need to do X before Y"?
- Research on AI agents and planning: how do agents like AutoGPT, CrewAI, or LangGraph decompose goals into prerequisite steps?
- How should the AI explain "why is this output bad?" in terms of a dependency graph? What's the right level of detail vs. overwhelming the user?
- Should the AI proactively surface "you're missing X" or wait until asked? What's the right balance between helpful guidance and annoying nagging?

### 4. Goal-Oriented Onboarding for Multi-Persona Tools

Research how tools with multiple user types handle the "what do you want to do?" question:

- **Canva**: designers vs. social media managers vs. students — how does it route users?
- **Figma**: designers vs. developers vs. stakeholders — different entry points, same tool
- **Notion**: notes vs. project management vs. docs — template gallery as entry point
- **Linear**: IC engineers vs. managers vs. execs — how does it handle different workflows?

Specific questions:
- Is goal selection at onboarding worth the friction? Or should the tool infer from behavior?
- How do tools handle goal CHANGES? ("I started with X but now I want Y")
- What's the best pattern for "I don't know what I want yet — let me explore"?
- Templates vs. freeform: when do templates help vs. constrain?
- How do the best tools handle the spectrum from "do everything for me" to "I want full control"?

### 5. The "Skipped Upstream" Problem in Production Tools

Research how creative and engineering tools handle the specific problem of "user triggered a downstream capability without doing upstream work":

- **Render engines**: What happens when you render a scene with missing textures or unresolved references? Warning, block, or fallback?
- **Compilers/build systems**: How do build tools communicate "this target depends on X which hasn't been built"? What error UX works?
- **AI image generation**: When Midjourney/DALL-E output is bad because the prompt was underspecified, how do users learn to improve? Is there guidance, or just iteration?
- **3D printing slicers**: How do they warn about unsupported geometry or missing parameters before committing to a long print?

I'm looking for:
- Do tools block, warn, or let you fail and diagnose?
- Which approach leads to better user outcomes?
- How do tools explain what went wrong in terms of upstream dependencies?
- What's the right balance: never letting users make mistakes vs. learning by doing?

## Output Format

For each category, provide:
1. **Recommended patterns** with reasoning — what should CineForge adopt?
2. **Anti-patterns** — what looks tempting but fails in practice?
3. **Specific examples** with screenshots/descriptions where possible
4. **Evidence** — links, case studies, user research, community sentiment
5. **Synthesis** — how do the patterns across categories combine into a coherent system?
