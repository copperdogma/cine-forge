# Story 011c: Resource-oriented Routing

**Status**: To Do
**Phase**: Phase 2.5 — UI
**Priority**: Medium

## Context
The current UI uses "Page-based" routing with project identity stored in `localStorage` and entity identity in query strings (e.g., `/run?run_id=...`). This prevents having multiple projects open in different tabs and makes the URLs less intuitive for a professional tool.

## Objective
Transition the Operator Console to a **Resource-oriented (Hierarchical) Routing** pattern where the URL Path defines **Identity** and the Query String defines **View State**.

## Requirements

### 1. Hierarchical URL Structure
Implement the following route map:
- **Project Selection**: `/` (List recent projects / Project Switcher)
- **New Project**: `/new`
- **Project Dashboard**: `/:projectId` (Redirects to `/:projectId/run`)
- **Run Pipeline**: `/:projectId/run`
- **Run History**: `/:projectId/runs`
- **Specific Run**: `/:projectId/runs/:runId`
- **Artifacts Browser**: `/:projectId/artifacts`
- **Artifact Detail**: `/:projectId/artifacts/:type/:entity/:version`

### 2. Project Scoping
- Move `projectId` from `localStorage` into the URL path.
- Enable opening different CineForge projects in separate browser tabs without state collision.
- The "Projects" toggle should navigate back to `/` or open a modal that changes the base path.

### 3. State vs. Identity
- **Path**: Must contain everything needed to identify the resource (Project, Run, Artifact).
- **Query String**: Use only for UI modifiers (e.g., `?expert=true`, `?filter=char`).

### 4. Breadcrumb Navigation
- Use the hierarchical routes to automatically generate breadcrumbs: `Projects > The Mariner > Runs > run-123`.

## Definition of Done
1. [ ] Navigating to a specific project URL (e.g., `/abc123/run`) automatically activates that project.
2. [ ] Refreshing a specific artifact URL (e.g., `/abc123/artifacts/scene/scene_001/1`) restores the exact view.
3. [ ] Multiple browser tabs can hold different projects open simultaneously.
4. [ ] Standard `localStorage` fallback removed for project identity.
