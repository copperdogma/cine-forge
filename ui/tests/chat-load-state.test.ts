import assert from 'node:assert/strict'
import test from 'node:test'
import {
  DEFAULT_CHAT_LOAD_STATE,
  resolveChatLoadErrorMessage,
  shouldAttemptChatLoad,
  shouldAutoSyncChat,
} from '../src/lib/chat-load-state.ts'

test('idle chat state allows a single automatic load attempt', () => {
  assert.equal(shouldAttemptChatLoad(DEFAULT_CHAT_LOAD_STATE), true)
})

test('error chat state blocks automatic reload and sync retries', () => {
  const errorState = { phase: 'error' as const, error: 'backend unavailable' }

  assert.equal(shouldAttemptChatLoad(errorState), false)
  assert.equal(shouldAutoSyncChat(errorState), false)
})

test('loading and ready states do not re-arm background fetching', () => {
  assert.equal(shouldAttemptChatLoad({ phase: 'loading', error: null }), false)
  assert.equal(shouldAttemptChatLoad({ phase: 'ready', error: null }), false)
})

test('error messages stay operator-visible', () => {
  assert.equal(resolveChatLoadErrorMessage(new Error('Request failed (503)')), 'Request failed (503)')
  assert.equal(resolveChatLoadErrorMessage(null), 'Chat is temporarily unavailable.')
})
