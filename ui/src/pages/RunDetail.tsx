import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useHistoryBack } from '@/lib/use-history-back'
import {
  Loader2,
  ArrowLeft,
  Package,
  AlertCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RunCostSummaryPanel } from '@/components/RunCostSummaryPanel'
import { RunDetailHeader, RunDetailMetrics } from '@/components/RunDetailOverview'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { RunEventLog, type RunEvent } from '@/components/RunEventLog'
import { ErrorState } from '@/components/StateViews'
import { cn } from '@/lib/utils'
import type { SceneActionPreflight, SceneExecutionScope, StageState } from '@/lib/types'
import {
  useRetryFailedStage,
  useResumeRun,
  useRunCosts,
  useRunEvents,
  useRunState,
} from '@/lib/hooks'
import { getOrderedStageIds, getSceneScopeLabel, getSceneScopeTargetLabel } from '@/lib/constants'
import { toast } from 'sonner'
import { formatDuration } from '@/lib/format'
import { StatusIcon } from '@/components/StatusBadge'
import { humanizeStageName } from '@/lib/chat-messages'

// Derive overall status from stage states
function getOverallStatus(stages: Record<string, StageState>, stageOrder?: string[]): string {
  const stageIds = getOrderedStageIds(Object.keys(stages), stageOrder)
  const stagesList = stageIds.map((stageId) => stages[stageId]).filter(Boolean)
  if (stagesList.some(s => s.status === 'failed')) return 'failed'
  if (stagesList.some(s => s.status === 'running')) return 'running'
  if (stagesList.every(s => s.status === 'done' || s.status === 'skipped_reused')) return 'done'
  if (stagesList.some(s => s.status === 'paused')) return 'paused'
  return 'pending'
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>

      {/* Summary cards skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-16 mb-2" />
              <Skeleton className="h-6 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Stages skeleton */}
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="py-0 px-0">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i}>
              <div className="flex items-center gap-3 px-4 py-3">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-32 flex-1" />
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-12" />
              </div>
              {i < 4 && <Separator />}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

// Helper to map API events to RunEvent format
function mapApiEventsToRunEvents(apiEvents: Array<Record<string, unknown>>): RunEvent[] {
  const eventTypeMap: Record<string, RunEvent['type']> = {
    stage_started: 'stage_start',
    stage_finished: 'stage_end',
    stage_failed: 'error',
    stage_retrying: 'warning',
    stage_fallback: 'warning',
    stage_paused: 'warning',
    budget_warning: 'warning',
  }
  return apiEvents.map((event) => {
    const backendEvent = (event.event as string) ?? ''
    const stageId = (event.stage as string) ?? (event.stage_id as string) ?? undefined
    let message = (event.message as string) || JSON.stringify(event)
    if (backendEvent === 'stage_retrying') {
      const delay = typeof event.retry_delay_seconds === 'number'
        ? ` in ~${event.retry_delay_seconds.toFixed(1)}s`
        : ''
      message = `Retrying ${stageId ?? 'stage'} after transient failure${delay}`
    } else if (backendEvent === 'stage_fallback') {
      message = `Fallback model selected: ${(event.to_model as string) ?? 'unknown'}`
    } else if (backendEvent === 'stage_failed') {
      message = (event.error as string) || `Stage ${stageId ?? ''} failed`
    } else if (backendEvent === 'budget_warning') {
      const scope = (event.budget_scope as string) ?? 'budget'
      message = (event.reason as string) ?? `${scope} budget warning`
    }
    return {
      timestamp:
        typeof event.ts === 'number'
          ? event.ts * 1000
          : typeof event.timestamp === 'number'
            ? event.timestamp * 1000
            : Date.now(),
      type: eventTypeMap[backendEvent] ?? ((event.type as RunEvent['type']) || 'info'),
      stage: stageId,
      message,
      details: event.details as Record<string, unknown> | undefined,
    }
  })
}

function readSceneScope(value: unknown): SceneExecutionScope | null {
  if (!value || typeof value !== 'object') return null
  const maybeScope = value as Partial<SceneExecutionScope>
  if (maybeScope.mode !== 'all_scenes' && maybeScope.mode !== 'current_scene') {
    return null
  }
  return {
    mode: maybeScope.mode,
    scene_ids: Array.isArray(maybeScope.scene_ids)
      ? maybeScope.scene_ids.filter((item): item is string => typeof item === 'string')
      : [],
  }
}

