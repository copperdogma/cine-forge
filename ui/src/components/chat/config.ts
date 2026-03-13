import type { ElementType } from 'react'
import {
  Activity,
  Clapperboard,
  Drama,
  Eye,
  MapPin,
  MessageSquare,
  Package,
  Scissors,
  Sparkles,
  User,
  Users,
  Volume2,
} from 'lucide-react'
import type { InteractionMode } from '@/lib/types'

export type RoleDisplayConfig = {
  name: string
  icon: ElementType
  iconClass: string
  badgeClass: string
  bgClass: string
}

export const ROLE_DISPLAY: Record<string, RoleDisplayConfig> = {
  assistant: {
    name: 'Assistant',
    icon: Sparkles,
    iconClass: 'text-zinc-400',
    badgeClass: 'text-zinc-400',
    bgClass: 'bg-zinc-500/5',
  },
  director: {
    name: 'Director',
    icon: Clapperboard,
    iconClass: 'text-violet-400',
    badgeClass: 'text-violet-400',
    bgClass: 'bg-violet-500/8',
  },
  editorial_architect: {
    name: 'Editorial Architect',
    icon: Scissors,
    iconClass: 'text-pink-400',
    badgeClass: 'text-pink-400',
    bgClass: 'bg-pink-500/8',
  },
  visual_architect: {
    name: 'Visual Architect',
    icon: Eye,
    iconClass: 'text-sky-400',
    badgeClass: 'text-sky-400',
    bgClass: 'bg-sky-500/8',
  },
  sound_designer: {
    name: 'Sound Designer',
    icon: Volume2,
    iconClass: 'text-emerald-400',
    badgeClass: 'text-emerald-400',
    bgClass: 'bg-emerald-500/8',
  },
  story_editor: {
    name: 'Story Editor',
    icon: Drama,
    iconClass: 'text-amber-400',
    badgeClass: 'text-amber-400',
    bgClass: 'bg-amber-500/8',
  },
}

export function getRoleDisplay(
  speaker: string,
): RoleDisplayConfig & { isCharacter?: boolean; characterId?: string } {
  if (speaker.startsWith('char:')) {
    const handle = speaker.slice(5)
    const displayName = handle.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    return {
      name: displayName,
      icon: User,
      iconClass: 'text-amber-200',
      badgeClass: 'text-amber-200',
      bgClass: 'bg-amber-100/8',
      isCharacter: true,
      characterId: handle,
    }
  }

  return ROLE_DISPLAY[speaker] ?? {
    name: speaker.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()),
    icon: MessageSquare,
    iconClass: 'text-zinc-500',
    badgeClass: 'text-zinc-500',
    bgClass: 'bg-zinc-500/5',
  }
}

export const PICKABLE_ROLES = [
  'assistant',
  'director',
  'editorial_architect',
  'visual_architect',
  'sound_designer',
  'story_editor',
] as const

export const MENTION_SHORTCUTS = [
  { id: 'all-creatives', name: 'All Creatives', description: 'Director + all creative roles' },
] as const

export type MentionItem = {
  kind: 'shortcut' | 'role' | 'character'
  id: string
  name: string
  description?: string
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_artifact: 'Reading artifact',
  get_project_state: 'Checking project state',
  list_scenes: 'Browsing scenes',
  list_characters: 'Looking up characters',
  list_locations: 'Looking up locations',
  propose_artifact_edit: 'Proposing edits',
  propose_run: 'Preparing pipeline run',
}

export function friendlyToolName(rawName: string): string {
  return TOOL_DISPLAY_NAMES[rawName] ?? rawName.replace(/_/g, ' ')
}

export const RUN_ACTION_IDS: Record<string, string> = {
  start_analysis: 'mvp_ingest',
  go_deeper: 'world_building',
}

export const SECTION_ICONS: Record<string, ElementType> = {
  characters: Users,
  locations: MapPin,
  props: Package,
  scenes: Clapperboard,
  activity: Activity,
}

export const MODE_OPTIONS: { value: InteractionMode; label: string; tip: string }[] = [
  { value: 'guided', label: 'Guided', tip: 'Verbose, step-by-step explanations' },
  { value: 'balanced', label: 'Balanced', tip: 'Clear and concise (default)' },
  { value: 'expert', label: 'Expert', tip: 'Terse, action-oriented' },
]
