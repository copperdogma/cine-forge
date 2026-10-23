import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { costLabel, formatCost } from '@/lib/cost-format'
import type { ProjectCostSummary } from '@/lib/cost-types'

type Props = { summary: ProjectCostSummary }
type Direction = ProjectCostSummary['trend']['direction']

function TrendIcon({ direction }: { direction: Direction }) {
  if (direction === 'up') return <ArrowUpRight className="h-4 w-4 text-destructive" />
  if (direction === 'down') return <ArrowDownRight className="h-4 w-4 text-primary" />
  return <Minus className="h-4 w-4 text-muted-foreground" />
}

function TrendLabel({ direction }: { direction: Direction }) {
  if (direction === 'up') return 'Runs are trending more expensive'
  if (direction === 'down') return 'Runs are trending cheaper'
  if (direction === 'flat') return 'Runs are cost-stable'
  return 'Need more runs for a trend'
}

export function ProjectCostMetrics({ summary }: Props) {
  const trendComplete = summary.cost_is_complete && summary.trend.cost_is_complete
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="text-xs text-muted-foreground mb-1">
            {costLabel(summary.cost_is_complete, 'Cumulative project cost estimate')}
          </div>
          <div className="text-xl font-semibold">{formatCost(summary.total_cost_usd)}</div>
          {summary.cost_is_complete && (
            <div className="text-xs text-muted-foreground mt-1">
              Recorded estimate, not a provider bill
            </div>
          )}
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
            {trendComplete ? formatCost(summary.trend.recent_average_usd) : 'Unknown'}
          </div>
          {!trendComplete && (
            <div className="text-xs text-muted-foreground mt-1">
              Unresolved charges affect this average
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <TrendIcon direction={trendComplete ? summary.trend.direction : 'insufficient_data'} />
            Cost Trend
          </div>
          <div className="text-sm font-medium">
            {trendComplete
              ? <TrendLabel direction={summary.trend.direction} />
              : 'Unknown until charges resolve'}
          </div>
          {trendComplete && (
            <div className="text-xs text-muted-foreground mt-1">
              Delta {formatCost(summary.trend.delta_usd)}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
