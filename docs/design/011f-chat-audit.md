# 011f Chat Behavior Audit — 011e Baseline

**Date**: 2026-02-16
**Story**: 011f (Conversational AI Chat)
**Purpose**: Complete behavior map of 011e's hardcoded chat system. Feature-parity baseline for AI replacement.

---

## Overview

The 011e chat panel is **not a real chatbot**. It's a state-machine that generates context-aware messages with action buttons based on project state. The text input is disabled. Users interact only by clicking buttons.

---

## Message Types

**Definition**: `ui/operator-console/src/lib/types.ts:150`

| Type | Icon | Purpose |
|------|------|---------|
| `ai_welcome` | Sparkles (primary) | Welcome message or status update |
| `ai_suggestion` | MessageSquare (primary) | Actionable suggestion with buttons |
| `ai_status` | Loader2 (spinning, muted) | In-progress pipeline status |
| `ai_status_done` | CheckCircle2 (primary) | Completed pipeline status |
| `user_action` | CheckCircle2 (emerald) | User confirmed an action |

### Message Schema

```typescript
type ChatMessage = {
  id: string              // msg_{timestamp}_{counter}
  type: ChatMessageType
  content: string         // Supports *emphasis* markdown
  timestamp: number
  actions?: ChatAction[]  // Optional buttons
  needsAction?: boolean   // Buttons hide after user responds
}

type ChatAction = {
  id: string              // Determines behavior
  label: string           // Button text
  variant: 'default' | 'secondary' | 'outline'
  route?: string          // Navigation target
}
```

---

## Project State Machine

**Definition**: `ui/operator-console/src/lib/hooks.ts:107-130`

```
empty → fresh_import → processing → analyzed → processing → complete
```

| State | Condition | Welcome Messages |
|-------|-----------|------------------|
| `empty` | No inputs uploaded | "Upload a screenplay to get started." + Upload button |
| `fresh_import` | Has inputs, no runs/artifacts | Script loaded + "Start Analysis" suggestion |
| `processing` | Active run (running/pending) | "Reading your screenplay..." spinner |
| `analyzed` | Has artifacts, no creative artifacts | Analysis complete + "Go Deeper" suggestion |
| `complete` | Has bible_manifest or entity_graph | Story world complete + navigation links |

---

## Suggestion Flow

**Definition**: `ui/operator-console/src/lib/chat-messages.ts:11-108`

### Fresh Import
- "I'll read through the screenplay and identify all the scenes, characters, and locations."
- Buttons: **Start Analysis** (starts mvp_ingest) | **Just Let Me Read** (navigation only)

### Analyzed (after MVP ingest)
- "You can review what I found, or I can go deeper — building character bibles, creative world details, and visual style guides."
- Buttons: **Review Scenes** (nav to artifacts) | **Go Deeper** (starts world_building)

### Complete (after world building)
- "Here's what you can do next:"
- Buttons: **Scenes** (nav to artifacts) | **Inbox** (nav to inbox)

---

## Action Button Behaviors

**Definition**: `ui/operator-console/src/components/ChatPanel.tsx:14-18, 37-139`

### Run-triggering actions

| Action ID | Recipe | Behavior |
|-----------|--------|----------|
| `start_analysis` | `mvp_ingest` | Add user_action msg → startRun → add ai_status → enable polling |
| `go_deeper` | `world_building` | Same flow with world_building recipe |

Execution flow:
1. Add `user_action` message with button label
2. Call `startRun.mutateAsync()` with project_id, latest input, `claude-sonnet-4-5-20250929`, recipe_id, `accept_config: true`
3. Set `activeRunId` in store (enables 2s polling)
4. Add `ai_status` message with "View Run Details" action
5. On error: add `ai_suggestion` with error text + "Configure Manually" action

### Navigation actions

| Action ID | Route |
|-----------|-------|
| `upload` | `/new` (absolute) |
| `review` | `artifacts` (relative to project) |
| `scenes` | `artifacts` (relative) |
| `inbox` | `inbox` (relative) |
| `view_run_details` | `runs/{run_id}` (relative) |
| `manual_pipeline` | `run` (relative) |

### Button visibility

Buttons with `needsAction: true` are hidden once a subsequent `user_action` message exists. Buttons without `needsAction` are always visible.

---

## Run Progress Messages

**Definition**: `ui/operator-console/src/lib/use-run-progress.ts`

Polls `useRunState(activeRunId)` every 2 seconds while a run is active.

### Events → Messages

