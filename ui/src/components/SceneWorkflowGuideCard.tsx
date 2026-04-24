import { Link } from 'react-router-dom'
import { CheckCircle2, Clapperboard, Film, Image as ImageIcon } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { buildSceneWorkspaceRoute } from '@/lib/constants'
import type { SceneWorkflowGuide } from '@/lib/scene-workflow'
import { cn } from '@/lib/utils'

type SceneWorkflowGuideCardProps = {
  projectId: string
  sceneId: string
  guide: SceneWorkflowGuide
  onJumpToPanel?: () => void
}

const STEP_META: Record<
  'shots' | 'storyboard' | 'render',
  { label: string; iconClassName: string }
> = {
  shots: {
    label: 'Shot Plan',
    iconClassName: 'text-violet-400',
  },
  storyboard: {
    label: 'Storyboard',
    iconClassName: 'text-fuchsia-400',
  },
  render: {
    label: 'Render',
    iconClassName: 'text-rose-400',
  },
}

function StepBadge({
  label,
  state,
}: {
  label: string
  state: 'done' | 'current' | 'pending'
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium',
        state === 'done'
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100'
          : state === 'current'
            ? 'border-sky-500/30 bg-sky-500/10 text-sky-100'
            : 'border-border bg-card/50 text-muted-foreground',
      )}
    >
      {label}
    </span>
  )
}

export function SceneWorkflowGuideCard({
  projectId,
  sceneId,
  guide,
  onJumpToPanel,
}: SceneWorkflowGuideCardProps) {
  const Icon = guide.stepId === 'shots'
    ? Clapperboard
    : guide.stepId === 'storyboard'
      ? ImageIcon
      : guide.stepId === 'render'
        ? Film
        : CheckCircle2
  const iconClassName = guide.stepId === 'done'
    ? 'text-emerald-400'
    : STEP_META[guide.stepId].iconClassName

  const steps: Array<{ id: 'shots' | 'storyboard' | 'render'; label: string }> = [
    { id: 'shots', label: STEP_META.shots.label },
    { id: 'storyboard', label: STEP_META.storyboard.label },
    { id: 'render', label: STEP_META.render.label },
  ]

  return (
    <div className="rounded-2xl border border-border bg-card/80 px-4 py-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">
              {guide.stepId === 'done'
                ? 'Scene tutorial complete'
                : `Scene tutorial • Step ${guide.stepNumber} of ${guide.totalSteps}`}
            </Badge>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-xl border border-border bg-muted/40 p-2.5">
              <Icon className={cn('h-5 w-5', iconClassName)} />
            </div>
            <div className="space-y-1.5">
              <h2 className="text-sm font-semibold text-foreground">{guide.title}</h2>
              <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {guide.description}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {steps.map((step, index) => {
              const state = guide.stepId === 'done'
                ? 'done'
                : index + 1 < guide.stepNumber
                  ? 'done'
                  : step.id === guide.stepId
                    ? 'current'
                    : 'pending'
              return <StepBadge key={step.id} label={step.label} state={state} />
            })}
          </div>
        </div>

        {guide.actionKind === 'route' && guide.targetTab && guide.actionLabel && (
          <Button asChild className="shrink-0 self-start">
            <Link to={buildSceneWorkspaceRoute(projectId, sceneId, guide.targetTab)}>
              {guide.actionLabel}
            </Link>
          </Button>
        )}

        {guide.actionKind === 'jump' && guide.actionLabel && onJumpToPanel && (
          <Button
            type="button"
            className="shrink-0 self-start"
            onClick={onJumpToPanel}
          >
            {guide.actionLabel}
          </Button>
        )}
      </div>
    </div>
  )
}
