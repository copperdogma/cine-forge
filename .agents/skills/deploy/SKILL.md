---
name: deploy
description: Deploy CineForge production app to Fly.io with preflight and smoke checks
user-invocable: true
---

# /deploy

Deploy CineForge to production on Fly.io.

## References

- `docs/deployment.md` — infrastructure, architecture, DNS, troubleshooting
- `docs/runbooks/browser-automation-and-mcp.md` — browser automation + MCP runbook
- `docs/deploy-log.md` — deploy duration history and recalibration memory

## Expected Duration

~1.5 minutes total (preflight ~15s, deploy ~45s, smoke tests ~30s).  
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

2. **Deploy:**
   - Capture start time (`date +%s`)
   - Run:
     - `fly deploy --depot=false --yes`
   - Capture end time and duration
   - Capture post-deploy status:
     - `fly status -a cineforge-app`

3. **API smoke tests (all must pass):**
   - `curl -sf https://cineforge.copper-dog.com/api/health`
   - `curl -sf https://cineforge.copper-dog.com/api/recipes`
   - `curl -sf https://cineforge.copper-dog.com/api/projects/recent`
   - `curl -sf https://cineforge.copper-dog.com/api/changelog`

4. **UI smoke tests:**
   - If browser tooling available (preferred):
     - Open `https://cineforge.copper-dog.com/`
     - Capture screenshot(s) of landing/project flow
     - Check console for errors
   - If browser tooling unavailable (fallback):
     - `curl -sf https://cineforge.copper-dog.com/` and verify title/bundle references
     - Verify referenced JS bundle returns 200
     - Report that browser coverage was unavailable in-session

5. **Report only after all smoke checks pass:**
   - Deployed commit hash and summary
   - API check results
   - UI check results (including whether browser or fallback path was used)
   - Health endpoint version/status
   - Total duration vs expected (+ explanation if >20% off)

6. **Log + recalibration:**
   - Append deploy row in `docs/deploy-log.md`
   - Apply recalibration rule if criteria are met

## On Failure

If any check fails:
1. Report exactly what failed and with what output.
2. Gather recent logs (bounded):
   - `timeout 10 fly logs -a cineforge-app 2>&1 | tail -30`
3. Check relevant troubleshooting in `docs/deployment.md`.
4. For UI issues, include browser console errors if available.
5. Propose concrete fix; do not silently retry multiple times.

## Guardrails

- Never deploy with failing required checks.
- Never deploy with uncommitted changes unless user explicitly approves.
- Never deploy from non-main without explicit user approval.
- Never claim success until API + UI smoke checks pass.
- Never run unbounded `fly logs` streaming.
- Always use `--depot=false` for deploy command.
