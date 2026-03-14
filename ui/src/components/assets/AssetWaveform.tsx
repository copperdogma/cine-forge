import { cn } from '@/lib/utils'

export function AssetWaveform({
  points,
  className,
}: {
  points: number[]
  className?: string
}) {
  if (points.length === 0) {
    return (
      <div className={cn('rounded-lg border border-dashed border-border/60 p-3 text-xs text-muted-foreground', className)}>
        Waveform unavailable
      </div>
    )
  }

  return (
    <div className={cn('rounded-lg border border-border/60 bg-muted/30 px-3 py-2.5', className)}>
      <div className="flex h-14 items-end gap-[2px]">
        {points.map((point, index) => (
          <div
            key={`${index}-${point}`}
            className="flex-1 rounded-full bg-emerald-400/80"
            style={{ height: `${Math.max(point * 100, 8)}%` }}
          />
        ))}
      </div>
    </div>
  )
}
