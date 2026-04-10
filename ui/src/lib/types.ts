// API response types matching the FastAPI backend models.

export type ApiError = {
  code: string
  message: string
  hint?: string | null
}

export type InteractionMode = 'guided' | 'balanced' | 'expert'
export type ProductionFormat =
  | 'live_action'
  | 'animation_2d'
  | 'animation_3d'
  | 'anime'
  | 'graphic_novel'
  | 'concept_art'

export type ProjectSummary = {
  project_id: string
  display_name: string
  artifact_groups: number
  run_count: number
  has_inputs: boolean
  input_files: string[]
  ui_preferences: Record<string, string>
  human_control_mode: 'autonomous' | 'checkpoint' | 'advisory'
  production_format: ProductionFormat | null
  interaction_mode: InteractionMode
  default_model?: string | null
  work_model?: string | null
  verify_model?: string | null
  escalate_model?: string | null
  project_budget_limit_usd?: number | null
  default_run_budget_limit_usd?: number | null
  budget_warning_threshold_ratio: number
  preference_learning_enabled: boolean
  preference_learning_cleared_at?: string | null
  style_packs: Record<string, string>
}

export type StylePackProvider = 'openai' | 'anthropic' | 'google'

export type StylePackProviderOption = {
  provider: StylePackProvider
  display_name: string
  recommended: boolean
}

export type StylePackDraftFile = {
  kind: 'description' | 'reference_image' | 'frame_grab' | 'palette' | 'notes' | 'audio_reference'
  path: string
  caption?: string | null
  content: string
}

export type StylePackResearchCost = {
  model: string
  total_tokens: number
  estimated_cost_usd?: number | null
  latency_seconds?: number | null
  request_id?: string | null
  attribution: 'deep_research_cli_estimate' | 'provider_unavailable'
  note?: string | null
}

export type StylePackLibraryItem = {
  role_id: string
  style_pack_id: string
  display_name: string
  summary: string
  source: 'built_in' | 'project'
}

export type RoleStylePackLibrary = {
  role_id: string
  display_name: string
  can_generate: boolean
  selected_style_pack_id?: string | null
  style_packs: StylePackLibraryItem[]
}

export type StylePackLibraryResponse = {
  roles: RoleStylePackLibrary[]
  providers: StylePackProviderOption[]
}

export type StylePackManualPromptResponse = {
  role_id: string
  role_display_name: string
  subject: string
  prompt: string
}

export type StylePackDraft = {
  generation_mode: 'deep_research' | 'manual_import'
  role_id: string
  role_display_name: string
  provider?: StylePackProvider | null
  subject: string
  style_pack_id: string
  display_name: string
  summary: string
  prompt_injection: string
  style_markdown: string
  additional_files: StylePackDraftFile[]
  research_cost?: StylePackResearchCost | null
}

export type StylePackSaveResponse = {
  style_pack: StylePackLibraryItem
  assigned_style_pack_id?: string | null
  project_summary: ProjectSummary
}

export type PreferenceSignalPolarity = 'positive' | 'negative' | 'directional' | 'neutral'
export type PreferenceCueType = 'preferred' | 'avoid' | 'variation'
export type PreferenceEntityType = 'character' | 'location' | 'prop'

export type PreferenceSignal = {
  signal_id: string
  source_kind: 'design_study_decision'
  entity_id: string
  entity_type: PreferenceEntityType
  round_number: number
  image_filename: string
  decision: 'pending' | 'selected_final' | 'favorite' | 'rejected' | 'seed_for_variants'
  polarity: PreferenceSignalPolarity
  guidance?: string | null
  round_directive?: string | null
  prompt_used: string
  prompt_sources_used: string[]
  model?: string | null
  created_at: string
}

export type PreferenceCue = {
  cue_type: PreferenceCueType
  entity_id: string
  entity_type: PreferenceEntityType
  text: string
  weight: number
  signal_count: number
  source_signal_ids: string[]
  source_image_filenames: string[]
}

export type PreferenceProfile = {
  enabled: boolean
  last_cleared_at?: string | null
  active_signal_count: number
  entity_count: number
  summary_lines: string[]
  preferred_cues: PreferenceCue[]
  avoid_cues: PreferenceCue[]
  variation_cues: PreferenceCue[]
  recent_signals: PreferenceSignal[]
}

