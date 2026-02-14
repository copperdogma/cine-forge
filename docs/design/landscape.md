# UI Landscape & Design Inspiration

**Status**: Not yet researched
**Method**: Deep research (`deep-research init ui-landscape`)

---

## Purpose

Survey creative tools, pipeline UIs, and artifact browsers to find interaction patterns worth stealing. This is not competitive analysis — CineForge is not a product competing in a market. The goal is to find good ideas and design paradigms that make the CineForge UI feel intuitive and polished.

## Research Questions

### Creative Tool UX Patterns
- What do the best creative tools (Figma, Linear, Arc Studio Pro, Highland) do for progressive disclosure? How do they balance simplicity with depth?
- How do AI creative tools (Runway, Midjourney, Pika, Kling, Kaiber) present AI-generated output for review/approval? What makes "accept this AI suggestion" feel good?
- What onboarding patterns work for tools where the user has a file and wants to see it transformed? (Think Canva's "upload and go" vs. Figma's blank canvas.)

### Pipeline & DAG Visualization
- How do pipeline tools (Dagster, Prefect, n8n, Apache Airflow) visualize stage progress, success/failure, and data flow?
- What patterns work for showing "this stage produced these artifacts, which fed into this stage"?
- How do version-control UIs (GitHub, GitKraken) present version history, diffs, and lineage?

### Artifact Browsing & Inspection
- What do structured data browsers (JSON viewers, API explorers, database GUIs) do well?
- How do document/content management tools present version history with meaningful diffs?
- What patterns exist for "show me the summary, let me drill into the detail"?

### Film/Production Tool Patterns
- How do production management tools (Frame.io, Shotgrid, StudioBinder, Celtx) organize project assets?
- What do screenwriting tools (Highland, Final Draft, WriterSolo) do for script presentation and navigation?
- How do storyboarding tools (Storyboarder, Boords) present sequential visual content?

## Expected Output

A document with:
- Annotated screenshots or descriptions of the best patterns found
- Specific interaction paradigms to adopt (with rationale)
- Anti-patterns to avoid (with examples of why they fail)
- A short "design direction" synthesis: what CineForge should feel like, informed by the landscape

## Deep Research Prompt Guidance

When running this research, the prompt should emphasize:
- Visual quality and interaction feel, not feature checklists
- Patterns that work for non-expert users doing complex tasks
- How tools handle the transition from "autopilot" to "I want to control this one thing"
- Real examples with specific tool names, not generic UX advice
