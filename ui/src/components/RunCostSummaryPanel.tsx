import { Download, Wallet } from 'lucide-react'

import { CostCompletenessNotice } from '@/components/CostCompletenessNotice'
import { RunCostBreakdowns } from '@/components/RunCostBreakdowns'
import { RunCostBudgetSection } from '@/components/RunCostBudgetSection'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getCostExportUrl } from '@/lib/api'
import { costLabel, formatCost } from '@/lib/cost-format'
import type { RunCostSummary } from '@/lib/cost-types'

type Props = {
  projectId: string
  summary: RunCostSummary
  resumeAction?: {
    isPending: boolean
    onResume: (nextRunBudgetLimitUsd?: number) => void
  }
}

function RunCostHeader({ projectId, runId }: { projectId: string; runId: string }) {
  return (
    <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-4 w-4" />
          Run Cost Breakdown
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          Stage, model, role, and scene cost estimates for this run.
        </p>
      </div>
      <div className="flex gap-2">
        <Button asChild size="sm" variant="outline">
          <a href={getCostExportUrl(projectId, 'cost-report-csv', runId)}>
            <Download className="h-4 w-4" />
            CSV
          </a>
        </Button>
        <Button asChild size="sm" variant="outline">
          <a href={getCostExportUrl(projectId, 'cost-report-json', runId)}>
            <Download className="h-4 w-4" />
            JSON
          </a>
        </Button>
      </div>
    </CardHeader>
  )
}

function RunCostMetrics({ summary }: { summary: RunCostSummary }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">
          {costLabel(summary.cost_is_complete, 'Run total estimate')}
        </div>
        <div className="text-lg font-semibold">{formatCost(summary.total_cost_usd)}</div>
      </div>
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">Stages</div>
        <div className="text-lg font-semibold">{summary.stages.length}</div>
      </div>
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">Models Used</div>
        <div className="text-lg font-semibold">{summary.by_model.length}</div>
      </div>
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">Scene Attribution</div>
        <div className="text-lg font-semibold">{summary.by_scene.length}</div>
      </div>
    </div>
  )
}

export function RunCostSummaryPanel({ projectId, summary, resumeAction }: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <RunCostHeader projectId={projectId} runId={summary.run_id} />
        <CardContent className="space-y-4">
          {!summary.cost_is_complete && (
            <CostCompletenessNotice scope="run" receipts={summary.uncertain_cost_receipts} />
          )}
          <RunCostMetrics summary={summary} />
          {summary.cost_is_complete && (
            <p className="text-xs text-muted-foreground">
              Cost figures are estimates from recorded usage and prices, not provider bills.
            </p>
          )}
          <RunCostBudgetSection summary={summary} resumeAction={resumeAction} />
        </CardContent>
      </Card>
      <RunCostBreakdowns summary={summary} />
    </div>
  )
}
