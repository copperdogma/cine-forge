# Story 201 — Keyframe Affordance Truth

Date: 2026-10-23. Source checkout: `714802a` plus the uncommitted repair.
Cam authorized a continuing triage-and-fix goal. No commit, push, deployment,
paid evaluation, or generation was performed.

## Triage decision

Five neutral lane packets covered stories, inbox, evals, architecture, and
health. The parent ran `.venv/bin/python scripts/triage_facts.py --json`
successfully. Cheaper Sol/Luna workers gathered factual story/inbox/health
packets; inherited stronger workers reviewed architecture and eval integrity.

The candidate gaps were misleading scene-generation guidance (`spec:6/7`,
climb), reference/identity quality (`spec:6/7`, climb), and stale product-truth
coverage (`spec:5`, hold). No phase is currently convergence-ready.

1. **Continue Story 201: optional-keyframe guidance.** Current code and direct
   API reproduction confirm the May 4 Story 196 defect: a completed scene with
   eight render clips warns `Keyframes missing`, then offers `Open Render`
   while already on Render. Fixing the existing owner advances R7/R8/R11/R12
   without a new workflow or model call. Stop at focused preflight regressions
   and representative desktop/mobile Render/Previz proof. It ranks first
   because the defect is current, bounded, and immediately repairable.
2. **Continue the realistic-reference quality line in Story 197 / the existing
   storyboard evidence chain.** Story 208's repaired parent shows unresolved
   identity and source-cue failures; Story 190's unchanged anchor strategy was
   already exhausted. R7/R8/R17 value is higher output fidelity. First establish
   representative references, provenance, and a distinct falsifiable strategy;
   stop if that evidence cannot justify a bounded comparison. This ranks below
   201 because repeating the old generator matrix would add no new evidence.
3. **Refresh the canonical FP1 walkthrough.** The last complete scout was April
   12, now 194 days old against a 14-day cadence. A fresh surfaced desktop walk
   plus mobile spot-check serves easy/fun/engaging and `spec:5.6`. Stop when the
   current honest boundary is walked and new defects have owners. It ranks
   below 201 because a confirmed defect can be repaired before a broad scout.

Project Home placement remains a separate concrete candidate owned by Draft
Story 185; its explicit product decision still needs resolution. No new story
was created. Exhausted Script Bible/ordered-frame retries, stale score dates,
and architecture cadence alone did not justify new paid runs or refactors.

**Vs Ideal:** a real scene-generation path and inspectable output exist;
film-level consistency and effortless iteration remain distant. Present-day
progress is mixed: useful substrate works, but output quality and misleading
setup still interrupt creative flow. This repair removes one unnecessary
piece of setup while retaining honest quality and prerequisite signals.

## Implementation and proof

Deleted the Render-only missing-keyframe warning and its circular action.
No new informational preflight kind or keyframe generator was added. Render
copy now states that keyframes are optional, that available locked frames are
used, and how current/all-scene scope works. Existing schemas, artifact
versions, locks, review pages, and adapter input handling remain intact.

ADRs reviewed: ADR-002 (honest next actions) and ADR-003 (Scene Workspace
ownership). Relevant constraints are `spec:6.4`, `spec:7.1`, `spec:10.3` and
C6; none requires keyframes as a render prerequisite. Deterministic code is
the appropriate owner for this preflight/copy defect.

The new mechanical fixture covers both recipes, both scopes, and absent,
healthy, and stale keyframes. Before the runtime deletion, four Render cases
failed and eight controls passed. Afterward all 12 cases pass, and all 31
scene-action tests pass. These fixtures are isolated plumbing checks, not
representative product or media-quality evidence.

Representative proof used the existing `brick-steel-full-retired` project,
`scene_001`, previously produced through the normal driver and documented in
Story 196. The scene has eight generated render clips and no keyframe
artifact. No artifacts were seeded, copied, regenerated, or edited for this
browser pass. API requests cover both recipes and both scopes:

- [Before Render preflight](render-before.json) has the obsolete warning.
- [After Render, current scene](render_generation-current_scene-after.json)
  and [all scenes](render_generation-all_scenes-after.json) omit keyframe
  homework while retaining real planning/direction work.
- [After AI Previz, current scene](ai_previz_generation-current_scene-after.json)
  and [all scenes](ai_previz_generation-all_scenes-after.json) retain their
  existing classification. The normal API process resolves configured xAI
  credentials; an earlier standalone helper invocation without provider-env
  loading correctly reported credentials unavailable. No secret was changed.

