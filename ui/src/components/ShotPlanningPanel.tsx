import { Link } from 'react-router-dom'
import { Clapperboard, ExternalLink, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useArtifact, useProjectInputs, useRunState, useStartRun } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'
import { ShotPlanViewer } from '@/components/ShotPlanViewer'

type ShotPlanningPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
}

export function ShotPlanningPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
}: ShotPlanningPanelProps) {
  const { data: shotPlanArtifact, isLoading: artifactLoading } = useArtifact(
    projectId,
    'shot_plan',
    sceneId,
    shotPlanGroup?.latest_version,
  )
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = !!activeRunId && !runState?.state.finished_at
  const shotPlanningRunActive = hasActiveRun && runState?.state.recipe_id === 'shot_planning'
  const anotherRunActive = hasActiveRun && !!runState && runState.state.recipe_id !== 'shot_planning'
  const runBlocked = startRun.isPending || hasActiveRun

  const artifactData = shotPlanArtifact?.payload?.data as Record<string, unknown> | undefined
  const detailHref = shotPlanGroup
    ? `/${projectId}/artifacts/shot_plan/${sceneId}/${shotPlanGroup.latest_version}`
    : null

  async function handleStartShotPlanning() {
    if (!latestInputPath) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'shot_planning',
        accept_config: true,
        force: !!shotPlanGroup,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        shotPlanGroup
          ? 'Refreshing shot plans for all scenes'
          : 'Started shot planning for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start shot planning')
    }
  }

  const actionLabel = shotPlanGroup
    ? 'Refresh Shot Plans for All Scenes'
    : 'Run Shot Planning for All Scenes'

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Shot Planning</CardTitle>
                <Badge variant="outline">Runs for all scenes</Badge>
                {shotPlanGroup && <Badge variant="secondary">v{shotPlanGroup.latest_version}</Badge>}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Shot planning turns the current film-lane direction into a cuttable shot list.
                The existing recipe runs across every scene in the project, then this tab resolves
                back to the latest result for {sceneHeading}.
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
                onClick={handleStartShotPlanning}
                disabled={!latestInputPath || runBlocked}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : shotPlanGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Clapperboard className="h-3.5 w-3.5" />
                )}
                {actionLabel}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && (
            <p>No screenplay input is available for this project yet.</p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              shot planning.
            </p>
          )}
          {shotPlanningRunActive && (
            <p>
              Shot planning is currently running for all scenes. Stay here and this scene will
              refresh when the new shot plan lands.
            </p>
          )}
        </CardContent>
      </Card>

      {shotPlanningRunActive && artifactData && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Refreshing shot plans for all scenes</p>
              <p className="text-sm text-muted-foreground">
                You can keep reading this scene while the updated plan renders in place when the
                run finishes.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!artifactData && shotPlanningRunActive && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-amber-500/10 p-3">
              <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Shot planning is running</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                CineForge is building shot plans for every scene in the project. When it finishes,
                this tab will load the result for {sceneHeading} automatically.
              </p>
            </div>
          </div>
        </div>
      )}

      {!artifactData && !shotPlanningRunActive && !shotPlanGroup && !artifactLoading && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Clapperboard className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No shot plan for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Shot planning turns scene intent into ordered coverage, camera choices, and edit
                intent. Starting it here runs the existing project-wide recipe, then this tab
                resolves back to {sceneHeading}.
              </p>
            </div>
            <Button onClick={handleStartShotPlanning} disabled={!latestInputPath || runBlocked}>
              {startRun.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Clapperboard className="h-4 w-4" />
              )}
              {actionLabel}
            </Button>
          </div>
        </div>
      )}

      {artifactLoading && shotPlanGroup && !artifactData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {!artifactLoading && shotPlanGroup && !artifactData && !shotPlanningRunActive && (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-muted-foreground">
              CineForge found a shot-plan artifact for this scene, but it could not be loaded into
              the viewer.
            </p>
          </CardContent>
        </Card>
      )}

      {artifactData && <ShotPlanViewer data={artifactData} />}
    </div>
  )
}
