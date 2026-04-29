import assert from 'node:assert/strict'
import test from 'node:test'
import {
  RUN_PROGRESS_RECOVERY_MESSAGE,
  buildRunProgressRecoveryMessage,
  recoverRunProgressUiError,
} from '../src/lib/run-progress-recovery.ts'
import type { ChatMessage } from '../src/lib/types.ts'

test('run progress recovery message links to run details', () => {
  assert.deepEqual(buildRunProgressRecoveryMessage('run-123', 42), {
    id: 'progress_run-123_ui_recovered',
    type: 'ai_suggestion',
    content: RUN_PROGRESS_RECOVERY_MESSAGE,
    timestamp: 42,
    actions: [
      {
        id: 'view_run_detail',
        label: 'Run Details',
        variant: 'outline',
        route: 'runs/run-123',
      },
    ],
  })
})

test('run progress recovery reports once and clears the active run', () => {
  const messages: ChatMessage[] = []
  let clearedProject: string | null = null
  const logs: Array<[string, unknown]> = []

  const store = {
    getMessages: () => messages,
    addMessage: (_projectId: string, message: ChatMessage) => {
      messages.push(message)
    },
    clearActiveRun: (projectId: string) => {
      clearedProject = projectId
    },
  }

  recoverRunProgressUiError({
    projectId: 'project-a',
    runId: 'run-abc',
    error: new Error('bad terminal state'),
    store,
    log: (message, error) => logs.push([message, error]),
  })
  recoverRunProgressUiError({
    projectId: 'project-a',
    runId: 'run-abc',
    error: new Error('bad terminal state again'),
    store,
    log: (message, error) => logs.push([message, error]),
  })

  assert.equal(messages.length, 1)
  assert.equal(messages[0].id, 'progress_run-abc_ui_recovered')
  assert.equal(clearedProject, 'project-a')
  assert.equal(logs.length, 2)
})
