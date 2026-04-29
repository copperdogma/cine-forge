---
name: setup-methodology
description: Canonical installer/normalizer for the full Ideal-first methodology package after Ideal/spec intake exists, including upgraded triage, core story-loop, and loop-verify bootstrap
user-invocable: true
---

# /setup-methodology [greenfield|retrofit|adr-021-migration|refresh]

> Alignment check: Before choosing an approach, verify it aligns with
> `docs/ideal.md`, `docs/methodology/state.yaml`,
> `docs/methodology/graph.json`, and relevant decision records in
> `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`,
> respect its limitation type and evolution path. If none apply, say so
> explicitly.

Use this skill as the **canonical full-package setup entrypoint** for the
methodology package. It assumes project-specific `docs/ideal.md` and
`docs/spec.md` already exist from `/init-project` or equivalent source-backed
intake. It replaces the old phased setup surface with one integrated package
installer/normalizer.

`/setup-methodology` does not discover a blank project's idea. For a greenfield
folder with no real Ideal/spec, stop and route to `/init-project new-idea`.

## What This Skill Owns

- `docs/ideal.md` / `docs/spec.md` / `docs/methodology/state.yaml` / `docs/methodology/graph.json` alignment after Ideal/spec intake
- `docs/setup-checklist.md` working copy generation from the bundled template
- eval harness bootstrap, day-zero golden workspace bootstrap, and root eval
  ladder setup where the repo owns product evidence
- story/decomposition bootstrap
- core story-loop bootstrap: `/create-story`, `/build-story`, and `/validate`
  guidance for optional sidecar evidence, plan-gated delegation, parallel
  validation, and `/loop-verify` escalation
- upgraded triage bootstrap: `/triage`, lane-packet leaf skills,
  `/triage-health`, sparse-safe triage facts, and wrapper sync
- upgraded verification bootstrap: `/loop-verify` materiality/no-hard-cap
  guidance with a minor-only stop rule
- optional recurring methodology lanes already encoded in the package, such as
  `architecture_audits` / `/triage-architecture` and `ui_scout` /
  `docs/ui-scout*`
- `AGENTS.md` methodology wiring and state/graph-first operating rules
- cross-CLI skill sync via `scripts/sync-agent-skills.sh`
- repo-specific package variants, including Conductor's supervisor routing,
  scouting, and alignment surfaces when the repo identity is Conductor

Use the bundled checklist template at
`.agents/skills/setup-methodology/templates/setup-checklist.md` and the mode
reference at `.agents/skills/setup-methodology/references/modes.md` when that
bundle exists. If a repo intentionally carries a lean local setup package
without those files, refresh `docs/setup-checklist.md` directly and record the
local variant in the setup summary.

## Modes

### `greenfield`

For a new project after `/init-project new-idea` or equivalent intake has
produced reviewed `docs/ideal.md` and v0 `docs/spec.md`. Install and normalize
the full methodology package around those authored truths: state/graph,
checklist, eval + golden bootstrap, story bootstrap, and public skill surface.

### `retrofit`

For an existing project that needs the full methodology package applied or
reapplied. Read the repo thoroughly, classify what already exists, preserve
provenance, and bring the project onto the canonical package. If the project
lacks a real Ideal/spec, route through `/init-project from-existing` first to
reconstruct them from code/docs and user conversation.

### `adr-021-migration`

For repos that already use Ideal-first but still need the ADR-021 structure:
dual ideal, category-aligned spec/state structure, execution constraints, and
state/graph-centered planning.

### `refresh`

For repos that already have the package but need it re-synced: update AGENTS,
runbook, checklist structure, eval/golden references, and public-surface docs
without redoing the whole bootstrap conversation.

## Repo Package Variants

Keep this setup skill text byte-identical across Conductor and the tracked
product repos. Apply the package according to repo identity rather than
silently forking the setup contract.

- **Product repos** use the full product methodology package: Ideal/spec,
  state/graph, eval/golden bootstrap or explicit deferral, story loop, triage,
  optional recurring lanes, AGENTS, and wrappers.
- **Conductor** uses the supervisor package: `projects.yaml`, `inbox.md`,
  `docs/scout.md`, `docs/scout/`, `docs/align-projects.md`,
  `docs/alignments/`, and supervisor skills such as `/align-projects`,
  `/scout`, and `/triage-stories` are first-class setup surfaces. Do not import
  product-only eval/golden/UI lanes into Conductor unless its Ideal/spec/state
  explicitly add them; mark them absent or deferred instead. Still install or
  refresh the shared triage, core story-loop, and `/loop-verify` guidance so
  Conductor follows the same practical loop: triage, create story, build,
  validate, close out.

