import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
import { canConfirmMedia, canPrepareMedia, mediaSelectionKey, mediaSourceKey, selectedMediaClipIds, mediaPreparationOutcome, canReuseMediaPreparation } from '../src/lib/media-generation-policy.ts'
import type { MediaExecutionPlanResponse } from '../src/lib/media-generation-types.ts'
import type { RunStateResponse, SceneActionPreflight } from '../src/lib/types.ts'

const inspection: MediaExecutionPlanResponse = {
  plan_ref: { artifact_type: 'media_execution_plan', entity_id: 'scene_001', version: 1, path: 'artifacts/plan.json' },
  plan: { project_id: 'film', recipe_id: 'render_generation', scene_id: 'scene_001', render_clip_ids: null,
    binding_sha256: 'binding', status: 'ready', blockers: [], video_estimate_usd: 1.2,
    total_estimate_usd: null, excluded_costs: ['Prompt compilation'], source_bindings: [],
    units: [{ entity_id: 'scene_001_clip_001', clip_id: 'clip_001', title: 'Clip 1',
      planned_duration_seconds: 5, duration_seconds: 8, resolution: '720p', aspect_ratio: '16:9',
      provider: 'provider', model: 'configured-model', video_estimate_usd: 1.2, price: null }],
  },
}
const generationPreflight: SceneActionPreflight = { recipe_id: 'render_generation', recipe_name: 'Render',
  scene_scope: { mode: 'current_scene', scene_ids: ['scene_001'] }, status: 'ready', summary: 'Ready', items: [] }
const options = { generationPreflight, inspection, projectId: 'film', sceneId: 'scene_001', recipeId: 'render_generation' as const,
  currentKey: 'current:all', inspectedKey: 'current:all', busy: false, rejected: false }

test('only current, ready, nonempty inspected work may be confirmed', () => {
  assert.equal(canConfirmMedia(options), true)
  for (const change of [{ inspection: undefined }, { currentKey: 'changed:all' },
    { currentKey: 'current:clip_002' }, { inspectedKey: null }, { busy: true }, { rejected: true },
    { generationPreflight: undefined }, { availabilityBusy: true },
    { generationPreflight: { ...generationPreflight, status: 'soft_block' as const } },
    { generationPreflight: { ...generationPreflight, end_at: 'render_clip_planning' } },
    { generationPreflight: { ...generationPreflight, scene_scope: { mode: 'current_scene' as const, scene_ids: ['scene_002'] } } },
    { projectId: 'other' }, { sceneId: 'scene_002' }, { recipeId: 'ai_previz_generation' as const }]) {
    assert.equal(canConfirmMedia({ ...options, ...change }), false)
  }
  assert.equal(canConfirmMedia({ ...options, inspection: { ...inspection, plan: { ...inspection.plan, status: 'blocked' } } }), false)
  assert.equal(canConfirmMedia({ ...options, inspection: { ...inspection, plan: { ...inspection.plan, blockers: ['Retired target'] } } }), false)
  assert.equal(canConfirmMedia({ ...options, inspection: { ...inspection, plan: { ...inspection.plan, units: [] } } }), false)
})

test('preparation requires a loaded preflight authorizing the preparation boundary', () => {
  const preflight: SceneActionPreflight = { recipe_id: 'render_generation', recipe_name: 'Render',
    end_at: 'render_clip_planning', scene_scope: { mode: 'current_scene', scene_ids: ['scene_001'] },
    status: 'warn', summary: 'Preparation may use text AI', items: [] }
  assert.equal(canPrepareMedia(undefined), false)
  assert.equal(canPrepareMedia(preflight), true)
  assert.equal(canPrepareMedia({ ...preflight, end_at: null }), false)
  assert.equal(canPrepareMedia({ ...preflight, status: 'soft_block' }), false)
})

test('selecting clips changes inspection identity without treating empty selection as all', () => {
  assert.deepEqual(selectedMediaClipIds(null, ['one', 'two'], 'one'), ['two'])
  assert.deepEqual(selectedMediaClipIds(['one'], ['one', 'two'], 'one'), [])
  assert.notEqual(mediaSelectionKey([]), mediaSelectionKey(null))
  assert.equal(mediaSelectionKey(['two', 'one']), mediaSelectionKey(['one', 'two']))
})

