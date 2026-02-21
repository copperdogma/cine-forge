import { useParams, useNavigate } from 'react-router-dom'
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  History,
  Plus,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useRuns } from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { RECIPE_NAMES } from '@/lib/constants'

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
  const { data: runs, isLoading, error, refetch } = useRuns(projectId)

  const header = (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Run History</h1>
        <p className="text-muted-foreground text-sm">
          All pipeline runs for this project
        </p>
      </div>
      <Button size="sm" onClick={() => navigate(`/${projectId}/run`)}>
        <Plus className="h-4 w-4 mr-2" />
        Start New Run
      </Button>
    </div>
  )

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto">
        {header}
        <RunListSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto">
        {header}
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
      <div className="max-w-5xl mx-auto">
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
    <div className="max-w-5xl mx-auto">
      {header}

      <Card>
        <CardContent className="py-2 px-0">
          {runs.map((run, i) => (
            <div key={run.run_id}>
              <button
                className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors"
                onClick={() => navigate(`/${projectId}/run/${run.run_id}`)}
              >
                {statusIcon(run.status)}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">
                      {RECIPE_NAMES[run.recipe_id] || 'Unknown Run'}
                    </span>
                    {statusBadge(run.status)}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-[10px] font-mono text-muted-foreground/60 uppercase truncate max-w-[120px]">
                      {run.run_id}
                    </span>
                    {run.started_at && (
                      <span className="text-xs text-muted-foreground">
                        Started {timeAgo(run.started_at * 1000)}
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
