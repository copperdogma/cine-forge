import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles, CheckCircle2, Loader2, MessageSquare, Send, User, Wrench } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore } from '@/lib/chat-store'
import { useProjectInputs, useStartRun } from '@/lib/hooks'
import { streamChatMessage } from '@/lib/api'
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
    case 'user_message':
      return <User className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
    case 'ai_response':
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_tool_status':
      return <Wrench className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5 animate-pulse" />
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
    // --- Confirmation actions (AI-proposed writes) ---
    if (action.confirm_action) {
      setBusy(true)
      const store = useChatStore.getState()
      store.addMessage(projectId, {
        id: `action_${Date.now()}`,
        type: 'user_action',
        content: action.label,
        timestamp: Date.now(),
      })

      try {
        const response = await fetch(action.confirm_action.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.confirm_action.payload),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => null)
          throw new Error(errorData?.message ?? `Request failed (${response.status})`)
        }

        const result = await response.json()

        if (action.confirm_action.type === 'start_run' && result.run_id) {
          store.setActiveRun(projectId, result.run_id)
          store.addMessage(projectId, {
            id: `run_started_${result.run_id}`,
            type: 'ai_status',
            content: 'Run started — processing your project now...',
            timestamp: Date.now(),
            actions: [
              { id: 'view_run', label: 'View Run Details', variant: 'outline', route: `runs/${result.run_id}` },
            ],
          })
        } else if (action.confirm_action.type === 'edit_artifact') {
          store.addMessage(projectId, {
            id: `edit_done_${Date.now()}`,
            type: 'ai_status_done',
            content: `Changes applied — created version ${result.version ?? 'new'} of ${result.artifact_type ?? 'artifact'}/${result.entity_id ?? 'unknown'}.`,
            timestamp: Date.now(),
            actions: result.artifact_type && result.entity_id ? [
              {
                id: 'view_artifact',
                label: 'View Artifact',
                variant: 'outline',
                route: `artifacts/${result.artifact_type}/${result.entity_id}/${result.version ?? 1}`,
              },
            ] : undefined,
          })
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Action failed'
        toast.error(message)
        store.addMessage(projectId, {
          id: `error_${Date.now()}`,
          type: 'ai_suggestion',
          content: `Something went wrong: ${message}. You can try again or ask the AI for help.`,
          timestamp: Date.now(),
        })
      } finally {
        setBusy(false)
      }
      return
    }

    // --- Legacy run-triggering actions (from 011e hardcoded buttons) ---
    const recipeId = RUN_ACTION_IDS[action.id]

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
        store.setActiveRun(projectId, result.run_id)
        store.addMessage(projectId, {
          id: `run_started_${result.run_id}`,
          type: 'ai_status',
          content: 'Analysis started — reading your screenplay now...',
          timestamp: Date.now(),
          actions: [
            { id: 'view_run_details', label: 'View Run Details', variant: 'outline', route: `runs/${result.run_id}` },
          ],
        })
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

    // --- Standard navigation ---
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
  const isUser = message.type === 'user_action' || message.type === 'user_message'
  const showActions = message.actions && message.actions.length > 0 && !actionTaken
  const isStreaming = message.streaming

  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
          {isStreaming && <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse ml-0.5 align-text-bottom" />}
        </p>
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
  const addMessage = useChatStore(s => s.addMessage)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const startRun = useStartRun()
  const { data: inputs } = useProjectInputs(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const [inputText, setInputText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  // Auto-scroll to bottom within the chat scroll area only (not the whole page)
  useEffect(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight
    }
  }, [messages.length, messages[messages.length - 1]?.content])

  const handleSendMessage = async () => {
    if (!inputText.trim() || !projectId || isStreaming) return

    const userText = inputText.trim()
    const userMsgId = `user_${Date.now()}`
    const aiMsgId = `ai_${Date.now()}`

    // Add user message
    addMessage(projectId, {
      id: userMsgId,
      type: 'user_message',
      content: userText,
      timestamp: Date.now(),
    })

    // Add placeholder AI message for streaming
    const store = useChatStore.getState()
    store.addMessage(projectId, {
      id: aiMsgId,
      type: 'ai_response',
      content: '',
      timestamp: Date.now(),
      streaming: true,
    })

    setInputText('')
    setIsStreaming(true)

    // Build chat history from recent messages
    const chatHistory = messages.slice(-20).map(m => ({
      type: m.type,
      content: m.content,
    }))

    let fullContent = ''

    await streamChatMessage(
      projectId,
      userText,
      chatHistory,
      (chunk) => {
        if (chunk.type === 'text') {
          fullContent += chunk.content ?? ''
          useChatStore.getState().updateMessageContent(projectId, aiMsgId, fullContent)
        } else if (chunk.type === 'tool_start') {
          const toolName = chunk.name?.replace(/_/g, ' ') ?? 'tool'
          useChatStore.getState().addMessage(projectId, {
            id: `tool_${Date.now()}_${chunk.id}`,
            type: 'ai_tool_status',
            content: `Looking up ${toolName}...`,
            timestamp: Date.now(),
          })
        } else if (chunk.type === 'actions' && chunk.actions) {
          // Attach proposal action buttons to the AI message
          useChatStore.getState().attachActions(projectId, aiMsgId, chunk.actions)
        }
      },
      () => {
        // Done — finalize the streaming message
        useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
        setIsStreaming(false)
      },
      (error) => {
        // Error — show in the AI message
        const errorContent = fullContent
          ? fullContent + '\n\n(Stream interrupted)'
          : `Sorry, something went wrong: ${error.message}`
        useChatStore.getState().updateMessageContent(projectId, aiMsgId, errorContent)
        useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
        setIsStreaming(false)
        toast.error(`Chat error: ${error.message}`)
      },
    )
  }

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

      {/* Chat input */}
      <div className="border-t border-border p-3 shrink-0">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            placeholder={isStreaming ? 'Waiting for response...' : 'Ask about your project or screenplay...'}
            disabled={isStreaming}
            className={cn(
              'flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 focus:ring-offset-background',
              'placeholder:text-muted-foreground',
              isStreaming && 'opacity-50 cursor-not-allowed',
            )}
          />
          <Button
            size="sm"
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isStreaming}
            className="shrink-0"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
