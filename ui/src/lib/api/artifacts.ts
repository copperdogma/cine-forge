import type {
  ArtifactDetailResponse,
  ArtifactEditRequest,
  ArtifactEditResponse,
  ArtifactGroupSummary,
  ArtifactHealthOverrideRequest,
  ArtifactHealthOverrideResponse,
  ArtifactVersionSummary,
  ImpactAssessmentRequest,
  ImpactAssessmentResponse,
  ImpactPreviewRequest,
  ImpactPreviewResponse,
} from '../types'
import { request } from './core'

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

export function previewImpactScope(
  projectId: string,
  payload: ImpactPreviewRequest,
): Promise<ImpactPreviewResponse> {
  return request<ImpactPreviewResponse>(`/api/projects/${projectId}/impact/preview`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function runImpactAssessment(
  projectId: string,
  payload: ImpactAssessmentRequest,
): Promise<ImpactAssessmentResponse> {
  return request<ImpactAssessmentResponse>(`/api/projects/${projectId}/impact/assess`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function overrideArtifactHealth(
  projectId: string,
  payload: ArtifactHealthOverrideRequest,
): Promise<ArtifactHealthOverrideResponse> {
  return request<ArtifactHealthOverrideResponse>(`/api/projects/${projectId}/impact/override`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
