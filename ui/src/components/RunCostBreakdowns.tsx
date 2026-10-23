import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { costLabel, formatCost } from '@/lib/cost-format'
import type { RunCostSummary } from '@/lib/cost-types'
import { formatDuration } from '@/lib/format'

type Props = { summary: RunCostSummary }

function StageBreakdown({ summary }: Props) {
  return (
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
                <div className="font-medium">{formatCost(stage.estimated_cost_usd)}</div>
                <div className="text-xs text-muted-foreground">
                  {costLabel(stage.cost_is_complete, 'Estimated stage cost')} ·{' '}
                  {formatDuration(stage.duration_seconds)}
                </div>
              </div>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <div>Calls {stage.call_count}</div>
              <div>Attempts {stage.attempt_count}</div>
              <div>Module {formatCost(stage.module_cost_usd)}</div>
              <div>Role {formatCost(stage.role_cost_usd)}</div>
            </div>
            {stage.pause_reason && (
              <div className="text-xs text-muted-foreground mt-2">{stage.pause_reason}</div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function ModelBreakdown({ summary }: Props) {
  return (
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
              <div className="text-right">
                <div className="font-medium">{formatCost(model.estimated_cost_usd)}</div>
                <div className="text-xs text-muted-foreground">
                  {costLabel(model.cost_is_complete, 'Estimated model cost')}
                </div>
              </div>
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
  )
}

function RoleBreakdown({ summary }: Props) {
  return (
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
              <div className="text-right">
                <div className="font-medium">{formatCost(role.estimated_cost_usd)}</div>
                <div className="text-xs text-muted-foreground">
                  {costLabel(summary.cost_is_complete, 'Estimated role cost')}
                </div>
              </div>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              {role.call_count} calls · stages {role.stage_ids.join(', ') || '—'} · scenes{' '}
              {role.scene_ids.join(', ') || '—'}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function SceneBreakdown({ summary }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">By Scene</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {summary.by_scene.length === 0 && (
          <div className="text-sm text-muted-foreground">No scene-attributed cost data recorded.</div>
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
              <div className="text-right">
                <div className="font-medium">{formatCost(scene.estimated_cost_usd)}</div>
                <div className="text-xs text-muted-foreground">
                  {costLabel(scene.cost_is_complete, 'Estimated scene cost')}
                </div>
              </div>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              {scene.call_count} calls · stages {scene.stage_ids.join(', ') || '—'}
            </div>
            <div className="text-xs text-muted-foreground mt-1">{scene.attribution.basis}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function RunCostBreakdowns({ summary }: Props) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <StageBreakdown summary={summary} />
      <ModelBreakdown summary={summary} />
      <RoleBreakdown summary={summary} />
      <SceneBreakdown summary={summary} />
    </div>
  )
}
