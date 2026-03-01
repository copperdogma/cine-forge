import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import {
  Activity, Clapperboard, Drama, Eye, MapPin,
  Package, Scissors, Send, Sparkles, Square, CheckCircle2, Loader2,
  MessageSquare, User, UserRound, Users, Volume2, Wrench,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useChatStore } from '@/lib/chat-store'
import { useProject, useProjectInputs, useStartRun, useProjectCharacters } from '@/lib/hooks'
import { postChatMessage, streamChatMessage, updateProjectSettings } from '@/lib/api'
import { PreflightCard } from '@/components/PreflightCard'
import { RunProgressCard } from '@/components/RunProgressCard'
import { TaskProgressCard } from '@/components/TaskProgressCard'
import type { ChatMessage, ChatAction, InteractionMode, ProjectSummary, ToolCallStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

// ---------------------------------------------------------------------------
// Role display config — visual identity for each role in the group chat
// ---------------------------------------------------------------------------

type RoleDisplayConfig = {
  name: string
  icon: React.ElementType
  iconClass: string      // Tailwind classes for the avatar icon
  badgeClass: string     // Color for name label text
  bgClass: string        // Very dim background tint for message bubble
}

const ROLE_DISPLAY: Record<string, RoleDisplayConfig> = {
  assistant: {
    name: 'Assistant',
    icon: Sparkles,
    iconClass: 'text-zinc-400',
    badgeClass: 'text-zinc-400',
    bgClass: 'bg-zinc-500/5',
  },
  director: {
    name: 'Director',
    icon: Clapperboard,
    iconClass: 'text-violet-400',
    badgeClass: 'text-violet-400',
    bgClass: 'bg-violet-500/8',
  },
  editorial_architect: {
    name: 'Editorial Architect',
    icon: Scissors,
    iconClass: 'text-pink-400',
    badgeClass: 'text-pink-400',
    bgClass: 'bg-pink-500/8',
  },
  visual_architect: {
    name: 'Visual Architect',
    icon: Eye,
    iconClass: 'text-sky-400',
    badgeClass: 'text-sky-400',
    bgClass: 'bg-sky-500/8',
  },
  sound_designer: {
    name: 'Sound Designer',
    icon: Volume2,
    iconClass: 'text-emerald-400',
    badgeClass: 'text-emerald-400',
    bgClass: 'bg-emerald-500/8',
  },
  story_editor: {
    name: 'Story Editor',
    icon: Drama,
    iconClass: 'text-amber-400',
    badgeClass: 'text-amber-400',
    bgClass: 'bg-amber-500/8',
  },
}

/** Get role display config with character handling and generic fallback. */
function getRoleDisplay(speaker: string): RoleDisplayConfig & { isCharacter?: boolean; characterId?: string } {
  // Character speakers use "char:handle" format
  if (speaker.startsWith('char:')) {
    const handle = speaker.slice(5)
    const displayName = handle.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    return {
      name: displayName,
      icon: User,
      iconClass: 'text-amber-200',
      badgeClass: 'text-amber-200',
      bgClass: 'bg-amber-100/8',
      isCharacter: true,
      characterId: handle,
    }
  }
  return ROLE_DISPLAY[speaker] ?? {
    name: speaker.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    icon: MessageSquare,
    iconClass: 'text-zinc-500',
    badgeClass: 'text-zinc-500',
    bgClass: 'bg-zinc-500/5',
  }
}

/** All roles available for @-mention in the role picker. */
const PICKABLE_ROLES = [
  'assistant', 'director', 'editorial_architect',
  'visual_architect', 'sound_designer', 'story_editor',
] as const

/** Shortcuts that expand to special behavior. */
const MENTION_SHORTCUTS = [
  { id: 'all-creatives', name: 'All Creatives', description: 'Director + all creative roles' },
] as const

/** Autocomplete item — a role, character, or shortcut. */
type MentionItem = {
  kind: 'shortcut' | 'role' | 'character'
  id: string
  name: string
  description?: string
}

/** Human-friendly tool name mapping. */
const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_artifact: 'Reading artifact',
  get_project_state: 'Checking project state',
  list_scenes: 'Browsing scenes',
  list_characters: 'Looking up characters',
  list_locations: 'Looking up locations',
  propose_artifact_edit: 'Proposing edits',
  propose_run: 'Preparing pipeline run',
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

function MessageIcon({ type, speaker }: { type: ChatMessage['type']; speaker?: string }) {
  // For AI responses with a known speaker, use the role's icon and color
  if (speaker && (type === 'ai_response' || type === 'ai_welcome' || type === 'ai_suggestion')) {
    const config = getRoleDisplay(speaker)
    const Icon = config.icon
    return <Icon className={cn('h-4 w-4 shrink-0 mt-0.5', config.iconClass)} />
  }

  switch (type) {
    case 'ai_welcome':
    case 'ai_suggestion':
      return <MessageSquare className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_status':
      return <Loader2 className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5 animate-spin" />
    case 'ai_status_done':
      return <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'user_action':
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
    case 'user_message':
      return <UserRound className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
    case 'ai_response':
      return <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
    case 'ai_tool_status':
    case 'ai_tool_done':
      return <Wrench className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
    case 'ai_progress':
    case 'task_progress':
      return null
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
  const navigate = useNavigate()
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
        <RunProgressCard content={message.content} />
      </div>
    )
  }

  // Task progress card — compact multi-item progress (propagation, exports, etc.)
  if (message.type === 'task_progress') {
    return (
      <div className="py-1">
        <TaskProgressCard content={message.content} />
      </div>
    )
  }

  // Activity notes render as compact, subtle inline entries
  if (isActivity) {
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

  // Role display config for AI messages with speaker identity
  const roleConfig = message.speaker ? getRoleDisplay(message.speaker) : undefined
  const showRoleLabel = roleConfig && (message.type === 'ai_response' || message.type === 'ai_welcome' || message.type === 'ai_suggestion')

  // Role-identified AI messages use a full-width tinted bubble (no side icon)
  if (showRoleLabel) {
    const RoleIcon = roleConfig.icon
    return (
      <div className={cn('py-1.5')} data-role-speaker={message.speaker}>
        <div className={cn('rounded-lg px-3 py-2', roleConfig.bgClass)}>
          {/* Role/character label with icon + optional context chip */}
          <div className="flex items-center gap-1.5 mb-1">
            <RoleIcon className={cn('h-3 w-3 shrink-0', roleConfig.iconClass)} />
            {'isCharacter' in roleConfig && roleConfig.isCharacter ? (
              <button
                type="button"
                className={cn(
                  'text-[11px] font-medium cursor-pointer',
                  'hover:underline underline-offset-2',
                  roleConfig.badgeClass,
                )}
                onClick={() => {
                  navigate(`/${projectId}/characters/${roleConfig.characterId}`)
                }}
              >
                {roleConfig.name}
              </button>
            ) : (
              <span className={cn('text-[11px] font-medium', roleConfig.badgeClass)}>
                {roleConfig.name}
              </span>
            )}
            {message.pageContext && (() => {
              const CtxIcon = SECTION_ICONS[message.pageContext.toLowerCase().split(' ')[0]] ?? Sparkles
              return (
                <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-muted/60">
                  <CtxIcon className="h-3 w-3 text-muted-foreground/70 shrink-0" />
                  <span className="text-[11px] text-muted-foreground/80 truncate max-w-[160px]">
                    {message.pageContext}
                  </span>
                </span>
              )
            })()}
          </div>
          {/* Thinking indicator */}
          {isThinking && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
              <span>{roleConfig.name} is thinking...</span>
            </div>
          )}
          {/* Tool indicators */}
          {toolCalls && toolCalls.length > 0 && (
            <div className="space-y-1 mb-2">
              {toolCalls.map(tool => (
                <ToolIndicator key={tool.id} tool={tool} />
              ))}
            </div>
          )}
          {message.content ? (
            <div className="text-sm leading-relaxed prose prose-sm prose-invert max-w-none overflow-hidden break-words prose-p:my-1.5 prose-strong:text-foreground prose-em:text-foreground/90 prose-ul:my-1.5 prose-li:my-0.5 prose-headings:text-foreground prose-headings:mt-3 prose-headings:mb-1.5">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {isStreaming && <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse ml-0.5 align-text-bottom" />}
            </div>
          ) : isStreaming && !isThinking ? (
            <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse align-text-bottom" />
          ) : null}
          {showActions && message.preflightData && (
            <PreflightCard data={message.preflightData} />
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

  // Non-role messages: icon + content side by side
  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} speaker={message.speaker} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        {isThinking && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
            <span>Thinking...</span>
          </div>
        )}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-1 mb-2">
            {toolCalls.map(tool => (
              <ToolIndicator key={tool.id} tool={tool} />
            ))}
          </div>
        )}
        {message.type === 'ai_response' && message.content ? (
          <div className="text-sm leading-relaxed prose prose-sm prose-invert max-w-none overflow-hidden break-words prose-p:my-1.5 prose-strong:text-foreground prose-em:text-foreground/90 prose-ul:my-1.5 prose-li:my-0.5 prose-headings:text-foreground prose-headings:mt-3 prose-headings:mb-1.5">
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

const SECTION_ICONS: Record<string, React.ElementType> = {
  characters: Users,
  locations: MapPin,
  props: Package,
  scenes: Clapperboard,
}

// ---------------------------------------------------------------------------
// Interaction Mode Selector — small segmented control in chat header
// ---------------------------------------------------------------------------

const MODE_OPTIONS: { value: InteractionMode; label: string; tip: string }[] = [
  { value: 'guided', label: 'Guided', tip: 'Verbose, step-by-step explanations' },
  { value: 'balanced', label: 'Balanced', tip: 'Clear and concise (default)' },
  { value: 'expert', label: 'Expert', tip: 'Terse, action-oriented' },
]

function InteractionModeSelector({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const current: InteractionMode = project?.interaction_mode ?? 'balanced'

  const setMode = useCallback((mode: InteractionMode) => {
    if (mode === current) return
    // Optimistic update
    queryClient.setQueryData<ProjectSummary>(['projects', projectId], old => {
      if (!old) return old
      return { ...old, interaction_mode: mode }
    })
    // Persist
    updateProjectSettings(projectId, { interaction_mode: mode }).catch(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    })
  }, [projectId, current, queryClient])

  return (
    <div className="flex items-center rounded-md bg-muted/50 p-0.5">
      {MODE_OPTIONS.map(opt => (
        <Tooltip key={opt.value}>
          <TooltipTrigger asChild>
            <button
              onClick={() => setMode(opt.value)}
              className={cn(
                'px-2 py-0.5 text-[11px] font-medium rounded-sm transition-colors cursor-pointer',
                opt.value === current
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {opt.label}
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">{opt.tip}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}

export function ChatPanel() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const messages = useChatStore(s => s.messages[projectId ?? ''] ?? EMPTY_MESSAGES)
  const addMessage = useChatStore(s => s.addMessage)
  const entityContext = useChatStore(s => s.entityContext[projectId ?? ''] ?? null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  // True while the user is at (or near) the bottom of the chat. Used by the ResizeObserver
  // to decide whether to snap to bottom when content grows. Updated by the scroll listener.
  const shouldAutoScrollRef = useRef(true)
  const startRun = useStartRun()
  const { data: inputs } = useProjectInputs(projectId)
  const { data: characters } = useProjectCharacters(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const [inputText, setInputText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  // @-mention autocomplete state
  const [mentionQuery, setMentionQuery] = useState<string | null>(null)
  const [mentionIndex, setMentionIndex] = useState(0)
  const [mentionAnchor, setMentionAnchor] = useState<{ top: number; left: number } | null>(null)
  const mentionStartRef = useRef<number>(-1) // cursor position where @ was typed

  // Sticky role header — shows role name at top when scrolling through a long message
  const [stickyRole, setStickyRole] = useState<string | null>(null)

  // Custom drag-to-resize: drag handle at top of input, drag up = grow
  const MIN_INPUT_H = 100
  const MAX_INPUT_H = 400
  const [inputHeight, setInputHeight] = useState(MIN_INPUT_H)
  const dragRef = useRef<{ startY: number; startH: number } | null>(null)

  const onDragStart = (e: React.PointerEvent) => {
    e.preventDefault()
    dragRef.current = { startY: e.clientY, startH: inputHeight }
    const onMove = (ev: PointerEvent) => {
      if (!dragRef.current) return
      // Dragging UP (negative deltaY) = increase height
      const delta = dragRef.current.startY - ev.clientY
      setInputHeight(Math.max(MIN_INPUT_H, Math.min(MAX_INPUT_H, dragRef.current.startH + delta)))
    }
    const onUp = () => {
      dragRef.current = null
      document.removeEventListener('pointermove', onMove)
      document.removeEventListener('pointerup', onUp)
    }
    document.addEventListener('pointermove', onMove)
    document.addEventListener('pointerup', onUp)
  }

  // Auto-resize textarea to content height (ChatGPT-style)
  const autoResize = () => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    const scrollH = el.scrollHeight
    // Grow the container if content exceeds current height (up to max)
    if (scrollH > inputHeight) {
      setInputHeight(Math.min(scrollH, MAX_INPUT_H))
    }
    el.style.height = `${Math.min(scrollH, MAX_INPUT_H)}px`
  }

  // Build sectioned mention items: Shortcuts → Roles → Characters
  const mentionItems: MentionItem[] = useMemo(() => {
    if (mentionQuery === null) return []
    const q = mentionQuery.toLowerCase()
    const items: MentionItem[] = []

    // Shortcuts
    for (const s of MENTION_SHORTCUTS) {
      if (s.id.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)) {
        items.push({ kind: 'shortcut', id: s.id, name: s.name, description: s.description })
      }
    }
    // Roles
    for (const r of PICKABLE_ROLES) {
      const display = ROLE_DISPLAY[r]
      if (r.toLowerCase().includes(q) || display.name.toLowerCase().includes(q)) {
        items.push({ kind: 'role', id: r, name: display.name })
      }
    }
    // Characters
    if (characters) {
      for (const c of characters) {
        if (c.id.toLowerCase().includes(q) || c.name.toLowerCase().includes(q)) {
          items.push({ kind: 'character', id: c.id, name: c.name })
        }
      }
    }
    return items
  }, [mentionQuery, characters])

  // Detect @-mention trigger and update popup position
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInputText(value)

    const cursorPos = e.target.selectionStart ?? value.length
    // Look backward from cursor for an unmatched @
    const textBefore = value.slice(0, cursorPos)
    const atIdx = textBefore.lastIndexOf('@')
    if (atIdx !== -1 && !textBefore.slice(atIdx).includes(' ')) {
      // Active @-mention — extract query after @
      const query = textBefore.slice(atIdx + 1)
      mentionStartRef.current = atIdx
      setMentionQuery(query)
      setMentionIndex(0)

      // Position popup above the cursor using a mirror span
      const el = inputRef.current
      if (el) {
        const rect = el.getBoundingClientRect()
        const lines = textBefore.split('\n')
        const currentLine = lines.length - 1
        setMentionAnchor({
          top: rect.top - 4, // just above the textarea
          left: rect.left + Math.min((lines[currentLine]?.length ?? 0) * 7.5, rect.width - 100),
        })
      }
    } else {
      setMentionQuery(null)
      setMentionAnchor(null)
    }
  }

  // Insert a mention at the @ position, replacing the partial query
  const insertMention = (roleId: string) => {
    const start = mentionStartRef.current
    if (start < 0) return
    const cursorPos = inputRef.current?.selectionStart ?? inputText.length
    const before = inputText.slice(0, start)
    const after = inputText.slice(cursorPos)
    const newText = `${before}@${roleId} ${after}`
    setInputText(newText)
    setMentionQuery(null)
    setMentionAnchor(null)
    mentionStartRef.current = -1

    // Restore focus + cursor position after the inserted mention
    requestAnimationFrame(() => {
      const el = inputRef.current
      if (el) {
        el.focus()
        const pos = start + roleId.length + 2 // @roleId + space
        el.setSelectionRange(pos, pos)
      }
    })
  }

  // Handle keyboard navigation in mention popup
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Mention popup keyboard navigation
    if (mentionQuery !== null && mentionItems.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setMentionIndex(i => (i + 1) % mentionItems.length)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setMentionIndex(i => (i - 1 + mentionItems.length) % mentionItems.length)
        return
      }
      if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault()
        insertMention(mentionItems[mentionIndex].id)
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        setMentionQuery(null)
        setMentionAnchor(null)
        return
      }
    }

    // Normal Enter to send (Shift+Enter for newline)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSendMessage = async (overrideText?: string) => {
    const textToSend = overrideText ?? inputText.trim()
    if (!textToSend || !projectId || isStreaming) return

    const userText = textToSend
    // eslint-disable-next-line react-hooks/purity -- event handler, not render
    const now = Date.now()
    const userMsgId = `user_${now}`

    // Build page context from current URL (primary) or entity context store (fallback).
    // Reading directly from the URL avoids any store-timing edge cases after navigation.
    // Computed before addMessage so it can be persisted on the user message.
    const urlMatch = window.location.pathname.match(
      new RegExp(`^/${projectId}/(characters|locations|props|scenes)/([^/]+)$`),
    )
    let pageContext: string | undefined
    if (urlMatch) {
      const [, section, entityId] = urlMatch
      const entityName = entityId.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      pageContext = `User is viewing ${section}/${entityId} ("${entityName}")`
    } else {
      // Fallback: read from the store (covers edge cases where URL doesn't match)
      const entityCtx = useChatStore.getState().entityContext[projectId]
      pageContext = entityCtx
        ? `User is viewing ${entityCtx.section}/${entityCtx.entityId} ("${entityCtx.name}")`
        : undefined
    }

    // Add user message (include pageContext so it persists to chat.jsonl)
    addMessage(projectId, {
      id: userMsgId,
      type: 'user_message',
      content: userText,
      timestamp: now,
      ...(pageContext ? { pageContext } : {}),
    })

    if (!overrideText) setInputText('')
    setIsStreaming(true)
    const controller = new AbortController()
    abortRef.current = controller

    // Build full chat history for the AI (persistent thread) — include speaker
    const chatHistory = messages.map(m => ({
      type: m.type,
      content: m.content,
      ...(m.speaker ? { speaker: m.speaker } : {}),
    }))

    // Get active role for stickiness (no @-mention → route to last-addressed role)
    const activeRole = useChatStore.getState().getActiveRole(projectId)

    // Track the current streaming message ID — changes on role_start for multi-role
    let currentMsgId = ''
    let currentContent = ''
    const lastUserText = userText  // For retry on error

    // Create the first (or only) streaming placeholder
    const createStreamingMsg = (speaker?: string): string => {
      const msgId = `ai_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
      useChatStore.getState().addMessage(projectId, {
        id: msgId,
        type: 'ai_response',
        content: '',
        timestamp: Date.now(),
        streaming: true,
        speaker,
      })
      return msgId
    }

    currentMsgId = createStreamingMsg()
    currentContent = ''

    await streamChatMessage(
      projectId,
      userText,
      chatHistory,
      (chunk) => {
        const store = useChatStore.getState()

        if (chunk.type === 'role_start') {
          // New role starting — finalize previous message if it has content
          if (currentMsgId && currentContent) {
            store.finalizeStreamingMessage(projectId, currentMsgId)
          } else if (currentMsgId && !currentContent) {
            // Empty placeholder from before role_start arrived — discard it
            store.removeMessage(projectId, currentMsgId)
          }
          // Create a new streaming message for this role
          currentContent = ''
          currentMsgId = createStreamingMsg(chunk.speaker)
          // Update stickiness — this role is now the active one
          if (chunk.speaker) {
            store.setActiveRole(projectId, chunk.speaker)
          }
        } else if (chunk.type === 'role_done') {
          // Role finished — finalize its message
          if (currentMsgId) {
            store.finalizeStreamingMessage(projectId, currentMsgId)
            currentMsgId = ''
            currentContent = ''
          }
        } else if (chunk.type === 'text') {
          currentContent += chunk.content ?? ''
          store.updateMessageContent(projectId, currentMsgId, currentContent)
          // Set speaker on first text chunk if not set via role_start
          if (chunk.speaker && currentMsgId) {
            const msgs = store.messages[projectId] ?? []
            const msg = msgs.find(m => m.id === currentMsgId)
            if (msg && !msg.speaker) {
              store.updateMessageSpeaker(projectId, currentMsgId, chunk.speaker)
              store.setActiveRole(projectId, chunk.speaker)
            }
          }
        } else if (chunk.type === 'context_info') {
          // Store context as metadata on the message for chip rendering
          // Parse "User is viewing scenes/scene_004 ("Scene 004")" → "Scene 004"
          const ctxMatch = chunk.content?.match(/User is viewing (\w+)\/([\w_]+)\s*(?:\("([^"]+)"\))?/)
          const label = ctxMatch
            ? ctxMatch[2].replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
            : chunk.content ?? ''
          store.setMessageContext(projectId, currentMsgId, label)
        } else if (chunk.type === 'injected_content') {
          // Store the actual artifact content on the USER message that triggered it
          // (it's context about what the user is viewing, not metadata about the AI response).
          // Re-persist to backend so chat.jsonl records what was injected.
          store.setInjectedContent(projectId, userMsgId, chunk.content ?? '')
          // Read fresh state — `store` is a stale snapshot from before the set() call
          const updated = useChatStore.getState().messages[projectId]?.find(m => m.id === userMsgId)
          if (updated) {
            postChatMessage(projectId, updated).catch(() => {})
          }
        } else if (chunk.type === 'tool_start') {
          const rawName = chunk.name ?? 'tool'
          store.addToolCall(projectId, currentMsgId, {
            id: chunk.id ?? `tool_${Date.now()}`,
            name: rawName,
            displayName: friendlyToolName(rawName),
            done: false,
          })
        } else if (chunk.type === 'tool_result') {
          if (chunk.id) {
            store.completeToolCall(projectId, currentMsgId, chunk.id)
          }
        } else if (chunk.type === 'actions' && chunk.actions) {
          store.attachActions(projectId, currentMsgId, chunk.actions, chunk.preflight_data)
        }
      },
      () => {
        // Done — finalize any remaining streaming message
        if (currentMsgId) {
          useChatStore.getState().finalizeStreamingMessage(projectId, currentMsgId)
        }
        // Refresh artifact data — the AI may have generated new artifacts
        queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'artifacts'] })
        setIsStreaming(false)
      },
      (error) => {
        // Abort is intentional — just finalize quietly
        if (error.name === 'AbortError' || error.message === 'The user aborted a request.') {
          const store = useChatStore.getState()
          if (currentMsgId) {
            if (currentContent) {
              store.updateMessageContent(projectId, currentMsgId, currentContent + '\n\n*(stopped)*')
            } else {
              store.removeMessage(projectId, currentMsgId)
            }
            store.finalizeStreamingMessage(projectId, currentMsgId)
          }
          setIsStreaming(false)
          return
        }
        // Real error — show in the current AI message with retry affordance
        const errorContent = currentContent
          ? currentContent + '\n\n(Stream interrupted)'
          : `Sorry, something went wrong. ${error.message}`
        const store = useChatStore.getState()
        if (currentMsgId) {
          store.updateMessageContent(projectId, currentMsgId, errorContent)
          store.attachActions(projectId, currentMsgId, [
            { id: `retry_${Date.now()}`, label: 'Try Again', variant: 'outline', retry_text: lastUserText },
          ])
          store.finalizeStreamingMessage(projectId, currentMsgId)
        }
        setIsStreaming(false)
        toast.error(`Chat error: ${error.message}`)
      },
      pageContext,
      activeRole,
      controller.signal,
    )
  }

  const handleCancelStream = () => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
  }

  // Auto-scroll strategy: track user intent via a scroll listener, then snap to bottom
  // whenever content grows (ResizeObserver) if the user was at the bottom.
  //
  // Why not measure distFromBottom inside the ResizeObserver callback?
  //   When the RunProgressCard adds several stage rows at once, the content can grow
  //   200–300px in a single paint. By the time the observer fires, distFromBottom is
  //   already large, so the old "< 120px" check wrongly treats it as a user-scroll-up.
  //
  // The intent-ref approach: the scroll listener continuously tracks whether the user is
  // near the bottom (<120px). The ResizeObserver just reads that flag — it never re-measures
  // distance itself, so it's immune to large content jumps.
  useEffect(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (!viewport) return

    const onScroll = () => {
      const distFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
      shouldAutoScrollRef.current = distFromBottom < 120

      // Sticky role header: find the role message whose bubble overlaps the top of the viewport.
      // A role is "sticky" when its bubble starts above the viewport top AND ends below it —
      // meaning the user is scrolling through its content.
      const viewportTop = viewport.scrollTop
      const roleBubbles = viewport.querySelectorAll<HTMLElement>('[data-role-speaker]')
      let foundRole: string | null = null
      for (const bubble of roleBubbles) {
        const bubbleTop = bubble.offsetTop
        const bubbleBottom = bubbleTop + bubble.offsetHeight
        // The bubble's header is scrolled past the viewport top, but the bubble hasn't ended yet
        if (bubbleTop < viewportTop + 30 && bubbleBottom > viewportTop + 50) {
          foundRole = bubble.dataset.roleSpeaker ?? null
          break
        }
      }
      setStickyRole(foundRole)
    }

    const snapToBottom = () => {
      if (!shouldAutoScrollRef.current) return
      viewport.scrollTop = viewport.scrollHeight
    }

    // Snap immediately (e.g. on initial load while already at bottom)
    snapToBottom()

    const observer = new ResizeObserver(snapToBottom)
    const content = viewport.firstElementChild
    if (content) observer.observe(content)

    viewport.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      observer.disconnect()
      viewport.removeEventListener('scroll', onScroll)
    }
  }, [])

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

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Interaction mode selector bar */}
      {projectId && (
        <div className="flex items-center justify-end px-3 py-1.5 border-b border-border/30">
          <InteractionModeSelector projectId={projectId} />
        </div>
      )}
      <ScrollArea className="flex-1 min-h-0 relative" ref={scrollRef}>
        {/* Sticky role header — shows when scrolling through a long role message */}
        {stickyRole && (() => {
          const config = getRoleDisplay(stickyRole)
          const StickyIcon = config.icon
          return (
            <div className={cn(
              'sticky top-0 z-20 flex items-center gap-1.5 px-4 py-1',
              'border-b border-border/50 backdrop-blur-sm',
              config.bgClass,
            )}>
              <StickyIcon className={cn('h-3 w-3 shrink-0', config.iconClass)} />
              <span className={cn('text-[11px] font-medium', config.badgeClass)}>
                {config.name}
              </span>
            </div>
          )
        })()}
        <div className="px-3 pr-4 py-3 space-y-1 w-0 min-w-full">
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

      {/* @-mention autocomplete popup — sectioned: Shortcuts → Roles → Characters */}
      {mentionQuery !== null && mentionItems.length > 0 && mentionAnchor && (
        <div
          className="fixed z-50 rounded-lg border border-border bg-popover shadow-lg py-1 min-w-[220px] max-w-[300px] max-h-[320px] overflow-y-auto"
          style={{ bottom: `calc(100vh - ${mentionAnchor.top}px)`, left: mentionAnchor.left }}
        >
          {/* Render items with section headers when kind changes */}
          {mentionItems.map((item, i) => {
            const prevKind = i > 0 ? mentionItems[i - 1].kind : null
            const showHeader = item.kind !== prevKind
            const iconForItem = item.kind === 'shortcut'
              ? { Icon: Users, cls: 'text-violet-400' }
              : item.kind === 'character'
                ? { Icon: User, cls: 'text-amber-200' }
                : (() => { const c = getRoleDisplay(item.id); return { Icon: c.icon, cls: c.iconClass } })()
            return (
              <React.Fragment key={`${item.kind}-${item.id}`}>
                {showHeader && (
                  <div className="px-3 pt-1.5 pb-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60">
                    {item.kind === 'shortcut' ? 'Shortcuts' : item.kind === 'role' ? 'Roles' : 'Characters'}
                  </div>
                )}
                <button
                  type="button"
                  className={cn(
                    'flex items-center gap-2 w-full px-3 py-1.5 text-sm text-left',
                    'transition-colors cursor-pointer',
                    i === mentionIndex ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50',
                  )}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    insertMention(item.id)
                  }}
                  onMouseEnter={() => setMentionIndex(i)}
                >
                  <iconForItem.Icon className={cn('h-4 w-4 shrink-0', iconForItem.cls)} />
                  <span className="truncate">{item.name}</span>
                  <span className="text-xs text-muted-foreground ml-auto">@{item.id}</span>
                </button>
              </React.Fragment>
            )
          })}
        </div>
      )}
      {/* Chat input — input container with top-edge drag handle */}
      <div className="shrink-0 relative pb-2" style={{ height: inputHeight }}>
        {/* Top-edge drag handle — matches panel resize pill style */}
        <div
          onPointerDown={onDragStart}
          className="absolute -top-1 left-0 right-0 h-2 cursor-ns-resize hover:bg-primary/40 active:bg-primary/60 transition-colors z-10 flex items-center justify-center group"
        >
          <div className="w-8 h-1 rounded-full bg-border group-hover:bg-primary/50 transition-colors" />
        </div>
        <div
          className={cn(
            'relative flex flex-col h-full rounded-xl border border-border bg-background mx-2',
            'focus-within:ring-2 focus-within:ring-primary',
          )}
        >
          {/* Entity context chip — compact top-left pill */}
          {entityContext && (() => {
            const CtxIcon = SECTION_ICONS[entityContext.section] ?? Sparkles
            return (
              <div className="absolute top-1.5 left-2 z-10 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-muted/60">
                <CtxIcon className="h-3 w-3 text-muted-foreground/70 shrink-0" />
                <span
                  className="text-[11px] text-muted-foreground/80 hover:text-muted-foreground cursor-pointer truncate transition-colors max-w-[160px]"
                  onClick={() => navigate(`/${projectId}/${entityContext.section}/${entityContext.entityId}`)}
                >
                  {entityContext.name}
                </span>
              </div>
            )
          })()}
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onInput={autoResize}
            rows={1}
            placeholder="Ask about your project... (@ to mention roles or characters)"
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
            data-form-type="other"
            data-1p-ignore=""
            data-lpignore="true"
            className={cn(
              'flex-1 min-h-0 bg-transparent text-sm resize-none',
              'overflow-x-hidden overflow-y-auto',
              'focus:outline-none placeholder:text-muted-foreground leading-relaxed',
              entityContext ? 'pl-4 pr-10 pt-7 pb-3' : 'pl-4 pr-10 pt-2 pb-3',
            )}
          />
          {/* Send / Stop button — overlaid bottom-right */}
          {isStreaming ? (
            <Button
              size="icon"
              variant="destructive"
              onClick={handleCancelStream}
              className="absolute bottom-2 right-2 h-7 w-7 rounded-lg z-10"
              title="Stop response"
            >
              <Square className="h-3 w-3 fill-current" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim()}
              className="absolute bottom-2 right-2 h-7 w-7 rounded-lg z-10"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
