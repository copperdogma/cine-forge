// TanStack React Query hooks for CineForge API client.

import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query'
import type {
  ArtifactDetailResponse,
  ArtifactEditRequest,
  ArtifactEditResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  InputFileSummary,
  ProjectSummary,
  ProjectState,
  RecentProjectSummary,
  RecipeSummary,
  RunEventsResponse,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
  UploadedInputResponse,
} from './types'
import * as api from './api'

// Scene data types for UI components
export interface Scene {
  index: number
  heading: string
  location: string
  intExt: 'INT' | 'EXT' | 'INT/EXT'
  timeOfDay: string
  summary: string
}

// --- Recipes ---

export function useRecipes() {
  return useQuery<RecipeSummary[]>({
    queryKey: ['recipes'],
    queryFn: api.listRecipes,
  })
}

// --- Projects ---

export function useRecentProjects() {
  return useQuery<RecentProjectSummary[]>({
    queryKey: ['projects', 'recent'],
    queryFn: api.listRecentProjects,
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery<ProjectSummary>({
    queryKey: ['projects', projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, string>({
    mutationFn: api.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useOpenProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, string>({
    mutationFn: api.openProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUploadInput(projectId: string) {
  return useMutation<UploadedInputResponse, Error, File>({
    mutationFn: (file: File) => api.uploadProjectInput(projectId, file),
  })
}

// --- Inputs ---

export function useProjectInputs(projectId: string | undefined) {
  return useQuery<InputFileSummary[]>({
    queryKey: ['projects', projectId, 'inputs'],
    queryFn: () => api.listProjectInputs(projectId!),
    enabled: !!projectId,
  })
}

export function useProjectInputContent(projectId: string | undefined, filename: string | undefined) {
  return useQuery<string>({
    queryKey: ['projects', projectId, 'inputs', filename, 'content'],
    queryFn: () => api.getProjectInputContent(projectId!, filename!),
    enabled: !!(projectId && filename),
    staleTime: Infinity,
  })
}

// --- Project State ---

export function useProjectState(projectId: string | undefined): ProjectState {
  const { data: project } = useProject(projectId)
  const { data: runs } = useRuns(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)

  if (!project) return 'empty'

  const hasInputs = project.has_inputs
  const hasArtifacts = (artifactGroups?.length ?? 0) > 0
  const hasRuns = (runs?.length ?? 0) > 0
  const hasActiveRun = runs?.some(r => r.status === 'running' || r.status === 'pending') ?? false

  if (!hasInputs) return 'empty'
  if (hasActiveRun) return 'processing'
  if (hasArtifacts) {
    // Check if we have creative artifacts (bibles, etc.) beyond just extraction
    const hasCreativeArtifacts = artifactGroups?.some(
      g => g.artifact_type === 'bible_manifest' || g.artifact_type === 'entity_graph'
    ) ?? false
    return hasCreativeArtifacts ? 'complete' : 'analyzed'
  }
  if (hasRuns && !hasArtifacts) return 'analyzed' // runs completed but artifacts may be zero (edge case)
  return 'fresh_import'
}

// --- Runs ---

export function useRuns(projectId: string | undefined) {
  return useQuery<RunSummary[]>({
    queryKey: ['projects', projectId, 'runs'],
    queryFn: () => api.listRuns(projectId!),
    enabled: !!projectId,
  })
}

export function useStartRun() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, RunStartPayload>({
    mutationFn: api.startRun,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.project_id, 'runs'],
      })
    },
  })
}

export function useRunState(runId: string | undefined) {
  return useQuery<RunStateResponse>({
    queryKey: ['runs', runId, 'state'],
    queryFn: () => api.getRunState(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.state?.finished_at ? false : 2000
    },
  })
}

export function useRunEvents(runId: string | undefined) {
  return useQuery<RunEventsResponse>({
    queryKey: ['runs', runId, 'events'],
    queryFn: () => api.getRunEvents(runId!),
    enabled: !!runId,
  })
}

// --- Artifacts ---

export function useArtifactGroups(projectId: string | undefined) {
  return useQuery<ArtifactGroupSummary[]>({
    queryKey: ['projects', projectId, 'artifacts'],
    queryFn: () => api.listArtifactGroups(projectId!),
    enabled: !!projectId,
  })
}

export function useArtifactVersions(
  projectId: string | undefined,
  artifactType: string | undefined,
  entityId: string | undefined,
) {
  return useQuery<ArtifactVersionSummary[]>({
    queryKey: ['projects', projectId, 'artifacts', artifactType, entityId],
    queryFn: () => api.listArtifactVersions(projectId!, artifactType!, entityId!),
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
    queryFn: () => api.getArtifact(projectId!, artifactType!, entityId!, version!),
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
      api.editArtifact(projectId, artifactType, entityId, payload),
    onSuccess: (_data, variables) => {
      // Invalidate artifact queries to refetch the new version
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'artifacts', variables.artifactType],
      })
    },
  })
}

// --- Scenes (derived from artifacts) ---

/**
 * Transforms artifact data into Scene format for the SceneStrip component.
 * Handles both individual scene artifacts and scene_breakdown artifacts.
 */
function transformArtifactToScene(artifact: ArtifactDetailResponse, fallbackIndex: number): Scene | null {
  const data = artifact.payload.data as any

  // Extract fields from artifact data
  const sceneNumber = data?.scene_number ?? fallbackIndex
  const heading = data?.heading ?? data?.scene_heading ?? `Scene ${sceneNumber}`
  const location = data?.location ?? data?.scene_location ?? heading
  const intExtRaw = data?.int_ext ?? data?.interior_exterior ?? 'INT'
  const timeOfDay = data?.time_of_day ?? data?.time ?? 'DAY'
  const summary = data?.summary ?? data?.description ?? heading

  // Map int_ext to union type, handling variations
  let intExt: 'INT' | 'EXT' | 'INT/EXT' = 'INT'
  const normalized = intExtRaw.toUpperCase().trim()
  if (normalized === 'EXT' || normalized === 'EXTERIOR') {
    intExt = 'EXT'
  } else if (normalized === 'INT/EXT' || normalized === 'INT./EXT.' || normalized === 'BOTH') {
    intExt = 'INT/EXT'
  }

  return {
    index: sceneNumber,
    heading,
    location,
    intExt,
    timeOfDay: timeOfDay.toUpperCase(),
    summary,
  }
}

/**
 * Hook to fetch and transform scene data from artifacts.
 * Looks for both individual 'scene' artifacts and 'scene_breakdown' artifact.
 */
export function useScenes(projectId: string | undefined) {
  // First, get the list of artifact groups to find scene-related artifacts
  const { data: artifactGroups } = useArtifactGroups(projectId)

  // Find all scene-related artifact groups
  const sceneGroups = artifactGroups?.filter(
    (g) => g.artifact_type === 'scene' || g.artifact_type === 'scene_breakdown'
  ) ?? []

  // Fetch all scene artifacts in parallel
  const sceneQueries = useQueries({
    queries: sceneGroups.map((group) => ({
      queryKey: ['projects', projectId, 'artifacts', group.artifact_type, group.entity_id, group.latest_version],
      queryFn: () => api.getArtifact(projectId!, group.artifact_type, group.entity_id ?? 'project', group.latest_version),
      enabled: !!projectId && sceneGroups.length > 0,
    })),
  })

  // Transform fetched artifacts into Scene objects
  const scenes: Scene[] = []

  sceneQueries.forEach((query, index) => {
    if (!query.data) return

    const artifact = query.data
    const group = sceneGroups[index]

    // Handle scene_breakdown artifact (contains multiple scenes)
    if (group.artifact_type === 'scene_breakdown') {
      const data = artifact.payload.data as any
      const sceneList = data?.scenes ?? []

      sceneList.forEach((sceneData: any, idx: number) => {
        const sceneNumber = sceneData?.scene_number ?? idx + 1
        const heading = sceneData?.heading ?? sceneData?.scene_heading ?? `Scene ${sceneNumber}`
        const location = sceneData?.location ?? sceneData?.scene_location ?? heading
        const intExtRaw = sceneData?.int_ext ?? sceneData?.interior_exterior ?? 'INT'
        const timeOfDay = sceneData?.time_of_day ?? sceneData?.time ?? 'DAY'
        const summary = sceneData?.summary ?? sceneData?.description ?? heading

        let intExt: 'INT' | 'EXT' | 'INT/EXT' = 'INT'
        const normalized = intExtRaw.toUpperCase().trim()
        if (normalized === 'EXT' || normalized === 'EXTERIOR') {
          intExt = 'EXT'
        } else if (normalized === 'INT/EXT' || normalized === 'INT./EXT.' || normalized === 'BOTH') {
          intExt = 'INT/EXT'
        }

        scenes.push({
          index: sceneNumber,
          heading,
          location,
          intExt,
          timeOfDay: timeOfDay.toUpperCase(),
          summary,
        })
      })
    } else {
      // Handle individual scene artifact
      const scene = transformArtifactToScene(artifact, index + 1)
      if (scene) {
        scenes.push(scene)
      }
    }
  })

  // Sort scenes by index
  scenes.sort((a, b) => a.index - b.index)

  // Determine loading state: loading if any query is loading
  const isLoading = sceneQueries.some((q) => q.isLoading)

  return {
    data: scenes,
    isLoading,
  }
}
