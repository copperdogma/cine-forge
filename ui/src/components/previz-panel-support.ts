import { formatMoney } from '@/components/render-utils'
import type { PrevizAdoptionStatus, PrevizLaneStatus } from '@/lib/types'

export function formatAdoptionState(value: PrevizLaneStatus['adoption_state'] | null | undefined): string {
  switch (value) {
    case 'default':
      return 'Default'
    case 'recommended_optional':
      return 'Recommended Optional'
    case 'experimental_manual':
      return 'Experimental / Manual'
    default:
      return 'Manual Lane'
  }
}

export function previzDescription(status: PrevizAdoptionStatus | null | undefined): string {
  const base =
    'AI Previz is the shipped generated-motion previz lane. Historical deterministic animatic comparisons remain eval evidence only and are no longer part of the normal previz workflow.'
  if (!status) {
    return `${base} Final footage still lives in the Render tab.`
  }
  return `${base} ${status.policy_summary} Final footage still lives in the Render tab.`
}

export function aiPrevizCostBadge(status: PrevizLaneStatus | null | undefined): string | null {
  if (!status) return null
  const amount = formatMoney(status.cost.estimated_cost_usd ?? null)
  if (status.cost.status === 'verified' && amount) return amount
  if (status.cost.status === 'estimated' && amount) return `Est. ${amount}`
  if (status.cost.status === 'blocked') return 'Cost blocked'
  return null
}