## Working Rules

1. **Ideal/spec preflight is mandatory.** Before installing package surfaces,
   verify `docs/ideal.md` and `docs/spec.md` exist and are project-specific.
   They may be v0, but they must be real authored artifacts. If either is
   missing, generic, only a placeholder, or not yet reviewed for cohesion
   against raw intake, stop and route to `/init-project`; do not fabricate them
   from the setup template.
2. **Create or refresh the checklist first after preflight.** Copy the bundled
   template to `docs/setup-checklist.md` if the template exists and the working
   checklist is missing or still an older one-off format. If the repo has no
   bundled template by design, refresh the local checklist directly. Work from
   that file and check items off as the run proceeds.
3. **State/graph-first operating rule:** planning and triage start from
   `docs/methodology/state.yaml` and `docs/methodology/graph.json`.
   Implementation starts from the active story, but must read the relevant
   `spec:N` sections plus the matching state/graph slice first.
4. **Treat goldens and evals as baseline setup when the repo owns product
   evidence.** Day-zero product setup is incomplete
   until the repo has the golden workspace, the eval harness/story, and a root
   Ideal eval or explicit deferral. For AI-capability work, preserve the
   initial decomposition ladder: root eval, known parent failures, child evals,
   and the implementation stories that exist because those evals fail. For
   Conductor or other non-product supervisor packages, preserve local
   supervisor evidence surfaces instead and mark product-only evidence lanes
   absent or deferred.
5. **Keep recurring work separate.** The bootstrap skill installs the package
   and preserves optional recurring lanes that are already part of it. Ongoing
   product work uses `/create-eval`, `/improve-eval`, `/align`,
   `/triage-architecture`, the local `ui-scout` lane when `state.ui_scout`
   exists, story/build skills, and normal ADR/story workflows. Conductor
   supervisor work uses `/align-projects`, `/scout`, `/triage-stories`, the
   core story loop, and normal ADR/story workflows.
6. **Core story-loop setup is part of refresh.** Install or refresh
   `/create-story`, `/build-story`, and `/validate` with the accepted
   core-loop guidance: the main thread owns Ideal/spec judgment, story
   boundaries, build plans, and final validation disposition; subagents gather
   bounded sidecar evidence or handle disjoint non-blocking work only when that
   reduces risk; sequential fallback is explicit; and `/loop-verify` escalation
   is reserved for repeated material review/fix rounds. Do not make subagents
   mandatory for ordinary setup, no-code repos, routine story creation, or
   small validation passes.
7. **Canonical public surface only.** AGENTS/docs should advertise
   `/init-project` for greenfield idea intake and `/setup-methodology` for
   full package setup. Do not reintroduce the old phased setup skills.
8. **No-code repos get a sparse package, not a long forensic loop.** When a
   repo has little or no code, install the methodology surfaces quickly around
   the authored Ideal/spec, mark unavailable lanes as absent or deferred, and
   avoid asking agents to infer runtime truth that cannot exist yet.
9. **Shared skill surfaces should be copied exactly.** When this setup skill or
   the shared triage/core story-loop/loop-verify package changes, upgrade one
   source copy, perform a local propagation sweep, then copy the exact shared
   files to the other repos and run wrapper checks. Do not independently
   rewrite the same skill in each repo.

## Greenfield / No-Code Fast Path

For a repo with no meaningful code yet, the goal is to install a useful package
without spending many rounds proving absent evidence. Do this:

1. Verify `/init-project` or equivalent intake produced real `docs/ideal.md`
   and `docs/spec.md`. If not, stop and route back to intake.
2. Create the smallest coherent methodology state/graph that reflects the
   authored Ideal/spec. Do not invent implementation history.
3. Install the shared skill package exactly:
   - `/triage` with main-thread Ideal/spec synthesis, top-three recommendations,
     and one final yes-ready recommendation
   - `/create-story` with optional sidecar evidence for non-trivial story
     scoping while the main thread owns the final story boundary
   - `/build-story` with delegation only after the plan gate, only for bounded
     non-blocking work with disjoint ownership
   - `/validate` with optional parallel validation packets and escalation to
     `/loop-verify` only when a complete material clean round matters
   - triage leaf skills in packet mode where their lanes are present
   - `/triage-health` for sparse health/freshness packets
   - `/loop-verify` with material-vs-minor stop rules and no hard round cap
4. Add a sparse-safe triage fact collector when the repo has enough tooling to
   support one. It should report absent/deferred/empty statuses directly rather
   than treating missing reports, missing codebase scans, missing UI scouts, or
   missing eval attempts as broken files.
