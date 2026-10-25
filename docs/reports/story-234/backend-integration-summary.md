# Story 234 offline integration validation

Result: **23 passed, 0 failed, 0 errors, 0 skipped** in 25.21 seconds.

Executed from `/Users/cam/.codex/worktrees/triage-batch-integration-20261023/cine-forge` against the current uncommitted Story 234 changes. `PYTHONPATH=src` selected this checkout; the offline launcher removed inherited provider credentials and disabled dotenv loading. `CINE_FORGE_LIVE_TESTS=0` was explicit. These are mechanical integration fixtures, not live provider, media-quality, or representative UI acceptance evidence.

Command:

```bash
CINE_FORGE_LIVE_TESTS=0 PYTHONPATH=src \
  /Users/cam/Documents/Projects/cine-forge/.venv/bin/python output/offline-pytest.py \
  tests/integration/test_api_integration.py \
  tests/integration/test_pipeline_integration.py \
  tests/integration/test_render_adapter_integration.py \
  tests/integration/test_media_cost_receipts.py \
  tests/integration/test_cost_budget_pause.py \
  tests/integration/test_final_output_integration.py \
  tests/integration/test_track_system_integration.py \
  tests/integration/test_shot_planning_integration.py \
  tests/integration/test_style_pack_integration.py \
  tests/integration/test_project_config_integration.py \
  -m integration -ra \
  --junitxml=docs/reports/story-234/backend-integration.xml \
  > docs/reports/story-234/backend-integration.txt 2>&1
```

Coverage includes API/driver execution, render persistence and partial failure, cost receipts and uncertain-job guards, budget pause/resume, final output, track/shot planning, style packs, and project configuration. No implementation changes were required by this run. Raw summary: `backend-integration.txt`; test identities and timings: `backend-integration.xml`.
