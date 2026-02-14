# Story 014: Role System Foundation

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.1 (Role Hierarchy), 8.2 (Capability Gating), 8.3 (Style Packs — loading), 2.4 (AI-Driven), 2.6 (Explanation Mandatory)
**Depends On**: Story 002 (pipeline foundation), Story 006 (project configuration — style pack selections)

---

## Goal

Build the role system infrastructure: role definitions, hierarchy enforcement, capability gating, style pack loading, and the runtime contract for how modules invoke roles. This is the AI persona layer that sits inside pipeline modules — roles define *who does the thinking* while modules define *what happens*.

This story creates the framework. Stories 015–018 populate it with specific roles and behaviors.

---

## Acceptance Criteria

### Role Definition Model
- [ ] Roles are defined as structured artifacts in `src/cine_forge/roles/`.
- [ ] Each role definition includes:
  - [ ] **Role ID**: unique identifier (e.g., `director`, `script_supervisor`, `visual_architect`).
  - [ ] **Display name**: human-readable name.
  - [ ] **Tier**: `canon_authority`, `canon_guardian`, `structural_advisor`, or `performance`.
  - [ ] **Description**: what this role does.
  - [ ] **System prompt**: the AI persona prompt for this role.
  - [ ] **Capabilities**: declared perception abilities (`text`, `image`, `video`, `audio+video`).
  - [ ] **Style pack slot**: whether this role accepts a style pack (Canon Guardians do not).
  - [ ] **Permissions**: what artifact types this role can propose changes to.
- [ ] Role definitions are loaded at runtime and validated.

### Role Hierarchy (Spec 8.1)
- [ ] Hierarchy tiers enforced:
  - [ ] **Canon Authority** (Director): final decision authority, can override lower tiers.
  - [ ] **Canon Guardians** (Script Supervisor, Continuity Supervisor): can block progression pending review.
  - [ ] **Structural Advisors** (Editorial Architect, Visual Architect, Sound Designer): propose and design, cannot finalize canon.
  - [ ] **Performance** (Actor Agents): suggest only, cannot modify canon.
- [ ] Tier-based permission checks: a role cannot perform actions above its tier.
- [ ] Override mechanism: higher-tier roles can override lower-tier objections with explicit justification.

### Capability Gating (Spec 8.2)
- [ ] Roles declare their perception capabilities.
- [ ] Runtime validation: a role cannot be asked to evaluate media it cannot perceive.
- [ ] Capability check before AI calls: if a role claims `text` only, it cannot be asked to evaluate an image artifact.
- [ ] Capability declarations are checked against the actual model being used.

### Style Pack Loading (Spec 8.3)
- [ ] Style packs are folder-based artifacts:
  - [ ] Rich text description of creative personality.
  - [ ] Optional reference images, frame grabs, palettes.
  - [ ] Manifest listing all files.
- [ ] Style pack selected per-role in project configuration.
- [ ] Default "generic" pack exists for each role type that accepts style packs.
- [ ] Style pack content is injected into the role's system prompt at runtime.
- [ ] Canon Guardians reject style pack assignment (enforced).

### Role Runtime Contract
- [ ] Modules invoke roles through a `RoleContext` interface:
  ```python
  class RoleContext:
      def invoke(self, role_id: str, prompt: str, inputs: dict) -> RoleResponse
      def check_capability(self, role_id: str, media_type: str) -> bool
      def get_hierarchy_tier(self, role_id: str) -> str
  ```
- [ ] `RoleResponse` includes: response content, confidence, rationale, cost data.
- [ ] Role invocations are logged with full audit metadata.
- [ ] Cost tracking per role invocation.

### Schema
- [ ] `RoleDefinition` Pydantic schema.
- [ ] `RoleResponse` Pydantic schema.
- [ ] `StylePack` Pydantic schema (manifest + content references).
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for role loading and validation.
- [ ] Unit tests for hierarchy enforcement (tier permissions, override logic).
- [ ] Unit tests for capability gating (valid/invalid capability checks).
- [ ] Unit tests for style pack loading and prompt injection.
- [ ] Unit tests for RoleContext invocation (mocked AI).
- [ ] Integration test: load role definitions → invoke via RoleContext → validate response.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Roles vs. Modules (Architecture)
- **Modules** = pipeline stages (stateless, declarative, orchestrated by driver).
- **Roles** = AI personas (prompt persona, style pack, hierarchy position, permissions).
- A module may invoke one role, multiple roles, or no roles.
- The Render Adapter (Story 028) is explicitly "not a role" — it's a stateless module.

### Style Pack Injection
Style packs modify *how* a role thinks, not *what* it does. The injection happens at prompt construction time: the role's system prompt is composed of its base persona + the active style pack's creative direction. This keeps the role's structural function stable while allowing creative variation.

### What This Story Does NOT Include
- **Specific role implementations** — Story 015 (Director, Canon Guardians), Stories 020-024 (creative roles).
- **Suggestion system** — Story 017.
- **Inter-role communication** — Story 018.
- **Human interaction with roles** — Story 019.
- **Style pack creation** — Story 034.

---

## Tasks

- [ ] Design and implement `RoleDefinition`, `RoleResponse`, `StylePack` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement role definition loading from `src/cine_forge/roles/`.
- [ ] Implement hierarchy tier enforcement.
- [ ] Implement capability gating.
- [ ] Implement style pack loading and prompt injection.
- [ ] Implement `RoleContext` interface for module-role invocation.
- [ ] Create generic default style packs for each role type.
- [ ] Create skeleton role definition files for all spec-defined roles (Director, Script Supervisor, Continuity Supervisor, Editorial Architect, Visual Architect, Sound Designer, Actor Agent). These are structural definitions (role ID, tier, capabilities, style pack slot, permissions) with placeholder system prompts. Full system prompts and role-specific behaviors are implemented in their respective stories (015 for canon roles, 020-023 for creative roles).
- [ ] Implement role invocation logging with audit metadata.
- [ ] Write unit tests for all components.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
