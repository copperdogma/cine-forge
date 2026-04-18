import type { ArtifactGroupSummary, ArtifactHealthDetails } from './types'

export const ATTENTION_HEALTHS = ['stale', 'needs_revision', 'needs_review', 'confirmed_valid'] as const
export const BIBLE_REVIEW_TYPES = ['character_bible', 'location_bible', 'prop_bible'] as const

export type MediaValidationStatus = {
  label: 'Validation Pending' | 'Validated' | 'Validation Failed'
  description: string
  tone: 'pending' | 'validated' | 'failed'
}

export function isAttentionHealth(health: string | null | undefined): boolean {
  return !!health && ATTENTION_HEALTHS.includes(health as (typeof ATTENTION_HEALTHS)[number])
}

export function actionableHealthGroups(
  groups: ArtifactGroupSummary[] | null | undefined,
): ArtifactGroupSummary[] {
  return (groups ?? []).filter(
    group => isAttentionHealth(group.health) && group.artifact_type !== 'stage_review',
  )
}

export function reviewableBibleGroups(
  groups: ArtifactGroupSummary[] | null | undefined,
): ArtifactGroupSummary[] {
  return (groups ?? []).filter(
    group =>
      BIBLE_REVIEW_TYPES.includes(group.artifact_type as (typeof BIBLE_REVIEW_TYPES)[number]) &&
      group.latest_version === 1 &&
      !isAttentionHealth(group.health),
  )
}

export function gateReviewGroups(
  groups: ArtifactGroupSummary[] | null | undefined,
): ArtifactGroupSummary[] {
  return (groups ?? []).filter(
    group => group.artifact_type === 'stage_review' && group.health === 'needs_review',
  )
}

export function healthLabel(
  health: string | null | undefined,
  details?: ArtifactHealthDetails | null,
): string {
  const validationStatus = mediaValidationStatus(health, details)
  if (validationStatus) return validationStatus.label

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
  const validationStatus = mediaValidationStatus(health, details)
  if (validationStatus) {
    return validationStatus.description
  }

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

export function mediaValidationStatus(
  health: string | null | undefined,
  details?: ArtifactHealthDetails | null,
): MediaValidationStatus | null {
  if (!details?.source_kind) return null

  if (
    details.source_kind === 'media_validation_missing'
    || details.source_kind === 'media_validation_stale'
  ) {
    return {
      label: 'Validation Pending',
      description:
        details.reason
        ?? 'This artifact is playable, but media validation for the latest version is still pending.',
      tone: 'pending',
    }
  }

  if (details.source_kind !== 'media_validation') return null

  if (health === 'valid' || health === 'healthy' || health === 'confirmed_valid') {
    return {
      label: 'Validated',
      description: details.reason ?? 'Validation is available for this artifact.',
      tone: 'validated',
    }
  }

  return {
    label: 'Validation Failed',
    description: details.reason ?? 'Validation flagged this artifact for follow-up.',
    tone: 'failed',
  }
}
