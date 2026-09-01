# Browser Automation and MCP Runbook

Canonical operational guide for browser-based validation in AI-led workflows.

Use this for:
- UI screenshot verification
- Browser console error checks
- Browser tool selection
- Browser automation troubleshooting
- MCP setup/recovery across agent environments

## Choosing the Browser Lane

- **Playwright is the default for deterministic testing**: use it for
  repeatable setup, selectors, assertions, scripted smoke tests, and regression
  coverage.
- **Computer Use is better for vision-led and real-browser tasks**: use it when
  the question is "does this look right?", when you need to judge rendered
  layout or clipped text, or when the flow involves OAuth, permission prompts,
  native dialogs, or an already-running Chrome profile.
- **Best practice is often both**: let Playwright drive the product into the
  target state, then use Computer Use or screenshot review to judge the final
  rendered result.

Simple rule:
- If the question is "does this behave correctly?", favor Playwright.
- If the question is "does this look right?", favor Computer Use.

## Scope and Placement

Keep responsibilities split:
- Policy and expected behavior: `AGENTS.md` / agent instruction files
- Tool/server wiring: environment MCP config (`codex mcp`, Cursor MCP config, Claude MCP config, Gemini MCP config)
- Operational troubleshooting and recovery steps: this runbook

This keeps instruction files small and stable while preserving concrete fix procedures.

## Codex Browser Tool Selection

For current Codex app sessions, choose the smallest browser tool that can prove
the behavior:

| Tool | Use when | Avoid when |
|---|---|---|
| Browser / in-app browser | Localhost, file, or public unauthenticated UI checks need DOM inspection, screenshots, clicks, typed input, and console capture. | The flow needs the user's Chrome profile, existing tabs, extension behavior, or file upload. |
| Chrome / Codex Chrome Extension | The task depends on the user's Chrome profile: signed-in sessions, cookies, existing tabs, extensions, or authenticated remote pages. | The same proof can run in the isolated in-app browser. Extension-origin console noise and profile state make evidence less clean. |
| Playwright / repo test tooling | The proof must be deterministic, repeatable, selector-driven, file-upload capable, or close to CI/e2e coverage. | The task is exploratory product judgment where screenshots and direct inspection matter more than a script. |
| Computer Use | A native browser surface is required: browser chrome, OS dialogs, OAuth handoffs, permission prompts, or another desktop app involved in the flow. | Normal page DOM work, console checks, screenshots, and form filling are available through Browser, Chrome, or Playwright. |

Observed limitations from first-hand testing:

- Browser / in-app browser handled local navigation, DOM reads, clicks, typed
  input, screenshots, and console capture, but file upload was unsupported.
- Chrome handled profile-backed navigation, DOM reads, clicks, typed input,
  screenshots, console capture, and existing-tab visibility, but extension-origin
  console noise must be filtered and file upload can be blocked by extension
  access rules.
- Playwright handled deterministic selectors, screenshots, console capture, and
  file upload. Prefer it for repeatable evidence and CI-shaped probes.
- Computer Use handled OS/browser-level interaction, but lacks DOM/test-id and
  console ergonomics. Keep it for native surfaces and fallbacks.

## Environment Matrix

### Codex
- MCP config path: `~/.codex/config.toml` (or via `codex mcp ...`)
- List servers: `codex mcp list`
- Add Playwright MCP: `codex mcp add playwright -- npx -y @playwright/mcp@latest`
- Prefer Browser / in-app browser for ordinary local UI checks before adding or
  debugging Playwright MCP.
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
4. Record which browser tool was used and why.

For CineForge production smoke:
- Landing page: `https://cineforge.copper-dog.com/`
- Project page: `https://cineforge.copper-dog.com/<project-id>`
- Artifacts:
  - `tmp/browser-smoke/mcp-landing.png`
  - `tmp/browser-smoke/mcp-project.png`

## Troubleshooting Flow

1. Confirm the task actually needs MCP/Playwright. For ordinary Codex localhost
   UI checks, try Browser / in-app browser first.
