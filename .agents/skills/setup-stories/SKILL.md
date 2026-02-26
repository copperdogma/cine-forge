---
name: setup-stories
description: Decompose spec into tracked stories via feature map and coverage matrix
user-invocable: true
---

# /setup-stories

Decompose `docs/spec.md` (and ADRs) into a complete, tracked set of stories.
This is Phase 6 of project setup — run after `/setup-spec` produces the organized
spec with confirmed compromises. Can also be re-run when the spec changes
significantly (e.g., after new eval results eliminate compromises).

## Pipeline

spec.md + ADRs → Feature Map → Coverage Matrix → Stories
                  (systems)     (line-by-line)    (vertical slices)

## Key Concept: Systems Own Stories

The feature map defines systems — technical umbrellas like "Screenplay Intake", "World Building",
or "Operator Console". A system is NOT a story. Each system owns one or more stories,
starting with an MVP slice and adding capability with follow-up stories.

Feature Map System (e.g., "Screenplay Intake")
  ├── Story 001 — FDX/Fountain parsing (MVP slice: detect format → normalize → store)
  ├── Story 002 — PDF extraction & OCR
  └── Story 003 — Format validation & error recovery

Small systems (auth, scaffold, spikes) may be a single story. Large systems should always be
multiple stories. The feature map checkbox means "ALL stories under this system are complete",
not "one story exists."

## Steps

1. Build the Feature Map — Read `docs/ideal.md` first to understand the north star,
   then read `docs/spec.md` and all decided ADRs. Identify major systems/components.
   Write to docs/feature-map.md:
   - Each system gets a section with: name, summary, spec sections covered, ADR refs,
     dependencies on other systems
   - Order by dependency (foundations first)
   - Mark each system: MVP or Future
   - Add checkboxes: [ ] = no stories yet, [x] = fully covered by stories

2. Build the Coverage Matrix — For every actionable checkbox/requirement in spec.md, create
   a row in docs/coverage.md:
   - Spec line number, item description, Ideal requirement it serves, system it belongs to,
     story ID (or —), status
   - This is the "nothing missed" guarantee
   - Items explicitly marked "Future" or "NOT MVP" in spec get tagged but no story needed yet
   - For each AI compromise: verify a detection eval story is included (no pipeline stage
     should be built without its deletion mechanism)

3. Create Story Skeletons — For each MVP system, create one or more vertical-slice stories
   via /create-story:

   The umbrella rule: A feature map system is NOT a story. Systems own stories. Start each
   system with its MVP slice — the smallest vertical cut that delivers demoable value for
   that system. Larger systems get additional skeleton stories for follow-up slices.

   Story sizing: A story should be buildable in 1-2 AI sessions (~1-3 hours of focused work).
   If a story touches too many concerns, split it. Signs a story is too fat:
   - It touches 3+ distinct technical concerns
   - It requires multiple external service integrations or model APIs
   - You can't describe the demoable outcome in one sentence
   - The acceptance criteria would exceed 8-10 items

   Skeleton format: Title, Goal (one-liner), Ideal Refs (which ideal.md requirements this
   serves), Spec Refs, Depends On, and a Notes section for accumulated observations —
   everything else stays as template placeholder.

   **Skeleton stories get status `Draft`** — they have a goal and notes but lack detailed
   acceptance criteria and tasks. Draft status signals to other skills (build-story,
   triage-stories) that the story is NOT ready to build.

   Ordering: Stories ordered by dependency (artifact store first → driver orchestration →
   pipeline modules → backend API → UI → polish).

   Coverage link: Every story must reference which coverage matrix items it addresses. The
   coverage matrix gets updated with the story ID.

   Don't over-decompose future work. For systems that won't be built soon, a single skeleton
   with notes is fine. Break them into smaller stories when they're next in the build queue.

4. Detail Immediate Stories — For the first 2-3 stories in build order, fill in full detail:
   acceptance criteria, tasks, AI considerations, files to modify. **Set these to status
   `Pending`** — they are ready to build. Only fully detailed stories get Pending status.

5. Verify Coverage — Walk the coverage matrix. Every MVP spec item must map to at least one
   story. Flag gaps.

## Living Documents

- docs/feature-map.md — Updated when spec changes or new ADRs are decided. Systems checked
  off when ALL their stories are complete.
- docs/coverage.md — Updated every time a story is created, modified, or completed. The
  single source of truth for "is every spec item tracked?"
- Story skeletons — Accumulate notes over time (research findings, tech recommendations,
  design ideas). When it's time to build, /build-story incorporates these notes. Larger
  skeletons get broken into smaller stories at promotion time.

## Promoting Draft Stories to Pending

When ready to build a Draft story:
1. Read the skeleton's Notes section for accumulated context
2. Read all linked spec refs and ADRs
3. Check story size — if the skeleton has grown too large, split it into multiple stories first
4. Fill in: acceptance criteria, tasks, AI considerations, files to modify, out of scope
5. Incorporate any notes into the appropriate sections
6. **Change status from `Draft` to `Pending`** in both the story file and `docs/stories.md`
7. Story is now build-ready — use /build-story to implement

## Completion

Update `docs/setup-checklist.md` — check off Phase 6 items.

## Guardrails

- Never create stories without updating the coverage matrix
- Every story must trace back to an Ideal requirement or a spec compromise. Untraceable stories are scope creep.
- For every system that implements an AI compromise: include a story for the detection eval. No stage ships without its deletion mechanism.
- Never skip the feature map — it prevents the "flat list" problem
- A feature map system ≠ a story. Systems are umbrellas; stories are vertical slices under them.
- One story = one demoable outcome. If you can't demo it in one sentence, split it.
- Skeleton stories are real story files (same template) with status `Draft` — just not fully detailed yet
- The coverage matrix is append-only for spec items — don't remove rows, mark them Deferred or Cut
- Don't pre-split distant future work — a fat skeleton is fine until it's next in the build queue
