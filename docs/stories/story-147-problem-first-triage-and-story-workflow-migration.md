---
id: "147"
title: "Problem-First Triage and Story Workflow Migration"
status: "Done"
priority: "High"
ideal_refs:
  - "Execution Ideal"
  - "radical transparency"
  - "R14 (Nothing is ever lost)"
spec_refs:
  - "spec:11"
  - "spec:11.1"
  - "spec:11.2"
  - "spec:11.3"
  - "spec:11.4"
adr_refs: []
depends_on:
  - "145"
  - "146"
category_refs:
  - "spec:11"
compromise_refs:
  - "B1"
  - "B2"
  - "B3"
  - "B4"
  - "B5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags: []
legacy_system: "Cross-Cutting"
---

# Story 147 — Problem-First Triage and Story Workflow Migration

**Priority**: High
**Status**: Done
**Ideal Refs**: Execution Ideal; radical transparency; R14 (nothing is ever lost)
**Spec Refs**: spec:11; spec:11.1; spec:11.2; spec:11.3; spec:11.4
**ADR Refs**: None found after search in local CineForge ADRs for post-migration story-progression semantics; reviewed `docs/design/decisions.md`, Stories 145 and 146, the user-supplied migration runbook, and doc-web commit `eac7b3e1ac20f2d6a60e372219bcc189cf64ca90`.
**Depends On**: Story 145, Story 146

## Goal

Repair CineForge's story workflow after the graph+state migration so it behaves
like one coherent planning system instead of a backlog-ceremony wrapper around
the new substrate. The local drift is already visible: `docs/spec.md` and
`AGENTS.md` still teach a four-status lifecycle while the compiler already
accepts `Blocked`; `/create-story` can only emit `Draft` or `Pending`;
`/build-story` still dead-ends on detailed `Draft` stories instead of doing the
obvious promotion step; and `/validate` plus `/mark-story-done` can still push
same-surface work toward `Rescope then close` instead of keeping one coherent
problem line together. This story should make triage problem-first, make story
status transitions honest, surface blocked-story truth in the canonical
artifacts, and keep user-facing work packaged as whole usable slices by default.

## Acceptance Criteria

- [x] This story records a CineForge-specific audit of the workflow failure mode
      with concrete local evidence from current skills, `docs/spec.md`,
      `AGENTS.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`,
      and the post-migration story chain through Stories 145 and 146.
- [x] CineForge has an explicit canonical story-progression policy for the
      graph+state framework that keeps `Draft`, `Pending`, `In Progress`,
      `Blocked`, and `Done`, with honest transitions between them:
  - [x] `/create-story` can emit `Draft`, `Pending`, or `Blocked` based on
        actual repo reality
  - [x] `Pending` means fully fleshed out and honestly buildable now
  - [x] `Blocked` means the work is concrete enough to preserve, but cannot
        proceed because of a named blocker with explicit evidence and an
        unblock condition
  - [x] `Draft` remains the right state for ideas or partial scopes, not a
        dumping ground for stories that are already buildable
- [x] `/create-story` defaults to whole usable slices rather than backend-only
      partials when functionality is meant to be user-facing:
  - [x] if a feature needs an operator or end-user UI to be used or inspected
        honestly, the default story shape includes that UI slice
  - [x] backend-only stories remain valid only when the functionality is
        genuinely non-UI or when the story explicitly records why the UI is
        intentionally deferred or owned elsewhere
- [x] `/triage`, `triage-stories`, `/create-story`, `/build-story`, `/validate`,
      and `/mark-story-done` all enforce the same anti-fragmentation rule:
      same subsystem + same validation boundary + same success surface stays in
      one story unless the work becomes materially distinct, crosses a new
      runtime or ownership seam, or would make validation unclear.
- [x] `/triage` and `triage-stories` use a problem-first weighting model:
  - [x] existing story shells do not gain major intrinsic priority merely
        because they exist
  - [x] continuity and momentum remain a positive bias for active or recently
        advanced work lines with an unresolved success surface
  - [x] story existence acts as packaging and tie-break context, not as a
        primary value signal
- [x] `/build-story` no longer hard-stops on a sufficiently detailed `Draft`
      story when the required sections and substrate already exist; it performs
      the obvious promotion or blocking path and records that decision
      explicitly.
