import { useParams, useNavigate } from 'react-router-dom'
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  DollarSign,
  Layers,
  History,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useInspector } from '@/lib/right-panel'
import { useRuns, useRunState } from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { cn } from '@/lib/utils'
import type { RunSummary } from '@/lib/types'

function statusIcon(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return <CheckCircle2 className="h-4 w-4 text-primary" />
    case 'failed':
      return <XCircle className="h-4 w-4 text-destructive" />
    case 'running':
      return <Loader2 className="h-4 w-4 text-primary animate-spin" />
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />
  }
}

function statusBadge(status: string) {
  const variant = status === 'failed' ? 'destructive' as const : 'secondary' as const
  return (
    <Badge variant={variant} className="text-xs capitalize">
      {status}
    </Badge>
  )
}

function timeAgo(ms: number): string {
  const seconds = Math.floor((Date.now() - ms) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function stageStatusIcon(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
    case 'failed':
      return <XCircle className="h-3.5 w-3.5 text-destructive" />
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
    default:
      return <Clock className="h-3.5 w-3.5 text-muted-foreground/40" />
  }
}

function RunInspectorContent({ runId }: { runId: string }) {
  const { data: runStateData, isLoading } = useRunState(runId)

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-24" />
      </div>
    )
  }

  if (!runStateData?.state) {
    return (
      <p className="text-xs text-muted-foreground">
        Could not load run details.
      </p>
    )
  }

  const { state } = runStateData
  const stageEntries = Object.entries(state.stages || {})
  const doneCount = stageEntries.filter(
    ([, s]) => s.status === 'done' || s.status === 'skipped_reused'
  ).length

  const formatDuration = (seconds: number) => {
    if (!seconds || seconds <= 0) return null
    const rounded = Math.round(seconds)
    if (rounded < 60) return `${rounded}s`
    const mins = Math.floor(rounded / 60)
    const secs = rounded % 60
    return `${mins}m ${secs}s`
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {statusBadge(state.finished_at ? 'done' : 'running')}
          <span className="text-xs text-muted-foreground">{state.recipe_id}</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <DollarSign className="h-3 w-3" />
            ${(state.total_cost_usd ?? 0).toFixed(2)}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Layers className="h-3 w-3" />
            {doneCount}/{stageEntries.length} stages
          </div>
          {state.started_at && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {timeAgo(state.started_at * 1000)}
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* Stage list */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground mb-2">Stages</p>
        {stageEntries.map(([stageName, stage]) => {
          const duration = formatDuration(stage.duration_seconds)
          return (
            <div key={stageName} className="flex items-center gap-2 py-1.5">
              {stageStatusIcon(stage.status)}
              <span
                className={cn(
                  'text-xs flex-1',
                  stage.status === 'pending' ? 'text-muted-foreground' : 'text-foreground',
                )}
              >
                {stageName}
              </span>
              {duration && (
                <span className="text-xs text-muted-foreground">{duration}</span>
              )}
              {stage.cost_usd > 0 && (
                <span className="text-xs text-muted-foreground">${stage.cost_usd.toFixed(2)}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function RunListSkeleton() {
  return (
    <Card>
      <CardContent className="py-2 px-0">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i}>
            <div className="flex items-center gap-3 px-4 py-3">
              <Skeleton className="h-4 w-4 rounded-full" />
              <div className="min-w-0 flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <div className="flex items-center gap-3">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
              <Skeleton className="h-3 w-16 shrink-0" />
            </div>
            {i < 3 && <Separator />}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export default function ProjectRuns() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const inspector = useInspector()
  const { data: runs, isLoading, error, refetch } = useRuns(projectId)

  function selectRun(run: RunSummary) {
    inspector.open(
      run.run_id,
      <RunInspectorContent runId={run.run_id} />,
    )
  }

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Run History</h1>
        <p className="text-muted-foreground text-sm mb-6">
          All pipeline runs for this project
        </p>
        <RunListSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Run History</h1>
        <p className="text-muted-foreground text-sm mb-6">
          All pipeline runs for this project
        </p>
        <ErrorState
          message="Failed to load run history"
          hint={error.message}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  if (!runs || runs.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Run History</h1>
        <p className="text-muted-foreground text-sm mb-6">
          All pipeline runs for this project
        </p>
        <EmptyState
          icon={History}
          title="No runs yet"
          description="Start a pipeline run to see it here"
          action={{
            label: 'Go to Pipeline',
            onClick: () => navigate(`/${projectId}/run`),
          }}
        />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Run History</h1>
      <p className="text-muted-foreground text-sm mb-6">
        All pipeline runs for this project
      </p>

      <Card>
        <CardContent className="py-2 px-0">
          {runs.map((run, i) => (
            <div key={run.run_id}>
              <button
                className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors"
                onClick={() => selectRun(run)}
              >
                {statusIcon(run.status)}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{run.run_id}</span>
                    {statusBadge(run.status)}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    {run.started_at && (
                      <span className="text-xs text-muted-foreground">
                        Started {timeAgo(run.started_at * 1000)}
                      </span>
                    )}
                    {run.finished_at && (
                      <span className="text-xs text-muted-foreground">
                        Finished {timeAgo(run.finished_at * 1000)}
                      </span>
                    )}
                  </div>
                </div>
                <span className="text-xs text-muted-foreground shrink-0">
                  {run.started_at ? timeAgo(run.started_at * 1000) : 'Unknown'}
                </span>
              </button>
              {i < runs.length - 1 && <Separator />}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