function readSceneActionPreflight(value: unknown): SceneActionPreflight | null {
  if (!value || typeof value !== 'object') return null
  const maybePreflight = value as Partial<SceneActionPreflight>
  if (
    maybePreflight.status !== 'ready'
    && maybePreflight.status !== 'warn'
    && maybePreflight.status !== 'soft_block'
  ) {
    return null
  }
  return {
    recipe_id: typeof maybePreflight.recipe_id === 'string' ? maybePreflight.recipe_id : 'unknown',
    recipe_name: typeof maybePreflight.recipe_name === 'string' ? maybePreflight.recipe_name : 'Scene Action',
    start_from: typeof maybePreflight.start_from === 'string' ? maybePreflight.start_from : null,
    end_at: typeof maybePreflight.end_at === 'string' ? maybePreflight.end_at : null,
    scene_scope: readSceneScope(maybePreflight.scene_scope) ?? { mode: 'all_scenes', scene_ids: [] },
    status: maybePreflight.status,
    summary: typeof maybePreflight.summary === 'string' ? maybePreflight.summary : '',
    items: Array.isArray(maybePreflight.items)
      ? maybePreflight.items.filter(
          (item): item is SceneActionPreflight['items'][number] =>
            !!item
            && typeof item === 'object'
            && typeof (item as { label?: unknown }).label === 'string'
            && typeof (item as { detail?: unknown }).detail === 'string'
            && ['warning', 'auto_build', 'soft_block'].includes(
              String((item as { kind?: unknown }).kind),
            ),
        )
      : [],
  }
}

