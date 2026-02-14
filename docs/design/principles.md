# CineForge UI Design Principles

These principles govern every UI surface in CineForge. They are derived from the product specification and the project's core values. Every UI story should reference this document.

---

## 1. Zero-Effort Default Path

The most common workflow — "I have a script, I want a film" — should require near-zero configuration. Drag in a file, click OK a few times, get artifacts. Every screen must have an obvious default action. If the user has to think about what to do next, the UI has failed.

- AI fills in every field it can. The user's job is to approve, not to author.
- Defaults are opinionated and good, not neutral and empty.
- The first run of a new project should take under 60 seconds of user attention.

## 2. AI-First, Human-Guided

AI does the work. The human steers.

- Every pipeline stage runs autonomously by default. The user intervenes only when they want to, or when the AI is uncertain.
- AI suggestions are presented with one-click approval. Saying "yes" should be frictionless; saying "no" or "change this" should be easy.
- When AI confidence is low, the UI surfaces this clearly — don't hide uncertainty behind clean layouts.

## 3. Progressive Disclosure

Simple by default, infinitely deep on demand.

- The top-level view of any artifact is a summary: title, status, confidence, one-line description.
- Clicking in reveals the full artifact, metadata, lineage, QA results.
- Clicking deeper reveals raw JSON, cost data, agent reasoning transcripts.
- The user who wants to drag-and-drop and the user who wants to read every decision chain both use the same UI — they just go to different depths.

## 4. Artifact-Centric

Artifacts are the primary objects in the UI, not pipeline stages or module names.

- Navigation should be organized around what was produced (scripts, scenes, bibles, configs), not how it was produced (ingest, normalize, extract).
- Every artifact is inspectable: content, metadata, version history, lineage graph, QA results, cost.
- Artifact viewers should be type-aware: screenplay text gets a script viewer, structured data gets a structured viewer, graphs get a graph viewer. Raw JSON is always available but never the default.

## 5. Override Anywhere

At any point, the user can take control of a specific decision, then step back and let AI continue.

- Overriding one field in a project config doesn't require re-running the entire pipeline.
- Editing an artifact creates a new version (immutability preserved) and marks downstream artifacts as stale.
- The UI must make it clear what the user changed vs. what the AI produced — both for trust and for debugging.
- After an override, returning to autopilot should be one action, not a multi-step process.

## 6. Transparency Without Noise

The system explains itself, but doesn't shout.

- Every AI decision has a rationale accessible on demand (spec 2.6), but it's not displayed by default.
- Cost tracking (spec 2.7) is visible but unobtrusive — a running total, not a per-call alert.
- QA results are surfaced as health indicators (green/yellow/red), with details on click.
- Agent disagreements (spec 8.6) are preserved and browsable, but don't interrupt flow unless the user is in checkpoint mode.

## 7. State Is Always Clear

The user should never wonder "what happened?" or "what do I do next?"

- Pipeline progress is visible at a glance: which stages ran, which are pending, which failed.
- Artifact health (valid, stale, needs_review) is shown inline with clear visual indicators.
- The difference between a draft and a confirmed artifact is obvious.
- Error states include remediation guidance, not just error messages.
