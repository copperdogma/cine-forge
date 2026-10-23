import { useEffect, useState } from 'react'
import { AlertTriangle, PauseCircle, Play } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { formatCost } from '@/lib/cost-format'
import type { BudgetStatus, RunCostSummary } from '@/lib/cost-types'

type ResumeAction = {
  isPending: boolean
  onResume: (nextRunBudgetLimitUsd?: number) => void
}

type Props = {
  summary: RunCostSummary
  resumeAction?: ResumeAction
}

function budgetBadgeVariant(status: BudgetStatus): 'default' | 'secondary' | 'destructive' {
  if (status.health === 'limit_reached') return 'destructive'
  if (status.health === 'warning') return 'secondary'
  return 'default'
}

function BudgetStatuses({ statuses, complete }: { statuses: BudgetStatus[]; complete: boolean }) {
  if (statuses.length === 0) return null
  return (
    <>
      <Separator />
      <div className="space-y-3">
        <div className="text-sm font-medium">Budget Status</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {statuses.map((status) => (
            <div key={status.scope} className="rounded-md border border-border px-3 py-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <div className="font-medium capitalize">{status.scope} budget</div>
                {complete && (
                  <Badge variant={budgetBadgeVariant(status)}>
                    {status.health.replace('_', ' ')}
                  </Badge>
                )}
              </div>
              <div className="text-muted-foreground mt-2">
                {formatCost(status.consumed_usd)} known estimated use of{' '}
                {formatCost(status.limit_usd)} limit
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {complete
                  ? `Estimated remaining ${formatCost(status.remaining_usd)}`
                  : 'Remaining amount unknown while charges are unresolved'}
              </div>
              {status.message && (
                <div className="flex items-start gap-2 text-xs text-muted-foreground mt-2">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>{status.message}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function ResumeControl({ summary, resumeAction }: { summary: RunCostSummary; resumeAction: ResumeAction }) {
  const [limit, setLimit] = useState(
    summary.budget_config.default_run_budget_limit_usd?.toString() ?? '',
  )
  const limitReached = summary.budget_statuses.some((status) => status.health === 'limit_reached')

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLimit(summary.budget_config.default_run_budget_limit_usd?.toString() ?? '')
    }, 0)
    return () => clearTimeout(timeout)
  }, [summary.run_id, summary.budget_config.default_run_budget_limit_usd])

  function resume() {
    const parsed = Number(limit)
    resumeAction.onResume(
      limitReached && Number.isFinite(parsed) && parsed > 0 ? parsed : undefined,
    )
  }

  return (
    <>
      <Separator />
      <div className="rounded-md border border-border px-3 py-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <PauseCircle className="h-4 w-4" />
          {limitReached ? 'Increase budget and resume' : 'Resume paused run'}
        </div>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
          {limitReached && (
            <div className="flex-1">
              <label
                htmlFor="resume-budget-limit"
                className="text-xs font-medium text-muted-foreground mb-1.5 block"
              >
                New Run Budget Limit (USD)
              </label>
              <Input
                id="resume-budget-limit"
                type="number"
                min="0"
                step="0.01"
                value={limit}
                onChange={(event) => setLimit(event.target.value)}
                placeholder="Enter a higher cap"
              />
            </div>
          )}
          <Button disabled={resumeAction.isPending} onClick={resume}>
            <Play className="h-4 w-4" />
            {resumeAction.isPending ? 'Resuming...' : 'Resume'}
          </Button>
        </div>
      </div>
    </>
  )
}

export function RunCostBudgetSection({ summary, resumeAction }: Props) {
  return (
    <>
      <BudgetStatuses statuses={summary.budget_statuses} complete={summary.cost_is_complete} />
      {summary.status === 'paused' && resumeAction && (
        summary.cost_is_complete ? (
          <ResumeControl summary={summary} resumeAction={resumeAction} />
        ) : (
          <p className="text-sm text-muted-foreground">
            Resolve uncertain charges before using cost-based resume controls.
          </p>
        )
      )}
    </>
  )
}
