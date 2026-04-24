/** Human-readable names for recipes. */
export const RECIPE_NAMES: Record<string, string> = {
  mvp_ingest: 'Script Intake',
  world_building: 'World Building',
  narrative_analysis: 'Narrative Logic',
  creative_direction: 'Creative Direction',
  shot_planning: 'Shot Planning',
  ai_previz_generation: 'AI Previz',
  render_generation: 'Scene Renders',
  final_output: 'Final Output',
}

/** Plain-language recipe names for operator-facing UI. */
export const USER_FACING_RECIPE_NAMES: Record<string, string> = {
  mvp_ingest: 'Script Breakdown',
  world_building: 'Deep Breakdown',
  narrative_analysis: 'Narrative Analysis',
  creative_direction: 'Creative Direction',
  shot_planning: 'Shot Planning',
  ai_previz_generation: 'AI Previz',
  render_generation: 'Scene Renders',
  final_output: 'Final Output',
}

const SCENE_WORK_NEXT_STEP_ACTION = {
  id: 'scenes',
  label: 'Start Scene Work',
  variant: 'default' as const,
  route: 'scenes',
}

export function getSceneWorkNextStepContent(): string {
  return 'Next: pick a scene and start with shot planning. Storyboards and generation build from there.'
}

export function getSceneWorkNextStepActions() {
  return [{ ...SCENE_WORK_NEXT_STEP_ACTION }]
}

export function buildSceneScope(mode: 'current_scene' | 'all_scenes', sceneId: string) {
  return {
    mode,
    scene_ids: mode === 'current_scene' ? [sceneId] : [],
  } as const
}

export function getSceneScopeLabel(sceneScope: unknown): string {
  if (
    sceneScope
    && typeof sceneScope === 'object'
    && 'mode' in sceneScope
    && (sceneScope as { mode?: unknown }).mode === 'current_scene'
  ) {
    const scopeWithIds = sceneScope as { scene_ids?: unknown }
    const ids = Array.isArray(scopeWithIds.scene_ids)
      ? scopeWithIds.scene_ids
      : []
    if (ids.length === 1 && typeof ids[0] === 'string') {
      return 'Current scene'
    }
    return 'Selected scenes'
  }
  return 'All scenes'
}

export function getSceneScopeTargetLabel(sceneScope: unknown): string {
  return getSceneScopeLabel(sceneScope) === 'Current scene' ? 'this scene' : 'all scenes'
}

export function getUserFacingRecipeName(recipeId: string | null | undefined): string {
  if (!recipeId) return 'Run'
  return USER_FACING_RECIPE_NAMES[recipeId] ?? RECIPE_NAMES[recipeId] ?? recipeId
}

export function getRunningRunLabel(recipeId: string | null | undefined): string {
  return `Running ${getUserFacingRecipeName(recipeId)}...`
}

export function getRunStartedMessage(recipeId: string | null | undefined): string {
  if (recipeId === 'world_building') {
    return 'Deep Breakdown started — building your story world now...'
  }
  if (recipeId === 'mvp_ingest') {
    return 'Script Breakdown started — processing your screenplay now...'
  }
  if (recipeId === 'creative_direction') {
    return 'Creative Direction started — generating scene direction now...'
  }
  if (recipeId === 'shot_planning') {
    return 'Shot Planning started — building scene shot lists now...'
  }
  if (recipeId === 'ai_previz_generation') {
    return 'AI Previz started — generating low-fidelity planning clips now...'
  }
  if (recipeId === 'render_generation') {
    return 'Scene Renders started — compiling prompts and generating scene video now...'
  }
  if (recipeId === 'final_output') {
    return 'Final Output started — assembling your project cut now...'
  }
  return 'Run started — processing your project now...'
}

