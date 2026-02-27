# Story 090 — Persona-Adaptive Workspaces

**Priority**: Low
**Status**: Cancelled — Superseded by the two-view architecture (Story Explorer + Scene Workspace) combined with interaction mode (Story 089). The four personas (Screenwriter, Director, Producer, Explorer) each find their home in one or both views. See ADR-003 for the element grouping that replaces the direction architecture.
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation) — Layer 4
**Depends On**: Story 089 (interaction mode selection), Story 085 (pipeline capability graph)

## Goal

Implement the full persona-adaptive workspace system from ADR-002 Layer 4. Unlike Story 089's verbosity toggle (guided/balanced/expert), this story introduces *role-based personas* that change what the user sees and what the AI prioritizes.

ADR-002 envisions four personas:
- **Screenwriter** — Focused on script, characters, dialogue. Auto-runs normalization, pauses for creative direction. Hides production pipeline stages.
- **Director** — Full pipeline visibility. Creative direction is primary surface. Shot planning and storyboards prominent.
- **Producer** — Timeline, budget, schedule focus. Artifact health and staleness prominent. Less creative detail, more operational status.
- **Explorer** — Everything visible. No auto-actions. Full manual control. Good for learning the system.

Each persona adjusts:
1. **Pipeline bar visibility** — which phases/nodes are shown vs hidden
2. **AI autonomy per feature** — which actions auto-execute vs require confirmation
3. **Default navigation** — which page is "home" after opening a project
4. **System prompt framing** — AI speaks to the user's role and priorities

## Acceptance Criteria

### Persona Selection
- [ ] `persona` field in project settings (screenwriter / director / producer / explorer)
- [ ] Default is `explorer` (everything visible, no surprises)
- [ ] Persona selector in project settings (not in chat header — this is a heavier choice than interaction mode)
- [ ] Persona persists in project.json

### Pipeline Bar Filtering
- [ ] Each persona defines which pipeline phases are visible vs collapsed
- [ ] Screenwriter: Script + World prominent, Direction/Shots/Storyboards/Production collapsed
- [ ] Director: all phases visible, Direction phase highlighted
- [ ] Producer: all phases visible, status/health indicators enlarged
- [ ] Explorer: all phases visible (current default behavior)

### Per-Feature Autonomy
- [ ] Each persona defines autonomy levels per pipeline action (auto / confirm / hidden)
- [ ] Screenwriter: normalization=auto, world_building=confirm, creative_direction=confirm
- [ ] Director: all=confirm (wants oversight on everything)
- [ ] Producer: all=auto except creative_direction=confirm
- [ ] Explorer: all=confirm (manual control)
- [ ] Autonomy levels respected in `propose_run` and auto-insight triggers

### AI Prompt Framing
- [ ] System prompt includes persona-specific context beyond verbosity (role identity, priorities)
- [ ] Interaction mode (Story 089) and persona are orthogonal — a screenwriter can be in expert mode

### Testing
- [ ] Unit tests for persona→pipeline visibility filtering
- [ ] Unit tests for persona→autonomy level mapping
- [ ] Unit test for system prompt variation per persona

## Out of Scope
- Onboarding flow / persona quiz (future)
- Custom persona creation
- Per-scene persona switching
- Persona migration (changing persona doesn't re-run pipeline)

## Tasks

- [ ] Task 1: Define persona schema and configuration
- [ ] Task 2: Add persona to project settings (backend + API)
- [ ] Task 3: Pipeline bar filtering based on persona
- [ ] Task 4: Per-feature autonomy level enforcement
- [ ] Task 5: System prompt persona framing
- [ ] Task 6: Persona selector UI
- [ ] Task 7: Tests
- [ ] Task 8: Runtime smoke test

## Work Log

*(append-only)*

20260226 — Story created from ADR-002 alignment review. Story 089 delivered the lightweight verbosity toggle; this story delivers the full persona system (ADR-002 Layer 4).
