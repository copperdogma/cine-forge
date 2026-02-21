// Zustand store for chat messages. Backend (JSONL) is the source of truth.
// Store is the in-memory view for rendering. Write-through on addMessage.

import { create } from 'zustand'
import { postChatMessage } from './api'
import type { ChatAction, ChatMessage, ChatMessageType, ToolCallStatus } from './types'

/**
 * Migrate messages loaded from JSONL: resolve all ai_status spinners.
 * On a cold load there's no live polling, so any ai_status message represents
 * a past event. Convert them all to ai_status_done (static checkmark).
 */
function migrateMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages
    .filter((m) => m.type !== 'ai_tool_status') // Remove legacy separate tool messages
    .map((m) =>
      m.type === 'ai_status' ? { ...m, type: 'ai_status_done' as const } : m,
    )
}

interface ChatStore {
  messages: Record<string, ChatMessage[]>
  /** Tracks which projects have been loaded from the backend. */
  loaded: Record<string, boolean>
  activeRunId: Record<string, string | null>

  /** Bulk-load messages from backend (replaces any in-memory state for the project). */
  loadMessages: (projectId: string, messages: ChatMessage[]) => void
  /** Add a message to store and persist to backend (fire-and-forget). */
  addMessage: (projectId: string, message: ChatMessage) => void
  /** Post a compact activity note to the chat timeline. */
  addActivity: (projectId: string, content: string, route?: string) => void
  /** Update the type of an existing message (in-memory only, no backend write). */
  updateMessageType: (projectId: string, messageId: string, newType: ChatMessageType) => void
  /** Update the content of an existing message (in-memory only — for streaming). */
  updateMessageContent: (projectId: string, messageId: string, content: string) => void
  /** Attach actions to an existing message (in-memory only — for proposal buttons). */
  attachActions: (projectId: string, messageId: string, actions: ChatAction[]) => void
  /** Add a tool call to an existing AI message (in-memory only — for inline tool indicators). */
  addToolCall: (projectId: string, messageId: string, tool: ToolCallStatus) => void
  /** Mark a tool call as complete on an existing AI message (in-memory only). */
  completeToolCall: (projectId: string, messageId: string, toolId: string) => void
  /** Finalize a streaming message: remove streaming flag, persist to backend. */
  finalizeStreamingMessage: (projectId: string, messageId: string) => void
  getMessages: (projectId: string) => ChatMessage[]
  clearMessages: (projectId: string) => void
  hasMessages: (projectId: string) => boolean
  isLoaded: (projectId: string) => boolean
  setActiveRun: (projectId: string, runId: string) => void
  clearActiveRun: (projectId: string) => void
}

export const useChatStore = create<ChatStore>()(
  (set, get) => ({
    messages: {},
    loaded: {},
    activeRunId: {},

    loadMessages: (projectId, messages) =>
      set((state) => ({
        messages: { ...state.messages, [projectId]: migrateMessages(messages) },
        loaded: { ...state.loaded, [projectId]: true },
      })),

    addMessage: (projectId, message) => {
      set((state) => {
        const existing = state.messages[projectId] ?? []
        // Idempotent: skip if message ID already exists
        if (existing.some(m => m.id === message.id)) return state
        return {
          messages: {
            ...state.messages,
            [projectId]: [...existing, message],
          },
        }
      })

      // Don't persist streaming placeholders — they'll be saved when finalized
      if (message.streaming) return

      // Write-through to backend (fire-and-forget)
      postChatMessage(projectId, message).catch(() => {
        // Silently ignore — backend may be unreachable during dev
      })
    },

    addActivity: (projectId, content, route) => {
      const state = get()
      const existing = state.messages[projectId] ?? []
      const lastMsg = existing[existing.length - 1]

      const message: ChatMessage = {
        id: `activity_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        type: 'activity',
        content,
        timestamp: Date.now(),
        route,
      }

      if (lastMsg?.type === 'activity') {
        // Replace last activity message instead of appending to avoid navigation spam
        set((state) => {
          const updated = [...(state.messages[projectId] ?? [])]
          updated[updated.length - 1] = message
          return { messages: { ...state.messages, [projectId]: updated } }
        })
        // Note: We don't explicitly persist deletions to the backend JSONL yet, 
        // but new additions are persisted. Replacing in-memory keeps the UI clean.
        postChatMessage(projectId, message).catch(() => {})
      } else {
        get().addMessage(projectId, message)
      }
    },

    updateMessageType: (projectId, messageId, newType) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1 || msgs[idx].type === newType) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], type: newType }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    updateMessageContent: (projectId, messageId, content) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], content }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    attachActions: (projectId, messageId, actions) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], actions, needsAction: true }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    addToolCall: (projectId, messageId, tool) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        const existing = updated[idx].toolCalls ?? []
        updated[idx] = { ...updated[idx], toolCalls: [...existing, tool] }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    completeToolCall: (projectId, messageId, toolId) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        const tools = updated[idx].toolCalls?.map(t =>
          t.id === toolId ? { ...t, done: true } : t,
        )
        updated[idx] = { ...updated[idx], toolCalls: tools }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    finalizeStreamingMessage: (projectId, messageId) => {
      const msgs = get().messages[projectId]
      if (!msgs) return
      const msg = msgs.find(m => m.id === messageId)
      if (!msg) return
      // Mark all tools as done and remove streaming flag
      const finalTools = msg.toolCalls?.map(t => ({ ...t, done: true }))
      const finalized = { ...msg, streaming: undefined, toolCalls: finalTools }
      set((state) => {
        const updated = (state.messages[projectId] ?? []).map(m =>
          m.id === messageId ? finalized : m,
        )
        return { messages: { ...state.messages, [projectId]: updated } }
      })
      // Persist to backend — streaming placeholder was never saved, so this
      // is the first write for this message ID
      const { ...persistable } = finalized
      // Remove runtime-only field toolCalls from persistence if present
      delete (persistable as any).toolCalls
      postChatMessage(projectId, persistable as any).catch(() => {})
    },

    getMessages: (projectId) => get().messages[projectId] ?? [],

    clearMessages: (projectId) =>
      set((state) => {
        const { [projectId]: _discardedMessages, ...rest } = state.messages
        const { [projectId]: _discardedLoaded, ...loadedRest } = state.loaded
        return { messages: rest, loaded: loadedRest }
      }),

    hasMessages: (projectId) => (get().messages[projectId]?.length ?? 0) > 0,

    isLoaded: (projectId) => get().loaded[projectId] === true,

    setActiveRun: (projectId, runId) =>
      set((state) => ({
        activeRunId: { ...state.activeRunId, [projectId]: runId },
      })),

    clearActiveRun: (projectId) =>
      set((state) => ({
        activeRunId: { ...state.activeRunId, [projectId]: null },
      })),
  }),
)
