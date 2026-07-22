---
id: "209"
title: "Evidence-First Evaluate-Model Workflow"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "Execution Ideal (AI owns technical workflow)"
spec_refs:
  - "spec:8"
  - "spec:11.3"
  - "spec:11.4"
adr_refs: []
depends_on:
  - "035"
  - "208"
category_refs:
  - "spec:8"
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "agent-tools"
legacy_system: "Cross-Cutting"
---

# Story 209 — Evidence-First Evaluate-Model Workflow

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (transparency & control), Execution Ideal (AI owns technical workflow)
**Spec Refs**: spec:8, spec:11.3, spec:11.4
**ADR Refs**: None
**Depends On**: Story 035, Story 208

## Goal

Give CineForge a self-contained `/evaluate-model <natural-language brief>`
workflow that evaluates one or more models fairly instead of changing a model
name and interpreting the first harness output. The workflow must discover
current API facts, qualify production transport and structured output, use
CineForge's real model-slot evidence and provider environment, debug failures
before attributing quality, preserve reproducible evidence, and return an
explicit per-slot adoption decision without silently changing defaults.

## Eval Ladder Context

- **Root / parent need**: `spec:8` requires trustworthy cost, quality, and
  model-selection evidence; R12 and the Execution Ideal require the AI to expose
  why it made a model decision while owning the technical process.
- **Parent surfaces**: the maintained registry, Promptfoo model-slot tasks,
  Story 035's benchmark substrate, and Stories 204–208's model-refresh evidence.
- **Measured failure mode**: recent refreshes exposed transport/config failures,
  same-family model misidentification, unsupported parameters, token-budget
  truncation, stale runtime assumptions, and materially contaminated QA/video
  truth surfaces. A naive model-name swap can therefore produce an unfair or
  inverted verdict.
- **Child baseline**: a forward-testable skill and paired runbook that interpret
  natural briefs, qualify each candidate/surface, enforce bounded fair runs,
  classify failures, and record exact decision evidence. No provider eval is
  required to validate this documentation-only workflow rollout.

## Acceptance Criteria

- [x] `/evaluate-model` accepts broad, narrow, rambly, multi-model, audit-only,
  and force-fresh briefs without requiring separate discovery/story/eval
  commands from the user.
- [x] Execution refreshes current first-party docs and exact live identity,
  qualifies access/native/production-contract/harness-parity transport, fails
  closed on prompt/schema/served-model defects, and keeps infrastructure
  failures separate from model quality.
- [x] A default US$5 all-provider cap, predeclared arms/retries, no-cache rules,
  progressive screening, and independent per-slot progression bound spend and
  prevent opportunistic tuning.
- [x] CineForge-specific guidance resolves the actual benchmark workspace,
  loads credentials only through `with_cine_forge_provider_env.py`, reads
  dynamic registry gates, and distinguishes actual runtime defaults from best
  eligible maintained evidence.
- [x] Structural plus rubric scoring remains mandatory; judge-provider bias,
  source-backed golden inspection, and the Story 208 QA/video quarantine cannot
  be silently bypassed.
- [x] Exact clean/dirty code and artifact provenance, registry/story/methodology
  recording, mismatch taxonomy, and `not measured` semantics are explicit.
- [x] AGENTS, eval README, Promptfoo runbook, changelog, canonical skill links,
  and generated planning surfaces are consistent.
- [x] Initial skill/methodology/diff checks and local no-provider forward tests
  pass, with results recorded in the work log.

## Out of Scope

- Calling any provider or running a paid/free model eval during this rollout.
- Changing `docs/evals/registry.yaml`, `docs/evals/models-available.yaml`, model
  lists, model defaults, provider adapters, benchmark task YAML, or runtime code.
- Repairing the contaminated `qa-pass` or `video-understanding` fixtures; this
  story only quarantines them until separately source-repaired and revalidated.
- Committing, pushing, deploying, or marking the story Done.

## Approach Evaluation