- [x] Blocked-story recording becomes inspectable and consistent:
  - [x] the story template has a canonical place for blocker summary, blocker
        evidence, and unblock condition
  - [x] if the compiler and generated dashboards participate in story-truth
        consumption, blocked-story metadata is surfaced there well enough for
        triage and close-out to reason about it without hidden prose
- [x] `docs/spec.md`, `AGENTS.md`, the relevant methodology docs, lifecycle
      skills, runbooks, and generated planning surfaces all teach one
      consistent story-lifecycle contract after the change.
- [x] A reusable migration runbook exists for other repos, is updated only with
      settled and landed changes during implementation, and captures the final
      porting steps without preserving false starts.
- [x] A behavior-certification matrix exists in this story and is checked
      during implementation, covering the required workflow scenarios rather
      than relying only on clean compile output.
- [x] Fresh methodology validation passes after the last fix:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `make skills-check`
  - [x] `git diff --check`
  - [x] targeted methodology regression coverage for the new status and
        blocked-story behavior passes

## Out of Scope

- Rewriting the whole methodology architecture beyond the story-lifecycle,
  triage, compiler, and documentation surfaces that actually cause this problem
- Changing product-runtime behavior, schemas, or format-coverage truth outside
  methodology tooling
- Bulk-cleaning every historical story status oddity unless that cleanup is
  required to land the new canonical contract
- Creating a new methodology ADR unless implementation proves that post-migration
  story-progression semantics are now a hard-to-reverse architecture decision
- Reopening the graph+state substrate migration or legacy metadata backfill
  beyond the narrow follow-on changes this workflow repair genuinely needs

## Approach Evaluation

- **Simplification baseline**: No. This is a workflow-contract and consumer
  behavior problem, not a missing-ideas problem. A single LLM call can describe
  a better policy, but it cannot fix CineForge until the spec, AGENTS
  contract, lifecycle skills, compiler output, and generated dashboards all
  agree.
- **AI-only**: Wrong fit as the full solution. Better wording alone would not
  stop `/build-story` from hard-stopping on `Draft`, `/create-story` from
  minting duplicate same-line stories, or `/validate` from nudging coherent
  work toward premature split-and-close behavior.
- **Hybrid**: Expected winner. Use the current CineForge repo plus the supplied
  doc-web migration references to audit responsibilities, then make narrow
  deterministic changes to workflow skills, docs, templates, and compiler
  surfaces where inspectability actually matters.
- **Pure code**: Only partially viable. Some behavior belongs in
  `scripts/methodology-graph.js`, but the real contract also lives in
  `docs/spec.md`, `AGENTS.md`, skills, templates, and the new runbook.
- **Repo constraints / ADRs**: Stories 145 and 146 established the graph+state
  substrate and explicit story metadata. CineForge now has structured planning
  authority, so the remaining drift is in story semantics and consumer behavior.
  `docs/spec.md` and `AGENTS.md` still encode an older four-status model, while
  the compiler already accepts `Blocked`; the fix should align consumers toward
  one honest model instead of adding another compatibility layer.
- **Existing patterns to reuse**: Story 145, Story 146,
  `scripts/methodology-graph.js`, the current story frontmatter and template,
  existing methodology runbooks, and the supplied doc-web migration runbook and
  commit diff as reference material to adapt rather than copy blindly.
- **Eval**: Success is repo-native. The proof surface is clean methodology
  compile/check output, updated generated artifacts, regression coverage for the
  new blocked-story and status semantics, and manual inspection of the updated
  policy surfaces plus the behavior-certification matrix.

## Tasks

- [x] Audit the current workflow failure modes before changing tooling:
  - [x] record the local status-model mismatch between `docs/spec.md`,
        `AGENTS.md`, skills, and `scripts/methodology-graph.js`
  - [x] record where `/build-story` currently dead-ends on detailed `Draft`
        stories
  - [x] record where `/create-story` still treats story creation as the default
        even when work may belong to the same problem line
  - [x] record where `/validate` or `/mark-story-done` pressure same-surface
        work toward `Rescope then close`
  - [x] record at least one concrete local fragmentation or near-fragmentation
        example instead of relying on intuition alone
