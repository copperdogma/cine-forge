# Deployment & Hosting Reference

Canonical reference for CineForge's production infrastructure. For deploying, use the `/deploy` skill.

## Infrastructure Map

| Component | Service | Details |
|---|---|---|
| **App hosting** | Fly.io | App: `cineforge-app`, region: `ord` (Chicago) |
| **Domain** | `cineforge.copper-dog.com` | Also accessible at `cineforge-app.fly.dev` |
| **DNS** | Cloudflare | Zone: `copper-dog.com`, Zone ID: `372acf29f0a6f95c35e9f7ea94aa7efa` |
| **SSL** | Let's Encrypt (via Fly.io) | Auto-renewed, CNAME-validated |
| **Storage** | Fly.io Volume | `cineforge_data_v2` 1GB mounted at `/app/output` |
| **Secrets** | Fly.io Secrets | `ANTHROPIC_API_KEY`, `CINE_FORGE_GEMINI_API_KEY`, `CINE_FORGE_OPENAI_API_KEY`, `CINE_FORGE_XAI_API_KEY` |
| **Container** | Multi-stage Docker | Node 24 (frontend build) → Python 3.12-slim (runtime), ~168MB |
| **Cost** | ~$5-7/month | shared-cpu-2x, 512MB RAM, 1GB volume, auto-stop |

## Architecture

```
┌─────────────────────────────────────────────┐
│  Fly.io Machine (shared-cpu-2x, 512MB)      │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ uvicorn → FastAPI                   │    │
│  │   /api/*  → Python handlers         │    │
│  │   /*      → SPA catch-all (static/) │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  /app/src/       Python source (PYTHONPATH) │
│  /app/static/    Vite frontend build        │
│  /app/configs/   Recipe YAML configs        │
│  /app/output/    ← Fly Volume (persists)    │
└─────────────────────────────────────────────┘
```

- **Single container**: FastAPI serves both the API (`/api/*`) and frontend static files (SPA catch-all).
- **Volume at `/app/output`**: Projects, runs, and artifacts persist across deploys. Configs/recipes are baked into the image.
- **Auto-stop**: Machine stops when idle, auto-starts on request (~5-10s cold start).
- **No auth**: App is open (2 users: Cam + sister). No login required.
- **Health check**: `GET /api/health` every 15s, 10s grace period.
- **Dependency health**: `GET /api/health/dependencies` exposes cached provider readiness for Anthropic, Google, OpenAI, and xAI; use `?refresh=1` for an immediate post-rollout probe.
- **Live capability smoke**: `POST /api/health/live-smoke` runs a bounded real-call smoke across the default text, storyboard-image, scene-render video, and shipped AI-previz video lanes. Use it before an expensive QA session or after credential changes when you need stronger proof than cheap readiness alone.

## Container Environment

| Var | Value | Purpose |
|---|---|---|
| `PYTHONPATH` | `/app/src` | Python module resolution |
| `CINEFORGE_STATIC_DIR` | `/app/static` | Frontend build directory |
| `ANTHROPIC_API_KEY` | (Fly secret) | AI chat feature |
| `CINE_FORGE_GEMINI_API_KEY` | (Fly secret) | `mvp_ingest` `script_bible_v1` default Gemini 3.5 Flash-Lite transport |
| `CINE_FORGE_OPENAI_API_KEY` | (Fly secret) | `mvp_ingest` `project_config_v1` QA/default OpenAI transport |
| `CINE_FORGE_XAI_API_KEY` | (Fly secret) | `ai_previz_generation` shipped `xai_grok_imagine_video` transport; legacy `XAI_API_KEY` is accepted by the app but should not be the preferred Fly secret name |

## Docker Build

Multi-stage build defined in `/Dockerfile`:

1. **Stage 1 (frontend)**: `node:24-slim` — `npm ci && npm run build` → produces `/app/ui/dist/`
2. **Stage 2 (runtime)**: `python:3.12-slim` — pinned `uv` bootstrap + `uv pip install --exclude-newer <7d cutoff> .` → copies frontend dist to `/app/static/`
3. Runs as non-root user `cineforge` (uid 1001)
4. Entrypoint: `uvicorn cine_forge.api.app:app --host 0.0.0.0 --port 8000`

## CLI Commands

### Deploy
```bash
fly deploy --depot=false --yes
```

