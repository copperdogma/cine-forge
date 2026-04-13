import { Link } from 'react-router-dom'
import { AlertCircle, ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  asArray,
  asNumber,
  asRecord,
  asString,
  formatDuration,
} from '@/components/render-utils'
import {
  isRunActive,
  runHasFailed,
  useArtifact,
  useRunState,
  useStartRun,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'

type FinalOutputCardProps = {
  projectId: string
  latestInputPath: string | null
  artifactGroups?: ArtifactGroupSummary[]
  sceneCount: number
}

type FinalOutputSummary = {
  coverageState: string | null
  includedCount: number
  omittedCount: number
  durationSeconds: number | null
}

function parseSummary(data: Record<string, unknown> | undefined): FinalOutputSummary | null {
  if (!data) return null
  return {
    coverageState: asString(data.coverage_state),
    includedCount: asArray(data.included_scenes).length,
    omittedCount: asArray(data.omitted_scenes).length,
    durationSeconds: asNumber(asRecord(data.video)?.duration_seconds),
  }
}

function coverageLabel(state: string | null): string {
  if (state === 'complete') return 'Complete Coverage'
  if (state === 'partial') return 'Partial Coverage'
  return 'No Final Output Yet'
}

export function FinalOutputCard({
  projectId,
  latestInputPath,
  artifactGroups,
  sceneCount,
}: FinalOutputCardProps) {
  const finalOutputGroup = artifactGroups?.find(group => group.artifact_type === 'final_output')
  const finalOutputEntityId = finalOutputGroup?.entity_id ?? 'project'
  const renderedSceneCount = artifactGroups?.filter(group => group.artifact_type === 'generated_video').length ?? 0
  const { data: finalOutputArtifact } = useArtifact(
    projectId,
    'final_output',
    finalOutputEntityId,
    finalOutputGroup?.latest_version,
  )
  const startRun = useStartRun()
  const activeRunId = useChatStore(store => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  const hasActiveRun = isRunActive(activeRunId, runState)
  const finalOutputRunActive = hasActiveRun && runState?.state.recipe_id === 'final_output'
  const anotherRunActive = hasActiveRun && !!runState && runState.state.recipe_id !== 'final_output'
  const finalOutputRunFailed =
    !!activeRunId && runState?.state.recipe_id === 'final_output' && runHasFailed(runState)
  const finalOutputError = finalOutputRunFailed
    ? runState?.background_error ?? 'Final output assembly failed. Open run details for more information.'
    : null
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartFinalOutput =
    !!latestInputPath && renderedSceneCount > 0 && sceneCount > 0 && !runBlocked

  const finalOutputData = finalOutputArtifact?.payload?.data as Record<string, unknown> | undefined
  const summary = parseSummary(finalOutputData)
  const detailHref = finalOutputGroup
    ? `/${projectId}/artifacts/final_output/${finalOutputEntityId}/${finalOutputGroup.latest_version}`
    : null
  const runDetailHref = activeRunId ? `/${projectId}/run/${activeRunId}` : null

  async function handleStartFinalOutput() {
    if (!latestInputPath) return

    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'final_output',
        accept_config: true,
        force: !!finalOutputGroup,
      })

      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        finalOutputGroup
          ? 'Refreshing the project final output from current scene renders'
          : 'Started assembling the project final output',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start final output assembly')
    }
  }

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Final Output</CardTitle>
                <Badge variant={summary?.coverageState === 'complete' ? 'secondary' : 'outline'}>
                  {coverageLabel(summary?.coverageState ?? null)}
                </Badge>
                {finalOutputGroup && <Badge variant="secondary">v{finalOutputGroup.latest_version}</Badge>}
                <Badge variant="outline">
                  {renderedSceneCount}/{sceneCount} scenes rendered
                </Badge>
                {formatDuration(summary?.durationSeconds ?? null) && (
                  <Badge variant="outline">{formatDuration(summary?.durationSeconds ?? null)}</Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Assemble a project-level playable cut from the current generated scene renders.
                This first slice stays honest: it never swaps in storyboards or previz when a
                scene is missing from the rendered cut.
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
                onClick={handleStartFinalOutput}
                disabled={!canStartFinalOutput}
              >
                {startRun.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : finalOutputGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Film className="h-3.5 w-3.5" />
                )}
                {finalOutputGroup ? 'Refresh Final Output' : 'Assemble Final Output'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {sceneCount === 0 && (
            <p>Scene extraction has not produced a timeline for this project yet.</p>
          )}
          {renderedSceneCount === 0 && sceneCount > 0 && (
            <p>
              Final Output needs at least one generated scene render before CineForge can assemble
              a project cut.
            </p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before assembling
              the project cut.
            </p>
          )}
          {finalOutputRunActive && (
            <p>
              Final Output assembly is running now. This card will refresh when the new cut lands.
            </p>
          )}
          {summary && (
            <p>
              {summary.coverageState === 'complete'
                ? `The current cut includes all ${summary.includedCount} rendered scenes in timeline order.`
                : `The current cut includes ${summary.includedCount} scene${summary.includedCount === 1 ? '' : 's'} and explicitly omits ${summary.omittedCount} scene${summary.omittedCount === 1 ? '' : 's'} that still lack render coverage.`}
            </p>
          )}
          {!summary && renderedSceneCount > 0 && !finalOutputRunActive && (
            <p>
              CineForge has enough rendered scene media to assemble the first project cut. Start
              Final Output when you want one playable artifact instead of scene-by-scene review.
            </p>
          )}
        </CardContent>
      </Card>

      {finalOutputRunFailed && finalOutputError && (
        <Card className="gap-0 border-destructive/40 bg-destructive/5">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive" />
            <div className="space-y-2">
              <div className="space-y-1">
                <p className="text-sm font-medium text-destructive">Final output assembly failed</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {finalOutputError}
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
    </div>
  )
}
