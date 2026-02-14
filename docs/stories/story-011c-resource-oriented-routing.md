# Story 011c: Resource-oriented Routing

**Status**: Done
**Phase**: Phase 2.5 — UI
**Priority**: Medium

## Context
The current UI uses "Page-based" routing with project identity stored in `localStorage` and entity identity in query strings (e.g., `/run?run_id=...`). This prevents having multiple projects open in different tabs and makes the URLs less intuitive for a professional tool.

## Goal
Transition the Operator Console to a **Resource-oriented (Hierarchical) Routing** pattern where the URL Path defines **Identity** and the Query String defines **View State**.

### Bedrock Mandate
**IMPORTANT**: A future story (011b) involves a complete rebuild of the UI from scratch. Therefore, this story must focus on establishing **bedrock functionality**. The goal is not visual polish, but a robust architectural foundation where the URL is the absolute source of truth for identity. This routing logic should remain solid and reusable even if the entire visual presentation changes.

## Acceptance Criteria

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

## Tasks
- [x] Refactor `App.tsx` to use hierarchical `Routes`.
- [x] Implement `ProjectContext` to manage active project state derived from URL.
- [x] Update `RunPage` to extract `projectId` and `runId` from URL path.
- [x] Update `RunsPage` to extract `projectId` and `runId` from URL path.
- [x] Update `ArtifactsPage` to extract `projectId`, `type`, `entity`, and `version` from URL path.
- [x] Implement automatic redirection from `/:projectId` to `/:projectId/run`.
- [x] Update `ProjectSwitcher` to navigate to the correct resource-based URL on selection.
- [x] Remove `localStorage` project persistence.
- [x] Add breadcrumb component to the layout.

## Work Log

### 20260214-2330 — Implemented Bedrock Hierarchical Routing
- **Result:** Success.
- **Evidence:**
  - URL structure now follows `/:projectId/run/:runId` and `/:projectId/artifacts/...`.
  - `localStorage` dependency for project identity removed.
  - `ProjectContext` provides project metadata to sub-pages.
  - Automatic project metadata fetching for direct URL hits.
  - Functional breadcrumbs added.
  - Verified with `npm run build` (Clean).
- **Next Step:** Proceed to Story 011b (Production UI Rebuild) using this bedrock.

### 20260214-2345 — Final Validation and Handover
- **Result:** Success.
- **Verification:** Completed final validation of all hierarchical routes, breadcrumb behavior, and stateless project switching. Verified that bookmarking/refreshing deep URLs correctly restores the full project and resource context.
