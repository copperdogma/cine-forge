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

### Backend Infrastructure (Python)
- [x] Add `fpdf2` dependency to `pyproject.toml`
- [x] Create `src/cine_forge/export/` module
- [x] Implement `MarkdownExporter` class (ports logic from UI prototype, supports all entity types)
- [x] Implement `PDFExporter` class using `fpdf2` (supports Project Report and Call Sheet layouts)
- [x] **Verification:** Write script `scripts/verify_backend_export.py` to generate files from `lc-2` and manually verify contents.

### API Layer
- [x] Create `src/cine_forge/api/routers/export.py`
- [x] Implement `GET /api/projects/{id}/export/markdown` endpoint
- [x] Implement `GET /api/projects/{id}/export/pdf` endpoint
- [x] Wire router into `src/cine_forge/api/main.py` (actually `app.py`)

### CLI Layer (Headless Operation)
- [x] Implement `python -m cine_forge export` command in driver/CLI
- [x] Supports arguments: `--project`, `--format`, `--scope`, `--out`

### UI Refactor
- [x] Update `ExportModal.tsx` to use API endpoints for download/copy
- [x] Delete legacy `ui/src/lib/export/` directory (cleanup)

### Refinements (Round 2)
- [x] **Granular Selection:** For "Project" scope, allow selecting specific components to export (Script, Scenes, Characters, Locations, Props). Default to All.
- [x] **Check All/None:** Provide convenience controls for selection.
- [x] **Script-Only Export:** Add a dedicated, top-level option or ensure it's easily selectable (e.g., just "Script" checked) for exporting the raw screenplay content.
- [x] **Backend Support:** Update API to accept a list of included components (e.g., `?include=script,scenes,characters`).

### Screenplay Formats (Round 3)
- [x] **Research:** Identify open-source libraries for Fountain/Screenplay formatting.
- [x] **Fountain Export:** Implement `.fountain` file download.
- [x] **Markdown (Fountain):** Ensure Markdown script export complies with Fountain syntax.
- [x] **Standard PDF Screenplay:**
    - [x] Debug `FPDFException` (horizontal space error).
    - [x] Set industry-standard margins (1.5" left, 1" top/bottom/right).
    - [x] Implement precise indents for: Action (0"), Character (2.0"), Parenthetical (1.5"), Dialogue (1.0"), Transition (4.0").
    - [x] Add page numbering in the top-right corner.
- [x] **Standard DOCX Screenplay:**
    - [x] Implement `python-docx` renderer with matching indents and Courier font.
    - [x] Ensure proper spacing between elements (e.g., space before headings).

### PDF Export Improvement
- [x] **Fix Project Report PDF:**
    - [x] Redesign Layout: Move from basic tables to a structured "Record" format.
    - [x] Sections: Clearly separated sections for Scenes, Characters (with traits/evidence), and Locations.
    - [x] Styling: Use bold headers, subtle backgrounds for entity names, and readable line spacing.
- [x] **Granular Selection Support:**
    - [x] Update PDF Generator to respect the `include` list (only generate requested sections).

## Acceptance Criteria

- [x] **Headless:** User/AI can export any artifact format via CLI without launching the UI.
- [x] **API-Driven:** UI delegates all generation to the backend.
- [x] **Content Parity:** Exports contain full enriched data (evidence, traits, narrative roles, etc.) as verified in the UI prototype.
- [x] **Formats:** Markdown (Project, Entity, List) and PDF (Report, Call Sheet) are supported.
- [x] **Manual QA:** Output files from `lc-2` have been manually inspected by the implementer and confirmed correct.

## AI Considerations

- **Call sheet generation** could benefit from LLM assistance for grouping scenes by shooting day (proximity heuristic vs. true scheduling). Start with a deterministic grouping (by location), add AI scheduling later.
- **One-sheet generation** could use LLM to write the logline/pitch summary if one doesn't exist in project config. The project_config artifact already has genre, themes, and tone.

## Files to Modify

- `pyproject.toml` — add `fpdf2`
- `src/cine_forge/export/*.py` — [NEW] export logic
- `src/cine_forge/api/routers/export.py` — [NEW] API endpoints
- `src/cine_forge/driver/cli.py` (or similar) — add export command
- `ui/src/components/ExportModal.tsx` — update to fetch from API
- `ui/src/lib/export/` — DELETE

## Tenet Verification

- [x] Immutability: Export is read-only, doesn't modify artifacts
- [x] Lineage: N/A
- [x] Explanation: N/A
- [x] Cost transparency: N/A (no LLM calls in initial version)
- [x] Human control: ✅ User controls what to export and in what format
- [x] QA: Visual verification of exported documents

## Work Log

2026-02-21 14:00 — Implemented comprehensive export system (UI-Only).
- *Superseded by backend requirement.*

2026-02-21 14:10 — Fixed UI build errors.
- *Superseded by backend requirement.*

2026-02-21 14:25 — Refined export UX and fixed bugs based on user feedback.
- *Superseded by backend requirement.*

2026-02-21 14:40 — Pivoting to Backend-First Architecture.
- User mandate: "Headless Operation". AI must be able to export without UI.
- Plan: Port Markdown/PDF logic to Python (`fpdf2`), expose via API, consume in UI.

2026-02-21 15:10 — Implemented Backend Export & CLI.
- Added `fpdf2` dependency.
- Created `src/cine_forge/export/` with `MarkdownExporter` and `PDFGenerator`.
- Verified logic with `scripts/verify_backend_export.py` (manual inspection passed).
- Created `src/cine_forge/api/routers/export.py` with endpoints for MD and PDF.
- Created `src/cine_forge/cli.py` and `__main__.py` to support `cine_forge run` and `cine_forge export` commands.
- Updated `ui/src/components/ExportModal.tsx` to use backend endpoints.
- Deleted legacy client-side export code.
- Verified CLI export with `python -m cine_forge export ...`.

2026-02-21 15:40 — Completed Round 2 Refinements (Granular Selection).
- Updated `ExportModal` to support granular component selection (Script, Scenes, Characters, etc.).
- Updated API (`/api/projects/{id}/export/markdown`) to accept `include` list.
- Updated `MarkdownExporter` to respect `include` list and support raw script export.
- Verified via UI build.

2026-02-21 16:30 — Completed Round 3 (Professional Formats & PDF Overhaul).
- **Standard Screenplay Export**: Implemented precise formatting for PDF and DOCX (Courier 12pt, industry indents for Character/Dialogue/Action/etc.).
- **PDF Overhaul**: Redesigned the Project Report PDF to be readable and professional (Record-based instead of basic tables).
- **Bug Fix**: Debugged and resolved `FPDFException` (horizontal space error) by forcing X-position resets after `multi_cell` calls.
- **Fountain Export**: Added dedicated `.fountain` download.
- **Verification**: Verified all formats via `scripts/verify_v3_exports.py` against real `lc-2` data.