| Event | Message Type | Content |
|-------|-------------|---------|
| Run starts | `ai_status` | "Analysis started — reading your screenplay now..." |
| Stage starts running | `ai_status` | Stage-specific text (see below) |
| Stage completes | `ai_status_done` | Previous spinner → checkmark + completion text |
| Stage fails | `ai_suggestion` | Error text + "View Details" button |
| Run completes (success) | `ai_status_done` | Summary with artifact counts |
| Run completes (mvp_ingest) | `ai_suggestion` | "Go Deeper" suggestion |

### Stage Descriptions

**Definition**: `ui/operator-console/src/lib/chat-messages.ts:120-181`

| Stage | Start | Done |
|-------|-------|------|
| `ingest` | "Reading your document..." | "Document loaded successfully." |
| `normalize` | "Converting to standard screenplay format..." | "Screenplay format standardized." |
| `classify` | "Classifying your document type..." | "Document classified." |
| `extract_scenes` | "Finding scene boundaries and structure..." | "Scenes identified." |
| `scene_breakdown` | "Breaking down scenes — identifying characters, locations, and action..." | "Scene breakdown complete." |
| `extract` | "Extracting story elements from your screenplay..." | "Extraction complete." |
| `entity_graph` | "Building relationships between characters, locations, and story elements..." | "Story graph built." |
| `world_overview` | "Building your story world — themes, tone, and setting..." | "World overview created." |
| `character_bibles` | "Writing character bibles — backstories, motivations, and arcs..." | "Character bibles written." |
| `location_bibles` | "Developing location details, atmosphere, and visual identity..." | "Location bibles written." |
| `qa` | "Running quality checks on produced artifacts..." | "Quality checks passed." |

Fallback: `humanizeStageName(name)` converts snake_case → Title Case.

---

## Chat Persistence

### Backend

**Files**: `src/cine_forge/api/service.py:615-652`, `src/cine_forge/api/app.py:154-163`

- Storage: `{project_dir}/chat.jsonl` (one JSON line per message)
- `GET /api/projects/{project_id}/chat` → list all messages
- `POST /api/projects/{project_id}/chat` → append (idempotent by `id`)

### Frontend Store

**File**: `ui/operator-console/src/lib/chat-store.ts`

```typescript
state = {
  messages: Record<projectId, ChatMessage[]>
  loaded: Record<projectId, boolean>
  activeRunId: Record<projectId, string | null>
}
```

Operations:
- `loadMessages` — bulk load from backend (replaces in-memory)
- `addMessage` — add + persist to backend (fire-and-forget)
- `updateMessageType` — in-memory only (spinner → checkmark)
- `setActiveRun` / `clearActiveRun` — polling control

Migration on load: any `ai_status` from JSONL → `ai_status_done` (no live polling on cold load).

### Loading Flow

**File**: `ui/operator-console/src/lib/hooks.ts:363-401` (`useChatLoader`)

1. Called from AppShell on every page (not just Home)
2. If backend has messages → load them (persisted history)
3. If no backend messages → generate welcome messages from project state → persist
4. On error → generate client-side only (no persistence)

---

## UI Layout

**File**: `ui/operator-console/src/components/ChatPanel.tsx:180-242`

- Right panel of AppShell, toggled via "Chat" | "Inspector" tabs
- Keyboard shortcut: `Cmd+I`
- ScrollArea with auto-scroll to bottom on new messages
- Disabled text input: "Chat coming in a future update..."
- User messages (`user_action`) right-aligned, AI messages left-aligned

---

## Feature Parity Checklist

The AI replacement must replicate ALL of this before adding new capabilities:

### Messages & State
- [ ] Generate welcome messages based on project state (empty/fresh/processing/analyzed/complete)
- [ ] Track active runs and report stage-by-stage progress
- [ ] Update spinner → checkmark on stage completion
- [ ] Generate completion summaries with artifact counts
- [ ] Suggest next steps based on pipeline completion (mvp_ingest → "Go Deeper")
- [ ] Persist all messages to chat.jsonl (idempotent)
- [ ] Migrate ai_status → ai_status_done on cold load

### Actions & Navigation
- [ ] Support action buttons that start pipeline runs (with recipe selection)
- [ ] Support action buttons that navigate to routes
- [ ] Add user_action messages when user clicks a button
- [ ] Hide needsAction buttons after user responds
- [ ] Handle run start errors with fallback suggestion

### UI Integration
- [ ] Render in right panel (Chat tab)
- [ ] Auto-scroll on new messages
- [ ] Correct icons per message type
- [ ] Markdown emphasis in content
- [ ] Right-align user messages