export default function RunDetail() {
  const { projectId, runId } = useParams()
  const navigate = useNavigate()
  const goBack = useHistoryBack(`/${projectId}/runs`)

  const { data: runCostSummary } = useRunCosts(runId)
  const { data: runStateResponse, isLoading, error, refetch } = useRunState(runId)
  const { data: eventsResponse, isLoading: eventsLoading } = useRunEvents(runId, !!runStateResponse?.state?.finished_at)
  const retryFailedStage = useRetryFailedStage()
  const resumeRun = useResumeRun()

  // Derive running state (safe even when data is undefined)
  const overallStatus = runStateResponse
    ? getOverallStatus(
        runStateResponse.state.stages,
        runStateResponse.state.stage_order as string[] | undefined,
      )
    : 'pending'
  const isRunning = overallStatus === 'running'

  // Live-ticking duration: ticks every second while running
  // Must be above early returns to satisfy Rules of Hooks
  const [now, setNow] = useState(() => Date.now() / 1000)
  useEffect(() => {
    if (!isRunning) return
    const id = setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => clearInterval(id)
  }, [isRunning])

  if (isLoading) {
    return <DetailSkeleton />
  }

  if (error) {
    return (
      <div>
        <Button
          variant="ghost"
          size="sm"
          className="mb-4"
          onClick={goBack}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <ErrorState
          message="Failed to load run details"
          hint={error?.message}
          onRetry={() => {
            refetch()
          }}
        />
      </div>
    )
  }

  if (!runStateResponse) {
    return (
      <ErrorState
        message="Run not found"
        hint={`No run state found for ${runId}`}
      />
    )
  }

  const runState = runStateResponse

  const { state } = runState
  const sceneScope = readSceneScope(state.runtime_params.scene_scope)
  const sceneActionPreflight = readSceneActionPreflight(state.runtime_params.scene_action_preflight)
  const startFrom = typeof state.runtime_params.start_from === 'string'
    ? state.runtime_params.start_from
    : sceneActionPreflight?.start_from ?? null
  const endAt = typeof state.runtime_params.end_at === 'string'
    ? state.runtime_params.end_at
    : sceneActionPreflight?.end_at ?? null
  const scopeLabel = getSceneScopeLabel(sceneScope)
  const scopeTargetLabel = getSceneScopeTargetLabel(sceneScope)
  const orderedStageIds = getOrderedStageIds(
    Object.keys(state.stages),
    state.stage_order as string[] | undefined,
  )
  const stageOrderSummary = orderedStageIds.join(', ')

  const duration = state.finished_at && state.started_at
    ? state.finished_at - state.started_at
    : state.started_at
      ? now - state.started_at
      : 0

  const stageEntries = orderedStageIds
    .map((stageId) => [stageId, state.stages[stageId]] as const)
    .sort(([, a], [, b]) => {
    // Sort by started_at ascending; stages that haven't started go last
    const aTime = a.started_at ?? Infinity
    const bTime = b.started_at ?? Infinity
    return aTime - bTime
  })
  const completedStages = stageEntries.filter(([, s]) => s.status === 'done' || s.status === 'skipped_reused').length
  const totalStages = stageEntries.length

  // Collect all artifacts
  const allArtifacts = stageEntries.flatMap(([stageName, stage]) =>
    stage.artifact_refs.map(ref => ({
      artifact_type: ref.artifact_type as string,
      entity_id: ref.entity_id as string,
      version: ref.version as number,
      stageName,
    }))
  )
  const failedAllScenesRun = overallStatus === 'failed' && sceneScope?.mode === 'all_scenes'
  const partialFailureSummary = failedAllScenesRun
    ? allArtifacts.length > 0
      ? `This all-scenes run failed after saving ${allArtifacts.length} artifact${allArtifacts.length === 1 ? '' : 's'}. Review the preserved outputs below, then rerun from the failed scene set or refresh the affected scenes.`
      : 'This all-scenes run failed before CineForge finished the batch. Inspect the error details and event log below to see which scenes still need another pass.'
    : null

  // Map API events to RunEvent format
  const events: RunEvent[] = eventsResponse?.events
    ? mapApiEventsToRunEvents(eventsResponse.events)
    : []

  // The detailed cost response is authoritative. A false flag in live run state
  // closes the replay controls immediately while the summary refetches.
  const costRecordComplete = runCostSummary?.cost_is_complete === true
    && state.cost_is_complete !== false
  const costAmount = runCostSummary?.total_cost_usd ?? state.total_cost_usd
  const costCaption = state.cost_is_complete === false || runCostSummary?.cost_is_complete === false
    ? 'Known estimated subtotal'
    : runCostSummary
      ? 'Recorded cost estimate'
      : 'Recorded estimate · completeness unknown'

  async function resumePipeline(nextRunBudgetLimitUsd?: number) {
    if (!costRecordComplete || !runId) return
    try {
      const result = await resumeRun.mutateAsync({
        runId,
        projectId,
        runBudgetLimitUsd: nextRunBudgetLimitUsd,
      })
      navigate(`/${projectId}/run/${result.run_id}`)
      toast.success('Pipeline resumed')
    } catch (err) {
      toast.error('Failed to resume: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  async function retryPipeline() {
    if (!costRecordComplete || !runId) return
    try {
      const result = await retryFailedStage.mutateAsync({ runId, projectId })
      navigate(`/${projectId}/run/${result.run_id}`)
    } catch (err) {
      toast.error('Failed to retry: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  return (
    <div className="w-full min-w-0">
      <RunDetailHeader
        recipeId={state.recipe_id}
        runId={state.run_id}
        overallStatus={overallStatus}
        canReplay={costRecordComplete}
        retryPending={retryFailedStage.isPending}
        resumePending={resumeRun.isPending}
        onBack={goBack}
        onResume={() => { void resumePipeline() }}
        onRetry={() => { void retryPipeline() }}
      />

      <RunDetailMetrics
        totalCostUsd={costAmount}
        costLabel={costCaption}
        durationSeconds={duration}
        defaultModel={String(state.runtime_params.default_model || 'Unknown')}
        completedStages={completedStages}
        totalStages={totalStages}
      />

      {projectId && runCostSummary && (
        <div className="mb-6">
          <RunCostSummaryPanel
            projectId={projectId}
            summary={costRecordComplete
              ? runCostSummary
              : { ...runCostSummary, cost_is_complete: false }}
            resumeAction={costRecordComplete ? {
              isPending: resumeRun.isPending,
              onResume: (nextRunBudgetLimitUsd?: number) => {
                void resumePipeline(nextRunBudgetLimitUsd)
              },
            } : undefined}
          />
        </div>
      )}

      {(sceneScope || sceneActionPreflight) && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Execution Scope</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Selected: {scopeLabel}</Badge>
              {startFrom && (
                <Badge variant="secondary" className="font-mono text-[11px]">
                  start_from={startFrom}
                </Badge>
              )}
              {endAt && (
                <Badge variant="secondary" className="font-mono text-[11px]">
                  end_at={endAt}
                </Badge>
              )}
              {orderedStageIds.length > 0 && (
                <Badge variant="secondary" className="font-mono text-[11px]">
                  stage_order=[{stageOrderSummary}]
                </Badge>
              )}
              {sceneActionPreflight && (
                <Badge
                  variant="outline"
                  className={cn(
                    sceneActionPreflight.status === 'soft_block'
                      ? 'border-red-500/30 bg-red-500/10 text-red-200'
                      : sceneActionPreflight.status === 'warn'
                        ? 'border-amber-500/30 bg-amber-500/10 text-amber-100'
                        : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100',
                  )}
                >
                  {sceneActionPreflight.status === 'soft_block'
                    ? 'Soft Block'
                    : sceneActionPreflight.status === 'warn'
                      ? 'Warnings'
                      : 'Ready'}
                </Badge>
              )}
              {sceneScope?.mode === 'current_scene' && sceneScope.scene_ids.map((sceneId) => (
                <Badge key={sceneId} variant="secondary">
                  {sceneId}
                </Badge>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">
              {sceneActionPreflight?.summary
                || `This run targeted ${scopeTargetLabel}.`}
            </p>
            {(startFrom || orderedStageIds.length > 0) && (
              <p className="text-sm text-muted-foreground">
                {startFrom
                  ? `This run resumed at ${humanizeStageName(startFrom)}. `
                  : ''}
                {orderedStageIds.length > 0
                  ? `Executed stages: ${orderedStageIds.map(humanizeStageName).join(' -> ')}.`
                  : ''}
              </p>
            )}
            {sceneActionPreflight && sceneActionPreflight.items.length > 0 && (
              <div className="space-y-2">
                {sceneActionPreflight.items.map((item, index) => (
                  <div
                    key={`${item.kind}-${item.label}-${index}`}
                    className="rounded-lg border border-border/60 px-3 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium">{item.label}</span>
                      <Badge variant="outline">{item.kind.replace('_', ' ')}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{item.detail}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Stage progress */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Pipeline Stages</CardTitle>
        </CardHeader>
        <CardContent className="py-0 px-0">
          {stageEntries.map(([stageName, stage], i) => (
            <div key={stageName}>
              <div className="flex items-center gap-3 px-4 py-3">
                <StatusIcon status={stage.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'text-sm font-medium capitalize',
                        stage.status === 'pending' && 'text-muted-foreground'
                      )}
                    >
                      {stageName.replace(/_/g, ' ')}
                    </span>
                    {stage.model_used && (
                      <span className="text-xs text-muted-foreground">
                        {stage.model_used.replace('claude-', '')}
                      </span>
                    )}
                  </div>
                  {stage.call_count !== undefined && stage.call_count > 0 && (
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {stage.call_count} AI {stage.call_count === 1 ? 'call' : 'calls'}
                      {stage.attempt_count !== undefined && stage.attempt_count > 1 && (
                        <> • {stage.attempt_count} attempts</>
                      )}
                      {stage.artifact_refs.length > 0 && (
                        <> • {stage.artifact_refs.length} {stage.artifact_refs.length === 1 ? 'artifact' : 'artifacts'}</>
                      )}
                    </div>
                  )}
                  {stage.status === 'failed' && stage.final_error_class && (
                    <div className="text-xs text-destructive mt-0.5">
                      Error type: {stage.final_error_class}
                    </div>
                  )}
                </div>
                {stage.duration_seconds > 0 && (
                  <span className="text-xs text-muted-foreground shrink-0">
                    {formatDuration(stage.duration_seconds)}
                  </span>
                )}
                {stage.cost_usd > 0 && (
                  <span className="text-xs text-muted-foreground shrink-0 min-w-[60px] text-right">
                    ${stage.cost_usd.toFixed(2)}
                  </span>
                )}
              </div>
              {i < stageEntries.length - 1 && <Separator />}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Artifacts produced */}
      {allArtifacts.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-3">
            Artifacts Produced ({allArtifacts.length})
          </h2>
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
            {allArtifacts.map((artifact, i) => (
              <Link
                key={i}
                to={`/${projectId}/artifacts/${artifact.artifact_type}/${artifact.entity_id}/${artifact.version}`}
                className="block"
              >
                <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-md bg-primary/10 p-2 shrink-0">
                        <Package className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                          {artifact.artifact_type}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          v{artifact.version} • {artifact.stageName.replace(/_/g, ' ')}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Event log */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">Event Log</h2>
        <Card>
          <CardContent className="p-0">
            {eventsLoading ? (
              <div className="flex items-center justify-center h-[400px] text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Loading events...
              </div>
            ) : (
              <RunEventLog events={events} maxHeight="400px" />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Background error warning */}
      {runState.background_error && (
        <Card className="mt-6 border-destructive/50 bg-destructive/5">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-sm mb-1">
                  {failedAllScenesRun ? 'All-Scenes Run Failed' : 'Background Error'}
                </div>
                {partialFailureSummary && (
                  <div className="text-sm text-muted-foreground mb-2">
                    {partialFailureSummary}
                  </div>
                )}
                <div className="text-sm text-muted-foreground">
                  {runState.background_error}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
