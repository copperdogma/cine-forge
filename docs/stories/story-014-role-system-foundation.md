# Story 014: Role System Foundation

**Status**: Done
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
- [x] Roles are defined as structured artifacts in `src/cine_forge/roles/`.
- [x] Each role definition includes:
  - [x] **Role ID**: unique identifier (e.g., `director`, `script_supervisor`, `visual_architect`).
  - [x] **Display name**: human-readable name.
  - [x] **Tier**: `canon_authority`, `canon_guardian`, `structural_advisor`, or `performance`.
  - [x] **Description**: what this role does.
  - [x] **System prompt**: the AI persona prompt for this role.
  - [x] **Capabilities**: declared perception abilities (`text`, `image`, `video`, `audio+video`).
  - [x] **Style pack slot**: whether this role accepts a style pack (Canon Guardians do not).
  - [x] **Permissions**: what artifact types this role can propose changes to.
- [x] Role definitions are loaded at runtime and validated.

### Role Hierarchy (Spec 8.1)
- [x] Hierarchy tiers enforced:
  - [x] **Canon Authority** (Director): final decision authority, can override lower tiers.
  - [x] **Canon Guardians** (Script Supervisor, Continuity Supervisor): can block progression pending review.
  - [x] **Structural Advisors** (Editorial Architect, Visual Architect, Sound Designer): propose and design, cannot finalize canon.
  - [x] **Performance** (Actor Agents): suggest only, cannot modify canon.
- [x] Tier-based permission checks: a role cannot perform actions above its tier.
- [x] Override mechanism: higher-tier roles can override lower-tier objections with explicit justification.

### Capability Gating (Spec 8.2)
- [x] Roles declare their perception capabilities.
- [x] Runtime validation: a role cannot be asked to evaluate media it cannot perceive.
- [x] Capability check before AI calls: if a role claims `text` only, it cannot be asked to evaluate an image artifact.
- [x] Capability declarations are checked against the actual model being used.

### Style Pack Loading (Spec 8.3)
- [x] Style packs are folder-based artifacts:
  - [x] Rich text description of creative personality.
  - [x] Optional reference images, frame grabs, palettes.
  - [x] Manifest listing all files.
- [x] Style pack selected per-role in project configuration.
- [x] Default "generic" pack exists for each role type that accepts style packs.
- [x] Style pack content is injected into the role's system prompt at runtime.
- [x] Canon Guardians reject style pack assignment (enforced).

### Role Runtime Contract
- [x] Modules invoke roles through a `RoleContext` interface:
  ```python
  class RoleContext:
      def invoke(self, role_id: str, prompt: str, inputs: dict) -> RoleResponse
      def check_capability(self, role_id: str, media_type: str) -> bool
      def get_hierarchy_tier(self, role_id: str) -> str
  ```
- [x] `RoleResponse` includes: response content, confidence, rationale, cost data.
- [x] Role invocations are logged with full audit metadata.
- [x] Cost tracking per role invocation.

### Schema
- [x] `RoleDefinition` Pydantic schema.
- [x] `RoleResponse` Pydantic schema.
- [x] `StylePack` Pydantic schema (manifest + content references).
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for role loading and validation.
- [x] Unit tests for hierarchy enforcement (tier permissions, override logic).
- [x] Unit tests for capability gating (valid/invalid capability checks).
- [x] Unit tests for style pack loading and prompt injection.
- [x] Unit tests for RoleContext invocation (mocked AI).
- [x] Integration test: load role definitions → invoke via RoleContext → validate response.
- [x] Schema validation on all outputs.

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

- [x] Design and implement `RoleDefinition`, `RoleResponse`, `StylePack` schemas.
- [x] Register schemas in schema registry.
- [x] Implement role definition loading from `src/cine_forge/roles/`.
- [x] Implement hierarchy tier enforcement.
- [x] Implement capability gating.
- [x] Implement style pack loading and prompt injection.
- [x] Implement `RoleContext` interface for module-role invocation.
- [x] Create generic default style packs for each role type.
- [x] Create skeleton role definition files for all spec-defined roles (Director, Script Supervisor, Continuity Supervisor, Editorial Architect, Visual Architect, Sound Designer, Actor Agent). These are structural definitions (role ID, tier, capabilities, style pack slot, permissions) with placeholder system prompts. Full system prompts and role-specific behaviors are implemented in their respective stories (015 for canon roles, 020-023 for creative roles).
- [x] Implement role invocation logging with audit metadata.
- [x] Write unit tests for all components.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*

