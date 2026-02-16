import { createContext, useContext, useState, type ReactNode } from 'react'

type ActiveTab = 'chat' | 'inspector'

interface RightPanelState {
  open: boolean
  activeTab: ActiveTab
  inspectorTitle: string | null
  inspectorContent: ReactNode | null
}

interface RightPanelContextValue {
  state: RightPanelState
  openChat: () => void
  openInspector: (title: string, content: ReactNode) => void
  close: () => void
  toggle: () => void
  setTab: (tab: ActiveTab) => void
}

const RightPanelContext = createContext<RightPanelContextValue | null>(null)

export function RightPanelProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RightPanelState>({
    open: true,
    activeTab: 'chat',
    inspectorTitle: null,
    inspectorContent: null,
  })

  const openChat = () => {
    setState(s => ({ ...s, open: true, activeTab: 'chat' }))
  }

  const openInspector = (title: string, content: ReactNode) => {
    setState({ open: true, activeTab: 'inspector', inspectorTitle: title, inspectorContent: content })
  }

  const close = () => {
    setState(s => ({ ...s, open: false }))
  }

  const toggle = () => {
    setState(s => ({ ...s, open: !s.open }))
  }

  const setTab = (tab: ActiveTab) => {
    setState(s => ({ ...s, activeTab: tab }))
  }

  return (
    <RightPanelContext.Provider value={{ state, openChat, openInspector, close, toggle, setTab }}>
      {children}
    </RightPanelContext.Provider>
  )
}

export function useRightPanel() {
  const ctx = useContext(RightPanelContext)
  if (!ctx) throw new Error('useRightPanel must be used within RightPanelProvider')
  return ctx
}

// Backward-compatible wrapper for existing code that uses useInspector
export function useInspector() {
  const panel = useRightPanel()
  return {
    state: {
      open: panel.state.open && panel.state.activeTab === 'inspector',
      content: panel.state.inspectorContent,
      title: panel.state.inspectorTitle,
    },
    open: panel.openInspector,
    close: panel.close,
    toggle: panel.toggle,
  }
}
