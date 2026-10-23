import { DollarSign } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { asArray, asNumber, asRecord, asString, formatMoney } from '@/components/render-utils'

type UnresolvedCharge = {
  id: string
  provider: string | null
  model: string | null
  jobId: string | null
  reason: string | null
}

type VideoCostView = {
  amountUsd: number | null
  complete: boolean | null
  unresolved: UnresolvedCharge[]
}

function parseGeneratedVideoCost(data: Record<string, unknown>): VideoCostView {
  const cost = asRecord(data.cost)
  const complete = typeof data.cost_is_complete === 'boolean' ? data.cost_is_complete : null
  const unresolved = asArray(data.cost_receipts)
    .map((value) => asRecord(value))
    .filter((receipt) => receipt?.status === 'uncertain')
    .map((receipt, index) => ({
      id: asString(receipt?.receipt_id) ?? `unresolved-${index}`,
      provider: asString(receipt?.provider),
      model: asString(receipt?.model),
      jobId: asString(receipt?.provider_job_id),
      reason: asString(receipt?.reason),
    }))
  return { amountUsd: asNumber(cost?.estimated_cost_usd), complete, unresolved }
}

export function GeneratedVideoCost({ data }: { data: Record<string, unknown> }) {
  const cost = parseGeneratedVideoCost(data)
  const amount = formatMoney(cost.amountUsd)
  const label = cost.complete === true
    ? 'Estimated generation cost'
    : cost.complete === false
      ? 'Known estimated subtotal'
      : 'Recorded estimate · completeness unknown'
  return (
    <>
      {amount && (
        <Badge
          variant="outline"
          className="h-auto max-w-full min-w-0 shrink whitespace-normal break-words justify-start text-left"
        >
          <DollarSign className="h-3 w-3 shrink-0" />
          <span className="min-w-0 break-words">{label}: {amount}</span>
        </Badge>
      )}
      {cost.complete !== true && (
        <div role="status" className="w-full min-w-0 break-words rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-sm text-muted-foreground">
          {cost.complete === false
            ? amount
              ? 'Generation cost is incomplete. The amount shown includes only known estimates; unresolved provider charges may add cost.'
              : 'Generation cost is incomplete. A provider charge amount remains unresolved.'
            : amount
              ? 'This saved video has no cost-completeness record. Its amount is an unverified historical estimate.'
              : 'This saved video has no cost-completeness record or verified amount.'}
          {cost.unresolved.length > 0 && (
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {cost.unresolved.map((charge) => (
                <li key={charge.id}>
                  {charge.provider ?? 'Provider'}
                  {charge.model && <> · {charge.model}</>}
                  {charge.jobId && <> · job {charge.jobId}</>}
                  {charge.reason && <> — {charge.reason}</>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </>
  )
}
