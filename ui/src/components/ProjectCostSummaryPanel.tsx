import {
  ArrowDownRight,
  ArrowUpRight,
  Download,
  Minus,
  Wallet,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { getCostExportUrl } from '@/lib/api'
import { formatDuration, timeAgo } from '@/lib/format'
import type { ProjectCostSummary } from '@/lib/types'

type Props = {
  projectId: string
  summary: ProjectCostSummary
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value)
}

function TrendIcon({ direction }: { direction: ProjectCostSummary['trend']['direction'] }) {
  if (direction === 'up') {
    return <ArrowUpRight className="h-4 w-4 text-destructive" />
  }
  if (direction === 'down') {
    return <ArrowDownRight className="h-4 w-4 text-primary" />
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />
}

function TrendLabel({ direction }: { direction: ProjectCostSummary['trend']['direction'] }) {
  if (direction === 'up') return 'Runs are trending more expensive'
  if (direction === 'down') return 'Runs are trending cheaper'
  if (direction === 'flat') return 'Runs are cost-stable'
  return 'Need more runs for a trend'
}

export function ProjectCostSummaryPanel({ projectId, summary }: Props) {
  const trendPoints = summary.trend_points.slice(-6)
  const recentRuns = summary.runs.slice(0, 5)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground mb-1">Cumulative Project Cost</div>
            <div className="text-xl font-semibold">{formatCurrency(summary.total_cost_usd)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground mb-1">Tracked Runs</div>
            <div className="text-xl font-semibold">{summary.run_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground mb-1">Recent Average</div>
            <div className="text-xl font-semibold">
              {formatCurrency(summary.trend.recent_average_usd)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
              <TrendIcon direction={summary.trend.direction} />
              Cost Trend
            </div>
            <div className="text-sm font-medium">
              <TrendLabel direction={summary.trend.direction} />
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Delta {formatCurrency(summary.trend.delta_usd)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Project Cost Ledger
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Historical run spend, budget defaults, and current trend.
            </p>
          </div>
          <div className="flex gap-2">
            <Button asChild size="sm" variant="outline">
              <a href={getCostExportUrl(projectId, 'cost-report-csv')}>
                <Download className="h-4 w-4" />
                CSV
              </a>
            </Button>
            <Button asChild size="sm" variant="outline">
              <a href={getCostExportUrl(projectId, 'cost-report-json')}>
                <Download className="h-4 w-4" />
                JSON
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="rounded-md border border-border px-3 py-2">
              <div className="text-xs text-muted-foreground mb-1">Project Budget Limit</div>
              <div className="font-medium">
                {summary.budget_config.project_budget_limit_usd != null
                  ? formatCurrency(summary.budget_config.project_budget_limit_usd)
                  : 'Not set'}
              </div>
            </div>
            <div className="rounded-md border border-border px-3 py-2">
              <div className="text-xs text-muted-foreground mb-1">Default Run Budget</div>
              <div className="font-medium">
                {summary.budget_config.default_run_budget_limit_usd != null
                  ? formatCurrency(summary.budget_config.default_run_budget_limit_usd)
                  : 'Not set'}
              </div>
            </div>
          </div>

          {trendPoints.length > 0 && (
            <>
              <Separator />
              <div>
                <div className="text-sm font-medium mb-2">Trend Points</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2">
                  {trendPoints.map((point) => (
                    <div
                      key={point.run_id}
                      className="rounded-md border border-border px-3 py-2 text-sm"
                    >
                      <div className="font-medium">{point.run_id}</div>
                      <div className="text-xs text-muted-foreground">
                        {point.started_at != null
                          ? timeAgo(point.started_at * 1000)
                          : 'Unknown start'}
                      </div>
                      <div className="mt-1">{formatCurrency(point.total_cost_usd)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          <Separator />

          <div>
            <div className="text-sm font-medium mb-2">Recent Runs</div>
            <div className="space-y-2">
              {recentRuns.map((run) => (
                <div
                  key={run.run_id}
                  className="rounded-md border border-border px-3 py-2 text-sm"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-medium">{run.run_id}</div>
                      <div className="text-xs text-muted-foreground">
                        {run.recipe_id} · {run.status}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatCurrency(run.total_cost_usd)}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatDuration(run.duration_seconds)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
