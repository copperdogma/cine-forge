// State-driven chat message generator.
// Produces initial messages for each project state with appropriate action buttons.

import {
  getSceneScopeTargetLabel,
  getSceneWorkNextStepActions,
  getSceneWorkNextStepContent,
} from './constants'
import type { ChatMessage, ProjectState, ProjectSummary } from './types'

const BOOTSTRAP_WELCOME_ID = 'bootstrap_welcome'
const BOOTSTRAP_SUGGESTION_ID = 'bootstrap_suggestion'

const BOOTSTRAP_ACTION_IDS = new Set([
  'upload',
  'start_analysis',
  'just_read',
  'go_deeper',
  'review',
  'scenes',
  'inbox',
])

const LEGACY_BOOTSTRAP_CONTENTS = {
  welcome: [
    'Welcome to CineForge! Upload a screenplay to get started.',
    'Your screenplay is loaded',
    'Your screenplay has been broken down',
    'Your story world is built.',
  ],
  suggestion: [
    "I'll break your screenplay into individual scenes",
    'Ready for a deep breakdown?',
    "Here's what you can do next:",
  ],
  status: [
    'Reading your screenplay and extracting story elements...',
  ],
} as const

function isBootstrapContent(message: ChatMessage): boolean {
  if (message.type === 'ai_welcome') {
    return LEGACY_BOOTSTRAP_CONTENTS.welcome.some(prefix => message.content.startsWith(prefix))
  }
  if (message.type === 'ai_suggestion') {
    return LEGACY_BOOTSTRAP_CONTENTS.suggestion.some(prefix => message.content.startsWith(prefix))
  }
  if (message.type === 'ai_status') {
    return LEGACY_BOOTSTRAP_CONTENTS.status.some(prefix => message.content.startsWith(prefix))
  }
  return false
}

function hasOnlyBootstrapActions(message: ChatMessage): boolean {
  const actions = message.actions ?? []
  return actions.every(action => BOOTSTRAP_ACTION_IDS.has(action.id))
}

function serializeBootstrapShape(message: ChatMessage) {
  return {
    id: message.id,
    type: message.type,
    content: message.content,
    actions: (message.actions ?? []).map(action => ({
      id: action.id,
      label: action.label,
      variant: action.variant,
      route: action.route,
    })),
  }
}

export function isBootstrapChatMessage(message: ChatMessage): boolean {
  if (message.id === BOOTSTRAP_WELCOME_ID || message.id === BOOTSTRAP_SUGGESTION_ID) {
    return true
  }

  if (!isBootstrapContent(message)) {
    return false
  }

  if (
    message.speaker
    || message.model
    || message.streaming
    || message.toolCalls?.length
    || message.route
    || message.pageContext
    || message.injectedContent
    || message.preflightData
    || message.resolvedMessageId
  ) {
    return false
  }

  return hasOnlyBootstrapActions(message)
}

export function hasOnlyBootstrapMessages(messages: ChatMessage[]): boolean {
  return messages.length > 0 && messages.every(isBootstrapChatMessage)
}

export function dropLegacyBootstrapMessages(messages: ChatMessage[]): ChatMessage[] {
  const hasStableBootstrap = messages.some(
    message => message.id === BOOTSTRAP_WELCOME_ID || message.id === BOOTSTRAP_SUGGESTION_ID,
  )
  if (!hasStableBootstrap) {
    return messages
  }

  return messages.filter((message) => {
    if (message.id === BOOTSTRAP_WELCOME_ID || message.id === BOOTSTRAP_SUGGESTION_ID) {
      return true
    }
    return !isBootstrapChatMessage(message)
  })
}

