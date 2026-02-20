# Browser Automation and MCP Runbook

Canonical operational guide for browser-based validation in AI-led workflows.

Use this for:
- UI screenshot verification
- Browser console error checks
- Browser automation troubleshooting
- MCP setup/recovery across agent environments

## Scope and Placement

Keep responsibilities split:
- Policy and expected behavior: `AGENTS.md` / agent instruction files
- Tool/server wiring: environment MCP config (`codex mcp`, Cursor MCP config, Claude MCP config, Gemini MCP config)
- Operational troubleshooting and recovery steps: this runbook

This keeps instruction files small and stable while preserving concrete fix procedures.

## Environment Matrix

### Codex
- MCP config path: `~/.codex/config.toml` (or via `codex mcp ...`)
- List servers: `codex mcp list`
- Add Playwright MCP: `codex mcp add playwright -- npx -y @playwright/mcp@latest`
- Validate browser tooling via nested run:
  - `mkdir -p tmp/browser-smoke tmp/browser-smoke/logs`
  - `codex exec --sandbox workspace-write --skip-git-repo-check -o tmp/browser-smoke/logs/landing.txt "Use playwright MCP to navigate to https://cineforge.copper-dog.com/, take screenshot tmp/browser-smoke/mcp-landing.png, and report console errors at level error."`

### Cursor
- MCP config path: `~/.cursor/mcp.json`
- Verify browser MCP server entry exists and is enabled
- Restart Cursor/agent session after config changes

### Claude Code
- Configure MCP server in Claude Code MCP settings/config
- Restart session after enabling/changing MCP servers
- Verify by executing one minimal browser probe (navigate + screenshot + console check)

### Gemini CLI
- MCP config path: `.gemini/settings.json` (project) or `~/.gemini/settings.json` (global)
- List servers: `gemini mcp list`
- Add Playwright MCP: `gemini mcp add playwright npx -- -y @playwright/mcp@latest`
- Restart CLI session after config changes (tools are discovered at startup). **Verified: Integrated browser tools (navigate, click, screenshot) become available natively after restart.**
- Verify browser tooling via fallback script if tools are missing:
  - `npm install playwright`
  - `node scripts/ui_smoke_probe.mjs` (See `scripts/` for reference implementation)

## Minimal Browser Probe (Required)

A browser setup is considered working only when all are true:
1. Navigate to app URL successfully.
2. Save a screenshot artifact.
3. Return browser console errors at `error` level.

For CineForge production smoke:
- Landing page: `https://cineforge.copper-dog.com/`
- Project page: `https://cineforge.copper-dog.com/<project-id>`
- Artifacts:
  - `tmp/browser-smoke/mcp-landing.png`
  - `tmp/browser-smoke/mcp-project.png`

## Troubleshooting Flow

1. Confirm whether browser MCP tools are visible in the current agent session.
2. If not visible, verify MCP server is configured for the current environment (not a different tool's config).
3. Restart the host app/CLI session after MCP config changes.
4. Re-run the minimal browser probe.
5. If still failing, classify failure:
   - MCP server missing
   - MCP server start failure
   - Browser launch failure
   - Page navigation failure
   - Screenshot/console tool failure
6. Capture evidence:
   - exact command/tool call
   - error text
   - whether API fallback checks passed
7. Use fallback HTTP checks only when browser path is blocked:
   - `curl -sf https://cineforge.copper-dog.com/` and verify `<title>CineForge</title>`
   - verify JS bundle returns HTTP 200

## Common Failure Modes (Observed)

1. **Wrong MCP config file for the active agent**
   - Symptom: browser tools unavailable even though another app has MCP configured.
   - Cause: MCP configured in Cursor/Claude/Gemini config, but current run is Codex (or vice versa).
   - Fix: configure MCP for the current environment, then restart session.

2. **Gemini CLI requires restart for tool discovery**
   - Symptom: `gemini mcp add` reports success but tools like `playwright_navigate` are not found.
   - Cause: Gemini CLI loads available tools once at the beginning of the session.
   - Fix: Close the current session and start a new one after modifying settings. Use a local Playwright script (`node scripts/smoke_test_ui.mjs`) as a fallback during the current session.

2. **Redirecting logs into non-existent directory**
   - Symptom: shell fails before browser command starts (`No such file or directory`).
   - Fix: create directories first (`mkdir -p tmp/browser-smoke tmp/browser-smoke/logs`) before `> .../log.txt`.

3. **Verbose nested-run output is hard to parse**
   - Symptom: giant stdout logs with mixed tool traces.
   - Fix: use `codex exec -o <file>` to save final message and keep deterministic evidence.

4. **`list_mcp_resources` appears empty while nested browser runs still work**
   - Symptom: resource listing looks unavailable, but `codex exec` with MCP succeeds.
   - Fix: trust probe execution result; record the discrepancy and continue with evidence artifacts.

## Known CineForge-Specific Gotcha

- Cursor MCP config (`~/.cursor/mcp.json`) does not automatically configure Codex MCP.
- Fix: configure Codex MCP directly (`codex mcp add ...`) and validate with `codex exec` browser probe.

## References

- Deployment skill: `skills/deploy/SKILL.md`
- Deployment reference: `docs/deployment.md`
- Project policy: `AGENTS.md`
