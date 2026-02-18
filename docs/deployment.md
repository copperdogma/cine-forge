# Deployment & Hosting Reference

Canonical reference for CineForge's production infrastructure. For deploying, use the `/deploy` skill.

## Infrastructure Map

| Component | Service | Details |
|---|---|---|
| **App hosting** | Fly.io | App: `cineforge-app`, region: `ord` (Chicago) |
| **Domain** | `cineforge.copper-dog.com` | Also accessible at `cineforge-app.fly.dev` |
| **DNS** | Cloudflare | Zone: `copper-dog.com`, Zone ID: `372acf29f0a6f95c35e9f7ea94aa7efa` |
| **SSL** | Let's Encrypt (via Fly.io) | Auto-renewed, CNAME-validated |
| **Storage** | Fly.io Volume | `cineforge_data` 1GB mounted at `/app/output` |
| **Secrets** | Fly.io Secrets | `ANTHROPIC_API_KEY` |
| **Container** | Multi-stage Docker | Node 24 (frontend build) → Python 3.12-slim (runtime), ~168MB |
| **Cost** | ~$3-5/month | shared-cpu-1x, 512MB RAM, 1GB volume, auto-stop |

## Architecture

```
┌─────────────────────────────────────────────┐
│  Fly.io Machine (shared-cpu-1x, 512MB)      │
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

## Container Environment

| Var | Value | Purpose |
|---|---|---|
| `PYTHONPATH` | `/app/src` | Python module resolution |
| `CINEFORGE_STATIC_DIR` | `/app/static` | Frontend build directory |
| `ANTHROPIC_API_KEY` | (Fly secret) | AI chat feature |

## Docker Build

Multi-stage build defined in `/Dockerfile`:

1. **Stage 1 (frontend)**: `node:24-slim` — `npm ci && npm run build` → produces `/app/ui/dist/`
2. **Stage 2 (runtime)**: `python:3.12-slim` — `pip install .` → copies frontend dist to `/app/static/`
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
```

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
3. `fly secrets set ANTHROPIC_API_KEY=<key> -a cineforge-app`
4. `fly deploy --depot=false --yes`
5. `fly certs add cineforge.copper-dog.com -a cineforge-app`
6. Add DNS CNAMEs via Cloudflare API (see DNS Management above)
7. Verify: `curl https://cineforge.copper-dog.com/api/health`

## History

Built in Story 037 (2026-02-15 to 2026-02-17). See `docs/stories/story-037-production-deployment.md` for the full decision log including platform evaluation (Fly.io vs Dreamhost), security hardening, and smoke test results.
