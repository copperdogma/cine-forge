import type {
  ArtifactEditResponse,
  ProjectCostSummary,
  RunEventsResponse,
  RunCostSummary,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
} from '../types'
import { request } from './core'

export function listRuns(projectId: string): Promise<RunSummary[]> {
  return request<RunSummary[]>(`/api/projects/${projectId}/runs`)
}

export function startRun(payload: RunStartPayload): Promise<{ run_id: string }> {
  return request<{ run_id: string }>('/api/runs/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function retryFailedStage(runId: string): Promise<{ run_id: string }> {
  return request<{ run_id: string }>(`/api/runs/${runId}/retry-failed-stage`, {
    method: 'POST',
  })
}

export function resumeRun(
  runId: string,
  overrides?: { run_budget_limit_usd?: number | null },
): Promise<{ run_id: string }> {
  return request<{ run_id: string }>(`/api/runs/${runId}/resume`, {
    method: 'POST',
    body: overrides ? JSON.stringify(overrides) : undefined,
  })
}

export function respondToReview(
  projectId: string,
  sceneId: string,
  stageId: string,
  approved: boolean,
  feedback?: string,
): Promise<ArtifactEditResponse> {
  return request<ArtifactEditResponse>(
    `/api/projects/${projectId}/reviews/${sceneId}/${stageId}/respond`,
    {
      method: 'POST',
      body: JSON.stringify({ approved, feedback }),
    },
  )
}

export function getRunState(runId: string): Promise<RunStateResponse> {
  return request<RunStateResponse>(`/api/runs/${runId}/state`)
}

export function getRunEvents(runId: string): Promise<RunEventsResponse> {
  return request<RunEventsResponse>(`/api/runs/${runId}/events`)
}

export function getRunCosts(runId: string): Promise<RunCostSummary> {
  return request<RunCostSummary>(`/api/runs/${runId}/costs`)
}

export function getProjectCosts(projectId: string): Promise<ProjectCostSummary> {
  return request<ProjectCostSummary>(`/api/projects/${projectId}/costs`)
}
