import { Link } from 'react-router-dom'
import { ExternalLink, Loader2 } from 'lucide-react'
import { HealthBadge } from '@/components/HealthBadge'
import { PrevizCostExample } from '@/components/PrevizCostExample'
import { formatLatencyMs } from '@/components/preview-provenance'
import { formatAdoptionState } from '@/components/previz-panel-support'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { ArtifactGroupSummary, PrevizLaneStatus } from '@/lib/types'

type Props = {
  status?: PrevizLaneStatus
  primaryGroup?: ArtifactGroupSummary
  detailHref: string | null
  promptHref: string | null
  validationHref: string | null
  hasSavedOutput: boolean
  running: boolean
}
export function PrevizLaneEvidence({ status, primaryGroup, detailHref, promptHref, validationHref, hasSavedOutput, running }: Props) {
  return (
    <Card className="gap-0 border-sky-500/30">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-lg">{status?.label ?? 'AI Previz'}</CardTitle>
          {status && <Badge variant="outline">{formatAdoptionState(status.adoption_state)}</Badge>}
          {primaryGroup && <HealthBadge health={primaryGroup.health} details={primaryGroup.health_details} />}
        </div>
        <CardDescription>{status?.fidelity_disclosure ?? 'Low-fidelity motion and staging review. Final footage belongs in Render.'}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {status && <p className="text-muted-foreground">{status.reason} {status.intended_use}</p>}
        <PrevizCostExample status={status} />
        {status && <div className="flex flex-wrap gap-2">
          {status.latency_ms != null && <Badge variant="outline">Measured first pass {formatLatencyMs(status.latency_ms)}</Badge>}
          {status.regenerate_reuse_latency_ms != null && <Badge variant="outline">Measured reuse {formatLatencyMs(status.regenerate_reuse_latency_ms)}</Badge>}
          {status.regenerate_full_latency_ms != null && <Badge variant="outline">Measured full regeneration {formatLatencyMs(status.regenerate_full_latency_ms)}</Badge>}
        </div>}
        <div className="flex flex-wrap gap-2">
          {[[detailHref, 'AI Previz Detail'], [promptHref, 'Prompt Detail'], [validationHref, 'Validation Detail']].map(([href, label]) => href && (
            <Button asChild key={label} variant="outline" size="sm"><Link to={href}><ExternalLink className="h-3.5 w-3.5" />{label}</Link></Button>
          ))}
        </div>
        {running && <p className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" />AI previz generation is running.</p>}
        {!hasSavedOutput && !running && <p className="text-muted-foreground">No AI previz is saved yet. Prepare and inspect the clips above before confirming a motion pass.</p>}
      </CardContent>
    </Card>
  )
}
