import type { DesignStudyGenerationFailure, DesignStudyRound } from './api/design-study'

export function getDesignStudyRoundStatus(round: DesignStudyRound): DesignStudyRound['status'] {
  return round.status ?? 'completed'
}

export function isDesignStudyRoundActive(round: DesignStudyRound): boolean {
  return getDesignStudyRoundStatus(round) === 'generating'
}

export function getDesignStudyProgressText(round: DesignStudyRound): string {
  const generated = round.images.length
  const requested = Math.max(round.count || generated || 1, generated)
  const status = getDesignStudyRoundStatus(round)

  if (status === 'generating') {
    return `Generating ${generated} of ${requested} image${requested === 1 ? '' : 's'}`
  }
  if (status === 'failed') {
    return `Failed after ${generated} of ${requested} image${requested === 1 ? '' : 's'}`
  }
  return `${generated} image${generated === 1 ? '' : 's'} generated`
}

export function formatDesignStudyFailureSummary(
  failure: DesignStudyGenerationFailure,
): string {
  const classification = failure.classification
    ? ` (${failure.classification.replaceAll('_', ' ')})`
    : ''
  const request = failure.request_id ? ` Request ID: ${failure.request_id}.` : ''
  return `${providerLabel(failure.provider)} failed on ${failure.model}${classification}.${request}`
}

export function getDesignStudyFailureRows(
  failure: DesignStudyGenerationFailure,
): Array<{ label: string; value: string }> {
  return [
    { label: 'Provider', value: providerLabel(failure.provider) },
    { label: 'Model', value: failure.model },
    { label: 'Classification', value: failure.classification?.replaceAll('_', ' ') ?? 'provider error' },
    ...(failure.status_code ? [{ label: 'HTTP', value: String(failure.status_code) }] : []),
    ...(failure.request_id ? [{ label: 'Request', value: failure.request_id }] : []),
    ...(failure.error_code ? [{ label: 'Code', value: failure.error_code }] : []),
    { label: 'Prompt', value: failure.prompt_sha256.slice(0, 12) },
  ]
}

function providerLabel(provider: string): string {
  const normalized = provider.trim().toLowerCase()
  if (normalized === 'openai') return 'OpenAI Images'
  if (normalized === 'google') return 'Google Imagen'
  return provider || 'Provider'
}
