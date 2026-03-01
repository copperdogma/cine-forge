/** Human-readable names for recipes. */
export const RECIPE_NAMES: Record<string, string> = {
  mvp_ingest: 'Script Intake',
  world_building: 'World Building',
  narrative_analysis: 'Narrative Logic',
  creative_direction: 'Creative Direction',
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
}> = {
  rhythm_and_flow:           { label: 'Rhythm & Flow',           roleId: 'editorial_architect', roleName: 'Editorial Architect' },
  look_and_feel:             { label: 'Look & Feel',             roleId: 'visual_architect',    roleName: 'Visual Architect' },
  sound_and_music:           { label: 'Sound & Music',           roleId: 'sound_designer',      roleName: 'Sound Designer' },
  character_and_performance: { label: 'Character & Performance', roleId: 'story_editor',        roleName: 'Story Editor' },
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
): { label: string; roleId: string; roleName: string } | null {
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
  const ordered = stageOrder.filter(id => stageKeys.includes(id))
  const extras = stageKeys.filter(id => !stageOrder.includes(id))
  return [...ordered, ...extras]
}
