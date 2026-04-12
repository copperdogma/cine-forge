import { createContext } from 'react'
import type { ChatIntent } from '@/lib/chat-intents'

export interface RightPanelState {
  open: boolean
  pendingIntent: ChatIntent | null
}

export interface RightPanelContextValue {
  state: RightPanelState
  openChat: () => void
  openChatWithIntent: (intent: ChatIntent) => void
  consumePendingIntent: () => void
  close: () => void
  toggle: () => void
}

export const RightPanelContext = createContext<RightPanelContextValue | null>(null)
