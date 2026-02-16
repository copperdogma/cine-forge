# Story 037 — Production Deployment to cineforge.copper-dog.com

**Status**: In Progress
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

- [ ] Deployment platform chosen with documented rationale
- [ ] Dockerfile builds and runs the full app (backend + frontend)
- [ ] App is accessible at `https://cineforge.copper-dog.com`
- [ ] SSL/TLS working (HTTPS)
- [ ] Persistent storage for project data survives deploys
- [ ] AI can deploy updates via CLI (`fly deploy` or equivalent)
- [ ] User action checklist documented (DNS, auth, etc.)
- [ ] Frontend loads and can communicate with backend API
- [ ] File upload and artifact storage works end-to-end

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
- [ ] User completes manual steps

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
- [ ] Modify FastAPI to serve frontend static files in production
- [ ] Create production configuration (env vars, CORS, paths)
- [ ] Create Dockerfile (multi-stage: Node build + Python runtime)
- [ ] Create .dockerignore
- [ ] Create fly.toml
- [ ] Run `fly launch` to create app
- [ ] Create persistent volume
- [ ] Deploy to Fly.io
- [ ] Configure custom domain + SSL
- [ ] Verify end-to-end functionality at public URL

## Notes

- The app stores everything on the filesystem — persistent volumes are critical
- No database means simpler deployment but volume management is important
- Backend currently doesn't serve static files — needs modification for single-container deploy
- CORS needs updating for production domain

## Work Log

20260215-1800 — Phase 1 complete: Platform decision
- Researched Fly.io and Dreamhost capabilities in depth
- Decision: Fly.io (containerized) + Dreamhost DNS only
- Dreamhost VPS lacks root/sudo, can't run Docker — eliminates it as app host
- Fly.io is CLI-first (perfect for AI), ~$3-5/mo, auto SSL, persistent volumes
- Phase 2 user action checklist written (4 steps, ~10 min)
- Next: User completes manual steps, then AI builds Phase 3
