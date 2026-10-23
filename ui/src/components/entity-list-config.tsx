import { useNavigate } from 'react-router-dom'
import { Clapperboard, MapPin, Users, Wrench } from 'lucide-react'
import { EmptyState, ListSkeleton } from '@/components/StateViews'
import type { ExportScope } from '@/lib/api'
import { useArtifactGroups, useProjectInputs } from '@/lib/hooks'

export type EntitySection = 'characters' | 'locations' | 'props' | 'scenes'
export type BibleArtifactType = 'character_bible' | 'location_bible' | 'prop_bible'

// Shared list metadata stays beside the empty-state action it describes.
// eslint-disable-next-line react-refresh/only-export-components
export const sectionConfig: Record<EntitySection, {
  icon: typeof Users
  color: string
  label: string
  description: string
  artifactType: BibleArtifactType | 'scene'
  exportScope: ExportScope
  emptyTitle: string
  emptyDescription: string
}> = {
  characters: {
    icon: Users,
    color: 'text-amber-400',
    label: 'Characters',
    description: 'All characters discovered in your screenplay',
    artifactType: 'character_bible',
    exportScope: 'characters',
    emptyTitle: 'No characters yet',
    emptyDescription: 'Deep Breakdown can build character profiles from your screenplay.',
  },
  locations: {
    icon: MapPin,
    color: 'text-rose-400',
    label: 'Locations',
    description: 'All locations discovered in your screenplay',
    artifactType: 'location_bible',
    exportScope: 'locations',
    emptyTitle: 'No locations yet',
    emptyDescription: 'Deep Breakdown can build location profiles from your screenplay.',
  },
  props: {
    icon: Wrench,
    color: 'text-orange-400',
    label: 'Props',
    description: 'All props discovered in your screenplay',
    artifactType: 'prop_bible',
    exportScope: 'props',
    emptyTitle: 'No props yet',
    emptyDescription: 'Deep Breakdown can identify the props in your screenplay.',
  },
  scenes: {
    icon: Clapperboard,
    color: 'text-primary',
    label: 'Scenes',
    description: 'All scenes extracted from your screenplay',
    artifactType: 'scene',
    exportScope: 'scenes',
    emptyTitle: 'No scenes yet',
    emptyDescription: 'Open your script to break it into scenes.',
  },
}

export function EntityListEmptyState({
  section,
  projectId,
}: {
  section: EntitySection
  projectId: string
}) {
  const navigate = useNavigate()
  const config = sectionConfig[section]
  const isScenes = section === 'scenes'
  const { data: artifactGroups, isLoading: artifactsLoading } = useArtifactGroups(
    isScenes ? undefined : projectId,
  )
  const { data: inputs, isLoading: inputsLoading } = useProjectInputs(
    isScenes ? undefined : projectId,
  )
  if (!isScenes && (artifactsLoading || inputsLoading)) return <ListSkeleton />

  const hasInput = !!inputs?.length
  const hasScriptBreakdown = artifactGroups?.some(group =>
    ['canonical_script', 'script_bible', 'scene'].includes(group.artifact_type)
  ) ?? false
  const hasDeepBreakdown = artifactGroups?.some(group =>
    group.artifact_type === 'character_bible' || group.artifact_type === 'entity_graph'
  ) ?? false
  const canOpenDeepBreakdown = !isScenes && hasInput && hasScriptBreakdown && !hasDeepBreakdown
  const description = isScenes
    ? config.emptyDescription
    : !hasInput
      ? 'Open your script to add a screenplay first.'
      : !hasScriptBreakdown
        ? 'Open your script to break it down first.'
        : hasDeepBreakdown
          ? `No ${config.label.toLowerCase()} are available from the current breakdown.`
          : config.emptyDescription

  return (
    <EmptyState
      icon={config.icon}
      title={config.emptyTitle}
      description={description}
      action={{
        label: canOpenDeepBreakdown ? 'Open Deep Breakdown' : 'Open Script',
        onClick: () => navigate(canOpenDeepBreakdown ? `/${projectId}/intent` : `/${projectId}`),
      }}
    />
  )
}
