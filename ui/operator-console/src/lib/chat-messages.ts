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
            { id: 'start_analysis', label: 'Start Analysis', variant: 'default', route: 'run' },
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
            { id: 'go_deeper', label: 'Go Deeper', variant: 'secondary', route: 'run' },
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