export function getRunCompletedMessage(
  recipeId: string | null | undefined,
  summary?: string,
): string {
  if (recipeId === 'mvp_ingest') {
    return summary
      ? `Script Breakdown complete! I found ${summary} in your screenplay.`
      : 'Script Breakdown complete!'
  }
  if (recipeId === 'world_building') {
    return summary
      ? `Deep Breakdown complete! I built ${summary} for your project. You're ready to move into scene work.`
      : 'Deep Breakdown complete! Your story world is ready for scene work.'
  }
  if (recipeId === 'ai_previz_generation') {
    return summary
      ? `AI Previz complete! I produced ${summary} for your project.`
      : 'AI Previz complete!'
  }
  if (recipeId === 'render_generation') {
    return summary
      ? `Scene Renders complete! I produced ${summary} for your project.`
      : 'Scene Renders complete!'
  }
  if (recipeId === 'final_output') {
    return summary
      ? `Final Output complete! I assembled ${summary} for your project.`
      : 'Final Output complete!'
  }
  return summary
    ? `Run complete! I produced ${summary} for your project.`
    : 'Run complete!'
}

export function getRunActivityLabel(recipeId: string | null | undefined): string {
  return recipeId ? `Started ${getUserFacingRecipeName(recipeId)}` : 'Started pipeline run'
}

export type SceneWorkspaceTab =
  | 'overview'
  | 'look_and_feel'
  | 'sound_and_music'
  | 'rhythm_and_flow'
  | 'character_and_performance'
  | 'story_world'
  | 'shots'
  | 'storyboard'
  | 'previz'
  | 'render'

export const SCENE_WORKSPACE_TAB_IDS: readonly SceneWorkspaceTab[] = [
  'overview',
  'look_and_feel',
  'sound_and_music',
  'rhythm_and_flow',
  'character_and_performance',
  'story_world',
  'shots',
  'storyboard',
  'previz',
  'render',
] as const

const SCENE_WORKSPACE_PHASE_TABS: Record<string, SceneWorkspaceTab> = {
  shots: 'shots',
  storyboards: 'storyboard',
  production: 'render',
}

const SCENE_WORKSPACE_RECIPE_TABS: Record<string, SceneWorkspaceTab> = {
  shot_planning: 'shots',
  storyboard_generation: 'storyboard',
  ai_previz_generation: 'previz',
  render_generation: 'render',
}

export function buildSceneWorkspaceRoute(
  projectId: string,
  sceneId: string,
  tab: SceneWorkspaceTab | null | undefined = null,
): string {
  const baseRoute = `/${projectId}/scenes/${sceneId}`
  return tab && tab !== 'overview' ? `${baseRoute}?tab=${tab}` : baseRoute
}

export function buildRelativeSceneWorkspaceRoute(
  sceneId: string,
  tab: SceneWorkspaceTab | null | undefined = null,
): string {
  const baseRoute = `scenes/${sceneId}`
  return tab && tab !== 'overview' ? `${baseRoute}?tab=${tab}` : baseRoute
}

export function getSceneWorkspaceTabForPhaseId(phaseId: string): SceneWorkspaceTab | null {
  return SCENE_WORKSPACE_PHASE_TABS[phaseId] ?? null
}

export function getSceneWorkspaceTabForRecipeId(recipeId: string): SceneWorkspaceTab | null {
  return SCENE_WORKSPACE_RECIPE_TABS[recipeId] ?? null
}

/** Human-readable names for artifact types produced by stages. */
export const ARTIFACT_NAMES: Record<string, [string, string]> = {
  scene: ['scene', 'scenes'],
  canonical_script: ['script', 'scripts'],
  character_bible: ['character', 'characters'],
  location_bible: ['location', 'locations'],
  prop_bible: ['prop', 'props'],
  scene_breakdown: ['scene breakdown', 'scene breakdowns'],
  script_bible: ['script bible', 'script bibles'],
  entity_graph: ['story graph', 'story graphs'],
  world_overview: ['world overview', 'world overviews'],
  entity_discovery_results: ['entity discovery results', 'entity discovery results'],
  intent_mood: ['intent & mood', 'intent & mood'],
  rhythm_and_flow: ['rhythm & flow', 'rhythm & flow'],
  rhythm_and_flow_index: ['rhythm & flow index', 'rhythm & flow indexes'],
  look_and_feel: ['look & feel', 'look & feel'],
  sound_and_music: ['sound & music', 'sound & music'],
  character_and_performance: ['character & performance', 'character & performance'],
  story_world: ['story world', 'story world'],
  shot_plan: ['shot plan', 'shot plans'],
  storyboard: ['storyboard', 'storyboards'],
  ai_previz_prompt: ['ai previz prompt', 'ai previz prompts'],
  ai_previz_video: ['ai previz clip', 'ai previz clips'],
  keyframe: ['keyframe set', 'keyframe sets'],
  render_prompt: ['render prompt', 'render prompts'],
  generated_video: ['generated video', 'generated videos'],
  final_output: ['final output cut', 'final output cuts'],
  media_validation: ['media validation', 'media validation reports'],
}

