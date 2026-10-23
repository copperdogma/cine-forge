export type CostRecord = {
  model: string
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  latency_seconds?: number | null
  request_id?: string | null
}

export type VideoPrice = {
  provider: string
  model: string
  resolution: string
  unit: 'USD/second'
  unit_price_usd: number
  source_url: string
  checked_on: string
}

export type CostReceipt = {
  receipt_id: string
  component: 'compiler' | 'video' | 'image'
  model: string
  status: 'estimated' | 'uncertain'
  cost: CostRecord | null
  provider?: string | null
  provider_job_id?: string | null
  scene_id?: string | null
  entity_id?: string | null
  price?: VideoPrice | null
  quantity?: number | null
  reason?: string | null
}

export type BudgetScope = 'project' | 'run' | 'stage'
export type BudgetHealth = 'ok' | 'warning' | 'limit_reached'
export type CostAttributionKind = 'exact' | 'allocated' | 'unattributed'

export type BudgetConfig = {
  project_budget_limit_usd?: number | null
  default_run_budget_limit_usd?: number | null
  budget_warning_threshold_ratio: number
  stage_budget_limits_usd: Record<string, number>
}

export type BudgetStatus = {
  scope: BudgetScope
  limit_usd: number
  consumed_usd: number
  remaining_usd: number
  warning_threshold_ratio: number
  warning_threshold_usd: number
  health: BudgetHealth
  message?: string | null
}

export type CostAttribution = {
  kind: CostAttributionKind
  basis: string
}

export type StageCostSummary = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  stage_id: string
  status: string
  model_used?: string | null
  call_count: number
  attempt_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  module_cost_usd: number
  role_cost_usd: number
  duration_seconds: number
  artifact_count: number
  pause_reason?: string | null
}

export type ModelCostSummary = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  model: string
  call_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
}

export type RoleCostSummary = {
  role_id: string
  models: string[]
  call_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  stage_ids: string[]
  scene_ids: string[]
  entity_ids: string[]
  attribution: CostAttribution
}

export type SceneCostSummary = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  scene_id: string
  call_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  stage_ids: string[]
  attribution: CostAttribution
}

export type RunCostOverview = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  run_id: string
  recipe_id: string
  status: string
  started_at?: number | null
  finished_at?: number | null
  total_cost_usd: number
  duration_seconds: number
}

export type ProjectCostTrendPoint = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  run_id: string
  started_at?: number | null
  total_cost_usd: number
}

export type ProjectCostTrend = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  direction: 'up' | 'down' | 'flat' | 'insufficient_data'
  recent_average_usd: number
  previous_average_usd: number
  delta_usd: number
}

export type RunCostSummary = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  run_id: string
  project_id: string
  recipe_id: string
  status: string
  started_at?: number | null
  finished_at?: number | null
  total_cost_usd: number
  stages: StageCostSummary[]
  by_model: ModelCostSummary[]
  by_role: RoleCostSummary[]
  by_scene: SceneCostSummary[]
  budget_config: BudgetConfig
  budget_statuses: BudgetStatus[]
}

export type ProjectCostSummary = {
  cost_is_complete: boolean
  uncertain_cost_receipts: CostReceipt[]
  project_id: string
  total_cost_usd: number
  run_count: number
  runs: RunCostOverview[]
  trend_points: ProjectCostTrendPoint[]
  trend: ProjectCostTrend
  budget_config: BudgetConfig
}
