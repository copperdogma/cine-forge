import assert from 'node:assert/strict'
import test from 'node:test'
import {
  getRunCompletedMessage,
  getSceneWorkNextStepActions,
  getSceneWorkNextStepContent,
} from '../src/lib/constants.ts'

test('scene-work next step uses the scenes route as the default path', () => {
  assert.match(getSceneWorkNextStepContent(), /shot planning/i)
  assert.deepEqual(getSceneWorkNextStepActions(), [
    { id: 'scenes', label: 'Start Scene Work', variant: 'default', route: 'scenes' },
  ])
})

test('deep breakdown completion copy signals scene-work readiness', () => {
  assert.match(getRunCompletedMessage('world_building'), /scene work/i)
  assert.match(getRunCompletedMessage('world_building', '67 artifacts'), /scene work/i)
})
