# Story 099: Scene Workspace

**Status**: Pending
**Created**: 2026-02-27
**Source**: ADR-003, Ideal R11
**Spec Refs**: 12.7 (Readiness Indicators)
**Ideal Refs**: R11 (production readiness per scene), R7 (iterative refinement)
**Depends On**: Story 094 (concern group schemas), Story 095 (intent/mood layer), Story 085 (pipeline graph)

---

## Goal

Build the **Scene Workspace** — the per-scene production control surface (View 2 in the two-view architecture from ADR-002). Shows five concern group tabs (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World) with red/yellow/green readiness indicators per group. This is where filmmakers do their creative work.

## Why (Ideal Alignment)

R11: "The system must show production readiness per scene." The Scene Workspace is the primary realization of this requirement — for every scene, users see what's specified, what AI has inferred, and what's completely missing. The five concern group tabs (from ADR-003) organize the ~87 creative elements into navigable groups.

The Ideal says CineForge should feel like a creative conversation. The Scene Workspace is where that conversation happens — each concern group is an invitation to explore, refine, or leave to AI.

## Acceptance Criteria

- [ ] Per-scene view with five concern group tabs
- [ ] Each tab shows: specified elements (user input), AI-inferred elements (yellow), missing elements (red)
- [ ] Summary bar: five colored indicators per scene showing readiness at a glance
- [ ] Intent/Mood controls at the top (project-wide or per-scene override)
- [ ] "Let AI fill this" button per concern group (generates missing elements)
- [ ] "Generate scene" button that runs the full film-lane pipeline for this scene, flagging or auto-generating missing upstream
- [ ] Links to entity detail pages for characters/locations/props referenced in the scene
- [ ] Preview panel: best available representation of the scene (text → storyboard → animatic → video)

## Relationship to ADR-002

ADR-002 defined the two-view architecture: Story Explorer (existing) + Scene Workspace (this story). The Scene Workspace was described as an inbox item; this story makes it concrete using the concern group structure from ADR-003.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation. Scene Workspace concept from inbox + ADR-002 + ADR-003 concern groups.
