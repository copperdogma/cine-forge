import { Compass, Loader2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { VisualCreativeBrief } from '@/lib/api'

interface CreativeBriefPreviewCardProps {
  brief: VisualCreativeBrief | null | undefined
  isLoading?: boolean
}

export function CreativeBriefPreviewCard({
  brief,
  isLoading = false,
}: CreativeBriefPreviewCardProps) {
  return (
    <Card className="border-border/70">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base">
              <Compass className="h-4 w-4 text-sky-400" />
              Compiled Creative Brief
            </CardTitle>
            <CardDescription>
              Read-only preview compiled from saved Intent inputs and active project taste references.
            </CardDescription>
          </div>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!brief ? (
          <p className="text-sm text-muted-foreground">
            Save project-level taste inputs to compile the shared brief preview.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5">
              {brief.sources_used.map(source => (
                <Badge key={source} variant="secondary" className="text-[10px] tracking-wide">
                  {source.replaceAll('_', ' ')}
                </Badge>
              ))}
            </div>
            <p className="text-sm text-foreground">{brief.operator_preview}</p>
            <div className="space-y-1.5">
              {brief.summary_lines.map((line) => (
                <p key={line} className="text-xs text-muted-foreground">
                  {line}
                </p>
              ))}
            </div>
            {brief.active_project_references.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-foreground">Active project references</p>
                <div className="space-y-2">
                  {brief.active_project_references.map((reference) => (
                    <div
                      key={reference.asset_id}
                      className="rounded-md border border-border/60 bg-muted/20 p-2"
                    >
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge variant="outline" className="text-[10px]">
                          {reference.filename}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px]">
                          {reference.purpose}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px]">
                          {reference.lock_status}
                        </Badge>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {reference.transparency_note}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