- [x] Lock the canonical five-status model and honest transition rules:
  - [x] update `docs/spec.md` story-lifecycle semantics to include `Blocked`
  - [x] update `AGENTS.md` so repo policy matches the intended skill behavior
  - [x] define what `Draft`, `Pending`, `In Progress`, `Blocked`, and `Done`
        mean in CineForge after the migration
  - [x] define the legal promotion, blocking, and close-out transitions
- [x] Patch `/triage` and `triage-stories` to become problem-first:
  - [x] keep Ideal/spec/state leverage ahead of backlog-shell existence
  - [x] preserve continuity bias for active unresolved work lines
  - [x] allow recommendations to continue, reopen, expand, or consolidate the
        existing problem line instead of only selecting the next story shell
- [x] Patch `/create-story` to choose the honest initial state and resist
      fragmentation:
  - [x] check whether the requested work actually belongs to a recent story in
        the same subsystem, validation boundary, and success surface
  - [x] stop before minting a new story ID when expansion or reopen is the
        honest move
  - [x] infer `Draft`, `Pending`, or `Blocked` from actual story completeness
        and substrate reality
  - [x] bias user-facing functionality toward UI-complete slices by default
- [x] Patch `/build-story` to promote or block based on evidence:
  - [x] promote a buildable `Draft` instead of dead-ending on status paperwork
  - [x] mark the story `Blocked` when exploration proves a real blocker
  - [x] keep small coherent deltas in the same story by default
- [x] Patch `/validate` and `/mark-story-done` so close-out stops fragmenting
      coherent work:
  - [x] prefer `Keep open` for same-surface remaining work
  - [x] reserve `Rescope then close` for genuinely separate remaining work
  - [x] preserve `Mark blocked` for named external blockers with evidence
- [x] Patch the story template and compiler surfaces where blocked-story truth
      must be inspectable:
  - [x] add canonical `Blocker Summary`, `Blocker Evidence`, and `Unblock Condition`
        sections to the story template
  - [x] update `scripts/methodology-graph.js` and generated surfaces if blocked
        metadata or status legends need to be emitted explicitly
  - [x] add targeted regression coverage for blocked-story graph output and
        story-status semantics
- [x] Create and maintain `docs/runbooks/migrate-problem-first-triage-and-story-workflow.md`
      as the cross-repo porting runbook, updating it only with settled decisions
      and landed changes during implementation.
- [x] Check whether the chosen implementation makes any skill wording, boilerplate
      status guidance, or promotion ceremony redundant; remove it or create a
      concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `make skills-check`
  - [x] targeted methodology regression tests
  - [x] `git diff --check`
  - [x] Backend minimum and UI static checks only if scope expands beyond docs,
        skills, templates, and methodology tooling
- [x] Search all docs and update any directly related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user/runtime data path becomes less auditable;
        this remains methodology-surface work
  - [x] **T1 — AI-Coded:** Future sessions can understand the workflow without
        rediscovering status semantics from conflicting files
  - [x] **T2 — Architect for 100x:** Remove process friction and duplicate
        story ceremony instead of entrenching it
  - [x] **T3 — Fewer Files:** Keep the contract aligned across existing surfaces
        rather than creating parallel status registries
  - [x] **T4 — Verbose Artifacts:** Record the audit, certification matrix,
        generated-output review, and final landed behavior explicitly
  - [x] **T5 — Ideal vs Today:** Move the methodology workflow closer to the
        execution ideal of low-friction, honest planning state

## Behavior Certification Matrix

- [x] Rough idea -> `Draft`
- [x] Concrete and buildable -> `Pending`
- [x] Concrete but blocked -> `Blocked`
- [x] Buildable `Draft` -> promote instead of stop
- [x] Proven blocker during build -> `Blocked`
- [x] Continuity beats unrelated shell
- [x] User-facing functionality -> UI-complete story by default
- [x] Validation keeps coherent work together
- [x] Close-out only splits truly separate work
- [x] Same-line request -> no new story ID

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: This belongs to methodology tooling and workflow
  policy only: `docs/spec.md`, `AGENTS.md`, `.agents/skills/`, the story
  template, methodology runbooks, and `scripts/methodology-graph.js`. No
  product-runtime module should absorb it.
