// API response types matching the FastAPI backend models.

export type ApiError = {
  code: string
  message: string
  hint?: string | null
}

export type InteractionMode = 'guided' | 'balanced' | 'expert'

export type ProjectSummary = {
  project_id: string
  display_name: string
  artifact_groups: number
  run_count: number
  has_inputs: boolean
  input_files: string[]
  ui_preferences: Record<string, string>
  human_control_mode: 'autonomous' | 'checkpoint' | 'advisory'
  interaction_mode: InteractionMode
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
}

export type UploadedInputResponse = {
  original_name: string
  stored_path: string
  size_bytes: number
}

export type RunStartPayload = {
  project_id: string
  input_file: string
  default_model: string
  work_model?: string
  verify_model?: string
  escalate_model?: string
  recipe_id?: string
  human_control_mode?: 'autonomous' | 'checkpoint' | 'advisory'
  skip_qa?: boolean
  qa_model?: string
  accept_config: boolean
  run_id?: string
  force?: boolean
  start_from?: string
  end_at?: string
  config_file?: string
  config_overrides?: Record<string, unknown>
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
  artifact_refs: Array<Record<string, unknown>>
  started_at?: number | null
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
    runtime_params: Record<string, unknown>
    total_cost_usd: number
  }
  background_error?: string | null
}

export type RunEventsResponse = {
  run_id: string
  events: Array<Record<string, unknown>>
}

export type ArtifactGroupSummary = {
  artifact_type: string
  entity_id: string | null
  latest_version: number
  health: string | null
}

export type ArtifactVersionSummary = {
  artifact_type: string
  entity_id: string | null
  version: number
  health: string | null
  path: string
  created_at?: string
  intent?: string
  producing_module?: string
}

export type ArtifactDetailResponse = {
  artifact_type: string
  entity_id: string | null
  version: number
  payload: Record<string, unknown>
  bible_files?: Record<string, unknown>
}

export type ArtifactEditRequest = {
  data: Record<string, unknown>
  rationale: string
}

export type ArtifactEditResponse = {
  artifact_type: string
  entity_id: string | null
  version: number
  path: string
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
}

// --- Search ---

export type SearchResultScene = {
  scene_id: string
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