20260219-2204 — implementation start: audited Story 014 requirements, spec section 8, and dependency stories (015-019) to lock scope boundaries and avoid bleeding later-role behavior into this foundation story; evidence=`docs/stories/story-014-role-system-foundation.md`, `docs/spec.md`, next=implement schemas + runtime + defaults.

20260219-2222 — role-system foundation shipped: added role schemas (`RoleDefinition`, `RoleResponse`, `StylePack`) and runtime contract (`RoleCatalog`, `RoleContext`) with hierarchy checks, explicit override-justification enforcement, capability gating, model-capability validation, style-pack injection, and immutable JSONL role invocation audit logs with per-call cost envelopes; evidence=`src/cine_forge/schemas/role.py`, `src/cine_forge/roles/runtime.py`, `src/cine_forge/driver/engine.py`, `src/cine_forge/schemas/__init__.py`, next=add defaults and tests.

20260219-2231 — defaults + skeletons completed: created structural role definition files for Director, Script Supervisor, Continuity Supervisor, Editorial Architect, Visual Architect, Sound Designer, and Actor Agent; created generic style-pack manifests and prompt assets for all style-pack-accepting roles; evidence=`src/cine_forge/roles/director/role.yaml`, `src/cine_forge/roles/script_supervisor/role.yaml`, `src/cine_forge/roles/continuity_supervisor/role.yaml`, `src/cine_forge/roles/editorial_architect/role.yaml`, `src/cine_forge/roles/visual_architect/role.yaml`, `src/cine_forge/roles/sound_designer/role.yaml`, `src/cine_forge/roles/actor_agent/role.yaml`, `src/cine_forge/roles/style_packs/`, next=verify via tests.

20260219-2236 — verification completed: added unit coverage for loading, hierarchy enforcement, override logic, capability gating, style-pack assignment rules, invocation logging, and schema registration plus integration coverage for load→invoke→validate flow; ran `make test-unit PYTHON=.venv/bin/python` (pass), `make lint PYTHON=.venv/bin/python` (initial fail on pre-existing benchmark lints), applied mechanical lint-only cleanup in benchmark scorers, reran lint to green; scoped lint/run checks now pass (`.venv/bin/python -m ruff check src/ tests/`, `make lint`); evidence=`tests/unit/test_role_system.py`, `tests/integration/test_role_system_integration.py`, `benchmarks/scorers/*.py`, next=mark story + index done.

20260219-2238 — tenet check + closeout: validated data safety (append-only invocation logs), AI-first boundaries (roles/prompt composition kept explicit), architecture flexibility (role/model decoupling maintained), and traceability (audit + cost metadata persisted per invocation); story accepted as complete and ready for Story 015 to consume foundation APIs; evidence=`src/cine_forge/roles/runtime.py`, `docs/stories.md`, `AGENTS.md`, next=begin Story 015 canon-role behaviors.

20260219-2247 — validation remediation applied: aligned `permissions` semantics to artifact-type scope in role definitions and updated runtime/tests so model capability checks apply to invocation-requested media types (not all declared role capabilities), preserving valid text-only calls for multimodal roles while still blocking unsupported media requests; evidence=`src/cine_forge/roles/*/role.yaml`, `src/cine_forge/roles/runtime.py`, `tests/unit/test_role_system.py`; verification=`.venv/bin/python -m pytest tests/unit/test_role_system.py tests/integration/test_role_system_integration.py`, `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `make lint PYTHON=.venv/bin/python`, next=resume Story 015.

20260219-2251 — story formally closed via mark-story-done: re-ran required backend closure checks (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`) and targeted role-system tests, confirmed all acceptance criteria/tasks remain checked and dependency prerequisites (Stories 002/006) are satisfied, then added Story 014 changelog entry without duplication; evidence=`CHANGELOG.md`, `docs/stories.md`, test outputs in session, next=begin Story 015 implementation.
