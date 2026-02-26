# Story 023: Performance Direction Artifacts

**Status**: Draft
**Created**: 2026-02-13
**Rewritten**: 2026-02-25 — Original scope largely superseded by Story 084.
**Spec Refs**: 12.4 (Performance Direction)
**Depends On**: Story 008 (character bibles), Story 005 (scene extraction), Story 010 (entity graph — relationship dynamics), Story 011 (continuity tracking — emotional/physical state)

---

## What Changed

Story 084 (Character Chat Agents) delivered the core of what this story originally proposed:

- **Dynamic per-character agents**: `@billy` chats with Billy in character, grounded in bible + scene context.
- **Character-specific system prompts**: built from bible entry + scene summaries, updated when bible changes.
- **Actor Agent → Story Editor rename**: the "acting coach" role was replaced with a narrative logic specialist.
- **Governance**: characters can't modify canon — they chat, they don't write artifacts.

What 084 did NOT deliver: **structured PerformanceDirection artifacts** (per-scene, per-character emotional state, subtext, physical notes, dialogue delivery as formal schema'd output).

---

## What Remains

The only unbuilt piece is the PerformanceDirection artifact — a structured, per-scene, per-character document containing:

- Emotional state entering the scene
- Arc through the scene (how emotional state changes)
- Motivation (what the character wants)
- Subtext (what they're not saying)
- Physical notes (posture, energy, gestures)
- Key beats (moments of change, realization)
- Relationship dynamics (how they relate to others present)
- Dialogue delivery notes (tone, pace, emphasis)

---

## This Story Must Prove Its Worth

**The open question: what actually consumes performance direction artifacts?**

### Claimed downstream consumers

1. **Story 024 — Direction Convergence**: The Director reviews "all four direction types" (editorial, visual, sound, performance) for consistency before shot planning. Performance direction is one of the four inputs. **But**: does convergence actually need a formal artifact, or could the Director just chat with the character to get performance context on demand?

2. **Story 025 — Shot Planning**: Coverage strategy includes "performance notes" that inform framing and blocking decisions. A character's emotional state affects whether you shoot a close-up or a wide. **But**: the shot planner could pull this from the character bible + scene context directly, the same way the character chat agents already do.

3. **Storyboards / Render (Stories 026–028)**: Character emotional state and physical notes would inform facial expressions, body language in generated imagery. **But**: this is far downstream and may be better handled by the render prompt itself pulling from bibles.

### The case against

- **Cost**: N characters × M scenes = N×M LLM calls to produce artifacts that may never be read by a human or meaningfully consumed by downstream stages.
- **Redundancy**: Character bibles already contain traits, arc, relationships, dialogue style. Scene context already captures who's present and what happens. The performance direction artifact is largely a re-derivation of data that already exists.
- **The chat alternative**: Users can already `@billy` to ask "what are you feeling in Scene 8?" and get a richer, more contextual answer than any pre-computed artifact. The conversational approach is more flexible and costs nothing until invoked.
- **Direction convergence can adapt**: Story 024 could require only 3 direction types (editorial, visual, sound) and pull character context on demand from bibles + chat. This is arguably more natural than batch-computing performance notes.

### The case for

- **Structured data for automation**: If shot planning or render adapters need machine-readable emotional state per character per scene, a formal schema is better than free-text chat output.
- **Completeness of the direction layer**: The spec envisions four parallel creative directions. Dropping one creates an asymmetry.
- **Proactive insight**: Batch performance analysis might surface things the user wouldn't think to ask — "Billy's emotional state entering Scene 12 contradicts what happened in Scene 9."

### Verdict

**Defer until a real consumer proves the need.** If Story 024 (convergence) or Story 025 (shot planning) discovers it genuinely needs structured per-character-per-scene emotional data that can't be pulled from existing artifacts, this story gets promoted. Until then, character chat agents (Story 084) cover the interactive use case, and character bibles cover the data use case.

If promoted, the implementation is straightforward: reuse `build_character_system_prompt()` from 084, add a structured output schema, run batch extraction per character per scene (same pattern as editorial direction in Story 020).

---

## If We Build It

### Scope (reduced)

The actor agent instantiation, governance, and suggestion flow from the original story are all delivered by 084. What's left:

1. `PerformanceDirection` Pydantic schema (spec 12.4 fields)
2. `performance_direction_v1` module (batch extraction using character system prompts + structured output)
3. Wire into creative direction recipe
4. UI rendering in DirectionTab (reuse `DirectionAnnotation` component — already parameterized)
5. Tests

Estimated effort: Small-medium. The pattern is proven (copy editorial direction module structure).

### Schema (draft)

```python
class PerformanceDirection(BaseModel):
    scene_id: str
    character_id: str
    emotional_state_entering: str
    arc_through_scene: str
    motivation: str
    subtext: str
    physical_notes: str
    key_beats: list[str]
    relationship_dynamics: list[dict]  # character_id, dynamic description
    dialogue_delivery: list[dict]  # line reference, tone, pace, emphasis
    confidence: float
```

---

## Tasks

- [ ] Decide: does Story 024 or 025 actually need this? (answer during those stories)
- [ ] If yes: implement schema, module, recipe integration, UI tab, tests
- [ ] If no: close this story as "Won't Do — covered by character chat agents (084)"

---

## Work Log

*(append-only)*

20260225 — Story rewritten. Original scope (actor agent instantiation, per-character system prompts, governance) delivered by Story 084. Remaining scope narrowed to PerformanceDirection artifacts only. Status changed to Draft pending proof of need from downstream consumers (024, 025). Key question: does formal structured performance data add value over existing character bibles + interactive character chat?
