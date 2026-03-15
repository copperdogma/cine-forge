import type { ArtifactHealthDetails } from './types'

export const ATTENTION_HEALTHS = ['stale', 'needs_revision', 'confirmed_valid'] as const

export function isAttentionHealth(health: string | null | undefined): boolean {
  return !!health && ATTENTION_HEALTHS.includes(health as (typeof ATTENTION_HEALTHS)[number])
}

export function healthLabel(health: string | null | undefined): string {
  switch (health) {
    case 'valid':
    case 'healthy':
      return 'Current'
    case 'stale':
      return 'Stale'
    case 'needs_revision':
      return 'Needs Revision'
    case 'confirmed_valid':
      return 'Confirmed Valid'
    case 'needs_review':
      return 'Needs Review'
    default:
      return health ?? 'Unknown'
  }
}

export function healthDescription(
  health: string | null | undefined,
  details?: ArtifactHealthDetails | null,
): string {
  if (details?.reason) {
    return details.reason
  }

  switch (health) {
    case 'valid':
    case 'healthy':
      return 'This artifact is current and ready for downstream use.'
    case 'stale':
      return 'Upstream artifacts changed after this was produced. Preview or assess the impact before relying on it.'
    case 'needs_revision':
      return 'Impact assessment found this artifact depends on outdated upstream information and should be revised.'
    case 'confirmed_valid':
      return 'Impact assessment found this artifact still holds after the upstream change. Acknowledge it to clear the attention state.'
    case 'needs_review':
      return 'This artifact needs human review before it should drive downstream work.'
    default:
      return 'Health status not yet determined.'
  }
}
