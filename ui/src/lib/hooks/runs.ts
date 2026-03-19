import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getRunEvents,
  getRunCosts,
  getRunState,
  getProjectCosts,
  listRuns,
  respondToReview,
  resumeRun,
  retryFailedStage,
  startRun,
} from '../api'
import { useChatStore } from '../chat-store'
import type {
  ArtifactEditResponse,
  ProjectCostSummary,
  RunEventsResponse,
  RunCostSummary,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
} from '../types'

export function useRuns(projectId: string | undefined) {
  return useQuery<RunSummary[]>({
    queryKey: ['projects', projectId, 'runs'],
    queryFn: () => listRuns(projectId!),
    enabled: !!projectId,
  })
}

export function useStartRun() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, RunStartPayload>({
    mutationFn: startRun,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.project_id, 'runs'],
      })
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.project_id, 'costs'],
      })
    },
  })
}

export function useRetryFailedStage() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, { runId: string; projectId?: string }>({
    mutationFn: ({ runId }) => retryFailedStage(runId),
    onSuccess: (_data, variables) => {
      if (variables.projectId) {
        queryClient.invalidateQueries({
          queryKey: ['projects', variables.projectId, 'runs'],
        })
      }
    },
  })
}

export function useResumeRun() {
  const queryClient = useQueryClient()
  return useMutation<
    { run_id: string },
    Error,
    { runId: string; projectId?: string; runBudgetLimitUsd?: number | null }
  >({
    mutationFn: ({ runId, runBudgetLimitUsd }) =>
      resumeRun(
        runId,
        runBudgetLimitUsd != null
          ? { run_budget_limit_usd: runBudgetLimitUsd }
          : undefined,
      ),
    onSuccess: (_data, variables) => {
      if (variables.projectId) {
        queryClient.invalidateQueries({
          queryKey: ['projects', variables.projectId, 'runs'],
        })
        queryClient.invalidateQueries({
          queryKey: ['projects', variables.projectId, 'costs'],
        })
      }
    },
  })
}

export function useRespondToReview() {
  const queryClient = useQueryClient()
  return useMutation<
    ArtifactEditResponse,
    Error,
    {
      projectId: string
      sceneId: string
      stageId: string
      approved: boolean
      feedback?: string
    }
  >({
    mutationFn: ({ projectId, sceneId, stageId, approved, feedback }) =>
      respondToReview(projectId, sceneId, stageId, approved, feedback),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'artifacts'],
      })
    },
  })
}

export function useRunState(runId: string | undefined) {
  return useQuery<RunStateResponse>({
    queryKey: ['runs', runId, 'state'],
    queryFn: () => getRunState(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.state?.finished_at ? false : 2000
    },
    refetchIntervalInBackground: true,
  })
}

export function useRunEvents(runId: string | undefined, finished?: boolean) {
  return useQuery<RunEventsResponse>({
    queryKey: ['runs', runId, 'events'],
    queryFn: () => getRunEvents(runId!),
    enabled: !!runId,
    refetchInterval: finished ? false : 3000,
    refetchIntervalInBackground: true,
  })
}

export function useRunCosts(runId: string | undefined) {
  return useQuery<RunCostSummary>({
    queryKey: ['runs', runId, 'costs'],
    queryFn: () => getRunCosts(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.finished_at ? false : 2000
    },
    refetchIntervalInBackground: true,
  })
}

export function useProjectCosts(projectId: string | undefined) {
  return useQuery<ProjectCostSummary>({
    queryKey: ['projects', projectId, 'costs'],
    queryFn: () => getProjectCosts(projectId!),
    enabled: !!projectId,
    refetchInterval: 3000,
    refetchIntervalInBackground: true,
  })
}

export function useActiveProjectRun(projectId: string | undefined) {
  const activeRunId = useChatStore((store) => (projectId ? store.activeRunId?.[projectId] ?? null : null))
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const recipeId = runState?.state.recipe_id ?? null
  const isRunning = !!activeRunId && !runState?.state.finished_at

  return {
    activeRunId,
    runState,
    recipeId,
    isRunning,
  }
}
