import { Link } from 'react-router-dom'
import { ExternalLink, Image as ImageIcon, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { StoryboardViewer } from '@/components/StoryboardViewer'
import { isRunActive, useArtifact, useProjectInputs, useRunState, useStartRun } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'

type StoryboardPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  storyboardGroup?: ArtifactGroupSummary
  shotPlanGroup?: ArtifactGroupSummary
}

export function StoryboardPanel({
  projectId,
  sceneId,
  sceneHeading,
  storyboardGroup,
  shotPlanGroup,
}: StoryboardPanelProps) {
  const { data: storyboardArtifact, isLoading: artifactLoading } = useArtifact(
    projectId,
    'storyboard',
    sceneId,
    storyboardGroup?.latest_version,
  )
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const storyboardRunActive = hasActiveRun && runState?.state.recipe_id === 'storyboard_generation'
  const anotherRunActive =
    hasActiveRun && !!runState && runState.state.recipe_id !== 'storyboard_generation'
  const canStartStoryboard = !!latestInputPath && !!shotPlanGroup && !hasActiveRun
  const artifactData = storyboardArtifact?.payload?.data as Record<string, unknown> | undefined
  const detailHref = storyboardGroup
    ? `/${projectId}/artifacts/storyboard/${sceneId}/${storyboardGroup.latest_version}`
    : null

  async function handleStartStoryboard() {
    if (!latestInputPath || !shotPlanGroup) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'storyboard_generation',
        accept_config: true,
        force: !!storyboardGroup,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        storyboardGroup
          ? 'Refreshing storyboards for all scenes'
          : 'Started storyboard generation for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start storyboard generation')
    }
  }

  const actionLabel = storyboardGroup
    ? 'Refresh Storyboards for All Scenes'
    : 'Run Storyboards for All Scenes'

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Storyboard</CardTitle>
                <Badge variant="outline">Runs for all scenes</Badge>
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
                {storyboardGroup && (
                  <Badge variant="secondary">v{storyboardGroup.latest_version}</Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Storyboards turn the current shot plan into a fast visual review pass. The recipe
                runs across every scene in the project, then this tab resolves back to the latest
                storyboard for {sceneHeading}.
              </CardDescription>
            </div>

            <div className="flex flex-wrap gap-2">
              {detailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={detailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open Artifact Detail
                  </Link>
                </Button>
              )}
              <Button
                size="sm"
                className="sm:self-start"
                onClick={handleStartStoryboard}
                disabled={!canStartStoryboard || startRun.isPending}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : storyboardGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <ImageIcon className="h-3.5 w-3.5" />
                )}
                {actionLabel}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {!shotPlanGroup && (
            <p>
              Storyboards depend on shot plans. Open the <span className="font-medium">Shots</span>{' '}
              tab first and generate coverage for this scene before running storyboards.
            </p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              storyboard generation.
            </p>
          )}
          {storyboardRunActive && (
            <p>
              Storyboard generation is currently running for all scenes. Stay here and this scene
              will refresh when the new storyboard lands.
            </p>
          )}
        </CardContent>
      </Card>

      {storyboardRunActive && artifactData && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Refreshing storyboards for all scenes</p>
              <p className="text-sm text-muted-foreground">
                You can keep reviewing this scene while updated storyboard frames render in place
                when the run finishes.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!artifactData && storyboardRunActive && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-amber-500/10 p-3">
              <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Storyboard generation is running</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                CineForge is generating storyboard frames for every scene in the project. When it
                finishes, this tab will load the result for {sceneHeading} automatically.
              </p>
            </div>
          </div>
        </div>
      )}

      {!artifactData && !storyboardRunActive && !storyboardGroup && !artifactLoading && !shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <ImageIcon className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Storyboard needs a shot plan first</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                This scene does not have a shot plan yet, so CineForge has nothing to visualize.
                Generate shots first, then come back here for storyboard frames.
              </p>
            </div>
          </div>
        </div>
      )}

      {!artifactData && !storyboardRunActive && !storyboardGroup && !artifactLoading && !!shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <ImageIcon className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No storyboard for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Storyboards provide a quick visual pass over blocking, eyelines, and camera intent.
                Starting it here runs the existing project-wide recipe, then this tab resolves back
                to {sceneHeading}.
              </p>
            </div>
            <Button onClick={handleStartStoryboard} disabled={!canStartStoryboard || startRun.isPending}>
              {startRun.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ImageIcon className="h-4 w-4" />
              )}
              {actionLabel}
            </Button>
          </div>
        </div>
      )}

      {artifactLoading && storyboardGroup && !artifactData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {!artifactLoading && storyboardGroup && !artifactData && !storyboardRunActive && (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-muted-foreground">
              CineForge found a storyboard artifact for this scene, but it could not be loaded into
              the viewer.
            </p>
          </CardContent>
        </Card>
      )}

      {artifactData && <StoryboardViewer data={artifactData} projectId={projectId} />}
    </div>
  )
}
