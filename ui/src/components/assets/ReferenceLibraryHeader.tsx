import { Layers3 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function ReferenceLibraryHeader({
  title,
  description,
  activeReferenceHint,
  uploadedCount,
  aiCount,
  activeCount,
  hasAiItems,
}: {
  title: string
  description: string
  activeReferenceHint: string
  uploadedCount: number
  aiCount: number
  activeCount: number
  hasAiItems: boolean
}) {
  return (
    <CardHeader className="border-b border-border/50 bg-gradient-to-r from-sky-500/8 via-background to-emerald-500/8">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Layers3 className="h-4 w-4 text-sky-300" />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <CardDescription className="max-w-2xl text-sm leading-relaxed">
            {description}
          </CardDescription>
          <p className="text-xs text-muted-foreground">{activeReferenceHint}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{uploadedCount} uploaded</Badge>
          {hasAiItems && <Badge variant="outline">{aiCount} AI study</Badge>}
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-200">
            {activeCount} active
          </Badge>
        </div>
      </div>
    </CardHeader>
  )
}
