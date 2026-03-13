import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ChatIntent } from '@/lib/chat-intents'

interface RightPanelState {
  open: boolean
  pendingIntent: ChatIntent | null
}

interface RightPanelContextValue {
  state: RightPanelState
  openChat: () => void
  openChatWithIntent: (intent: ChatIntent) => void
  consumePendingIntent: () => void
  close: () => void
  toggle: () => void
}

const RightPanelContext = createContext<RightPanelContextValue | null>(null)

export function RightPanelProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RightPanelState>({
    open: true,
    pendingIntent: null,
  })

  const openChat = () => {
    setState(s => ({ ...s, open: true }))
  }

  const openChatWithIntent = (intent: ChatIntent) => {
    setState(s => ({ ...s, open: true, pendingIntent: intent }))
  }

  const consumePendingIntent = () => {
    setState(s => (
      s.pendingIntent
        ? { ...s, pendingIntent: null }
        : s
    ))
  }

  const close = () => {
    setState(s => ({ ...s, open: false }))
  }

  const toggle = () => {
    setState(s => ({ ...s, open: !s.open }))
  }

  return (
    <RightPanelContext.Provider
      value={{ state, openChat, openChatWithIntent, consumePendingIntent, close, toggle }}
    >
      {children}
    </RightPanelContext.Provider>
  )
}

export function useRightPanel() {
  const ctx = useContext(RightPanelContext)
  if (!ctx) throw new Error('useRightPanel must be used within RightPanelProvider')
  return ctx
}
