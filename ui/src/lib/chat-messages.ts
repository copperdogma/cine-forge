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
          content: "I'll read through the screenplay and identify all the scenes, characters, and locations. This usually takes about a minute.",
          timestamp: now + 1,
          actions: [
            { id: 'start_analysis', label: 'Start Analysis', variant: 'default' },
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
          content: `Your screenplay has been analyzed! I found ${artifactCount} story elements ready to explore.`,
          timestamp: now,
        },
        {
          id: msgId(),
          type: 'ai_suggestion',
          content: 'You can review what I found, or I can go deeper — building character bibles, creative world details, and visual style guides.',
          timestamp: now + 1,
          actions: [
            { id: 'review', label: 'Review Scenes', variant: 'default', route: 'artifacts' },
            { id: 'go_deeper', label: 'Go Deeper', variant: 'secondary' },
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

const STAGE_DESCRIPTIONS: Record<string, { start: string; done: string }> = {
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
  scene_breakdown: {
    start: 'Breaking down scenes — identifying characters, locations, and action in each scene...',
    done: 'Scene breakdown complete.',
  },
  extract: {
    start: 'Extracting story elements from your screenplay...',
    done: 'Extraction complete.',
  },
  entity_graph: {
    start: 'Building relationships between characters, locations, and story elements...',
    done: 'Story graph built.',
  },
  world_overview: {
    start: 'Building your story world — themes, tone, and setting...',
    done: 'World overview created.',
  },
  character_bibles: {
    start: 'Writing character bibles — backstories, motivations, and arcs...',
    done: 'Character bibles written.',
  },
  location_bibles: {
    start: 'Developing location details, atmosphere, and visual identity...',
    done: 'Location bibles written.',
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