export function areBootstrapMessagesCurrent(
  messages: ChatMessage[],
  projectState: ProjectState,
  project?: ProjectSummary,
): boolean {
  const expected = getWelcomeMessages(projectState, project)
  const actual = dropLegacyBootstrapMessages(messages).filter(isBootstrapChatMessage)
  if (actual.length !== expected.length) {
    return false
  }

  return actual.every((message, index) => {
    const expectedMessage = expected[index]
    return JSON.stringify(serializeBootstrapShape(message)) === JSON.stringify(serializeBootstrapShape(expectedMessage))
  })
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
          id: BOOTSTRAP_WELCOME_ID,
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
          id: BOOTSTRAP_WELCOME_ID,
          type: 'ai_welcome',
          content: `Your screenplay is loaded${project?.input_files?.[0] ? ` — *${cleanFilename(project.input_files[0])}*` : ''}. Ready to bring your story to life?`,
          timestamp: now,
        },
        {
          id: BOOTSTRAP_SUGGESTION_ID,
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
          id: BOOTSTRAP_WELCOME_ID,
          type: 'ai_status',
          content: 'Reading your screenplay and extracting story elements...',
          timestamp: now,
        },
      ]

    case 'analyzed': {
      const artifactCount = project?.artifact_groups ?? 0
      return [
        {
          id: BOOTSTRAP_WELCOME_ID,
          type: 'ai_welcome',
          content: `Your screenplay has been broken down — ${artifactCount} story elements found.`,
          timestamp: now,
        },
        {
          id: BOOTSTRAP_SUGGESTION_ID,
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
          id: BOOTSTRAP_WELCOME_ID,
          type: 'ai_welcome',
          content: 'Your story world is built. CineForge is ready for scene work.',
          timestamp: now,
        },
        {
          id: BOOTSTRAP_SUGGESTION_ID,
          type: 'ai_suggestion',
          content: getSceneWorkNextStepContent(),
          timestamp: now + 1,
          actions: getSceneWorkNextStepActions(),
          needsAction: true,
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
  breakdown_scenes: {
    start: 'Breaking down scene boundaries and structure...',
    done: 'Scene breakdown complete.',
  },
  script_bible: {
    start: 'Analyzing story structure, themes, and narrative arc...',
    done: 'Script bible complete.',
  },
  analyze_scenes: {
    start: 'Analyzing narrative beats, tone, and subtext across scenes...',
    done: 'Scene analysis complete.',
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
  // --- Creative direction concern group stages ---
  intent_mood: {
    start: 'Working on Intent & Mood...',
    done: 'Intent & Mood complete.',
  },
  rhythm_and_flow: {
    start: 'Working on Rhythm & Flow...',
    done: 'Rhythm & Flow direction complete.',
  },
  look_and_feel: {
    start: 'Working on Look & Feel...',
    done: 'Look & Feel direction complete.',
  },
  sound_and_music: {
    start: 'Working on Sound & Music...',
    done: 'Sound & Music direction complete.',
  },
  character_and_performance: {
    start: 'Working on Character & Performance...',
    done: 'Character & Performance direction complete.',
  },
  shot_planning: {
    start: 'Planning coverage and shot lists across your scenes...',
    done: 'Shot planning complete.',
  },
  ai_previz: {
    start: 'Generating low-fidelity AI previz clips for blocking and camera review...',
    done: 'AI previz complete.',
  },
  keyframes: {
    start: 'Deriving lockable start, mid, and end keyframes...',
    done: 'Keyframes complete.',
  },
  render: {
    start: 'Compiling render prompts and generating scene videos...',
    done: 'Scene renders complete.',
  },
  final_output: {
    start: 'Assembling the rendered project cut...',
    done: 'Final output assembly complete.',
  },
}

export function humanizeStageName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function getStageStartMessage(stageName: string, sceneScope?: unknown): string {
  const scopeTarget = getSceneScopeTargetLabel(sceneScope)
  if (stageName === 'shot_planning') {
    return scopeTarget === 'this scene'
      ? 'Planning coverage and shot list for this scene...'
      : 'Planning coverage and shot lists across your scenes...'
  }
  if (stageName === 'storyboards') {
    return scopeTarget === 'this scene'
      ? 'Generating storyboard frames for this scene...'
      : 'Generating storyboard frames across your scenes...'
  }
  if (stageName === 'ai_previz') {
    return scopeTarget === 'this scene'
      ? 'Generating low-fidelity AI previz clip for this scene...'
      : 'Generating low-fidelity AI previz clips for blocking and camera review...'
  }
  return STAGE_DESCRIPTIONS[stageName]?.start ?? `Working on ${humanizeStageName(stageName)}...`
}

export function getStageCompleteMessage(stageName: string): string {
  return STAGE_DESCRIPTIONS[stageName]?.done ?? `${humanizeStageName(stageName)} finished.`
}
