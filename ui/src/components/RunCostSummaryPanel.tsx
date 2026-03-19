import { useEffect, useState } from 'react'
import { AlertTriangle, Download, PauseCircle, Play, Wallet } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { getCostExportUrl } from '@/lib/api'
import { formatDuration } from '@/lib/format'
import type { BudgetStatus, RunCostSummary } from '@/lib/types'

type ResumeAction = {
  isPending: boolean
  onResume: (nextRunBudgetLimitUsd?: number) => void
}

type Props = {
  projectId: string
  summary: RunCostSummary
  resumeAction?: ResumeAction
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value)
}

function budgetBadgeVariant(status: BudgetStatus): 'default' | 'secondary' | 'destructive' {
  if (status.health === 'limit_reached') return 'destructive'
  if (status.health === 'warning') return 'secondary'
  return 'default'
}

export function RunCostSummaryPanel({ projectId, summary, resumeAction }: Props) {
  const [resumeBudgetLimitUsd, setResumeBudgetLimitUsd] = useState(
    summary.budget_config.default_run_budget_limit_usd != null
      ? String(summary.budget_config.default_run_budget_limit_usd)
      : '',
  )

  useEffect(() => {
    const timeout = setTimeout(() => {
      setResumeBudgetLimitUsd(
        summary.budget_config.default_run_budget_limit_usd != null
          ? String(summary.budget_config.default_run_budget_limit_usd)
          : '',
      )
    }, 0)
    return () => clearTimeout(timeout)
  }, [summary.run_id, summary.budget_config.default_run_budget_limit_usd])

  const limitReached = summary.budget_statuses.some((status) => status.health === 'limit_reached')
  const canResume = summary.status === 'paused' && resumeAction != null

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Run Cost Breakdown
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Stage, model, role, and scene spend for this run.
            </p>
          </div>
          <div className="flex gap-2">
            <Button asChild size="sm" variant="outline">
              <a href={getCostExportUrl(projectId, 'cost-report-csv', summary.run_id)}>
                <Download className="h-4 w-4" />
                CSV
              </a>
            </Button>
            <Button asChild size="sm" variant="outline">
              <a href={getCostExportUrl(projectId, 'cost-report-json', summary.run_id)}>
                <Download className="h-4 w-4" />
                JSON
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            <div className="rounded-md border border-border px-3 py-2">
              <div className="text-xs text-muted-foreground mb-1">Run Total</div>
              <div className="text-lg font-semibold">{formatCurrency(summary.total_cost_usd)}</div>
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

          {summary.budget_statuses.length > 0 && (
            <>
              <Separator />
              <div className="space-y-3">
                <div className="text-sm font-medium">Budget Status</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {summary.budget_statuses.map((status) => (
                    <div
                      key={status.scope}
                      className="rounded-md border border-border px-3 py-3 text-sm"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="font-medium capitalize">{status.scope} budget</div>
                        <Badge variant={budgetBadgeVariant(status)}>
                          {status.health.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div className="text-muted-foreground mt-2">
                        {formatCurrency(status.consumed_usd)} used of{' '}
                        {formatCurrency(status.limit_usd)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Remaining {formatCurrency(status.remaining_usd)}
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
          )}

          {canResume && (
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
                        value={resumeBudgetLimitUsd}
                        onChange={(event) => setResumeBudgetLimitUsd(event.target.value)}
                        placeholder="Enter a higher cap"
                      />
                    </div>
                  )}
                  <Button
                    disabled={resumeAction.isPending}
                    onClick={() => {
                      const parsedBudget = Number(resumeBudgetLimitUsd)
                      if (limitReached && Number.isFinite(parsedBudget) && parsedBudget > 0) {
                        resumeAction.onResume(parsedBudget)
                        return
                      }
                      resumeAction.onResume()
                    }}
                  >
                    <Play className="h-4 w-4" />
                    {resumeAction.isPending ? 'Resuming...' : 'Resume'}
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">By Stage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {summary.stages.map((stage) => (
              <div key={stage.stage_id} className="rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{stage.stage_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {stage.model_used ?? 'code'} · {stage.status}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(stage.estimated_cost_usd)}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatDuration(stage.duration_seconds)}
                    </div>
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <div>Calls {stage.call_count}</div>
                  <div>Attempts {stage.attempt_count}</div>
                  <div>Module {formatCurrency(stage.module_cost_usd)}</div>
                  <div>Role {formatCurrency(stage.role_cost_usd)}</div>
                </div>
                {stage.pause_reason && (
                  <div className="text-xs text-muted-foreground mt-2">{stage.pause_reason}</div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">By Model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {summary.by_model.length === 0 && (
              <div className="text-sm text-muted-foreground">No model cost data recorded.</div>
            )}
            {summary.by_model.map((model) => (
              <div key={model.model} className="rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium break-all">{model.model}</div>
                  <div className="font-medium">{formatCurrency(model.estimated_cost_usd)}</div>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                  <div>Calls {model.call_count}</div>
                  <div>In {model.input_tokens}</div>
                  <div>Out {model.output_tokens}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">By Role</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {summary.by_role.length === 0 && (
              <div className="text-sm text-muted-foreground">No role-attributed cost data recorded.</div>
            )}
            {summary.by_role.map((role) => (
              <div key={role.role_id} className="rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{role.role_id}</div>
                    <div className="text-xs text-muted-foreground">{role.models.join(', ')}</div>
                  </div>
                  <div className="font-medium">{formatCurrency(role.estimated_cost_usd)}</div>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                  {role.call_count} calls · stages {role.stage_ids.join(', ') || '—'} · scenes{' '}
                  {role.scene_ids.join(', ') || '—'}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">By Scene</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {summary.by_scene.length === 0 && (
              <div className="text-sm text-muted-foreground">
                No scene-attributed cost data recorded.
              </div>
            )}
            {summary.by_scene.map((scene) => (
              <div key={scene.scene_id} className="rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{scene.scene_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {scene.attribution.kind.replace('_', ' ')}
                    </div>
                  </div>
                  <div className="font-medium">{formatCurrency(scene.estimated_cost_usd)}</div>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                  {scene.call_count} calls · stages {scene.stage_ids.join(', ') || '—'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">{scene.attribution.basis}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
