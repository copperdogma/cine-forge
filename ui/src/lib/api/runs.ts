import type {
  ArtifactEditResponse,
  RunEventsResponse,
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

export function resumeRun(runId: string): Promise<{ run_id: string }> {
  return request<{ run_id: string }>(`/api/runs/${runId}/resume`, {
    method: 'POST',
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
