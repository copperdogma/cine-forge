import { formatMoney } from '@/components/render-utils'
import type { PrevizLaneStatus } from '@/lib/previz-types'

export function PrevizCostExample({ status }: { status?: PrevizLaneStatus | null }) {
  const cost = status?.cost
  if (
    cost?.status !== 'estimated'
    || !cost.price
    || cost.duration_seconds == null
    || cost.estimated_cost_usd == null
  ) return null

  const price = cost.price
  return (
    <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
      <p>
        Recipe-default video example: {cost.duration_seconds}s ×{' '}
        {formatMoney(price.unit_price_usd)}/second ={' '}
        {formatMoney(cost.estimated_cost_usd)} estimated for{' '}
        {price.provider} {price.model} at {price.resolution}.
      </p>
      <p className="mt-1">
        List price checked {price.checked_on}.{' '}
        <a
          href={price.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 hover:text-foreground"
        >
          Pricing source
        </a>
      </p>
      <p className="mt-1">
        This is one video example, not a scene or run cost quote. It excludes prompt compilation,
        backfill, validation, and additional clips; actual plans may use different durations.
      </p>
    </div>
  )
}
