import { Link } from 'react-router-dom'
import { Clapperboard, ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AnimaticViewer } from '@/components/AnimaticViewer'
import { KeyframeViewer } from '@/components/KeyframeViewer'
import { useArtifact, useProjectInputs, useRunState, useStartRun } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'

type AnimaticsPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  storyboardGroup?: ArtifactGroupSummary
  animaticGroup?: ArtifactGroupSummary
  keyframeGroup?: ArtifactGroupSummary
  previzGroup?: ArtifactGroupSummary
}

export function AnimaticsPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  storyboardGroup,
  animaticGroup,
  keyframeGroup,
  previzGroup,
}: AnimaticsPanelProps) {
  const { data: animaticArtifact, isLoading: animaticLoading } = useArtifact(
    projectId,
    'animatic',
    sceneId,
    animaticGroup?.latest_version,
  )
  const { data: keyframeArtifact, isLoading: keyframeLoading } = useArtifact(
    projectId,
    'keyframe',
    sceneId,
    keyframeGroup?.latest_version,
  )
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = !!activeRunId && !runState?.state.finished_at
  const animaticsRunActive = hasActiveRun && runState?.state.recipe_id === 'animatics_generation'
  const anotherRunActive =
    hasActiveRun && !!runState && runState.state.recipe_id !== 'animatics_generation'
  const canStart = !!latestInputPath && !!shotPlanGroup && !hasActiveRun

  const animaticData = animaticArtifact?.payload?.data as Record<string, unknown> | undefined
  const keyframeData = keyframeArtifact?.payload?.data as Record<string, unknown> | undefined
  const animaticDetailHref = animaticGroup
    ? `/${projectId}/artifacts/animatic/${sceneId}/${animaticGroup.latest_version}`
    : null
  const keyframeDetailHref = keyframeGroup
    ? `/${projectId}/artifacts/keyframe/${sceneId}/${keyframeGroup.latest_version}`
    : null
  const previzDetailHref = previzGroup
    ? `/${projectId}/artifacts/previz_reel/${previzGroup.entity_id ?? 'project'}/${previzGroup.latest_version}`
    : null

  async function handleStartAnimatics() {
    if (!latestInputPath || !shotPlanGroup) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'animatics_generation',
        accept_config: true,
        force: !!animaticGroup || !!keyframeGroup,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        animaticGroup || keyframeGroup
          ? 'Refreshing animatics and keyframes for all scenes'
          : 'Started animatics generation for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start animatics generation')
    }
  }

  const actionLabel = animaticGroup || keyframeGroup
    ? 'Refresh Animatics for All Scenes'
    : 'Run Animatics for All Scenes'

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Animatics</CardTitle>
                <Badge variant="outline">Runs for all scenes</Badge>
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
                {storyboardGroup && (
                  <Badge variant="secondary">Storyboard-informed</Badge>
                )}
                {animaticGroup && <Badge variant="secondary">Animatic v{animaticGroup.latest_version}</Badge>}
                {keyframeGroup && <Badge variant="secondary">Keyframes v{keyframeGroup.latest_version}</Badge>}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Animatics turn the current shot plan into a playable rough cut with timing,
                lightweight motion, and temp audio when available. The recipe runs across every
                scene in the project, then this tab resolves back to the latest result for {sceneHeading}.
              </CardDescription>
            </div>

            <div className="flex flex-wrap gap-2">
              {animaticDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={animaticDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Animatic Detail
                  </Link>
                </Button>
              )}
              {keyframeDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={keyframeDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Keyframe Detail
                  </Link>
                </Button>
              )}
              {previzDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={previzDetailHref}>
                    <Film className="h-3.5 w-3.5" />
                    Open Previz Reel
                  </Link>
                </Button>
              )}
              <Button
                size="sm"
                className="sm:self-start"
                onClick={handleStartAnimatics}
                disabled={!canStart || startRun.isPending}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : animaticGroup || keyframeGroup ? (
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
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {!shotPlanGroup && (
            <p>
              Animatics depend on shot plans. Open the <span className="font-medium">Shots</span>{' '}
              tab first and generate coverage for this scene before running animatics.
            </p>
          )}
          {!storyboardGroup && !!shotPlanGroup && (
            <p>
              Storyboards are optional here. CineForge will fall back to generated placeholder stills
              for any shots that do not already have storyboard frames.
            </p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              animatics generation.
            </p>
          )}
          {animaticsRunActive && (
            <p>
              Animatics generation is currently running for all scenes. Stay here and this scene
              will refresh when the new animatic and keyframes land.
            </p>
          )}
        </CardContent>
      </Card>

      {animaticsRunActive && (animaticData || keyframeData) && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Refreshing animatics and keyframes for all scenes</p>
              <p className="text-sm text-muted-foreground">
                You can keep reviewing the current rough cut while CineForge rebuilds the latest
                version in the background.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!animaticData && !animaticsRunActive && !animaticGroup && !animaticLoading && !!shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Clapperboard className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No animatic for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                This run creates a playable rough cut, then derives lockable keyframes for the same
                scene. Starting it here runs the project-wide recipe and resolves back to {sceneHeading}.
              </p>
            </div>
            <Button onClick={handleStartAnimatics} disabled={!canStart || startRun.isPending}>
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

      {(animaticLoading || keyframeLoading) && (animaticGroup || keyframeGroup) && !animaticData && !keyframeData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {animaticData && <AnimaticViewer data={animaticData} projectId={projectId} />}
      {keyframeData && (
        <KeyframeViewer
          data={keyframeData}
          projectId={projectId}
          entityId={sceneId}
          editable
        />
      )}
    </div>
  )
}
