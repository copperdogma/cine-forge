# deploy

Deploy CineForge to production on Fly.io.

## Reference

Full infrastructure details, architecture, DNS, and troubleshooting: `docs/deployment.md`

## Steps

1. **Pre-flight checks** (all must pass before deploying):
   - `git status --short` — working tree must be clean (no uncommitted changes)
   - `.venv/bin/python -m pytest -m unit --tb=short -q` — all unit tests pass
   - `.venv/bin/python -m ruff check src/ tests/` — lint clean
   - Verify on `main` branch: `git branch --show-current`
2. **Deploy**:
   - `fly deploy --depot=false --yes`
   - Watch output for build success and health check pass
3. **Verify**:
   - `fly status -a cineforge-app` — machine is running
   - `curl -s https://cineforge.copper-dog.com/api/health` — returns `{"status": "ok"}`
   - `fly logs -a cineforge-app` — check last 20 lines for errors
4. **Report**: Summarize what was deployed (commit hash, key changes) and verification results.

## Guardrails

- NEVER deploy with uncommitted changes — commit or stash first.
- NEVER deploy with failing tests or lint errors.
- NEVER deploy from a non-main branch without explicit user approval.
- If deploy fails, check `docs/deployment.md#troubleshooting` before retrying.
- If health check fails after deploy, run `fly logs -a cineforge-app` and report the error — do not blindly retry.
- Always use `--depot=false` — Depot has intermittent 401 registry push errors.
