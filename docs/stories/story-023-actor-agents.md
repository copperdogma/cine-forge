# Story 023: Character & Performance — Performance Direction

**Status**: Draft
**Created**: 2026-02-13
**Rewritten**: 2026-02-25 — Original scope largely superseded by Story 084.
**Reshaped**: 2026-02-27 — ADR-003 reorganizes direction types into concern groups. Performance direction → Character & Performance concern group.
**Spec Refs**: 12.5 (Character & Performance)
**Depends On**: Story 008 (character bibles), Story 005 (scene extraction), Story 010 (entity graph), Story 011 (continuity tracking)
**Ideal Refs**: R4 (creative conversation with characters), R7 (iterative refinement)

---

## Goal

Determine whether **Character & Performance** needs a formal structured artifact beyond what character bibles + interactive character chat (Story 084) already provide.

Character & Performance is one of five concern groups in the ADR-003 three-layer architecture. It covers: emotional intensity, vocal delivery, physical performance, blocking, motivation, and performance arc within scenes.

---

## ADR-003 Context

**Before:** Performance direction was one of four role-produced direction types. Story 024 (convergence) required all four to exist before shot planning.

**After:** Character & Performance is a concern group. Story 024 is cancelled — no convergence gate. This changes the "prove your worth" question: the formal artifact no longer needs to exist for convergence. The question is now purely: **does shot planning (Story 025) or generation (Stories 026-028) need structured per-character-per-scene performance data that can't be pulled from existing artifacts?**

**What Story 084 already delivered:**
- Dynamic per-character agents (`@billy` chats in character)
- Character-specific system prompts built from bible + scene context
- Governance: characters chat, they don't write artifacts

**What remains unbuilt:**
- `PerformanceDirection` structured artifact (emotional state, arc, motivation, subtext, physical notes, key beats, relationship dynamics, dialogue delivery per character per scene)

---

## Resolution Criteria

This story gets **promoted to Pending** if:
- Story 025 (shot planning) discovers it genuinely needs structured per-character-per-scene emotional data that can't be pulled from character bibles + scene context on demand

This story gets **closed as Won't Do** if:
- Shot planning and generation work fine pulling character context from bibles + chat
- The N characters × M scenes cost of batch extraction isn't justified by downstream consumption

---

## If We Build It

### Character & Performance Artifacts (per scene, per character)
- [ ] Emotional state entering the scene
- [ ] Arc through the scene (how emotional state changes)
- [ ] Motivation (what the character wants)
- [ ] Subtext (what they're not saying)
- [ ] Physical notes (posture, energy, gestures)
- [ ] Key beats (moments of change, realization)
- [ ] Relationship dynamics with others present
- [ ] Dialogue delivery notes (tone, pace, emphasis)
- [ ] Blocking notes — where the character should be physically in the scene (ADR-003 Decision #3: blocking is an acknowledged unknown; storyboard-as-input is the primary hypothesis)

### Progressive Disclosure
- [ ] AI generates on demand; user specifies any subset.
- [ ] Readiness indicator: red/yellow/green.

---

## Tasks

- [ ] Decide: does Story 025 actually need this? (answer during that story's implementation)
- [ ] If yes: implement schema, module, tests
- [ ] If no: close as "Won't Do — covered by character bibles + chat agents (084)"

---

## Work Log

*(append-only)*

20260225 — Story rewritten. Original scope (actor agent instantiation, per-character system prompts, governance) delivered by Story 084. Remaining scope narrowed to PerformanceDirection artifacts only.

20260227 — Story reshaped per ADR-003. Performance direction → Character & Performance concern group. Convergence dependency (024) eliminated — the "prove your worth" question is now simpler: does shot planning need formal artifacts or can it pull from bibles + chat? Blocking notes added per ADR-003 Decision #3 (blocking is an acknowledged unknown).