### Operations
```bash
fly status -a cineforge-app       # Machine state, image, region
fly logs -a cineforge-app         # Live log tail
fly ssh console -a cineforge-app  # Shell into running container
```

### Secrets
```bash
fly secrets list -a cineforge-app
fly secrets set KEY=VALUE -a cineforge-app

# xAI AI-previz lane; do not paste or log the value outside the shell
fly secrets set CINE_FORGE_XAI_API_KEY=<key> -a cineforge-app
```

### Post-rollout eval
```bash
.venv/bin/python scripts/post_rollout_breakdown_eval.py \
  --base-url https://cineforge.copper-dog.com
```

This creates a fresh project, uploads the canonical short
`tests/fixtures/ingest_inputs/open_frequency_short.fountain` fixture, starts
the surfaced `Break Down Script` (`mvp_ingest`) flow, and fails if
`script_bible` or `project_config` do not land.

### Dependency health
```bash
curl -sf "https://cineforge.copper-dog.com/api/health/dependencies?refresh=1"
```

Use this as the fast provider-readiness signal after deploy. It should report
Anthropic, Google, OpenAI, and xAI separately. The xAI entry checks the shipped
`grok-imagine-video` model-access surface without generating media. Do not treat
it as a replacement for the representative post-rollout eval above.

### Live capability smoke
```bash
curl -sf -X POST "https://cineforge.copper-dog.com/api/health/live-smoke"

PYTHONPATH=src .venv/bin/python scripts/live_ai_capability_smoke.py
```

Use this when the cheap dependency surface is not enough and you want a
real-generation preflight before burning time on a full manual QA session. It
is intentionally slower and more expensive than `/api/health/dependencies`
because it performs tiny real text, image, and video calls, including the
`xai_grok_imagine_video` AI-previz lane. Treat it as a bounded operator
preflight, not a startup health check.

### Volumes
```bash
fly volumes list -a cineforge-app
```

## DNS Management

DNS is on Cloudflare (not Dreamhost — Cloudflare controls nameservers for `copper-dog.com`).

Requires `CLOUDFLARE_API_TOKEN` env var (stored in `~/.zshenv`). Token has `Zone.DNS` edit permission.

```bash
source ~/.zshenv

# List all DNS records
curl -s "https://api.cloudflare.com/client/v4/zones/372acf29f0a6f95c35e9f7ea94aa7efa/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | python3 -m json.tool
```

### Current DNS Records
| Record | Type | Value |
|---|---|---|
| `cineforge.copper-dog.com` | CNAME | `cineforge-app.fly.dev` |
| `_acme-challenge.cineforge.copper-dog.com` | CNAME | `cineforge.copper-dog.com.53l6r9n.flydns.net` |

## Troubleshooting

### `fly logs` Hangs Forever
`fly logs` is a **streaming command** — it tails logs in real-time and never exits. Do not use it as a verification step.
Fix: Use `timeout 10 fly logs -a cineforge-app 2>&1 | tail -20` if you need recent logs. But prefer `/api/health` for process liveness and `/api/health/dependencies?refresh=1` for fast provider readiness — logs are for debugging failures only.

