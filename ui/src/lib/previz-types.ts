import type { VideoPrice } from './cost-types'

export type PrevizCostEvidence = {
  status: 'verified' | 'estimated' | 'blocked'
  estimated_cost_usd?: number | null
  reason?: string | null
  basis: 'recipe_default_video_example'
  duration_seconds?: number | null
  price?: VideoPrice | null
}

export type PrevizLaneStatus = {
  lane_id: 'ai_previz'
  label: string
  candidate_label?: string | null
  latency_class: 'fast' | 'slow'
  adoption_state: 'default' | 'recommended_optional' | 'experimental_manual'
  reason: string
  intended_use: string
  fidelity_disclosure: string
  blocker_reasons: string[]
  overall_score?: number | null
  baseline_score?: number | null
  score_margin?: number | null
  measured_at?: string | null
  latency_ms?: number | null
  latency_budget_ms?: number | null
  regenerate_reuse_latency_ms?: number | null
  regenerate_full_latency_ms?: number | null
  engine_pack_id?: string | null
  target_model?: string | null
  resolution?: string | null
  duration_seconds?: number | null
  consistency_strategy?: string | null
  cost: PrevizCostEvidence
  validation_stage_enabled: boolean
}

export type PrevizAdoptionStatus = {
  policy_summary: string
  ai_previz: PrevizLaneStatus
}
