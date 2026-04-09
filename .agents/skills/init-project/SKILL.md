---
name: init-project
description: Bootstrap a new AI-coded repo from patterns in existing repos, installing the canonical methodology package instead of re-explaining setup from scratch
user-invocable: true
---

# /init-project [repo-path-or-url ...]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Bootstrap a new AI-coded project repo by extracting reusable patterns from one
or more reference repos, then installing the **same methodology package** used
here: ideal/spec/state, generated graph surfaces, checklist, eval/golden
baseline, AGENTS wiring, and canonical cross-CLI skill surface.

## What It Does

1. Reads reference repos for durable patterns.
2. Extracts the project-agnostic methodology package.
3. Adapts that package to the new project's domain, stack, and constraints.
4. Installs the canonical bootstrap/eval skill surface into the new repo.
5. Leaves the new repo ready to use `/setup-methodology greenfield` as the
   canonical day-zero workflow.

## Steps

1. **Read reference repos** — For each provided repo, read:
   - `AGENTS.md` / `CLAUDE.md` — Agent instructions and conventions
   - `.agents/skills/` — All skill definitions (canonical cross-CLI location)
   - Doc structure — How docs, stories, decisions, research are organized
   - Build/package config — `pyproject.toml` and/or `package.json`, workspace config, Makefile/task runners
   - `.gitignore`, type checker config (`mypy/pyright/tsconfig`), and other scaffolding
   - `CHANGELOG.md` — Versioning format
   - AI Learning Log in AGENTS.md — Accumulated wisdom from past sessions

2. **Extract the methodology package** — Preserve the durable package, not just
   isolated docs:
- dual ideal structure
- category-aligned spec + methodology state
- generated planning dashboards (`docs/build-map.md`, `docs/stories.md`)
- setup checklist flow
   - baseline eval + golden discipline, including registry/docs/templates and
     the golden fixture workspace
   - story / decomposition discipline
   - canonical skill surface and cross-CLI sync

3. **Gather project details** — Ask the user:
   - Project name and description
   - Tech stack (or ask if they want to research it)
   - Core tenets beyond the universal ones
   - Monorepo structure (packages needed)
   - Any project-specific skills needed
   - Deployment target
   - Where legacy/intake artifacts live (if any)

4. **Generate the new repo** — See "Generated Artifacts" below.

5. **Verify** — Show the generated structure to the user for review before committing.

## Project-Agnostic Patterns (ALWAYS include)

These patterns have been validated across multiple AI-coded projects. Include all of them in every new project:

### Core Tenets (adapt wording, keep the principles)
0. **Never Lose User Data** — Capture first, process second. Raw originals permanent.
1. **100% AI-Coded** — Human is architect, AI implements. Optimize for AI agents.
2. **AI Evolves Rapidly** — Architect for 100x. Single-call over multi-step. Maintain evals.
3. **Fewer, Fatter Files** — Start consolidated, split when too large. 200-600 line sweet spot.
4. **Verbose Build Artifacts** — Stories/work logs are build artifacts for cross-session continuity.
5. **Design for Ideal, Build for Today** — Describe unconstrained ideal, decompose to buildable.

### AI-First Problem Solving (CRITICAL — include verbatim or adapted)
- Before writing complex code: "Can an LLM call solve this?"
- Code = orchestration, storage, UI. AI = extraction, classification, generation, analysis.
- Training data has a cutoff — always research SOTA before architecture decisions.
- Models underestimate their own capabilities. Research, don't assume.
- Include "AI Considerations" section in every story template.

### promptfoo Evals
- Every AI prompt in production code gets a promptfoo eval.
- Test prompt variants + multiple providers to find best model per task.
- When new models drop, re-run all evals. Update calls where new model wins.
- Eval workspace: `benchmarks/` directory.

### Methodology Package

- `ideal.md` holds both product and execution ideals
- `spec.md` is category-aligned and contains product + build constraints
- `docs/methodology/state.yaml` is the canonical planning / triage state
- `build-map.md` and `stories.md` are generated dashboard views
- `docs/setup-checklist.md` is the working copy used during bootstrap / refresh runs
- goldens + evals are part of baseline setup, not an optional later add-on
- planning starts from methodology state; implementation starts from the story,
  but must read the relevant `spec:N` category, state lane, and ADRs first

### Checkboxes Everywhere
- All planning docs, stories, specs, work logs use checkboxes.
- Check off items when captured elsewhere — never delete.
- Ensures nothing lost across context loss/compaction.
- Any AI session can pick up work at any time.
- Stories include per-tenet verification checkboxes.

### Story-Based Development
- Stories are the primary AI guidance surface (mandates in story > mandates in AGENTS.md only).
- Template includes: Goal, Acceptance Criteria, Out of Scope, AI Considerations, Tasks (with standard closing tasks), Files to Modify, Notes, Work Log.
- Standard closing tasks: run checks, update docs, verify tenets (individual checkboxes per tenet).
- Work log format: `YYYYMMDD-HHMM — action: result, evidence, next step`

### AI Learning Log (in AGENTS.md)
- Section for recording mistakes and effective patterns discovered during work.
- All AI agents contribute. The file evolves with every session.
- Format: `YYYY-MM-DD — short title`: what happened, what to do differently.

### AGENTS.md Conventions
- 100-300 lines. Under 50 too sparse, over 300 causes skimming.
- Contains: project overview, tenets, tech stack, commands, code conventions, AI-first guidance, pitfalls, docs index, skills index, learning log.
- When approaching 300 lines: move detail to runbooks/docs, keep AGENTS.md as summary.
- No aggressive "DO NOT CHANGE" language — let the conversation stay open.