The Codex in-app browser checked Render and Previz at 1600×1100 and 390×844,
using surfaced tab changes and execution-scope controls. Screenshots were
manually inspected. No keyframe warning or keyframe action remains; real
planning warnings and saved clips remain visible. Console logs were empty.
Retained CDP events show canceled media requests during tab switching and no
HTTP error status or uncaught exception; earlier events were evicted, so the
network capture is explicitly partial. See [browser summary](iab-browser-summary.json).

- [Desktop Render](iab-desktop-render.png)
- [Mobile Render](iab-mobile-render.png)
- [Desktop Previz](iab-desktop-previz.png)
- [Mobile Previz](iab-mobile-previz.png)

The narrower verification does **not** reset FP1 full-walkthrough freshness.

## Validation and follow-up

- Focused scene-action suite: 31 passed.
- Backend/test Ruff: passed.
- UI lint, TypeScript build-mode check, production build: passed after final
  copy changes. The existing large-chunk build warning remains advisory.
- Methodology compile/check and diff hygiene: passed at implementation;
  regenerate after final story closure.
- Full backend unit run: 2,215 passed, one pre-existing historical-manifest
  failure. `test_story_213_manifest_is_hash_complete_for_final_qa_contract`
  compares immutable hashes with evolving live files; Story 213's existing
  scheduled-note edits add a sixth mismatch to its five-path exception list.
  Existing Story 208 repaired that boundary using immutable archived bytes,
  restored live runtime-task coverage, and then reclosed. All 65 affected
  scene-action/manifest/ledger tests pass; the 2,215 unaffected broad-suite
  passes are reused under proportional validation.

`make check-size` ran before planning. The change removes logic from the
929-line `scene_actions.py` and edits only description text in the 660-line
Render component. No new class responsibility or schema boundary was added.
The obsolete warning is removed rather than hidden by the UI. Extra `codex
review` is unnecessary for this small deletion/copy diff; the parent reviewed
the changed owner and consumers directly. No model/scored evaluation ran, so
no new registry score or mismatch classification is warranted.

Browser tooling recovery followed the project runbook. Playwright MCP's
profile was occupied; the installed Python Playwright lacked its bundled
Chromium. A bounded check of the [official browser-channel guidance](https://playwright.dev/python/docs/browsers)
confirmed installed Chrome support. A separate scripted probe then timed out
on its exact readiness string and is not acceptance evidence. The successful
in-app browser proof above is the authority; it also showed why the script's
exact AI Previz summary match was too narrow (configured-credential text is
appended). Temporary viewport overrides were reset.

Optional operator check: open Scene Workspace → Render for Brick & Steel
scene 001, read the optional-keyframe explanation, then switch to Previz.

## Final disposition

Stories 201 and 208 are Done, with no remaining material code finding in their
changed scope. A separate strong review verified all36 archived commit/path
identities, accepted the missing live runtime-task fix, and then found no
material findings. The final 65 affected tests, full backend/test plus builder
Ruff, truth-audit ledger, current-manifest, methodology and diff checks pass;
UI lint/tsc/build and desktop/mobile evidence remain applicable. No additional
full suite was repeated over unchanged runtime code.

Current contracts are frozen at v22 (993 files, bundle
`61df75c110877ec80b1a71be128cc34fe74b1fac2407dbfa277361c1c128423e`).
The earlier v21 interim snapshot is preserved; original Story213 and v20
manifests remain unchanged. These dirty working copies are provisional until
committed; no commit or push was authorized.

The broader primary-workspace registry check remains red: all91 declared
retained-media files are present and byte-identical, while44 untracked files
that predate this work sit beside that immutable packet. Its strict extra-file
rejection is correct. Those files and the existing dirty registry/Story213/
deploy-log work were preserved; no score, evidence gate, or old manifest was
relaxed to hide the ambient-workspace issue. New self-email items also arrived
in `docs/inbox.md` during this turn from other work; this goal did not edit them.

The goal remains active. The next triage has no ready Pending story, which is
not feature completeness: Home hierarchy (185), realistic-reference fidelity
(197), the pilot draft (228), stale FP1 coverage, and the newly imported inbox
items remain concrete product/evidence candidates.


Integration provenance correction (2026-10-23): the v21/v22 checkpoints above
were this task’s unlanded provisional outputs. Their exact bytes now live in
`docs/evals/snapshots/triage-goal-20261023-provisional-manifests/`, distinguished
by SHA256 in its index. Incoming main independently owns canonicalv21/v22. The
quoted993-file digest identifies this task’s archivedv22, not incoming main.
No historical JSON bytes were edited to resolve that naming collision.
