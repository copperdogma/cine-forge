# Story 053 — Cross-CLI Skills/Prompts Unification

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done

## Goal

Define and implement a single maintainable workflow so major local agent CLIs (`codex`, `claude`, `gemini cli`, `cursor`) can reuse the same project automation surface (skills/prompts/commands) with minimal duplication and predictable behavior.

## Acceptance Criteria

- [x] Deep research completed and saved under `docs/research/story-053-cross-cli-skills/`.
- [x] Story captures dated, primary-source-verified discovery results for each target CLI:
  - [x] Discovery paths and loading precedence.
  - [x] Invocation UX (`slash`, explicit trigger, implicit matching).
  - [x] Packaging format constraints (`SKILL.md`, commands, wrappers).
  - [x] Gaps/compatibility risks and fallback strategy.
- [x] Canonical layout is finalized as `.agents/skills` and justified.
- [x] Migration plan is documented for current CineForge assets (`skills/`, `.claude/skills`, `.cursor/commands`, prompt aliases).
- [x] Implementation completed for baseline unification:
  - [x] `.agents/skills` populated with project skills.
  - [x] `.claude/skills` points to canonical skills.
  - [x] `.cursor/skills` points to canonical skills.
  - [x] Gemini command wrappers are generated from canonical skills.
- [x] Prompt duplication removed (or retained only as temporary generated compatibility wrappers with explicit removal criteria).
- [x] Validation evidence (commands + outputs) is recorded in this work log.
- [x] A cross-agent skill authoring contract is documented so any AI creating a new skill writes it in the canonical cross-CLI format.

## Verified Findings (As Of 2026-02-19)

### Codex

- **Status:** Native Agent Skills support confirmed.
- **Discovery paths:** `.agents/skills` (project), `~/.agents/skills` (user), system paths.
- **Invocation:** `/skills` list and explicit `$skill-name`; implicit matching supported.
- **Implication:** `.agents/skills` is a valid canonical project root.

### Claude Code

- **Status:** Native skills and commands confirmed.
- **Discovery paths:** `.claude/skills` and `~/.claude/skills`; commands under `.claude/commands`.
- **Invocation:** slash commands and skill-triggered behavior.
- **Implication:** cleanly supports symlink to canonical `.agents/skills`.

### Cursor

- **Status:** Native Agent Skills support confirmed (v2.4+), plus legacy/custom commands still available.
- **Discovery paths:** `.cursor/skills` and `~/.cursor/skills`; commands under `.cursor/commands`.
- **Invocation:** `/skill-name` for skills; command UX still present.
- **Implication:** no need to keep prompt-only architecture; move to skills-first and keep command wrappers only if needed for transitional aliases.

### Gemini CLI

- **Status:** No first-class Agent Skills directory confirmed in current official docs.
- **Discovery paths:** `GEMINI.md` context file and command definitions under `.gemini/commands`.
- **Invocation:** command-driven flow.
- **Implication:** requires generated adapters/wrappers from canonical skills for parity.

### Source Quality Notes

- Deep research artifacts were generated on `2026-02-19`, but at least one claim was stale/incorrect.
- Final design decisions in this story must be based on primary vendor docs checked on the same day.

### Primary References Checked (2026-02-19)

- Codex skills: `https://developers.openai.com/codex/skills`
- Claude Code skills/commands: `https://docs.anthropic.com/en/docs/claude-code`
- Cursor skills: `https://cursor.com/docs/context/skills`
- Cursor commands: `https://cursor.com/docs/context/commands`
- Cursor changelog v2.4 (skills rollout): `https://cursor.com/changelog/2-4`
- Gemini CLI commands/context docs (repo docs): `https://github.com/google-gemini/gemini-cli/tree/main/docs`
- Agent Skills standard: `https://agentskills.io/`

## Cross-Agent Skill Authoring Contract

When any agent (Codex, Claude, Cursor, Gemini CLI workflow) is asked to create a new skill, it must:

1. Create skill only under `.agents/skills/<skill-name>/SKILL.md` (never as a tool-specific primary file).
2. Use standard skill frontmatter (`name`, `description`) and portable markdown instructions.
3. Keep optional assets colocated under `.agents/skills/<skill-name>/` (`scripts/`, `references/`, `assets/`) with relative paths.
4. Run sync (`scripts/sync-agent-skills.sh`) so adapters/symlinks update for Claude, Cursor, and Gemini wrappers.
5. Validate discoverability in at least Codex + one other CLI before marking complete.
6. If backward-compat command wrappers exist, generate them from canonical skill content; never hand-edit wrapper text.

## Tasks

- [x] Create story scaffold with required sections and explicit checkbox plan.
- [x] Inventory current local setup (`skills/`, `.claude/skills`, Codex-visible skill roots, prompt aliases).
- [x] Run `deep-research init` for Story 053 topic under `docs/research/`.
- [x] Author research prompt covering Codex/Claude/Gemini CLI/Cursor interoperability design.
- [x] Run `deep-research run` and collect all provider outputs.
- [x] Run `deep-research format` and synthesize with `deep-research final`.
- [x] Re-verify critical claims against primary vendor docs as of `2026-02-19`.
- [x] Decide canonical direction: all-in on skills with `.agents/skills` as source of truth.
- [x] Migrate existing project skills from `skills/` into `.agents/skills/` (preserve one folder per skill, `SKILL.md` format).
- [x] Update `.claude/skills` to point to `.agents/skills`.
- [x] Update `.cursor/skills` to point to `.agents/skills`.
- [x] Remove or archive prompt-era files under `.cursor/commands` and `.cursor/commands/build-story.md` style aliases unless explicitly required.
- [x] Implement Gemini compatibility layer: generate `.gemini/commands/*` wrappers from `.agents/skills/*/SKILL.md`.
- [x] Add `scripts/sync-agent-skills.sh` for idempotent local setup (symlinks + Gemini wrappers).
- [x] Add `make skills-sync` and `make skills-check` targets.
- [x] Add a project skill for skill creation itself (e.g., `.agents/skills/create-cross-cli-skill/SKILL.md`) that enforces this contract.
- [x] Validate in Codex, Claude, Cursor, and Gemini CLI with at least one shared skill invocation each.
- [x] Update `AGENTS.md` memory section with durable lessons learned from this migration.

