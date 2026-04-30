import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { GeneratedVideoViewer } from '@/components/GeneratedVideoViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { RenderPromptViewer } from '@/components/RenderPromptViewer'
import { SceneActionControls } from '@/components/SceneActionControls'
import { ScenePlanUnitSummary } from '@/components/ScenePlanUnitSummary'
import { asArray, asNumber, asRecord, asString, asStringArray, formatDuration } from '@/components/render-utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getAssetFileUrl } from '@/lib/api/assets'
import {
  isRunActive,
  runHasFailed,
  useArtifact,
  useProjectInputs,
  useRunState,
  useSceneActionPreflight,
  useStartRun,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary, SceneScopeMode } from '@/lib/types'
import { buildSceneScope, getSceneScopeLabel, getSceneScopeTargetLabel } from '@/lib/constants'

function latestFailedAttemptError(attempts: Array<Record<string, unknown>> | undefined): string | null {
  if (!Array.isArray(attempts)) return null
  for (const attempt of [...attempts].reverse()) {
    if (attempt.status !== 'failed') continue
    if (typeof attempt.error === 'string' && attempt.error.trim()) {
      return attempt.error
    }
  }
  return null
}

function plannedRenderClipIds(renderClipPlanData: Record<string, unknown> | undefined): string[] {
  const ids: string[] = []
  asArray(renderClipPlanData?.clips).forEach(item => {
    const clipId = asString(asRecord(item)?.clip_id)
    if (clipId && !ids.includes(clipId)) ids.push(clipId)
  })
  return ids
}

function renderUnitEntityId(sceneId: string, clipId: string): string {
  if (clipId === sceneId || clipId.startsWith(`${sceneId}_`)) return clipId
  return `${sceneId}__${clipId}`
}

function matchingRenderClipGroup(
  groups: ArtifactGroupSummary[],
  sceneId: string,
  clipId: string,
): ArtifactGroupSummary | undefined {
  const entityId = renderUnitEntityId(sceneId, clipId)
  return groups.find(group => group.entity_id === clipId || group.entity_id === entityId)
}

function savedRenderClipIds(groups: ArtifactGroupSummary[], sceneId: string): string[] {
  const ids: string[] = []
  groups.forEach(group => {
    const entityId = group.entity_id
    if (!entityId || entityId === sceneId || ids.includes(entityId)) return
    ids.push(entityId)
  })
  return ids
}

type GeneratedVideoPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  renderClipPlanGroup?: ArtifactGroupSummary
  renderPromptGroup?: ArtifactGroupSummary
  renderPromptGroups?: ArtifactGroupSummary[]
  generatedVideoGroup?: ArtifactGroupSummary
  generatedVideoGroups?: ArtifactGroupSummary[]
  keyframeGroup?: ArtifactGroupSummary
}

type RenderClipCardProps = {
  projectId: string
  clipId: string
  videoGroup?: ArtifactGroupSummary
  promptGroup?: ArtifactGroupSummary
  canStartRender: boolean
  pendingClipId: string | null
  onRegenerateClip: (clipId: string) => void
}

function clipWindowLabel(startSeconds: number | null, endSeconds: number | null): string | null {
  if (startSeconds === null || endSeconds === null) return null
  return `${formatDuration(startSeconds) ?? `${startSeconds}s`} - ${formatDuration(endSeconds) ?? `${endSeconds}s`}`
}

