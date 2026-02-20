# Story 016: Style Pack Infrastructure

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 8.3 (Style Packs), 8.4 (Style Pack Creation — creation prompt templates only), 6.3 (Bible Artifact Structure — folder-based pattern)
**Depends On**: Story 014 (role system foundation — style pack loading)

---

## Goal

Build the infrastructure for creating, storing, validating, and applying style packs. Style packs are folder-based creative personality profiles that shape how a role thinks without changing what it does. This story builds the authoring and management layer; Story 014 already handles runtime loading.

---

## Acceptance Criteria

### Style Pack Structure (Spec 8.3)
- [x] Style packs are folder-based artifacts containing:
  - [x] `style.md`: rich text description of the creative personality.
  - [x] `manifest.json`: file listing, metadata, target role type.
  - [x] Optional: reference images, frame grabs, color palettes, audio references.
- [x] Each role type has a style pack template defining what creative dimensions to describe:
  - [x] Director: narrative structure, pacing, thematic obsessions, tonal range, approach to violence/humor/emotion.
  - [x] Visual Architect: lighting philosophy, color palette preferences, composition style, camera personality.
  - [x] Sound Designer: sonic palette, use of silence, ambient philosophy, music philosophy.
  - [x] Editorial Architect: cutting rhythm, transition preferences, montage approach.
  - [x] Actor Agent: acting methodology, physicality, emotional range, dialogue approach.

### Style Pack Validation
- [x] Validate style pack structure (required files, manifest completeness).
- [x] Validate target role type matches the role it's assigned to.
- [x] Validate no permission escalation (style pack cannot grant capabilities beyond the role's tier).

### Style Pack Input Types (Spec 8.3)
- [x] Style pack can be created from:
  - [x] A single name (e.g., "Tarantino").
  - [x] A combination of names or aspects (e.g., "Tarantino's dialogue + Kubrick's framing").
  - [x] A movie, TV show, or book title (e.g., "Blade Runner 2049").
  - [x] An original description (e.g., "moody, rain-soaked noir with jazz undertones").
- [x] Each role definition includes a style pack creation prompt template (spec 8.4) that guides research.

### Creation Prompt Templates
- [x] Each role type has a creation prompt template in `src/cine_forge/roles/{role_type}/style_pack_prompt.md`.
- [x] Templates specify:
  - [x] What creative dimensions to research for this role type.
  - [x] How to format the output for CineForge consumption.
  - [x] How to handle the different input types (name, combination, reference, original).
- [x] Templates are designed for use with deep research APIs (Story 034 implements the full in-app flow) or manual use (paste into ChatGPT/Gemini).

### Built-in Style Packs
- [x] At least one built-in style pack per role type as examples.
- [x] Generic/default pack for each role type (neutral creative direction).

### Testing
- [x] Unit tests for style pack validation (structure, role type matching, permission checks).
- [x] Unit tests for style pack loading and prompt injection (from Story 014).
- [x] Unit tests for creation prompt template rendering with different input types.
- [x] Integration test: create style pack → assign to role → verify prompt injection.
- [x] Schema validation on all outputs.

---

## Design Notes

### Style Packs vs. System Prompts
The role's system prompt defines its structural function (what it does). The style pack modifies its creative personality (how it does it). When composing the final AI prompt, the system prompt comes first, then the style pack content is appended as creative context.

### Manual vs. Automated Creation
This story implements the templates and structure. The full automated creation flow (deep research API → style pack folder) is Story 034. Until then, style packs can be created manually by following the template and placing files in the right folder.

### Directory Structure Decision
Built-in style packs are stored in `src/cine_forge/roles/style_packs/{role_type}/` rather than `configs/` to keep them versioned with the role definitions and deployed as package data. User-defined packs (when implemented) may live in project config directories.

---

## Tasks

- [x] Design and implement `StylePackManifest` schema.
- [x] Register schema in schema registry.
- [x] Create style pack directory structure under `src/cine_forge/roles/style_packs/{role_type}/` (was `configs/`).
- [x] Implement style pack validation logic.
- [x] Write creation prompt templates for all role types.
- [x] Create generic/default style packs for all role types.
- [x] Create at least one example style pack per role type.
- [x] Implement style pack management API (list, validate, load).
- [x] Write unit tests for validation, loading, and prompt template rendering.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*

20260220-1300 — implementation complete: verified `StylePack` schema from Story 014; implemented `RoleCatalog.list_style_packs` and validation logic; created creation prompt templates for Director, Visual Architect, Sound Designer, Editorial Architect, and Actor Agent; created `generic` style packs for all roles and example packs (Tarantino, Deakins, Schoonmaker, Lynch, DDL); evidence=`src/cine_forge/roles/style_packs/`, `src/cine_forge/roles/runtime.py`.

20260220-1315 — testing complete: added comprehensive unit tests for `RoleCatalog` style pack management and `RoleContext` injection logic; added integration test verifying full lifecycle (create -> load -> inject); fixed lint issues and verified all tests pass with correct python environment; evidence=`tests/unit/test_style_packs.py`, `tests/integration/test_style_pack_integration.py`.