5. Mark optional lanes honestly:
   - `architecture_audits`: deferred until there is architecture to audit
   - `ui_scout`: absent or deferred until there is a real UI surface
   - eval/golden lanes: present only when there is an actual initial eval or an
     explicit deferral with a trigger
   - codebase-improvement: absent until there is enough code for a scan
6. Run cheap validation only: skill wrapper check, methodology compile/check,
   direct fact JSON parse if a fact script exists, and whitespace/diff checks.
   Do not run heavy evals, browser scouts, provider calls, or repeated
   subagent verification just because evidence is absent by design.
7. Before the first `/loop-verify`, run a local propagation sweep for shared
   semantics across the main triage skill, core story-loop skills, leaves,
   health runbook, fact script, tests, and wrappers. This prevents Echo-style
   long loops where the same fact meaning is rediscovered one adjacent surface
   at a time.

## Steps

1. **Determine mode from repo reality** — new repo, retrofit, ADR-021 migration,
   or refresh. If the user supplied a mode, verify it matches what the repo
   actually looks like.

2. **Run the Ideal/spec preflight**:
   - Confirm `docs/ideal.md` exists and is not a blank/template placeholder
   - Confirm `docs/spec.md` exists and has real project-specific compromise or
     constraint content
   - For greenfield, confirm the artifacts came from `/init-project` or
     equivalent idea intake
   - Confirm the Ideal/spec were reviewed against raw intake for coverage,
     contradictions, duplicate ideas, and late-arriving Ideal material
   - If this fails, stop and tell the user to run `/init-project new-idea` or
     `/init-project from-existing`

