import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  editArtifact,
  getArtifact,
  getPipelineGraph,
  listArtifactGroups,
  listArtifactVersions,
  overrideArtifactHealth,
  previewImpactScope,
  runImpactAssessment,
} from '../api'
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
  PipelineGraphResponse,
} from '../types'

export function usePipelineGraph(projectId: string | undefined, activeRunId?: string | null) {
  return useQuery<PipelineGraphResponse>({
    queryKey: ['projects', projectId, 'pipeline-graph'],
    queryFn: () => getPipelineGraph(projectId!),
    enabled: !!projectId,
    refetchInterval: activeRunId ? 2000 : 30000,
    refetchIntervalInBackground: false,
  })
}

export function useArtifactGroups(projectId: string | undefined, refetchInterval?: number) {
  return useQuery<ArtifactGroupSummary[]>({
    queryKey: ['projects', projectId, 'artifacts'],
    queryFn: () => listArtifactGroups(projectId!),
    enabled: !!projectId,
    refetchInterval,
  })
}

export function useArtifactVersions(
  projectId: string | undefined,
  artifactType: string | undefined,
  entityId: string | undefined,
) {
  return useQuery<ArtifactVersionSummary[]>({
    queryKey: ['projects', projectId, 'artifacts', artifactType, entityId],
    queryFn: () => listArtifactVersions(projectId!, artifactType!, entityId!),
    enabled: !!(projectId && artifactType && entityId),
  })
}

export function useArtifact(
  projectId: string | undefined,
  artifactType: string | undefined,
  entityId: string | undefined,
  version: number | undefined,
) {
  return useQuery<ArtifactDetailResponse>({
    queryKey: ['projects', projectId, 'artifacts', artifactType, entityId, version],
    queryFn: () => getArtifact(projectId!, artifactType!, entityId!, version!),
    enabled: !!(projectId && artifactType && entityId && version !== undefined),
  })
}

export function useEditArtifact() {
  const queryClient = useQueryClient()
  return useMutation<
    ArtifactEditResponse,
    Error,
    {
      projectId: string
      artifactType: string
      entityId: string
      payload: ArtifactEditRequest
    }
  >({
    mutationFn: ({ projectId, artifactType, entityId, payload }) =>
      editArtifact(projectId, artifactType, entityId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'artifacts', variables.artifactType],
      })
    },
  })
}

export function usePreviewImpactScope() {
  return useMutation<
    ImpactPreviewResponse,
    Error,
    {
      projectId: string
      payload: ImpactPreviewRequest
    }
  >({
    mutationFn: ({ projectId, payload }) => previewImpactScope(projectId, payload),
  })
}

export function useRunImpactAssessment() {
  const queryClient = useQueryClient()
  return useMutation<
    ImpactAssessmentResponse,
    Error,
    {
      projectId: string
      payload: ImpactAssessmentRequest
    }
  >({
    mutationFn: ({ projectId, payload }) => runImpactAssessment(projectId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId, 'artifacts'] })
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'pipeline-graph'],
      })
      queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId] })
    },
  })
}

export function useOverrideArtifactHealth() {
  const queryClient = useQueryClient()
  return useMutation<
    ArtifactHealthOverrideResponse,
    Error,
    {
      projectId: string
      payload: ArtifactHealthOverrideRequest
    }
  >({
    mutationFn: ({ projectId, payload }) => overrideArtifactHealth(projectId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId, 'artifacts'] })
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'pipeline-graph'],
      })
      queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId] })
    },
  })
}

export function useSceneIndex(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const sceneIndexGroup = groups?.find((group) => group.artifact_type === 'scene_index')

  return useArtifact(
    projectId,
    'scene_index',
    sceneIndexGroup?.entity_id ?? 'project',
    sceneIndexGroup?.latest_version,
  )
}

export function useCanonicalScript(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const group = groups?.find((artifactGroup) => artifactGroup.artifact_type === 'canonical_script')

  return useArtifact(
    projectId,
    'canonical_script',
    group?.entity_id ?? 'project',
    group?.latest_version,
  )
}

export function useScriptBible(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const group = groups?.find((artifactGroup) => artifactGroup.artifact_type === 'script_bible')

  return useArtifact(
    projectId,
    'script_bible',
    group?.entity_id ?? 'project',
    group?.latest_version,
  )
}

export function useEntityGraph(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const graphGroup = groups?.find((group) => group.artifact_type === 'entity_graph')

  return useArtifact(
    projectId,
    'entity_graph',
    graphGroup?.entity_id ?? 'project',
    graphGroup?.latest_version,
  )
}
