# Story 034: In-App Style Pack Creator

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.4 (Style Pack Creation), 8.3 (Style Packs)
**Depends On**: Story 016 (style pack infrastructure — templates and format), Story 011b (Operator Console — UI for creation flow)

---

## Goal

Implement **in-app style pack creation** using deep research APIs. The user selects a role type, provides freeform input (a name, a combination, a reference work, or an original description), and the system uses a deep research API to produce a properly structured style pack.

This is the automated version of the manual workflow established in Story 016.

---

## Acceptance Criteria

### Creation Flow
- [ ] User selects a role type (Director, Visual Architect, Sound Designer, Editorial Architect, Actor Agent).
- [ ] User provides freeform input:
  - [ ] A single name (e.g., "Tarantino").
  - [ ] A combination (e.g., "Tarantino's dialogue + Kubrick's framing").
  - [ ] A reference work (e.g., "Blade Runner 2049").
  - [ ] An original description (e.g., "moody noir with jazz undertones").
- [ ] System loads the role-specific creation prompt template (from Story 016).
- [ ] Template + user input sent to deep research API.
- [ ] Research runs asynchronously with progress updates.
- [ ] Result auto-formatted into a properly structured style pack folder.

### Deep Research API Integration
- [ ] Support for deep research APIs:
  - [ ] OpenAI Agents SDK (if available).
  - [ ] Google Gemini (if available).
  - [ ] Anthropic (if available).
  - [ ] Fallback: manual flow (user pastes output from external tool).
- [ ] API selection configurable.
- [ ] Progress reporting during research (may take minutes).
- [ ] Cost tracking for research API calls.
- [ ] Alternative: integration with `deep-research` CLI tool for multi-model research.

### Output Validation
- [ ] Generated style pack validated against schema (Story 016).
- [ ] Pack includes all required components:
  - [ ] `style.md` with rich creative description.
  - [ ] `manifest.json` with proper metadata.
  - [ ] Optional reference materials (if the research produced/referenced them).
- [ ] User can review and edit the generated pack before activating it.

### UI Integration
- [ ] Style pack creation accessible from Operator Console.
- [ ] Progress indicator during async research.
- [ ] Preview of generated pack with ability to edit before saving.
- [ ] Library of created packs browsable and selectable per-role.

### Testing
- [ ] Unit tests for creation prompt template rendering.
- [ ] Unit tests for style pack output formatting and validation.
- [ ] Unit tests for deep research API integration (mocked).
- [ ] Integration test: user input → research → style pack → validation → storage.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Deep Research for Style
Style packs benefit enormously from deep research because creative influences are nuanced and multi-faceted. A "Tarantino" style pack for a Director needs to cover narrative structure, dialogue philosophy, tonal range, genre mixing, and thematic obsessions — all extracted from analysis of the filmmaker's body of work. A single AI call won't capture this depth; deep research with multiple models can.

### Manual Fallback
Not everyone will have deep research API keys configured. The creation prompt templates (from Story 016) should be usable standalone — the user can paste them into ChatGPT, Gemini, or any capable model and manually save the output as a style pack. The in-app creation flow is a convenience, not a requirement.

### CineForge's Deep Research Tool
The project has a custom `deep-research` CLI tool ([deep-research-manager](https://github.com/copperdogma/deep-research-manager)) that can orchestrate multi-model research. Consider integrating with this tool as an alternative to direct API calls — it supports multiple providers and produces formatted research outputs.

---

## Tasks

- [ ] Implement deep research API integration (at least one provider).
- [ ] Implement creation flow: template + input → research → output → validation → storage.
- [ ] Implement async progress reporting.
- [ ] Implement output formatting (research result → style pack folder structure).
- [ ] Implement manual fallback flow.
- [ ] Integrate with `deep-research` CLI tool (optional, if installed).
- [ ] Implement UI for creation flow in Operator Console.
- [ ] Implement style pack library (browse, select, assign to role).
- [ ] Write unit tests.
- [ ] Write integration test (mocked research API).
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