export type RecentProjectSummary = ProjectSummary & {
  project_path: string
  last_modified?: number | null
}

export type RunSummary = {
  run_id: string
  status: string
  recipe_id: string
  started_at?: number
  finished_at?: number
  total_cost_usd: number
}

export type UploadedInputResponse = {
  original_name: string
  stored_path: string
  size_bytes: number
}

export type SceneScopeMode = 'all_scenes' | 'current_scene'

export type SceneExecutionScope = {
  mode: SceneScopeMode
  scene_ids: string[]
}

export type SceneActionPreflightItem = {
  kind: 'warning' | 'auto_build' | 'soft_block'
  label: string
  detail: string
}

export type SceneActionPreflight = {
  recipe_id: string
  recipe_name: string
  start_from?: string | null
  end_at?: string | null
  scene_scope: SceneExecutionScope
  status: 'ready' | 'warn' | 'soft_block'
  summary: string
  items: SceneActionPreflightItem[]
}

export type RunRuntimeParams = Record<string, unknown> & {
  default_model?: string | null
  scene_scope?: SceneExecutionScope
  scene_action_preflight?: SceneActionPreflight | null
}

export type RunStartPayload = {
  project_id: string
  input_file: string
  default_model: string
  work_model?: string | null
  verify_model?: string | null
  escalate_model?: string | null
  recipe_id?: string
  human_control_mode?: 'autonomous' | 'checkpoint' | 'advisory'
  skip_qa?: boolean
  qa_model?: string | null
  accept_config: boolean
  run_id?: string
  force?: boolean
  start_from?: string
  end_at?: string
  scene_scope?: SceneExecutionScope
  config_file?: string
  config_overrides?: Record<string, unknown>
  project_budget_limit_usd?: number | null
  run_budget_limit_usd?: number | null
  budget_warning_threshold_ratio?: number | null
}

export type StageState = {
  status: string
  model_used?: string | null
  call_count?: number
  attempt_count?: number
  attempts?: Array<Record<string, unknown>>
  final_error_class?: string | null
  duration_seconds: number
  cost_usd: number
  input_tokens?: number
  output_tokens?: number
  pause_reason?: string | null
  artifact_refs: Array<Record<string, unknown>>
  started_at?: number | null
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
  scene_id: string
  call_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  stage_ids: string[]
  attribution: CostAttribution
}

export type RunCostOverview = {
  run_id: string
  recipe_id: string
  status: string
  started_at?: number | null
  finished_at?: number | null
  total_cost_usd: number
  duration_seconds: number
}

export type ProjectCostTrendPoint = {
  run_id: string
  started_at?: number | null
  total_cost_usd: number
}

export type ProjectCostTrend = {
  direction: 'up' | 'down' | 'flat' | 'insufficient_data'
  recent_average_usd: number
  previous_average_usd: number
  delta_usd: number
}

export type RunCostSummary = {
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
  project_id: string
  total_cost_usd: number
  run_count: number
  runs: RunCostOverview[]
  trend_points: ProjectCostTrendPoint[]
  trend: ProjectCostTrend
  budget_config: BudgetConfig
}

export type RunStateResponse = {
  run_id: string
  state: {
    run_id: string
    recipe_id: string
    started_at?: number
    finished_at?: number
    stages: Record<string, StageState>
    stage_order?: string[]
    runtime_params: RunRuntimeParams
    total_cost_usd: number
  }
  background_error?: string | null
}

export type RunEventsResponse = {
  run_id: string
  events: Array<Record<string, unknown>>
}

export type ArtifactRef = {
  artifact_type: string
  entity_id: string | null
  version: number
  path: string
}

export type CostRecord = {
  model: string
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  latency_seconds?: number | null
  request_id?: string | null
}

export type ArtifactHealthDetails = {
  health: string
  source_kind?: string | null
  reason?: string | null
  trigger_ref?: ArtifactRef | null
  source_artifact_ref?: ArtifactRef | null
  upstream_change_summary?: string | null
  suggested_revision?: string | null
  confidence?: number | null
  assessing_role?: string | null
  decided_by?: string | null
  updated_at?: string | null
}

