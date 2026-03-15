import { Check, Loader2 } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { PRODUCTION_FORMAT_OPTIONS } from '@/lib/production-format'
import type { ProductionFormat } from '@/lib/types'

interface ProductionFormatModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelect: (format: ProductionFormat) => void | Promise<void>
  selectedFormat?: ProductionFormat | null
  onSkip?: () => void | Promise<void>
  pending?: boolean
  title?: string
  description?: string
}

export function ProductionFormatModal({
  open,
  onOpenChange,
  onSelect,
  selectedFormat = null,
  onSkip,
  pending = false,
  title = 'Choose a visual medium',
  description = 'Pick the broad image archetype CineForge should target for image generation in this project.',
}: ProductionFormatModalProps) {
  return (
    <Dialog open={open} onOpenChange={pending ? undefined : onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2">
          {PRODUCTION_FORMAT_OPTIONS.map((option) => {
            const isSelected = option.value === selectedFormat
            return (
              <button
                key={option.value}
                type="button"
                disabled={pending}
                onClick={() => onSelect(option.value)}
                className={cn(
                  'rounded-xl border p-4 text-left transition-colors',
                  'hover:border-primary/60 hover:bg-accent/40',
                  isSelected && 'border-primary bg-primary/8',
                  pending && 'cursor-not-allowed opacity-70',
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold">{option.label}</div>
                    <p className="mt-1 text-sm text-muted-foreground">{option.description}</p>
                  </div>
                  <span className="mt-0.5 flex size-5 items-center justify-center">
                    {pending && isSelected ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : isSelected ? (
                      <Check className="size-4 text-primary" />
                    ) : null}
                  </span>
                </div>
              </button>
            )
          })}
        </div>

        {onSkip && (
          <DialogFooter>
            <Button variant="ghost" onClick={() => onSkip()} disabled={pending}>
              Skip for now
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
