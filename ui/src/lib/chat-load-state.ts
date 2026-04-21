export type ChatLoadPhase = 'idle' | 'loading' | 'ready' | 'error'

export interface ChatLoadState {
  phase: ChatLoadPhase
  error: string | null
}

export const DEFAULT_CHAT_LOAD_STATE: ChatLoadState = {
  phase: 'idle',
  error: null,
}

export function shouldAttemptChatLoad(state: ChatLoadState | undefined): boolean {
  return (state ?? DEFAULT_CHAT_LOAD_STATE).phase === 'idle'
}

export function shouldAutoSyncChat(state: ChatLoadState | undefined): boolean {
  return (state ?? DEFAULT_CHAT_LOAD_STATE).phase !== 'error'
}

export function resolveChatLoadErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const message = error.message.trim()
    if (message.length > 0) {
      return message
    }
  }

  return 'Chat is temporarily unavailable.'
}