3. **Read the canonical references**:
   - `docs/runbooks/setup-methodology.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - relevant ADRs in `docs/decisions/`
   - `AGENTS.md`
   - existing setup/eval/golden/story docs if present

4. **Create or refresh `docs/setup-checklist.md`** from the bundled template
   when the template exists; otherwise refresh the repo's local checklist
   directly. Replace placeholders and check items off as work is completed.
   Never treat the checklist as optional.

5. **Install or refresh the methodology package around the authored Ideal/spec**:
   - `docs/ideal.md` — product + execution ideal, preserved/refined from intake
   - `docs/spec.md` — category-aligned constraint source, preserved/refined from intake
   - `docs/methodology/state.yaml` — central operational state
   - `docs/methodology/graph.json` — compiled methodology joins
   - `docs/stories.md` — generated story view
   - `docs/runbooks/setup-methodology.md` — prose front door
   - core story-loop skill surfaces — `/create-story`, `/build-story`, and
     `/validate` with accepted sidecar/delegation/parallel-validation guardrails
   - optional recurring lane docs/routing such as `docs/ui-scout.md`, its
     companion runbook, and AGENTS/triage references when `state.ui_scout`
     exists
   - `AGENTS.md` — canonical public surface and operating rules
   - for Conductor, preserve supervisor surfaces instead of product-only lanes:
     `projects.yaml`, `inbox.md`, `docs/scout.md`, `docs/scout/`,
     `docs/align-projects.md`, and `docs/alignments/`

6. **Bootstrap baseline evidence infrastructure**:
   - For Conductor or another non-product supervisor package, preserve local
     supervisor evidence surfaces and explicitly defer product-only golden/eval
     lanes unless the repo state adds them.
   - For product evidence lanes, continue with the golden/eval checks below.
   - Ensure the golden workspace exists and matches project schemas
   - Ensure the root Ideal eval/golden exists or is explicitly deferred with a
     reason and a next trigger
   - Ensure any day-zero child evals record their parent eval and measured
     failure mode
   - Ensure the eval package exists and is wired together: `docs/evals/README.md`,
     `docs/evals/registry.yaml`, `docs/evals/attempt-template.md`,
     `docs/runbooks/promptfoo.md` when promptfoo applies, and the linked
     `tests/fixtures/golden/` workspace or repo-equivalent locations
   - Ensure day-to-day eval creation and improvement paths are documented and
     installed (`/create-eval`, `/improve-eval`)

7. **Bootstrap story/planning infrastructure**:
   - Ensure state/graph-backed story decomposition exists
   - Ensure the story framework points back to methodology state/graph + spec,
     not to a stale feature-map or legacy dashboard model
   - Ensure `/create-story` preserves optional sidecar evidence only for
     non-trivial scoping and keeps the main thread responsible for the final
     story boundary
   - Ensure `/build-story` preserves the human plan gate and allows delegation
     only after that gate for bounded, disjoint, non-blocking work
   - Ensure `/validate` preserves main-thread final disposition while allowing
     optional parallel validation packets and `/loop-verify` escalation for
     material repeated review/fix rounds

8. **Install the upgraded triage, core story-loop, and verification surface**:
   - Install or refresh `/triage` as the orchestration skill: Ideal/spec first,
     main-thread facts, neutral lane packets, top three recommendations, and
     one final yes-ready recommendation.
   - Install or refresh `/create-story` so subagents are optional sidecars for
     non-trivial evidence gathering only. The main thread decides whether a new
     story is warranted, sets story boundaries, and owns the final artifact.
   - Install or refresh `/build-story` so delegation starts only after the
     required plan/human gate and only for bounded sidecar exploration,
     disjoint implementation slices, tests, or review work. The main thread
     owns the plan, scope coherence, and final handoff.
   - Install or refresh `/validate` so parallel validation packets can inspect
     changed files, acceptance criteria, checks, and architecture/intent fit
     when the diff warrants it. The main thread synthesizes the report and
     final grade/disposition.
   - Install or refresh packet-mode triage leaves. In full `/triage`, leaves
     return candidates and stop conditions; they do not emit lane-local final
     recommendations, kickoff phrasing, or yes-ready handoffs.
   - Install or refresh `/triage-health` only as a sparse health/freshness
     packet lane. It reports architecture, UI, eval, codebase, methodology,
     wrapper, dependency, or provider risks without running deeper audits by
     default.
   - Install or refresh a sparse-safe triage fact collector when repo tooling
     exists. It must be cheap, read-only, deterministic, and parseable through
     the direct script command.
   - Install or refresh `/loop-verify` with materiality guidance: material
     semantic/executable/contract/generated changes reset a full fresh pass;
     minor typo/formatting/non-contract wording fixes only need targeted
     checks; no hard round cap.

9. **Run the shared-surface propagation sweep**:
   - Check that setup, triage, core story-loop skills, triage leaves,
     triage-health, loop-verify, runbooks, fact script/tests, and wrappers
     agree on the same terms.
   - For no-code repos, confirm absent/deferred lanes are explicit and do not
     create fake triage pressure.
   - Confirm direct fact commands are separate from convenience package scripts
     so package-manager banners cannot corrupt JSON proof.
   - Confirm wrapper facts distinguish `absent`, `ok`, and `drift`; UI/eval
     facts distinguish empty paths, deferred evidence, and broken pointers.

10. **Normalize the public skill surface**:
   - `init-project` is the greenfield idea-intake seed skill
   - `setup-methodology` is the canonical full-package setup entrypoint
   - old phased setup skills are removed rather than preserved as aliases
   - `/triage-architecture` is installed when the package includes the
     architecture-audit lane
   - `ui_scout` is documented only when the package includes the UI
     product-truth lane
   - `init-project` seeds Ideal/spec first, then imports the appropriate package
   - run `scripts/sync-agent-skills.sh`
   - validate with `scripts/sync-agent-skills.sh --check`

11. **Audit and summarize**:
   - reference audit for stale phased-setup language
   - surface audit confirming the removed setup commands are no longer active
   - eval workflow audit (`create-eval` vs `improve-eval`)
   - triage/loop-verify surface audit
   - short alignment sweep across Ideal / Spec / State / Stories / Evals / ADRs

## Outputs

- Canonical setup skill surface installed
- Existing project-specific Ideal/spec preserved, reviewed, and aligned
- Working copy of `docs/setup-checklist.md`
- Runbook + AGENTS docs aligned to the same package
- Baseline golden/eval/story bootstrap included or explicitly deferred by repo
  variant
- Core story-loop skill surfaces installed or refreshed with sidecar,
  plan-gated delegation, parallel validation, and loop-verify escalation
  guardrails
- Upgraded triage, triage-health, sparse facts, and loop-verify surfaces
  installed or explicitly deferred by lane
- Cross-CLI wrappers regenerated and checked

## Guardrails

- Do not teach multiple competing setup models in AGENTS or docs.
- Do not fabricate a generic `docs/ideal.md` or `docs/spec.md`; use
  `/init-project` for greenfield idea intake first.
- Do not recreate or advertise the removed phased setup skills.
- Do not treat old setup notes or retrofit notes as canonical bootstrapping
  docs once the runbook exists; mark them historical/superseded instead.
- Do not split day-zero bootstrap from golden/eval setup unless the user
  explicitly chooses to defer them.
- Do not create a new methodology shape in one doc and leave the old shape in
  the skill surface or `init-project`.
- Do not make sidecar or subagent guidance mandatory for routine story
  creation, no-code setup, ordinary refreshes, or small validation passes.
- Do not run long subagent verification loops in a no-code repo just to prove
  that code-dependent evidence does not exist yet. Install the sparse package,
  mark absent/deferred lanes, run cheap checks, and let later real code create
  real evidence.
