import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createProject,
  getProject,
  getProjectInputContent,
  listProjectInputs,
  listRecentProjects,
  openProject,
  updateProjectSettings,
  uploadProjectInput,
} from '../api'
import type {
  InputFileSummary,
  ProjectState,
  ProjectSummary,
  RecentProjectSummary,
  UploadedInputResponse,
} from '../types'
import { useArtifactGroups } from './artifacts'
import { useRuns } from './runs'

export function useRecentProjects(limit?: number) {
  return useQuery<RecentProjectSummary[]>({
    queryKey: ['projects', 'recent', limit ?? 'all'],
    queryFn: () => listRecentProjects(limit),
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery<ProjectSummary>({
    queryKey: ['projects', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  })
}

export function useStickyPreference<T extends string>(
  projectId: string | undefined,
  key: string,
  defaultValue: T,
): [T, (value: T) => void] {
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const currentValue = (project?.ui_preferences?.[key] as T) ?? defaultValue

  const setValue = useCallback((value: T) => {
    if (!projectId) return

    queryClient.setQueryData<ProjectSummary>(['projects', projectId], (old) => {
      if (!old) return old
      return {
        ...old,
        ui_preferences: { ...old.ui_preferences, [key]: value },
      }
    })

    updateProjectSettings(projectId, {
      ui_preferences: { [key]: value },
    }).catch(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    })
  }, [projectId, key, queryClient])

  return [currentValue, setValue]
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, { slug: string; displayName: string }>({
    mutationFn: ({ slug, displayName }) => createProject(slug, displayName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useOpenProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, string>({
    mutationFn: openProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUploadInput(projectId: string) {
  return useMutation<UploadedInputResponse, Error, File>({
    mutationFn: (file: File) => uploadProjectInput(projectId, file),
  })
}

export function useProjectInputs(projectId: string | undefined) {
  return useQuery<InputFileSummary[]>({
    queryKey: ['projects', projectId, 'inputs'],
    queryFn: () => listProjectInputs(projectId!),
    enabled: !!projectId,
  })
}

export function useProjectInputContent(
  projectId: string | undefined,
  filename: string | undefined,
) {
  return useQuery<string>({
    queryKey: ['projects', projectId, 'inputs', filename, 'content'],
    queryFn: () => getProjectInputContent(projectId!, filename!),
    enabled: !!(projectId && filename),
    staleTime: Infinity,
  })
}

export function useProjectState(projectId: string | undefined): ProjectState {
  const { data: project } = useProject(projectId)
  const { data: runs } = useRuns(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)

  if (!project) return 'empty'

  const hasInputs = project.has_inputs
  const hasArtifacts = (artifactGroups?.length ?? 0) > 0
  const hasRuns = (runs?.length ?? 0) > 0
  const hasActiveRun = runs?.some((run) => run.status === 'running' || run.status === 'pending') ?? false

  if (!hasInputs) return 'empty'
  if (hasActiveRun) return 'processing'
  if (hasArtifacts) {
    const hasCreativeArtifacts = artifactGroups?.some(
      (group) => group.artifact_type === 'bible_manifest' || group.artifact_type === 'entity_graph',
    ) ?? false
    return hasCreativeArtifacts ? 'complete' : 'analyzed'
  }
  if (hasRuns && !hasArtifacts) return 'analyzed'
  return 'fresh_import'
}
