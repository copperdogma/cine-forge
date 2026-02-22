import { useParams, useNavigate } from 'react-router-dom'
import { History, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useRuns } from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { RECIPE_NAMES } from '@/lib/constants'
import { timeAgo } from '@/lib/format'
import { StatusIcon, StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'

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

  if (isLoading) {
    return (
      <div className="w-full">
        <PageHeader title="Run History" subtitle="All pipeline runs for this project" />
        <RunListSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full">
        <PageHeader title="Run History" subtitle="All pipeline runs for this project" />
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
      <div className="w-full">
        <PageHeader title="Run History" subtitle="All pipeline runs for this project" />
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
    <div className="w-full">
      <PageHeader title="Run History" subtitle="All pipeline runs for this project" />

      <div className="mb-6">
        <Button size="sm" onClick={() => navigate(`/${projectId}/run`)}>
          <Plus className="h-4 w-4 mr-2" />
          Start New Run
        </Button>
      </div>

      <Card>
        <CardContent className="py-2 px-0">
          {runs.map((run, i) => (
            <div key={run.run_id}>
              <button
                className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors"
                onClick={() => navigate(`/${projectId}/run/${run.run_id}`)}
              >
                <StatusIcon status={run.status} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">
                      {RECIPE_NAMES[run.recipe_id] || 'Unknown Run'}
                    </span>
                    <StatusBadge status={run.status} />
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
