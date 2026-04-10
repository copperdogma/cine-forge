import { useChatStore } from '@/lib/chat-store'
import { getRunActivityLabel, getRunStartedMessage } from '@/lib/constants'
import type { RunStartPayload } from '@/lib/types'

interface StartTrackedRunOptions {
  projectId: string
  payload: RunStartPayload
  actionLabel: string
  resolvedMessageId?: string
  startRun: (payload: RunStartPayload) => Promise<{ run_id: string }>
}

export async function startTrackedRun({
  projectId,
  payload,
  actionLabel,
  resolvedMessageId,
  startRun,
}: StartTrackedRunOptions): Promise<{ run_id: string }> {
  const store = useChatStore.getState()

  store.addMessage(projectId, {
    id: `action_${Date.now()}`,
    type: 'user_action',
    content: actionLabel,
    timestamp: Date.now(),
    resolvedMessageId,
  })

  const result = await startRun(payload)

  store.setActiveRun(projectId, result.run_id)
  store.addMessage(projectId, {
    id: `run_started_${result.run_id}`,
    type: 'ai_status',
    content: getRunStartedMessage(payload.recipe_id),
    timestamp: Date.now(),
    actions: [
      { id: 'view_run_details', label: 'View Run Details', variant: 'outline', route: `runs/${result.run_id}` },
    ],
  })
  store.addActivity(projectId, getRunActivityLabel(payload.recipe_id), `runs/${result.run_id}`)

  return result
}