export type ArtifactGroupSummary = {
  artifact_type: string
  entity_id: string | null
  latest_version: number
  health: string | null
  health_details?: ArtifactHealthDetails | null
}

export type ReadinessState = 'red' | 'yellow' | 'green'

export type SceneReadiness = {
  scene_id: string
  intent_mood: ReadinessState
  look_and_feel: ReadinessState
  sound_and_music: ReadinessState
  rhythm_and_flow: ReadinessState
  character_and_performance: ReadinessState
  story_world: ReadinessState
}

export type ArtifactVersionSummary = {
  artifact_type: string
  entity_id: string | null
  version: number
  health: string | null
  health_details?: ArtifactHealthDetails | null
  path: string
  created_at?: string
  intent?: string
  producing_module?: string
}

export type ArtifactDetailResponse = {
  artifact_type: string
  entity_id: string | null
  version: number
  health?: string | null
  health_details?: ArtifactHealthDetails | null
  payload: Record<string, unknown>
  bible_files?: Record<string, unknown>
}

export type PrevizCostEvidence = {
  status: 'verified' | 'estimated' | 'blocked'
  estimated_cost_usd?: number | null
  reason?: string | null
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

export type ArtifactEditRequest = {
  data: Record<string, unknown>
  rationale: string
  source?: 'human' | 'ai'
  producing_role?: string | null
  chat_message_id?: string | null
  bible_files?: Record<string, unknown> | null
}

export type ArtifactEditResponse = {
  artifact_type: string
  entity_id: string | null
  version: number
  path: string
}

export type ImpactPreviewTarget = {
  artifact_ref: ArtifactRef
  artifact_type: string
  entity_id: string | null
  current_health: string
}

export type ImpactPreviewRequest = {
  artifact_ref: ArtifactRef
  selected_artifact_refs?: ArtifactRef[] | null
  model?: string | null
  budget_cap_usd?: number | null
}

export type ImpactPreviewResponse = {
  trigger_artifact_ref: ArtifactRef
  requested_artifact_ref: ArtifactRef
  total_stale: number
  affected_types: string[]
  estimated_cost: CostRecord
  budget_cap_usd?: number | null
  within_budget: boolean
  targets: ImpactPreviewTarget[]
}

export type ArtifactImpact = {
  artifact_ref: ArtifactRef
  previous_health: string
  assessed_health: 'needs_revision' | 'confirmed_valid'
  rationale: string
  upstream_change_summary: string
  suggested_revision?: string | null
  confidence: number
  assessing_role: string
}

export type ImpactAssessment = {
  trigger_artifact_ref: ArtifactRef
  trigger_diff_summary: string
  assessments: ArtifactImpact[]
  total_stale: number
  total_needs_revision: number
  total_confirmed_valid: number
  assessment_cost: CostRecord
}

export type ImpactAssessmentRequest = {
  artifact_ref: ArtifactRef
  selected_artifact_refs?: ArtifactRef[] | null
  model?: string | null
  role_id?: string | null
  budget_cap_usd?: number | null
}

export type ImpactAssessmentResponse = {
  assessment_ref: ArtifactRef
  assessment: ImpactAssessment
}

export type ArtifactHealthOverrideRequest = {
  artifact_ref: ArtifactRef
  target_health: 'valid' | 'needs_revision' | 'confirmed_valid'
  rationale: string
  decided_by?: string
}

export type ArtifactHealthOverrideResponse = {
  decision_ref: ArtifactRef
  artifact_ref: ArtifactRef
  health: string
  health_details?: ArtifactHealthDetails | null
}

export type RecipeSummary = {
  recipe_id: string
  name: string
  description: string
  stage_count: number
}

// --- Slug Preview ---

export type SlugPreviewResponse = {
  slug: string
  display_name: string
  alternatives: string[]
}

// --- Input Files ---

export type InputFileSummary = {
  filename: string
  original_name: string
  size_bytes: number
  stored_path: string
}

// --- Project State ---

export type ProjectState = 'empty' | 'fresh_import' | 'processing' | 'analyzed' | 'complete'

// --- Chat ---

export type ChatMessageType = 'ai_welcome' | 'ai_status' | 'ai_status_done' | 'ai_suggestion' | 'ai_progress' | 'task_progress' | 'user_action' | 'user_message' | 'ai_response' | 'ai_tool_status' | 'ai_tool_done' | 'activity'

export type ConfirmAction = {
  type: 'edit_artifact' | 'start_run'
  endpoint: string
  payload: Record<string, unknown>
}

export type ChatAction = {
  id: string
  label: string
  variant: 'default' | 'secondary' | 'outline'
  route?: string
  confirm_action?: ConfirmAction
  /** If true, clicking this action records the dismissal locally without a network call. */
  dismiss_action?: boolean
  /** If set, clicking this action re-sends the given text as a new chat message. */
  retry_text?: string
}

export type ToolCallStatus = {
  id: string
  name: string
  displayName: string
  done: boolean
}

export type PreflightWarning = {
  type: 'stale' | 'missing'
  label: string
}

export type PreflightData = {
  recipe_id: string
  recipe_name: string
  description: string
  stage_count: number
  stages: string[]
  input_file: string
  tier: 'ready' | 'warn_stale' | 'block_missing'
  warnings: PreflightWarning[]
}

export type ChatMessage = {
  id: string
  type: ChatMessageType
  content: string
  timestamp: number
  /** Role that produced this message (e.g., "assistant", "director", "editorial_architect"). */
  speaker?: string
  /** Runtime model that produced this AI message (e.g., "claude-sonnet-4-6"). */
  model?: string | null
  actions?: ChatAction[]
  needsAction?: boolean
  streaming?: boolean
  toolCalls?: ToolCallStatus[]
  /** Optional route for activity notes (e.g., "artifacts/bible_manifest/character_the_mariner/1") */
  route?: string
  /** Page context label injected into this message's prompt (e.g., "Scene 005"). */
  pageContext?: string
  /** The actual artifact content injected into the system prompt (scene text, bible, etc.). */
  injectedContent?: string
  /** Structured preflight data for run proposals. */
  preflightData?: PreflightData
  /** Actionable message this user action resolved, if any. */
  resolvedMessageId?: string
}

// --- Search ---

export type SearchResultScene = {
  scene_id: string
  scene_number: number
  heading: string
  location: string
  time_of_day: string
  int_ext: string
}

export type SearchResultEntity = {
  entity_id: string
  display_name: string
  entity_type: string
  artifact_type: string
}

export type SearchResponse = {
  query: string
  scenes: SearchResultScene[]
  characters: SearchResultEntity[]
  locations: SearchResultEntity[]
  props: SearchResultEntity[]
}

// --- Chat Characters ---

export type ChatCharacter = {
  id: string          // handle without 'character_' prefix
  entity_id: string   // full entity id e.g. 'character_billy'
  name: string        // display name e.g. 'Billy'
  prominence: string  // 'primary' | 'secondary' | 'minor'
}

// --- Pipeline Graph ---

export type PipelineNodeStatus = 'completed' | 'stale' | 'in_progress' | 'available' | 'blocked' | 'not_implemented'
export type PipelinePhaseStatus = 'completed' | 'partial' | 'available' | 'blocked' | 'not_started'

export type PipelineGraphNode = {
  id: string
  label: string
  phase_id: string
  status: PipelineNodeStatus
  artifact_count: number
  dependencies: string[]
  nav_route: string | null
  implemented: boolean
  stale_reason?: string
  fix_recipe?: string
}

export type PipelineGraphPhase = {
  id: string
  label: string
  icon: string
  status: PipelinePhaseStatus
  nav_route: string | null
  completed_count: number
  implemented_count: number
  total_count: number
}

export type PipelineGraphResponse = {
  phases: PipelineGraphPhase[]
  nodes: PipelineGraphNode[]
  edges: Array<{ from: string; to: string }>
}

// --- List UI State ---

export type SortMode = 'script-order' | 'alphabetical' | 'prominence'
export type SortDirection = 'asc' | 'desc'
export type ViewDensity = 'compact' | 'medium' | 'large'
export type ProminenceFilter = 'all' | 'primary' | 'secondary' | 'minor'
