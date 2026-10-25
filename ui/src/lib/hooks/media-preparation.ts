import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useArtifactGroups } from './artifacts'
import { useProject, useProjectInputs } from './projects'
import { isRunActive, isRunStateTerminal, runHasFailed, useRunState, useStartRun } from './runs'
import { useSceneActionPreflight } from './scene-actions'
import { useChatStore } from '../chat-store'
import { canPrepareMedia, mediaPreparationOutcome } from '../media-generation-policy'
import type { MediaRecipeId } from '../media-generation-types'

export function useMediaPreparation(projectId: string, sceneId: string, recipeId: MediaRecipeId,
  disabled: boolean, onPrepared: () => Promise<unknown>) {
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const activeRunId = useChatStore(store => store.activeRunId?.[projectId] ?? null)
  const { data: activeRun } = useRunState(activeRunId ?? undefined)
  const [startedPrepId, setStartedPrepId] = useState<string | null>(null)
  const recoveredPrep = activeRun?.state.recipe_id === recipeId
    && activeRun.state.runtime_params.end_at === 'render_clip_planning'
    && activeRun.state.runtime_params.scene_scope?.scene_ids.includes(sceneId)
  const trackedPrepId = startedPrepId ?? (recoveredPrep ? activeRunId : null)
  const { data: preparationRun } = useRunState(trackedPrepId ?? undefined)
  const handledPrepKey = useRef<string | null>(null)
  const { data: groups } = useArtifactGroups(projectId)
  const hasExistingClipPlan = !!groups?.some(group => group.artifact_type === 'render_clip_plan' && group.entity_id === sceneId)
  const outcome = mediaPreparationOutcome(preparationRun, hasExistingClipPlan)
  const startRun = useStartRun()
  const scope = { mode: 'current_scene' as const, scene_ids: [sceneId] }
  const preflight = useSceneActionPreflight(projectId, {
    recipe_id: recipeId, end_at: 'render_clip_planning', scene_scope: scope,
  })
  const generationPreflight = useSceneActionPreflight(projectId, { recipe_id: recipeId, scene_scope: scope })
  const preparing = isRunActive(trackedPrepId, preparationRun)
  const busy = disabled || isRunActive(activeRunId, activeRun) || preparing || startRun.isPending

  useEffect(() => {
    const terminalKey = `${trackedPrepId}:${outcome}`
    if (!trackedPrepId || !isRunStateTerminal(preparationRun) || handledPrepKey.current === terminalKey) return
    handledPrepKey.current = terminalKey
    void (async () => {
      await queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'artifacts'] })
      await queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'scene-action-preflight'] })
      if (outcome === 'complete' || outcome === 'existing') {
        if (outcome === 'complete') toast.success('Clip preparation complete. Inspect the prepared work before generating video.')
        else toast.info('No preparation stages ran. Inspecting the existing clip plan.')
        await onPrepared()
      }
    })().catch(() => { /* Inspection errors are surfaced by the inspection mutation. */ })
  }, [trackedPrepId, preparationRun, projectId, queryClient, onPrepared, outcome])

  async function prepare() {
    if (outcome === 'paused' || busy || !generationPreflight.data || generationPreflight.isFetching || generationPreflight.isError || !canPrepareMedia(preflight.data) || !inputs?.length || preflight.isFetching || preflight.isError) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId, input_file: inputs[inputs.length - 1].stored_path,
        default_model: project?.default_model ?? 'gpt-5.4-mini', recipe_id: recipeId,
        accept_config: true, start_from: preflight.data?.start_from ?? undefined,
        end_at: 'render_clip_planning', scene_scope: scope,
      })
      setStartedPrepId(run_id)
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success('Preparing the clip plan. Video generation still requires confirmation.')
    } catch { /* The mutation error is displayed beside the action. */ }
  }
  return { prepare, busy, preparing, preflight, generationPreflight, error: startRun.error,
    canPrepare: outcome !== 'paused' && !!generationPreflight.data && !generationPreflight.isFetching && !generationPreflight.isError && canPrepareMedia(preflight.data) && !!inputs?.length && !busy && !preflight.isFetching && !preflight.isError,
    preparationFailed: runHasFailed(preparationRun),
    preparationPaused: outcome === 'paused', preparationRunId: trackedPrepId,
    preparationIncomplete: isRunStateTerminal(preparationRun) && outcome === 'pending',
  }
}