- **Data contracts**: No runtime cross-layer Pydantic contracts are expected.
  The operational contract is story frontmatter plus the generated methodology
  outputs (`docs/methodology/graph.json`, `docs/stories.md`,
  `docs/build-map.md`). If blocked-story truth becomes inspectable in the
  graph, the compiler must derive it from canonical story files rather than a
  parallel registry.
- **File sizes**: `make check-size` run on 2026-04-04. Likely touched large
  files include `docs/spec.md` (`1434`), `AGENTS.md` (`679`), and
  `scripts/methodology-graph.js` (`944`), so edits there must stay narrow and
  explicit. Other likely surfaces are smaller: `docs/methodology/state.yaml`
  (`395`), `docs/methodology-ideal-spec-compromise.md` (`208`),
  `.agents/skills/build-story/SKILL.md` (`179`), `.agents/skills/validate/SKILL.md`
  (`175`), `.agents/skills/triage/SKILL.md` (`135`),
  `.agents/skills/create-story/templates/story.md` (`107`),
  `.agents/skills/create-story/SKILL.md` (`103`),
  `docs/runbooks/setup-methodology.md` (`130`),
  `docs/runbooks/triage-architecture.md` (`130`), and
  `docs/runbooks/triage.md` (`102`).
- **Decision context**: Reviewed `docs/design/decisions.md`, local ADR-001..003
  directory inventory, Stories 145 and 146, the user-supplied migration
  runbook, and doc-web commit `eac7b3e1ac20f2d6a60e372219bcc189cf64ca90`. No
  CineForge-local ADR currently settles story progression semantics after the
  graph+state migration.

## Files to Modify

- `docs/stories/story-147-problem-first-triage-and-story-workflow-migration.md` —
  execution artifact, audit notes, certification matrix, and proof log (new)
- `docs/spec.md` — update `spec:11.1` story-lifecycle semantics and any related
  methodology wording (`1434`)
- `AGENTS.md` — align repo policy with the repaired story workflow (`679`)
- `.agents/skills/triage/SKILL.md` — problem-first weighting and continuity
  guidance (`135`)
- `.agents/skills/triage-stories/SKILL.md` — anti-fragmentation and same-line
  continuation behavior (`92`)
- `.agents/skills/create-story/SKILL.md` — honest initial status selection and
  same-line story refusal (`103`)
- `.agents/skills/create-story/templates/story.md` — blocker sections and
  updated story-shape contract (`107`)
- `.agents/skills/build-story/SKILL.md` — promote buildable `Draft` stories and
  record real blockers (`179`)
- `.agents/skills/validate/SKILL.md` — keep coherent same-surface work together
  (`175`)
- `.agents/skills/mark-story-done/SKILL.md` — limit `Rescope then close` to
  genuinely separate follow-up work (`98`)
- `docs/methodology-ideal-spec-compromise.md` — align the methodology doctrine
  with the repaired workflow semantics (`208`)
- `docs/runbooks/triage.md` — align the triage runbook with the new weighting
  and continuity rules (`102`)
- `docs/runbooks/migrate-problem-first-triage-and-story-workflow.md` —
  cross-repo migration runbook for this workflow repair (new)
- `scripts/methodology-graph.js` — surface blocked-story truth and keep status
  legends or validation aligned with the canonical contract (`944`)
- `tests/unit/test_methodology_graph.py` — targeted regression coverage for
  blocked-story metadata and status behavior in the repo-native pytest surface
  (new)
- `docs/methodology/graph.json` — regenerated graph output (`6316`)
- `docs/stories.md` — regenerated story index (`303`)
- `docs/build-map.md` — regenerated build dashboard (`271`)
- `docs/methodology/state.yaml` — roadmap or campaign notes only if the landed
  behavior needs explicit state updates (`395`)

## Redundancy / Removal Targets

- Manual story-promotion ceremony that exists only because skills disagree
  about what `Draft` or `Pending` means
- Skill wording that treats story-shell existence as a primary priority signal
  instead of packaging context
- Close-out guidance that encourages fragmenting same-surface work into serial
  micro-stories
- Hidden blocked-story truth that lives only in prose or session memory instead
  of inspectable canonical artifacts

## Notes

