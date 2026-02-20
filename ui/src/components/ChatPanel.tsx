import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Activity, Sparkles, CheckCircle2, Loader2, MessageSquare, Send, User, Wrench } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore } from '@/lib/chat-store'
import { useProjectInputs, useStartRun } from '@/lib/hooks'
import { streamChatMessage } from '@/lib/api'
import { RunProgressCard } from '@/components/RunProgressCard'
import type { ChatMessage, ChatAction, ToolCallStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Human-friendly tool name mapping. */
const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_artifact: 'Reading artifact',
  get_project_state: 'Checking project state',
  list_scenes: 'Browsing scenes',
  list_characters: 'Looking up characters',
  list_locations: 'Looking up locations',
  edit_artifact: 'Proposing edits',
  start_pipeline: 'Preparing pipeline run',
  talk_to_role: 'Consulting expert role',
}

function friendlyToolName(rawName: string): string {
  return TOOL_DISPLAY_NAMES[rawName] ?? rawName.replace(/_/g, ' ')
}

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
    case 'ai_tool_done':
      return <Wrench className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
    case 'ai_progress':
      return null // Progress card renders its own icons per stage
    case 'activity':
      return <Activity className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0 mt-0.5" />
    default:
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
  }
}

function ActionButton({
  action,
  projectId,
  startRun,
  inputPath,
  onRetry,
}: {
  action: ChatAction
  projectId: string
  startRun: ReturnType<typeof useStartRun>
  inputPath: string | undefined
  onRetry?: (text: string) => void
}) {
  const navigate = useNavigate()
  const addMessage = useChatStore(s => s.addMessage)
  const [busy, setBusy] = useState(false)

  const handleClick = async () => {
    // --- Retry action (re-send a failed message) ---
    if (action.retry_text && onRetry) {
      onRetry(action.retry_text)
      return
    }

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
          store.addActivity(projectId, `Started pipeline run`, `runs/${result.run_id}`)
        } else if (action.confirm_action.type === 'edit_artifact') {
          const artLabel = `${result.artifact_type ?? 'artifact'}/${result.entity_id ?? 'unknown'}`
          const artRoute = result.artifact_type && result.entity_id
            ? `artifacts/${result.artifact_type}/${result.entity_id}/${result.version ?? 1}`
            : undefined
          store.addMessage(projectId, {
            id: `edit_done_${Date.now()}`,
            type: 'ai_status_done',
            content: `Changes applied — created version ${result.version ?? 'new'} of ${artLabel}.`,
            timestamp: Date.now(),
            actions: artRoute ? [
              { id: 'view_artifact', label: 'View Artifact', variant: 'outline', route: artRoute },
            ] : undefined,
          })
          store.addActivity(projectId, `Updated: ${artLabel}`, artRoute)
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
          default_model: 'claude-sonnet-4-6',
          recipe_id: recipeId,
          accept_config: true,
        })
        store.setActiveRun(projectId, result.run_id)
        store.addMessage(projectId, {
          id: `run_started_${result.run_id}`,
          type: 'ai_status',
          content: 'Breaking down your screenplay now...',
          timestamp: Date.now(),
          actions: [
            { id: 'view_run_details', label: 'View Run Details', variant: 'outline', route: `runs/${result.run_id}` },
          ],
        })
        store.addActivity(projectId, `Started pipeline: ${recipeId}`, `runs/${result.run_id}`)
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

function ToolIndicator({ tool }: { tool: ToolCallStatus }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Wrench className={cn('h-3.5 w-3.5 shrink-0', !tool.done && 'animate-pulse')} />
      <span>{tool.displayName}{tool.done ? '' : '...'}</span>
      {tool.done && <CheckCircle2 className="h-3 w-3 text-primary shrink-0" />}
    </div>
  )
}

