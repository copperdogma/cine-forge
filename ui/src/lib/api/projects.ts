import type {
  InputFileSummary,
  PipelineGraphResponse,
  ProductionFormat,
  ProjectSummary,
  RecentProjectSummary,
  SearchResponse,
  SlugPreviewResponse,
  UploadedInputResponse,
} from '../types'
import { request, requestFormData, requestText } from './core'

export function listRecentProjects(limit?: number): Promise<RecentProjectSummary[]> {
  const url = limit != null ? `/api/projects/recent?limit=${limit}` : '/api/projects/recent'
  return request<RecentProjectSummary[]>(url)
}

export function countProjects(): Promise<{ total: number }> {
  return request<{ total: number }>('/api/projects/count')
}

export function previewSlug(
  contentSnippet: string,
  originalFilename: string,
): Promise<SlugPreviewResponse> {
  return request<SlugPreviewResponse>('/api/projects/preview-slug', {
    method: 'POST',
    body: JSON.stringify({ content_snippet: contentSnippet, original_filename: originalFilename }),
  })
}

export async function quickScan(file: File): Promise<SlugPreviewResponse> {
  const form = new FormData()
  const blob = file.slice(0, 1024 * 1024)
  form.append('file', blob, file.name)
  return requestFormData<SlugPreviewResponse>('/api/projects/quick-scan', form, {
    method: 'POST',
  })
}

export function createProject(slug: string, displayName: string): Promise<ProjectSummary> {
  return request<ProjectSummary>('/api/projects/new', {
    method: 'POST',
    body: JSON.stringify({ slug, display_name: displayName }),
  })
}

export function openProject(projectPath: string): Promise<ProjectSummary> {
  return request<ProjectSummary>('/api/projects/open', {
    method: 'POST',
    body: JSON.stringify({ project_path: projectPath }),
  })
}

export function getProject(projectId: string): Promise<ProjectSummary> {
  return request<ProjectSummary>(`/api/projects/${projectId}`)
}

export function updateProjectSettings(
  projectId: string,
  settings: {
    display_name?: string
    human_control_mode?: 'autonomous' | 'checkpoint' | 'advisory'
    production_format?: ProductionFormat | null
    interaction_mode?: 'guided' | 'balanced' | 'expert'
    default_model?: string | null
    work_model?: string | null
    verify_model?: string | null
    escalate_model?: string | null
    project_budget_limit_usd?: number | null
    default_run_budget_limit_usd?: number | null
    budget_warning_threshold_ratio?: number | null
    preference_learning_enabled?: boolean
    preference_learning_cleared_at?: string | null
    ui_preferences?: Record<string, string>
  },
): Promise<ProjectSummary> {
  return request<ProjectSummary>(`/api/projects/${projectId}/settings`, {
    method: 'PATCH',
    body: JSON.stringify(settings),
  })
}

export async function uploadProjectInput(
  projectId: string,
  file: File,
): Promise<UploadedInputResponse> {
  const form = new FormData()
  form.append('file', file, file.name)
  return requestFormData<UploadedInputResponse>(`/api/projects/${projectId}/inputs/upload`, form, {
    method: 'POST',
  })
}

export function listProjectInputs(projectId: string): Promise<InputFileSummary[]> {
  return request<InputFileSummary[]>(`/api/projects/${projectId}/inputs`)
}

export function getProjectInputContent(projectId: string, filename: string): Promise<string> {
  return requestText(`/api/projects/${projectId}/inputs/${encodeURIComponent(filename)}`)
}

export function getPipelineGraph(projectId: string): Promise<PipelineGraphResponse> {
  return request<PipelineGraphResponse>(`/api/projects/${projectId}/pipeline-graph`)
}

export function searchProject(projectId: string, query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/api/projects/${projectId}/search?q=${encodeURIComponent(query)}`)
}
