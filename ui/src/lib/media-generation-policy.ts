import type { MediaExecutionPlanResponse, MediaRecipeId } from './media-generation-types'
import type { ArtifactGroupSummary, RunStateResponse, SceneActionPreflight } from './types'

export function mediaSelectionKey(selection: string[] | null): string {
  return selection === null ? 'all' : JSON.stringify([...selection].sort())
}

export function canPrepareMedia(preflight: SceneActionPreflight | null | undefined): boolean {
  return !!preflight && preflight.end_at === 'render_clip_planning' && preflight.status !== 'soft_block'
}

export function canConfirmMedia(options: {
  inspection?: MediaExecutionPlanResponse
  projectId: string
  sceneId: string
  recipeId: MediaRecipeId
  currentKey: string
  inspectedKey: string | null
  busy: boolean
  rejected: boolean
  generationPreflight?: SceneActionPreflight
  availabilityBusy?: boolean
}): boolean {
  const { inspection, projectId, sceneId, recipeId, currentKey, inspectedKey, busy, rejected, generationPreflight, availabilityBusy } = options
  return !busy && !availabilityBusy && !rejected && currentKey === inspectedKey
    && !!generationPreflight && generationPreflight.status !== 'soft_block'
    && generationPreflight.recipe_id === recipeId && !generationPreflight.end_at
    && generationPreflight.scene_scope.mode === 'current_scene'
    && generationPreflight.scene_scope.scene_ids.length === 1
    && generationPreflight.scene_scope.scene_ids[0] === sceneId
    && !!inspection && inspection.plan.status === 'ready'
    && inspection.plan.blockers.length === 0 && inspection.plan.units.length > 0
    && inspection.plan.project_id === projectId && inspection.plan.scene_id === sceneId
    && inspection.plan.recipe_id === recipeId
}

export function selectedMediaClipIds(selection: string[] | null, allClipIds: string[], clipId: string): string[] {
  const selected = selection ?? allClipIds
  return selected.includes(clipId) ? selected.filter(id => id !== clipId) : [...selected, clipId]
}

export function mediaSourceKey(project: unknown, groups: ArtifactGroupSummary[] | undefined): string {
  return JSON.stringify({ project, groups: groups?.filter(group =>
    group.artifact_type !== 'media_execution_plan',
  ) })
}

export type MediaPreparationOutcome = 'pending' | 'paused' | 'failed' | 'complete' | 'existing'

export function mediaPreparationOutcome(run: RunStateResponse | null | undefined, hasExistingClipPlan = false): MediaPreparationOutcome {
  if (!run) return 'pending'
  const state = run.state
  const selected = state.stage_order ?? []
  const stages = selected.map(id => state.stages[id])
  if (run.background_error || stages.some(stage => stage?.status === 'failed')) return 'failed'
  if (stages.some(stage => stage?.status === 'paused')) return 'paused'
  if (state.finished_at == null) return 'pending'
  if (selected.length === 0 && hasExistingClipPlan && state.runtime_params.end_at === 'render_clip_planning') return 'existing'
  if (!selected.includes('render_clip_planning')) return 'pending'
  return stages.length > 0 && stages.every(stage => stage?.status === 'done' || stage?.status === 'skipped_reused')
    ? 'complete' : 'pending'
}

export function canReuseMediaPreparation(preflight: SceneActionPreflight | null | undefined, hasExistingClipPlan: boolean): boolean {
  return hasExistingClipPlan && canPrepareMedia(preflight)
    && ['render', 'ai_previz', 'media_validation'].includes(preflight?.start_from ?? '')
}