- **Simplification baseline**: an unconstrained capable agent can run Promptfoo,
  but the doc-web pilot and CineForge Stories 204–208 show that generic
  instructions do not reliably catch invalid transport, structured-output,
  model-identity, stale-default, judge, or golden failures.
- **AI-only**: rely on model judgment with no durable workflow. Rejected because
  the recurring failures are exactly omissions in model judgment under time and
  context pressure.
- **Hybrid**: use one concise judgment-oriented skill plus a mechanical runbook,
  existing discovery/env/Promptfoo/metric tools, dynamic repo truth, and human
  authority gates. Chosen because it preserves agent adaptability while making
  fragile evidence boundaries explicit.
- **Pure code**: a script could enforce paths and response fields, but cannot
  select decision-bearing slots, interpret ambiguous briefs, inspect source
  goldens, or make scoped adoption judgments. Existing scripts remain the
  deterministic substrate rather than a new orchestrator.
- **Repo constraints / decisions**: Ideal R18 requires evidence before model
  improvements remove scaffolding; `spec:8` is a hold lane where value
  maintenance and current truth matter more than one-off model tweaks. No
  architecture decision record governs this workflow-only adaptation.
- **Existing patterns to reuse**: doc-web's proven `/evaluate-model` semantics,
  CineForge's `discover-models`, `create-story`, `create-eval`, `improve-eval`,
  provider-env wrapper, Promptfoo runbook, dual scoring, registry, and recent
  model-refresh stories.
- **Eval**: static skill validation plus local forward-test reasoning over a
  broad launch request, narrow slot request, multiple candidates, read-only
  audit, and force-fresh reproduction. Provider calls are intentionally absent.

## Tasks

- [x] Read Ideal/spec/state/graph/build-map, eval README,
  Promptfoo runbook, current registry evidence, and recent model-refresh stories.
- [x] Create the canonical `/evaluate-model` skill under 500 lines with portable
  natural-language semantics and CineForge-specific evidence contracts.
- [x] Add the matching `docs/runbooks/evaluate-model.md` and route AGENTS/eval/
  Promptfoo guidance to it.
- [x] Preserve dynamic slot gates, runtime-default versus best-eligible truth,
  dual scoring/judge-bias handling, golden taxonomy, and QA/video quarantine.
- [x] Check whether the implementation makes existing paths redundant; keep
  `/create-eval` and `/improve-eval` as subordinate capability/repair workflows
  rather than duplicating or deleting them.
- [x] Run required checks for touched scope:
  - [x] `make skills-check`
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `git diff --check`
- [x] Run local no-provider forward-test reasoning across representative
  natural-language invocation shapes.
- [x] Confirm no UI, backend/runtime, model, provider, benchmark task, registry,
  or golden file changed; backend/UI/browser checks are not applicable.
- [x] Search docs and update AGENTS, eval README, Promptfoo runbook, dedicated
  evaluate-model runbook, changelog, story, and generated planning owners.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No project data or provider secret is read or
    mutated; future evals require payload eligibility.
  - [x] **T1 — AI-Coded:** A future agent can infer scope and run the complete
    evaluation from one natural-language command.
  - [x] **T2 — Architect for 100x:** The workflow reads live provider/runtime
    truth and does not hard-code model lineups, defaults, or scores.
  - [x] **T3 — Fewer Files:** One canonical skill and one required runbook reuse
    all existing scripts and eval workflows.
  - [x] **T4 — Verbose Artifacts:** Story, registry, attempt, raw-result, and
    hash-manifest requirements preserve handoff truth.
  - [x] **T5 — Ideal vs Today:** Better models can collapse slots only after
    current decision-grade evidence, avoiding permanent workaround bias.

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

- **Owning class/module**: `.agents/skills/evaluate-model/SKILL.md` owns agent
  decision behavior; the paired runbook owns repeatable operational mechanics.
  Existing discovery, env, Promptfoo, scorer, and registry owners remain intact.
- **Data contracts**: no application or inter-layer data contract changes. The
  skill consumes existing registry/task/result contracts and demands fail-closed
  provider schema/identity evidence during future evaluations.
