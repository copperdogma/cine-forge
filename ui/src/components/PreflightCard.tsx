import { CheckCircle2, AlertTriangle, FileText, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { PreflightData } from '@/lib/types'

type Props = {
  data: PreflightData
}

export function PreflightCard({ data }: Props) {
  const tierConfig = {
    ready: {
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/5',
      icon: CheckCircle2,
      iconClass: 'text-emerald-400',
      label: 'Ready to run',
    },
    warn_stale: {
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/5',
      icon: AlertTriangle,
      iconClass: 'text-amber-400',
      label: 'Stale upstream',
    },
    block_missing: {
      border: 'border-red-500/30',
      bg: 'bg-red-500/5',
      icon: AlertTriangle,
      iconClass: 'text-red-400',
      label: 'Missing prerequisites',
    },
  }

  const tier = tierConfig[data.tier]
  const TierIcon = tier.icon

  return (
    <div className={cn(
      'rounded-lg border p-3 text-xs space-y-2 my-1',
      tier.border,
      tier.bg,
    )}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <Layers className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="font-semibold text-sm">{data.recipe_name}</span>
        <div className={cn('flex items-center gap-1 ml-auto', tier.iconClass)}>
          <TierIcon className="h-3.5 w-3.5" />
          <span className="text-[10px] font-medium">{tier.label}</span>
        </div>
      </div>

      {/* Description */}
      {data.description && (
        <p className="text-muted-foreground">{data.description}</p>
      )}

      {/* Details row */}
      <div className="flex items-center gap-4 text-muted-foreground">
        <div className="flex items-center gap-1">
          <FileText className="h-3 w-3" />
          <span>{data.input_file}</span>
        </div>
        {data.stage_count > 0 && (
          <span>{data.stage_count} stages</span>
        )}
      </div>

      {/* Warnings */}
      {data.warnings.length > 0 && (
        <div className="space-y-1 pt-1 border-t border-border/50">
          {data.warnings.map((w, i) => (
            <div key={i} className="flex items-center gap-1.5 text-amber-400/80">
              <AlertTriangle className="h-3 w-3 shrink-0" />
              <span>{w.label} is stale — results may be outdated</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
