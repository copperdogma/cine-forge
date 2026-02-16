import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles, CheckCircle2, Loader2, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore } from '@/lib/chat-store'
import { useProjectInputs, useStartRun } from '@/lib/hooks'
import type { ChatMessage, ChatAction } from '@/lib/types'
import { cn } from '@/lib/utils'

const EMPTY_MESSAGES: ChatMessage[] = []

// Action IDs that trigger API calls instead of navigation
const RUN_ACTION_IDS: Record<string, string> = {
  start_analysis: 'mvp_ingest',
  go_deeper: 'world_building',
}

function MessageIcon({ type }: { type: ChatMessage['type'] }) {
  switch (type) {
    case 'ai_welcome':
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_suggestion':
      return <MessageSquare className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_status':
      return <Loader2 className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5 animate-spin" />
    case 'ai_status_done':
      return <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'user_action':
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
    default:
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
  }
}

function ActionButton({
  action,
  projectId,
  startRun,
  inputPath,
}: {
  action: ChatAction
  projectId: string
  startRun: ReturnType<typeof useStartRun>
  inputPath: string | undefined
}) {
  const navigate = useNavigate()
  const addMessage = useChatStore(s => s.addMessage)
  const [busy, setBusy] = useState(false)

  const handleClick = async () => {
    // Check for run-triggering actions
    const recipeId = RUN_ACTION_IDS[action.id]

    // Only log user_action for real operations (not navigation links)
    if (recipeId) {
      addMessage(projectId, {
        id: `action_${Date.now()}`,
        type: 'user_action',
        content: action.label,
        timestamp: Date.now(),
      })
    }
    if (recipeId && inputPath) {
      setBusy(true)
      const store = useChatStore.getState()
      try {
        const result = await startRun.mutateAsync({
          project_id: projectId,
          input_file: inputPath,
          default_model: 'claude-sonnet-4-5-20250929',
          recipe_id: recipeId,
          accept_config: true,
        })
        // Track the run — useRunProgressChat in AppShell picks up the polling
        store.setActiveRun(projectId, result.run_id)
        store.addMessage(projectId, {
          id: `run_started_${result.run_id}`,
          type: 'ai_status',
          content: 'Analysis started — reading your screenplay now...',
          timestamp: Date.now(),
          actions: [
            {
              id: 'view_run_details',
              label: 'View Run Details',
              variant: 'outline',
              route: `runs/${result.run_id}`,
            },
          ],
        })
        // Stay on the current page — progress will appear in chat
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to start analysis'
        toast.error(message)
        store.addMessage(projectId, {
          id: `error_${Date.now()}`,
          type: 'ai_suggestion',
          content: `Something went wrong: ${message}. You can try again or configure the pipeline manually.`,
          timestamp: Date.now(),
          actions: [
            { id: 'manual_pipeline', label: 'Configure Manually', variant: 'outline', route: 'run' },
          ],
        })
      } finally {
        setBusy(false)
      }
      return
    }

    // Standard navigation
    if (action.route) {
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
      disabled={busy || startRun.isPending}
    >
      {busy ? (
        <>
          <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
          Starting...
        </>
      ) : (
        action.label
      )}
    </Button>
  )
}

function ChatMessageItem({
  message,
  projectId,
  actionTaken,
  startRun,
  inputPath,
}: {
  message: ChatMessage
  projectId: string
  actionTaken: boolean
  startRun: ReturnType<typeof useStartRun>
  inputPath: string | undefined
}) {
  const isUser = message.type === 'user_action'
  const showActions = message.actions && message.actions.length > 0 && !actionTaken

  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        {showActions && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.actions!.map(action => (
              <ActionButton
                key={action.id}
                action={action}
                projectId={projectId}
                startRun={startRun}
                inputPath={inputPath}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatPanel() {
  const { projectId } = useParams()
  const messages = useChatStore(s => s.messages[projectId ?? ''] ?? EMPTY_MESSAGES)
  const scrollRef = useRef<HTMLDivElement>(null)
  const startRun = useStartRun()
  const { data: inputs } = useProjectInputs(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path

  // Auto-scroll to bottom within the chat scroll area only (not the whole page)
  useEffect(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight
    }
  }, [messages.length])

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <ScrollArea className="flex-1 min-h-0" ref={scrollRef}>
        <div className="px-3 pr-4 py-3 space-y-1">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Sparkles className="h-8 w-8 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                Your project journal will appear here.
              </p>
            </div>
          ) : (
            messages.map((msg, i) => {
              // Hide action buttons if a subsequent user_action message exists (action was taken)
              const actionTaken = !!(
                msg.needsAction &&
                messages.slice(i + 1).some(m => m.type === 'user_action')
              )
              return (
                <ChatMessageItem
                  key={msg.id}
                  message={msg}
                  projectId={projectId ?? ''}
                  actionTaken={actionTaken}
                  startRun={startRun}
                  inputPath={latestInputPath}
                />
              )
            })
          )}
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
