# Triage batch integration — 2026-10-23

Remote main advanced12 commits while this task ran. Preserve incoming work.
Local FP1 Story229 is now232; local guidance Story230 is now233. The report
directories named story-229-canonical-ui and story-230-first-use-guidance retain
their original names and captured records as historical evidence; their current
owning stories are232 and233. No artifact bytes are rewritten for ID renaming.

Remote canonical contract v21/v22 differ from this task’s unlanded provisional
outputs. Exact local bytes and remote distinctions are recorded in
`docs/evals/snapshots/triage-goal-20261023-provisional-manifests/index.json`.
Local v23-v28 remain unchanged; a new final current snapshot will bind merged
contracts. Live registry scheduled comments, liveStory213 notes, deploy log and
untracked retained-media/Attempt028 work remain excluded and preserved. Inbox
captures are reviewed and byte-identical to incoming main; leave them untriaged.

Integration fixes: both Changelog histories retained in date order; generated
planning views rebuilt from merged canon. Final builder/test contract moves to
v31, preserving remotev21/v22, archivedlocalv21/v22 and localv23-v28 bytes.
The original primary counters included unrelated scheduled Story213 notes;
excluding those notes requires measured cadence counts10 methodology and13
ingest. Canonical checker output determines those counts; no validation was
weakened or unrelated history imported. Source newline cleanup is nonsemantic;
raw captured pytest logs retain their original whitespace as evidence.


The integration review restored authored evidence links to retained report
directories without changing current story IDs. It also added the current image
runtime dependencies `ai/image.py` and `ai/gemini_image.py` to the existing
visual-runtime ledger owner. Intermediate v29 and v30 remain unchanged; v31
binds the settled integration fixtures and final story work log.

## Validation

Checks ran in the attached integration checkout with `PYTHONPATH=src`. The
existing Python environment and UI dependencies are symlinked; package/lock
files are unchanged. Offline pytest was launched by `output/offline-pytest.py`,
which removes inherited provider keys and disables dotenv before collection.
The separate7-test environment-fixture run enables only its fake dotenv inputs.
No paid provider evaluation or generation was run during close-out.

- Broad unit run:2412 passed,3 failed. Two stale image-default assertions were
  corrected with test-only changes. Focused rerun:
  `PYTHONPATH=src .venv/bin/python output/offline-pytest.py -q tests/unit/test_render_adapter_accounting.py tests/unit/test_scene_actions.py`
  —60 passed, including current Nano unpriced backfill and explicit retired
  Imagen coverage.
- Broad integration run:69 passed,1 failed,4 skipped. The stale retired-Veo
  fixture now exercises partial final output through the active xAI target and
  current receipt seam. Rerun:
  `PYTHONPATH=src .venv/bin/python output/offline-pytest.py -q tests/integration/test_final_output_integration.py`
  —4 passed; scene001 remains included and scene002 omitted after the synthetic
  second-scene failure. Active target plans one successful first-scene unit.
- UI: `pnpm --dir ui lint`, `pnpm --dir ui exec tsc -b --force`,
  `pnpm --dir ui build`, and `node --test ui/tests/*.test.ts` pass;27 UI tests.
  Build retains its existing bundle-size advisory.
- Full source/tests and changed tooling Ruff pass.
- `check_eval_registry.py`, `check_truth_audit_ledger.py`, current contract
  manifest check and methodology check pass.45 manifest/ledger tests pass.
  Methodology warnings truthfully retain due audits and blocked FP1 Story232.
- Desktop1600×1100/mobile390×844 screenshots, DOM and empty console are under
  `docs/reports/triage-batch-landing/`. Integrated API source serves the original
  normal pipeline-produced primary output via supported `workspace_root`; no
  artifacts are copied or manually seeded for this UI proof. API adoption
  response retains experimental/manual status and a4s ×$0.05=$0.20 video-only
  example. Historical cost-completeness warning remains separate.

Passing focused worker runs are retained as session evidence; their exact
commands are above. Broad XML/logs and final check logs are copied alongside
the browser evidence. Checks over unchanged sources are reused; no repeated
full-suite run or paid eval is needed for documentation/version changes.

## Inherited failure

`tests/unit/test_gpt61_video_verification.py::test_tracked_verification_needs_no_local_receipts_or_provider_calls`
fails because its immutable freeze predates newer eval-provider edits already
on origin/main `ecedeab`. Independent exact-byte inspection proved all63
freeze-referenced inputs, plus test/verifier/runner, match origin/main. This is
static condition proof; baseline pytest was not separately rerun. The first
provider mismatch is:

- Frozen expected SHA256: `783d4cacbcfaa9449b975cf4ed2d58eaa8f5af0bf63473ca9630bcbb3b9be15f`,14689bytes.
- Candidate and origin actual: `f59f5c670c1e966db8526ec04f41bf68dd509cefca2dbeedf4dd17790c012362`,14916bytes.

Remote `4fce5f32` first changed the provider for Mistral; `3a029014` added Argon
dispatch. Three later mismatches (Anthropic provider, vision provider and video
task YAML) are also unchanged from origin. This unrelated immutable-eval repair
is not absorbed into close-out. The full unit suite is therefore not reported
all-green. All owned failures from integration have passing targeted reruns.

## Scope and landing

One writer owns Git. Candidate batch `ea0cf54` is merged into latest remote main
in `codex/triage-integration-20261023`. No deployment is requested. The primary
checkout's unrelated3 tracked and45 untracked paths remain outside this
candidate and are verified against saved fingerprints before landing. Current
FP1 is still Blocked; broader budget controls remain Draft. The exposed xAI
key incident and operator rotation follow-up remain recorded in Story032; no
credential was used in final offline validation.

After the validated merge commit lands on remote main, the indefinite triage
goal stays paused at Cam's explicit request. Task branches/worktree are retained
because cleanup was not requested.
