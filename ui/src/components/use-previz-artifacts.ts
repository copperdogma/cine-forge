import { hasRenderClipPrevizScope } from '@/components/previz-panel-support'
import { useQueries } from '@tanstack/react-query'
import { getArtifact } from '@/lib/api'
import { useArtifact } from '@/lib/hooks'
import { asRecord, asString } from '@/components/render-utils'
import type { ArtifactGroupSummary, ArtifactDetailResponse } from '@/lib/types'

export type PrevizArtifactProps = {
  projectId: string
  sceneId: string
  shotPlanGroup?: ArtifactGroupSummary
  renderClipPlanGroup?: ArtifactGroupSummary
  aiPrevizGroup?: ArtifactGroupSummary
  aiPrevizGroups?: ArtifactGroupSummary[]
  aiPrevizPromptGroup?: ArtifactGroupSummary
  aiPrevizPromptGroups?: ArtifactGroupSummary[]
}

function isRenderClipEntityId(entityId: string | null | undefined, sceneId: string): boolean {
  if (!entityId || entityId === sceneId) return false
  return entityId.startsWith(`${sceneId}_clip_`) || entityId.startsWith(`${sceneId}__`)
}

function sortArtifactGroups(groups: ArtifactGroupSummary[]): ArtifactGroupSummary[] {
  return [...groups].sort((left, right) => (left.entity_id ?? '').localeCompare(right.entity_id ?? ''))
}

function currentRenderClipPlanPath(
  renderClipPlanGroup: ArtifactGroupSummary | undefined,
  sceneId: string,
): string | null {
  if (!renderClipPlanGroup?.latest_version) return null
  const entityId = renderClipPlanGroup.entity_id ?? sceneId
  return `artifacts/render_clip_plan/${entityId}/v${renderClipPlanGroup.latest_version}.json`
}

function plannedRenderClipIds(renderClipPlanData: Record<string, unknown> | undefined): string[] {
  const ids: string[] = []
  const clips = Array.isArray(renderClipPlanData?.clips) ? renderClipPlanData.clips : []
  clips.forEach(item => {
    const clipId = asString(asRecord(item)?.clip_id)
    if (clipId && !ids.includes(clipId)) ids.push(clipId)
  })
  return ids
}

function renderClipPlanRefPath(data: Record<string, unknown> | undefined): string | null {
  return asString(asRecord(data?.render_clip_plan_ref)?.path)
}

export function renderClipIdForData(
  group: ArtifactGroupSummary,
  data: Record<string, unknown> | undefined,
): string | null {
  return asString(data?.render_clip_id) ?? group.entity_id ?? null
}

function isCurrentRenderClipArtifact(
  group: ArtifactGroupSummary,
  data: Record<string, unknown> | undefined,
  options: {
    renderClipPlanPath: string | null
    plannedClipIds: string[]
  },
): boolean {
  if (!data) return false
  const { renderClipPlanPath, plannedClipIds } = options
  const renderClipId = renderClipIdForData(group, data)
  if (plannedClipIds.length > 0 && (!renderClipId || !plannedClipIds.includes(renderClipId))) {
    return false
  }
  if (!renderClipPlanPath) return true
  return renderClipPlanRefPath(data) === renderClipPlanPath
}

type LoadedPrevizClip = {
  group: ArtifactGroupSummary
  artifact?: ArtifactDetailResponse
  data?: Record<string, unknown>
  isLoading: boolean
}

export function matchingPromptGroup(
  promptGroups: ArtifactGroupSummary[],
  entityId: string | null | undefined,
): ArtifactGroupSummary | undefined {
  if (!entityId) return undefined
  return promptGroups.find(group => group.entity_id === entityId)
}

