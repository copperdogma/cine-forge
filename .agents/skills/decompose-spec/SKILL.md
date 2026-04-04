---
name: decompose-spec
description: Pipeline to decompose spec.md into tracked stories via methodology state, generated dashboards, and a coverage matrix
user-invocable: true
---

# /decompose-spec

Systematic pipeline to turn `docs/spec.md` (and ADRs) into a complete, tracked set of stories.
Run once to bootstrap, then maintain the coverage matrix as a living doc.

## Pipeline

spec.md + ADRs → Methodology State → Generated Dashboards → Coverage Matrix → Stories
                  (categories)      (views)                 (line-by-line)    (vertical slices)

## Key Concept: Categories Own Stories

Methodology state defines category ownership — technical umbrellas like story
intake, world building, or operator-console substrate. A category is NOT a
story. Each category owns one or more stories, starting with an MVP slice and
adding capability with follow-up stories.

Methodology Category (e.g., `spec:2 Story Intake & Understanding`)
  ├── Story 001 — FDX/Fountain parsing (MVP slice: detect format → normalize → store)
  ├── Story 002 — PDF extraction & OCR
  └── Story 003 — Format validation & error recovery

Small systems (auth, scaffold, spikes) may be a single story. Large systems should always be
multiple stories. The category checkbox means "ALL stories under this category are complete",
not "one story exists."

## Steps

1. Build or refresh methodology state — Read `docs/ideal.md`, `docs/spec.md`,
   `docs/methodology/state.yaml` (if it exists), generated dashboards, and all
   decided ADRs. Identify the owning categories/components. Update
   `docs/methodology/state.yaml`:
   - each category gets a state entry with summary, substrate, phase, and notes
   - dependencies and roadmap overlays stay in state, not hand-authored
     dashboards
   - rerun `pnpm methodology:compile` after changes so the generated views stay
     current

2. Build the Coverage Matrix — For every actionable checkbox/requirement in spec.md, create
   a row in docs/coverage.md:
   - Spec line number, item description, category it belongs to, story ID (or —), status
   - This is the "nothing missed" guarantee
   - Items explicitly marked "Future" or "NOT MVP" in spec get tagged but no story needed yet

3. Create Story Skeletons — For each active category, create one or more vertical-slice stories
   via /create-story:

   The umbrella rule: A category is NOT a story. Categories own stories. Start each
   category with its MVP slice — the smallest vertical cut that delivers demoable value for
   that category. Larger categories get additional skeleton stories for follow-up slices.

   Story sizing: A story should be buildable in 1-2 AI sessions (~1-3 hours of focused work).
   If a story touches too many concerns, split it. Signs a story is too fat:
   - It touches 3+ distinct technical concerns
   - It requires multiple external service integrations or model APIs
   - You can't describe the demoable outcome in one sentence
   - The acceptance criteria would exceed 8-10 items

   Skeleton format: Title, Goal (one-liner), Spec Refs, Depends On, and a Notes section for
   accumulated observations — everything else stays as template placeholder.

   Ordering: Stories ordered by dependency (artifact store first → driver orchestration →
   pipeline modules → backend API → UI → polish).

   Coverage link: Every story must reference which coverage matrix items it addresses. The
   coverage matrix gets updated with the story ID.

   Don't over-decompose future work. For systems that won't be built soon, a single skeleton
   with notes is fine. Break them into smaller stories when they're next in the build queue.

4. Detail Immediate Stories — For the first 2-3 stories in build order, fill in full detail:
   acceptance criteria, tasks, AI considerations, files to modify. These are ready-to-build.

5. Verify Coverage — Walk the coverage matrix. Every MVP spec item must map to at least one
   story. Flag gaps.

## Living Documents

- `docs/methodology/state.yaml` — Updated when spec changes, new ADRs are
  decided, or planning state changes.
- `docs/build-map.md` / `docs/stories.md` — Generated views refreshed by
  `pnpm methodology:compile`.
- docs/coverage.md — Updated every time a story is created, modified, or completed. The
  single source of truth for "is every spec item tracked?"
- Story skeletons — Accumulate notes over time (research findings, tech recommendations,
  design ideas). When it's time to build, /build-story incorporates these notes. Larger
  skeletons get broken into smaller stories at promotion time.

## Promoting Skeletons to Full Stories

When ready to build a skeleton story:
1. Read the skeleton's Notes section for accumulated context
2. Read all linked spec refs and ADRs
3. Check story size — if the skeleton has grown too large, split it into multiple stories first
4. Fill in: acceptance criteria, tasks, AI considerations, files to modify, out of scope
5. Incorporate any notes into the appropriate sections
6. Story is now build-ready — use /build-story to implement

## Guardrails

- Never create stories without updating the coverage matrix
- Never skip methodology state — it prevents the "flat list" problem
- A category ≠ a story. Categories are umbrellas; stories are vertical slices under them.
- One story = one demoable outcome. If you can't demo it in one sentence, split it.
- Skeleton stories are real story files (same template) — just not fully detailed yet
- The coverage matrix is append-only for spec items — don't remove rows, mark them Deferred or Cut
- Don't pre-split distant future work — a fat skeleton is fine until it's next in the build queue