function RenderClipCard({
  projectId,
  clipId,
  videoGroup,
  promptGroup,
  canStartRender,
  pendingClipId,
  onRegenerateClip,
}: RenderClipCardProps) {
  const { data: videoArtifact, isLoading } = useArtifact(
    projectId,
    'generated_video',
    videoGroup?.entity_id ?? undefined,
    videoGroup?.latest_version,
  )
  const data = videoArtifact?.payload?.data as Record<string, unknown> | undefined
  const video = asRecord(data?.video)
  const videoPath = asString(video?.relative_path)
  const videoUrl = videoPath ? getAssetFileUrl(projectId, videoPath) : null
  const startSeconds = asNumber(data?.render_clip_start_time_seconds)
  const endSeconds = asNumber(data?.render_clip_end_time_seconds)
  const durationSeconds = asNumber(data?.duration_seconds)
  const sourceShots = asStringArray(data?.source_shot_ids)
  const clipWindow = clipWindowLabel(startSeconds, endSeconds)
  const hasClipOutput = !!videoGroup || !!promptGroup
  const videoHref = videoGroup?.entity_id
    ? `/${projectId}/artifacts/generated_video/${videoGroup.entity_id}/${videoGroup.latest_version}`
    : null
  const promptHref = promptGroup?.entity_id
    ? `/${projectId}/artifacts/render_prompt/${promptGroup.entity_id}/${promptGroup.latest_version}`
    : null

  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/60 px-4 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{clipId}</p>
            {videoGroup ? (
              <Badge variant="outline">video v{videoGroup.latest_version}</Badge>
            ) : (
              <Badge variant="outline">Missing video</Badge>
            )}
            {promptGroup ? (
              <Badge variant="outline">prompt v{promptGroup.latest_version}</Badge>
            ) : (
              <Badge variant="outline">Missing prompt</Badge>
            )}
            {clipWindow && <Badge variant="secondary">{clipWindow}</Badge>}
            {formatDuration(durationSeconds) && (
              <Badge variant="outline">{formatDuration(durationSeconds)}</Badge>
            )}
            {sourceShots.length > 0 && (
              <Badge variant="outline">Shots {sourceShots.join(', ')}</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {hasClipOutput
              ? 'Generated video for this render clip.'
              : 'No generated video has been saved for this render clip yet.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRegenerateClip(clipId)}
            disabled={!canStartRender}
          >
            {pendingClipId === clipId ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : hasClipOutput ? (
              <RefreshCw className="h-3.5 w-3.5" />
            ) : (
              <Film className="h-3.5 w-3.5" />
            )}
            {hasClipOutput ? 'Regenerate Clip' : 'Generate Clip'}
          </Button>
          {videoHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={videoHref}>
                <Film className="h-3.5 w-3.5" />
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
      {isLoading && videoGroup && (
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
          {videoGroup
            ? 'Generated video media is missing for this clip.'
            : `Generate ${clipId} to create its render video.`}
        </div>
      )}
    </div>
  )
}

export function GeneratedVideoPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  renderClipPlanGroup,
  renderPromptGroup,
  renderPromptGroups = [],
  generatedVideoGroup,
  generatedVideoGroups = [],
  keyframeGroup,
}: GeneratedVideoPanelProps) {
  const hasSavedRenderOutput = renderPromptGroups.length > 0 || generatedVideoGroups.length > 0 || !!renderPromptGroup || !!generatedVideoGroup
  const savedMultiClipRender = generatedVideoGroups.length > 1 || renderPromptGroups.length > 1
  const sceneLevelRenderPromptGroup = renderPromptGroups.find(group => group.entity_id === sceneId)
    ?? (renderPromptGroup?.entity_id === sceneId ? renderPromptGroup : undefined)
  const sceneLevelGeneratedVideoGroup = generatedVideoGroups.find(group => group.entity_id === sceneId)
    ?? (generatedVideoGroup?.entity_id === sceneId ? generatedVideoGroup : undefined)
  const primaryRenderPromptGroup = savedMultiClipRender
    ? sceneLevelRenderPromptGroup
    : renderPromptGroup
  const primaryGeneratedVideoGroup = savedMultiClipRender
    ? sceneLevelGeneratedVideoGroup
    : generatedVideoGroup
  const { data: promptArtifact, isLoading: promptLoading } = useArtifact(
    projectId,
    'render_prompt',
    primaryRenderPromptGroup?.entity_id ?? sceneId,
    primaryRenderPromptGroup?.latest_version,
  )
  const { data: videoArtifact, isLoading: videoLoading } = useArtifact(
    projectId,
    'generated_video',
    primaryGeneratedVideoGroup?.entity_id ?? sceneId,
    primaryGeneratedVideoGroup?.latest_version,
  )
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
  const validationRef = primaryGeneratedVideoGroup?.health_details?.source_kind === 'media_validation'
    ? primaryGeneratedVideoGroup.health_details.source_artifact_ref
    : null
  const { data: validationArtifact, isLoading: validationLoading } = useArtifact(
    projectId,
    validationRef?.artifact_type,
    validationRef?.entity_id ?? undefined,
    validationRef?.version,
  )
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore(store => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const [scope, setScope] = useState<SceneScopeMode>('current_scene')
  const [pendingClipId, setPendingClipId] = useState<string | null>(null)
  const sceneScope = buildSceneScope(scope, sceneId)
  const { data: preflight } = useSceneActionPreflight(projectId, {
    recipe_id: 'render_generation',
    scene_scope: sceneScope,
  })

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const renderRunActive = hasActiveRun && runState?.state.recipe_id === 'render_generation'
  const anotherRunActive =
    hasActiveRun && !!runState && runState.state.recipe_id !== 'render_generation'
  const renderRunFailed =
    !!activeRunId && runState?.state.recipe_id === 'render_generation' && runHasFailed(runState)
  const failedAllScenesRun =
    renderRunFailed && runState?.state.runtime_params?.scene_scope?.mode === 'all_scenes'
  const renderStage = runState?.state.stages?.render
  const renderError = renderRunFailed
    ? runState?.background_error?.trim()
      || latestFailedAttemptError(renderStage?.attempts)
      || 'Scene render failed. Open run details for more information.'
    : null
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartRender = !!latestInputPath && !runBlocked && preflight?.status !== 'soft_block'
  const renderStartFrom = preflight?.start_from ?? undefined
  const renderReusesShotPlan = renderStartFrom === 'render'
  const promptData = promptArtifact?.payload?.data as Record<string, unknown> | undefined
  const videoData = videoArtifact?.payload?.data as Record<string, unknown> | undefined
  const shotPlanData = shotPlanArtifact?.payload?.data as Record<string, unknown> | undefined
  const renderClipPlanData = renderClipPlanArtifact?.payload?.data as Record<string, unknown> | undefined
  const plannedClipIds = plannedRenderClipIds(renderClipPlanData)
  const renderClipIds = plannedClipIds.length > 0
    ? plannedClipIds
    : savedRenderClipIds([...generatedVideoGroups, ...renderPromptGroups], sceneId)
  const isMultiClipRender = plannedClipIds.length > 1 || savedMultiClipRender
  const validationData = validationArtifact?.payload?.data as Record<string, unknown> | undefined
  const promptDetailHref = primaryRenderPromptGroup?.entity_id
    ? `/${projectId}/artifacts/render_prompt/${primaryRenderPromptGroup.entity_id}/${primaryRenderPromptGroup.latest_version}`
    : null
  const videoDetailHref = primaryGeneratedVideoGroup?.entity_id
    ? `/${projectId}/artifacts/generated_video/${primaryGeneratedVideoGroup.entity_id}/${primaryGeneratedVideoGroup.latest_version}`
    : null
  const validationDetailHref = validationRef?.entity_id && validationRef.version
    ? `/${projectId}/artifacts/${validationRef.artifact_type}/${validationRef.entity_id}/${validationRef.version}`
    : null
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)
  const runDetailHref = activeRunId ? `/${projectId}/runs/${activeRunId}` : null
  const currentSceneHasSavedOutput = !!(videoData || promptData || hasSavedRenderOutput)

  async function handleStartRender() {
    if (!latestInputPath) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'render_generation',
        accept_config: true,
        force: !!generatedVideoGroup || !!renderPromptGroup,
        start_from: renderStartFrom,
        scene_scope: sceneScope,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        hasSavedRenderOutput
          ? renderReusesShotPlan
            ? `Refreshing scene renders from the current shot plan for ${configuredScopeLabel.toLowerCase()}`
            : `Refreshing scene renders for ${configuredScopeLabel.toLowerCase()}`
          : renderReusesShotPlan
            ? `Started scene render generation from the current shot plan for ${configuredScopeLabel.toLowerCase()}`
            : `Started scene render generation for ${configuredScopeLabel.toLowerCase()}`,
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start scene render generation')
    }
  }

  async function handleStartRenderClip(clipId: string) {
    if (!latestInputPath) return
    setPendingClipId(clipId)
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'render_generation',
        accept_config: true,
        force: true,
        start_from: renderStartFrom,
        scene_scope: buildSceneScope('current_scene', sceneId),
        render_clip_ids: [clipId],
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(`Regenerating render clip ${clipId} for ${sceneHeading}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start render clip')
    } finally {
      setPendingClipId(null)
    }
  }

  const actionLabel = scope === 'current_scene'
    ? (hasSavedRenderOutput
      ? 'Refresh Render for Current Scene'
      : 'Run Render for Current Scene')
    : (hasSavedRenderOutput
      ? 'Refresh Scene Renders for All Scenes'
      : 'Run Scene Renders for All Scenes')

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Render</CardTitle>
                <Badge variant="outline">Selected: {configuredScopeLabel}</Badge>
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
                {keyframeGroup && (
                  <Badge variant="secondary">Keyframes v{keyframeGroup.latest_version}</Badge>
                )}
                {!isMultiClipRender && primaryRenderPromptGroup && (
                  <Badge variant="secondary">Prompt v{primaryRenderPromptGroup.latest_version}</Badge>
                )}
                {!isMultiClipRender && primaryGeneratedVideoGroup && (
                  <>
                    <Badge variant="secondary">Render v{primaryGeneratedVideoGroup.latest_version}</Badge>
                    <HealthBadge
                      health={primaryGeneratedVideoGroup.health}
                      details={primaryGeneratedVideoGroup.health_details}
                    />
                  </>
                )}
                {isMultiClipRender && (
                  <Badge variant="outline">{generatedVideoGroups.length} clips</Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Render compiles the current shot plan, concern-group direction, keyframes, and
                available references into provider-ready render prompts, then records which
                references became direct provider inputs versus prompt-only context before
                generating scene media. Stay depth-first on this scene when you want to test one
                moment quickly, or switch to all scenes when you want a broader pass. This tab
                always resolves back to the latest output for {sceneHeading}.
              </CardDescription>
            </div>

            <div className="flex flex-wrap gap-2">
              {!isMultiClipRender && promptDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={promptDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Prompt Detail
                  </Link>
                </Button>
              )}
              {!isMultiClipRender && videoDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={videoDetailHref}>
                    <Film className="h-3.5 w-3.5" />
                    Video Detail
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
                className="sm:self-start"
                onClick={handleStartRender}
                disabled={!canStartRender}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : hasSavedRenderOutput ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Film className="h-3.5 w-3.5" />
                )}
                {actionLabel}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              scene renders.
            </p>
          )}
          {renderRunActive && (
            <p>
              Scene render generation is currently running for {activeRunScopeLabel.toLowerCase()}.
              Stay here and this scene will refresh when the new prompt and render land.
            </p>
          )}
          {renderReusesShotPlan && (
            <p>
              Reuse path: CineForge will keep the current shot plan and rerun only render plus
              media validation.
            </p>
          )}
          <SceneActionControls
            scope={scope}
            onScopeChange={setScope}
            preflight={preflight}
            disabled={runBlocked}
          />
        </CardContent>
      </Card>

      {renderRunFailed && renderError && (
        <Card className="gap-0 border-destructive/40 bg-destructive/5">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive" />
            <div className="space-y-2">
              <div className="space-y-1">
                <p className="text-sm font-medium text-destructive">
                  {failedAllScenesRun ? 'All-scenes render run failed' : 'Scene render failed'}
                </p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {failedAllScenesRun
                    ? currentSceneHasSavedOutput
                      ? `${renderError} CineForge may already have saved successful outputs before the batch failed. This scene is showing the latest render artifacts that landed here; open Run Details to see which scenes still need another pass.`
                      : `${renderError} CineForge may still have saved outputs for other scenes before the batch failed. Open Run Details to inspect preserved artifacts and the failed scene list.`
                    : renderError}
                </p>
              </div>
              {runDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={runDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open Run Details
                  </Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <ScenePlanUnitSummary
        mode="render"
        sceneHeading={sceneHeading}
        shotPlanData={shotPlanData}
        renderClipPlanData={renderClipPlanData}
        currentOutputData={isMultiClipRender && generatedVideoGroups.length > 0 ? {} : videoData ?? promptData}
        generatedVideoCount={generatedVideoGroups.length}
      />

      {renderRunActive && (videoData || promptData) && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">
                Refreshing scene renders for {activeRunScopeLabel.toLowerCase()}
              </p>
              <p className="text-sm text-muted-foreground">
                You can keep reviewing the current prompt and render while CineForge rebuilds the
                next version in the background.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!videoData && !promptData && renderRunActive && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-amber-500/10 p-3">
              <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Scene render generation is running</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                CineForge is compiling render prompts and generating videos for {configuredScopeTarget}.
                When it finishes, this tab will load the latest result for {sceneHeading}.
              </p>
            </div>
          </div>
        </div>
      )}

      {!videoData && !promptData && !renderRunActive && !renderRunFailed && !hasSavedRenderOutput && !videoLoading && !promptLoading && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Film className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No scene render for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Render compiles the provider-ready prompt, stores it for audit, and generates the
                scene video for {configuredScopeTarget}. The resulting prompt and video artifacts
                keep the resolved reference usage visible so provider-input demotions stay honest.
                Use the scope controls above to widen or narrow the run.
              </p>
            </div>
            <Button onClick={handleStartRender} disabled={!canStartRender}>
              {startRun.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Film className="h-4 w-4" />
              )}
              {actionLabel}
            </Button>
          </div>
        </div>
      )}

      {(videoLoading || promptLoading) && hasSavedRenderOutput && !videoData && !promptData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {validationLoading && validationRef && !validationArtifact && (
        <div className="h-36 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {validationData && (
        <MediaValidationViewer
          data={validationData}
          projectId={projectId}
          compact
          detailHref={validationDetailHref}
        />
      )}

      {isMultiClipRender && (
        <Card className="gap-0">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Render Clips</CardTitle>
            <CardDescription>
              {plannedClipIds.length > 0
                ? `${sceneHeading} has ${generatedVideoGroups.length} of ${plannedClipIds.length} generated-video clips.`
                : `${sceneHeading} has ${generatedVideoGroups.length} generated-video clips.`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {renderClipIds.map(clipId => {
              const videoGroup = matchingRenderClipGroup(generatedVideoGroups, sceneId, clipId)
              const promptGroup = matchingRenderClipGroup(renderPromptGroups, sceneId, clipId)
              return (
                <RenderClipCard
                  key={`render-clip-${clipId}`}
                  projectId={projectId}
                  clipId={clipId}
                  videoGroup={videoGroup}
                  promptGroup={promptGroup}
                  canStartRender={canStartRender}
                  pendingClipId={pendingClipId}
                  onRegenerateClip={handleStartRenderClip}
                />
              )
            })}
          </CardContent>
        </Card>
      )}

      {!isMultiClipRender && videoData && <GeneratedVideoViewer data={videoData} projectId={projectId} />}
      {!isMultiClipRender && promptData && <RenderPromptViewer data={promptData} />}
    </div>
  )
}
