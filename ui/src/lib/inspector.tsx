import { createContext, useContext, useState, type ReactNode } from 'react'

interface InspectorState {
  open: boolean
  content: ReactNode | null
  title: string | null
}

interface InspectorContextValue {
  state: InspectorState
  open: (title: string, content: ReactNode) => void
  close: () => void
  toggle: () => void
}

const InspectorContext = createContext<InspectorContextValue | null>(null)

export function InspectorProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<InspectorState>({
    open: false,
    content: null,
    title: null,
  })

  const open = (title: string, content: ReactNode) => {
    setState({ open: true, title, content })
  }

  const close = () => {
    setState(s => ({ ...s, open: false }))
  }

  const toggle = () => {
    setState(s => ({ ...s, open: !s.open }))
  }

  return (
    <InspectorContext.Provider value={{ state, open, close, toggle }}>
      {children}
    </InspectorContext.Provider>
  )
}

export function useInspector() {
  const ctx = useContext(InspectorContext)
  if (!ctx) throw new Error('useInspector must be used within InspectorProvider')
  return ctx
}
