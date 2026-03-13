import { request } from './core'

export interface ScriptContextResponse {
  title: string
  logline: string
  genre: string
  tone: string
  themes: string[]
}

export interface IntentMoodSuggestion {
  mood_descriptors: string[]
  reference_films: string[]
  style_preset_id: string | null
  natural_language_intent: string | null
  rationale: string
}

export interface StylePresetResponse {
  preset_id: string
  display_name: string
  description: string
  mood_descriptors: string[]
  reference_films: string[]
  thumbnail_emoji: string
  concern_group_ids: string[]
}

export interface IntentMoodResponse {
  scope: string
  scene_id: string | null
  mood_descriptors: string[]
  reference_films: string[]
  style_preset_id: string | null
  natural_language_intent: string | null
  user_approved: boolean
  version: number
}

export interface IntentMoodInput {
  mood_descriptors: string[]
  reference_films: string[]
  style_preset_id: string | null
  natural_language_intent: string | null
  scope: string
  scene_id?: string | null
}

export interface PropagatedGroupResponse {
  fields: Record<string, unknown>
  rationale: string
}

export interface PropagationResponse {
  look_and_feel: PropagatedGroupResponse | null
  sound_and_music: PropagatedGroupResponse | null
  rhythm_and_flow: PropagatedGroupResponse | null
  character_and_performance: PropagatedGroupResponse | null
  story_world: PropagatedGroupResponse | null
  overall_rationale: string
  confidence: number
  artifacts_created: string[]
}

export function getScriptContext(projectId: string): Promise<ScriptContextResponse | null> {
  return request<ScriptContextResponse | null>(`/api/projects/${projectId}/script-context`)
}

export function suggestIntentMood(projectId: string): Promise<IntentMoodSuggestion> {
  return request<IntentMoodSuggestion>(`/api/projects/${projectId}/intent-mood/suggest`, {
    method: 'POST',
  })
}

export function getStylePresets(projectId: string): Promise<StylePresetResponse[]> {
  return request<StylePresetResponse[]>(`/api/projects/${projectId}/style-presets`)
}

export function getIntentMood(
  projectId: string,
  sceneId?: string,
): Promise<IntentMoodResponse | null> {
  const url = sceneId
    ? `/api/projects/${projectId}/intent-mood?scene_id=${encodeURIComponent(sceneId)}`
    : `/api/projects/${projectId}/intent-mood`
  return request<IntentMoodResponse | null>(url)
}

export function saveIntentMood(projectId: string, data: IntentMoodInput): Promise<IntentMoodResponse> {
  return request<IntentMoodResponse>(`/api/projects/${projectId}/intent-mood`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function propagateMood(
  projectId: string,
  scope?: string,
  sceneId?: string,
): Promise<PropagationResponse> {
  return request<PropagationResponse>(`/api/projects/${projectId}/intent-mood/propagate`, {
    method: 'POST',
    body: JSON.stringify({ scope: scope ?? 'project', scene_id: sceneId }),
  })
}
