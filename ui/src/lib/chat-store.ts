// Zustand store for chat messages. Backend (JSONL) is the source of truth.
// Store is the in-memory view for rendering. Write-through on addMessage.

import { create } from 'zustand'
import { postChatMessage, getChatMessages } from './api'
import type { ChatAction, ChatMessage, ChatMessageType, PreflightData, ToolCallStatus } from './types'

/** AI message types that should have an explicit speaker. */
const AI_MESSAGE_TYPES: ReadonlySet<string> = new Set([
  'ai_response', 'ai_welcome', 'ai_suggestion',
])

/**
 * Migrate messages loaded from JSONL: resolve all ai_status spinners,
 * backfill speaker on AI messages, and deduplicate activity notes.
 */
/** Resolve stale task_progress items: running → done on reload. */
function resolveTaskProgress(msg: ChatMessage): ChatMessage {
  if (msg.type !== 'task_progress') return msg
  try {
    const data = JSON.parse(msg.content)
    if (!Array.isArray(data?.items)) return msg
    const hasStale = data.items.some(
      (i: { status: string }) => i.status === 'running' || i.status === 'pending',
    )
    if (!hasStale) return msg
    const resolved = {
      ...data,
      items: data.items.map((i: { status: string }) =>
        i.status === 'running' || i.status === 'pending'
          ? { ...i, status: 'done' }
          : i,
      ),
    }
    return { ...msg, content: JSON.stringify(resolved) }
  } catch {
    return msg
  }
}

function migrateMessages(messages: ChatMessage[]): ChatMessage[] {
  const migrated = messages
    .filter((m) => m.type !== 'ai_tool_status') // Remove legacy separate tool messages
    .map((m) => {
      let msg = m.type === 'ai_status' ? { ...m, type: 'ai_status_done' as const } : m
      // Resolve stale task_progress spinners from previous sessions
      msg = resolveTaskProgress(msg)
      // Backfill speaker on AI messages that predate the group chat architecture
      if (AI_MESSAGE_TYPES.has(msg.type) && !msg.speaker) {
        msg = { ...msg, speaker: 'assistant' }
      }
      return msg
    })

  // Deduplicate activity messages: keep only the last one.
  let lastActivityIdx = -1
  for (let i = migrated.length - 1; i >= 0; i--) {
    if (migrated[i].type === 'activity') { lastActivityIdx = i; break }
  }
  if (lastActivityIdx > 0) {
    return migrated.filter((m, i) => m.type !== 'activity' || i === lastActivityIdx)
  }
  return migrated
}

export interface EntityContext {
  name: string
  section: string
  entityId: string
}

interface ChatStore {
  messages: Record<string, ChatMessage[]>
  /** Tracks which projects have been loaded from the backend. */
  loaded: Record<string, boolean>
  activeRunId: Record<string, string | null>
  /** Currently-viewed entity, shown as a context chip above the chat input. */
  entityContext: Record<string, EntityContext | null>
  /** Last-addressed role per project (conversation stickiness). */
  activeRole: Record<string, string>
  setActiveRole: (projectId: string, roleId: string) => void
  getActiveRole: (projectId: string) => string
  setEntityContext: (projectId: string, ctx: EntityContext) => void
  clearEntityContext: (projectId: string) => void

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
  attachActions: (projectId: string, messageId: string, actions: ChatAction[], preflightData?: PreflightData) => void
  /** Add a tool call to an existing AI message (in-memory only — for inline tool indicators). */
  addToolCall: (projectId: string, messageId: string, tool: ToolCallStatus) => void
  /** Mark a tool call as complete on an existing AI message (in-memory only). */
  completeToolCall: (projectId: string, messageId: string, toolId: string) => void
  /** Remove a message (in-memory only — for discarding empty streaming placeholders). */
  removeMessage: (projectId: string, messageId: string) => void
  /** Update the speaker of an existing message (in-memory only — for streaming). */
  updateMessageSpeaker: (projectId: string, messageId: string, speaker: string) => void
  /** Set page context label on a message (e.g., "Scene 005"). */
  setMessageContext: (projectId: string, messageId: string, context: string) => void
  /** Set the actual injected artifact content on a message (for persistence/debugging). */
  setInjectedContent: (projectId: string, messageId: string, content: string) => void
  /** Finalize a streaming message: remove streaming flag, persist to backend. */
  finalizeStreamingMessage: (projectId: string, messageId: string) => void
  getMessages: (projectId: string) => ChatMessage[]
  clearMessages: (projectId: string) => void
  hasMessages: (projectId: string) => boolean
  isLoaded: (projectId: string) => boolean
  setActiveRun: (projectId: string, runId: string) => void
  clearActiveRun: (projectId: string) => void
  /** Refresh messages from backend for the given project. */
  syncMessages: (projectId: string) => Promise<void>
}

