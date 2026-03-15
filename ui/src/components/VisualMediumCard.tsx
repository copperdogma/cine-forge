import { Film } from 'lucide-react'

import { ProductionFormatPill } from '@/components/ProductionFormatPill'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { ProductionFormat } from '@/lib/types'

interface VisualMediumCardProps {
  projectId: string
  value: ProductionFormat | null
  className?: string
}

export function VisualMediumCard({ projectId, value, className }: VisualMediumCardProps) {
  return (
    <Card id="visual-medium" className={cn('border-primary/20 bg-primary/5', className)}>
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base">
              <Film className="h-4 w-4 text-primary" />
              Visual Medium
            </CardTitle>
            <CardDescription className="max-w-2xl text-sm leading-relaxed">
              Pick the broad image archetype first. Then use presets, reference films, and written
              direction below to ground the taste.
            </CardDescription>
          </div>
          <ProductionFormatPill
            projectId={projectId}
            value={value}
            mode="edit"
            className="h-8 rounded-full px-3 text-xs"
          />
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="max-w-3xl text-sm text-muted-foreground">
          This is the top-level medium choice, not the whole aesthetic. &ldquo;Live Action&rdquo;
          vs. &ldquo;Anime&rdquo; belongs here; directors, films, mood boards, and vibe notes
          belong in the rest of Intent & Mood.
        </p>
      </CardContent>
    </Card>
  )
}