- **File sizes**: before changes, `AGENTS.md` was 709 lines,
  `docs/evals/README.md` 212, `docs/runbooks/promptfoo.md` 99, and
  `CHANGELOG.md` 3,226. The new skill is 360 lines, below the 500-line skill
  budget; the new runbook is 217 lines. Large documentation files receive only
  narrow routing additions and no source-code owner is touched.
- **Decision context**: reviewed Ideal R12/R18, the `spec:8` and `spec:11`
  methodology lanes, Stories 204–208, and the user-approved Conductor Alignment
  042 rollout plan. No new ADR is needed because this adapts established eval
  workflow rather than changing product/runtime architecture.

## Files to Modify

- `.agents/skills/evaluate-model/SKILL.md` — canonical self-contained model-eval workflow (new; 360 lines)
- `docs/runbooks/evaluate-model.md` — operational companion runbook (new; 217 lines)
- `AGENTS.md` — route model evaluations and preserve local evidence rules (709 lines before change)
- `docs/evals/README.md` — distinguish model evaluation from eval creation/repair (212 lines before change)
- `docs/runbooks/promptfoo.md` — env-wrapper, workspace, scoring, and quarantine rules (99 lines before change)
- `CHANGELOG.md` — Story 209 operator-facing change record (3,226 lines before change)
- `docs/stories/story-209-evaluate-model-evidence-first-workflow.md` — plan, scope, and work log
- `docs/methodology/state.yaml` — refresh methodology-tooling audit freshness for Story 209
- `docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json` — generated planning surfaces

## Redundancy / Removal Targets

- Replace the old manual "add a provider block and run Promptfoo" new-model
  shortcut in AGENTS with `/evaluate-model` routing.
- Keep `/create-eval`, `/improve-eval`, `/discover-models`, and the Promptfoo
  runbook; they remain focused subordinate workflows rather than duplicates.
- Do not add a second orchestration script or tool-specific skill copy.

## Notes

- This is a documentation/tooling build. No runtime smoke or browser proof is
  applicable.
- User approval plus Conductor Alignment 042 satisfied the build-story plan
  gate for this scoped rollout. Any future `/evaluate-model` invocation still
  obeys the skill's explicit spend, privacy, default-change, and commit gates.
- The skill intentionally contains no historical scores, default model names,
  or fixed fixture counts. It discovers those from current repo truth.

## Plan

1. **Add the canonical skill** — adapt the proven doc-web workflow to
   CineForge's natural briefs, local methodology, model-slot decisions,
   benchmark workspace, credential wrapper, dual scoring, dynamic gates, and
   exact provenance. Done when the skill is self-contained and under 500 lines.
2. **Add and route the runbook** — create the required 3+-step runbook and
   update AGENTS/eval/Promptfoo guidance without duplicating the full skill.
   Done when model evaluation, capability-eval creation, and eval repair have
   distinct owners.
3. **Preserve local truth boundaries** — encode runtime-default versus
   best-eligible comparison, independent slots, judge-bias handling, and
   QA/video quarantine. Done when raw contaminated or invalid transport evidence
   cannot honestly drive adoption.
4. **Generate and verify** — sync canonical skill links, compile/check
   methodology, run diff hygiene, and forward-test representative invocation
   shapes without provider calls. Done when checks pass, independent validation
   is clean, and the story closes through `/mark-story-done`.

## Work Log

20260722-1656 — exploration-and-approved-plan: verified Story 208 is the highest
existing story and bootstrapped Story 209 with the repo script. Read AGENTS,
Ideal/spec/state/graph/build-map, eval registry/README,
Promptfoo/create-story/build-story/create-cross-cli-skill guidance, recent model
refresh stories, CineForge env wrapper, and the proven doc-web skill. `make
check-size` showed only existing source/UI large-file watchpoints; this rollout
touches docs/skills only. User approval and Conductor Alignment 042 authorize
the written plan. Next step: finish local skill/methodology checks and no-provider
forward tests, then leave the story In Progress for independent `/validate`.

