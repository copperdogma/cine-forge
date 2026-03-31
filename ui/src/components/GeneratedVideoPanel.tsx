import { Link } from 'react-router-dom'
import { ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { GeneratedVideoViewer } from '@/components/GeneratedVideoViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { RenderPromptViewer } from '@/components/RenderPromptViewer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { isRunActive, useArtifact, useProjectInputs, useRunState, useStartRun } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'

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

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const renderRunActive = hasActiveRun && runState?.state.recipe_id === 'render_generation'
  const anotherRunActive =
    hasActiveRun && !!runState && runState.state.recipe_id !== 'render_generation'
  const canStartRender = !!latestInputPath && !!shotPlanGroup && !hasActiveRun
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

  async function handleStartRender() {
    if (!latestInputPath || !shotPlanGroup) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'render_generation',
        accept_config: true,
        force: !!generatedVideoGroup || !!renderPromptGroup,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        generatedVideoGroup || renderPromptGroup
          ? 'Refreshing scene renders for all scenes'
          : 'Started scene render generation for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start scene render generation')
    }
  }

  const actionLabel = generatedVideoGroup || renderPromptGroup
    ? 'Refresh Scene Renders'
    : 'Run Scene Renders'

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Render</CardTitle>
                <Badge variant="outline">Runs for all scenes</Badge>
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
                The recipe runs across every scene in the project and resolves back to the latest
                output for {sceneHeading}.
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
                disabled={!canStartRender || startRun.isPending}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : generatedVideoGroup || renderPromptGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Film className="h-3.5 w-3.5" />
                )}
                {actionLabel} for All Scenes
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {!shotPlanGroup && (
            <p>
              Render depends on shot planning. Open the <span className="font-medium">Shots</span>{' '}
              tab first and generate coverage for this scene before starting scene renders.
            </p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              scene renders.
            </p>
          )}
          {renderRunActive && (
            <p>
              Scene render generation is currently running for all scenes. Stay here and this scene
              will refresh when the new prompt and render land.
            </p>
          )}
        </CardContent>
      </Card>

      {renderRunActive && (videoData || promptData) && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Refreshing scene renders for all scenes</p>
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
                CineForge is compiling render prompts and generating videos for every scene in the
                project. When it finishes, this tab will load the latest result for {sceneHeading}.
              </p>
            </div>
          </div>
        </div>
      )}

      {!videoData && !promptData && !renderRunActive && !generatedVideoGroup && !renderPromptGroup && !videoLoading && !promptLoading && !shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Film className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Render needs a shot plan first</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                This scene does not have a shot plan yet, so CineForge has no coverage plan to turn
                into a render. Generate shots first, then come back here for the compiled prompt and
                scene video.
              </p>
            </div>
          </div>
        </div>
      )}

      {!videoData && !promptData && !renderRunActive && !generatedVideoGroup && !renderPromptGroup && !videoLoading && !promptLoading && !!shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Film className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No scene render for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Starting render here runs the current project-wide recipe, stores the compiled
                provider-ready prompt for audit, and resolves back to the generated video for {sceneHeading}.
              </p>
            </div>
            <Button onClick={handleStartRender} disabled={!canStartRender || startRun.isPending}>
              {startRun.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Film className="h-4 w-4" />
              )}
              {actionLabel} for All Scenes
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
