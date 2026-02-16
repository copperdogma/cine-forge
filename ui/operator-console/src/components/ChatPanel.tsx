import { useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles, CheckCircle2, Loader2, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore } from '@/lib/chat-store'
import type { ChatMessage, ChatAction } from '@/lib/types'
import { cn } from '@/lib/utils'

function MessageIcon({ type }: { type: ChatMessage['type'] }) {
  switch (type) {
    case 'ai_welcome':
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_suggestion':
      return <MessageSquare className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_status':
      return <Loader2 className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5 animate-spin" />
    case 'user_action':
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
    default:
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
  }
}

function ActionButton({ action, projectId }: { action: ChatAction; projectId: string }) {
  const navigate = useNavigate()
  const addMessage = useChatStore(s => s.addMessage)

  const handleClick = () => {
    // Log the user action in chat
    addMessage(projectId, {
      id: `action_${Date.now()}`,
      type: 'user_action',
      content: action.label,
      timestamp: Date.now(),
    })

    // Navigate if route provided
    if (action.route) {
      // Handle absolute routes (starting with /) vs relative
      if (action.route.startsWith('/')) {
        navigate(action.route)
      } else {
        navigate(`/${projectId}/${action.route}`)
      }
    }
  }

  return (
    <Button
      variant={action.variant === 'default' ? 'default' : action.variant === 'secondary' ? 'secondary' : 'outline'}
      size="sm"
      className="cursor-pointer"
      onClick={handleClick}
    >
      {action.label}
    </Button>
  )
}

function ChatMessageItem({ message, projectId }: { message: ChatMessage; projectId: string }) {
  const isUser = message.type === 'user_action'

  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        {message.actions && message.actions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.actions.map(action => (
              <ActionButton key={action.id} action={action} projectId={projectId} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatPanel() {
  const { projectId } = useParams()
  const messages = useChatStore(s => s.getMessages(projectId ?? ''))
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-1">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Sparkles className="h-8 w-8 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                Your project journal will appear here.
              </p>
            </div>
          ) : (
            messages.map(msg => (
              <ChatMessageItem key={msg.id} message={msg} projectId={projectId ?? ''} />
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Disabled text input — affordance for 011f */}
      <div className="border-t border-border p-3 shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            disabled
            placeholder="Chat coming in a future update..."
            className="flex-1 rounded-md border border-border bg-muted/50 px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
          />
        </div>
      </div>
    </div>
  )
}
