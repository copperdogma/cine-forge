# Story 037 — Production Deployment to cineforge.copper-dog.com

**Status**: Done
**Created**: 2026-02-15
**Phase**: Cross-Cutting
**Priority**: High
**Spec Refs**: N/A (operational)
**Depends On**: 011d (Operator Console build)

## Goal

Deploy CineForge (FastAPI backend + React frontend) to a public URL at `cineforge.copper-dog.com` so the operator (Cam) and one other user (sister) can access it. No auth required. AI must be able to manage all deployments and operations via CLI.

## Context

- App: FastAPI backend (API-only) + React 19 frontend (Vite build)
- Data: All filesystem-based (JSON artifacts, no database)
- Users: 2 (Cam + sister), no auth needed
- Domain: copper-dog.com hosted on Dreamhost
- Available platforms: Dreamhost (existing account), Fly.io (existing account)
- Key constraint: AI auditability — all operations must be doable via CLI

## Acceptance Criteria

- [x] Deployment platform chosen with documented rationale
- [x] Dockerfile builds and runs the full app (backend + frontend)
- [x] App is accessible at `https://cineforge.copper-dog.com`
- [x] SSL/TLS working (HTTPS) — Let's Encrypt issued (RSA + ECDSA)
- [x] Persistent storage for project data survives deploys
- [x] AI can deploy updates via CLI (`fly deploy` or equivalent)
- [x] User action checklist documented (DNS, auth, etc.)
- [x] Frontend loads and can communicate with backend API
- [x] File upload and artifact storage works end-to-end (smoke test: upload → pipeline → artifacts → AI chat)

## Out of Scope

- Authentication / authorization (private use, 2 users)
- CI/CD pipeline (manual deploys via AI are fine)
- Multi-region / high availability
- Database migration (no database)
- Monitoring / alerting infrastructure

## Tasks

### Phase 1 — Platform Decision
- [x] Research Fly.io capabilities (volumes, custom domains, CLI, pricing)
- [x] Research Dreamhost capabilities (VPS, Python support, SSH, containers)
- [x] Evaluate against requirements (filesystem storage, AI CLI access, custom domain)
- [x] Document decision with rationale

**Decision: Fly.io (containerized) + Dreamhost DNS**

Rationale:
- Dreamhost VPS has no root/sudo — can't install Docker or manage systemd. Dead end.
- Dreamhost DreamCompute works but requires full DevOps (managing OS, certbot, etc.).
- Fly.io is CLI-first — every operation is a traceable `flyctl` command. Perfect for AI.
- `fly deploy` builds and ships from Dockerfile. Persistent volumes at $0.15/GB/mo.
- Custom domains with automatic SSL. ~$3-5/month total.
- Dreamhost handles DNS only: CNAME `cineforge` → `cineforge-app.fly.dev`.

### Phase 2 — User Action Checklist
- [x] Identify all steps requiring human action (DNS, auth, billing)
- [x] Write detailed step-by-step instructions for user
- [x] User completes manual steps (flyctl install + auth; DNS handled via Cloudflare API)

**What YOU (Cam) need to do** — 4 steps, ~10 minutes total:

#### Step 1: Install flyctl CLI (if not already installed)
```bash
brew install flyctl
```
Or: `curl -L https://fly.io/install.sh | sh`

#### Step 2: Authenticate with Fly.io
```bash
fly auth login
```
This opens a browser. Log in with your Fly.io account. AI cannot do this step — it requires your browser session.

If your Fly.io account doesn't have a payment method, add one at https://fly.io/dashboard (needed since free tier was discontinued — cost will be ~$3-5/month).

