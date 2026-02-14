import type {
  ApiError,
  ArtifactDetailResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  ProjectSummary,
  RecentProjectSummary,
  RunEventsResponse,
  RunStateResponse,
  RunSummary,
  UploadedInputResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export type RunStartPayload = {
  project_id: string;
  input_file: string;
  default_model: string;
  work_model?: string;
  verify_model?: string;
  escalate_model?: string;
  recipe_id?: string;
  skip_qa?: boolean;
  qa_model?: string;
  accept_config: boolean;
  run_id?: string;
  force?: boolean;
  start_from?: string;
  config_file?: string;
  config_overrides?: Record<string, unknown>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Cannot reach Operator Console API at ${API_BASE}. Start the backend with 'PYTHONPATH=src python -m cine_forge.operator_console --reload'.`,
      );
    }
    throw error;
  }
  if (!response.ok) {
    let payload: ApiError | null = null;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = null;
    }
    const message = payload
      ? `${payload.message}${payload.hint ? ` (${payload.hint})` : ""}`
      : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export function listRecentProjects(): Promise<RecentProjectSummary[]> {
  return request<RecentProjectSummary[]>("/api/projects/recent");
}

export async function uploadProjectInput(
  projectId: string,
  file: File,
): Promise<UploadedInputResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/projects/${projectId}/inputs/upload`, {
      method: "POST",
      body: form,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Cannot reach Operator Console API at ${API_BASE}. Start the backend with 'PYTHONPATH=src python -m cine_forge.operator_console --reload'.`,
      );
    }
    throw error;
  }
  if (!response.ok) {
    let payload: ApiError | null = null;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = null;
    }
    const message = payload
      ? `${payload.message}${payload.hint ? ` (${payload.hint})` : ""}`
      : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as UploadedInputResponse;
}

export function createProject(projectPath: string): Promise<ProjectSummary> {
  return request<ProjectSummary>("/api/projects/new", {
    method: "POST",
    body: JSON.stringify({ project_path: projectPath }),
  });
}

export function openProject(projectPath: string): Promise<ProjectSummary> {
  return request<ProjectSummary>("/api/projects/open", {
    method: "POST",
    body: JSON.stringify({ project_path: projectPath }),
  });
}

export function getProject(projectId: string): Promise<ProjectSummary> {
  return request<ProjectSummary>(`/api/projects/${projectId}`);
}

export function listRuns(projectId: string): Promise<RunSummary[]> {
  return request<RunSummary[]>(`/api/projects/${projectId}/runs`);
}

export function startRun(payload: RunStartPayload): Promise<{ run_id: string }> {
  return request<{ run_id: string }>("/api/runs/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRunState(runId: string): Promise<RunStateResponse> {
  return request<RunStateResponse>(`/api/runs/${runId}/state`);
}

export function getRunEvents(runId: string): Promise<RunEventsResponse> {
  return request<RunEventsResponse>(`/api/runs/${runId}/events`);
}

export function listArtifactGroups(projectId: string): Promise<ArtifactGroupSummary[]> {
  return request<ArtifactGroupSummary[]>(`/api/projects/${projectId}/artifacts`);
}

export function listArtifactVersions(
  projectId: string,
  artifactType: string,
  entityId: string,
): Promise<ArtifactVersionSummary[]> {
  return request<ArtifactVersionSummary[]>(
    `/api/projects/${projectId}/artifacts/${artifactType}/${entityId}`,
  );
}

export function getArtifact(
  projectId: string,
  artifactType: string,
  entityId: string,
  version: number,
): Promise<ArtifactDetailResponse> {
  return request<ArtifactDetailResponse>(
    `/api/projects/${projectId}/artifacts/${artifactType}/${entityId}/${version}`,
  );
}
