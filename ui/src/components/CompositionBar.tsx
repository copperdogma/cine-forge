import { Loader2, Minus, Plus, Wand2, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

type CompositionRefPolarity = 'positive' | 'negative'

type ModelOption = {
  id: string
  label: string
}

type CompositionRefChip = {
  filename: string
  label: string
}

interface Props {
  directive: string
  positiveRefs: CompositionRefChip[]
  negativeRefs: CompositionRefChip[]
  count: 1 | 2 | 4 | 8
  model: string
  models: ModelOption[]
  canGenerate: boolean
  isGenerating: boolean
  generationLabel: string
  errorMessage?: string | null
  latestSeedFilename?: string | null
  useSeedVariants: boolean
  onDirectiveChange: (value: string) => void
  onCountChange: (count: 1 | 2 | 4 | 8) => void
  onModelChange: (model: string) => void
  onRemoveRef: (filename: string, polarity: CompositionRefPolarity) => void
  onToggleSeedVariants: () => void
  onGenerate: () => void
}

function RefChip({
  chip,
  polarity,
  onRemove,
}: {
  chip: CompositionRefChip
  polarity: CompositionRefPolarity
  onRemove: (filename: string, polarity: CompositionRefPolarity) => void
}) {
  const positive = polarity === 'positive'
  return (
    <span
      className={cn(
        'inline-flex max-w-full items-center gap-1 rounded-full border px-2 py-1 text-[11px]',
        positive
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
          : 'border-destructive/30 bg-destructive/10 text-red-200',
      )}
    >
      {positive ? <Plus className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
      <span className="truncate">{chip.label}</span>
      <button
        type="button"
        className="rounded-full p-0.5 transition-colors hover:bg-black/10"
        onClick={() => onRemove(chip.filename, polarity)}
        aria-label={`Remove ${chip.label}`}
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  )
}

export function CompositionBar({
  directive,
  positiveRefs,
  negativeRefs,
  count,
  model,
  models,
  canGenerate,
  isGenerating,
  generationLabel,
  errorMessage = null,
  latestSeedFilename = null,
  useSeedVariants,
  onDirectiveChange,
  onCountChange,
  onModelChange,
  onRemoveRef,
  onToggleSeedVariants,
  onGenerate,
}: Props) {
  return (
    <div className="sticky bottom-3 z-20 rounded-xl border border-border/70 bg-card/95 p-3 shadow-xl backdrop-blur">
      <div className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold">Next round</h4>
              <Badge variant="outline" className="text-[10px]">
                {positiveRefs.length + negativeRefs.length} ref
                {positiveRefs.length + negativeRefs.length !== 1 ? 's' : ''}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Stage positive and negative references, set a directive, then generate the next pass.
            </p>
          </div>
          {latestSeedFilename && (
            <button
              type="button"
              onClick={onToggleSeedVariants}
              className={cn(
                'rounded-full border px-2.5 py-1 text-xs transition-colors',
                useSeedVariants
                  ? 'border-sky-400/40 bg-sky-500/20 text-sky-100'
                  : 'border-border bg-background text-muted-foreground hover:bg-muted',
              )}
            >
              {useSeedVariants ? 'Seed on' : 'Seed off'}
            </button>
          )}
        </div>

        <div className="space-y-2 rounded-lg border border-border/60 bg-muted/20 p-3">
          <div className="flex flex-wrap gap-2">
            {positiveRefs.map(chip => (
              <RefChip
                key={`positive-${chip.filename}`}
                chip={chip}
                polarity="positive"
                onRemove={onRemoveRef}
              />
            ))}
            {negativeRefs.map(chip => (
              <RefChip
                key={`negative-${chip.filename}`}
                chip={chip}
                polarity="negative"
                onRemove={onRemoveRef}
              />
            ))}
            {positiveRefs.length === 0 && negativeRefs.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No composition refs yet. Use the image card ref buttons to stage them here.
              </p>
            )}
          </div>
          {latestSeedFilename && (
            <p className="text-xs text-muted-foreground">
              Seed candidate: <span className="font-mono text-foreground">{latestSeedFilename}</span>
              {' '}
              {useSeedVariants
                ? 'will also guide the next prompt.'
                : 'is available but currently disabled.'}
            </p>
          )}
        </div>

        <Textarea
          placeholder="Directive for the next round — e.g. 'older, harsher silhouette, less polished wardrobe'"
          value={directive}
          onChange={event => onDirectiveChange(event.target.value)}
          className="min-h-20 resize-none text-sm"
        />

        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              {([1, 2, 4, 8] as const).map(option => (
                <button
                  key={option}
                  type="button"
                  onClick={() => onCountChange(option)}
                  className={cn(
                    'h-7 w-7 rounded border text-xs transition-colors',
                    count === option
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-background text-muted-foreground hover:bg-muted',
                  )}
                >
                  {option}
                </button>
              ))}
              <span className="text-xs text-muted-foreground">
                image{count !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {models.map(option => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => onModelChange(option.id)}
                  className={cn(
                    'rounded border px-2 py-1 text-xs transition-colors',
                    model === option.id
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-background text-muted-foreground hover:bg-muted',
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <Button
            size="sm"
            className="min-w-36 justify-center"
            disabled={!canGenerate || isGenerating}
            onClick={onGenerate}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                {generationLabel}
              </>
            ) : (
              <>
                <Wand2 className="h-3.5 w-3.5" />
                Generate
              </>
            )}
          </Button>
        </div>

        {errorMessage && <p className="text-xs text-destructive">{errorMessage}</p>}
      </div>
    </div>
  )
}
