import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  DollarSign,
  Layers,
  Cpu,
  ArrowLeft,
  Package,
  AlertCircle,
  Play,
  PauseCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { RunEventLog, type RunEvent } from '@/components/RunEventLog'
import { ErrorState } from '@/components/StateViews'
import { cn } from '@/lib/utils'
import type { StageState } from '@/lib/types'
import { useRunState, useRunEvents, useRetryFailedStage, useResumeRun } from '@/lib/hooks'
import { RECIPE_NAMES } from '@/lib/constants'
import { toast } from 'sonner'

function statusBadge(status: string) {
  if (status === 'done' || status === 'skipped_reused') {
    return (
      <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-primary/20">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        {status === 'done' ? 'Done' : 'Reused'}
      </Badge>
    )
  }
  if (status === 'failed') {
    return (
      <Badge variant="destructive" className="text-xs">
        <XCircle className="h-3 w-3 mr-1" />
        Failed
      </Badge>
    )
  }
  if (status === 'running') {
    return (
      <Badge variant="secondary" className="text-xs">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Running
      </Badge>
    )
  }
  if (status === 'paused') {
    return (
      <Badge variant="secondary" className="text-xs bg-amber-400/10 text-amber-400 border-amber-400/20">
        <PauseCircle className="h-3 w-3 mr-1" />
        Paused
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="text-xs">
      <Clock className="h-3 w-3 mr-1" />
      {status}
    </Badge>
  )
}

function stageStatusIcon(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return <CheckCircle2 className="h-4 w-4 text-primary" />
    case 'failed':
      return <XCircle className="h-4 w-4 text-destructive" />
    case 'running':
      return <Loader2 className="h-4 w-4 text-primary animate-spin" />
    case 'paused':
      return <PauseCircle className="h-4 w-4 text-amber-400" />
    default:
      return <Clock className="h-4 w-4 text-muted-foreground/40" />
  }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

// Derive overall status from stage states
function getOverallStatus(stages: Record<string, StageState>): string {
  const stagesList = Object.values(stages)
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
    }
    return {
      timestamp: (event.timestamp as number) || Date.now(),
      type: eventTypeMap[backendEvent] ?? ((event.type as RunEvent['type']) || 'info'),
      stage: stageId,
      message,
      details: event.details as Record<string, unknown> | undefined,
    }
  })
}

export default function RunDetail() {
  const { projectId, runId } = useParams()
  const navigate = useNavigate()

  const { data: runStateResponse, isLoading, error, refetch } = useRunState(runId)
  const { data: eventsResponse, isLoading: eventsLoading } = useRunEvents(runId)
  const retryFailedStage = useRetryFailedStage()
  const resumeRun = useResumeRun()

  // Derive running state (safe even when data is undefined)
  const overallStatus = runStateResponse
    ? getOverallStatus(runStateResponse.state.stages)
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
          onClick={() => navigate(`/${projectId}/runs`)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Runs
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
  const recipeName = state.recipe_id.replace('recipe-', '').replace(/-/g, ' ')

  const duration = state.finished_at && state.started_at
    ? state.finished_at - state.started_at
    : state.started_at
      ? now - state.started_at
      : 0

  const stageEntries = Object.entries(state.stages).sort(([, a], [, b]) => {
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

  // Map API events to RunEvent format
  const events: RunEvent[] = eventsResponse?.events
    ? mapApiEventsToRunEvents(eventsResponse.events)
    : []

  const canRetryFailedStage = overallStatus === 'failed' && !!runId && !retryFailedStage.isPending

  return (
    <div className="w-full min-w-0">
      {/* Header with back button */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          className="mb-3 -ml-2"
          onClick={() => navigate(`/${projectId}/runs`)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Runs
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight mb-1">
              {RECIPE_NAMES[state.recipe_id] || recipeName}
              {isRunning && <span className="ml-2 text-muted-foreground font-normal">Running</span>}
              {overallStatus === 'done' && <span className="ml-2 text-muted-foreground font-normal">Complete</span>}
              {overallStatus === 'failed' && <span className="ml-2 text-muted-foreground font-normal">Failed</span>}
              {overallStatus === 'paused' && <span className="ml-2 text-muted-foreground font-normal">Paused</span>}
            </h1>
            <p className="text-muted-foreground text-sm">
              {state.run_id}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {overallStatus === 'paused' && (
              <Button
                size="sm"
                className="gap-1.5"
                disabled={resumeRun.isPending}
                onClick={async () => {
                  try {
                    const result = await resumeRun.mutateAsync({
                      runId: runId!,
                      projectId,
                    })
                    navigate(`/${projectId}/run/${result.run_id}`)
                    toast.success("Pipeline resumed")
                  } catch (err) {
                    toast.error("Failed to resume: " + (err instanceof Error ? err.message : "Unknown error"))
                  }
                }}
              >
                <Play className="h-3.5 w-3.5" />
                Resume Pipeline
              </Button>
            )}
            {canRetryFailedStage && (
              <Button
                size="sm"
                onClick={async () => {
                  const result = await retryFailedStage.mutateAsync({
                    runId: runId!,
                    projectId,
                  })
                  navigate(`/${projectId}/run/${result.run_id}`)
                }}
              >
                Retry Failed Stage
              </Button>
            )}
            {statusBadge(overallStatus)}
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
              <DollarSign className="h-3.5 w-3.5" />
              Total Cost
            </div>
            <div className="text-xl font-bold">
              ${state.total_cost_usd.toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
              <Clock className="h-3.5 w-3.5" />
              Duration
            </div>
            <div className="text-xl font-bold">
              {formatDuration(duration)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
              <Cpu className="h-3.5 w-3.5" />
              Model
            </div>
            <div className="text-sm font-medium truncate" title={state.runtime_params.default_model as string}>
              {(state.runtime_params.default_model as string || 'Unknown').replace('claude-', '')}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
              <Layers className="h-3.5 w-3.5" />
              Stages
            </div>
            <div className="text-xl font-bold">
              {completedStages}/{totalStages}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stage progress */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Pipeline Stages</CardTitle>
        </CardHeader>
        <CardContent className="py-0 px-0">
          {stageEntries.map(([stageName, stage], i) => (
            <div key={stageName}>
              <div className="flex items-center gap-3 px-4 py-3">
                {stageStatusIcon(stage.status)}
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
                <div className="font-medium text-sm mb-1">Background Error</div>
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
