export type PreviewProvenanceView = {
  mode: string | null
  fidelityIntent: string | null
  intendedUse: string[]
  upstreamInputs: string[]
  consistencyStrategy: string | null
  promptProfile: string | null
  prerequisiteStrategy: string | null
  reusedArtifactTypes: string[]
  autoBuildArtifactTypes: string[]
  missingOptionalArtifactTypes: string[]
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
    consistencyStrategy: asString(record.consistency_strategy),
    promptProfile: asString(record.prompt_profile),
    prerequisiteStrategy: asString(record.prerequisite_strategy),
    reusedArtifactTypes: asStringArray(record.reused_artifact_types),
    autoBuildArtifactTypes: asStringArray(record.auto_build_artifact_types),
    missingOptionalArtifactTypes: asStringArray(record.missing_optional_artifact_types),
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
    case 'ai_previz':
      return 'AI previz'
    case 'generated_render':
      return 'Generated render'
    case 'final_render':
      return 'Final render'
    default:
      return mode
  }
}

export function formatConsistencyStrategy(value: string | null): string | null {
  switch (value) {
    case 'deterministic':
      return 'Deterministic'
    case 'prompt_only':
      return 'Prompt-only consistency'
    case 'optional_references':
      return 'Optional references'
    case 'reference_guided':
      return 'Reference-guided'
    default:
      return value
  }
}

export function formatPromptProfile(value: string | null): string | null {
  switch (value) {
    case 'standard':
      return 'Standard prompt'
    case 'compact':
      return 'Compact prompt'
    default:
      return value
  }
}

export function formatPrerequisiteStrategy(value: string | null): string | null {
  switch (value) {
    case 'reuse_existing_render_clip_plan':
      return 'Reuse current render clip plan'
    case 'reuse_existing_shot_plan':
      return 'Refresh render clips from current shot plan'
    case 'one_pass_previz_prep':
      return 'One-pass previz prep'
    default:
      return value
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
