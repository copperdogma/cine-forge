import type {
  StylePackDraft,
  StylePackLibraryResponse,
  StylePackManualPromptResponse,
  StylePackProvider,
  StylePackSaveResponse,
} from '../types'
import { request } from './core'

export function getProjectStylePackLibrary(projectId: string): Promise<StylePackLibraryResponse> {
  return request<StylePackLibraryResponse>(`/api/projects/${projectId}/style-packs`)
}

export function generateStylePackDraft(
  projectId: string,
  payload: {
    role_id: string
    subject: string
    provider: StylePackProvider
  },
): Promise<StylePackDraft> {
  return request<StylePackDraft>(`/api/projects/${projectId}/style-packs/generate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getManualStylePackPrompt(
  projectId: string,
  payload: {
    role_id: string
    subject: string
  },
): Promise<StylePackManualPromptResponse> {
  return request<StylePackManualPromptResponse>(`/api/projects/${projectId}/style-packs/manual-prompt`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function importManualStylePackDraft(
  projectId: string,
  payload: {
    role_id: string
    subject: string
    raw_output: string
  },
): Promise<StylePackDraft> {
  return request<StylePackDraft>(`/api/projects/${projectId}/style-packs/manual-import`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function saveStylePackDraft(
  projectId: string,
  payload: {
    role_id: string
    style_pack_id: string
    display_name: string
    summary: string
    prompt_injection: string
    style_markdown: string
    additional_files: Array<{
      kind: 'description' | 'reference_image' | 'frame_grab' | 'palette' | 'notes' | 'audio_reference'
      path: string
      caption?: string | null
      content: string
    }>
    assign_to_role: boolean
  },
): Promise<StylePackSaveResponse> {
  return request<StylePackSaveResponse>(`/api/projects/${projectId}/style-packs/save`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
