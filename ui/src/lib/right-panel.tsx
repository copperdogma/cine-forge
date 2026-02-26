import { createContext, useContext, useState, type ReactNode } from 'react'

interface RightPanelState {
  open: boolean
}

interface RightPanelContextValue {
  state: RightPanelState
  openChat: () => void
  close: () => void
  toggle: () => void
}

const RightPanelContext = createContext<RightPanelContextValue | null>(null)

export function RightPanelProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RightPanelState>({
    open: true,
  })

  const openChat = () => {
    setState({ open: true })
  }

  const close = () => {
    setState(s => ({ ...s, open: false }))
  }

  const toggle = () => {
    setState(s => ({ ...s, open: !s.open }))
  }

  return (
    <RightPanelContext.Provider value={{ state, openChat, close, toggle }}>
      {children}
    </RightPanelContext.Provider>
  )
}

export function useRightPanel() {
  const ctx = useContext(RightPanelContext)
  if (!ctx) throw new Error('useRightPanel must be used within RightPanelProvider')
  return ctx
}
