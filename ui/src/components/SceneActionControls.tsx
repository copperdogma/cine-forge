import { AlertTriangle, ArrowRight, CheckCircle2, Wrench } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { SceneActionPreflight, SceneScopeMode } from '@/lib/types'

type SceneActionControlsProps = {
  scope: SceneScopeMode
  onScopeChange: (scope: SceneScopeMode) => void
  preflight?: SceneActionPreflight | null
  disabled?: boolean
}

const ITEM_ORDER = {
  soft_block: 0,
  auto_build: 1,
  warning: 2,
} as const

export function SceneActionControls({
  scope,
  onScopeChange,
  preflight,
  disabled = false,
}: SceneActionControlsProps) {
  const { projectId } = useParams<{ projectId: string }>()
  const statusBadge = preflight?.status === 'soft_block'
    ? { label: 'Soft Block', className: 'border-red-500/30 bg-red-500/10 text-red-200' }
    : preflight?.status === 'warn'
      ? { label: 'Warnings', className: 'border-amber-500/30 bg-amber-500/10 text-amber-100' }
      : { label: 'Ready', className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100' }
  const items = [...(preflight?.items ?? [])].sort((a, b) => ITEM_ORDER[a.kind] - ITEM_ORDER[b.kind])

  const actionHref = (actionPath?: string | null) => {
    if (!projectId || actionPath == null) return null
    if (actionPath.startsWith('/')) return actionPath
    const normalized = actionPath.replace(/^\/+/, '')
    return normalized ? `/${projectId}/${normalized}` : `/${projectId}`
  }

  return (
    <div className="space-y-3 rounded-lg border border-border/70 bg-card/70 px-4 py-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Execution Scope
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant={scope === 'current_scene' ? 'default' : 'outline'}
              disabled={disabled}
              onClick={() => onScopeChange('current_scene')}
            >
              Current Scene
            </Button>
            <Button
              type="button"
              size="sm"
              variant={scope === 'all_scenes' ? 'default' : 'outline'}
              disabled={disabled}
              onClick={() => onScopeChange('all_scenes')}
            >
              All Scenes
            </Button>
          </div>
        </div>
        <Badge variant="outline" className={cn('w-fit', statusBadge.className)}>
          {statusBadge.label}
        </Badge>
      </div>

      {preflight?.summary && (
        <p className="text-sm leading-relaxed text-muted-foreground">
          {preflight.summary}
        </p>
      )}

      {items.length > 0 && (
        <div className="space-y-2 border-t border-border/60 pt-3">
          {items.map((item, index) => {
            const Icon = item.kind === 'auto_build'
              ? Wrench
              : item.kind === 'soft_block'
                ? AlertTriangle
                : CheckCircle2
            const tone = item.kind === 'soft_block'
              ? 'text-red-200'
              : item.kind === 'auto_build'
                ? 'text-sky-100'
                : 'text-amber-100'
            const href = actionHref(item.action_path)
            return (
              <div key={`${item.kind}-${item.label}-${index}`} className="flex items-start gap-2">
                <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', tone)} />
                <div className="space-y-2">
                  <p className={cn('text-sm font-medium', tone)}>{item.label}</p>
                  <p className="text-sm leading-relaxed text-muted-foreground">{item.detail}</p>
                  {href && item.action_label && (
                    <Button asChild type="button" size="sm" variant="outline" className="h-8 w-fit">
                      <Link to={href}>
                        <ArrowRight className="h-3.5 w-3.5" />
                        {item.action_label}
                      </Link>
                    </Button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
