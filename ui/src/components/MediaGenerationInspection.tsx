import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDuration, formatMoney } from '@/components/render-utils'
import type { MediaExecutionPlanResponse, MediaExecutionUnit } from '@/lib/media-generation-types'
import { selectedMediaClipIds } from '@/lib/media-generation-policy'

type Props = {
  review?: MediaExecutionPlanResponse
  catalog: MediaExecutionUnit[]
  selection: string[] | null
  onSelectionChange: (selection: string[] | null) => void
  disabled: boolean
  stale: boolean
}

export function MediaGenerationInspection({ review, catalog, selection, onSelectionChange, disabled, stale }: Props) {
  const units = catalog
  const allIds = units.flatMap(unit => unit.clip_id ? [unit.clip_id] : [])
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-medium">Choose clips to inspect</p>
        <Button size="sm" variant="outline" disabled={disabled} onClick={() => onSelectionChange(null)}>All current clips</Button>
        {allIds.length > 0 && <Button size="sm" variant="outline" disabled={disabled} onClick={() => onSelectionChange([])}>Clear selection</Button>}
      </div>
      {selection !== null && <p className="text-sm text-muted-foreground">Selected: {selection.length ? selection.join(', ') : 'No clips'}</p>}
      {units.map(unit => (
        <label key={unit.entity_id} className="flex items-start gap-3 rounded-lg border border-border p-3">
          {unit.clip_id && <input type="checkbox" className="mt-1 h-4 w-4 shrink-0" aria-label={`Select ${unit.title}`}
            checked={selection === null || selection.includes(unit.clip_id)} disabled={disabled}
            onChange={() => onSelectionChange(selectedMediaClipIds(selection, allIds, unit.clip_id!))} />}
          <div className="min-w-0 space-y-1 text-sm">
            <p className="font-medium break-words">{unit.title}</p>
            <p>Planned {formatDuration(unit.planned_duration_seconds)} · Provider request {formatDuration(unit.duration_seconds)}</p>
            <p className="break-words">{unit.resolution} · {unit.aspect_ratio} · {unit.provider} / {unit.model}</p>
            <p>Video estimate: {formatMoney(unit.video_estimate_usd) ?? 'Unknown'}</p>
            {unit.price && <p className="text-xs text-muted-foreground break-words">
              USD {unit.price.unit_price_usd} per second · Checked {unit.price.checked_on} ·{' '}
              <a href={unit.price.source_url} target="_blank" rel="noreferrer" className="underline">Price source</a>
            </p>}
          </div>
        </label>
      ))}
      {review && <div className="space-y-2 rounded-lg border border-border p-3 text-sm" aria-live="polite">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{review.plan.units.length} inspected clip{review.plan.units.length === 1 ? '' : 's'}</Badge>
          <Badge variant="outline">{review.plan.status === 'blocked' ? 'Generation blocked' : 'Inspected'}</Badge>
        </div>
        <p>Video-only estimate for the inspected selection: <strong>{formatMoney(review.plan.video_estimate_usd) ?? 'Unknown'}</strong></p>
        <p className="text-muted-foreground">Full workflow total: unknown. This is an estimate, not a spending cap.</p>
        {review.plan.excluded_costs.length > 0 && <div className="text-muted-foreground">
          <p>Excluded or unknown:</p>
          <ul className="ml-4 list-disc">{review.plan.excluded_costs.map(cost => <li key={cost}>{cost}</li>)}</ul>
        </div>}
        {review.plan.blockers.map(blocker => <p key={blocker} className="text-amber-200">{blocker}</p>)}
        {stale && <p className="text-amber-200">Work or selection changed, or the previous confirmation was rejected. Inspect again before confirming.</p>}
      </div>}
    </div>
  )
}
