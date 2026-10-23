import { Separator } from '@/components/ui/separator'
import { costLabel, formatCost } from '@/lib/cost-format'
import type { ProjectCostSummary } from '@/lib/cost-types'
import { formatDuration, timeAgo } from '@/lib/format'

type Props = { summary: ProjectCostSummary }

function TrendPoints({ points }: { points: ProjectCostSummary['trend_points'] }) {
  if (points.length === 0) return null
  return (
    <>
      <Separator />
      <div>
        <div className="text-sm font-medium mb-2">Trend Points</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2">
          {points.slice(-6).map((point) => (
            <div key={point.run_id} className="rounded-md border border-border px-3 py-2 text-sm">
              <div className="font-medium">{point.run_id}</div>
              <div className="text-xs text-muted-foreground">
                {point.started_at != null ? timeAgo(point.started_at * 1000) : 'Unknown start'}
              </div>
              <div className="mt-1">{formatCost(point.total_cost_usd)}</div>
              <div className="text-xs text-muted-foreground">
                {costLabel(point.cost_is_complete, 'Estimated run cost')}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function RecentRuns({ runs }: { runs: ProjectCostSummary['runs'] }) {
  return (
    <div>
      <div className="text-sm font-medium mb-2">Recent Runs</div>
      <div className="space-y-2">
        {runs.slice(0, 5).map((run) => (
          <div key={run.run_id} className="rounded-md border border-border px-3 py-2 text-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="font-medium">{run.run_id}</div>
                <div className="text-xs text-muted-foreground">
                  {run.recipe_id} · {run.status}
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium">{formatCost(run.total_cost_usd)}</div>
                <div className="text-xs text-muted-foreground">
                  {costLabel(run.cost_is_complete, 'Estimated run cost')} ·{' '}
                  {formatDuration(run.duration_seconds)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ProjectCostHistory({ summary }: Props) {
  return (
    <>
      <TrendPoints points={summary.trend_points} />
      <Separator />
      <RecentRuns runs={summary.runs} />
    </>
  )
}
