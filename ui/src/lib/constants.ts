/**
 * Canonical stage order per recipe. Unknown stages go at the end.
 * Used by RunProgressCard and ProjectRun pages to ensure consistent
 * sequential display of pipeline progress.
 */
export const RECIPE_STAGE_ORDER: Record<string, string[]> = {
  mvp_ingest: ['ingest', 'normalize', 'extract_scenes', 'project_config'],
  world_building: ['entity_discovery', 'character_bible', 'location_bible', 'prop_bible'],
  narrative_analysis: ['entity_graph', 'continuity_tracking'],
}

/** Human-readable names for recipes. */
export const RECIPE_NAMES: Record<string, string> = {
  mvp_ingest: 'Script Intake',
  world_building: 'World Building',
  narrative_analysis: 'Narrative Logic',
}

/** Human-readable names for artifact types produced by stages. */
export const ARTIFACT_NAMES: Record<string, [string, string]> = {
  scene: ['scene', 'scenes'],
  canonical_script: ['script', 'scripts'],
  character_bible: ['character', 'characters'],
  location_bible: ['location', 'locations'],
  prop_bible: ['prop', 'props'],
  scene_breakdown: ['scene breakdown', 'scene breakdowns'],
  entity_graph: ['story graph', 'story graphs'],
  world_overview: ['world overview', 'world overviews'],
  entity_discovery_results: ['entity discovery results', 'entity discovery results'],
}

/** Skip internal artifact types the user doesn't care about. */
export const SKIP_TYPES = new Set(['raw_input', 'project_config', 'scene_index', 'entity_discovery_results'])

/** Shared utility to sort stage IDs based on the canonical recipe order. */
export function getOrderedStageIds(recipeId: string, stageKeys: string[]): string[] {
  const knownOrder = RECIPE_STAGE_ORDER[recipeId]
  if (!knownOrder) return stageKeys
  const ordered = knownOrder.filter(id => stageKeys.includes(id))
  const extras = stageKeys.filter(id => !knownOrder.includes(id))
  return [...ordered, ...extras]
}
