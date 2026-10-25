import { useCallback, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { inspectMediaExecution, confirmMediaExecution } from '../api/media-generation'
import { useArtifactGroups } from './artifacts'
import { useProject } from './projects'
import { useMediaPreparation } from './media-preparation'
import { useChatStore } from '../chat-store'
import { canConfirmMedia, canReuseMediaPreparation, mediaSelectionKey, mediaSourceKey } from '../media-generation-policy'
import type { MediaExecutionPlanResponse, MediaRecipeId } from '../media-generation-types'
import type { ArtifactGroupSummary } from '../types'

export function useMediaGeneration(projectId: string, sceneId: string, recipeId: MediaRecipeId) {
  const queryClient = useQueryClient()
  const { data: groups } = useArtifactGroups(projectId)
  const { data: project } = useProject(projectId)
  const sourceKey = mediaSourceKey(project, groups)
  const [chosen, updateSelection] = useState<{ sourceKey: string; clips: string[] | null } | null>(null)
  const selection = chosen?.sourceKey === sourceKey ? chosen.clips : null
  const [review, setReview] = useState<{ response: MediaExecutionPlanResponse; key: string } | null>(null)
  const [catalog, setCatalog] = useState<{ sourceKey: string; units: MediaExecutionPlanResponse['plan']['units'] }>({ sourceKey: '', units: [] })
  const [rejected, setRejected] = useState(false)
  const currentKey = `${sourceKey}:${mediaSelectionKey(selection)}`
  const inspection = useMutation({
    mutationFn: async ({ clips, key, sourceKey }: { clips: string[] | null; key: string; sourceKey: string }) => ({
      response: await inspectMediaExecution(projectId, {
        recipe_id: recipeId, scene_id: sceneId,
        ...(clips !== null ? { render_clip_ids: clips } : {}),
      }), key, sourceKey,
    }),
    onSuccess: result => {
      setReview(result)
      setRejected(false)
      setCatalog(current => {
        const fresh = result.response.plan.units
        if (result.response.plan.render_clip_ids === null || current.sourceKey !== result.sourceKey) {
          return { sourceKey: result.sourceKey, units: fresh }
        }
        const updates = new Map(fresh.map(unit => [unit.entity_id, unit]))
        return { sourceKey: result.sourceKey, units: current.units.map(unit => updates.get(unit.entity_id) ?? unit) }
      })
    },
  })
  const { mutateAsync: inspectAsync } = inspection
  const inspectPrepared = useCallback(() => {
    const nextProject = queryClient.getQueryData(['projects', projectId])
    const nextGroups = queryClient.getQueryData<ArtifactGroupSummary[]>(['projects', projectId, 'artifacts'])
    const sourceKey = mediaSourceKey(nextProject, nextGroups)
    return inspectAsync({ clips: null, key: `${sourceKey}:all`, sourceKey })
  }, [inspectAsync, projectId, queryClient])
  const confirmation = useMutation({ mutationFn: confirmMediaExecution })
  const prep = useMediaPreparation(projectId, sceneId, recipeId, inspection.isPending || confirmation.isPending, inspectPrepared)
  const busy = prep.busy
  const inspect = () => {
    if (busy || selection?.length === 0) return
    confirmation.reset()
    inspection.mutate({ clips: selection, key: currentKey, sourceKey })
  }
  const canConfirm = canConfirmMedia({
    inspection: review?.response, projectId, sceneId, recipeId, currentKey,
    inspectedKey: review?.key ?? null, busy, rejected: rejected || inspection.isError,
    generationPreflight: prep.generationPreflight.isError ? undefined : prep.generationPreflight.data,
    availabilityBusy: prep.generationPreflight.isFetching || prep.generationPreflight.isPending,
  })
  async function confirm() {
    if (!canConfirm || !review) return
    try {
      const { run_id } = await confirmation.mutateAsync({ project_id: projectId, media_execution_plan_ref: review.response.plan_ref })
      setRejected(true)
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success('Confirmed video generation started for the inspected clips.')
    } catch { setRejected(true) }
  }
  function setSelection(next: string[] | null) {
    setRejected(true)
    confirmation.reset()
    updateSelection({ sourceKey, clips: next })
  }
  const reusesExistingPlan = canReuseMediaPreparation(prep.preflight.data, !!groups?.some(group => group.artifact_type === 'render_clip_plan' && group.entity_id === sceneId))
  function prepare() {
    if (!prep.canPrepare) return
    setRejected(true)
    setSelection(null)
    if (reusesExistingPlan) {
      toast.info('Using the existing clip plan. Inspect it before confirming video generation.')
      return inspectPrepared().catch(() => { /* Inspection errors are surfaced beside the action. */ })
    }
    return prep.prepare()
  }
  return { selection, setSelection, review: review?.response, catalog: catalog.sourceKey === sourceKey ? catalog.units : [], inspect, prepare, confirm,
    busy, preparing: prep.preparing, canConfirm, preflight: prep.preflight, generationPreflight: prep.generationPreflight,
    canPrepare: prep.canPrepare, reusesExistingPlan, canInspect: !!groups && !busy && selection?.length !== 0,
    stale: !!review && (review.key !== currentKey || rejected),
    error: inspection.error ?? confirmation.error ?? prep.error,
    inspecting: inspection.isPending, confirming: confirmation.isPending,
    preparationFailed: prep.preparationFailed, preparationPaused: prep.preparationPaused,
    preparationIncomplete: prep.preparationIncomplete, preparationRunId: prep.preparationRunId,
  }
}
