# Story 023: Actor Agents and Performance Direction

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 10 (Performance System), 12.4 (Performance Direction), 10.2 (Governance — actor agents cannot modify canon)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews performance direction), Story 008 (character bibles), Story 010 (entity graph — relationship dynamics), Story 011 (continuity tracking — emotional/physical state entering scenes)

---

## Goal

Implement **Actor Agents** — one AI per character — that embody character psychology and produce **performance direction artifacts**. Each Actor Agent analyzes scenes from inside their character's role, suggesting motivation, subtext, dialogue alternatives, and behavioral consistency.

Actor Agents are the lowest tier in the role hierarchy. They suggest but cannot modify canon. Accepted insights may update character bibles.

---

## Acceptance Criteria

### Actor Agent System
- [ ] One Actor Agent instantiated per significant character (from character bible).
- [ ] Each Actor Agent:
  - [ ] Has a system prompt embodying their specific character's psychology, history, and personality.
  - [ ] Tier: performance.
  - [ ] Style pack slot (accepts acting methodology packs — e.g., "Daniel Day-Lewis").
  - [ ] Capability: `text`.
  - [ ] Cannot modify canon directly (spec 10.2).
  - [ ] Generates suggestions that, if accepted, may update character bibles.

### Performance Direction Artifacts (Spec 12.4)
- [ ] Per-scene, per-character direction including:
  - [ ] **Emotional state entering**: where the character is psychologically at scene start.
  - [ ] **Arc through the scene**: how emotional state changes (or doesn't).
  - [ ] **Motivation**: what the character wants in this scene.
  - [ ] **Subtext**: what they're not saying, what's beneath the surface.
  - [ ] **Physical notes**: posture, energy level, gestures, habits.
  - [ ] **Key beats**: moments of change, realization, decision.
  - [ ] **Relationship dynamics**: how this character relates to others in the scene (using entity graph).
  - [ ] **Dialogue delivery notes**: tone, pace, emphasis for specific lines.
- [ ] Reviewed by Director and Script Supervisor.
- [ ] All direction artifacts immutable, versioned, with audit metadata.

### Actor Agent Instantiation
- [ ] Automatic: when character bibles are created (Story 008), Actor Agents are instantiated for primary and supporting characters.
- [ ] Agent prompt is constructed from character bible content + entity graph relationships + style pack.
- [ ] Agent prompt updates when character bible is updated (new version).

### Performance Direction Module
- [ ] Module directory: `src/cine_forge/modules/creative_direction/performance_direction_v1/`
- [ ] Reads scene artifacts, character bibles, entity graph, and continuity states (for emotional/physical state entering each scene).
- [ ] Invokes each Actor Agent for scenes where their character appears.
- [ ] Outputs one performance direction artifact per character per scene.

### Schema
- [ ] `PerformanceDirection` Pydantic schema with all fields from spec 12.4.
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for Actor Agent instantiation from character bibles.
- [ ] Unit tests for performance direction generation (mocked AI).
- [ ] Unit tests for governance (cannot modify canon, suggestions only).
- [ ] Integration test: character bibles + scenes → performance direction artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### One Agent Per Character
Each character gets their own Agent instance with a unique system prompt built from their bible. This means character-specific reasoning — the Agent for a villain thinks differently than the Agent for a hero. The style pack adds methodology (method acting vs. classical technique) on top of character-specific psychology.

### Suggestion Flow
Actor Agents can't change anything directly. When an Agent notices something (e.g., "my character wouldn't say this line"), it generates a suggestion via Story 017. If the Director or human accepts the suggestion, it produces a new artifact version. This keeps the Actor Agent useful without giving it authority to break consistency.

---

## Tasks

- [ ] Implement Actor Agent instantiation logic (from character bibles).
- [ ] Implement per-character system prompt construction.
- [ ] Design and implement `PerformanceDirection` schema.
- [ ] Register schema in schema registry.
- [ ] Create `performance_direction_v1` module.
- [ ] Implement performance direction generation per character per scene.
- [ ] Implement governance constraints (suggestions only, no canon modification).
- [ ] Implement bible-based prompt updates.
- [ ] Wire into creative direction recipe.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
