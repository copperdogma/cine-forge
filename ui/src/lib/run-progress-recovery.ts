import type { ChatMessage } from './types'

export type RunProgressRecoveryStore = {
  getMessages: (projectId: string) => ChatMessage[]
  addMessage: (projectId: string, message: ChatMessage) => void
  clearActiveRun: (projectId: string) => void
}

export const RUN_PROGRESS_RECOVERY_MESSAGE =
  'The run finished, but the progress panel hit a UI error while updating the chat. Your project is still available; open Run Details to inspect the run.'

export function buildRunProgressRecoveryMessage(
  runId: string,
  timestamp: number = Date.now(),
): ChatMessage {
  return {
    id: `progress_${runId}_ui_recovered`,
    type: 'ai_suggestion',
    content: RUN_PROGRESS_RECOVERY_MESSAGE,
    timestamp,
    actions: [
      {
        id: 'view_run_detail',
        label: 'Run Details',
        variant: 'outline',
        route: `runs/${runId}`,
      },
    ],
  }
}

export function recoverRunProgressUiError({
  projectId,
  runId,
  error,
  store,
  log = console.error,
}: {
  projectId: string
  runId: string
  error: unknown
  store: RunProgressRecoveryStore
  log?: (message: string, error: unknown) => void
}) {
  log('Run progress UI update failed', error)

  const recoveryMessage = buildRunProgressRecoveryMessage(runId)
  const alreadyReported = store
    .getMessages(projectId)
    .some((message) => message.id === recoveryMessage.id)

  if (!alreadyReported) {
    store.addMessage(projectId, recoveryMessage)
  }

  store.clearActiveRun(projectId)
}