### Depot 401 Registry Push
```
Error: failed to push to registry: 401 Unauthorized
```
Fix: Always use `--depot=false` flag. Depot (Fly's remote builder) has intermittent auth failures with the registry.

### 500 on First Request After Deploy
```
Error: Internal Server Error (500) on /api/health or any endpoint
```
Fix: Check `fly logs`. Common cause: missing or expired `ANTHROPIC_API_KEY` secret, or a volume mount issue. Verify with `fly secrets list -a cineforge-app` and `fly volumes list -a cineforge-app`.

### "Break Down Script" Fails Immediately After Deploy
If health/homepage checks pass but the surfaced Script Breakdown flow fails
within a few seconds, the deploy is not actually healthy.

Most common causes are broken provider credentials on the shipped `mvp_ingest`
path. Today that surfaced path depends on:
- `ANTHROPIC_API_KEY`
- `CINE_FORGE_GEMINI_API_KEY`
- `CINE_FORGE_OPENAI_API_KEY`

The shipped AI-previz scene path also depends on:
- `CINE_FORGE_XAI_API_KEY` (preferred) or legacy `XAI_API_KEY`

Fix:
1. Probe dependency health directly:
   - `curl -sf "https://cineforge.copper-dog.com/api/health/dependencies?refresh=1"`
2. If you need stronger proof before another costly QA run, trigger the live smoke:
   - `curl -sf -X POST "https://cineforge.copper-dog.com/api/health/live-smoke"`
3. Verify Fly sees the secret names:
   - `fly secrets list -a cineforge-app`
4. If a key is missing or stale, roll the relevant secret again. For the shipped xAI AI-previz lane, use `fly secrets set CINE_FORGE_XAI_API_KEY=<key> -a cineforge-app` and do not record the value in logs, docs, screenshots, or chat.
5. Re-run the representative post-rollout eval:
   - `.venv/bin/python scripts/post_rollout_breakdown_eval.py --base-url https://cineforge.copper-dog.com`
6. If dependency health, live smoke, or the eval still fails with `API key not valid`, the local source key is stale or revoked. Replace the local key with a known-good one, roll Fly again, and rerun all relevant checks.
7. Do not count the deploy as successful unless dependency health is green and the representative eval passes. The live smoke is an additional confidence layer, not a substitute for the eval.

### Volume Permission Errors
```
Error: PermissionError: [Errno 13] Permission denied: '/app/output/lost+found'
```
Fix: The `lost+found` directory is created by ext4 on Fly volumes and is owned by root. Code that scans `/app/output` must skip it. Fixed in `src/cine_forge/api/service.py` — if this recurs, check that directory listing code uses `try/except` on `os.scandir()`.

### Cold Start Timeout
The machine auto-stops when idle. First request after idle triggers a cold start (~5-10s). If a client times out before the machine is ready, retry. The health check (`/api/health`) has a 10s grace period for this reason.

### Frontend Shows Blank Page
If the API works but the frontend shows a blank page or 404:
1. Check that `CINEFORGE_STATIC_DIR=/app/static` is set
2. Verify the frontend build ran in Docker: `fly ssh console -a cineforge-app` → `ls /app/static/`
3. Check that the SPA catch-all in `app.py` is serving `index.html` for non-API routes

### Chrome MCP Unavailable During UI Smoke Tests
If deploy verification expects browser screenshots/console checks but the agent session cannot access Chrome MCP:
1. Confirm this is a tooling/session availability issue (not an app outage) by running API checks first (`/api/health`, `/api/health/dependencies?refresh=1`, `/api/recipes`, `/api/projects/recent`, `/api/changelog`).
2. Run fallback UI checks:
   - `curl -sf https://cineforge.copper-dog.com/` and verify `<title>CineForge</title>`
   - Verify a referenced JS bundle (`assets/index-*.js`) returns HTTP 200
3. Restart or reinitialize the agent session after enabling Chrome MCP in the host environment, then retry browser checks.
4. Report explicitly that browser automation coverage was unavailable in-session if fallback path was used.
5. For environment-specific setup and recovery steps, use:
   - `docs/runbooks/browser-automation-and-mcp.md`

### SSL Certificate Issues
SSL is auto-renewed by Fly.io via Let's Encrypt. If certs expire:
```bash
fly certs show cineforge.copper-dog.com -a cineforge-app
fly certs remove cineforge.copper-dog.com -a cineforge-app
fly certs add cineforge.copper-dog.com -a cineforge-app
```
Then verify the `_acme-challenge` CNAME still points to the correct flydns address.

## Setup From Scratch

If you ever need to recreate the infrastructure:

1. `fly apps create cineforge-app --org personal`
2. `fly volumes create cineforge_data --size 1 --region ord -a cineforge-app`
3. `fly secrets set ANTHROPIC_API_KEY=<key> CINE_FORGE_GEMINI_API_KEY=<key> CINE_FORGE_OPENAI_API_KEY=<key> CINE_FORGE_XAI_API_KEY=<key> -a cineforge-app`
4. `fly deploy --depot=false --yes`
5. `fly certs add cineforge.copper-dog.com -a cineforge-app`
6. Add DNS CNAMEs via Cloudflare API (see DNS Management above)
7. Verify: `curl https://cineforge.copper-dog.com/api/health`
8. Verify: `curl "https://cineforge.copper-dog.com/api/health/dependencies?refresh=1"`
9. Run `.venv/bin/python scripts/post_rollout_breakdown_eval.py --base-url https://cineforge.copper-dog.com`

## History

Built in Story 037 (2026-02-15 to 2026-02-17). See `docs/stories/story-037-production-deployment.md` for the full decision log including platform evaluation (Fly.io vs Dreamhost), security hardening, and smoke test results.