- Local evidence at story creation:
  - `docs/spec.md` and `AGENTS.md` still teach a four-status story lifecycle,
    while `scripts/methodology-graph.js` already accepts `Blocked` and
    generated story-index text includes a blocked lane.
  - `.agents/skills/create-story/SKILL.md` can only emit `Draft` or `Pending`.
  - `.agents/skills/build-story/SKILL.md` still stops on `Draft` instead of
    verifying whether the story is already buildable.
  - `.agents/skills/validate/SKILL.md` and
    `.agents/skills/mark-story-done/SKILL.md` still preserve a strong
    `Rescope then close` path that needs tighter same-surface guardrails.
  - `.agents/skills/triage-stories/SKILL.md` still treats Draft/Pending labels
    more like backlog shells than anti-fragmentation-aware continuations.
- New story justification: this stays a new story instead of reopening Story
  145 or 146 because those stories already closed their own success surfaces
  cleanly: Story 145 owned the graph+state substrate migration, and Story 146
  owned legacy metadata backfill. This follow-on work changes workflow
  semantics, skill behavior, and certification scenarios after that substrate
  landed, so it is a distinct repair story rather than hidden scope creep.
- External reference material to adapt, not copy: the user-supplied migration
  runbook and doc-web commit `eac7b3e1ac20f2d6a60e372219bcc189cf64ca90`
  ("Repair story progression workflow").

## Plan

### Baseline / Approach Gate

- [ ] Baseline the current behavior before changing anything:
  - Current checks already pass despite the workflow drift:
    `pnpm methodology:check`, `make skills-check`, and `make check-size`
    all came back green on 2026-04-04.
  - There is no targeted methodology regression test yet for blocked-story
    metadata or repaired status semantics, which is why the repo can be
    semantically wrong while staying mechanically green.
  - `scripts/methodology-graph.js` already accepts `Blocked`, but the consumer
    contract above it is still inconsistent, so compile success alone is not
    enough evidence.
- [ ] Use the deterministic workflow-tooling path, not an AI-only experiment:
  - This story is orchestration, planning, compiler, and instruction plumbing.
    No live model selection or model benchmark is needed.
  - Doc-only is insufficient because the skills and compiler already disagree.
  - Compiler-only is insufficient because `docs/spec.md`, `AGENTS.md`, and the
    skill surface still teach the old behavior.
  - The repo-fit winner is a narrow deterministic pass across the canonical
    policy docs, lifecycle skills, story template, compiler/parser, a new
    regression test, and regenerated artifacts.

### Implementation Sequence

- [ ] Task 1 — Lock the canonical story lifecycle in the written policy surface.
  Files: `docs/spec.md`, `AGENTS.md`.
  Change: teach the honest five-status model (`Draft`, `Pending`, `In Progress`,
  `Blocked`, `Done`), define what each state means, clarify legal transitions,
  add the anti-fragmentation rule, and remove the blanket claim that `Draft`
  must always be promoted before `/build-story` can proceed.
  Impact / break risk: high policy reach, but low runtime risk; if these two
  files still disagree after the patch, future sessions will reintroduce the
  same drift.
  Done when: both docs describe the same lifecycle contract and explicitly
  reserve `Blocked` for named blockers with evidence plus an unblock condition.

- [ ] Task 2 — Repair the lifecycle skills and story template so behavior matches
  the policy.
  Files: `.agents/skills/create-story/SKILL.md`,
  `.agents/skills/create-story/templates/story.md`,
  `.agents/skills/build-story/SKILL.md`,
  `.agents/skills/validate/SKILL.md`,
  `.agents/skills/mark-story-done/SKILL.md`.
  Change: let `/create-story` emit `Draft`, `Pending`, or `Blocked`; add the
  same-line no-new-story stop; bias user-facing work toward UI-complete slices;
  let `/build-story` promote a buildable `Draft` or mark a real blocker instead
  of dead-ending on status paperwork; and tighten `/validate` plus
  `/mark-story-done` so same-surface remaining work prefers `Keep open` instead
  of defaulting toward `Rescope then close`. Add canonical `Blocker Summary`,
  `Blocker Evidence`, and `Unblock Condition` sections to the template.
  Impact / break risk: medium. This is the main agent-behavior surface, so bad
  wording here would directly affect future sessions. `make skills-check` is the
  required guardrail after these edits.
  Done when: the five lifecycle skills and the template all describe the same
  initial-state, promotion, blocking, and close-out behavior without fallback to
  the old four-status rules.

