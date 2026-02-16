// API response types matching the FastAPI backend models.

export type ApiError = {
  code: string
  message: string
  hint?: string | null
}

export type ProjectSummary = {
  project_id: string
  display_name: string
  artifact_groups: number
  run_count: number
  has_inputs: boolean
  input_files: string[]
}

export type RecentProjectSummary = ProjectSummary & {
  project_path: string
}

export type RunSummary = {
  run_id: string
  status: string
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
  skip_qa?: boolean
  qa_model?: string
  accept_config: boolean
  run_id?: string
  force?: boolean
  start_from?: string
  config_file?: string
  config_overrides?: Record<string, unknown>
}

export type StageState = {
  status: string
  model_used?: string | null
  call_count?: number
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

// --- Input Files ---

export type InputFileSummary = {
  filename: string
  original_name: string
  size_bytes: number
}

// --- Project State ---

export type ProjectState = 'empty' | 'fresh_import' | 'processing' | 'analyzed' | 'complete'

// --- Chat ---

export type ChatMessageType = 'ai_welcome' | 'ai_status' | 'ai_suggestion' | 'user_action'

export type ChatAction = {
  id: string
  label: string
  variant: 'default' | 'secondary' | 'outline'
  route?: string
}

export type ChatMessage = {
  id: string
  type: ChatMessageType
  content: string
  timestamp: number
  actions?: ChatAction[]
  needsAction?: boolean
}
