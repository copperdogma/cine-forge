# deploy

Deploy CineForge to production on Fly.io.

## Reference

Full infrastructure details, architecture, DNS, and troubleshooting: `docs/deployment.md`

## Expected Duration

**~2 minutes total** (pre-flight ~15s, deploy ~90s, verify ~10s). Last updated: 2026-02-18.

Tell the user this estimate before starting. If actual duration deviates by more than 20%, investigate why (slow Docker build? large context transfer? cold remote builder?) and explain in the report. If the new duration reflects a genuine change (e.g., more dependencies, larger frontend), update the estimate above.

## Steps

1. **Pre-flight checks** (all must pass before deploying):
   - `git status --short` — working tree must be clean (no uncommitted changes)
   - `.venv/bin/python -m pytest -m unit --tb=short -q` — all unit tests pass
   - `.venv/bin/python -m ruff check src/ tests/` — lint clean
   - Verify on `main` branch: `git branch --show-current`
2. **Deploy**:
   - Record the start time: `date +%s`
   - `fly deploy --depot=false --yes`
   - Watch output for build success and health check pass
3. **Verify**:
   - `fly status -a cineforge-app` — machine is running
   - `curl -s https://cineforge.copper-dog.com/api/health` — returns `{"status": "ok"}`
   - If health check succeeds, deploy is **done**. Record end time: `date +%s`
4. **Report**:
   - What was deployed (commit hash, key changes)
   - Verification results
   - Total duration vs expected. If off by >20%, explain why.

## Guardrails

- NEVER deploy with uncommitted changes — commit or stash first.
- NEVER deploy with failing tests or lint errors.
- NEVER deploy from a non-main branch without explicit user approval.
- If deploy fails, check `docs/deployment.md#troubleshooting` before retrying.
- If health check fails after deploy, check `docs/deployment.md#troubleshooting` for the error pattern. Do not blindly retry.
- Always use `--depot=false` — Depot has intermittent 401 registry push errors.
- NEVER run `fly logs` without a timeout — it streams forever and will hang. Use `timeout 10 fly logs -a cineforge-app 2>&1 | tail -20` if you need logs, but only to debug failures — not as a success check.