- [ ] Task 3 — Make triage explicitly problem-first and continuity-biased without
  duplicating logic.
  Files: `.agents/skills/triage-stories/SKILL.md`,
  `.agents/skills/triage/SKILL.md`, `docs/runbooks/triage.md`.
  Change: update ranking language so story-shell existence is packaging context
  and tie-break signal only; tell `triage-stories` to recommend continue,
  reopen, expand, or consolidate an existing line when that is the honest move;
  keep `/triage` mostly intact but add any missing wording needed so the leaf and
  meta layer are aligned.
  Impact / break risk: low-to-medium. `/triage` already mostly follows the
  target model, so edits there should stay light. The main risk is leaving the
  leaf skill stricter or looser than the meta skill.
  Done when: triage guidance clearly ranks real gap leverage and momentum above
  backlog-shell existence, and same-line continuation is an explicit allowed
  recommendation.

- [ ] Task 4 — Surface blocked-story truth in the compiler and add the missing
  regression harness.
  Files: `scripts/methodology-graph.js`,
  `tests/unit/test_methodology_graph.py`.
  Change: extend story parsing so blocker sections are extracted from the
  canonical story artifact, expose that metadata in the generated graph, and add
  narrow pytest coverage for blocked-story parsing/serialization plus any
  validation or status-contract logic that the migration changes.
  Impact / break risk: medium. `scripts/methodology-graph.js` is already a large
  file (`944` lines), so the patch needs to stay surgical and test-backed. The
  absence of existing tests here is the main gap this story needs to close.
  Done when: a targeted pytest catches the pre-migration drift, the compiler
  emits blocker metadata from story files, and `pnpm methodology:check` passes
  with the repaired contract.

- [ ] Task 5 — Land the CineForge runbook, regenerate artifacts, and certify the
  behavior scenarios.
  Files: `docs/runbooks/migrate-problem-first-triage-and-story-workflow.md`,
  `docs/methodology-ideal-spec-compromise.md`,
  `docs/stories/story-147-problem-first-triage-and-story-workflow-migration.md`,
  `docs/methodology/graph.json`, `docs/stories.md`, `docs/build-map.md`,
  `docs/methodology/state.yaml` only if implementation proves a live state note
  is necessary.
  Change: port the settled migration guidance into a CineForge-native runbook,
  update only the doctrine docs that directly repeat the lifecycle contract, run
  the compiler, and record Story 147's ten behavior-certification scenarios
  against the landed files and outputs.
  Impact / break risk: low runtime risk, medium methodology drift risk if the
  generated surfaces are not reviewed after regeneration.
  Done when: the runbook reflects only landed behavior, generated artifacts are
  refreshed and manually inspected, and Story 147 maps each certification
  scenario to specific local evidence.

### Repo-Fit / Optimality Evidence

- [ ] The chosen approach matches CineForge better than the alternatives:
  - `docs/spec.md` still codifies a four-status lifecycle, while
    `scripts/methodology-graph.js` and generated `docs/stories.md` already know
    about `Blocked`. This is local proof that docs-only or compiler-only would
    each leave half the system lying.
  - `AGENTS.md` and `.agents/skills/build-story/SKILL.md` still teach a
    hard-stop on `Draft`, but the story template and graph substrate are now
    mature enough to support honest promotion/blocking instead. That makes this
    a workflow-consumer repair, not a substrate rewrite.
  - Stories 145 and 146 already landed the graph/state migration and metadata
    backfill. Reopening them would hide a new behavior repair inside a closed
    success surface; a dedicated follow-on story is cleaner and easier to
    certify.
  - Existing checks staying green while the behavior is still wrong is local
    evidence that a narrow regression harness is the missing piece.

### Structural Health Check

- [ ] File-size and contract findings recorded before implementation:
  - `docs/spec.md` is `1434` lines, `AGENTS.md` is `679`, and
    `scripts/methodology-graph.js` is `944`; edits there must stay surgical.
  - No new runtime schema or cross-layer Pydantic contract is expected because
    this story only changes methodology docs, skill text, story template shape,
    and compiler output.
  - No new event types are expected.
  - New regression coverage belongs under `tests/unit/`, not a repo-root
    `tests/test_*.py` file; that is a small scope correction discovered during
    exploration and folded into this plan.

