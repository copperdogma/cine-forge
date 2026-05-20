---
name: create-story
description: Scaffold a numbered story file and refresh the generated planning surfaces
user-invocable: true
---

# /create-story [title]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current state phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

Create a new story in `docs/stories/` with consistent format. `docs/stories.md`
is generated from story metadata; do not hand-edit it.

## Optional Sidecar Evidence

Use `/ideation` as an optional sidecar packet when possible story boundaries
are too same-shaped or vague to score honestly. It may expand candidate
boundaries or solution approaches, and may run in a bounded subagent when the
user has explicitly authorized delegation, but `/create-story` still owns
whether a story is warranted and which boundary is durable.

When launching sidecars, size each worker model and reasoning level to shard risk. Use cheaper or lower-reasoning workers for lookup, wrapper parity, and mechanical scans; keep stronger workers for semantic contracts, security, eval correctness, cross-repo decisions, or high-cost misses. Record any explicit override rationale in the handoff.

For non-trivial or cross-cutting story creation, the main thread may use
subagents or sidecar agents to gather bounded evidence before deciding whether
to bootstrap. Useful packets include codebase impact scans, recent or active
story lookup, decision/design/scout/eval lookup, source-specific research, and
edge-case completeness checks across UI, provider health, architecture, and
operator surfaces.

- Sidecars are optional and evidence-only. They do not decide whether a story is
  warranted, choose the story boundary, set the initial status, or write the
  final story artifact.
- Do not default story creation to `/loop-verify`; reserve repeated verify
  loops for later validation or unusually broad/high-risk planning surfaces.
- If subagents are unavailable, unsafe for the checkout, or explicitly disabled
  by the user, run the same evidence checks sequentially and state that
  fallback in the handoff.

## Eval Ladder Gate

For AI-capability work, identify the eval ladder before creating or prioritizing
implementation backlog:

- the root Ideal eval or full-path golden, or the explicit reason it is deferred
- the parent eval or latest higher-level result that shows the current failure
- the measured failure mode that makes decomposition necessary
- the child eval, failure-classification attempt, ADR/spec update, or story that
  advances the next unresolved ladder node

Prefer rerunning a root/parent eval when new models, provider changes, code
changes, scorer fixes, or changed constraints could collapse the current
decomposition. Prefer a child eval or failure-classification attempt when the
parent failure is still too vague to choose AI-only, multi-call AI, deterministic
code, or hybrid implementation honestly.

## Inputs

