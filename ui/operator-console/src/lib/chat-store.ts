// Zustand store for chat messages, persisted to localStorage.

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChatMessage } from './types'

interface ChatStore {
  messages: Record<string, ChatMessage[]>
  addMessage: (projectId: string, message: ChatMessage) => void
  getMessages: (projectId: string) => ChatMessage[]
  clearMessages: (projectId: string) => void
  hasMessages: (projectId: string) => boolean
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      messages: {},

      addMessage: (projectId, message) =>
        set((state) => ({
          messages: {
            ...state.messages,
            [projectId]: [...(state.messages[projectId] ?? []), message],
          },
        })),

      getMessages: (projectId) => get().messages[projectId] ?? [],

      clearMessages: (projectId) =>
        set((state) => {
          const { [projectId]: _, ...rest } = state.messages
          return { messages: rest }
        }),

      hasMessages: (projectId) => (get().messages[projectId]?.length ?? 0) > 0,
    }),
    {
      name: 'cineforge-chat',
    },
  ),
)