test('upstream and project changes invalidate inspection; writing inspection artifacts does not', () => {
  const group = { artifact_type: 'render_clip_plan', entity_id: 'scene_001', latest_version: 1, health: null }
  const key = mediaSourceKey({ default_model: 'first' }, [group])
  assert.notEqual(key, mediaSourceKey({ default_model: 'second' }, [group]))
  assert.notEqual(key, mediaSourceKey({ default_model: 'first' }, [{ ...group, latest_version: 2 }]))
  assert.equal(key, mediaSourceKey({ default_model: 'first' }, [group, { ...group, artifact_type: 'media_execution_plan' }]))
})

test('both normal panels route clip actions into review and provide no direct paid start', () => {
  for (const panel of ['GeneratedVideoPanel', 'PrevizPanel']) {
    const source = readFileSync(new URL(`../src/components/${panel}.tsx`, import.meta.url), 'utf8')
    assert.match(source, /<MediaGenerationControls/)
    assert.match(source, /onRegenerateClip=\{clipId => controlsRef.current\?\.selectClip\(clipId\)\}/)
    assert.doesNotMatch(source, /mutateAsync|useStartRun|scene_scope:|All Scenes.*onClick/)
  }
})

test('paused and unfinished preparation never authorize success; cached selected work does', () => {
  const stage = (status: string) => ({ status, duration_seconds: 0, cost_usd: 0, artifact_refs: [] })
  const run: RunStateResponse = { run_id: 'prep', state: {
    run_id: 'prep', recipe_id: 'render_generation', finished_at: 100, total_cost_usd: 0,
    runtime_params: { end_at: 'render_clip_planning' }, stage_order: ['shot_planning', 'render_clip_planning'],
    stages: { shot_planning: stage('done'), render_clip_planning: stage('paused'), render: stage('pending') },
  } }
  assert.equal(mediaPreparationOutcome(run), 'paused', 'a finished timestamp is also present on a budget pause')
  run.state.stages.render_clip_planning = stage('pending')
  assert.equal(mediaPreparationOutcome(run), 'pending')
  run.state.stages.render_clip_planning = stage('done')
  assert.equal(mediaPreparationOutcome(run), 'complete', 'unselected downstream pending work is irrelevant')
  run.state.stages.shot_planning = stage('skipped_reused')
  run.state.stages.render_clip_planning = stage('skipped_reused')
  assert.equal(mediaPreparationOutcome(run), 'complete', 'existing-artifact no-op preparation succeeds')
  run.state.finished_at = null
  assert.equal(mediaPreparationOutcome(run), 'pending', 'stage completion alone is not terminal completion')
  run.state.finished_at = 100
  run.state.stage_order = []
  assert.equal(mediaPreparationOutcome(run), 'pending', 'an empty slice cannot establish preparation completion')
  assert.equal(mediaPreparationOutcome(run, true), 'existing', 'a no-op may inspect an existing plan without claiming new preparation completed')
  run.state.stages.shot_planning = stage('pending')
  run.state.stages.render_clip_planning = stage('pending')
  assert.equal(mediaPreparationOutcome(run, true), 'existing', 'the observed empty interval leaves all recipe stages pending')
  run.state.stage_order = ['shot_planning', 'render_clip_planning']
  delete run.state.stages.render_clip_planning
  assert.equal(mediaPreparationOutcome(run), 'pending', 'missing selected stage evidence is incomplete')
  run.state.stages.render_clip_planning = stage('failed')
  assert.equal(mediaPreparationOutcome(run), 'failed')
  assert.equal(mediaPreparationOutcome({ ...run, background_error: 'worker failed' }), 'failed')
})

test('current existing plans are inspected without queuing an empty preparation interval', () => {
  const preflight: SceneActionPreflight = { recipe_id: 'render_generation', recipe_name: 'Render',
    start_from: 'render', end_at: 'render_clip_planning', scene_scope: { mode: 'current_scene', scene_ids: ['scene_002'] },
    status: 'ready', summary: 'Ready', items: [] }
  assert.equal(canReuseMediaPreparation(preflight, true), true)
  assert.equal(canReuseMediaPreparation(preflight, false), false)
  assert.equal(canReuseMediaPreparation({ ...preflight, start_from: 'render_clip_planning' }, true), false)
  assert.equal(canReuseMediaPreparation({ ...preflight, status: 'soft_block' }, true), false)
})
