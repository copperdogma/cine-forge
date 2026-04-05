import { forwardRef, useState } from 'react'
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
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { useIsMobile } from '@/lib/use-mobile'
import { cn } from '@/lib/utils'
import { askChatQuestion } from '@/lib/glossary'
import type {
  PipelineGraphNode,
  PipelineGraphPhase,
  PipelineNodeStatus,
  PipelinePhaseStatus,
} from '@/lib/types'

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
  defaultSceneId?: string | null
}

type PhaseNodeWithConfig = {
  node: PipelineGraphNode
  config: (typeof NODE_STATUS_CONFIG)[PipelineNodeStatus]
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

function PhaseDetails({
  phase,
  tooltipNodes,
  isClickable,
  onNavigate,
  showTitle = true,
}: {
  phase: PipelineGraphPhase
  tooltipNodes: PhaseNodeWithConfig[]
  isClickable: boolean
  onNavigate?: () => void
  showTitle?: boolean
}) {
  return (
    <div className="space-y-2 text-xs">
      {showTitle && <div className="font-semibold">{phase.label}</div>}
      <div className="space-y-1">
        {tooltipNodes.map(({ node: n, config: cfg }) => {
          const StatusIcon = cfg.icon
          return (
            <div key={n.id} className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <StatusIcon className={cn('h-3 w-3 shrink-0', cfg.className)} />
                <span className={cn(n.status === 'not_implemented' && 'text-muted-foreground/50')}>
                  {n.label}
                </span>
                {n.artifact_count > 0 && (
                  <span className="text-muted-foreground">({n.artifact_count})</span>
                )}
                <span className="ml-auto text-[10px] text-muted-foreground/60">
                  {cfg.label}
                </span>
              </div>
              {n.status === 'stale' && (
                <div className="space-y-0.5 pl-4.5">
                  {n.stale_reason && (
                    <div className="text-[10px] text-amber-400/70">
                      {n.stale_reason}
                    </div>
                  )}
                  {n.fix_recipe && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        askChatQuestion(`Rerun ${n.fix_recipe} to fix stale ${n.label.toLowerCase()} artifacts`)
                      }}
                      className="flex cursor-pointer items-center gap-1 text-[10px] text-blue-400 transition-colors hover:text-blue-300"
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
      {isClickable && onNavigate && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-1 h-8 w-full"
          onClick={(e) => {
            e.stopPropagation()
            onNavigate()
          }}
        >
          Open {phase.label}
        </Button>
      )}
    </div>
  )
}

const PhaseTrigger = forwardRef<HTMLButtonElement, {
  badge: string | null
  isClickable: boolean
  compact?: boolean
  onClick?: () => void
  phaseNodes: PipelineGraphNode[]
  phase: PipelineGraphPhase
  status: PipelinePhaseStatus
}>(function PhaseTrigger({
  badge,
  isClickable,
  compact = false,
  onClick,
  phaseNodes,
  phase,
  status,
}, ref) {
  const Icon = PHASE_ICONS[phase.icon] ?? Film

  return (
    <button
      ref={ref}
      type="button"
      onClick={onClick}
      disabled={!onClick && !isClickable}
      aria-label={phase.label}
      className={cn(
        'flex items-center rounded-md text-xs font-medium transition-all',
        compact ? 'gap-1 px-2 py-1.5' : 'gap-1.5 px-3 py-1.5',
        isClickable ? 'cursor-pointer hover:bg-muted/50' : 'cursor-default',
        statusColor(status),
      )}
    >
      {compact ? (
        <Icon className="h-3.5 w-3.5 shrink-0" />
      ) : status === 'completed' ? (
        <Check className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
      ) : status === 'partial' ? (
        <Icon className="h-3.5 w-3.5 shrink-0" />
      ) : status === 'not_started' && phase.implemented_count === 0 ? (
        <Lock className="h-3.5 w-3.5 shrink-0" />
      ) : (
        <Icon className="h-3.5 w-3.5 shrink-0" />
      )}
      <span className="hidden sm:inline">{phase.label}</span>
      {badge && !compact && (
        <span
          className={cn(
            'rounded px-1 text-[10px]',
            status === 'completed' ? 'bg-emerald-400/20' : 'bg-muted',
          )}
        >
          {badge}
        </span>
      )}
      {phaseNodes.some((n) => n.status === 'in_progress') && (
        <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
      )}
      <span className={cn('h-1.5 w-1.5 shrink-0 rounded-full sm:hidden', statusDot(status))} />
    </button>
  )
})

function PhaseSegment({
  phase,
  nodes,
  projectId,
  isMobile,
  defaultSceneId,
}: {
  phase: PipelineGraphPhase
  nodes: PipelineGraphNode[]
  projectId: string
  isMobile: boolean
  defaultSceneId?: string | null
}) {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const phaseNodes = nodes.filter((n) => n.phase_id === phase.id)
  const sceneWorkspaceTab =
    phase.id === 'shots'
      ? 'shots'
      : phase.id === 'storyboards'
        ? 'storyboard'
        : phase.id === 'production'
          ? 'render'
          : null
  const sceneWorkspaceRoute =
    defaultSceneId && sceneWorkspaceTab
      ? `/${projectId}/scenes/${defaultSceneId}?tab=${sceneWorkspaceTab}`
      : null
  const isClickable = !!phase.nav_route || !!sceneWorkspaceRoute
  const status = phase.status as PipelinePhaseStatus

  const handleNavigate = () => {
    if (phase.nav_route) {
      navigate(`/${projectId}${phase.nav_route === '/' ? '' : phase.nav_route}`)
      return
    }
    if (sceneWorkspaceRoute) {
      navigate(sceneWorkspaceRoute)
    }
  }

  const tooltipNodes = phaseNodes.map((n) => ({
    node: n,
    config: NODE_STATUS_CONFIG[n.status as PipelineNodeStatus],
  }))

  const badge = phase.completed_count > 0 && phase.implemented_count > 0
    ? `${phase.completed_count}/${phase.implemented_count}`
    : null

  if (isMobile) {
    return (
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <PhaseTrigger
            badge={badge}
            isClickable={isClickable}
            compact
            onClick={() => undefined}
            phaseNodes={phaseNodes}
            phase={phase}
            status={status}
          />
        </SheetTrigger>
        <SheetContent
          side="bottom"
          className="max-h-[70vh] gap-0 rounded-t-2xl px-0 pb-0"
        >
          <SheetHeader className="border-b pb-3">
            <SheetTitle>{phase.label}</SheetTitle>
            <SheetDescription>Phase modules and current status.</SheetDescription>
          </SheetHeader>
          <div className="overflow-y-auto px-4 pb-4">
            <PhaseDetails
              phase={phase}
              tooltipNodes={tooltipNodes}
              isClickable={isClickable}
              onNavigate={() => {
                setIsOpen(false)
                handleNavigate()
              }}
              showTitle={false}
            />
          </div>
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <div
          className="relative"
          onMouseEnter={() => setIsOpen(true)}
          onMouseLeave={() => setIsOpen(false)}
          onFocusCapture={() => setIsOpen(true)}
          onBlurCapture={(event) => {
            const nextTarget = event.relatedTarget
            if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
              setIsOpen(false)
            }
          }}
        >
          <PhaseTrigger
            badge={badge}
            isClickable={isClickable}
            onClick={isClickable ? handleNavigate : undefined}
            phaseNodes={phaseNodes}
            phase={phase}
            status={status}
          />
        </div>
      </PopoverTrigger>
      <PopoverContent
        side="bottom"
        align="center"
        sideOffset={8}
        className="w-[min(22rem,calc(100vw-2rem))] p-3"
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <PhaseDetails phase={phase} tooltipNodes={tooltipNodes} isClickable={false} />
      </PopoverContent>
    </Popover>
  )
}

export function PipelineBar({ phases, nodes, projectId, defaultSceneId }: Props) {
  const isMobile = useIsMobile()

  return (
    <div className="flex shrink-0 items-center gap-0.5 overflow-x-auto border-t border-border bg-card/50 px-2 py-1">
      {phases.map((phase, i) => (
        <div key={phase.id} className="flex items-center">
          {i > 0 && (
            <div className="mx-0.5 h-3 w-px shrink-0 bg-border" />
          )}
          <PhaseSegment
            phase={phase}
            nodes={nodes}
            projectId={projectId}
            isMobile={isMobile}
            defaultSceneId={defaultSceneId}
          />
        </div>
      ))}
    </div>
  )
}
