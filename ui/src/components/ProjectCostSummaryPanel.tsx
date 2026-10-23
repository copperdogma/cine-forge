import { Download, Wallet } from 'lucide-react'

import { CostCompletenessNotice } from '@/components/CostCompletenessNotice'
import { ProjectCostHistory } from '@/components/ProjectCostHistory'
import { ProjectCostMetrics } from '@/components/ProjectCostMetrics'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getCostExportUrl } from '@/lib/api'
import { formatCost } from '@/lib/cost-format'
import type { ProjectCostSummary } from '@/lib/cost-types'

type Props = { projectId: string; summary: ProjectCostSummary }

function ProjectCostHeader({ projectId }: { projectId: string }) {
  return (
    <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-4 w-4" />
          Project Cost Ledger
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          Historical run cost estimates and budget defaults.
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
  )
}

function ProjectBudgetLimits({ config }: { config: ProjectCostSummary['budget_config'] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">Project Budget Limit</div>
        <div className="font-medium">
          {config.project_budget_limit_usd != null
            ? formatCost(config.project_budget_limit_usd)
            : 'Not set'}
        </div>
      </div>
      <div className="rounded-md border border-border px-3 py-2">
        <div className="text-xs text-muted-foreground mb-1">Default Run Budget</div>
        <div className="font-medium">
          {config.default_run_budget_limit_usd != null
            ? formatCost(config.default_run_budget_limit_usd)
            : 'Not set'}
        </div>
      </div>
    </div>
  )
}

export function ProjectCostSummaryPanel({ projectId, summary }: Props) {
  return (
    <div className="space-y-4">
      {!summary.cost_is_complete && (
        <CostCompletenessNotice scope="project" receipts={summary.uncertain_cost_receipts} />
      )}
      <ProjectCostMetrics summary={summary} />
      <Card>
        <ProjectCostHeader projectId={projectId} />
        <CardContent className="space-y-4">
          <ProjectBudgetLimits config={summary.budget_config} />
          <ProjectCostHistory summary={summary} />
        </CardContent>
      </Card>
    </div>
  )
}
