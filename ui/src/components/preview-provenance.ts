export type PreviewProvenanceView = {
  mode: string | null
  fidelityIntent: string | null
  intendedUse: string[]
  upstreamInputs: string[]
  estimatedCostUsd: number | null
  generationLatencyMs: number | null
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function asStringArray(value: unknown): string[] {
  return asArray(value)
    .map(item => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

export function parsePreviewProvenance(value: unknown): PreviewProvenanceView | null {
  const record = asRecord(value)
  if (!record) return null
  return {
    mode: asString(record.mode),
    fidelityIntent: asString(record.fidelity_intent),
    intendedUse: asStringArray(record.intended_use),
    upstreamInputs: asStringArray(record.upstream_inputs),
    estimatedCostUsd: asNumber(record.estimated_cost_usd),
    generationLatencyMs: asNumber(record.generation_latency_ms),
  }
}

export function formatPreviewMode(mode: string | null): string | null {
  switch (mode) {
    case 'annotated_symbolic':
      return 'Annotated symbolic'
    case 'symbolic':
      return 'Symbolic'
    case 'shared_video':
      return 'Shared video'
    case 'generated_render':
      return 'Generated render'
    case 'final_render':
      return 'Final render'
    default:
      return mode
  }
}

export function formatPreviewIntent(intent: string | null): string | null {
  switch (intent) {
    case 'blocking_review':
      return 'Blocking review'
    case 'symbolic_baseline':
      return 'Symbolic baseline'
    case 'render_preview':
      return 'Render preview'
    case 'final_render':
      return 'Final render'
    default:
      return intent
  }
}

export function formatLatencyMs(value: number | null): string | null {
  if (value === null) return null
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`
  return `${Math.round(value)}ms`
}

export function formatMoney(value: number | null): string | null {
  if (value === null) return null
  return `$${value.toFixed(2)}`
}
