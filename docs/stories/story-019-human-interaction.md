# Story 019: Human Control Modes and Creative Sessions

**Status**: To Do
**Created**: 2026-02-12
**Spec Refs**: 2.5 (Human Control Modes), 8.7 (Human Interaction Model)
**Depends On**: Story 014 (Role System Foundation), Story 015 (Director and Canon Guardians), Story 006 (Project Configuration)

---

## Goal

Implement non-CLI human interaction modes for CineForge, including interactive review/edit cycles and chat-mediated direction, while preserving immutable artifact versioning and explicit approval gates.

## Acceptance Criteria

### Interaction Modes
- [ ] Provide an interactive review experience beyond CLI file editing.
- [ ] Support web-based UI interactions for review/approval of generated artifacts.
- [ ] Support interactive chat with the Director role for guided decisions and revisions.

### Project Config Interaction (Moved from Story 006)
- [ ] Support interactive editing/confirmation of draft project configuration through web UI and/or Director chat flows.
- [ ] Preserve immutable artifact behavior: interactive edits produce new artifact versions rather than mutating existing snapshots.
- [ ] Ensure interaction mode behavior honors `human_control_mode` (`autonomous`, `checkpoint`, `advisory`).

### Auditability and Safety
- [ ] Every human intervention is captured in artifact metadata/audit history.
- [ ] Approval/rejection actions are explicit, replayable, and attributable.

## Tasks

- [ ] Design interaction contract for review/approve/reject/edit across UI/chat channels.
- [ ] Define artifact mutation policy for interactive edits (version bump + lineage updates).
- [ ] Implement Director chat interaction hooks for human decision points.
- [ ] Implement web UI workflow for reviewing and editing draft artifacts.
- [ ] Add integration tests for control-mode behavior across interactive channels.

## Work Log

### 20260212-1617 — Story scaffold created to absorb deferred interaction scope
- **Result:** Success.
- **Notes:** Added missing Story 019 file and moved deferred Story 006 requirement for future interaction modes (web UI + interactive Director chat config editing) into this story's acceptance criteria and tasks.
- **Next:** Implement Story 019 when role-system interaction infrastructure is in place.
