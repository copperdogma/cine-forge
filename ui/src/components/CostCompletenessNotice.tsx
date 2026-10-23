import { AlertTriangle } from 'lucide-react'

import type { CostReceipt } from '@/lib/cost-types'

type Props = {
  receipts: CostReceipt[]
  scope: 'run' | 'project'
}

export function CostCompletenessNotice({ receipts, scope }: Props) {
  return (
    <div role="status" className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
      <div className="flex items-start gap-2 font-medium">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{scope === 'run' ? 'Run' : 'Project'} cost is incomplete</span>
      </div>
      <p className="mt-1 text-muted-foreground">
        Some submitted media charges have no reliable amount yet. The displayed amounts are known estimated subtotals, not provider bills. Budget remaining and cost trends may change when these charges are resolved.
      </p>
      {receipts.length > 0 && (
        <ul className="mt-2 space-y-1 pl-6 list-disc">
          {receipts.map((receipt) => (
            <li key={receipt.receipt_id}>
              {receipt.provider ?? receipt.component} · {receipt.model}
              {receipt.provider_job_id && <> · job {receipt.provider_job_id}</>}
              {receipt.scene_id && <> · scene {receipt.scene_id}</>}
              {receipt.reason && <> — {receipt.reason}</>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