2. Confirm whether browser MCP tools are visible in the current agent session.
3. If not visible, verify MCP server is configured for the current environment (not a different tool's config).
4. Restart the host app/CLI session after MCP config changes.
5. Re-run the minimal browser probe.
6. If still failing, classify failure:
   - MCP server missing
   - MCP server start failure
   - Browser launch failure
   - Page navigation failure
   - Screenshot/console tool failure
   - Local UI server bound to the wrong host/port
7. If the error looks like a wedged Playwright profile (`Opening in existing browser session`, `UKM database locked`, `bootstrap_check_in ... Permission denied`, or attach timeouts), reset only the Playwright-scoped session and retry once:
   - `python3 scripts/reset_playwright_mcp.py`
   - If the current MCP transport closes because the reset killed the stale `playwright-mcp` process itself, restart the host session once and re-run the probe
8. If the error is `ENOENT` / permission denied around `/.playwright-mcp`, treat it as a broken MCP working-directory/output-root setup, not an app failure:
   - Cause: Playwright MCP resolves its artifact output root from the server `cwd`; if the Codex MCP server starts with `cwd=/`, it tries to create `/.playwright-mcp`
   - Fix the Codex MCP config in `~/.codex/config.toml` so the Playwright server has a writable cwd and explicit output/profile dirs, for example:
     ```toml
     [mcp_servers.playwright]
     command = "npx"
     args = ["-y", "@playwright/mcp@latest"]
     cwd = "/Users/<you>"

     [mcp_servers.playwright.env]
     HOME = "/Users/<you>"
     PLAYWRIGHT_MCP_OUTPUT_DIR = "/Users/<you>/.codex/playwright"
     PLAYWRIGHT_MCP_USER_DATA_DIR = "/Users/<you>/Library/Caches/ms-playwright/mcp-chrome-profile"
     ```
   - Then restart the host Codex session and rerun the minimal probe
9. For local Vite-backed probes in this repo, prefer a direct Vite invocation over the npm script wrapper:
   - Use `pnpm --dir ui exec vite --host 127.0.0.1 --port 5174`
   - Avoid `pnpm --dir ui run dev -- --host 127.0.0.1 --port 5174` for automation here; in this workspace it leaves Vite on `localhost`, which can produce `ERR_CONNECTION_REFUSED` when the probe hits `127.0.0.1`
10. Capture evidence:
   - exact command/tool call
   - error text
   - whether API fallback checks passed
11. Use fallback HTTP checks only when browser path is blocked:
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
   - Fix: Close the current session and start a new one after modifying settings. Use a local Playwright script (`node scripts/ui_smoke_probe.mjs`) as a fallback during the current session.

3. **Stale Playwright MCP daemons or Playwright-scoped Chrome profile**
   - Symptom: browser attach fails with `Opening in existing browser session`, `UKM database locked`, `bootstrap_check_in ... Permission denied`, or repeated timeouts.
   - Cause: orphaned `playwright-mcp` / `npm exec @playwright/mcp@latest` processes or a stuck Chrome process using `~/Library/Caches/ms-playwright/mcp-*`.
   - Fix: run `python3 scripts/reset_playwright_mcp.py`, then retry the browser probe once. Prefer this over manually deleting the whole profile tree.

4. **Codex Playwright MCP started with `cwd=/`**
   - Symptom: browser actions fail immediately with `ENOENT: no such file or directory, mkdir '/.playwright-mcp'` or similar permission errors under `/.playwright-mcp`.
   - Cause: Playwright MCP resolves its output directory from the server working directory. If Codex launches the MCP server with `cwd=/`, the tool tries to write to the filesystem root.
   - Fix: set `mcp_servers.playwright.cwd` plus explicit `PLAYWRIGHT_MCP_OUTPUT_DIR` and `PLAYWRIGHT_MCP_USER_DATA_DIR` in `~/.codex/config.toml`, restart the Codex session, then rerun the minimal probe.

5. **Redirecting logs into non-existent directory**
   - Symptom: shell fails before browser command starts (`No such file or directory`).
   - Fix: create directories first (`mkdir -p tmp/browser-smoke tmp/browser-smoke/logs`) before `> .../log.txt`.

6. **Verbose nested-run output is hard to parse**
   - Symptom: giant stdout logs with mixed tool traces.
   - Fix: use `codex exec -o <file>` to save final message and keep deterministic evidence.

7. **`list_mcp_resources` appears empty while nested browser runs still work**
   - Symptom: resource listing looks unavailable, but `codex exec` with MCP succeeds.
   - Fix: trust probe execution result; record the discrepancy and continue with evidence artifacts.

8. **UI dev script wrapper can miss the requested host binding**
   - Symptom: `with_server.py` reports the UI ready, but Playwright gets `ERR_CONNECTION_REFUSED` on `http://127.0.0.1:<port>/...`; Vite logs still say `Local: http://localhost:<port>/`.
   - Cause: `pnpm --dir ui run dev -- --host 127.0.0.1 --port <port>` passes a literal `--` through the script wrapper in this repo, so Vite ignores the requested host override.
   - Fix: start the UI with `pnpm --dir ui exec vite --host 127.0.0.1 --port <port>` for automated probes.

## Known CineForge-Specific Gotcha

- Cursor MCP config (`~/.cursor/mcp.json`) does not automatically configure Codex MCP.
- Fix: configure Codex MCP directly (`codex mcp add ...`) and validate with `codex exec` browser probe.

## References

- Deployment skill: `skills/deploy/SKILL.md`
- Deployment reference: `docs/deployment.md`
- Project policy: `AGENTS.md`