- `title`: human-readable story title
- `slug`: kebab-case slug (derived from title if not provided)
- `priority`: High / Medium / Low (default: Medium)
- `ideal_refs`: ideal.md requirements this delivers (e.g., Reqs #1, #3)
- `spec_refs`: relevant spec.md sections or compromise numbers
- `adr_refs`: relevant decision records in `docs/decisions/` or `docs/design/` (or `None found after search`)
- `depends_on`: story IDs this depends on (if any)
- `status`: Draft (default, worth preserving but not honestly build-ready yet), Pending (fully detailed and honestly buildable now), or Blocked (concrete enough to preserve, but already proven blocked)

## Steps

1. **Check whether this should be a new story at all**:

   - Read recent or related stories in the same subsystem.
   - If the requested work still belongs to the same subsystem, validation boundary, and success surface as an existing story, STOP before bootstrapping a new ID.
   - Return the existing story to expand or reopen instead of fragmenting the work into a serial micro-story chain.

2. **Run the bootstrap script** only if a new story is still the honest move:

   ```bash
   .agents/skills/create-story/scripts/start-story.sh <slug> [priority]
   ```

   This creates `docs/stories/story-NNN-<slug>.md` from the template with the next available number. It outputs the file path.

3. **Fill in the story file** — Replace all placeholder text (`{...}`) with real content:
   - Title (replace the slug with the human-readable title)
   - Frontmatter references (`ideal_refs`, `spec_refs`, `adr_refs`,
     `depends_on`, `category_refs`, `compromise_refs`,
     `architecture_domains`, `roadmap_tags`, `legacy_system`)
   - Goal, acceptance criteria, out of scope, tasks, files to modify
   - Ideal refs, spec refs, ADR refs, and dependencies
   - Approach evaluation: simplification baseline, candidate approaches (AI-only, hybrid, code), repo constraints, existing patterns to reuse, and what eval distinguishes them
   - Workflow gates for build handoff, validation, and story closure
   - Canonical blocker fields: `Blocker Summary`, `Blocker Evidence`, and `Unblock Condition`. CineForge's methodology compiler currently reads those body sections directly, so keep them concrete and truthful when the story is `Blocked`.
   - Redundancy targets: old code or docs this story may make obsolete
  - UI verification work if the story touches the UI, including desktop and mobile coverage
   - If the feature is user-facing and requires both backend/API and UI to be usable, keep that end-to-end path in the same story by default. Split only when the scope is genuinely huge and independently deliverable.
   - Choose the honest initial state:
     - `Draft` when the story is still rough or missing verified substrate
     - `Pending` when the story is concrete and honestly buildable now
     - `Blocked` when the story is concrete enough to preserve and research already proves a real blocker
     - If the story starts `Blocked`, rewrite `## Plan` around the unblock path or blocker reassessment work. Do not leave stale implementation steps that assume the story can proceed immediately.

4. **Refresh generated planning surfaces** — Run:

   ```bash
   pnpm methodology:compile
   ```

   This rebuilds `docs/stories.md`, `docs/build-map.md`, and
   `docs/methodology/graph.json` from story metadata and methodology state.

5. **Verify** — Confirm the file exists, numbering is consistent, and the
   generated planning surfaces include the new story in the right order.

## Story Statuses

- **Draft**: Worth preserving, but still incomplete, underspecified, or not yet substrate-verified enough to claim build-readiness.
- **Pending**: Fully detailed ACs, tasks, files to modify, and honestly buildable now.
- **Blocked**: Concrete enough to preserve, but cannot honestly proceed now because of a named blocker with explicit evidence and an unblock condition.
- **In Progress**: Being built.
- **Done**: Validated complete.

## Conventions

- Acceptance criteria must be testable and concrete
- Explicitly call out what is in/out of scope
- Tasks should be implementation-oriented and ordered
- Always include the Approach Evaluation section — list candidate approaches (AI-only, hybrid, code) without pre-deciding. The story should identify what eval would distinguish approaches, what repo constraints matter, and which ADRs / existing patterns constrain the choice. Approach selection happens during build-story's eval-first gate with measured evidence.
- **Simplification baseline gate**: Every story involving new logic must answer: "Can a single LLM call already do this?" If untested, the first task should be measuring that baseline.
- Search `docs/decisions/` and `docs/design/` for relevant ADRs / decision records while drafting. If none apply, say so explicitly instead of leaving the field vague. If a scout doc or runbook materially constrains execution, cite it in Notes or Decision Context too.
- If the story changes existing behavior, name likely redundancy / removal targets up front. New code that supersedes old code should not silently accumulate parallel paths.
- If the story touches the UI, include explicit browser verification work in the task list for both desktop and mobile views. Static checks alone are not enough.
- **End-to-end user feature rule**: If a feature needs backend/API plus UI to be usable by a user, keep them in the SAME story by default. Do not create an "API now, UI later" split for an ordinary feature. Only split backend and UI into separate stories when the scope is genuinely huge (`L`/`XL`), independently valuable, and the dependency boundary is explicit in the story text.
- **Anti-fragmentation rule**: If the requested work still belongs to the same subsystem, validation boundary, and success surface as an existing story, expand or reopen that story instead of minting a new ID.
- **Blocked-story truth must stay inspectable**: If a story starts `Blocked`, replace the template `N/A` values in `Blocker Summary`, `Blocker Evidence`, and `Unblock Condition` with concrete blocker truth. Do not hide blocker state only in Notes or the work log.
- **Blocked-plan honesty**: If a story starts `Blocked`, the visible `## Plan` should describe the unblock path or blocker reassessment work, not stale "proceed now" implementation steps.
- If the story changes agent tooling or project instructions, include `make skills-check` in the task list.
- Always include the Workflow Gates section. These are not ordinary implementation tasks; they enforce the handoff chain: `/build-story` summary → `/validate` → `/mark-story-done`.
- If the story will involve running evals (extraction/pipeline behavior, golden comparison), add a task: "Run `/improve-eval` or equivalent mismatch investigation after the eval — classify all mismatches, fix golden if needed, document verified scores. Re-assess acceptance criteria against verified scores — raw scores do not determine story success."
- Always include the tenet verification checklist with individual checkboxes per tenet
- "Files to Modify" is gold for AI agents — fill it in when known
- Stories are living documents — the AI reads them repeatedly during implementation
- Every story should trace back to an Ideal requirement or spec compromise (via `Ideal Refs` / `Spec Refs`). Untraceable stories are potential scope creep.
- **Ideal alignment check** — Before writing the story file, verify alignment:
  - Does this story close an Ideal gap? → Good, proceed.
  - Does it move AWAY from the Ideal? → Push back. Explain why and suggest alternatives.
  - Does it only optimize a compromise without closing a gap? → Flag as low-value.
  - A story that references a spec compromise is not automatically aligned — it must move toward the Ideal, not entrench the compromise further.
  - If the story implements a new AI compromise: note whether a detection eval exists or should be created.
  - If the story adds or modifies an AI-powered capability: check `docs/evals/registry.yaml` for an existing eval. If none exists, note in the story that an eval entry should be created during implementation.

## Guardrails

- Never overwrite an existing story file — the script will error if the file exists
- Never commit or push without explicit user request
- Verify numbering is sequential — no gaps, no duplicates
- Do not leave ADR / decision references implicit for architecture-affecting stories
- Do not remove the frontmatter block — the methodology compiler depends on it

## Work Log Entry Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```
