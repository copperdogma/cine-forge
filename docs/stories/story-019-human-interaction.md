# Story 019: Human Control Modes and Creative Sessions

**Status**: Done
**Created**: 2026-02-12
**Updated**: 2026-02-20
**Spec Refs**: 2.5 (Human Control Modes), 8.7 (Human Interaction Model), 21 (Operating Modes)
**Depends On**: Story 014 (role system foundation), Story 015 (Director and Canon Guardians), Story 017 (suggestion/decision tracking), Story 018 (inter-role communication), Story 011b (Operator Console — UI surface for interactions)

---

## Goal

Implement the three modes of human participation in CineForge: **approve/reject** (respond to AI proposals), **creative sessions** (collaborative chat with roles), and **direct artifact editing** (authoritatively change any artifact). All three produce new artifact versions, never in-place mutations.

This is where the human becomes the ultimate authority in the system — above even the Director AI.

---

## Acceptance Criteria

### Operating Modes (Spec 2.5, 21)
- [x] Three operating modes configurable per-project:
  - [x] **Autonomous**: pipeline runs fully, Director makes progression decisions, human reviews output.
  - [x] **Checkpoint**: pipeline pauses at each stage for human approval before proceeding.
  - [x] **Advisory**: human drives manually, AI provides feedback on request.
- [x] Mode is set in project configuration and can be changed at any time.
- [x] Mode affects:
  - [x] Whether Canon Guardian sign-offs require human confirmation.
  - [x] Whether the Director can auto-progress or must wait for approval.
  - [x] Whether suggestions are auto-applied or queued for review.

### Approve/Reject Flow
- [x] AI-generated artifacts are presented for human review.
- [x] Human can approve (artifact becomes canon) or reject (with feedback).
- [x] Rejection feedback is recorded and fed back to the producing role for revision.
- [x] Approval/rejection are explicit, replayable, and attributable in audit trail.
- [x] Bulk approval: human can approve multiple artifacts at once.

### Creative Sessions (Spec 8.7)
- [x] Human can open a conversation with any role or group of roles.
- [x] **@agent addressing**: human directs remarks to specific roles (@director, @visual_architect, etc.).
- [x] **Auto-inclusion**: when conversation touches another role's domain, that role is automatically brought in (Director coordinates).
- [x] **Selective silence**: agents only speak when they have relevant input or are directly addressed.
- [x] **Wandering scope**: conversation topics can shift freely; system adapts by including/releasing agents.
- [x] **Artifact proposals**: when conversation converges on something actionable, responsible agents propose artifact updates via suggestion system.
- [x] **Inline decisions**: human can accept, reject, or defer suggestions during the conversation.
- [x] All creative session transcripts recorded as immutable artifacts (per Story 018).

### Direct Artifact Editing (Spec 8.7)
- [x] Human can directly edit any artifact at any time.
- [x] Edit creates a new artifact version (immutability preserved).
- [x] Edit is immediately canon — no approval required from any role.
- [x] System notifies responsible agents and Director of the change.
- [x] Agents may attach commentary as suggestions (e.g., "this may conflict with scene 2 continuity").
- [x] Human can incorporate, defer, or ignore agent feedback on their edits.

### UI Integration
- [x] All interaction modes accessible through the Operator Console (Story 011b).
- [x] Approve/reject as one-click actions on artifact review screens.
- [x] Creative sessions as a chat interface with @agent mentions.
- [x] Direct editing as inline editors on artifact viewers.
- [x] All modes preserve audit trail and artifact versioning.

### Testing
- [x] Unit tests for operating mode behavior (autonomous, checkpoint, advisory).
- [x] Unit tests for approve/reject flow with audit recording.
- [x] Unit tests for creative session orchestration (@agent routing, auto-inclusion, selective silence).
- [x] Unit tests for direct edit → new version → agent notification flow.
- [x] Integration test: creative session → suggestion → approval → new artifact version.
- [x] Integration test: direct edit → notification → agent commentary.
- [x] Schema validation on all interaction artifacts.

---

## Design Notes

### Human Above Director
The spec is explicit: the human is above even the Director in the hierarchy. A human edit cannot be blocked by any role. Roles can comment, warn, and suggest alternatives — but they cannot prevent a human edit from taking effect.

### Creative Session Architecture
Creative sessions are the most complex interaction pattern. They combine real-time multi-role conversation with suggestion generation and inline decision-making. The key challenge is making this feel natural (a conversation) while maintaining the artifact discipline (everything is recorded, versioned, and auditable).

### Mode Transitions
The user should be able to change operating mode at any time without losing state. Switching from autonomous to checkpoint mid-pipeline should pause at the next stage, not retroactively require approval for already-processed stages.

---

## Tasks

- [x] Implement operating mode configuration and enforcement.
- [x] Implement approve/reject flow with audit recording.
- [x] Implement creative session infrastructure:
  - [x] @agent addressing and routing.
  - [x] Auto-inclusion logic (topic detection → role inclusion).
  - [x] Selective silence (relevance filtering).
  - [x] Suggestion proposal during conversation.
  - [x] Inline accept/reject/defer.
- [x] Implement direct artifact editing flow:
  - [x] Edit → new version → dependency propagation.
  - [x] Agent notification and commentary.
- [x] Implement mode transition logic (change mode mid-pipeline).
- [x] Wire all interaction modes into Operator Console API.
- [x] Write unit tests for all modes and flows.
- [x] Write integration tests for end-to-end interaction scenarios.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

### 20260212-1617 — Story scaffold created to absorb deferred interaction scope
- **Result:** Success.
- **Notes:** Added missing Story 019 file and moved deferred Story 006 requirement for future interaction modes (web UI + interactive Director chat config editing) into this story's acceptance criteria and tasks.
- **Next:** Implement Story 019 when role-system interaction infrastructure is in place.

### 20260213 — Story expanded with full spec coverage
- **Result:** Success.
- **Notes:** Expanded scaffold to cover all three human participation modes (approve/reject, creative sessions, direct editing), operating modes (autonomous/checkpoint/advisory), and spec 8.7 creative session details (@agent addressing, auto-inclusion, selective silence, wandering scope).
- **Next:** Implement when Stories 014-018 are complete.

### 20260220 — Full implementation and verification
- **Result:** Success.
- **Backend:** 
  - Implemented `human_control_mode` in `ProjectConfig`, `RunStartRequest`, and `ProjectSettingsUpdate`.
  - Integrated `CanonGate` into `DriverEngine` with support for "Checkpoint" mode pausing.
  - Added `talk_to_role` tool to chat assistant for multi-role addressing.
  - Implemented human-edit background notifications for agents.
  - Added `/api/runs/{id}/resume` and review response endpoints.
- **Frontend:**
  - Added Human Control Mode selector to Project Settings.
  - Implemented Project Inbox for pending reviews and suggestions.
  - Added one-click "Approve Stage" and "Resume Pipeline" actions.
  - Updated RunProgressCard to handle `paused` state.
- **Testing:**
  - Added unit tests for checkpointing, `talk_to_role`, and thread-safe logging.
  - Added integration tests for review sign-off and checkpoint-awaiting-user.
  - Verified multi-role chat and checkpoint pausing in the browser.
  - All 255 unit tests and 40 integration tests passed.
