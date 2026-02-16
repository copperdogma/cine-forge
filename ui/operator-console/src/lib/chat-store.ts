// Zustand store for chat messages. Backend (JSONL) is the source of truth.
// Store is the in-memory view for rendering. Write-through on addMessage.

import { create } from 'zustand'
import { postChatMessage } from './api'
import type { ChatMessage, ChatMessageType } from './types'

/**
 * Migrate messages loaded from JSONL: resolve all ai_status spinners.
 * On a cold load there's no live polling, so any ai_status message represents
 * a past event. Convert them all to ai_status_done (static checkmark).
 */
function migrateMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages.map((m) =>
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
  /** Update the type of an existing message (in-memory only, no backend write). */
  updateMessageType: (projectId: string, messageId: string, newType: ChatMessageType) => void
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

      // Write-through to backend (fire-and-forget)
      postChatMessage(projectId, message).catch(() => {
        // Silently ignore — backend may be unreachable during dev
      })
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

    getMessages: (projectId) => get().messages[projectId] ?? [],

    clearMessages: (projectId) =>
      set((state) => {
        const { [projectId]: _, ...rest } = state.messages
        const { [projectId]: __, ...loadedRest } = state.loaded
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
