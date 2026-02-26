import { useNavigate } from 'react-router-dom'
import {
  FileText,
  Globe,
  Compass,
  Camera,
  LayoutGrid,
  Film,
  Check,
  Lock,
  Loader2,
  Circle,
  CircleOff,
  CircleAlert,
  Minus,
  RefreshCw,
} from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { askChatQuestion } from '@/lib/glossary'
import type { PipelineGraphPhase, PipelineGraphNode, PipelineNodeStatus, PipelinePhaseStatus } from '@/lib/types'

const NODE_STATUS_CONFIG: Record<PipelineNodeStatus, {
  icon: React.ComponentType<{ className?: string }>
  className: string
  label: string
}> = {
  completed: { icon: Check, className: 'text-emerald-400', label: 'Complete' },
  stale: { icon: CircleAlert, className: 'text-amber-400', label: 'Needs rerun' },
  in_progress: { icon: Loader2, className: 'text-blue-400 animate-spin', label: 'Running' },
  available: { icon: Circle, className: 'text-foreground/60', label: 'Run now' },
  blocked: { icon: CircleOff, className: 'text-muted-foreground/40', label: 'Blocked' },
  not_implemented: { icon: Minus, className: 'text-muted-foreground/30', label: 'Coming soon' },
}

const PHASE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  FileText,
  Globe,
  Compass,
  Camera,
  LayoutGrid,
  Film,
}

type Props = {
  phases: PipelineGraphPhase[]
  nodes: PipelineGraphNode[]
  projectId: string
}

function statusColor(status: PipelinePhaseStatus): string {
  switch (status) {
    case 'completed':
      return 'text-emerald-400'
    case 'partial':
      return 'text-blue-400'
    case 'available':
      return 'text-foreground'
    case 'blocked':
      return 'text-muted-foreground/50'
    case 'not_started':
      return 'text-muted-foreground/40'
  }
}

function statusDot(status: PipelinePhaseStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-emerald-400'
    case 'partial':
      return 'bg-blue-400'
    case 'available':
      return 'bg-foreground/60'
    case 'blocked':
      return 'bg-muted-foreground/30'
    case 'not_started':
      return 'bg-muted-foreground/20'
  }
}

function PhaseSegment({ phase, nodes, projectId }: {
  phase: PipelineGraphPhase
  nodes: PipelineGraphNode[]
  projectId: string
}) {
  const navigate = useNavigate()
  const Icon = PHASE_ICONS[phase.icon] ?? Film
  const phaseNodes = nodes.filter(n => n.phase_id === phase.id)
  const isClickable = !!phase.nav_route
  const status = phase.status as PipelinePhaseStatus

  const handleClick = () => {
    if (phase.nav_route) {
      navigate(`/${projectId}${phase.nav_route === '/' ? '' : phase.nav_route}`)
    }
  }

  // Build tooltip node list with icons.
  const tooltipNodes = phaseNodes.map(n => {
    const cfg = NODE_STATUS_CONFIG[n.status as PipelineNodeStatus]
    return { node: n, config: cfg }
  })

  // Badge text: show completion count if any nodes completed.
  const badge = phase.completed_count > 0 && phase.implemented_count > 0
    ? `${phase.completed_count}/${phase.implemented_count}`
    : null

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={handleClick}
          disabled={!isClickable}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
            isClickable ? 'cursor-pointer hover:bg-muted/50' : 'cursor-default',
            statusColor(status),
          )}
        >
          {status === 'completed' ? (
            <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          ) : status === 'partial' ? (
            <Icon className="h-3.5 w-3.5 shrink-0" />
          ) : status === 'not_started' && phase.implemented_count === 0 ? (
            <Lock className="h-3.5 w-3.5 shrink-0" />
          ) : (
            <Icon className="h-3.5 w-3.5 shrink-0" />
          )}
          <span className="hidden sm:inline">{phase.label}</span>
          {badge && (
            <span className={cn(
              'text-[10px] px-1 rounded',
              status === 'completed' ? 'bg-emerald-400/20' : 'bg-muted',
            )}>
              {badge}
            </span>
          )}
          {/* Animated pulse for in-progress phases */}
          {phaseNodes.some(n => n.status === 'in_progress') && (
            <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
          )}
          {/* Status dot — visible on narrow screens where label is hidden */}
          <span className={cn('sm:hidden h-1.5 w-1.5 rounded-full shrink-0', statusDot(status))} />
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs bg-popover text-popover-foreground border border-border shadow-lg [&>svg]:fill-popover [&>svg]:bg-popover">
        <div className="text-xs space-y-1">
          <div className="font-semibold mb-1.5">{phase.label}</div>
          {tooltipNodes.map(({ node: n, config: cfg }) => {
            const StatusIcon = cfg.icon
            return (
              <div key={n.id} className="space-y-0.5">
                <div className="flex items-center gap-1.5">
                  <StatusIcon className={cn('h-3 w-3 shrink-0', cfg.className)} />
                  <span className={cn(
                    n.status === 'not_implemented' && 'text-muted-foreground/50',
                  )}>
                    {n.label}
                  </span>
                  {n.artifact_count > 0 && (
                    <span className="text-muted-foreground">({n.artifact_count})</span>
                  )}
                  <span className="text-muted-foreground/60 ml-auto text-[10px]">
                    {cfg.label}
                  </span>
                </div>
                {n.status === 'stale' && (
                  <div className="pl-4.5 space-y-0.5">
                    {n.stale_reason && (
                      <div className="text-amber-400/70 text-[10px]">
                        {n.stale_reason}
                      </div>
                    )}
                    {n.fix_recipe && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          askChatQuestion(`Rerun ${n.fix_recipe} to fix stale ${n.label.toLowerCase()} artifacts`)
                        }}
                        className="flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
                      >
                        <RefreshCw className="h-2.5 w-2.5" />
                        Fix with rerun
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </TooltipContent>
    </Tooltip>
  )
}

export function PipelineBar({ phases, nodes, projectId }: Props) {
  return (
    <div className="shrink-0 border-t border-border bg-card/50 px-2 py-1 flex items-center gap-0.5 overflow-x-auto">
      {phases.map((phase, i) => (
        <div key={phase.id} className="flex items-center">
          {i > 0 && (
            <div className="h-3 w-px bg-border mx-0.5 shrink-0" />
          )}
          <PhaseSegment
            phase={phase}
            nodes={nodes}
            projectId={projectId}
          />
        </div>
      ))}
    </div>
  )
}