export function usePrevizArtifacts({ projectId, sceneId, shotPlanGroup, renderClipPlanGroup,
  aiPrevizGroup, aiPrevizGroups = [], aiPrevizPromptGroup, aiPrevizPromptGroups = [],
}: PrevizArtifactProps) {
  const allClipAiPrevizGroups = sortArtifactGroups(
    aiPrevizGroups.filter(group => isRenderClipEntityId(group.entity_id, sceneId)),
  )
  const sceneAiPrevizGroup = aiPrevizGroups.find(group => group.entity_id === sceneId) ?? aiPrevizGroup
  const allClipAiPrevizPromptGroups = sortArtifactGroups(
    aiPrevizPromptGroups.filter(group => isRenderClipEntityId(group.entity_id, sceneId)),
  )
  const sceneAiPrevizPromptGroup = aiPrevizPromptGroups.find(group => group.entity_id === sceneId)
    ?? aiPrevizPromptGroup
  const { data: shotPlanArtifact } = useArtifact(
    projectId,
    'shot_plan',
    sceneId,
    shotPlanGroup?.latest_version,
  )
  const { data: renderClipPlanArtifact } = useArtifact(
    projectId,
    'render_clip_plan',
    sceneId,
    renderClipPlanGroup?.latest_version,
  )
  const shotPlanData = shotPlanArtifact?.payload?.data as Record<string, unknown> | undefined
  const renderClipPlanData = renderClipPlanArtifact?.payload?.data as Record<string, unknown> | undefined
  const renderClipPlanPath = currentRenderClipPlanPath(renderClipPlanGroup, sceneId)
  const plannedClipIds = plannedRenderClipIds(renderClipPlanData)

  const clipVideoQueries = useQueries({
    queries: allClipAiPrevizGroups.map(group => ({
      queryKey: [
        'projects',
        projectId,
        'artifacts',
        'ai_previz_video',
        group.entity_id,
        group.latest_version,
      ],
      queryFn: () => getArtifact(
        projectId,
        'ai_previz_video',
        group.entity_id!,
        group.latest_version,
      ),
      enabled: !!(projectId && group.entity_id && group.latest_version),
    })),
  })
  const clipVideoDetails: LoadedPrevizClip[] = allClipAiPrevizGroups.map((group, index) => {
    const artifact = clipVideoQueries[index]?.data
    return {
      group,
      artifact,
      data: artifact?.payload?.data as Record<string, unknown> | undefined,
      isLoading: clipVideoQueries[index]?.isLoading ?? false,
    }
  })
  const currentClipVideoDetails = clipVideoDetails.filter(detail =>
    isCurrentRenderClipArtifact(
      detail.group,
      detail.data,
      {
        renderClipPlanPath,
        plannedClipIds,
      },
    ),
  )
  const staleClipVideoDetails = clipVideoDetails.filter(detail =>
    detail.data
    && !isCurrentRenderClipArtifact(
      detail.group,
      detail.data,
      {
        renderClipPlanPath,
        plannedClipIds,
      },
    ),
  )
  const currentClipEntityIds = new Set(
    currentClipVideoDetails
      .map(detail => detail.group.entity_id)
      .filter((entityId): entityId is string => !!entityId),
  )
  const currentClipRenderIds = new Set(
    currentClipVideoDetails
      .map(detail => renderClipIdForData(detail.group, detail.data))
      .filter((clipId): clipId is string => !!clipId),
  )
  const clipVideoDetailsLoading = clipVideoQueries.some(query => query.isLoading)
  const missingClipIds = clipVideoDetailsLoading
    ? []
    : plannedClipIds.filter(clipId => !currentClipRenderIds.has(clipId))
  const staleGroupByRenderClipId = new Map(
    staleClipVideoDetails
      .map(detail => [renderClipIdForData(detail.group, detail.data), detail.group] as const)
      .filter((entry): entry is readonly [string, ArtifactGroupSummary] => !!entry[0]),
  )
  const hasCurrentClipPrevizOutputs = currentClipVideoDetails.length > 0
  const hasClipPrevizOutputs = hasCurrentClipPrevizOutputs
  const hasAnyClipPrevizArtifacts = allClipAiPrevizGroups.length > 0
  const shouldUseRenderClipPreviz = hasRenderClipPrevizScope(plannedClipIds.length, hasAnyClipPrevizArtifacts)
  const displayedAiPrevizGroups = hasCurrentClipPrevizOutputs
    ? currentClipVideoDetails.map(detail => detail.group)
    : shouldUseRenderClipPreviz
      ? []
      : sortArtifactGroups(
        aiPrevizGroups.length > 0
          ? aiPrevizGroups
          : sceneAiPrevizGroup
            ? [sceneAiPrevizGroup]
            : [],
      )
  const displayedAiPrevizPromptGroups = hasCurrentClipPrevizOutputs
    ? allClipAiPrevizPromptGroups.filter(group =>
      !!group.entity_id && currentClipEntityIds.has(group.entity_id),
    )
    : shouldUseRenderClipPreviz
      ? []
      : sortArtifactGroups(
        aiPrevizPromptGroups.length > 0
          ? aiPrevizPromptGroups
          : sceneAiPrevizPromptGroup
            ? [sceneAiPrevizPromptGroup]
            : [],
      )
  const primaryAiPrevizGroup = displayedAiPrevizGroups[0] ?? (
    shouldUseRenderClipPreviz ? undefined : sceneAiPrevizGroup
  )
  const primaryAiPrevizPromptGroup = matchingPromptGroup(
    displayedAiPrevizPromptGroups,
    primaryAiPrevizGroup?.entity_id,
  ) ?? (shouldUseRenderClipPreviz ? undefined : sceneAiPrevizPromptGroup)

  return { shotPlanData, renderClipPlanData, plannedClipIds, primaryAiPrevizGroup, primaryAiPrevizPromptGroup, allClipAiPrevizPromptGroups, displayedAiPrevizGroups, displayedAiPrevizPromptGroups, hasAnyClipPrevizArtifacts, hasClipPrevizOutputs, sceneAiPrevizGroup, sceneAiPrevizPromptGroup, currentClipVideoDetails, clipVideoDetailsLoading, staleClipVideoDetails, missingClipIds, staleGroupByRenderClipId }
}