### Documentation Hierarchy
- **AGENTS.md** — repo facts, conventions, commands, public skill surface
- **docs/runbooks/setup-methodology.md** — canonical methodology bootstrap guide
- **docs/runbooks/promptfoo.md** — prompt-eval operating guide when the repo uses promptfoo
- **docs/ideal.md** — north star
- **docs/spec.md** — current constraints
- **docs/methodology/state.yaml** — canonical planning state
- **docs/build-map.md** — generated dashboard view
- **docs/stories.md** — generated story index and roadmap view
- **docs/stories/** — implementation slices
- **docs/decisions/** — ADRs and research
- **docs/evals/** — eval registry and attempt history
- **CHANGELOG.md** — updated by mark-story-done skill

### Canonical Skill Surface
Canonical location: `.agents/skills/` with symlinks for `.claude/skills`, `.cursor/skills`, and generated `.gemini/commands/*.toml` wrappers. Use `scripts/sync-agent-skills.sh` to wire everything up.

- `/setup-methodology`
- `/create-eval`
- `/improve-eval`
- `/align`
- `/create-story` — Scaffold story files with template (bootstrap script + template)
- `/build-story` — Implement stories with work-log discipline + AI-first check + tenet verification
- `/validate` — Assess implementation quality vs requirements
- `/check-in-diff` — Audit git changes before commit + CHANGELOG enforcement
- `/mark-story-done` — Validate and close stories + update CHANGELOG
- `/triage` — Identify the highest-leverage methodology gap and recommend the next action
- `/scout` — Research external sources for adoptable patterns
- `/create-adr` — Create ADR with research scaffolding (bootstrap script + templates)
- `/create-cross-cli-skill` — Create new skills in canonical cross-CLI format
- `/deploy` — Deploy to production (scaffold early, fill in when ready)

Do not install the old phased setup aliases in a fresh repo. The public setup
surface starts with `/setup-methodology`.

### Known AI Failure Modes (include all of these)
- **"Helpful Rewrite"** — rewrites entire file instead of minimal fix
- **"Phantom Import"** — imports from nonexistent modules
- **"Test That Tests Nothing"** — tests pass but don't test behavior
- **"Dependency Avalanche"** — installs packages for solvable problems
- **"Schema Drift"** — modifies schema without migration
- **"Context Cliff"** — quality degrades in long sessions
- **"Optimistic Path"** — builds happy path, ignores errors
- **"Code-First Bias"** — writes complex code when an LLM call would be better
- **"Human-Scale Estimates"** — gives time estimates as if humans do the work

### Code Conventions (adapt per tech stack)
- File size sweet spot (200-600 lines)
- Types centralized
- Max architectural layers (3)
- Integration tests over unit tests
- No new dependencies without approval
- No implicit commits — explicit permission only
- Minimum necessary changes

### No Backwards Compatibility (for greenfield projects)
- No migration paths, compat shims, deprecation warnings
- Change directly. Drop and recreate.

### Session Protocol
- Start: read AGENTS.md → read story → check git log → read source
- End: update work log → update status → run checks → check doc updates

## What Gets Customized (Project-Specific)

- Project name, description, identity
- Tech stack and package structure
- Domain-specific tenets (e.g., "Authentic Capture" for voice apps)
- Deployment config
- Project-specific conventions
- Tech-stack-specific commands and pitfalls
- Spec structure

## Generated Artifacts

```
AGENTS.md
CLAUDE.md
CHANGELOG.md
docs/
  ideal.md
  spec.md
  methodology/
    state.yaml
    graph.json
  build-map.md
  setup-checklist.md
  stories.md
  inbox.md
  decisions/
  intake/               # if applicable
  evals/
    README.md
    registry.yaml
    attempt-template.md
  runbooks/
    setup-methodology.md
    promptfoo.md        # if the repo uses promptfoo-style evals
.agents/skills/
  setup-methodology/
    SKILL.md
    templates/
    references/
  create-eval/SKILL.md
  improve-eval/SKILL.md
  align/SKILL.md
  create-story/SKILL.md   # + scripts/ + templates/
  build-story/SKILL.md
  validate/SKILL.md
  check-in-diff/SKILL.md
  mark-story-done/SKILL.md
  triage/SKILL.md
  scout/SKILL.md          # + scripts/ + templates/
  create-adr/SKILL.md     # + scripts/ + templates/
  create-cross-cli-skill/SKILL.md
  deploy/SKILL.md
  init-project/SKILL.md
skills -> .agents/skills
.claude/skills -> ../.agents/skills
.cursor/skills -> ../.agents/skills
.gemini/commands/*.toml
scripts/sync-agent-skills.sh
.gitignore
```

## Notes

- `init-project` should **install the package**, not reteach an older phased
  setup flow from scratch.
- After the repo skeleton exists, the canonical bootstrap path is
  `/setup-methodology greenfield`.
- When copying from a reference repo, prefer reusing the same templates and
  packaged skill assets over rewriting them by hand.
- Do not copy path assumptions blindly. If the target repo uses a different
  layout, update the bundled skills/runbooks/templates so their paths point at
  the new repo's actual eval, prompt, fixture, and story locations.
- This skill improves as more repos establish patterns
- The user's repos are the training data for what "good AI-coded repo" looks like
- When patterns conflict between reference repos, ask the user which to prefer
- Always show the generated structure before committing
- The AI Learning Log from reference repos is gold — carry forward confirmed patterns
