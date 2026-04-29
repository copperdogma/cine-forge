---
name: deploy
description: Deploy CineForge production app to Fly.io with preflight and smoke checks
user-invocable: true
---

# /deploy

> ADR check: If this task raises an architectural, workflow, schema, or UX question, read the relevant decision record(s) in `docs/decisions/` and supporting docs in `docs/design/` before choosing an approach. If none apply, say so explicitly.

Deploy CineForge to production on Fly.io.

## References

- `docs/deployment.md` — infrastructure, architecture, DNS, troubleshooting
- `docs/runbooks/browser-automation-and-mcp.md` — browser automation + MCP runbook
- `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` — canonical short fixture and surfaced-path truth
- `docs/deploy-log.md` — deploy duration history and recalibration memory

## Expected Duration

~3 minutes total (preflight ~45s, deploy ~90s, post-rollout eval ~35s, UI smoke ~10s).
Tell the user this estimate before starting. If actual duration deviates by more than 20%, explain why.

## Duration Recalibration (required)

After every deploy attempt:
- Append one line to `docs/deploy-log.md`:
  - `timestamp | duration_s | status | cache_hit | note`
- Keep append-only history.

After successful deploy:
- Read last 7 `success` rows.
- If median differs by >20% from this skill's expected duration, update the estimate and note why in the report.
- Exclude obvious anomalies (failed runs, outages, repeated retries).

## Steps

0. **Browser capability check (required before UI smoke path selection):**
   - Determine whether in-session browser automation is actually available.
   - If unavailable, do not claim screenshot/console coverage; use fallback HTTP UI checks and report the limitation.

1. **Preflight checks (all must pass):**
   - Branch/context:
     - `git branch --show-current` (confirm target branch with user if not `main`)
     - `git status --short` must be clean unless user explicitly overrides
   - Sync:
     - `git push origin main` (or approved target branch)
   - Required checks by scope:
     - Backend: `make test-unit PYTHON=.venv/bin/python`
     - Backend lint: `.venv/bin/python -m ruff check src/ tests/`
     - UI if touched:
       - `pnpm --dir ui run lint`
       - `cd ui && npx tsc -b` (use `-b`, not `--noEmit`)
   - Fly status:
     - `fly status -a cineforge-app`
   - Fly secrets:
     - `fly secrets list -a cineforge-app`
     - Confirm the currently shipped surfaced `mvp_ingest` path has its required provider secrets:
       `ANTHROPIC_API_KEY`, `CINE_FORGE_GEMINI_API_KEY`, and `CINE_FORGE_OPENAI_API_KEY`

2. **Deploy:**
   - Capture start time (`date +%s`)
   - First attempt:
     - `fly deploy --depot=false --yes`
   - If Fly fails before image build because the remote builder transport/heartbeat is broken (for example h2c/daemon-host/heartbeat errors), and preflight checks are already green, fall back once to:
     - `fly deploy --local-only --depot=false --yes`
   - If the required deploy-log append has dirtied the worktree between retries, stash only `docs/deploy-log.md` before the retry, then restore it immediately after the attempt so the retry still respects the clean-worktree guardrail.
   - If the local-only Docker build fails due to local cache/disk pressure, do one bounded cleanup before retrying:
     - `docker builder prune -af --builder desktop-linux`
   - Capture end time and duration
   - Capture post-deploy status:
     - `fly status -a cineforge-app`

3. **API smoke tests (all must pass):**
   - `curl -sf https://cineforge.copper-dog.com/api/health`
   - `curl -sf "https://cineforge.copper-dog.com/api/health/dependencies?refresh=1"`
   - `curl -sf https://cineforge.copper-dog.com/api/recipes`
   - `curl -sf https://cineforge.copper-dog.com/api/projects/recent`
   - `curl -sf https://cineforge.copper-dog.com/api/changelog`

4. **Representative post-rollout eval (must pass):**
   - Run the real surfaced Script Breakdown path against the canonical short fixture:
     - `.venv/bin/python scripts/post_rollout_breakdown_eval.py --base-url https://cineforge.copper-dog.com`
   - This eval must:
     - create a fresh project
     - upload `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
     - start `mvp_ingest`
     - fail on any stage error, including `script_bible`
     - verify `script_bible` and `project_config` artifacts land successfully

5. **UI smoke tests:**
   - If browser tooling available (preferred):
     - Open `https://cineforge.copper-dog.com/`
     - Capture screenshot(s) of landing/project flow
     - Check console for errors
   - If browser tooling unavailable (fallback):
     - `curl -sf https://cineforge.copper-dog.com/` and verify title/bundle references
     - Verify referenced JS bundle returns 200
     - Report that browser coverage was unavailable in-session

6. **Report only after all smoke checks pass:**
   - Deployed commit hash and summary
   - API check results
   - Dependency-health result (overall status plus any broken provider ids)
   - Post-rollout eval result (project id, run id, and surfaced-stage result)
   - UI check results (including whether browser or fallback path was used)
   - Health endpoint version/status
   - Total duration vs expected (+ explanation if >20% off)

7. **Log + recalibration:**
   - Append deploy row in `docs/deploy-log.md`
   - Apply recalibration rule if criteria are met

## On Failure

If any check fails:
1. Report exactly what failed and with what output.
2. Gather recent logs (bounded):
   - `timeout 10 fly logs -a cineforge-app 2>&1 | tail -30`
3. Check relevant troubleshooting in `docs/deployment.md`.
4. If the failure is a Fly remote-builder transport issue rather than an app/runtime issue, switch to the local-only fallback path instead of looping on the same remote command.
5. If the failure is local Docker disk pressure during a local-only build, do one bounded builder-cache prune and retry once.
6. If the retry required stashing `docs/deploy-log.md`, restore it before reporting so the attempt history stays complete.
7. If dependency health or the post-rollout eval fails, include the failing provider or stage id/message and current Fly secrets state.
8. For UI issues, include browser console errors if available.
9. Propose concrete fix; do not silently retry multiple times unless the user explicitly asked you to keep going.

## Guardrails

- Never deploy with failing required checks.
- Never deploy with uncommitted changes unless user explicitly approves.
- Never deploy from non-main without explicit user approval.
- Never claim success until API + UI smoke checks pass.
- Never run unbounded `fly logs` streaming.
- Always use `--depot=false` for deploy command.
