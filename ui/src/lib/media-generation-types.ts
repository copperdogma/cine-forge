import type { ArtifactRef } from './types'
import type { VideoPrice } from './cost-types'

export type MediaRecipeId = 'render_generation' | 'ai_previz_generation'
export type MediaExecutionUnit = {
  entity_id: string
  clip_id: string | null
  title: string
  planned_duration_seconds: number
  duration_seconds: number
  resolution: string
  aspect_ratio: string
  provider: string
  model: string
  video_estimate_usd: number | null
  price: VideoPrice | null
}
export type MediaExecutionPlan = {
  project_id: string
  recipe_id: MediaRecipeId
  scene_id: string
  render_clip_ids: string[] | null
  binding_sha256: string
  status: 'ready' | 'blocked'
  blockers: string[]
  units: MediaExecutionUnit[]
  video_estimate_usd: number | null
  total_estimate_usd: null
  excluded_costs: string[]
  source_bindings: Array<{ key: string; ref: ArtifactRef | null; sha256: string | null }>
}
export type MediaExecutionPlanResponse = { plan_ref: ArtifactRef; plan: MediaExecutionPlan }
export type MediaInspectionRequest = {
  recipe_id: MediaRecipeId
  scene_id: string
  render_clip_ids?: string[]
}
export type MediaConfirmationPayload = { project_id: string; media_execution_plan_ref: ArtifactRef }