/**
 * Concern group → role mapping for chat attribution.
 *
 * When a single concern group stage runs (via start_from/end_at on creative_direction),
 * use this to attribute chat messages to the correct creative role.
 * UI-specific configs (icon, color, badge) live in DirectionAnnotation.tsx and DirectionTab.tsx;
 * this is the minimal shared mapping for chat message attribution.
 */
export const CONCERN_GROUP_META: Record<string, {
  label: string       // "Rhythm & Flow"
  roleId: string      // "editorial_architect"
  roleName: string    // "Editorial Architect"
  sceneWorkspaceTab: SceneWorkspaceTab
}> = {
  rhythm_and_flow:           { label: 'Rhythm & Flow',           roleId: 'editorial_architect', roleName: 'Editorial Architect', sceneWorkspaceTab: 'rhythm_and_flow' },
  look_and_feel:             { label: 'Look & Feel',             roleId: 'visual_architect',    roleName: 'Visual Architect', sceneWorkspaceTab: 'look_and_feel' },
  sound_and_music:           { label: 'Sound & Music',           roleId: 'sound_designer',      roleName: 'Sound Designer', sceneWorkspaceTab: 'sound_and_music' },
  character_and_performance: { label: 'Character & Performance', roleId: 'story_editor',        roleName: 'Story Editor', sceneWorkspaceTab: 'character_and_performance' },
}

/**
 * Detect if a run is a single-concern-group creative direction run.
 * Returns the concern group meta if so, null otherwise.
 *
 * Usage: `detectConcernGroupRun(runState.state.recipe_id, stageOrder)`
 */
export function detectConcernGroupRun(
  recipeId: string,
  stageOrder: string[],
): { label: string; roleId: string; roleName: string; sceneWorkspaceTab: SceneWorkspaceTab } | null {
  if (recipeId !== 'creative_direction' || stageOrder.length !== 1) return null
  return CONCERN_GROUP_META[stageOrder[0]] ?? null
}

/** Skip internal artifact types the user doesn't care about. */
export const SKIP_TYPES = new Set(['raw_input', 'project_config', 'scene_index', 'entity_discovery_results'])

/**
 * Count scene-scoped artifacts already saved for a concern group stage.
 * Counts artifact_refs whose entity_id starts with "scene_" and whose
 * artifact_type matches the stage ID (e.g. "sound_and_music").
 */
export function countSceneProgress(stage: { artifact_refs: Array<Record<string, unknown>> }, stageId: string): number {
  return stage.artifact_refs.filter(
    (r) => String(r.entity_id ?? '').startsWith('scene_') && r.artifact_type === stageId,
  ).length
}

/**
 * Get total scene count from cached artifact groups.
 * Counts entries with artifact_type === 'scene'.
 */
export function countTotalScenes(groups: Array<{ artifact_type: string }> | undefined): number {
  if (!groups) return 0
  return groups.filter((g) => g.artifact_type === 'scene').length
}

/**
 * Return stage IDs in display order. Uses the explicit stage_order from
 * the run state (set by the backend from the recipe's declared order).
 * Falls back to stageKeys as-is if no order provided.
 */
export function getOrderedStageIds(stageKeys: string[], stageOrder?: string[]): string[] {
  if (!stageOrder || stageOrder.length === 0) return stageKeys
  return stageOrder.filter(id => stageKeys.includes(id))
}
