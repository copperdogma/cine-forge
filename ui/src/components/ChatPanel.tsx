import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { ScrollArea } from '@/components/ui/scroll-area'
import { postChatMessage, streamChatMessage } from '@/lib/api'
import { useChatStore } from '@/lib/chat-store'
import { useProjectCharacters, useProjectInputs, useStartRun } from '@/lib/hooks'
import type { ChatMessage } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ChatMessageItem } from './chat/ChatMessageItem'
import { Composer } from './chat/Composer'
import { InteractionModeSelector } from './chat/InteractionModeSelector'
import { friendlyToolName, getRoleDisplay } from './chat/config'

const EMPTY_MESSAGES: ChatMessage[] = []

function buildPageContext(projectId: string): string | undefined {
  const urlMatch = window.location.pathname.match(
    new RegExp(`^/${projectId}/(characters|locations|props|scenes)/([^/]+)$`),
  )
  if (urlMatch) {
    const [, section, entityId] = urlMatch
    const entityName = entityId.replace(/[-_]/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    return `User is viewing ${section}/${entityId} ("${entityName}")`
  }

  const entityCtx = useChatStore.getState().entityContext[projectId]
  return entityCtx
    ? `User is viewing ${entityCtx.section}/${entityCtx.entityId} ("${entityCtx.name}")`
    : undefined
}

export function ChatPanel() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const messages = useChatStore((store) => store.messages[projectId ?? ''] ?? EMPTY_MESSAGES)
  const addMessage = useChatStore((store) => store.addMessage)
  const entityContext = useChatStore((store) => store.entityContext[projectId ?? ''] ?? null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const shouldAutoScrollRef = useRef(true)
  const abortRef = useRef<AbortController | null>(null)
  const startRun = useStartRun()
  const { data: inputs } = useProjectInputs(projectId)
  const { data: characters } = useProjectCharacters(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const [inputText, setInputText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [stickyRole, setStickyRole] = useState<string | null>(null)

  const handleSendMessage = async (overrideText?: string) => {
    const textToSend = overrideText ?? inputText.trim()
    if (!textToSend || !projectId || isStreaming) return

    const userText = textToSend
    const now = Date.now()
    const userMsgId = `user_${now}`
    const pageContext = buildPageContext(projectId)

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

    const chatHistory = messages.map((message) => ({
      type: message.type,
      content: message.content,
      ...(message.speaker ? { speaker: message.speaker } : {}),
    }))

    const activeRole = useChatStore.getState().getActiveRole(projectId)
    let currentMsgId = ''
    let currentContent = ''
    const lastUserText = userText

    const createStreamingMsg = (speaker?: string): string => {
      const messageId = `ai_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
      useChatStore.getState().addMessage(projectId, {
        id: messageId,
        type: 'ai_response',
        content: '',
        timestamp: Date.now(),
        streaming: true,
        speaker,
      })
      return messageId
    }

    currentMsgId = createStreamingMsg()

    await streamChatMessage(
      projectId,
      userText,
      chatHistory,
      (chunk) => {
        const store = useChatStore.getState()

        if (chunk.type === 'role_start') {
          if (currentMsgId && currentContent) {
            store.finalizeStreamingMessage(projectId, currentMsgId)
          } else if (currentMsgId && !currentContent) {
            store.removeMessage(projectId, currentMsgId)
          }
          currentContent = ''
          currentMsgId = createStreamingMsg(chunk.speaker)
          if (chunk.speaker) {
            store.setActiveRole(projectId, chunk.speaker)
          }
        } else if (chunk.type === 'role_done') {
          if (currentMsgId) {
            store.finalizeStreamingMessage(projectId, currentMsgId)
            currentMsgId = ''
            currentContent = ''
          }
        } else if (chunk.type === 'text') {
          currentContent += chunk.content ?? ''
          store.updateMessageContent(projectId, currentMsgId, currentContent)
          if (chunk.speaker && currentMsgId) {
            const activeMessages = store.messages[projectId] ?? []
            const activeMessage = activeMessages.find((message) => message.id === currentMsgId)
            if (activeMessage && !activeMessage.speaker) {
              store.updateMessageSpeaker(projectId, currentMsgId, chunk.speaker)
              store.setActiveRole(projectId, chunk.speaker)
            }
          }
        } else if (chunk.type === 'context_info') {
          const ctxMatch = chunk.content?.match(/User is viewing (\w+)\/([\w_]+)\s*(?:\("([^"]+)"\))?/)
          const label = ctxMatch
            ? ctxMatch[2].replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
            : chunk.content ?? ''
          store.setMessageContext(projectId, currentMsgId, label)
        } else if (chunk.type === 'injected_content') {
          store.setInjectedContent(projectId, userMsgId, chunk.content ?? '')
          const updated = useChatStore.getState().messages[projectId]?.find((message) => message.id === userMsgId)
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
        if (currentMsgId) {
          useChatStore.getState().finalizeStreamingMessage(projectId, currentMsgId)
        }
        queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'artifacts'] })
        setIsStreaming(false)
      },
      (error) => {
        if (error.name === 'AbortError' || error.message === 'The user aborted a request.') {
          const store = useChatStore.getState()
          if (currentMsgId) {
            if (currentContent) {
              store.updateMessageContent(projectId, currentMsgId, `${currentContent}\n\n*(stopped)*`)
            } else {
              store.removeMessage(projectId, currentMsgId)
            }
            store.finalizeStreamingMessage(projectId, currentMsgId)
          }
          setIsStreaming(false)
          return
        }

        const errorContent = currentContent
          ? `${currentContent}\n\n(Stream interrupted)`
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

  useEffect(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (!viewport) return

    const onScroll = () => {
      const distFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
      shouldAutoScrollRef.current = distFromBottom < 120

      const viewportTop = viewport.scrollTop
      const roleBubbles = viewport.querySelectorAll<HTMLElement>('[data-role-speaker]')
      let foundRole: string | null = null
      for (const bubble of roleBubbles) {
        const bubbleTop = bubble.offsetTop
        const bubbleBottom = bubbleTop + bubble.offsetHeight
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

  useEffect(() => {
    const handler = (event: Event) => {
      const question = (event as CustomEvent).detail?.question
      if (question && !isStreaming) {
        handleSendMessage(question)
      }
    }
    window.addEventListener('cineforge:ask', handler)
    return () => window.removeEventListener('cineforge:ask', handler)
  })

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {projectId && (
        <div className="flex items-center justify-end px-3 py-1.5 border-b border-border/30">
          <InteractionModeSelector projectId={projectId} />
        </div>
      )}
      <ScrollArea className="flex-1 min-h-0 relative" ref={scrollRef}>
        {stickyRole && (() => {
          const config = getRoleDisplay(stickyRole)
          const StickyIcon = config.icon
          return (
            <div
              className={cn(
                'sticky top-0 z-20 flex items-center gap-1.5 px-4 py-1',
                'border-b border-border/50 backdrop-blur-sm',
                config.bgClass,
              )}
            >
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
            messages.map((message, index) => {
              const actionTaken = !!(
                message.needsAction
                && messages.slice(index + 1).some((nextMessage) => nextMessage.type === 'user_action')
              )
              return (
                <ChatMessageItem
                  key={message.id}
                  message={message}
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
      <Composer
        projectId={projectId}
        characters={characters}
        entityContext={entityContext}
        inputText={inputText}
        isStreaming={isStreaming}
        onInputTextChange={setInputText}
        onSend={() => handleSendMessage()}
        onCancel={handleCancelStream}
      />
    </div>
  )
}