## Work Log

### 20260219-0740 — Initialized Story 053 with actionable checklist

- **Action:** Created new cross-cutting story for multi-CLI skills/prompt unification and added explicit acceptance/tasks for deep-research-driven execution.
- **Result:** Success
- **Notes:** Checklist includes discovery, deep-research workflow, implementation spike, and validation evidence capture requirements.
- **Next:** Add Story 053 to `docs/stories.md`, then run the deep-research workflow and record findings incrementally.

### 20260219-0848 — Completed deep research run and captured artifacts

- **Action:** Ran deep-research workflow for Story 053 and generated provider reports plus synthesis under `docs/research/story-053-cross-cli-skills/`.
- **Result:** Success
- **Notes:** Artifacts generated include `gpt-5-2-report.md`, `claude-opus-4-6-report.md`, and `final-synthesis.md`.
- **Next:** Validate synthesized claims against primary vendor docs before implementation decisions.

### 20260219-1020 — Corrected synthesis with primary-source verification

- **Action:** Verified Codex, Claude, Gemini CLI, and Cursor capabilities directly from vendor docs/changelog.
- **Result:** Partial success
- **Notes:** Deep-research synthesis contained at least one stale claim; corrected baseline confirms Cursor now supports native skills (`.cursor/skills`) while Gemini still needs command wrappers.
- **Next:** Update story plan to an all-in skills architecture with `.agents/skills` canonical root and adapters only where required.

### 20260219-1054 — Replanned story for all-in skills architecture

- **Action:** Updated Story 053 acceptance criteria, findings, and tasks to reflect the approved strategy: canonical `.agents/skills`, remove prompt duplication, and add Gemini wrapper generation.
- **Result:** Success
- **Notes:** Plan now encodes a primary-source-first policy and explicit migration steps from legacy prompt-era files.
- **Next:** Execute implementation tasks (filesystem migration, symlink wiring, wrapper generation, and cross-CLI validation).

### 20260219-1100 — Added cross-agent authoring contract and meta-skill requirement

- **Action:** Extended Story 053 to include a formal contract for creating future skills in a cross-CLI-safe way plus a dedicated "create skill" meta-skill task.
- **Result:** Success
- **Notes:** Prevents drift where one agent creates tool-specific skills/prompts that other CLIs cannot consume.
- **Next:** Implement canonical layout and ship the meta-skill alongside sync/check tooling.

### 20260219-1101 — Implemented canonical `.agents/skills` migration and adapters

- **Action:** Migrated project skills to `.agents/skills`, replaced legacy `skills/` with symlink to canonical path, rewired `.claude/skills` and `.cursor/skills` to canonical path, and archived legacy Cursor prompt commands to `.cursor/commands.legacy/`.
- **Result:** Success
- **Evidence:** `ls -la .agents .claude .cursor .gemini skills` shows symlink wiring; canonical skills now under `.agents/skills/*/SKILL.md`.
- **Next:** Add and validate automation tooling for repeatable sync/check + Gemini wrappers.

### 20260219-1101 — Added sync tooling and Gemini command wrapper generation

- **Action:** Added `scripts/sync-agent-skills.sh` (apply/check modes), added `make skills-sync` and `make skills-check`, generated `.gemini/commands/*.toml` wrappers from canonical skills, and added `.agents/skills/create-cross-cli-skill/SKILL.md`.
- **Result:** Success
- **Evidence:** `make skills-sync` and `make skills-check` both pass; `.gemini/commands/` contains 10 wrappers matching 10 canonical skills.
- **Notes:** Fixed macOS portability issue in sync script (replaced `sort -z` usage).
- **Next:** Perform explicit CLI-level invocation checks in Codex/Claude/Cursor/Gemini and record results.

### 20260219-1101 — Validation run and AGENTS memory update

- **Action:** Ran unit tests in project venv and updated AGENTS memory with the canonical-skills pattern.
- **Result:** Partial success
- **Evidence:** `PYTHONPATH=src .venv/bin/python -m pytest -m unit` -> `207 passed, 53 deselected`; `AGENTS.md` updated with 2026-02-19 skills-unification lesson.
- **Notes:** `make test-unit` using system Python failed due missing `fastapi`; venv-based command passed.
- **Next:** Finish direct CLI invocation verification for all four target tools to close remaining task.

### 20260219-1116 — Cross-CLI invocation validation confirmed and story closed

- **Action:** Recorded user-confirmed validation that shared skills work in all target environments (Codex, Claude, Cursor, Gemini CLI), then finalized story completion state.
- **Result:** Success
- **Evidence:** User sign-off: "Yup works in all environments." Combined with prior sync/test evidence (`make skills-sync`, `make skills-check`, `.venv` unit tests) this satisfies remaining acceptance criteria.
- **Next:** None. Story 053 complete.
