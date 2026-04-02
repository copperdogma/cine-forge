import { Activity, CheckCircle2, Loader2, MessageSquare, Sparkles, UserRound, Wrench } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useNavigate } from 'react-router-dom'
import { PreflightCard } from '@/components/PreflightCard'
import { RunProgressCard } from '@/components/RunProgressCard'
import { TaskProgressCard } from '@/components/TaskProgressCard'
import { PROJECT_MODEL_OPTIONS } from '@/lib/project-models'
import type { ChatMessage } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ActionButton, type StartRunAction } from './ActionButton'
import { getRoleDisplay, SECTION_ICONS } from './config'
import { ToolIndicator } from './ToolIndicator'

const MODEL_LABELS = new Map(PROJECT_MODEL_OPTIONS.map((option) => [option.value, option.label]))

function getModelLabel(model?: string | null): string | null {
  if (!model) return null
  const normalized = model.split(':').at(-1) ?? model
  return MODEL_LABELS.get(normalized) ?? normalized
}

function ModelBadge({ model }: { model?: string | null }) {
  const label = getModelLabel(model)
  if (!label || label === 'mock') return null

  return (
    <span
      className="inline-flex items-center rounded-md border border-border/50 bg-background/40 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
      title={model ?? undefined}
    >
      {label}
    </span>
  )
}

function MessageIcon({ type, speaker }: { type: ChatMessage['type']; speaker?: string }) {
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

type ChatMessageItemProps = {
  message: ChatMessage
  projectId: string
  actionTaken: boolean
  startRun: StartRunAction
  inputPath: string | undefined
  onRetry?: (text: string) => void
}

export function ChatMessageItem({
  message,
  projectId,
  actionTaken,
  startRun,
  inputPath,
  onRetry,
}: ChatMessageItemProps) {
  const navigate = useNavigate()
  const isUser = message.type === 'user_action' || message.type === 'user_message'
  const isActivity = message.type === 'activity'
  const showActions = message.actions && message.actions.length > 0 && !actionTaken
  const isStreaming = message.streaming
  const toolCalls = message.toolCalls
  const isThinking = isStreaming && !message.content && (!toolCalls || toolCalls.length === 0)

  if (message.type === 'ai_progress') {
    return (
      <div className="py-1">
        <RunProgressCard content={message.content} />
      </div>
    )
  }

  if (message.type === 'task_progress') {
    return (
      <div className="py-1">
        <TaskProgressCard content={message.content} />
      </div>
    )
  }

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

  const roleConfig = message.speaker ? getRoleDisplay(message.speaker) : undefined
  const showRoleLabel = roleConfig && (
    message.type === 'ai_response' || message.type === 'ai_welcome' || message.type === 'ai_suggestion'
  )
  const showGenericModelLabel = !showRoleLabel && (
    message.type === 'ai_response' || message.type === 'ai_welcome' || message.type === 'ai_suggestion'
  ) && !!message.model

  if (showRoleLabel) {
    const RoleIcon = roleConfig.icon
    return (
      <div className="py-1.5" data-role-speaker={message.speaker}>
        <div className={cn('rounded-lg px-3 py-2', roleConfig.bgClass)}>
          <div className="flex items-center gap-1.5 mb-1 flex-wrap">
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
            <ModelBadge model={message.model} />
            {message.pageContext && (() => {
              const ContextIcon = SECTION_ICONS[message.pageContext.toLowerCase().split(' ')[0]] ?? Sparkles
              return (
                <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-muted/60">
                  <ContextIcon className="h-3 w-3 text-muted-foreground/70 shrink-0" />
                  <span className="text-[11px] text-muted-foreground/80 truncate max-w-[160px]">
                    {message.pageContext}
                  </span>
                </span>
              )
            })()}
          </div>
          {isThinking && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
              <span>{roleConfig.name} is thinking...</span>
            </div>
          )}
          {toolCalls && toolCalls.length > 0 && (
            <div className="space-y-1 mb-2">
              {toolCalls.map((tool) => (
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
          {showActions && message.preflightData && <PreflightCard data={message.preflightData} />}
          {showActions && (
            <div className="flex flex-wrap gap-2 mt-2">
              {message.actions!.map((action) => (
                <ActionButton
                  key={action.id}
                  action={action}
                  messageId={message.id}
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

  return (
    <div className={cn('flex gap-2.5 py-2', isUser && 'flex-row-reverse')}>
      <MessageIcon type={message.type} speaker={message.speaker} />
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        {showGenericModelLabel && (
          <div className={cn('mb-1', isUser && 'flex justify-end')}>
            <ModelBadge model={message.model} />
          </div>
        )}
        {isThinking && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
            <span>Thinking...</span>
          </div>
        )}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-1 mb-2">
            {toolCalls.map((tool) => (
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
            {message.actions!.map((action) => (
              <ActionButton
                key={action.id}
                action={action}
                messageId={message.id}
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
