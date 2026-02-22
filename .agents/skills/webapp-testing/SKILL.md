---
name: webapp-testing
description: Toolkit for testing web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing screenshots, and viewing browser logs.
---

# Web Application Testing

*Adapted from [anthropics/skills/webapp-testing](https://github.com/anthropics/skills). Original: Apache 2.0.*

Test CineForge's web application using Python Playwright scripts.

## Helper Scripts

- .agents/skills/webapp-testing/scripts/with_server.py — Manages server lifecycle (supports multiple servers)

Always run scripts with --help first to see usage. These scripts are black-box utilities — call them directly rather than reading their source.

## Decision Tree

Task → Is the server already running?
    ├─ No → Use with_server.py to start it:
    │        python .agents/skills/webapp-testing/scripts/with_server.py \
    │          --server "pnpm --dir ui dev" --port 5188 \
    │          -- python your_test.py
    │
    └─ Yes → Write Playwright script directly:
        1. Navigate and wait for networkidle
        2. Take screenshot or inspect DOM
        3. Identify selectors from rendered state
        4. Execute actions with discovered selectors

## Example: Testing with Server Management

Start UI dev server and run test:
  python .agents/skills/webapp-testing/scripts/with_server.py \
    --server "pnpm --dir ui dev" --port 5188 \
    -- python test_ui.py

Multiple servers (API + frontend):
  python .agents/skills/webapp-testing/scripts/with_server.py \
    --server "PYTHONPATH=src python -m cine_forge.api" --port 8642 \
    --server "pnpm --dir ui dev" --port 5188 \
    -- python test_full_stack.py

## Writing Test Scripts

Include only Playwright logic — servers are managed by the helper:

  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto('http://localhost:5188')
      page.wait_for_load_state('networkidle')  # CRITICAL: Wait for JS
      # ... your test logic
      browser.close()

## Reconnaissance-Then-Action Pattern

1. Inspect rendered DOM:
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()

2. Identify selectors from inspection results

3. Execute actions using discovered selectors

## Common Pitfall

Never inspect the DOM before waiting for networkidle on dynamic apps.
Always wait for page.wait_for_load_state('networkidle') before inspection.

## Best Practices

- Use sync_playwright() for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: text=, role=, CSS selectors, or IDs
- Add appropriate waits: page.wait_for_selector() or page.wait_for_timeout()
- Save screenshots to /tmp/ for inspection
