import { formatMoney } from './render-utils.ts'
import type { MediaValidationStatus } from '@/lib/health'
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
  if (status.cost.status === 'estimated' && amount && status.cost.duration_seconds) {
    return `${status.cost.duration_seconds}s video example: ${amount} est.`
  }
  if (status.cost.status === 'verified' && amount) return `Recorded estimate: ${amount}`
  if (status.cost.status === 'blocked') return 'Cost blocked'
  return null
}

export function previzPlaybackSummary({
  sceneHeading,
  hasIncompleteCurrentClipSet,
  previzClipArtifactCount,
  plannedClipCount,
  hasClipPrevizOutputs,
  validationStatus,
}: {
  sceneHeading: string
  hasIncompleteCurrentClipSet: boolean
  previzClipArtifactCount: number
  plannedClipCount: number
  hasClipPrevizOutputs: boolean
  validationStatus: MediaValidationStatus | null
}): string {
  if (hasIncompleteCurrentClipSet) {
    return `Current AI previz has ${previzClipArtifactCount} of ${plannedClipCount} render-clip players for ${sceneHeading}. Regenerate to fill the missing clip.`
  }
  const subject = hasClipPrevizOutputs ? 'Latest AI previz clips are' : 'Latest AI previz clip is'
  if (validationStatus?.label === 'Needs Review') {
    return `${subject} playable for ${sceneHeading}. Review is still required before relying on this media.`
  }
  if (validationStatus?.label === 'Validation Pending') {
    return `${subject} playable for ${sceneHeading}. Validation is still pending.`
  }
  if (validationStatus?.tone === 'failed') {
    return `${subject} playable for ${sceneHeading}, but validation flagged ${hasClipPrevizOutputs ? 'at least one' : 'it'} for follow-up.`
  }
  return `${subject} ready for ${sceneHeading}. ${hasClipPrevizOutputs ? 'The players appear below.' : 'The viewer appears below.'}`
}
