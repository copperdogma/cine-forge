# Story230 validation — first-use next-action truth

Final finding: no material findings remain. The accepted review finding was a
false Deep Breakdown promise for no-input/already-broken-down empty projects;
state-aware input/artifact checks now route those cases to Script with accurate
copy. Both strong independent re-review and scoped Codex CLI review cleared.

## Impact

A fresh project can move from empty Characters/Locations/Props directly to the
existing Deep Breakdown screen. Render/AI Previz consistently explain automatic
shot preparation and no longer offer a clip-planning link back to the active
tab. Generation, model selection, artifacts and warning severity are unchanged.

## Acceptance

| Criterion | Evidence | Result |
|---|---|---|
| Honest missing-shot guidance | Real Open Frequency desktop/mobile Render and Previz; shared summary uses shipped recipe behavior | Met |
| Useful preflight actions | Eight direct/cascade, two-recipe, two-scope regressions; current-tab links absent; all-scenes/context routes retained | Met |
| Empty-page next action | All3 real fresh-project buttons on desktop/mobile land at enabled Run Deep Breakdown; source-matched state gate prevents false promises; Scenes routes Script | Met |
| Contracts and browser checks |39 scene-action tests +3 affected API/service tests, full Ruff, UI lint/tsc/build,11 browser observations, clean console | Met |
| Parent truth preserved |229 report retains failures and blocked media boundary;230 is targeted proof, not full FP1 | Met |

## Validation and limits

- Tests: PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_scene_actions.py -q
  (39 passed); tests/unit/test_api.py with scene_action_preflight,
  persists_scene_scope and coerced_scene_preflight selection (3 passed).
- Baseline for the four initial route regressions:2 failed(current scene),
 2 passed(all scenes). One preliminary test-only nonexistent can_run assertion
  was corrected before taking that baseline. Expanded coverage includes direct
  prerequisite inspection and fresh-project cascading rebuild.
- Full source/test Ruff passed. UI lint and tsc passed after the final edge-case
  repair; final production build passed with the existing large-chunk warning.
- Fresh API process32680/32682, samecheckout, health200. No schemas changed;
  existing typed API/service consumer checks cover nullable action fields.
- Browser:1600x1100 and390x844, real open-frequency created via /new and completed
  normal mvp_ingest run-fae39865. All3 list actions were actually clicked and
  their destination CTA checked enabled. No generation CTA was clicked.
- browser-checks.json has11 structured observations; console.json contains[].
  Source-state-proof confirms four scenes, unchanged ingest state/input hash,
  unchanged recorded cost0.0809394, and no media-generation artifacts.
- edge-smoke.json is explicitly synthetic/non-representative. CDP only replaced
  GET input/artifact-list responses for two narrow component cases: no input,
  and an existing character Bible with empty props. Both show Open Script and
  no Deep Breakdown promise. No stored artifacts were changed; interception
  cleared and tab reloaded to real responses. edge-console.json also contains[].
- The alternative Vite SSR probe failed before any cases due to installed
  router module loading; its output/story-230-edge-smoke/ report is not counted.
  Reused the already-proven local CDP interception pattern instead of adding
  SSR framework work or dependencies.
- Independent strong review caught the edge case and cleared after its repair.
  Additional scoped codex review cleared final code; installed CLI rejected
  --uncommitted plus custom prompt, so a custom read-only review explicitly
  targeted the actual dirty five-file slice. Raw transcript remains in
  output/story-230-codex-review.txt; no unrelated eval/document work was adopted.
- Full backend suite evidence from earlier201 was not used to claim these new
  paths tested.39 focused tests and3 affected boundary tests were run on this
  code; broader unrelated suites/paid evals do not improve this repair's proof.
- Methodology compile/check pass; pre-existing architecture and incomplete-FP1
  warnings remain honest. Global retained-media consistency still has the known
 44 untracked extras and was not rerun or weakened for this UI change.

## Architecture and redundancy

ADR002/003 and screenplay-first doctrine apply. Preflight remains typed and
owned by pipeline/scene_actions.py. Its generation coordinator shrank161→90
lines, with35/18/20-line focused helpers; cascade is59lines. One shared
clip-planning item constructor prevents the two actual paths diverging again.
EntityListPage593→531 lines delegates the changed config/empty-state seam;
no logic was added to the oversized Render/Previz/SceneWorkspace parents.
Superseded inline config and mandatory Shots/self-link copy were removed.
No new schema/event/framework, compatibility shim, runtime model choice or
AI capability compromise was introduced.

Learning review considered: existing representative-state and actual-destination
verification rules already cover the accepted local oversight. No durable
workflow change or learning candidate is warranted; no memory/skill was edited.

Grade A for the bounded230 repair. Closure recommendation: Close now. The
separate229 media continuation remains blocked under its declared envelope.

Optional verification: open /open-frequency/characters and click Open Deep
Breakdown; or Scene1 → Render and inspect automatic-shot guidance. Generation
buttons remain untouched during this check.
