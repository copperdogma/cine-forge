import assert from 'node:assert/strict'
import test from 'node:test'
import { getSceneWorkflowGuide } from '../src/lib/scene-workflow.ts'

test('concern-group tabs point users to shot planning first when no downstream scene work exists', () => {
  const guide = getSceneWorkflowGuide({
    activeTab: 'look_and_feel',
    hasShotPlan: false,
    hasStoryboard: false,
    hasRender: false,
  })

  assert.equal(guide.stepId, 'shots')
  assert.equal(guide.stepNumber, 1)
  assert.equal(guide.actionKind, 'route')
  assert.equal(guide.targetTab, 'shots')
  assert.match(guide.hint, /shot plan/i)
})

test('shot-planning tabs advance to storyboard once a shot plan exists', () => {
  const guide = getSceneWorkflowGuide({
    activeTab: 'shots',
    hasShotPlan: true,
    hasStoryboard: false,
    hasRender: false,
  })

  assert.equal(guide.stepId, 'storyboard')
  assert.equal(guide.stepNumber, 2)
  assert.equal(guide.actionKind, 'route')
  assert.equal(guide.targetTab, 'storyboard')
  assert.match(guide.description, /render/i)
})

test('render becomes the final recommended step after storyboard generation', () => {
  const guide = getSceneWorkflowGuide({
    activeTab: 'storyboard',
    hasShotPlan: true,
    hasStoryboard: true,
    hasRender: false,
  })

  assert.equal(guide.stepId, 'render')
  assert.equal(guide.stepNumber, 3)
  assert.equal(guide.actionKind, 'route')
  assert.equal(guide.targetTab, 'render')
  assert.match(guide.description, /final scene video/i)
})

test('render tab flips to a terminal state once a scene video exists', () => {
  const guide = getSceneWorkflowGuide({
    activeTab: 'render',
    hasShotPlan: true,
    hasStoryboard: true,
    hasRender: true,
  })

  assert.equal(guide.stepId, 'done')
  assert.equal(guide.actionKind, 'none')
  assert.match(guide.description, /full render/i)
})