function ChatMessageItem({
  message,
  projectId,
  actionTaken,
  startRun,
  inputPath,
  onRetry,
}: {
  message: ChatMessage
  projectId: string
  actionTaken: boolean
  startRun: ReturnType<typeof useStartRun>
  inputPath: string | undefined
  onRetry?: (text: string) => void
}) {
  const isUser = message.type === 'user_action' || message.type === 'user_message'
  const isActivity = message.type === 'activity'
  const showActions = message.actions && message.actions.length > 0 && !actionTaken
  const isStreaming = message.streaming

  const toolCalls = message.toolCalls
  const isThinking = isStreaming && !message.content && (!toolCalls || toolCalls.length === 0)

  // Progress card — single widget for all pipeline stages
  if (message.type === 'ai_progress') {
    return (
      <div className="py-1">
        <RunProgressCard runId={message.content} />
      </div>
    )
  }

  // Activity notes render as compact, subtle inline entries
  if (isActivity) {
    const navigate = useNavigate()
    return (
      <div className="flex items-center gap-2 py-0.5 px-1">
        <MessageIcon type={message.type} />
        <span
          className={cn(
            'text-xs text-muted-foreground/60 truncate',
            message.route && 'hover:text-muted-foreground cursor-pointer underline-offset-2 hover:underline',
          )}
          onClick={() => {
            if (message.route) {
              navigate(message.route.startsWith('/') ? message.route : `/${projectId}/${message.route}`)
            }
          }}
        >
          {message.content}
        </span>
      </div>
    )
  }

  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        {/* Thinking indicator — shown before first token or tool call */}
        {isThinking && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
            <span>Thinking...</span>
          </div>
        )}
        {/* Inline tool indicators (shown above text for ai_response) */}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-1 mb-2">
            {toolCalls.map(tool => (
              <ToolIndicator key={tool.id} tool={tool} />
            ))}
          </div>
        )}
        {message.type === 'ai_response' && message.content ? (
          <div className="text-sm leading-relaxed prose prose-sm prose-invert max-w-none prose-p:my-1.5 prose-strong:text-foreground prose-em:text-foreground/90 prose-ul:my-1.5 prose-li:my-0.5 prose-headings:text-foreground prose-headings:mt-3 prose-headings:mb-1.5">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse ml-0.5 align-text-bottom" />}
          </div>
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
            {isStreaming && <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse ml-0.5 align-text-bottom" />}
          </p>
        )}
        {showActions && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.actions!.map(action => (
              <ActionButton
                key={action.id}
                action={action}
                projectId={projectId}
                startRun={startRun}
                inputPath={inputPath}
                onRetry={onRetry}
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

  // Listen for programmatic "ask" events (from GlossaryTerm, SectionHelp, etc.)
  useEffect(() => {
    const handler = (e: Event) => {
      const question = (e as CustomEvent).detail?.question
      if (question && !isStreaming) {
        handleSendMessage(question)
      }
    }
    window.addEventListener('cineforge:ask', handler)
    return () => window.removeEventListener('cineforge:ask', handler)
  }) // intentionally no deps — always use latest isStreaming/handleSendMessage

  const handleSendMessage = async (overrideText?: string) => {
    const textToSend = overrideText ?? inputText.trim()
    if (!textToSend || !projectId || isStreaming) return

    const userText = textToSend
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

    if (!overrideText) setInputText('')
    setIsStreaming(true)

    // Build full chat history for the AI (persistent thread)
    const chatHistory = messages.map(m => ({
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
          const rawName = chunk.name ?? 'tool'
          useChatStore.getState().addToolCall(projectId, aiMsgId, {
            id: chunk.id ?? `tool_${Date.now()}`,
            name: rawName,
            displayName: friendlyToolName(rawName),
            done: false,
          })
        } else if (chunk.type === 'tool_result') {
          if (chunk.id) {
            useChatStore.getState().completeToolCall(projectId, aiMsgId, chunk.id)
          }
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
        // Error — show in the AI message with retry affordance
        const errorContent = fullContent
          ? fullContent + '\n\n(Stream interrupted)'
          : `Sorry, something went wrong. ${error.message}`
        useChatStore.getState().updateMessageContent(projectId, aiMsgId, errorContent)
        useChatStore.getState().attachActions(projectId, aiMsgId, [
          { id: `retry_${Date.now()}`, label: 'Try Again', variant: 'outline', retry_text: userText },
        ])
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
                  onRetry={handleSendMessage}
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
            onClick={() => handleSendMessage()}
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
