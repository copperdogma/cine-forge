// Zustand store tracking all active long-running operations per project.
// OperationBanner reads from this; useLongRunningAction writes to it.

import { create } from 'zustand'

export interface Operation {
  id: string
  projectId: string
  label: string
  startedAt: number
  status: 'running' | 'done' | 'failed'
  progress?: { current: number; total: number }
  /** Linked chat message ID (for TaskProgressCard or ai_status). */
  chatMessageId?: string
}

interface OperationStore {
  /** Per-project active operations. */
  operations: Record<string, Operation[]>

  addOperation: (projectId: string, op: Operation) => void
  updateProgress: (projectId: string, opId: string, current: number) => void
  completeOperation: (projectId: string, opId: string) => void
  failOperation: (projectId: string, opId: string) => void
  removeOperation: (projectId: string, opId: string) => void
  getOperations: (projectId: string) => Operation[]
}

export const useOperationStore = create<OperationStore>()((set, get) => ({
  operations: {},

  addOperation: (projectId, op) =>
    set((state) => {
      const existing = state.operations[projectId] ?? []
      // Idempotent: skip if already tracked
      if (existing.some((o) => o.id === op.id)) return state
      return {
        operations: {
          ...state.operations,
          [projectId]: [...existing, op],
        },
      }
    }),

  updateProgress: (projectId, opId, current) =>
    set((state) => {
      const ops = state.operations[projectId]
      if (!ops) return state
      return {
        operations: {
          ...state.operations,
          [projectId]: ops.map((o) =>
            o.id === opId && o.progress
              ? { ...o, progress: { ...o.progress, current } }
              : o,
          ),
        },
      }
    }),

  completeOperation: (projectId, opId) =>
    set((state) => {
      const ops = state.operations[projectId]
      if (!ops) return state
      return {
        operations: {
          ...state.operations,
          [projectId]: ops.map((o) =>
            o.id === opId ? { ...o, status: 'done' as const } : o,
          ),
        },
      }
    }),

  failOperation: (projectId, opId) =>
    set((state) => {
      const ops = state.operations[projectId]
      if (!ops) return state
      return {
        operations: {
          ...state.operations,
          [projectId]: ops.map((o) =>
            o.id === opId ? { ...o, status: 'failed' as const } : o,
          ),
        },
      }
    }),

  removeOperation: (projectId, opId) =>
    set((state) => {
      const ops = state.operations[projectId]
      if (!ops) return state
      return {
        operations: {
          ...state.operations,
          [projectId]: ops.filter((o) => o.id !== opId),
        },
      }
    }),

  getOperations: (projectId) => get().operations[projectId] ?? [],
}))
