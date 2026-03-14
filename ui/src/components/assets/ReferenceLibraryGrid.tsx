import { Sparkles } from 'lucide-react'

import { ReferenceCard } from './ReferenceLibraryCard'
import type { ReferenceItem } from './reference-library-model'

export function ReferenceLibraryGrid({
  isLoading,
  items,
  onPreview,
}: {
  isLoading: boolean
  items: ReferenceItem[]
  onPreview: (item: ReferenceItem) => void
}) {
  if (isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {[0, 1, 2].map(index => (
          <div key={index} className="h-64 animate-pulse rounded-2xl border border-border bg-muted/30" />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border/70 bg-muted/15 px-6 py-10 text-center">
        <Sparkles className="mx-auto mb-3 h-5 w-5 text-muted-foreground" />
        <p className="text-sm font-medium">No references match the current filter</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Upload a batch above or switch the filter to browse the full reference stack.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {items.map(item => (
        <ReferenceCard
          key={item.id}
          item={item}
          onPreview={() => onPreview(item)}
        />
      ))}
    </div>
  )
}
