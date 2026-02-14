# Story 033: Memory Model and Transcript Retention

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 19 (Memory Model — full section), 8.6 (Conversation transcripts), 19.3 (Rule: chats are accelerators, artifacts are truth, transcripts are permanent)
**Depends On**: Story 018 (inter-role communication — conversation recording), Story 014 (role system — Director working memory)

---

## Goal

Implement the full **memory model**: canonical memory (artifacts, policies, decisions, suggestions, transcripts), working memory for long-running roles (Director, optionally Script Supervisor), and the transcript retention rule. Ensure that chats are accelerators, artifacts are truth, and transcripts are permanent.

---

## Acceptance Criteria

### Canonical Memory (Spec 19.1)
- [ ] All canonical memory types properly stored and queryable:
  - [ ] **Artifacts**: immutable, versioned (already implemented in Story 002).
  - [ ] **Policies**: project configuration, control mode.
  - [ ] **Decisions**: explicit decision artifacts with audit metadata (from Story 017).
  - [ ] **Suggestions**: full backlog with lifecycle status (from Story 017).
  - [ ] **Conversation transcripts**: raw turn-by-turn records (from Story 018).
- [ ] Canonical memory is the source of truth — roles consult it, not chat history.

### Working Memory (Spec 19.2)
- [ ] Long-running chat contexts for:
  - [ ] Director (required).
  - [ ] Script Supervisor (optional, configurable).
- [ ] Working memory capabilities:
  - [ ] Maintains running context across multiple interactions.
  - [ ] Periodically summarized into canonical artifacts.
  - [ ] Resettable (clear working memory, start fresh).
  - [ ] Summary artifacts are immutable.
- [ ] Raw transcripts always retained even when working memory is summarized or reset.

### Transcript Retention
- [ ] All conversation transcripts (role-to-role, human-to-role) retained permanently.
- [ ] Transcripts searchable by:
  - [ ] Participant roles.
  - [ ] Time range.
  - [ ] Related artifacts.
  - [ ] Content (full-text search).
- [ ] Transcripts linked to the decisions and artifacts they produced.

### Memory Query API
- [ ] Roles can query canonical memory:
  - [ ] "What decisions have been made about scene X?"
  - [ ] "What is the current state of character Y's bible?"
  - [ ] "What suggestions are deferred for location Z?"
  - [ ] "What did the Director and Visual Architect discuss about act 2?"
- [ ] Query results include provenance and timestamps.

### Schema
- [ ] `WorkingMemorySummary` schema.
- [ ] `TranscriptIndex` schema (searchable index of all transcripts).
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for working memory lifecycle (accumulate, summarize, reset).
- [ ] Unit tests for transcript retention and search.
- [ ] Unit tests for memory query API.
- [ ] Integration test: role conversations → transcript storage → search → retrieval.
- [ ] Schema validation on all outputs.

---

## Design Notes

### The Memory Rule (Spec 19.3)
"Chats are accelerators. Artifacts are truth. Transcripts are permanent."

This means:
- Roles should not rely on chat history for decision-making — they should consult artifacts.
- Working memory (chat context) is a performance optimization, not a source of truth.
- If working memory is lost (summarized, reset, context limit hit), no information is permanently lost — it's all in transcripts and artifacts.

### Storage Considerations
Transcripts will accumulate significantly over a project's lifetime. For MVP, file-based storage is fine. For larger projects, consider indexing with SQLite or similar for search performance.

---

## Tasks

- [ ] Implement canonical memory query interface.
- [ ] Implement working memory for Director role.
- [ ] Implement working memory summarization (periodic → canonical artifact).
- [ ] Implement working memory reset with transcript preservation.
- [ ] Implement transcript indexing and search.
- [ ] Implement memory query API for roles.
- [ ] Design and implement `WorkingMemorySummary`, `TranscriptIndex` schemas.
- [ ] Register schemas in schema registry.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
