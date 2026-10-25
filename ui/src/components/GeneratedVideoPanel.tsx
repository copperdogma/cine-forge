import { RenderClipCard } from '@/components/RenderClipCard'
import { useRef } from 'react'
import { MediaGenerationControls } from '@/components/MediaGenerationControls'
import type { MediaGenerationControlsHandle } from '@/components/MediaGenerationControls'
import { Link } from 'react-router-dom'
import { AlertCircle, ExternalLink, Film, Loader2 } from 'lucide-react'
import { GeneratedVideoViewer } from '@/components/GeneratedVideoViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { RenderPromptViewer } from '@/components/RenderPromptViewer'
import { ScenePlanUnitSummary } from '@/components/ScenePlanUnitSummary'
import { asArray, asRecord, asString } from '@/components/render-utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  isRunActive,
  runHasFailed,
  useArtifact,
  useRunState,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'
import { getSceneScopeLabel } from '@/lib/constants'

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
  const activeRunId = useChatStore(store => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const controlsRef = useRef<MediaGenerationControlsHandle>(null)
  const hasActiveRun = isRunActive(activeRunId, runState)
  const renderRunActive = hasActiveRun && runState?.state.recipe_id === 'render_generation'
    && runState.state.runtime_params.end_at !== 'render_clip_planning'
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
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)
  const runDetailHref = activeRunId ? `/${projectId}/runs/${activeRunId}` : null
  const currentSceneHasSavedOutput = !!(videoData || promptData || hasSavedRenderOutput)

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Render</CardTitle>
                <Badge variant="outline">Current scene</Badge>
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
                Render turns the current shot plan, direction, and references into scene video.
                Keyframes are optional: it can proceed without them and uses locked frames when
                available. Prompt and video details show how references were used. Inspect the clip
                plan below before confirming video generation for this scene.
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

            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
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
        </CardContent>
      </Card>

      <MediaGenerationControls key={`${projectId}-${sceneId}`} ref={controlsRef} projectId={projectId} sceneId={sceneId} recipeId="render_generation" />

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
                CineForge is compiling render prompts and generating videos for this scene.
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
                scene video for this scene. The resulting prompt and video artifacts
                keep the resolved reference usage visible so provider-input demotions stay honest.
                Prepare and inspect the clips above, then confirm the selected work.
              </p>
            </div>

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
                  canStartRender={!hasActiveRun}
                  pendingClipId={null}
                  onRegenerateClip={clipId => controlsRef.current?.selectClip(clipId)}
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
