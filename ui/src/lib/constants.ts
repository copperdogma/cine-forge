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
  editorial_direction: ['editorial direction', 'editorial directions'],
  editorial_direction_index: ['editorial index', 'editorial indexes'],
}

/** Skip internal artifact types the user doesn't care about. */
export const SKIP_TYPES = new Set(['raw_input', 'project_config', 'scene_index', 'entity_discovery_results'])

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
