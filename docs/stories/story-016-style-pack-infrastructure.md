# Story 016: Style Pack Infrastructure

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.3 (Style Packs), 8.4 (Style Pack Creation — creation prompt templates only), 6.3 (Bible Artifact Structure — folder-based pattern)
**Depends On**: Story 014 (role system foundation — style pack loading)

---

## Goal

Build the infrastructure for creating, storing, validating, and applying style packs. Style packs are folder-based creative personality profiles that shape how a role thinks without changing what it does. This story builds the authoring and management layer; Story 014 already handles runtime loading.

---

## Acceptance Criteria

### Style Pack Structure (Spec 8.3)
- [ ] Style packs are folder-based artifacts containing:
  - [ ] `style.md`: rich text description of the creative personality.
  - [ ] `manifest.json`: file listing, metadata, target role type.
  - [ ] Optional: reference images, frame grabs, color palettes, audio references.
- [ ] Each role type has a style pack template defining what creative dimensions to describe:
  - [ ] Director: narrative structure, pacing, thematic obsessions, tonal range, approach to violence/humor/emotion.
  - [ ] Visual Architect: lighting philosophy, color palette preferences, composition style, camera personality.
  - [ ] Sound Designer: sonic palette, use of silence, ambient philosophy, music philosophy.
  - [ ] Editorial Architect: cutting rhythm, transition preferences, montage approach.
  - [ ] Actor Agent: acting methodology, physicality, emotional range, dialogue approach.

### Style Pack Validation
- [ ] Validate style pack structure (required files, manifest completeness).
- [ ] Validate target role type matches the role it's assigned to.
- [ ] Validate no permission escalation (style pack cannot grant capabilities beyond the role's tier).

### Style Pack Input Types (Spec 8.3)
- [ ] Style pack can be created from:
  - [ ] A single name (e.g., "Tarantino").
  - [ ] A combination of names or aspects (e.g., "Tarantino's dialogue + Kubrick's framing").
  - [ ] A movie, TV show, or book title (e.g., "Blade Runner 2049").
  - [ ] An original description (e.g., "moody, rain-soaked noir with jazz undertones").
- [ ] Each role definition includes a style pack creation prompt template (spec 8.4) that guides research.

### Creation Prompt Templates
- [ ] Each role type has a creation prompt template in `src/cine_forge/roles/{role_type}/style_pack_prompt.md`.
- [ ] Templates specify:
  - [ ] What creative dimensions to research for this role type.
  - [ ] How to format the output for CineForge consumption.
  - [ ] How to handle the different input types (name, combination, reference, original).
- [ ] Templates are designed for use with deep research APIs (Story 034 implements the full in-app flow) or manual use (paste into ChatGPT/Gemini).

### Built-in Style Packs
- [ ] At least one built-in style pack per role type as examples.
- [ ] Generic/default pack for each role type (neutral creative direction).

### Testing
- [ ] Unit tests for style pack validation (structure, role type matching, permission checks).
- [ ] Unit tests for style pack loading and prompt injection (from Story 014).
- [ ] Unit tests for creation prompt template rendering with different input types.
- [ ] Integration test: create style pack → assign to role → verify prompt injection.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Style Packs vs. System Prompts
The role's system prompt defines its structural function (what it does). The style pack modifies its creative personality (how it does it). When composing the final AI prompt, the system prompt comes first, then the style pack content is appended as creative context.

### Manual vs. Automated Creation
This story implements the templates and structure. The full automated creation flow (deep research API → style pack folder) is Story 034. Until then, style packs can be created manually by following the template and placing files in the right folder.

---

## Tasks

- [ ] Design and implement `StylePackManifest` schema.
- [ ] Register schema in schema registry.
- [ ] Create style pack directory structure under `configs/style_packs/{role_type}/`.
- [ ] Implement style pack validation logic.
- [ ] Write creation prompt templates for all role types.
- [ ] Create generic/default style packs for all role types.
- [ ] Create at least one example style pack per role type.
- [ ] Implement style pack management API (list, validate, load).
- [ ] Write unit tests for validation, loading, and prompt template rendering.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
