import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { ExternalLink, Loader2, RefreshCw, Wand2 } from 'lucide-react'
import { toast } from 'sonner'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import {
  aiPrevizCostBadge,
  formatAdoptionState,
  previzDescription,
} from '@/components/previz-panel-support'
import { SceneActionControls } from '@/components/SceneActionControls'
import { ScenePlanUnitSummary } from '@/components/ScenePlanUnitSummary'
import { formatConsistencyStrategy, formatLatencyMs } from '@/components/preview-provenance'
import { asNumber, asRecord, asString, formatDuration, formatToken } from '@/components/render-utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getArtifact } from '@/lib/api'
import { getAssetFileUrl } from '@/lib/api/assets'
import {
  isRunActive,
  useArtifact,
  usePrevizAdoptionStatus,
  useProjectInputs,
  useRunState,
  useSceneActionPreflight,
  useStartRun,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import { mediaValidationStatus } from '@/lib/health'
import {
  buildSceneScope,
  getSceneScopeLabel,
  getSceneScopeTargetLabel,
} from '@/lib/constants'
import type {
  ArtifactDetailResponse,
  ArtifactGroupSummary,
  SceneScopeMode,
} from '@/lib/types'

type PrevizPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
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

function renderClipIdForData(
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

function matchingPromptGroup(
  promptGroups: ArtifactGroupSummary[],
  entityId: string | null | undefined,
): ArtifactGroupSummary | undefined {
  if (!entityId) return undefined
  return promptGroups.find(group => group.entity_id === entityId)
}

type PrevizClipCardProps = {
  projectId: string
  videoGroup: ArtifactGroupSummary
  promptGroup?: ArtifactGroupSummary
  canRegenerateClip: boolean
  isRegeneratingClip: boolean
  onRegenerateClip: (clipId: string) => void
}

function PrevizClipCard({
  projectId,
  videoGroup,
  promptGroup,
  canRegenerateClip,
  isRegeneratingClip,
  onRegenerateClip,
}: PrevizClipCardProps) {
  const { data: artifact, isLoading } = useArtifact(
    projectId,
    'ai_previz_video',
    videoGroup.entity_id ?? undefined,
    videoGroup.latest_version,
  )
  const data = artifact?.payload?.data as Record<string, unknown> | undefined
  const video = asRecord(data?.video)
  const videoPath = asString(video?.relative_path)
  const videoUrl = videoPath ? getAssetFileUrl(projectId, videoPath) : null
  const renderClipId = asString(data?.render_clip_id) ?? videoGroup.entity_id ?? null
  const renderClipLabel = renderClipId ?? 'AI previz clip'
  const startSeconds = asNumber(data?.render_clip_start_time_seconds)
  const endSeconds = asNumber(data?.render_clip_end_time_seconds)
  const durationSeconds = asNumber(data?.duration_seconds)
  const sourceShots = Array.isArray(data?.source_shot_ids)
    ? data.source_shot_ids.filter((item): item is string => typeof item === 'string')
    : []
  const promptRef = asRecord(data?.prompt_ref)
  const promptEntityId = asString(promptRef?.entity_id) ?? promptGroup?.entity_id
  const promptVersion = asNumber(promptRef?.version) ?? promptGroup?.latest_version
  const promptHref = promptEntityId && promptVersion
    ? `/${projectId}/artifacts/ai_previz_prompt/${promptEntityId}/${promptVersion}`
    : null
  const detailHref = videoGroup.entity_id
    ? `/${projectId}/artifacts/ai_previz_video/${videoGroup.entity_id}/${videoGroup.latest_version}`
    : null
  const clipWindow = startSeconds !== null && endSeconds !== null
    ? `${formatDuration(startSeconds) ?? `${startSeconds}s`} - ${formatDuration(endSeconds) ?? `${endSeconds}s`}`
    : null

  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/60 px-4 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{renderClipLabel}</p>
            <Badge variant="outline">video v{videoGroup.latest_version}</Badge>
            {promptVersion && <Badge variant="outline">prompt v{promptVersion}</Badge>}
            {clipWindow && <Badge variant="secondary">{clipWindow}</Badge>}
            {formatDuration(durationSeconds) && (
              <Badge variant="outline">{formatDuration(durationSeconds)}</Badge>
            )}
            {sourceShots.length > 0 && (
              <Badge variant="outline">Shots {sourceShots.join(', ')}</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            Low-fidelity previz video for this render clip.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => renderClipId && onRegenerateClip(renderClipId)}
            disabled={!renderClipId || !canRegenerateClip}
          >
            {isRegeneratingClip ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            Regenerate Clip
          </Button>
          {detailHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={detailHref}>
                <ExternalLink className="h-3.5 w-3.5" />
                Detail
              </Link>
            </Button>
          )}
          {promptHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={promptHref}>
                <ExternalLink className="h-3.5 w-3.5" />
                Prompt
              </Link>
            </Button>
          )}
        </div>
      </div>
      {isLoading && (
        <div className="aspect-video w-full rounded-lg border border-border bg-muted/20 animate-pulse" />
      )}
      {!isLoading && videoUrl && (
        <video
          controls
          preload="metadata"
          className="aspect-video w-full rounded-lg border border-border bg-black"
          src={videoUrl}
        />
      )}
      {!isLoading && !videoUrl && (
        <div className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
          Previz media is missing for this clip.
        </div>
      )}
    </div>
  )
}

type MissingPrevizClipCardProps = {
  clipId: string
  renderClipPlanVersion?: number
  staleGroup?: ArtifactGroupSummary
  canGenerateClip: boolean
  isGeneratingClip: boolean
  onGenerateClip: (clipId: string) => void
}

function MissingPrevizClipCard({
  clipId,
  renderClipPlanVersion,
  staleGroup,
  canGenerateClip,
  isGeneratingClip,
  onGenerateClip,
}: MissingPrevizClipCardProps) {
  return (
    <div className="rounded-lg border border-dashed border-amber-500/40 bg-amber-500/5 px-4 py-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{clipId}</p>
            <Badge variant="outline">Missing current previz</Badge>
            {renderClipPlanVersion && (
              <Badge variant="secondary">render clips v{renderClipPlanVersion}</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {staleGroup
              ? `Latest saved video v${staleGroup.latest_version} belongs to an older render clip plan and is hidden here.`
              : 'No playable previz video has been saved for this current render clip yet.'}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onGenerateClip(clipId)}
          disabled={!canGenerateClip}
        >
          {isGeneratingClip ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
          Generate Clip
        </Button>
      </div>
    </div>
  )
}

export function PrevizPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  renderClipPlanGroup,
  aiPrevizGroup,
  aiPrevizGroups = [],
  aiPrevizPromptGroup,
  aiPrevizPromptGroups = [],
}: PrevizPanelProps) {
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
  const shouldUseRenderClipPreviz = plannedClipIds.length > 1 || hasAnyClipPrevizArtifacts
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

  const { data: aiPrevizArtifact, isLoading: aiPrevizLoading } = useArtifact(
    projectId,
    'ai_previz_video',
    primaryAiPrevizGroup?.entity_id ?? sceneId,
    primaryAiPrevizGroup?.latest_version,
  )
  const { data: previzStatus } = usePrevizAdoptionStatus(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const [scope, setScope] = useState<SceneScopeMode>('current_scene')
  const [pendingClipId, setPendingClipId] = useState<string | null>(null)
  const sceneScope = buildSceneScope(scope, sceneId)
  const { data: aiPreflight } = useSceneActionPreflight(projectId, {
    recipe_id: 'ai_previz_generation',
    scene_scope: sceneScope,
  })

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const aiPrevizRunActive = hasActiveRun && runState?.state.recipe_id === 'ai_previz_generation'
  const anotherRunActive = hasActiveRun
    && !!runState
    && runState.state.recipe_id !== 'ai_previz_generation'
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartAiPreviz = !!latestInputPath
    && !runBlocked
    && aiPreflight?.status !== 'soft_block'

  const aiPrevizData = aiPrevizArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizStatus = previzStatus?.ai_previz
  const aiPrevizCostLabel = aiPrevizCostBadge(aiPrevizStatus)
  const aiPrevizStartFrom = aiPreflight?.start_from ?? undefined
  const aiPrevizReusesClipPlan = aiPrevizStartFrom === 'ai_previz'
  const aiPrevizReusesShotPlan = aiPrevizStartFrom === 'render_clip_planning'
  const hasSavedPrevizOutput = hasAnyClipPrevizArtifacts
    || allClipAiPrevizPromptGroups.length > 0
    || displayedAiPrevizGroups.length > 0
    || displayedAiPrevizPromptGroups.length > 0
    || !!primaryAiPrevizGroup
    || !!primaryAiPrevizPromptGroup
    || !!sceneAiPrevizGroup
    || !!sceneAiPrevizPromptGroup
  const isMultiClipPreviz = displayedAiPrevizGroups.length > 1 || plannedClipIds.length > 1
  const previzClipArtifactCount = displayedAiPrevizGroups.length
  const plannedClipCount = plannedClipIds.length
  const hasIncompleteCurrentClipSet = plannedClipCount > 0
    && !clipVideoDetailsLoading
    && previzClipArtifactCount < plannedClipCount
  const hiddenStaleClipCount = staleClipVideoDetails.length
  const firstPassLatencyMs = aiPrevizStatus?.latency_ms ?? null
  const regenerateReuseLatencyMs = aiPrevizStatus?.regenerate_reuse_latency_ms ?? null
  const regenerateFullLatencyMs = aiPrevizStatus?.regenerate_full_latency_ms ?? null
  const showReuseRegenerateLatency = (aiPrevizReusesClipPlan || aiPrevizReusesShotPlan)
    && regenerateReuseLatencyMs !== null
    && regenerateReuseLatencyMs !== firstPassLatencyMs
  const showFullRegenerateLatency = (aiPrevizReusesClipPlan || aiPrevizReusesShotPlan)
    && regenerateFullLatencyMs !== null
    && regenerateFullLatencyMs !== regenerateReuseLatencyMs
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)

  const aiPrevizDetailHref = primaryAiPrevizGroup
    ? `/${projectId}/artifacts/ai_previz_video/${primaryAiPrevizGroup.entity_id ?? sceneId}/${primaryAiPrevizGroup.latest_version}`
    : null
  const aiPrevizPromptHref = primaryAiPrevizPromptGroup
    ? `/${projectId}/artifacts/ai_previz_prompt/${primaryAiPrevizPromptGroup.entity_id ?? sceneId}/${primaryAiPrevizPromptGroup.latest_version}`
    : null
  const validationRef = (
    primaryAiPrevizGroup?.health_details?.source_kind === 'media_validation'
    || primaryAiPrevizGroup?.health_details?.source_kind === 'media_validation_stale'
  )
    ? primaryAiPrevizGroup.health_details.source_artifact_ref
    : null
  const validationStatus = mediaValidationStatus(
    primaryAiPrevizGroup?.health,
    primaryAiPrevizGroup?.health_details,
  )
  const { data: validationArtifact, isLoading: validationLoading } = useArtifact(
    projectId,
    validationRef?.artifact_type,
    validationRef?.entity_id ?? undefined,
    validationRef?.version,
  )
  const validationData = validationArtifact?.payload?.data as Record<string, unknown> | undefined
  const validationDetailHref = validationRef?.entity_id && validationRef.version
    ? `/${projectId}/artifacts/${validationRef.artifact_type}/${validationRef.entity_id}/${validationRef.version}`
    : null

  async function handleStartAiPreviz() {
    if (!latestInputPath) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'ai_previz_generation',
        accept_config: true,
        force: hasSavedPrevizOutput,
        start_from: aiPrevizStartFrom,
        scene_scope: sceneScope,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        hasSavedPrevizOutput
          ? aiPrevizReusesClipPlan
            ? `Regenerating AI previz from the current render clip plan for ${configuredScopeLabel.toLowerCase()}`
            : aiPrevizReusesShotPlan
              ? `Regenerating AI previz after refreshing render clips for ${configuredScopeLabel.toLowerCase()}`
              : `Refreshing AI previz for ${configuredScopeLabel.toLowerCase()}`
          : aiPrevizReusesClipPlan
            ? `Started AI previz from the current render clip plan for ${configuredScopeLabel.toLowerCase()}`
            : aiPrevizReusesShotPlan
              ? `Started AI previz after refreshing render clips for ${configuredScopeLabel.toLowerCase()}`
              : `Started AI previz for ${configuredScopeLabel.toLowerCase()}`,
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start AI previz')
    }
  }

  async function handleStartAiPrevizClip(clipId: string) {
    if (!latestInputPath) return
    setPendingClipId(clipId)
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'ai_previz_generation',
        accept_config: true,
        force: true,
        start_from: aiPrevizStartFrom,
        scene_scope: buildSceneScope('current_scene', sceneId),
        render_clip_ids: [clipId],
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(`Regenerating AI previz clip ${clipId} for ${sceneHeading}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start AI previz clip')
    } finally {
      setPendingClipId(null)
    }
  }

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Previz</CardTitle>
                <Badge variant="outline">Selected: {configuredScopeLabel}</Badge>
                <Badge variant="secondary">Shipped lane: {aiPrevizStatus?.label ?? 'AI Previz'}</Badge>
                {aiPrevizStatus && (
                  <Badge
                    variant={aiPrevizStatus.blocker_reasons.length > 0 ? 'outline' : 'secondary'}
                  >
                    AI lane: {formatAdoptionState(aiPrevizStatus.adoption_state)}
                  </Badge>
                )}
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
                {renderClipPlanGroup && (
                  <Badge variant="secondary">
                    Render clips v{renderClipPlanGroup.latest_version}
                  </Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                {previzDescription(previzStatus)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              AI previz.
            </p>
          )}
          {aiPrevizRunActive && (
            <p>AI previz is currently running for {activeRunScopeLabel.toLowerCase()}.</p>
          )}
          <SceneActionControls
            scope={scope}
            onScopeChange={setScope}
            preflight={aiPreflight}
            disabled={runBlocked}
          />
        </CardContent>
      </Card>

      <Card className="gap-0 border-sky-500/30">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-lg">{aiPrevizStatus?.label ?? 'AI Previz'}</CardTitle>
              <Badge variant="secondary">Only shipped previz lane</Badge>
              {aiPrevizStatus && (
                <Badge
                  variant={aiPrevizStatus.blocker_reasons.length > 0 ? 'outline' : 'secondary'}
                >
                  {formatAdoptionState(aiPrevizStatus.adoption_state)}
                </Badge>
              )}
              <Badge variant="outline">AI video lane</Badge>
              {aiPrevizStatus?.candidate_label && (
                <Badge variant="outline">{aiPrevizStatus.candidate_label}</Badge>
              )}
              {aiPrevizCostLabel && <Badge variant="outline">{aiPrevizCostLabel}</Badge>}
              {firstPassLatencyMs !== null && (
                <Badge variant="outline">First pass {formatLatencyMs(firstPassLatencyMs)}</Badge>
              )}
              {showReuseRegenerateLatency && regenerateReuseLatencyMs !== null && (
                <Badge variant="outline">Reuse {formatLatencyMs(regenerateReuseLatencyMs)}</Badge>
              )}
              {showFullRegenerateLatency && regenerateFullLatencyMs !== null && (
                <Badge variant="outline">Full regen {formatLatencyMs(regenerateFullLatencyMs)}</Badge>
              )}
              {aiPrevizStatus?.latency_budget_ms && (
                <Badge variant="outline">Target ≤ {formatLatencyMs(aiPrevizStatus.latency_budget_ms)}</Badge>
              )}
              {primaryAiPrevizGroup && (
                <>
                  <Badge variant="outline">v{primaryAiPrevizGroup.latest_version}</Badge>
                  <HealthBadge
                    health={primaryAiPrevizGroup.health}
                    details={primaryAiPrevizGroup.health_details}
                  />
                </>
              )}
            </div>
            <CardDescription>
              {aiPrevizStatus?.fidelity_disclosure
                ?? 'Provider-generated low-fidelity AI video for planning review, distinct from final render output.'}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {aiPrevizStatus && (
            <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
              <div className="space-y-1">
                <p>{aiPrevizStatus.reason}</p>
                <p>{aiPrevizStatus.intended_use}</p>
              </div>
            </div>
          )}
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
            <div className="space-y-1">
              <p>
                Preflight: {aiPrevizStatus?.engine_pack_id ?? 'ai_previz_generation'} /{' '}
                {aiPrevizStatus?.target_model ?? 'configured model'}
              </p>
              <p>
                {aiPrevizStatus?.resolution ?? 'Configured resolution'},{' '}
                {formatDuration(aiPrevizStatus?.duration_seconds ?? null) ?? 'configured duration'},{' '}
                {formatConsistencyStrategy(aiPrevizStatus?.consistency_strategy ?? null)
                  ?? 'configured consistency'}.
              </p>
              <p>
                Final footage still belongs in the Render tab. Keep this lane focused on motion,
                staging, and operator-readable planning feedback.
              </p>
              {aiPreflight?.prerequisite_strategy && (
                <p>
                  Prep strategy: {aiPreflight.prerequisite_strategy === 'reuse_existing_render_clip_plan'
                    ? 'Reuse current render clip plan'
                    : aiPreflight.prerequisite_strategy === 'reuse_existing_shot_plan'
                      ? 'Refresh render clips from current shot plan'
                      : 'One-pass previz prep'}.
                </p>
              )}
              {(aiPrevizReusesClipPlan || aiPrevizReusesShotPlan) && (
                <p>
                  Reuse path: CineForge will keep the current {aiPrevizReusesClipPlan
                    ? 'render clip plan'
                    : 'shot plan'} and rerun only the needed AI previz stages.
                </p>
              )}
              {showReuseRegenerateLatency && regenerateReuseLatencyMs !== null && (
                <p>
                  Measured regenerate loop: {formatLatencyMs(regenerateReuseLatencyMs)} to first
                  playable on the current reuse path
                  {showFullRegenerateLatency && regenerateFullLatencyMs !== null
                    ? ` versus ${formatLatencyMs(regenerateFullLatencyMs)} when rerunning from recipe start on the same existing-clip substrate.`
                    : '.'}
                </p>
              )}
              {(aiPreflight?.reused_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Reused:{' '}
                  {aiPreflight?.reused_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
              {(aiPreflight?.auto_build_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Auto-built:{' '}
                  {aiPreflight?.auto_build_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
              {(aiPreflight?.missing_optional_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Missing optional context:{' '}
                  {aiPreflight?.missing_optional_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {aiPrevizDetailHref && (
              <Button asChild variant="outline" size="sm">
                <Link to={aiPrevizDetailHref}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  AI Previz Detail
                </Link>
              </Button>
            )}
            {aiPrevizPromptHref && (
              <Button asChild variant="outline" size="sm">
                <Link to={aiPrevizPromptHref}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  Prompt Detail
                </Link>
              </Button>
            )}
            {validationDetailHref && (
              <Button asChild variant="outline" size="sm">
                <Link to={validationDetailHref}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  Validation Detail
                </Link>
              </Button>
            )}
            <Button
              size="sm"
              variant="default"
              onClick={handleStartAiPreviz}
              disabled={!canStartAiPreviz}
            >
              {startRun.isPending && aiPrevizRunActive ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : hasSavedPrevizOutput ? (
                <RefreshCw className="h-3.5 w-3.5" />
              ) : (
                <Wand2 className="h-3.5 w-3.5" />
              )}
              {scope === 'current_scene'
                ? hasSavedPrevizOutput
                  ? 'Regenerate AI Previz for Current Scene'
                  : 'Generate AI Previz for Current Scene'
                : hasSavedPrevizOutput
                  ? 'Regenerate AI Previz for All Scenes'
                  : 'Generate AI Previz for All Scenes'}
            </Button>
          </div>

          {aiPrevizData && (
            <p className="text-sm text-muted-foreground">
              {hasIncompleteCurrentClipSet
                ? `Current AI previz has ${previzClipArtifactCount} of ${plannedClipCount} render-clip players for ${sceneHeading}. Regenerate to fill the missing clip.`
                : validationStatus?.label === 'Validation Pending'
                ? hasClipPrevizOutputs
                  ? `Latest AI previz clips are playable for ${sceneHeading}. Validation is still pending.`
                  : `Latest AI previz clip is playable for ${sceneHeading}. Validation is still pending.`
                : validationStatus?.label === 'Validation Failed'
                  ? hasClipPrevizOutputs
                    ? `Latest AI previz clips are playable for ${sceneHeading}, but validation flagged at least one for follow-up.`
                    : `Latest AI previz clip is playable for ${sceneHeading}, but validation flagged it for follow-up.`
                  : hasClipPrevizOutputs
                    ? `Latest AI previz clips are ready for ${sceneHeading}. The players appear below.`
                    : `Latest AI previz clip is ready for ${sceneHeading}. The viewer appears below.`}
            </p>
          )}
          {!aiPrevizData && !aiPrevizRunActive && !aiPrevizLoading && !hasAnyClipPrevizArtifacts && (
            <div className="rounded-lg border border-dashed border-border bg-card/50 px-5 py-8 text-center">
              <div className="mx-auto flex max-w-md flex-col items-center gap-3">
                <div className="rounded-full bg-muted p-3">
                  <Wand2 className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">No AI previz yet</p>
                  <p className="text-sm text-muted-foreground">
                    {aiPrevizReusesShotPlan
                      ? `Generate an AI motion pass for ${configuredScopeTarget} from the current shot plan. CineForge keeps this lane intentionally low-fidelity and explicitly non-final.`
                      : `Generate an AI motion pass for ${configuredScopeTarget}. CineForge keeps this lane intentionally low-fidelity and explicitly non-final.`}
                  </p>
                </div>
              </div>
            </div>
          )}
          {!aiPrevizData && aiPrevizRunActive && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-5 py-6">
              <div className="flex items-start gap-3">
                <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">
                    AI previz is running for {activeRunScopeLabel.toLowerCase()}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    This tab will resolve back to {sceneHeading} as soon as the updated clip lands.
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <ScenePlanUnitSummary
        mode="previz"
        sceneHeading={sceneHeading}
        shotPlanData={shotPlanData}
        renderClipPlanData={renderClipPlanData}
        currentOutputData={aiPrevizData}
        generatedVideoCount={displayedAiPrevizGroups.length}
      />

      {isMultiClipPreviz && (
        <Card className="gap-0">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">AI Previz Clips</CardTitle>
            <CardDescription>
              {plannedClipCount > 0
                ? `${sceneHeading} has ${previzClipArtifactCount} of ${plannedClipCount} current low-fidelity previz clips.`
                : `${sceneHeading} has ${previzClipArtifactCount} low-fidelity previz clips.`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {hasIncompleteCurrentClipSet && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
                Current previz is incomplete for render clips v{renderClipPlanGroup?.latest_version}.
                {missingClipIds.length > 0 && ` Missing: ${missingClipIds.join(', ')}.`}
                {hiddenStaleClipCount > 0 && ` ${hiddenStaleClipCount} stale prior-plan clip${hiddenStaleClipCount === 1 ? ' is' : 's are'} hidden.`}
              </div>
            )}
            {hasClipPrevizOutputs && sceneAiPrevizGroup && (
              <p className="text-sm text-muted-foreground">
                A previous scene-level previz artifact exists for {sceneId}, but this scene now uses
                render-clip previz. The scene-level artifact is hidden here to avoid mixing old and
                current output models.
              </p>
            )}
            {displayedAiPrevizGroups.map(group => (
              <PrevizClipCard
                key={`previz-${group.entity_id}`}
                projectId={projectId}
                videoGroup={group}
                promptGroup={matchingPromptGroup(displayedAiPrevizPromptGroups, group.entity_id)}
                canRegenerateClip={canStartAiPreviz}
                isRegeneratingClip={pendingClipId === (
                  renderClipIdForData(group, currentClipVideoDetails.find(detail => detail.group === group)?.data)
                  ?? group.entity_id
                )}
                onRegenerateClip={handleStartAiPrevizClip}
              />
            ))}
            {missingClipIds.map(clipId => (
              <MissingPrevizClipCard
                key={`missing-previz-${clipId}`}
                clipId={clipId}
                renderClipPlanVersion={renderClipPlanGroup?.latest_version}
                staleGroup={staleGroupByRenderClipId.get(clipId)}
                canGenerateClip={canStartAiPreviz}
                isGeneratingClip={pendingClipId === clipId}
                onGenerateClip={handleStartAiPrevizClip}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {aiPrevizLoading && primaryAiPrevizGroup && !aiPrevizData && !hasClipPrevizOutputs && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}
      {validationLoading && validationRef && !validationArtifact && (
        <div className="h-36 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {aiPrevizData && !hasClipPrevizOutputs && (
        <AiPrevizViewer
          data={aiPrevizData}
          projectId={projectId}
          health={primaryAiPrevizGroup?.health}
          healthDetails={primaryAiPrevizGroup?.health_details}
        />
      )}
      {validationData && (
        <MediaValidationViewer
          data={validationData}
          projectId={projectId}
          compact
          detailHref={validationDetailHref}
        />
      )}
    </div>
  )
}
