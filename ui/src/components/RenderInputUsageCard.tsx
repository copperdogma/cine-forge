import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatToken, type RenderInputUsageView } from '@/components/render-utils'

type RenderInputUsageCardProps = {
  inputs: RenderInputUsageView[]
  title?: string
}

export function RenderInputUsageCard({
  inputs,
  title = 'Resolved Inputs',
}: RenderInputUsageCardProps) {
  if (inputs.length === 0) return null

  return (
    <Card className="gap-0">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {inputs.map(input => (
          <div
            key={input.inputId}
            className="rounded-lg border border-border bg-card/60 px-4 py-3"
          >
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  {input.label ?? formatToken(input.kind) ?? input.inputId}
                </p>
                {input.relativePath && (
                  <p className="font-mono text-xs text-muted-foreground">{input.relativePath}</p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {formatToken(input.usedAs) && (
                  <Badge variant="outline">{formatToken(input.usedAs)}</Badge>
                )}
                {formatToken(input.kind) && (
                  <Badge variant="secondary">{formatToken(input.kind)}</Badge>
                )}
                {input.required && <Badge variant="secondary">Required</Badge>}
                {formatToken(input.lockStatus) && (
                  <Badge variant="outline">{formatToken(input.lockStatus)}</Badge>
                )}
                {input.sourceRef?.artifactType && (
                  <Badge variant="outline">
                    {input.sourceRef.artifactType}
                    {input.sourceRef.version !== null ? ` v${input.sourceRef.version}` : ''}
                  </Badge>
                )}
              </div>
            </div>
            {(input.notes || input.mediaType) && (
              <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                {input.notes && <p>{input.notes}</p>}
                {input.mediaType && <p>Media type: {input.mediaType}</p>}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
