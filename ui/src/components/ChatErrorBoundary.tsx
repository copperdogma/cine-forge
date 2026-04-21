import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

type ChatErrorBoundaryProps = {
  children: ReactNode
}

type ChatErrorBoundaryState = {
  hasError: boolean
}

class ChatErrorBoundaryInner extends Component<ChatErrorBoundaryProps, ChatErrorBoundaryState> {
  override state: ChatErrorBoundaryState = {
    hasError: false,
  }

  static getDerivedStateFromError(): ChatErrorBoundaryState {
    return { hasError: true }
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Chat panel render failed:', error, errorInfo)
  }

  private readonly resetBoundary = () => {
    this.setState({ hasError: false })
  }

  override render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-8 text-center">
        <div className="rounded-full bg-destructive/10 p-3">
          <AlertTriangle className="h-6 w-6 text-destructive" />
        </div>
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Chat is temporarily unavailable</h3>
          <p className="text-sm text-muted-foreground">
            The chat panel hit an unexpected error. The rest of the project stays available.
          </p>
        </div>
        <Button type="button" variant="outline" className="gap-2" onClick={this.resetBoundary}>
          <RefreshCw className="h-4 w-4" />
          Retry Chat
        </Button>
      </div>
    )
  }
}

export function ChatErrorBoundary({ children }: ChatErrorBoundaryProps) {
  return <ChatErrorBoundaryInner>{children}</ChatErrorBoundaryInner>
}
