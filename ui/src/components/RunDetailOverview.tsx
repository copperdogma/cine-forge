import { ArrowLeft, Clock, Cpu, DollarSign, Layers, Play } from 'lucide-react'

import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { RECIPE_NAMES } from '@/lib/constants'
import { formatCost } from '@/lib/cost-format'
import { formatDuration } from '@/lib/format'

type HeaderProps = {
  recipeId: string
  runId: string
  overallStatus: string
  canReplay: boolean
  retryPending: boolean
  resumePending: boolean
  onBack: () => void
  onResume: () => void
  onRetry: () => void
}

type MetricsProps = {
  totalCostUsd: number
  costLabel: string
  durationSeconds: number
  defaultModel: string
  completedStages: number
  totalStages: number
}

export function RunDetailHeader({
  recipeId, runId, overallStatus, canReplay, retryPending, resumePending,
  onBack, onResume, onRetry,
}: HeaderProps) {
  const recipeName = recipeId.replace('recipe-', '').replace(/-/g, ' ')
  return (
    <div className="mb-6">
      <Button variant="ghost" size="sm" className="mb-3 -ml-2" onClick={onBack}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-1">
            {RECIPE_NAMES[recipeId] || recipeName}
            {overallStatus === 'running' && (
              <span className="ml-2 text-muted-foreground font-normal">Running</span>
            )}
            {overallStatus === 'done' && (
              <span className="ml-2 text-muted-foreground font-normal">Complete</span>
            )}
            {overallStatus === 'failed' && (
              <span className="ml-2 text-muted-foreground font-normal">Failed</span>
            )}
            {overallStatus === 'paused' && (
              <span className="ml-2 text-muted-foreground font-normal">Paused</span>
            )}
          </h1>
          <p className="text-muted-foreground text-sm">{runId}</p>
        </div>
        <div className="flex items-center gap-2">
          {overallStatus === 'paused' && canReplay && (
            <Button size="sm" className="gap-1.5" disabled={resumePending} onClick={onResume}>
              <Play className="h-3.5 w-3.5" />
              Resume Pipeline
            </Button>
          )}
          {overallStatus === 'failed' && canReplay && (
            <Button size="sm" disabled={retryPending} onClick={onRetry}>
              Retry Failed Stage
            </Button>
          )}
          <StatusBadge status={overallStatus} />
        </div>
      </div>
      {!canReplay && (overallStatus === 'paused' || overallStatus === 'failed') && (
        <p className="mt-2 text-sm text-muted-foreground">
          Replay is unavailable until the run’s cost record is complete.
        </p>
      )}
    </div>
  )
}

export function RunDetailMetrics({
  totalCostUsd, costLabel, durationSeconds, defaultModel, completedStages, totalStages,
}: MetricsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <DollarSign className="h-3.5 w-3.5" />
            {costLabel}
          </div>
          <div className="text-xl font-bold">{formatCost(totalCostUsd)}</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Clock className="h-3.5 w-3.5" />
            Duration
          </div>
          <div className="text-xl font-bold">{formatDuration(durationSeconds)}</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Cpu className="h-3.5 w-3.5" />
            Model
          </div>
          <div className="text-sm font-medium truncate" title={defaultModel}>
            {defaultModel.replace('claude-', '')}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Layers className="h-3.5 w-3.5" />
            Stages
          </div>
          <div className="text-xl font-bold">{completedStages}/{totalStages}</div>
        </CardContent>
      </Card>
    </div>
  )
}