### Redundancy Plan

- [ ] Remove or overwrite the old workflow assumptions instead of layering new
  wording beside them:
  - eliminate blanket "Draft must be promoted before build" language where the
    repaired contract now permits evidence-based promotion
  - eliminate any skill wording that treats story existence itself as major
    priority
  - eliminate close-out guidance that nudges same-surface work into serial
    micro-stories
  - eliminate hidden blocker truth by moving it into canonical template +
    compiler surfaces

### Scope Adjustments

- [ ] Folded into this story as small, necessary scope corrections:
  - use `tests/unit/test_methodology_graph.py` as the regression surface instead
    of the earlier placeholder `tests/test_methodology_graph.py`
  - treat `.agents/skills/triage/SKILL.md` as a light-touch alignment pass,
    because exploration shows the bigger drift is in `triage-stories`
  - only touch `docs/methodology/state.yaml` or extra runbooks if the landed
    implementation leaves a direct lifecycle contradiction there

### Verification Plan

- [ ] Required checks after implementation:
  - `pnpm methodology:compile`
  - `pnpm methodology:check`
  - `make skills-check`
  - targeted pytest for `tests/unit/test_methodology_graph.py`
  - `git diff --check`
- [ ] Manual inspection targets after regeneration:
  - verify the story index and graph surfaces show the repaired status language
  - verify blocked-story metadata is inspectable in generated output, not trapped
    in prose
  - verify Story 147's certification matrix points to concrete local evidence
- [ ] UI/browser verification: not expected for the current plan because this is
  methodology tooling only. If implementation unexpectedly touches UI surfaces,
  add browser verification work before continuing.

### Human Approval / Blockers

- [ ] No external blocker is known right now.
- [ ] No new dependency, runtime schema change, public API change, or model
  choice is planned.
- [ ] Approval needed only to start implementation of the deterministic doc,
  skill, compiler, test, and generated-artifact pass above.

## Work Log

