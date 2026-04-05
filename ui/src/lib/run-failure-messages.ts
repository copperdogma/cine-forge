import type { ChatMessage } from './types'

const GENERIC_RUN_FAILURE_PREFIX = 'progress_'
const GENERIC_RUN_FAILURE_SUFFIX = '_failed'

export function genericRunFailureMessageId(runId: string): string {
  return `${GENERIC_RUN_FAILURE_PREFIX}${runId}${GENERIC_RUN_FAILURE_SUFFIX}`
}

export function hasProviderFailureMessage(
  messages: ChatMessage[],
  runId: string,
): boolean {
  const providerFailurePrefix = `provider_failure_${runId}_`
  return messages.some((message) => message.id.startsWith(providerFailurePrefix))
}

export function dropShadowedGenericRunFailureMessages(
  messages: ChatMessage[],
): ChatMessage[] {
  return messages.filter((message) => {
    const runId = runIdFromGenericFailureMessageId(message.id)
    if (!runId) return true
    return !hasProviderFailureMessage(messages, runId)
  })
}

export function dropResolvedGenericRunFailureMessages(
  messages: ChatMessage[],
  resolvedRunIds: ReadonlySet<string>,
): ChatMessage[] {
  return messages.filter((message) => {
    const runId = runIdFromGenericFailureMessageId(message.id)
    return !runId || !resolvedRunIds.has(runId)
  })
}

function runIdFromGenericFailureMessageId(messageId: string): string | null {
  if (!messageId.startsWith(GENERIC_RUN_FAILURE_PREFIX)) return null
  if (!messageId.endsWith(GENERIC_RUN_FAILURE_SUFFIX)) return null
  return messageId.slice(
    GENERIC_RUN_FAILURE_PREFIX.length,
    -GENERIC_RUN_FAILURE_SUFFIX.length,
  )
}