export const useChatStore = create<ChatStore>()(
  (set, get) => ({
    messages: {},
    loaded: {},
    activeRunId: {},
    entityContext: {},
    activeRole: {},

    setActiveRole: (projectId, roleId) =>
      set((state) => ({ activeRole: { ...state.activeRole, [projectId]: roleId } })),

    getActiveRole: (projectId) => get().activeRole[projectId] ?? 'assistant',

    syncMessages: async (projectId) => {
      try {
        const messages = await getChatMessages(projectId)
        get().loadMessages(projectId, messages)
      } catch (error) {
        console.error('Failed to sync chat messages:', error)
      }
    },

    loadMessages: (projectId, messages) => {
      const migrated = migrateMessages(messages)
      // Restore active role stickiness from the last AI message's speaker
      const lastAi = [...migrated].reverse().find(
        m => m.type === 'ai_response' && m.speaker,
      )
      set((state) => ({
        messages: { ...state.messages, [projectId]: migrated },
        loaded: { ...state.loaded, [projectId]: true },
        ...(lastAi?.speaker
          ? { activeRole: { ...state.activeRole, [projectId]: lastAi.speaker } }
          : {}),
      }))
    },

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
      const stableId = `activity_nav_${projectId}`

      const message: ChatMessage = {
        id: stableId,
        type: 'activity',
        content,
        timestamp: Date.now(),
        route,
      }

      // Find the existing activity message anywhere in the list (not just when it's last).
      // The addMessage idempotency guard blocks updates when the stable ID already exists
      // but isn't the last message (e.g. after an AI response lands post-navigation).
      const existingIdx = existing.findIndex(m => m.id === stableId)
      if (existingIdx !== -1) {
        set((state) => {
          const updated = [...(state.messages[projectId] ?? [])]
          updated[existingIdx] = message
          return { messages: { ...state.messages, [projectId]: updated } }
        })
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

    attachActions: (projectId, messageId, actions, preflightData) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = {
          ...updated[idx],
          actions,
          needsAction: true,
          ...(preflightData ? { preflightData } : {}),
        }
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

    removeMessage: (projectId, messageId) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        return { messages: { ...state.messages, [projectId]: msgs.filter(m => m.id !== messageId) } }
      }),

    updateMessageSpeaker: (projectId, messageId, speaker) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], speaker }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    setMessageContext: (projectId, messageId, context) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], pageContext: context }
        return { messages: { ...state.messages, [projectId]: updated } }
      }),

    setInjectedContent: (projectId, messageId, content) =>
      set((state) => {
        const msgs = state.messages[projectId]
        if (!msgs) return state
        const idx = msgs.findIndex(m => m.id === messageId)
        if (idx === -1) return state
        const updated = [...msgs]
        updated[idx] = { ...updated[idx], injectedContent: content }
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
      // is the first write for this message ID.  Keep toolCalls + pageContext
      // so the chat log records what tools ran and what context was attached.
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { streaming: _s, ...persistable } = finalized
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      postChatMessage(projectId, persistable as any).catch(() => {})
    },

    getMessages: (projectId) => get().messages[projectId] ?? [],

    clearMessages: (projectId) =>
      set((state) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { [projectId]: _, ...rest } = state.messages
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
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

    setEntityContext: (projectId, ctx) =>
      set((state) => ({ entityContext: { ...state.entityContext, [projectId]: ctx } })),

    clearEntityContext: (projectId) =>
      set((state) => ({ entityContext: { ...state.entityContext, [projectId]: null } })),
  }),
)
