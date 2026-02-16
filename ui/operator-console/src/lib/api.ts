// API client for CineForge Operator Console backend.
// Ported from operator-console-lite/src/api.ts.

import type {
  ApiError,
  ArtifactDetailResponse,
  ArtifactEditRequest,
  ArtifactEditResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  ChatMessage,
  InputFileSummary,
  ProjectSummary,
  RecentProjectSummary,
  RecipeSummary,
  RunEventsResponse,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
  SearchResponse,
  SlugPreviewResponse,
  UploadedInputResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

class ApiRequestError extends Error {
  hint?: string
  constructor(message: string, hint?: string) {
    super(message)
    this.name = 'ApiRequestError'
    this.hint = hint
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(
        `Cannot reach API at ${API_BASE}. Start the backend with: PYTHONPATH=src python -m cine_forge.api`
      )
    }
    throw error
  }
  if (!response.ok) {
    let payload: ApiError | null = null
    try {
      payload = (await response.json()) as ApiError
    } catch {
      payload = null
    }
    const message = payload?.message ?? `Request failed (${response.status})`
    throw new ApiRequestError(message, payload?.hint ?? undefined)
  }
  return (await response.json()) as T
}

// --- Recipes ---

export function listRecipes(): Promise<RecipeSummary[]> {
  return request<RecipeSummary[]>('/api/recipes')
}

// --- Projects ---

export function listRecentProjects(): Promise<RecentProjectSummary[]> {
  return request<RecentProjectSummary[]>('/api/projects/recent')
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
  settings: { display_name?: string },
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
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/projects/${projectId}/inputs/upload`, {
      method: 'POST',
      body: form,
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(
        `Cannot reach API at ${API_BASE}. Start the backend.`
      )
    }
    throw error
  }
  if (!response.ok) {
    let payload: ApiError | null = null
    try {
      payload = (await response.json()) as ApiError
    } catch {
      payload = null
    }
    const message = payload?.message ?? `Upload failed (${response.status})`
    throw new ApiRequestError(message, payload?.hint ?? undefined)
  }
  return (await response.json()) as UploadedInputResponse
}

// --- Inputs ---

export function listProjectInputs(projectId: string): Promise<InputFileSummary[]> {
  return request<InputFileSummary[]>(`/api/projects/${projectId}/inputs`)
}

export async function getProjectInputContent(
  projectId: string,
  filename: string,
): Promise<string> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/projects/${projectId}/inputs/${encodeURIComponent(filename)}`)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(`Cannot reach API at ${API_BASE}. Start the backend.`)
    }
    throw error
  }
  if (!response.ok) {
    throw new ApiRequestError(`Failed to fetch input file (${response.status})`)
  }
  return response.text()
}

// --- Chat ---

export function getChatMessages(projectId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/api/projects/${projectId}/chat`)
}

export function postChatMessage(projectId: string, message: ChatMessage): Promise<ChatMessage> {
  return request<ChatMessage>(`/api/projects/${projectId}/chat`, {
    method: 'POST',
    body: JSON.stringify(message),
  })
}

// --- Search ---

export function searchProject(projectId: string, query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/api/projects/${projectId}/search?q=${encodeURIComponent(query)}`)
}

// --- Runs ---

export function listRuns(projectId: string): Promise<RunSummary[]> {
  return request<RunSummary[]>(`/api/projects/${projectId}/runs`)
}

export function startRun(payload: RunStartPayload): Promise<{ run_id: string }> {
  return request<{ run_id: string }>('/api/runs/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getRunState(runId: string): Promise<RunStateResponse> {
  return request<RunStateResponse>(`/api/runs/${runId}/state`)
}

export function getRunEvents(runId: string): Promise<RunEventsResponse> {
  return request<RunEventsResponse>(`/api/runs/${runId}/events`)
}

// --- Artifacts ---

export function listArtifactGroups(projectId: string): Promise<ArtifactGroupSummary[]> {
  return request<ArtifactGroupSummary[]>(`/api/projects/${projectId}/artifacts`)
}

export function listArtifactVersions(
  projectId: string,
  artifactType: string,
  entityId: string,
): Promise<ArtifactVersionSummary[]> {
  return request<ArtifactVersionSummary[]>(
    `/api/projects/${projectId}/artifacts/${artifactType}/${entityId}`,
  )
}

export function getArtifact(
  projectId: string,
  artifactType: string,
  entityId: string,
  version: number,
): Promise<ArtifactDetailResponse> {
  return request<ArtifactDetailResponse>(
    `/api/projects/${projectId}/artifacts/${artifactType}/${entityId}/${version}`,
  )
}

export function editArtifact(
  projectId: string,
  artifactType: string,
  entityId: string,
  payload: ArtifactEditRequest,
): Promise<ArtifactEditResponse> {
  return request<ArtifactEditResponse>(
    `/api/projects/${projectId}/artifacts/${artifactType}/${entityId}/edit`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}
