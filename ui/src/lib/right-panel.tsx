import { useState, type ReactNode } from 'react'
import type { ChatIntent } from '@/lib/chat-intents'
import { RightPanelContext, type RightPanelState } from '@/lib/right-panel-context'

export function RightPanelProvider({
  children,
  initialOpen = true,
}: {
  children: ReactNode
  initialOpen?: boolean
}) {
  const [state, setState] = useState<RightPanelState>({
    open: initialOpen,
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
