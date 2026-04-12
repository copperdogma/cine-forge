import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { GeneratedVideoViewer } from '@/components/GeneratedVideoViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { RenderPromptViewer } from '@/components/RenderPromptViewer'
import { SceneActionControls } from '@/components/SceneActionControls'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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

type GeneratedVideoPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  renderPromptGroup?: ArtifactGroupSummary
  generatedVideoGroup?: ArtifactGroupSummary
  keyframeGroup?: ArtifactGroupSummary
}

export function GeneratedVideoPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  renderPromptGroup,
  generatedVideoGroup,
  keyframeGroup,
}: GeneratedVideoPanelProps) {
  const { data: promptArtifact, isLoading: promptLoading } = useArtifact(
    projectId,
    'render_prompt',
    sceneId,
    renderPromptGroup?.latest_version,
  )
  const { data: videoArtifact, isLoading: videoLoading } = useArtifact(
    projectId,
    'generated_video',
    sceneId,
    generatedVideoGroup?.latest_version,
  )
  const validationRef = generatedVideoGroup?.health_details?.source_kind === 'media_validation'
    ? generatedVideoGroup.health_details.source_artifact_ref
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
  const renderStage = runState?.state.stages?.render
  const renderError = renderRunFailed
    ? runState?.background_error?.trim()
      || latestFailedAttemptError(renderStage?.attempts)
      || 'Scene render failed. Open run details for more information.'
    : null
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartRender = !!latestInputPath && !runBlocked && preflight?.status !== 'soft_block'
  const promptData = promptArtifact?.payload?.data as Record<string, unknown> | undefined
  const videoData = videoArtifact?.payload?.data as Record<string, unknown> | undefined
  const validationData = validationArtifact?.payload?.data as Record<string, unknown> | undefined
  const promptDetailHref = renderPromptGroup
    ? `/${projectId}/artifacts/render_prompt/${sceneId}/${renderPromptGroup.latest_version}`
    : null
  const videoDetailHref = generatedVideoGroup
    ? `/${projectId}/artifacts/generated_video/${sceneId}/${generatedVideoGroup.latest_version}`
    : null
  const validationDetailHref = validationRef?.entity_id && validationRef.version
    ? `/${projectId}/artifacts/${validationRef.artifact_type}/${validationRef.entity_id}/${validationRef.version}`
    : null
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)
  const runDetailHref = activeRunId ? `/${projectId}/run/${activeRunId}` : null

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
        scene_scope: sceneScope,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        generatedVideoGroup || renderPromptGroup
          ? `Refreshing scene renders for ${configuredScopeLabel.toLowerCase()}`
          : `Started scene render generation for ${configuredScopeLabel.toLowerCase()}`,
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start scene render generation')
    }
  }

  const actionLabel = scope === 'current_scene'
    ? (generatedVideoGroup || renderPromptGroup
      ? 'Refresh Render for Current Scene'
      : 'Run Render for Current Scene')
    : (generatedVideoGroup || renderPromptGroup
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
                {renderPromptGroup && (
                  <Badge variant="secondary">Prompt v{renderPromptGroup.latest_version}</Badge>
                )}
                {generatedVideoGroup && (
                  <>
                    <Badge variant="secondary">Render v{generatedVideoGroup.latest_version}</Badge>
                    <HealthBadge
                      health={generatedVideoGroup.health}
                      details={generatedVideoGroup.health_details}
                    />
                  </>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Render compiles the current shot plan, concern-group direction, keyframes, and
                approved references into one provider-ready prompt, then generates a scene video.
                Stay depth-first on this scene when you want to test one moment quickly, or switch
                to all scenes when you want a broader pass. This tab always resolves back to the
                latest output for {sceneHeading}.
              </CardDescription>
            </div>

            <div className="flex flex-wrap gap-2">
              {promptDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={promptDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Prompt Detail
                  </Link>
                </Button>
              )}
              {videoDetailHref && (
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
                ) : generatedVideoGroup || renderPromptGroup ? (
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
                <p className="text-sm font-medium text-destructive">Scene render failed</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {renderError}
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

      {!videoData && !promptData && !renderRunActive && !renderRunFailed && !generatedVideoGroup && !renderPromptGroup && !videoLoading && !promptLoading && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Film className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No scene render for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Render compiles the provider-ready prompt, stores it for audit, and generates the
                scene video for {configuredScopeTarget}. Use the scope controls above to widen or
                narrow the run.
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

      {(videoLoading || promptLoading) && (generatedVideoGroup || renderPromptGroup) && !videoData && !promptData && (
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

      {videoData && <GeneratedVideoViewer data={videoData} projectId={projectId} />}
      {promptData && <RenderPromptViewer data={promptData} />}
    </div>
  )
}
