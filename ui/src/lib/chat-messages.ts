// State-driven chat message generator.
// Produces initial messages for each project state with appropriate action buttons.

import type { ChatMessage, ProjectState, ProjectSummary } from './types'

let nextId = 0
function msgId(): string {
  return `msg_${Date.now()}_${nextId++}`
}

export function getWelcomeMessages(
  projectState: ProjectState,
  project?: ProjectSummary,
): ChatMessage[] {
  const now = Date.now()

  switch (projectState) {
    case 'empty':
      return [
        {
          id: msgId(),
          type: 'ai_welcome',
          content: 'Welcome to CineForge! Upload a screenplay to get started.',
          timestamp: now,
          actions: [
            { id: 'upload', label: 'Upload Screenplay', variant: 'default', route: '/new' },
          ],
        },
      ]

    case 'fresh_import':
      return [
        {
          id: msgId(),
          type: 'ai_welcome',
          content: `Your screenplay is loaded${project?.input_files?.[0] ? ` — *${cleanFilename(project.input_files[0])}*` : ''}. Ready to bring your story to life?`,
          timestamp: now,
        },
        {
          id: msgId(),
          type: 'ai_suggestion',
          content: "I'll break your screenplay into individual scenes and identify all the characters and locations. Takes about a minute.",
          timestamp: now + 1,
          actions: [
            { id: 'start_analysis', label: 'Break Down Script', variant: 'default' },
            { id: 'just_read', label: 'Just Let Me Read', variant: 'outline' },
          ],
          needsAction: true,
        },
      ]

    case 'processing':
      return [
        {
          id: msgId(),
          type: 'ai_status',
          content: 'Reading your screenplay and extracting story elements...',
          timestamp: now,
        },
      ]

    case 'analyzed': {
      const artifactCount = project?.artifact_groups ?? 0
      return [
        {
          id: msgId(),
          type: 'ai_welcome',
          content: `Your screenplay has been broken down — ${artifactCount} story elements found.`,
          timestamp: now,
        },
        {
          id: msgId(),
          type: 'ai_suggestion',
          content: 'Ready for a deep breakdown? I\'ll extract detailed character profiles, location guides, and map every relationship in your story.',
          timestamp: now + 1,
          actions: [
            { id: 'go_deeper', label: 'Deep Breakdown', variant: 'default' },
            { id: 'review', label: 'Browse Results', variant: 'outline', route: 'artifacts' },
          ],
          needsAction: true,
        },
      ]
    }

    case 'complete':
      return [
        {
          id: msgId(),
          type: 'ai_welcome',
          content: 'Your story world is built. Explore your scenes, characters, and creative bibles.',
          timestamp: now,
        },
        {
          id: msgId(),
          type: 'ai_suggestion',
          content: "Here's what you can do next:",
          timestamp: now + 1,
          actions: [
            { id: 'scenes', label: 'Explore Scenes', variant: 'default', route: 'artifacts' },
            { id: 'inbox', label: 'Review Inbox', variant: 'secondary', route: 'inbox' },
            { id: 'go_deeper', label: 'Re-run Deep Breakdown', variant: 'outline' },
          ],
        },
      ]

    default:
      return []
  }
}

function cleanFilename(name: string): string {
  return name
    .replace(/\.(pdf|fdx|fountain|txt|md|docx)$/i, '')
    .replace(/^\d{10,15}[_-]/, '')
    .replace(/[_-]/g, ' ')
    .replace(/\s+No\s+ID\s*$/i, '')
    .replace(/\s+/g, ' ')
    .trim()
}

// --- Stage progress descriptions ---

export const STAGE_DESCRIPTIONS: Record<string, { start: string; done: string }> = {
  ingest: {
    start: 'Reading your document...',
    done: 'Document loaded successfully.',
  },
  normalize: {
    start: 'Converting to standard screenplay format...',
    done: 'Screenplay format standardized.',
  },
  classify: {
    start: 'Classifying your document type — screenplay, treatment, or prose...',
    done: 'Document classified.',
  },
  extract_scenes: {
    start: 'Finding scene boundaries and structure...',
    done: 'Scenes identified.',
  },
  entity_discovery: {
    start: 'Discovering characters, locations, and props across your script...',
    done: 'Entities discovered.',
  },
  character_bible: {
    start: 'Writing character bibles — backstories, motivations, and arcs...',
    done: 'Character bibles written.',
  },
  location_bible: {
    start: 'Writing location bibles — atmosphere, visual identity, and story role...',
    done: 'Location bibles written.',
  },
  prop_bible: {
    start: 'Writing prop bibles — significance, symbolism, and plot function...',
    done: 'Prop bibles written.',
  },
  qa: {
    start: 'Running quality checks on produced artifacts...',
    done: 'Quality checks passed.',
  },
}

export function humanizeStageName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function getStageStartMessage(stageName: string): string {
  return STAGE_DESCRIPTIONS[stageName]?.start ?? `Working on ${humanizeStageName(stageName)}...`
}

export function getStageCompleteMessage(stageName: string): string {
  return STAGE_DESCRIPTIONS[stageName]?.done ?? `${humanizeStageName(stageName)} finished.`
}
