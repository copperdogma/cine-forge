import { request } from './core'
import type { MediaConfirmationPayload, MediaExecutionPlanResponse, MediaInspectionRequest } from '../media-generation-types'

export function inspectMediaExecution(projectId: string, payload: MediaInspectionRequest) {
  return request<MediaExecutionPlanResponse>(`/api/projects/${projectId}/media-execution-plans`, {
    method: 'POST', body: JSON.stringify(payload),
  })
}
export function confirmMediaExecution(payload: MediaConfirmationPayload) {
  return request<{ run_id: string }>('/api/runs/start', {
    method: 'POST', body: JSON.stringify(payload),
  })
}
