# Story 028: Render Adapter Module

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 17 (Render Adapter Layer), 17.1 (Two-Part Prompt Architecture), 17.2 (Engine Packs), 17.3 (Error Handling), 7.2 (Tracks — generated video track)
**Depends On**: Story 025 (shot planning — shot definitions), Story 027 (keyframes — optional generation constraints), Story 022 (Sound & Music — audio intent), Story 013 (track system — video track), Story 098 (real-world asset upload — R17 origin-agnostic inputs)

---

## Goal

Implement the **Render Adapter** — a stateless module (not a role) that translates film artifacts into model-ready generation prompts for AI video generation engines. The render adapter has no creative agency — it's a prompt compiler that optimizes for the target model's strengths and limitations.

---

## Acceptance Criteria

### Two-Part Prompt Architecture (Spec 17.1)
- [ ] **Part 1 — Generic meta-prompt**: expert at producing rich AI video generation prompts from film artifacts. Model-agnostic. Focuses on quality and completeness.
- [ ] **Part 2 — Model-specific engine pack**: adapts the prompt to a specific model's strengths, limits, preferred language, and supported inputs.
- [ ] **Synthesis**: a single AI call combines both parts with actual creative inputs into one cohesive, model-optimized prompt.
- [ ] Synthesized prompt sent to target model API along with supported inputs (keyframes, audio, reference images).

### Engine Packs (Spec 17.2)
- [ ] Per-generator tuning profiles (swappable configuration files):
  - [ ] Known strengths and limitations.
  - [ ] Supported inputs (number of keyframes, audio support, max duration).
  - [ ] Preferred prompt language and structure.
  - [ ] Retry and mitigation strategies.
- [ ] At least two engine packs for initial release (targeting most capable models available).
- [ ] Engine pack format designed for easy addition of new models.

### Prompt Construction (ADR-003 concern groups)
- [ ] Prompt compiled from upstream concern group artifacts:
  - [ ] Shot definition (framing, camera, content, blocking).
  - [ ] **Look & Feel** (lighting, color, composition, camera personality, costume, set design, visual motifs).
  - [ ] **Sound & Music** (ambient, emotional soundscape, silence, music intent, audio motifs).
  - [ ] **Character & Performance** (character emotional states, physical notes, blocking — from concern group artifacts or character bibles if formal artifacts don't exist).
  - [ ] **Rhythm & Flow** (pacing, transition intent, coverage approach — from editorial direction).
  - [ ] Character bible state snapshots (current appearance).
  - [ ] Location bible state snapshots (current appearance).
  - [ ] Keyframes (if locked, as generation constraints).
  - [ ] User-injected assets / real-world assets (reference images, audio — R17).
- [ ] Prompt quality verified before submission (completeness check).

### Error Handling (Spec 17.3)
- [ ] Reports errors when requests exceed model capabilities:
  - [ ] Duration exceeds model max.
  - [ ] Required inputs not supported by target model.
  - [ ] Resolution/quality beyond model capability.
- [ ] Errors bubble up to pipeline — adapter does not negotiate or make creative decisions.
- [ ] Cannot change creative intent.
- [ ] Retry strategy per engine pack (transient failures, rate limits).

### Prompt Transparency (Ideal R12, ADR-003 Decision #4)
- [ ] The synthesized generation prompt is stored as a first-class artifact alongside the generated video.
- [ ] Users can view the exact prompt that produced any generated output (read-only — "the prompt is a window, not a door").
- [ ] Prompts are NOT directly editable. Changes go upstream (via chat or direct artifact edit), and the prompt recompiles automatically from upstream artifacts.
- [ ] "Chat about this" affordance: user can highlight any part of the displayed prompt and drop it into chat with the appropriate AI role pre-tagged for discussion.
- [ ] Prompt versions are tracked — upstream changes that trigger prompt recompilation create a new version of both the prompt and the output.

### Output
- [ ] Generated video segments stored as artifacts with full metadata.
- [ ] Placed on generated video track in timeline (Story 013).
- [ ] Cost tracking per generation (model, tokens/compute, estimated cost).
- [ ] Generation parameters recorded for reproducibility.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/generation/render_adapter_v1/`
- [ ] Not a role — no system prompt, no hierarchy position, no style pack.
- [ ] Reads shot plans, concern group artifacts, bibles, keyframes.
- [ ] Outputs generated video artifacts.

### Testing
- [ ] Unit tests for prompt construction from shot definitions.
- [ ] Unit tests for engine pack loading and validation.
- [ ] Unit tests for capability checking (duration limits, input support).
- [ ] Unit tests for error handling (capability exceeded, transient failures).
- [ ] Integration test: shot plan → render adapter → prompt generation (mocked model API).
- [ ] Schema validation on all outputs.

---

## Design Notes

### Not a Role
The spec is explicit: the Render Adapter is not a role. It has no opinions, no hierarchy position, and no review gates. It's a stateless prompt compiler. It doesn't decide what to generate — it decides how to ask the model to generate what the creative roles decided.

### Engine Pack Longevity
AI video generation models evolve rapidly. Engine packs are designed to be swappable so that when a new model launches, adding support is just a new configuration file + any model-specific API integration.

### Keyframe Constraints
When keyframes are locked (Story 027), they become hard constraints for the render adapter. The generation prompt must instruct the model to match the keyframe at the specified point. How well the model respects this varies by engine — the engine pack should document this.

---

## Tasks

- [ ] Design generic meta-prompt (Part 1) for video generation.
- [ ] Design engine pack format and schema.
- [ ] Create at least two engine packs for current leading models.
- [ ] Implement prompt synthesis (Part 1 + Part 2 + creative inputs).
- [ ] Create `render_adapter_v1` module.
- [ ] Implement model API integration layer.
- [ ] Implement capability checking and error reporting.
- [ ] Implement retry strategy per engine pack.
- [ ] Implement video artifact storage and track placement.
- [ ] Implement cost tracking per generation.
- [ ] Write unit tests.
- [ ] Write integration test (mocked model API).
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
