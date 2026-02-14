# Story 018: Inter-Role Communication Protocol

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.6 (Inter-Role Communication and Disagreement Protocol), 19 (Memory Model — conversation transcripts), 20 (Metadata & Auditing)
**Depends On**: Story 014 (role system foundation), Story 015 (Director and Canon Guardians), Story 017 (suggestion/decision tracking)

---

## Goal

Implement the inter-role communication protocol: how roles talk to each other, how conversations are recorded, how disagreements are handled, and how all of this feeds into the audit trail. Every piece of inter-role communication is recorded as an immutable artifact.

---

## Acceptance Criteria

### Conversation Recording (Spec 8.6)
- [ ] All inter-role communication recorded as immutable conversation artifacts:
  - [ ] Raw turn-by-turn transcripts.
  - [ ] Linked to the decisions they produced.
  - [ ] Linked to the artifacts they discuss.
- [ ] Conversation transcripts retained in full (spec: "storage is cheap; forensic, educational, and creative-archaeological value is high").

### Disagreement Protocol Infrastructure
- [ ] General-purpose disagreement recording infrastructure:
  - [ ] Objection recorded as an artifact (not silently discarded).
  - [ ] Override rationale recorded as a linked artifact.
  - [ ] Both positions linked to affected artifacts and to each other.
  - [ ] Override chain visible: user can see the full disagreement and resolution history.
- [ ] Note: Story 015 defines the *rules* for Director/Guardian disagreements (who can override whom). This story provides the *infrastructure* for recording any inter-role disagreement. The same infrastructure is used by Story 019 for human-role disagreements.

### Conversation Orchestration
- [ ] Multi-role conversations supported:
  - [ ] Director can convene multiple roles for a review discussion.
  - [ ] Roles respond when they have relevant input.
  - [ ] Conversations produce decisions and/or suggestions as outcomes.
- [ ] Selective participation: roles only speak when the topic falls within their authority or they're directly addressed.

### Conversation Artifacts
- [ ] `Conversation` schema:
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
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for conversation recording and retrieval.
- [ ] Unit tests for disagreement protocol (objection, override, dual preservation).
- [ ] Unit tests for multi-role conversation orchestration.
- [ ] Integration test: multi-role discussion → disagreement → override → artifacts recorded.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Conversations as Artifacts
Conversations are not ephemeral chat logs — they're first-class artifacts. A Director should be able to revisit past conversations to understand the chain of thought behind any decision. This means conversations are versioned, searchable, and linked to the artifacts they produced.

### Working Memory (Spec 19.2)
Long-running chats are allowed only for the Director (and optionally Script Supervisor). They're periodically summarized into artifacts. Raw transcripts are always retained even when working memory is summarized or reset. The full memory model is Story 033 — this story handles the communication infrastructure.

---

## Tasks

- [ ] Design and implement `Conversation`, `ConversationTurn` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement conversation recording and storage.
- [ ] Implement disagreement protocol with dual-position preservation.
- [ ] Implement multi-role conversation orchestration.
- [ ] Implement conversation-to-artifact linking (decisions, suggestions).
- [ ] Wire communication into role invocation flow.
- [ ] Write unit tests for all components.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
