# Methodology Artifact Audit and Migration Plan

> CineForge graph+state migration audit artifact.
> Purpose: capture what the current methodology surfaces actually own, define
> the replacement model without losing responsibilities, and provide the phased
> migration checklist for replacing hand-authored planning surfaces with
> structured state, a compiled graph, generated views, and hard linting.

## Executive Summary

CineForge's methodology is conceptually coherent but physically over-distributed.
The repo currently relies on hand-authored markdown to carry both canonical
design truth and mutable planning state:

- `docs/build-map.md` mixes category summaries with mutable substrate/phase
  state and live story coverage
- `docs/stories.md` mixes the canonical story list with mutable execution-map
  narrative and backlog highlighting
- setup, triage, align, build, validate, closeout, and ADR tooling still teach
  those hand-authored surfaces as active truth
- there is no compiled methodology graph or structured state substrate yet
- there is no dedicated architecture-audit lane for agentic drift control

The migration target should not be "copy Storybook." CineForge already has
film-specific `spec:1` through `spec:11` categories, local compromise IDs
(`C*`, `B*`), a large eval registry, and legacy suffixed story IDs such as
`003b`, `007b`, and `011f`. The correct target is:

1. keep authored canonical sources where they already belong
2. move mutable planning state into `docs/methodology/state.yaml`
3. compile a deterministic graph into `docs/methodology/graph.json`
4. generate `docs/stories.md` and a human-readable `docs/build-map.md`
5. hard-fail active-surface drift and generated-output drift
6. add an explicit architecture-audit lane with bounded domains

## Non-Negotiable Canon

These remain canonical and hand-maintained:

- `docs/ideal.md`
  - product ideal, execution ideal, and vision-level preferences
- `docs/spec.md`
  - category-aligned product/build constraints and compromise definitions
- `docs/decisions/**/adr.md`
  - durable decision rationale and supersession history
- `docs/stories/story-*.md`
  - canonical execution artifacts, work logs, and closure evidence
- `docs/evals/registry.yaml`
  - canonical measured evidence and compromise detectors

The redesign must not create a parallel source that duplicates those truths.

## Current Responsibility Matrix

| Artifact | Type Today | Responsibilities It Actually Own Today | Migration Outcome |
|---|---|---|---|
| `docs/ideal.md` | Canonical authored source | Product ideal, execution ideal, vision-level preferences, feature filter | Keep canonical. Never render. |
| `docs/methodology-ideal-spec-compromise.md` | Explanatory reference | Explains the dual-ideal methodology, build-map role, and triage/align responsibilities | Keep as explanatory reference. Rewrite for state/graph authority. |
| `docs/spec.md` | Canonical authored source | Stable `spec:N` categories, compromise definitions, limitation types, deletion/evolution logic | Keep canonical. Parse IDs/compromise ownership into the graph. |
| `docs/build-map.md` | Hand-authored dashboard + mutable state | Category summaries, substrate state, category phase, live story coverage, ADR lookup surface, compromise-progress notes, human-readable planning dashboard | Replace as an authored source. Preserve as a generated dashboard view fed by state + graph. |
| `docs/stories.md` | Manual index + mutable planning overlay | Full story index, status buckets, execution-map narrative, backlog highlighting, phase summary, spec coverage map | Replace with a generated index. Move custom narrative/overlay sections into structured state. |
| `docs/setup-checklist.md` | Working checklist | Active methodology bootstrap state, currently teaches build-map/story-index truth | Keep as working copy, but rewrite around state/graph/generated views. |
| Story files | Canonical authored source | Scope, acceptance criteria, ADR/spec linkage, dependency graph, work log, closure evidence | Keep canonical. Add strict frontmatter for new stories; support legacy headers during migration. |
| `create-story` skill + template | Workflow substrate | Story numbering, metadata shape, story-index update contract | Update to emit frontmatter and rerun graph generation instead of editing `docs/stories.md` manually. |
| `docs/evals/registry.yaml` | Canonical authored source | Eval IDs, targets, scores, retry conditions, compromise hooks | Keep canonical. Parse into the graph and lint unresolved refs. |
| `setup-methodology` skill + runbook | Bootstrap surface | Teaches the repo's methodology package and checklist contract | Rewrite around `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated `docs/stories.md`, and generated `docs/build-map.md`. |
| `triage`, `align`, `build-story`, `validate`, `mark-story-done` | Workflow surface | Consume build-map/story-index truth, coordinate planning/build/validation/closure, teach manual story-index edits | Rewire to read compiled graph + state, and rerun generation instead of hand-editing output views. |
| `init-project` | Methodology package exporter | Teaches/install current package shape for new repos | Rewrite to export the graph+state package, or future repos will keep inheriting the old shape. |
| ADR tooling (`create-adr` template/docs) | Workflow substrate | Integration checklist still assumes manual story index updates | Rewrite to reference state/graph regeneration and generated views. |
| `docs/retrofit-gaps.md` | Historical migration artifact | Archived evidence from the earlier execution-ideal/spec migration | Keep as historical context only. Do not treat as live planning state. |