#### Step 3: Add DNS CNAME on Dreamhost
1. Log in to your Dreamhost panel: https://panel.dreamhost.com
2. Go to **Manage Websites** → find `copper-dog.com` → **DNS**
3. Click **Add Record**
4. Type: **CNAME**
5. Host: `cineforge`
6. Points to: `cineforge-app.fly.dev` (we'll confirm this after `fly launch`)
7. Save

#### Step 4: Add ACME challenge CNAME (for SSL)
After AI runs `fly certs add`, it will output an `_acme-challenge` CNAME value. Add this on Dreamhost:
1. Same DNS panel as above
2. Type: **CNAME**
3. Host: `_acme-challenge.cineforge`
4. Points to: (value AI will provide after `fly certs add`)
5. Save

**After these 4 steps, AI handles everything else.**

### Phase 3 — Build & Deploy
- [x] Modify FastAPI to serve frontend static files in production
- [x] Create production configuration (env vars, CORS, paths)
- [x] Create Dockerfile (multi-stage: Node build + Python runtime)
- [x] Create .dockerignore
- [x] Create fly.toml
- [x] Run `fly apps create cineforge-app` to create app
- [x] Create persistent volume (1GB, ord region)
- [x] Set ANTHROPIC_API_KEY secret
- [x] Deploy to Fly.io (via `fly deploy --depot=false`)
- [x] Configure custom domain + SSL (`fly certs add`)
- [x] Add DNS CNAME records via Cloudflare API (not Dreamhost — Cloudflare controls nameservers)
- [x] Verify end-to-end functionality at public URL

## Deployment Reference

### Quick Commands
```bash
# Deploy updates
fly deploy --depot=false --yes

# View logs
fly logs -a cineforge-app

# Check status
fly status -a cineforge-app

# SSH into running machine
fly ssh console -a cineforge-app

# Set secrets
fly secrets set KEY=VALUE -a cineforge-app

# View volumes
fly volumes list -a cineforge-app
```

### Architecture
- **App**: `cineforge-app` on Fly.io (personal org, ord region)
- **URL**: https://cineforge-app.fly.dev/ (+ cineforge.copper-dog.com pending DNS)
- **Volume**: `cineforge_data` 1GB mounted at `/app/output`
- **Image**: Multi-stage Docker (Node 24 + Python 3.12-slim), ~168MB
- **Secrets**: `ANTHROPIC_API_KEY`
- **Cost**: ~$3-5/month (shared-cpu-1x, 512MB, 1GB volume, auto-stop)

### Notes

- Depot builder has intermittent 401 registry errors — use `--depot=false` for reliability
- Volume persists project data across deploys; configs/recipes are baked into image
- `PYTHONPATH=/app/src` — workspace_root resolves to `/app` automatically
- `CINEFORGE_STATIC_DIR=/app/static` — frontend build served by FastAPI SPA catch-all
- Auto-stop enabled: machine stops when idle, starts on first request (~5-10s cold start)

## Work Log

20260215-1800 — Phase 1 complete: Platform decision
- Researched Fly.io and Dreamhost capabilities in depth
- Decision: Fly.io (containerized) + Dreamhost DNS only
- Dreamhost VPS lacks root/sudo, can't run Docker — eliminates it as app host
- Fly.io is CLI-first (perfect for AI), ~$3-5/mo, auto SSL, persistent volumes
- Phase 2 user action checklist written (4 steps, ~10 min)
- Next: User completes manual steps, then AI builds Phase 3

20260217-0900 — Phase 3 complete: App deployed to Fly.io
- Modified `src/cine_forge/api/app.py`: SPA catch-all route, CORS for production domain
- Created `Dockerfile`: multi-stage (Node 24 frontend build → Python 3.12-slim runtime)
- Created `fly.toml`: cineforge-app, ord region, 512MB shared-cpu, auto-stop, health checks
- Created `.dockerignore`: excludes .git, output, tests, docs, node_modules
- App: `cineforge-app` on Fly.io (personal org)
- Volume: `cineforge_data` 1GB in ord region (vol_re8qj9w5w55j09lr)
- Secret: ANTHROPIC_API_KEY set for AI chat feature
- Depot builder had registry 401 issue; used legacy Docker builder (`--depot=false`)
- Deploy successful: https://cineforge-app.fly.dev/
- Verified: `/api/health` → ok, frontend HTML 200, `/api/recipes` → 7 recipes
- Custom domain cert added: `fly certs add cineforge.copper-dog.com`
- DNS CNAME values provided to user for Dreamhost:
  - `cineforge` → `cineforge-app.fly.dev`
  - `_acme-challenge.cineforge` → `cineforge.copper-dog.com.53l6r9n.flydns.net`
- Pending: User adds DNS records on Dreamhost, then verify custom domain works

20260217-0930 — DNS and SSL complete: Custom domain live
- Discovered copper-dog.com nameservers point to Cloudflare (not Dreamhost)
- Used Cloudflare API to add CNAME records (Zone ID: 372acf29f0a6f95c35e9f7ea94aa7efa)
  - `cineforge.copper-dog.com` → `cineforge-app.fly.dev` (record ID: e8e23b9503474fead07688ec0428505d)
  - `_acme-challenge.cineforge.copper-dog.com` → `cineforge.copper-dog.com.53l6r9n.flydns.net` (record ID: bf044ecdfd4b7d6e88b935c6d3389155)
- SSL cert issued by Let's Encrypt (RSA + ECDSA) within 30 seconds
- Verified: `https://cineforge.copper-dog.com/api/health` → 200, `/api/recipes` → 7 recipes
- Added Production Deployment section to AGENTS.md for future AI sessions
- **Story 037 substantially complete** — all infra done, custom domain live with SSL

20260217-1000 — Smoke test + security hardening + redeployment
- Full production smoke test: created project, uploaded 840B screenplay, ran 4-stage MVP pipeline ($0.0065), AI chat streaming worked
- Security review found 3 issues, all fixed:
  - Critical: Path traversal in SPA catch-all → added `is_relative_to()` check
  - High: Docker running as root → added non-root `cineforge` user (uid 1001)
  - High: `.dockerignore` missing `.env*`, `*.key`, `*.pem` → added
- Redeployed with fixes: `fly deploy --depot=false --yes` → image 172MB, health check passed
- Path traversal verified blocked on production (returns index.html, not file contents)
- 156 unit tests pass, ruff lint clean
- **Story 037 complete** — all 9 acceptance criteria met, all phases done
