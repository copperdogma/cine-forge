import { CheckCircle2, ChevronDown, ChevronUp, GitBranch, Heart, Loader2, RotateCcw, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DesignStudyImageCard } from '@/components/DesignStudyImageCard'
import { DesignStudyRoundStatusPanel } from '@/components/DesignStudyRoundStatusPanel'
import { DesignStudySourcesPanel } from '@/components/DesignStudySourcesPanel'
import { getDesignStudyImageUrl } from '@/lib/api'
import { getDesignStudyProgressText, getDesignStudyRoundStatus } from '@/lib/design-study-status'
import { cn } from '@/lib/utils'
import type { DesignStudyImage, DesignStudyRound, ImageDecision } from '@/lib/api'

type CompositionRefPolarity = 'positive' | 'negative'

const MODEL_LABELS: Record<string, string> = {
  'imagen-4.0-generate-001': 'Imagen 4',
  'gpt-image-1': 'GPT-Image',
}

function modelLabel(model: string): string {
  return MODEL_LABELS[model] ?? model
}

function decisionBadge(decision: ImageDecision) {
  switch (decision) {
    case 'selected_final':
      return {
        icon: <CheckCircle2 className="h-3 w-3" />,
        className: 'bg-emerald-600 text-white',
      }
    case 'favorite':
      return {
        icon: <Heart className="h-3 w-3" />,
        className: 'bg-amber-400 text-black',
      }
    case 'rejected':
      return {
        icon: <XCircle className="h-3 w-3" />,
        className: 'bg-destructive text-white',
      }
    case 'seed_for_variants':
      return {
        icon: <GitBranch className="h-3 w-3" />,
        className: 'bg-sky-500 text-white',
      }
    default:
      return null
  }
}

interface Props {
  round: DesignStudyRound
  images: DesignStudyImage[]
  projectId: string
  entityId: string
  expanded: boolean
  isLatest: boolean
  isDeciding: boolean
  positiveRefs: string[]
  negativeRefs: string[]
  onExpand: () => void
  onRegenerateFromHere: (round: DesignStudyRound) => void
  onDecide: (filename: string, decision: ImageDecision, guidance?: string) => void
  onComposeRef: (filename: string, polarity: CompositionRefPolarity) => void
}

export function ContactSheetRow({
  round,
  images,
  projectId,
  entityId,
  expanded,
  isLatest,
  isDeciding,
  positiveRefs,
  negativeRefs,
  onExpand,
  onRegenerateFromHere,
  onDecide,
  onComposeRef,
}: Props) {
  const status = getDesignStudyRoundStatus(round)

  return (
    <section
      className={cn(
        'rounded-xl border border-border/70 bg-card/70 transition-colors',
        expanded && 'border-primary/30 bg-primary/5',
        status === 'failed' && 'border-destructive/40',
        status === 'generating' && 'border-sky-500/30',
      )}
    >
      <div className="flex flex-col gap-3 px-3 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <button
            type="button"
            className="flex-1 text-left"
            onClick={onExpand}
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">Round {round.round_number}</span>
              <span className="text-xs text-muted-foreground">{modelLabel(round.model)}</span>
              {status === 'generating' && <Loader2 className="h-3.5 w-3.5 animate-spin text-sky-300" />}
            </div>
            <p className="text-xs text-muted-foreground">
              {status === 'completed'
                ? `${images.length} visible of ${round.images.length} image${round.images.length !== 1 ? 's' : ''} ${expanded ? 'shown full size below.' : 'in the contact sheet.'}`
                : getDesignStudyProgressText(round)}
            </p>
          </button>

          <div className="flex items-center gap-2">
            {!isLatest && (
              <Button
                type="button"
                variant="outline"
                size="xs"
                onClick={() => onRegenerateFromHere(round)}
              >
                <RotateCcw className="h-3 w-3" />
                Regenerate from here
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              size="xs"
              onClick={onExpand}
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {expanded ? 'Expanded' : 'Expand'}
            </Button>
          </div>
        </div>

        {round.images.length > 0 ? (
          <button
            type="button"
            onClick={onExpand}
            className="grid auto-cols-[88px] grid-flow-col gap-2 overflow-x-auto pb-1 text-left"
          >
            {round.images.map((image, index) => {
              const badge = decisionBadge(image.decision)
              return (
                <span
                  key={image.filename}
                  className={cn(
                    'relative block overflow-hidden rounded-lg border border-border/60 bg-muted/20',
                    image.decision === 'rejected' && 'opacity-50 grayscale',
                  )}
                >
                  <img
                    src={getDesignStudyImageUrl(projectId, entityId, image.filename)}
                    alt={`Round ${round.round_number} study ${index + 1}`}
                    className="h-24 w-[88px] object-cover object-top"
                  />
                  <span className="absolute right-1 top-1 rounded bg-black/70 px-1 font-mono text-[10px] text-white">
                    {index + 1}
                  </span>
                  {badge && (
                    <span
                      className={cn(
                        'absolute left-1 top-1 rounded px-1 py-0.5',
                        badge.className,
                      )}
                    >
                      {badge.icon}
                    </span>
                  )}
                </span>
              )
            })}
          </button>
        ) : (
          <button
            type="button"
            onClick={onExpand}
            className="flex h-24 items-center justify-center rounded-lg border border-dashed border-border/70 bg-muted/20 text-xs text-muted-foreground"
          >
            {status === 'generating' ? 'Waiting for provider image…' : 'No images saved for this round'}
          </button>
        )}
      </div>

      {expanded && (
        <div className="space-y-3 border-t border-border/60 px-3 py-3">
          <DesignStudyRoundStatusPanel round={round} />
          <DesignStudySourcesPanel round={round} defaultOpen={isLatest} />
          {images.length > 0 ? (
            <div className="grid gap-3">
              {images.map((img, index) => (
                <DesignStudyImageCard
                  key={img.filename}
                  img={img}
                  index={index + 1}
                  projectId={projectId}
                  entityId={entityId}
                  onDecide={onDecide}
                  isDeciding={isDeciding}
                  onComposeRef={onComposeRef}
                  compositionState={
                    positiveRefs.includes(img.filename)
                      ? 'positive'
                      : negativeRefs.includes(img.filename)
                        ? 'negative'
                        : null
                  }
                />
              ))}
            </div>
          ) : (
            <p className="text-xs italic text-muted-foreground">
              No images in this round match the current filter.
            </p>
          )}
        </div>
      )}
    </section>
  )
}
