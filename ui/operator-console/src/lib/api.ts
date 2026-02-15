// API client for CineForge Operator Console backend.
// Ported from operator-console-lite/src/api.ts.

import type {
  ApiError,
  ArtifactDetailResponse,
  ArtifactEditRequest,
  ArtifactEditResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  ProjectSummary,
  RecentProjectSummary,
  RecipeSummary,
  RunEventsResponse,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
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

export function createProject(projectPath: string): Promise<ProjectSummary> {
  return request<ProjectSummary>('/api/projects/new', {
    method: 'POST',
    body: JSON.stringify({ project_path: projectPath }),
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
