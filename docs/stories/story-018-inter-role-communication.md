# Story 018: Inter-Role Communication Protocol

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 8.6 (Inter-Role Communication and Disagreement Protocol), 19 (Memory Model — conversation transcripts), 20 (Metadata & Auditing)
**Depends On**: Story 014 (role system foundation), Story 015 (Director and Canon Guardians), Story 017 (suggestion/decision tracking)

---

## Goal

Implement the inter-role communication protocol: how roles talk to each other, how conversations are recorded, how disagreements are handled, and how all of this feeds into the audit trail. Every piece of inter-role communication is recorded as an immutable artifact.

---

## Acceptance Criteria

### Conversation Recording (Spec 8.6)
- [x] All inter-role communication recorded as immutable conversation artifacts:
  - [x] Raw turn-by-turn transcripts.
  - [x] Linked to the decisions they produced.
  - [x] Linked to the artifacts they discuss.
- [x] Conversation transcripts retained in full (spec: "storage is cheap; forensic, educational, and creative-archaeological value is high").

### Disagreement Protocol Infrastructure
- [x] General-purpose disagreement recording infrastructure:
  - [x] Objection recorded as an artifact (not silently discarded).
  - [x] Override rationale recorded as a linked artifact.
  - [x] Both positions linked to affected artifacts and to each other.
  - [x] Override chain visible: user can see the full disagreement and resolution history.
- [x] Note: Story 015 defines the *rules* for Director/Guardian disagreements (who can override whom). This story provides the *infrastructure* for recording any inter-role disagreement. The same infrastructure is used by Story 019 for human-role disagreements.

### Conversation Orchestration
- [x] Multi-role conversations supported:
  - [x] Director can convene multiple roles for a review discussion.
  - [x] Roles respond when they have relevant input.
  - [x] Conversations produce decisions and/or suggestions as outcomes.
- [x] Selective participation: roles only speak when the topic falls within their authority or they're directly addressed.

### Conversation Artifacts
- [x] `Conversation` schema:
  ```python
  class ConversationTurn(BaseModel):
      role_id: str
      content: str
      timestamp: datetime
      references: list[ArtifactRef]

  class Conversation(BaseModel):
      conversation_id: str
      participants: list[str]
      topic: str
      related_artifacts: list[ArtifactRef]
      turns: list[ConversationTurn]
      outcome_decisions: list[str]     # Decision artifact IDs
      outcome_suggestions: list[str]   # Suggestion artifact IDs
      created_at: datetime
  ```
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for conversation recording and retrieval.
- [x] Unit tests for disagreement protocol (objection, override, dual preservation).
- [x] Unit tests for multi-role conversation orchestration.
- [x] Integration test: multi-role discussion → disagreement → override → artifacts recorded.
- [x] Schema validation on all outputs.

---

## Design Notes

### Conversations as Artifacts
Conversations are not ephemeral chat logs — they're first-class artifacts. A Director should be able to revisit past conversations to understand the chain of thought behind any decision. This means conversations are versioned, searchable, and linked to the artifacts they produced.

### Working Memory (Spec 19.2)
Long-running chats are allowed only for the Director (and optionally Script Supervisor). They're periodically summarized into artifacts. Raw transcripts are always retained even when working memory is summarized or reset. The full memory model is Story 033 — this story handles the communication infrastructure.

---

## Central Tenets Check

- [x] **Tenet 0 — Preserve user data / capture-first**: All transcripts and disagreements are recorded as immutable versioned artifacts.
- [x] **Tenet 1 — AI-friendly architecture**: Schemas provide structured turn-by-turn history for roles to reference.
- [x] **Tenet 2 — Avoid over-engineering**: Kept orchestration simple (convener → participants → synthesizer) while providing rich audit trails.
- [x] **Tenet 3 — Keep files manageable / types centralized**: Isolated communication logic in `src/cine_forge/roles/communication.py` and schemas in `src/cine_forge/schemas/conversation.py`.
- [x] **Tenet 4 — Verbose handoff log**: Work log entries capture implementation details and verification evidence.
- [x] **Tenet 5 — Simplify toward ideal**: Reused existing role invocation flow to capture suggestions automatically.

---

## Tasks

- [x] Design and implement `Conversation`, `ConversationTurn` schemas.
- [x] Register schemas in schema registry.
- [x] Implement conversation recording and storage.
- [x] Implement disagreement protocol with dual-position preservation.
- [x] Implement multi-role conversation orchestration.
- [x] Implement conversation-to-artifact linking (decisions, suggestions).
- [x] Wire communication into role invocation flow.
- [x] Write unit tests for all components.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*

20260220-1530 — implementation complete: added `Conversation`, `ConversationTurn`, and `DisagreementArtifact` schemas; implemented `ConversationManager` for orchestrating and recording multi-role review discussions; updated `RoleContext` to track and return `suggestion_ids` for linking to conversations; added disagreement recording with dual-position preservation; evidence=`src/cine_forge/schemas/conversation.py`, `src/cine_forge/roles/communication.py`, `src/cine_forge/roles/runtime.py`.

20260220-1545 — verification complete: added unit tests for conversation lifecycle, disagreement recording, and multi-role orchestration; added integration test for full disagreement-to-conversation lifecycle; verified all tests pass and lint is clean; evidence=`tests/unit/test_communication.py`, `tests/integration/test_communication_integration.py`.
