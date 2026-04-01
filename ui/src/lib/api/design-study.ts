import { ApiRequestError, API_BASE, request } from './core'
import type { VisualCreativeBrief } from './intent-mood'

export type ImageDecision =
  | 'pending'
  | 'selected_final'
  | 'favorite'
  | 'rejected'
  | 'seed_for_variants'

export type DesignStudyEntityType = 'character' | 'location' | 'prop'

export interface DesignStudyImage {
  filename: string
  decision: ImageDecision
  guidance: string | null
  prompt_used: string
  model: string
  round_number: number
  created_at: string
}

export interface DesignStudyRound {
  round_number: number
  prompt: string
  model: string
  entity_type: DesignStudyEntityType
  entity_id: string
  directive: string | null
  positive_refs: string[]
  negative_refs: string[]
  seed_image_filename: string | null
  sources_used: string[]
  learned_preferences_used: string[]
  creative_brief_preview: VisualCreativeBrief | null
  count: number
  created_at: string
  images: DesignStudyImage[]
}

export interface DesignStudyState {
  entity_id: string
  entity_type: DesignStudyEntityType
  rounds: DesignStudyRound[]
  selected_final_filename: string | null
  last_updated: string
}

export interface GenerateDesignStudyParams {
  entity_type: DesignStudyEntityType
  count?: 1 | 2 | 4 | 8
  directive?: string | null
  positive_refs?: string[]
  negative_refs?: string[]
  seed_image_filename?: string | null
  model?: string
}

export interface DecideDesignStudyParams {
  filename: string
  decision: ImageDecision
  guidance?: string | null
}

export async function getDesignStudy(
  projectId: string,
  entityId: string,
): Promise<DesignStudyState | null> {
  try {
    return await request<DesignStudyState>(`/api/projects/${projectId}/design-study/${entityId}`)
  } catch (err) {
    if (
      err instanceof ApiRequestError
      && (err.message.includes('404') || err.message.toLowerCase().includes('no design study'))
    ) {
      return null
    }
    throw err
  }
}

export function generateDesignStudy(
  projectId: string,
  entityId: string,
  params: GenerateDesignStudyParams,
): Promise<DesignStudyState> {
  return request<DesignStudyState>(
    `/api/projects/${projectId}/design-study/${entityId}/generate`,
    { method: 'POST', body: JSON.stringify(params) },
  )
}

export function decideDesignStudy(
  projectId: string,
  entityId: string,
  params: DecideDesignStudyParams,
): Promise<{ updated: boolean }> {
  return request<{ updated: boolean }>(
    `/api/projects/${projectId}/design-study/${entityId}/decide`,
    { method: 'POST', body: JSON.stringify(params) },
  )
}

export function getDesignStudyImageUrl(
  projectId: string,
  entityId: string,
  filename: string,
): string {
  return `${API_BASE}/api/projects/${projectId}/design-study/${entityId}/images/${filename}`
}
