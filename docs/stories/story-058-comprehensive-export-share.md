# Story 058 — Comprehensive Export & Share

**Phase**: 2.5 — UI
**Priority**: High
**Status**: To Do
**Created**: 2026-02-20
**Depends on**: Story 043 (Entity-First Navigation — Done)
**Requested by**: Gill (user testing Liberty & Church screenplay)

## Goal

Give users a unified way to export project data in multiple formats for sharing with collaborators, agents, producers, and crew. A single "Export" or "Share" button reveals the full range of options — from copying a single character profile to generating a production-ready call sheet PDF.

## Context

Source: Real user feedback (actor testing her own screenplay). Quotes:
- *"I would love a way to easily export all of this on to one sheet so that it can be copy and pasted with ease."*
- *"I wonder if it could handle creating day sheets for cast and crew if locations were added in?"*
- *"I feel like I could just hand this in to any literary agent and be like, here you go."*

She attached a [real industry call sheet](file:///Users/cam/Documents/Projects/cine-forge/input/CALL%20SHEET_DAY4_TSOT.pdf) as a reference for the day sheet format.

## Scope

### In Scope

**Export Granularity:**
- Export **everything** — full project dump (all scenes, characters, locations, props, relationships)
- Export **by type** — all characters, all scenes, all locations, all props
- Export **single entity** — one specific character, scene, etc.
- Export **custom selection** — pick specific entities to include

**Output Formats:**
- **Markdown** → clipboard (immediate, easy paste into docs/email/chat)
- **Markdown** → file download (.md)
- **PDF** download — formatted, professional-looking document
- **Industry-Standard Formats** (future-ready, can start with templates):
  - One-sheet / pitch sheet (project summary, logline, cast, tone)
  - Call sheet / day sheet (scenes grouped by location/day, cast required per scene)

**UI Pattern:**
- Single "Export" button (accessible from list pages, detail pages, and project overview)
- Dropdown/modal with format and scope selection
- Complexity hidden behind a clean interface

### Out of Scope

- Real scheduling/production planning (grouping scenes by shooting day is a display-time heuristic, not a full scheduler)
- FDX/Final Draft re-export
- Sharing via URL (public links, access control)
- Real-time collaboration on exports
- Print stylesheets (PDF covers this)

## Design Direction

### Export Button Placement

| Context | Button | Default |
|---------|--------|---------|
| Entity detail page | Export icon in header | Export this entity as markdown |
| Entity list page | Export icon in toolbar | Export all entities of this type |
| Project overview/sidebar | Export button | Export everything |

### Export Modal

```
┌─────────────────────────────────────┐
│  Export Project Data                 │
│                                     │
│  What to export:                    │
│  ○ Everything                       │
│  ○ Scenes (13)                      │
│  ○ Characters (8)                   │
│  ○ Locations (6)                    │
│  ○ Props (4)                        │
│  ○ Custom selection...              │
│                                     │
│  Format:                            │
│  ○ Markdown (clipboard)             │
│  ○ Markdown (download)              │
│  ○ PDF                              │
│  ○ One-Sheet                        │
│  ○ Call Sheet                       │
│                                     │
│  [Cancel]              [Export]      │
└─────────────────────────────────────┘
```

### Markdown Format

Clean, hierarchical markdown with headers, entity details, and cross-references formatted as readable text. Should look good when pasted into Google Docs, Notion, email, or Claude.

### PDF Format

Professional layout with:
- Project title + metadata header
- Table of contents
- Entity sections with consistent formatting
- Page numbers, clean typography

### Call Sheet Format

Based on industry standard (reference PDF on file):
- Production name, date, crew contacts
- Scene list grouped by location
- Cast required per scene with character names
- Special requirements notes

## Tasks

### Core Export Infrastructure
- [x] Design export data model — what data structure feeds all format renderers
- [x] Create `useExportData` hook to assemble artifact data for export
- [x] Create `ExportModal` component with scope + format selection
- [x] Wire Export button into entity detail pages, list pages, and sidebar

### Markdown Export
- [x] Build markdown renderer for each entity type (scene, character, location, prop)
- [x] Build project-level markdown renderer (combines all entities)
- [x] Implement clipboard copy with toast confirmation
- [x] Implement .md file download

### PDF Export
- [x] Research client-side PDF generation (likely `react-pdf` or `jspdf` + layout templates)
- [x] Create PDF templates for project export and per-type export
- [x] Implement PDF download

### Industry Formats
- [x] Define one-sheet template (project summary, logline, cast, genre, tone)
- [x] Define call sheet template (based on reference PDF)
- [x] Generate call sheet from scene + location + character data

### Polish
- [x] Loading state during PDF generation
- [x] Success toast with "Open file" action
- [x] Keyboard shortcut (Ctrl/Cmd+E) to open export modal

## Acceptance Criteria

- [x] User can export a single entity as markdown to clipboard from its detail page
- [x] User can export all entities of a type (e.g., all characters) as markdown
- [x] User can export the entire project as a markdown document
- [x] User can download a formatted PDF of the project
- [x] Export modal is accessible from entity detail pages, list pages, and project level
- [x] Call sheet export generates a recognizable industry-format document
- [x] One-sheet export generates a pitch-ready summary

## AI Considerations

- **Call sheet generation** could benefit from LLM assistance for grouping scenes by shooting day (proximity heuristic vs. true scheduling). Start with a deterministic grouping (by location), add AI scheduling later.
- **One-sheet generation** could use LLM to write the logline/pitch summary if one doesn't exist in project config. The project_config artifact already has genre, themes, and tone.

## Files to Modify

- `ui/src/components/ExportModal.tsx` — [NEW] main export UI
- `ui/src/lib/export/` — [NEW] export renderers (markdown, pdf, call-sheet, one-sheet)
- `ui/src/lib/hooks.ts` — add `useExportData` hook
- `ui/src/pages/EntityDetailPage.tsx` — add export button
- `ui/src/pages/ScenesList.tsx` — add export button to toolbar
- `ui/src/pages/CharactersList.tsx` — add export button to toolbar
- `ui/src/pages/LocationsList.tsx` — add export button to toolbar
- `ui/src/pages/PropsList.tsx` — add export button to toolbar

## Tenet Verification

- [x] Immutability: Export is read-only, doesn't modify artifacts
- [x] Lineage: N/A
- [x] Explanation: N/A
- [x] Cost transparency: N/A (no LLM calls in initial version)
- [x] Human control: ✅ User controls what to export and in what format
- [x] QA: Visual verification of exported documents

## Work Log

2026-02-21 14:00 — Implemented comprehensive export system.
- Created `ui/src/lib/export/` directory with `types.ts`, `markdown.ts`, and `pdf.ts`.
- Implemented `useExportData` hook in `ui/src/lib/hooks.ts` to aggregate project data.
- Created `ExportModal` component to handle scope (everything, scene, character, etc.) and format (markdown, PDF, call sheet).
- Integrated `jspdf` and `jspdf-autotable` for client-side PDF generation.
- Implemented Markdown generation logic for all entity types and full project.
- Implemented PDF generation with support for Call Sheets (grouping scenes by location).
- Wired `ExportModal` into `EntityDetailPage`, `ScenesList`, `CharactersList`, `LocationsList`, `PropsList`, and `ProjectHome` (FreshImportView).
- Verified with linting.
