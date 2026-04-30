import assert from 'node:assert/strict'
import test from 'node:test'
import {
  buildRelativeSceneWorkspaceRoute,
  buildSceneWorkspaceRoute,
  detectConcernGroupRun,
  getSceneProgressTotal,
  getSceneRunTargetLabel,
  getSingleSceneScopeId,
  getSceneWorkspaceTabForPhaseId,
  getSceneWorkspaceTabForRecipeId,
} from '../src/lib/constants.ts'

test('scene workspace routes omit the tab parameter for overview', () => {
  assert.equal(buildSceneWorkspaceRoute('project-123', 'scene_001'), '/project-123/scenes/scene_001')
  assert.equal(buildRelativeSceneWorkspaceRoute('scene_001'), 'scenes/scene_001')
})

test('scene workspace routes preserve explicit downstream tabs', () => {
  assert.equal(
    buildSceneWorkspaceRoute('project-123', 'scene_001', 'shots'),
    '/project-123/scenes/scene_001?tab=shots',
  )
  assert.equal(
    buildRelativeSceneWorkspaceRoute('scene_001', 'render'),
    'scenes/scene_001?tab=render',
  )
})

test('pipeline phases map to the expected scene workspace tabs', () => {
  assert.equal(getSceneWorkspaceTabForPhaseId('shots'), 'shots')
  assert.equal(getSceneWorkspaceTabForPhaseId('storyboards'), 'storyboard')
  assert.equal(getSceneWorkspaceTabForPhaseId('production'), 'render')
  assert.equal(getSceneWorkspaceTabForPhaseId('intent'), null)
})

test('recipe completions map to the expected scene workspace tabs', () => {
  assert.equal(getSceneWorkspaceTabForRecipeId('shot_planning'), 'shots')
  assert.equal(getSceneWorkspaceTabForRecipeId('storyboard_generation'), 'storyboard')
  assert.equal(getSceneWorkspaceTabForRecipeId('render_generation'), 'render')
  assert.equal(getSceneWorkspaceTabForRecipeId('world_building'), null)
})

test('single concern-group creative runs expose their matching scene workspace tab', () => {
  const run = detectConcernGroupRun('creative_direction', ['look_and_feel'])

  assert.deepEqual(run, {
    label: 'Look & Feel',
    roleId: 'visual_architect',
    roleName: 'Visual Architect',
    sceneWorkspaceTab: 'look_and_feel',
  })
})

test('single-scene run labels name the scene instead of showing batch progress', () => {
  const sceneScope = { mode: 'current_scene', scene_ids: ['scene_001'] }
  const sceneData = { heading: "EXT. BRICK'S PATIO - DAY" }

  assert.equal(getSingleSceneScopeId(sceneScope), 'scene_001')
  assert.equal(
    getSceneRunTargetLabel(sceneScope, sceneData),
    "SCENE 001: EXT. BRICK'S PATIO - DAY",
  )
  assert.equal(getSceneProgressTotal(sceneScope, 6), null)
})

test('multi-scene concern runs keep batch progress totals', () => {
  assert.equal(getSceneProgressTotal({ mode: 'all_scenes', scene_ids: [] }, 6), 6)
  assert.equal(
    getSceneProgressTotal({ mode: 'current_scene', scene_ids: ['scene_001', 'scene_002'] }, 6),
    2,
  )
})
