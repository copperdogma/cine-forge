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

export function primaryLaneLabel(status: PrevizAdoptionStatus | null | undefined): string {
  if (!status) return 'AI Previz'
  return status.primary_lane === 'ai_previz'
    ? status.ai_previz.label
    : status.deterministic_previz.label
}

export function previzDescription(status: PrevizAdoptionStatus | null | undefined): string {
  const base =
    'AI Previz is the intended generated-motion previz lane. Deterministic Baseline is the explicit fallback/control animatic, not the product previz answer.'
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

export function deterministicReuseDescription(
  startFrom: string | undefined,
  configuredScopeTarget: string,
): string | null {
  switch (startFrom) {
    case 'storyboards':
      return (
        `Reuse path: CineForge will keep the current shot plan and regenerate storyboard frames, ` +
        `animatics, and keyframes for ${configuredScopeTarget}.`
      )
    case 'animatics':
      return (
        `Reuse path: CineForge will keep the current shot plan and storyboard and rerun only ` +
        `animatics plus keyframes for ${configuredScopeTarget}.`
      )
    case 'keyframes':
      return (
        `Reuse path: CineForge will keep the current shot plan, storyboard, and animatic and ` +
        `rerun only keyframes for ${configuredScopeTarget}.`
      )
    default:
      return null
  }
}

export function deterministicPrevizToastMessage({
  hasExisting,
  scopeLabel,
  startFrom,
}: {
  hasExisting: boolean
  scopeLabel: string
  startFrom: string | undefined
}): string {
  const scope = scopeLabel.toLowerCase()
  if (startFrom === 'animatics') {
    return hasExisting
      ? `Regenerating deterministic baseline from the current storyboard for ${scope}`
      : `Started deterministic baseline from the current storyboard for ${scope}`
  }
  if (startFrom === 'storyboards') {
    return hasExisting
      ? `Regenerating deterministic baseline from the current shot plan for ${scope}`
      : `Started deterministic baseline from the current shot plan for ${scope}`
  }
  if (startFrom === 'keyframes') {
    return hasExisting
      ? `Regenerating keyframes for ${scope}`
      : `Started keyframes for ${scope}`
  }
  return hasExisting
    ? `Refreshing deterministic baseline for ${scope}`
    : `Started deterministic baseline for ${scope}`
}
