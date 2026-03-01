// Hook for long-running direct API calls (propagation, future AI ops).
// Automatically manages: button state, operation store, chat messages.
//
// For pipeline runs, use setActiveRun() instead — useRunProgressChat handles those.
// This hook is for non-pipeline operations that call an API and wait for a response.

import { useCallback, useRef } from 'react'
import { useOperationStore } from './operation-store'
import { useChatStore } from './chat-store'
import type { TaskProgressData } from '@/components/TaskProgressCard'

export interface ActionMeta {
  /** ID of the chat message the hook created (for custom updates in onSuccess). */
  chatMessageId: string
}

export interface LongRunningActionConfig<T> {
  /** Project this operation belongs to. */
  projectId: string
  /** Human-readable label shown in banner and chat (e.g. "Propagating creative intent"). */
  label: string
  /** Sub-items for multi-item progress. Omit for single-item operations. */
  items?: Array<{ label: string }>
  /** The async work to perform. */
  action: () => Promise<T>
  /**
   * Called after action succeeds and default chat updates are applied.
   * Use meta.chatMessageId to override the default "all done" with custom detail.
   */
  onSuccess?: (result: T, meta: ActionMeta) => void
  /** Called after action fails. Hook already shows error in chat. */
  onError?: (error: Error) => void
  /** Chat message speaker (defaults to 'director'). */
  speaker?: string
}

export function useLongRunningAction<T>(config: LongRunningActionConfig<T>) {
  const { projectId, label, items, action, onSuccess, onError, speaker = 'director' } = config

  const store = useOperationStore()
  const runningRef = useRef(false)

  const isRunning = useOperationStore(
    (s) => (s.operations[projectId] ?? []).some((o) => o.label === label && o.status === 'running'),
  )

  const start = useCallback(async () => {
    if (runningRef.current) return
    runningRef.current = true

    const opId = `${label.replace(/\s+/g, '_').toLowerCase()}_${Date.now()}`
    const chatMsgId = `op_${opId}`
    const chatStore = useChatStore.getState()

    // 1. Register operation in store (drives OperationBanner)
    store.addOperation(projectId, {
      id: opId,
      projectId,
      label,
      startedAt: Date.now(),
      status: 'running',
      progress: items ? { current: 0, total: items.length } : undefined,
      chatMessageId: chatMsgId,
    })

    // 2. Create chat message
    if (items && items.length > 0) {
      const data: TaskProgressData = {
        heading: label,
        items: items.map((i) => ({ label: i.label, status: 'running' as const })),
      }
      chatStore.addMessage(projectId, {
        id: chatMsgId,
        type: 'task_progress',
        content: JSON.stringify(data),
        timestamp: Date.now(),
        speaker,
      })
    } else {
      chatStore.addMessage(projectId, {
        id: chatMsgId,
        type: 'ai_status',
        content: `${label}...`,
        timestamp: Date.now(),
        speaker,
      })
    }

    // 3. Execute action
    try {
      const result = await action()

      // 4a. Success — update chat + store
      if (items && items.length > 0) {
        const doneData: TaskProgressData = {
          heading: label,
          items: items.map((i) => ({ label: i.label, status: 'done' as const })),
        }
        chatStore.updateMessageContent(projectId, chatMsgId, JSON.stringify(doneData))
      } else {
        chatStore.updateMessageType(projectId, chatMsgId, 'ai_status_done')
        chatStore.updateMessageContent(projectId, chatMsgId, `${label} — complete`)
      }

      store.completeOperation(projectId, opId)
      // Auto-remove after brief delay (lets banner show "done" flash)
      setTimeout(() => store.removeOperation(projectId, opId), 1500)

      onSuccess?.(result, { chatMessageId: chatMsgId })
    } catch (err) {
      // 4b. Failure — update chat + store
      const error = err instanceof Error ? err : new Error(String(err))

      if (items && items.length > 0) {
        const failData: TaskProgressData = {
          heading: label,
          items: items.map((i) => ({ label: i.label, status: 'failed' as const })),
        }
        chatStore.updateMessageContent(projectId, chatMsgId, JSON.stringify(failData))
      } else {
        chatStore.updateMessageType(projectId, chatMsgId, 'ai_status_done')
        chatStore.updateMessageContent(projectId, chatMsgId, `${label} — failed: ${error.message}`)
      }

      store.failOperation(projectId, opId)
      setTimeout(() => store.removeOperation(projectId, opId), 1500)

      onError?.(error)
    } finally {
      runningRef.current = false
    }
  }, [projectId, label, items, action, onSuccess, onError, speaker, store])

  return { isRunning, start }
}