20260404-1905 — story creation: created Story 147 as the honest follow-on to
Stories 145 and 146 so CineForge can port the new problem-first triage and
anti-fragmentation workflow contract without pretending the graph+state
migration already solved it. Evidence=`docs/spec.md`, `AGENTS.md`,
`scripts/methodology-graph.js`, and the current lifecycle skills still disagree
about story statuses and close-out behavior; the supplied doc-web runbook and
commit provide a settled external reference for the intended repair. Next=`/build-story`
20260404-1914 — build-story exploration: confirmed the story is Ideal-aligned
execution tooling work, but the local workflow contract is still split across
an old four-status policy surface and a newer compiler/status consumer surface.
Evidence=`docs/spec.md:1295-1304` lists only `Draft`, `Pending`, `In Progress`,
and `Done`; `AGENTS.md:344-357` still says `Draft` must be promoted before
`/build-story`; `.agents/skills/create-story/SKILL.md:21,58-63` only emits
`Draft`/`Pending`; `.agents/skills/triage-stories/SKILL.md:27-35,64,74-80`
still treats `Draft` as promotion paperwork instead of a possible continuation
surface; `.agents/skills/validate/SKILL.md` and
`.agents/skills/mark-story-done/SKILL.md` keep a broad `Rescope then close`
path; meanwhile `scripts/methodology-graph.js:24,497,544` and generated
`docs/stories.md` already support `Blocked`, yet `rg` found zero current stories
using `status: "Blocked"`. Current checks `pnpm methodology:check`,
`make skills-check`, and `make check-size` all passed, which proves the repo is
missing targeted regression coverage for this workflow contract. Local pressure
examples also exist: Story 032 validation explicitly recommended `Rescope then
close`, and Story 127 validation spun out Story 139 as a dedicated follow-up
for unrelated stale-run polling noise. Risk=`docs/spec.md`, `AGENTS.md`, and
`scripts/methodology-graph.js` are all large-file surgical edits; repo-native
test placement should be `tests/unit/test_methodology_graph.py`, not the
earlier placeholder repo-root path. Next=present the implementation plan and
wait for approval
20260404-1709 — implementation complete: aligned the methodology workflow
contract across `docs/spec.md`, `AGENTS.md`, `docs/methodology-ideal-spec-compromise.md`,
the lifecycle skills, and `docs/runbooks/triage.md`; added the new cross-repo
runbook at `docs/runbooks/migrate-problem-first-triage-and-story-workflow.md`;
extended `scripts/methodology-graph.js` to parse blocker sections, require
evidence-backed metadata for `Blocked` stories, and surface blocker summaries in
the generated story index; and added targeted regression coverage in
`tests/unit/test_methodology_graph.py`. Evidence=`.venv/bin/python -m pytest
tests/unit/test_methodology_graph.py` passed (`2 passed`); `pnpm
methodology:compile` regenerated `docs/methodology/graph.json`,
`docs/stories.md`, and `docs/build-map.md`; `pnpm methodology:check` passed;
`make skills-check` and `./scripts/sync-agent-skills.sh --check` both passed;
`git diff --check` passed; manual artifact review confirmed the updated status
key and new `Blocker` column in `docs/stories.md` plus blocker fields in
`docs/methodology/graph.json`. Scope note=backend/UI runtime checks stayed out
of scope because this remained methodology tooling only. Next=`/validate`
20260404-1711 — evidence refresh: reran `pnpm methodology:compile`,
`pnpm methodology:check`, and `git diff --check` after the final story/runbook
bookkeeping edits so the generated planning artifacts and drift check reflect
the exact implementation handoff state. Evidence=`docs/methodology/graph.json`,
`docs/stories.md`, and `docs/build-map.md` were regenerated cleanly; drift
check remained green. Next=`/validate`
20260404-1718 — migration audit fix: careful post-implementation review found
one remaining live contradiction in `docs/methodology/state.yaml`: the roadmap
sequencing bias, current execution map, and methodology-tooling audit summary
still described methodology work as post-145/146 warning-debt cleanup and still
said no stories were in progress, which contradicted Story 147's active
`spec:11` follow-on role. Updated the canonical state to reference Story 147 as
the active methodology line, added the active campaign
`problem-first-story-workflow-repair`, refreshed the current execution map's In
Progress lane, and extended the methodology-tooling audit summary to include the
workflow-semantics repair. Evidence=`pnpm methodology:compile` regenerated
`docs/stories.md`, `docs/build-map.md`, and `docs/methodology/graph.json` with
the corrected state narrative; `pnpm methodology:check` then passed cleanly;
`git diff --check` remained clean. Next=`/validate`
20260404-1723 — validation: reran the full validation suite against the final
filesystem state and confirmed Story 147 is implementation-complete. Validation
initially caught a fresh Ruff failure in the new regression harness
(`tests/unit/test_methodology_graph.py` line-length violations), so I fixed that
test inline and reran the affected backend checks before finalizing the review.
Evidence=`make test-unit PYTHON=.venv/bin/python` passed (`660 passed, 146
deselected, 1 pre-existing warning`); `.venv/bin/python -m ruff check src/
tests/` passed; `.venv/bin/python -m pytest tests/unit/test_methodology_graph.py`
passed (`2 passed`); `pnpm methodology:compile` regenerated
`docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`;
`pnpm methodology:check` passed; `make skills-check` passed;
`./scripts/sync-agent-skills.sh --check` passed; `git diff --check` passed;
`pnpm --dir ui run lint` passed with 5 pre-existing fast-refresh warnings and no
errors; `cd ui && npx tsc -b` passed. Review outcome=no remaining live-surface
migration gaps found, no ADR conflict found, no redundant compatibility shim or
duplicate ownership introduced, and browser verification was not required
because no UI files changed. Next=`/mark-story-done`
20260404-1728 — mark-story-done: closed Story 147 after validation confirmed
the workflow migration is implementation-complete and no live-surface gaps
remain. Evidence=story workflow gates now show build + validation + close-out
complete; `pnpm methodology:compile` and `pnpm methodology:check` were rerun to
refresh the generated planning surfaces after the status flip; the generated
story index and current execution map now move Story 147 out of the active lane
and preserve the repaired status contract and blocker surfacing. Next=`/check-in-diff`
