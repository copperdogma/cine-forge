# deploy

Deploy CineForge to production on Fly.io.

## Reference

Full infrastructure details, architecture, DNS, and troubleshooting: `docs/deployment.md`
Browser automation and MCP troubleshooting (cross-environment): `docs/runbooks/browser-automation-and-mcp.md`

## Expected Duration

**~3 minutes total** (pre-flight ~15s, deploy ~90s, smoke test ~60s). Last updated: 2026-02-18.

Tell the user this estimate before starting. If actual duration deviates by more than 20%, investigate why (slow Docker build? large context transfer? cold remote builder?) and explain in the report. If the new duration reflects a genuine change (e.g., more dependencies, larger frontend), update the estimate above.
Note: cache-hit deploys with unchanged layers can complete much faster (~60s); call this out explicitly in the report when it happens.

## Steps

0. **Browser capability check (required before UI smoke test path selection)**:
   - Check whether Chrome MCP tooling is actually available in the current agent session.
   - If unavailable, do **not** claim screenshot/console coverage; use the fallback HTTP UI smoke path and report the limitation explicitly.
   - If available, use Chrome MCP screenshot + console checks as the primary UI verification path.
1. **Pre-flight checks** (all must pass before deploying):
   - `git branch --show-current` — must be on `main` (or get explicit user approval for other branches)
   - `git status --short` — working tree must be clean. If dirty, commit first (use `/check-in-diff` to ensure CHANGELOG.md is included), then continue.
   - `git push origin main` — ensure remote is up to date with local
   - `.venv/bin/python -m pytest -m unit --tb=short -q` — all unit tests pass
   - `.venv/bin/python -m ruff check src/ tests/` — lint clean
2. **Deploy**:
   - Record the start time: `date +%s`
   - `fly deploy --depot=false --yes`
   - Watch output for build success and health check pass
3. **API smoke test** (all must pass — if ANY fail, go to On Failure):
   - `curl -sf https://cineforge.copper-dog.com/api/health` — returns JSON with `"status": "ok"` and `version`
   - `curl -sf https://cineforge.copper-dog.com/api/recipes` — returns JSON array (backend routing + config loading)
   - `curl -sf https://cineforge.copper-dog.com/api/projects/recent` — returns JSON array (filesystem/volume access)
   - `curl -sf https://cineforge.copper-dog.com/api/changelog` — returns text (CHANGELOG.md in image)
4. **UI smoke test**:
   - **If Chrome MCP is available** (preferred):
     - Navigate to `https://cineforge.copper-dog.com/`
     - Screenshot — verify landing page loads (CineForge branding, project list or upload area visible)
     - If existing projects are listed, click into one and screenshot — verify project shell renders (sidebar nav, content area)
     - If no projects exist, upload `tests/fixtures/normalize_inputs/valid_screenplay.fountain` (7-line test script) and verify the project is created
     - Check browser console for errors: `read_console_messages` with pattern `error|Error|ERR`
     - Screenshot final state
   - **If direct in-session browser tools are unavailable but Codex Playwright MCP is configured**:
     - Create artifact/log directories first: `mkdir -p tmp/browser-smoke tmp/browser-smoke/logs`
     - Run nested browser probes and persist outputs:
       - `codex exec --sandbox workspace-write --skip-git-repo-check -o tmp/browser-smoke/logs/landing.txt "Use playwright MCP to navigate to https://cineforge.copper-dog.com/, take full-page screenshot tmp/browser-smoke/deploy-landing.png, then return browser console errors at level error."`
       - `codex exec --sandbox workspace-write --skip-git-repo-check -o tmp/browser-smoke/logs/project.txt "Use playwright MCP to navigate to https://cineforge.copper-dog.com/<project-id>, take full-page screenshot tmp/browser-smoke/deploy-project.png, then return browser console errors at level error."`
     - Verify artifacts exist: `ls -lh tmp/browser-smoke/deploy-landing.png tmp/browser-smoke/deploy-project.png`
   - **If Chrome MCP is unavailable** (fallback):
     - `curl -sf https://cineforge.copper-dog.com/` — returns HTML with `<title>CineForge</title>`
     - Verify the HTML references a JS bundle (`assets/index-*.js`)
     - `curl -sf -o /dev/null -w "%{http_code}"` the JS bundle URL — returns 200
     - Note in report that browser-based testing was skipped and why
   - Record end time: `date +%s`
5. **Report** (only after ALL smoke tests pass):
   - What was deployed (commit hash, key changes)
   - API smoke test results (4 checks)
   - UI smoke test results (screenshots taken, any console errors)
   - Version reported by health endpoint
   - Total duration vs expected. If off by >20%, explain why.

## Chrome MCP Troubleshooting

Use the canonical runbook:
- `docs/runbooks/browser-automation-and-mcp.md`

Deploy-specific rule:
- Do not claim screenshot/console coverage unless browser tooling actually ran in-session.
- If browser tooling is unavailable, run fallback HTTP UI checks and report the limitation.
- When using nested Codex browser checks, include screenshot file paths and console-error summary from saved logs in the deploy report.

## On Failure

If any smoke test fails:
1. **Immediately tell the user** what failed and what the response/screenshot showed.
2. Run `timeout 10 fly logs -a cineforge-app 2>&1 | tail -30` to get recent logs.
3. Check `docs/deployment.md#troubleshooting` for matching error patterns.
4. If it's a UI issue, check `read_console_messages` for JavaScript errors.
5. Diagnose and propose a fix. Do NOT silently retry or declare success.

## Guardrails

- NEVER deploy with uncommitted changes — commit or stash first.
- NEVER deploy with failing tests or lint errors.
- NEVER deploy from a non-main branch without explicit user approval.
- NEVER declare success until ALL smoke tests pass (API + UI).
- NEVER run `fly logs` without a timeout — it streams forever and will hang.
- Always use `--depot=false` — Depot has intermittent 401 registry push errors.