## Current Consumer Hotspots

These are the main migration-risk surfaces because they currently assume
`docs/build-map.md` and/or `docs/stories.md` are hand-authored sources:

### Triage and Alignment

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/triage-stories/SKILL.md`
- `.agents/skills/triage-evals/SKILL.md`
- `.agents/skills/triage-inbox/SKILL.md`
- `.agents/skills/align/SKILL.md`
- `docs/runbooks/triage.md`
- `docs/runbooks/triage-evals.md`

### Story Execution and Closeout

- `.agents/skills/build-story/SKILL.md`
- `.agents/skills/validate/SKILL.md`
- `.agents/skills/mark-story-done/SKILL.md`
- `.agents/skills/create-story/SKILL.md`
- `.agents/skills/create-story/templates/story.md`

### Bootstrap and Package Export

- `.agents/skills/setup-methodology/SKILL.md`
- `.agents/skills/init-project/SKILL.md`
- `docs/runbooks/setup-methodology.md`
- `docs/setup-checklist.md`
- `.agents/skills/setup-methodology/templates/setup-checklist.md`

### ADR and Story Metadata Tooling

- `.agents/skills/create-adr/templates/adr.md`
- story files that still rely only on legacy `**Status**` / `**Spec Refs**` /
  `**ADR Refs**` headers

## Key Findings

### 1. `docs/build-map.md` owns more than a dashboard

Today it is responsible for:

- category identity in human-readable form
- substrate state
- category phase
- story coverage and story grouping
- ADR linkage notes
- compromise progress commentary
- the repo's central human-readable planning dashboard

Deleting it without replacement would definitely drop responsibilities.

### 2. `docs/stories.md` mixes index data with mutable planning overlays

It currently carries:

- canonical-looking story list data
- status buckets with rationale text
- current execution-map prose
- phase summary
- spec coverage map

Index data should be generated. Overlay prose should live in structured state.

### 3. CineForge needs a generated `build-map.md`, not necessarily a deleted path

Unlike Storybook, CineForge has already taught `docs/build-map.md` widely
across AGENTS, runbooks, and skills. The repo should stop treating it as
authority, but preserving the path as a generated dashboard view is lower risk
than deleting it outright.

### 4. Legacy suffixed story IDs are real migration debt

The repo has legitimate legacy story IDs such as `003b`, `007c`, `011f`, and
others. The graph compiler, state schema, and generated index must support them
during migration, while new stories continue using the next plain numeric ID.

### 5. There is no dedicated architecture-audit lane today

Validation and story notes already surface drift, but there is no bounded,
remembered mechanism for deciding:

- what old paths should now be deleted
- which areas need structural simplification
- which domains are overdue for audit

The new methodology package should add that lane explicitly.

## Recommended Replacement Model

## 1. Canonical Authored Sources

Keep these as the only hand-authored decision-bearing sources:

- `docs/ideal.md`
- `docs/spec.md`
- `docs/decisions/**/adr.md`
- `docs/stories/story-*.md`
- `docs/evals/registry.yaml`

## 2. Structured Operational State

Add one hand-maintained state file:

- `docs/methodology/state.yaml`

For CineForge, it should own:

- category substrate + category phase
- compromise phase state
- category dashboard summaries migrated out of `docs/build-map.md`
- story-index overlay sections migrated out of `docs/stories.md`
- roadmap focus / sequencing bias / active campaigns
- architecture-audit cadence, memory, and open findings
- temporary story metadata overrides when legacy story files need bridging

It should not restate:

- Ideal prose
- spec prose
- ADR rationale
- story work logs
- eval score history

## 3. Compiled Methodology Graph

Add a deterministic compiled graph:

- `docs/methodology/graph.json`

Compiler inputs:

- `docs/ideal.md`
- `docs/spec.md`
- `docs/decisions/**/adr.md`
- `docs/stories/story-*.md`
- `docs/evals/registry.yaml`
- `docs/methodology/state.yaml`

Required joins:

- spec category -> state -> stories -> ADRs -> evals
- compromise -> owning category -> phase -> detector evals
- story -> status -> deps -> spec refs -> ADR refs -> roadmap tags
- architecture domain -> recency -> recent stories -> open findings

## 4. Generated Views

Required generated views:

- `docs/stories.md`
  - generated from story metadata + state overlays
- `docs/build-map.md`
  - generated human-readable dashboard from state + graph
  - not a canonical source, but retained as a familiar inspection surface

## 5. Strong Metadata / Frontmatter

New stories should use strict frontmatter while the compiler still tolerates
legacy story headers during migration.

Minimum story metadata:

- `id`
- `title`
- `status`
- `priority`
- `ideal_refs`
- `spec_refs`
- `adr_refs`
- `depends_on`
- `category_refs`
- `compromise_refs`
- `architecture_domains`
- `roadmap_tags`

Minimum ADR metadata:

- `id`
- `status`
- `spec_refs`
- `ideal_refs`
- `story_refs`
- `compromise_refs`
- `related_adrs`
- `supersedes`
- `superseded_by`

## Proposed Structured State Shape

This is the recommended logical shape, not a locked schema:

```yaml
{
  "version": 1,
  "categories": {
    "spec:11": {
      "substrate": "exists",
      "phase": "climb",
      "product_need": "Planning scaffolding remains coherent while current AI still needs explicit repo guidance.",
      "tech_need": "State, graph, generated indexes/views, linting, and workflow tooling remain aligned.",
      "last_reviewed": "2026-04-04"
    }
  },
  "compromises": {
    "B2": { "phase": "climb", "last_reviewed": "2026-04-04" },
    "B3": { "phase": "hold", "last_reviewed": "2026-04-04" },
    "B5": { "phase": "hold", "last_reviewed": "2026-04-04" }
  },
  "roadmap": {
    "active_focus": ["spec:11", "spec:5", "spec:6"],
    "campaigns": [
      {
        "id": "methodology-graph-state-migration",
        "status": "active",
        "story_refs": ["145"],
        "notes": "Replace hand-authored methodology dashboards with structured state, compiled joins, generated views, and linting."
      }
    ]
  },
  "stories_index": {
    "sections": [
      {
        "id": "current-execution-map",
        "title": "Current Execution Map",
        "markdown": "Preserved narrative/overlay content from the former hand-authored story index."
      }
    ]
  },
  "architecture_audits": {
    "cadence": { "target_story_interval": 10 },
    "domains": {
      "methodology_tooling": {
        "last_audited_at": "2026-04-04",
        "recent_story_refs": ["134", "136", "145"],
        "stories_since_audit": 0,
        "open_findings": [],
        "manual_priority": "high"
      }
    }
  }
}
```

## Lint Contract

### Blocking Lints

- every story `spec_ref` resolves to a real `spec:N` or subsection
- every story `depends_on` resolves to an existing story ID, including suffixed
  legacy IDs
- every story `adr_ref` resolves to a real ADR when explicitly present
- every state compromise entry resolves to a real compromise in `docs/spec.md`
- generated `docs/stories.md`, generated `docs/build-map.md`, and
  `docs/methodology/graph.json` are current
- no active methodology surface tells agents to hand-edit `docs/stories.md`
- no active methodology surface still teaches `docs/build-map.md` as the
  canonical planning state
- no state key is ownerless or duplicated

### Warning Lints

- story files still on legacy headers only
- uncategorized stories caused by missing metadata
- category state older than recent linked story churn
- compromise phase older than related eval freshness
- architecture domains overdue for audit

## Architecture-Audit Operating Lane

### Purpose

Counter agentic architecture drift:

- wrappers instead of deletion
- duplicated ownership after refactors
- oversized files that remain oversized because no audit lane reclaims them
- stale compatibility paths that survive after feature work

### Where It Lives

- `docs/methodology/state.yaml` under `architecture_audits`

### Recommended CineForge Domains

- `methodology_tooling`
- `driver_and_runtime`
- `ingest_and_world_building`
- `api_service_and_operator_console`
- `creative_direction_and_chat`
- `generation_and_visualization`

### Expected Workflow Surface

Add:

- `.agents/skills/triage-architecture/SKILL.md`
- `docs/runbooks/triage-architecture.md`

And teach:

- `/triage` to route into it when due
- `/validate` to feed medium/high drift signals into it

## Migration Checklist

### Phase 0 — Freeze the Model

- [x] Accept this replacement shape as CineForge's migration target
- [x] Treat this audit artifact plus Story 145 as the in-flight authority
- [x] Stop adding new manual story-index/build-map obligations while the new substrate is landing

### Phase 1 — Build the New Substrate

- [x] Create `docs/methodology/state.yaml`
- [x] Build the graph compiler and local check command
- [x] Generate `docs/methodology/graph.json`
- [x] Generate `docs/stories.md`
- [x] Generate `docs/build-map.md`

### Phase 2 — Normalize Story and ADR Metadata

- [x] Add frontmatter support to the compiler
- [x] Update story and ADR templates/tooling to emit strict frontmatter
- [x] Migrate Story 145 and active methodology ADR/tooling artifacts first
- [x] Leave broader story backlog migration as staged warning debt, not hidden debt

### Phase 3 — Rewire Workflow Consumers

- [x] Update setup/bootstrap docs and skills
- [x] Update triage/alignment/build/validate/closeout skills
- [x] Update ADR tooling and story creation tooling
- [x] Remove manual `docs/stories.md` edit instructions from active surfaces

### Phase 4 — Add Architecture-Audit Lane

- [x] Seed architecture audit cadence and domains
- [x] Add `/triage-architecture`
- [x] Teach `/triage` and `/validate` the handoff

### Phase 5 — Add Hard Linting

- [x] Canonical ID linting
- [x] dependency/link linting
- [x] generated-view drift linting
- [x] active-surface stale-instruction linting
- [x] overdue architecture-audit warnings

### Phase 6 — Remove Legacy Manual Ownership

- [x] `docs/stories.md` no longer treated as authored input
- [x] `docs/build-map.md` no longer treated as authored input
- [x] AGENTS/runbooks/skills point to state+graph as the authority

## Certification Loop

The migration is not complete when it "looks done." It is complete only after:

1. the compiler regenerates clean outputs
2. the check command passes with no structural errors
3. active workflow docs are re-audited for stale manual-surface instructions
4. any remaining warnings are explicitly classified as staged migration debt or
   fixed immediately
5. the final pass is clean after the last unclassified issue

Use Story 145's work log as the proof log for each certified phase.
