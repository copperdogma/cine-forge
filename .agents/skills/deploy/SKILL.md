---
name: deploy
description: Deploy Storybook to production
user-invocable: false
---

# /deploy

> **NOT READY — CANNOT BE USED YET.**
> This is a scaffold based on CineForge's deploy skill. When ready to deploy, `/scout` the CineForge repo for the latest deploy patterns — they evolve frequently.

Deploy Storybook to production on Fly.io.

## What CineForge's Deploy Skill Does (Reference)

CineForge's deploy skill is the gold standard. Key patterns to adopt:

1. **Pre-flight checks** — Must pass before deploying:
   - On correct branch (main)
   - Working tree clean (if dirty, commit first via `/check-in-diff`)
   - Push to remote so it's up to date
   - All tests pass
   - Lint clean

2. **Deploy** — `fly deploy` with timing

3. **Tiered smoke tests** — Three levels of verification:
   - **API smoke tests** — curl health endpoint, key API routes
   - **UI smoke tests (browser)** — Navigate via Chrome MCP, screenshot, check console errors
   - **UI smoke tests (HTTP fallback)** — If browser MCP unavailable, curl HTML and verify JS bundle loads

4. **Expected duration tracking** — Estimate before starting, explain deviations >20%, update estimate if it's genuinely changed

5. **Failure protocol** — Immediately report what failed, grab logs, check troubleshooting docs, diagnose and propose fix. Never silently retry or declare success.

6. **Guardrails:**
   - Never deploy with uncommitted changes
   - Never deploy with failing tests
   - Never deploy from non-main without approval
   - Never declare success until ALL smoke tests pass
   - Never run `fly logs` without timeout (streams forever)

## Storybook-Specific Adaptations Needed

When building this out:

- [ ] Decide deployment target (Fly.io single Docker container per ADR-002)
- [ ] Define health endpoint (`/api/health`)
- [ ] Define key API routes to smoke test
- [ ] Define UI smoke test expectations (landing page, chat interface)
- [ ] Set up `docs/deployment.md` with full infrastructure reference
- [ ] Adapt pre-flight checks for pnpm (`pnpm typecheck && pnpm test && pnpm lint`)
- [ ] Set up DNS / domain
- [ ] Docker multi-stage build (backend serves frontend as static files)
- [ ] Consider: browser automation runbook (CineForge has `docs/runbooks/browser-automation-and-mcp.md`)

## When to Build This

After the first deployable version exists (post-MVP scaffolding stories). Don't build the skill before there's something to deploy.