20260722-1656 — implementation: added a 353-line canonical skill and 210-line
runbook, routed AGENTS/eval/Promptfoo docs, and added the changelog entry. The
adaptation preserves natural/multi/audit/force-fresh handling, the $5 cap,
provider-contract ladder, fail-closed schema/served-model rules, exact dirty-run
provenance, dynamic slot gates, runtime-default versus best-eligible evidence,
structural-plus-rubric scoring with judge-bias controls, independent-slot
progression, and explicit not-measured semantics. Story 208's contaminated
QA/video evidence is quarantined until source-repaired and revalidated. No
provider call or product/eval/runtime mutation occurred. Next step: run the
declared static checks and local forward tests.

20260722-1658 — methodology-compile-correction: the first compile correctly
rejected stale architecture-audit freshness metadata after Story 209 added the
`methodology_tooling` domain. Updated only that canonical state counter/reference
so generated planning surfaces can represent the new story honestly; no
architecture finding or audit conclusion changed. Next step: rerun compile/check.

20260722-1704 — no-provider-forward-tests: manually exercised the skill as an
invocation dispatcher without API calls or repo mutations. A broad "new model,
eval it" request selects current exact identity, a minimal decision-bearing
slot portfolio, the default $5 cap, and no implicit default change. A narrow
script-bible-only request preserves its slot/settings/exclusions and compares
against both runtime default and best eligible evidence. A rambling two-model
brief with a later scope correction honors the correction, uses shared
comparators, and screens progressively. An evidence-only audit makes no calls,
harness run, artifact, or write. A workflow-acceptance force-fresh request
reruns candidate plus incumbent with distinct uncached artifacts, while a
candidate-variance request may remain candidate-only and makes no superiority
claim. An unavailable preview/API produces access/capability not measured and a
defer result rather than an invented benchmark. All dispatches retained privacy,
retry, spend, schema, served-model, quarantine, provenance, and commit/default
boundaries. No semantic ambiguity requiring a skill change remained.

20260722-1707 — initial-validation: `make skills-check` passed with 40 canonical
skills and intact compatibility links; the evaluate-model skill is 353 lines,
below the 500-line budget. `pnpm methodology:compile` regenerated
`docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`, and
`pnpm methodology:check` confirmed they are current. `git diff --check` passed.
Only pre-existing methodology warnings remain for two due/open architecture
audit domains and the stale UI scout; this docs-only story did not create them.
The generic system `quick_validate.py` was also attempted through CineForge's
Python environment: it rejected the repo-required `user-invocable` extension as
an unknown key, while CineForge's authoritative cross-CLI validator accepted
the same frontmatter. No backend/UI tests or runtime smoke were run because no
runtime source changed, and no provider calls occurred. Build is complete;
leave Story 209 In Progress for independent `/validate`.

20260722-1730 — independent-hardening-and-validation: findings-first review
caught and repaired four rollout defects before landing: Story 209 could
incorrectly make C1/C2/C3/C5 actionable through its docs-only evidence;
configuration selection lacked an explicit held-out/repeated-confirmation
promotion rule; Promptfoo examples did not pin `PROMPTFOO_PYTHON` to the
resolved CineForge interpreter; and stale fixed-judge/all-provider wording
conflicted with dynamic narrow evaluation. The same pass removed inaccurate ADR
references, made discovery and metric commands checkout/interpreter-safe, and
restored explicit access/transport/reliability/capability verdict vocabulary.
Fresh methodology compile/check, skill/link validation, diff hygiene, and
secret-pattern review passed. Scoped Ruff over `src/ tests/` passed. The unit
suite passed with `917 passed, 186 deselected` and one known unregistered
acceptance-marker warning. Repo-wide Ruff still reports 25 pre-existing findings
in untouched skill/docs/scripts files; no changed Python file exists in this
story. The final skill is 360 lines and runbook 217 lines. No provider call,
registry/default/adapter/task/golden/runtime/UI change, or deployment occurred.
Independent review found no remaining material issue; marked Story 209 Done.
