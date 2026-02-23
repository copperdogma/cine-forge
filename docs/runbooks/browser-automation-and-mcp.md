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

### Claude Code (claude-in-chrome extension)

Claude Code uses the **claude-in-chrome** Chrome extension for browser automation, accessed via `mcp__claude-in-chrome__*` tools. This is distinct from Playwright MCP.

**Setup:**
- Install the Claude browser extension from https://claude.ai/chrome
- Must be logged into claude.ai with the same account as Claude Code
- Restart Chrome after first installation
- The extension creates a "tab group" that Claude Code operates within

**Verifying it works:**
1. Call `tabs_context_mcp` — should return tab list (this works even when screenshot is broken)
2. Call `tabs_create_mcp` to create a fresh tab
3. Call `navigate` to load a URL
4. Call `computer` with `action: screenshot` — if this succeeds, the extension is healthy

**Critical rule: always use a fresh MCP tab for screenshots**
- `tabs_context_mcp` and `navigate` use the extension's background page and work on any tab
- `computer` (screenshot, click, etc.) requires a tab the extension actively controls
- Pre-existing tabs, tabs opened before the session, or detached tabs will fail
- **Fix:** always call `tabs_create_mcp` → `navigate` → `screenshot` rather than reusing existing tabs

**Known failure modes:**

| Error | Cause | Fix |
|---|---|---|
| `Browser extension is not connected` | Extension lost connection or tab is in wrong state | Create fresh tab with `tabs_create_mcp`, navigate, retry |
| `Detached while handling command` | Tab content was unloaded or detached from extension | Create fresh tab with `tabs_create_mcp`, navigate, retry |
| `Cannot access contents of the page. Extension manifest must request permission...` | Tab was opened before the current session / not in extension's tab group | Create fresh tab with `tabs_create_mcp`, navigate, retry |
| `No other browsers available to switch to` | `switch_browser` found no other Chrome window with the extension | Ignore — this is a browser-switching utility, not the fix for the above errors |

**Console errors from extension itself:**
- `TypeError: Failed to fetch` in `content_script.js` is the extension polling claude.ai — not an app error, safe to ignore

**Minimal probe:**
```
tabs_create_mcp → navigate(url) → computer(screenshot) → read_console_messages(pattern="error")
```

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
