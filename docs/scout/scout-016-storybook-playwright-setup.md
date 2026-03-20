# Scout 016 — storybook-playwright-setup

**Source:** `/Users/cam/Documents/Projects/Storybook/storybook`
**Scouted:** 2026-03-20
**Scope:** Storybook browser automation and Playwright verification patterns, focused on recovery/setup quality rather than product UI behavior
**Previous:** Scout 001 (Storybook repo, 2026-02-22), Scout 015 (Storybook methodology delta, 2026-03-20)
**Status:** Complete

## Findings

1. **Storybook's durable pattern is isolated browser automation, not a special Playwright profile hack** — HIGH value
   What: Storybook's current reusable browser guidance lives in `docs/runbooks/browser-automation.md` and emphasizes fresh sessions/tabs, failure classification, and retry discipline. Its adopted `webapp-testing` package came from Anthropic and centers on isolated Playwright runs plus `with_server.py`, not on keeping a long-lived shared Chrome profile healthy.
   Us: CineForge already imported the `webapp-testing` skill and helper, but the browser runbook drifted toward MCP-environment mechanics without documenting when to reset the Playwright-scoped session or when to prefer local isolated Playwright fallback.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook's browser runbook plus the earlier `webapp-testing` adoption recorded in Scout 001
   Invariant: browser verification should recover through small, deterministic operational steps instead of ad hoc profile surgery
   Adaptation: CineForge needs a Playwright-MCP cleanup path because the repo now uses `@playwright/mcp` across Codex/Cursor/Gemini, not only Claude-in-Chrome
   Proof target: the runbook points to a deterministic reset step and the reset actually restores Playwright automation in this environment

2. **CineForge has a local recovery precedent that was not codified** — HIGH value
   What: Story 131 recorded that Playwright recovered after killing only the orphaned Playwright-scoped Chrome session; Story 121 later retried by manually deleting singleton links but still lacked a documented targeted reset tool.
   Us: Recovery knowledge existed only in story work logs, so the next validation repeated manual debugging instead of using a repo-owned operational fix.
   Recommendation: **Adopt inline**

3. **No extra Storybook code setup remains to port** — MEDIUM value
   What: Storybook does not currently carry a richer Playwright config or hidden helper beyond the runbook/skill patterns already imported. There was no additional `playwright.config.ts` or package-level setup worth copying into CineForge.
   Us: CineForge already has the relevant imported pieces. The gap was documentation drift and lack of a targeted cleanup tool.
   Recommendation: **Skip**

## Approved

- [x] 1. Isolated-browser recovery guidance — Adopted
- [x] 2. Codify the local Playwright reset pattern — Adopted
- [x] 3. Extra Storybook code/config port — Skipped

## Skipped / Rejected

- 3. Extra Storybook code/config port — Storybook had no additional Playwright config or setup worth copying; the useful parts were already present in CineForge via the earlier `webapp-testing` adoption

## Verification

- `python3 scripts/reset_playwright_mcp.py --dry-run` reported `76` stale Playwright-MCP / `mcp-chrome` processes and `9` removable singleton lock files.
- `python3 scripts/reset_playwright_mcp.py` terminated those `76` stale processes and cleared `6` live singleton lock files.
- `python3 -m py_compile scripts/reset_playwright_mcp.py` passed.
- Fresh isolated Playwright run in a temp workspace (`/tmp/cineforge-playwright-probe`) loaded `https://example.com`, captured a screenshot, and reported `consoleErrors=[]`.

## Evidence

- Added targeted cleanup tool: `scripts/reset_playwright_mcp.py`
- Updated `docs/runbooks/browser-automation-and-mcp.md` to document the stale-Playwright-profile failure mode, point to the new reset script, and fix the stale fallback script reference
- Screenshot artifact from the fresh isolated Playwright verification: `tmp/browser-smoke/example-playwright-reset.png`
