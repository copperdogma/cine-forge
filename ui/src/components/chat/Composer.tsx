import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Sparkles, Square, User, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { EntityContext } from '@/lib/chat-store'
import type { ChatCharacter } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  getRoleDisplay,
  MENTION_SHORTCUTS,
  PICKABLE_ROLES,
  SECTION_ICONS,
  type MentionItem,
} from './config'

type ComposerProps = {
  projectId?: string
  characters?: ChatCharacter[]
  entityContext: EntityContext | null
  inputText: string
  isStreaming: boolean
  onInputTextChange: (value: string) => void
  onSend: () => void
  onCancel: () => void
}

export function Composer({
  projectId,
  characters,
  entityContext,
  inputText,
  isStreaming,
  onInputTextChange,
  onSend,
  onCancel,
}: ComposerProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const mentionStartRef = useRef<number>(-1)
  const dragRef = useRef<{ startY: number; startH: number } | null>(null)
  const [mentionQuery, setMentionQuery] = useState<string | null>(null)
  const [mentionIndex, setMentionIndex] = useState(0)
  const [mentionAnchor, setMentionAnchor] = useState<{ top: number; left: number } | null>(null)

  const MIN_INPUT_H = 100
  const MAX_INPUT_H = 400
  const [inputHeight, setInputHeight] = useState(MIN_INPUT_H)

  const onDragStart = (event: React.PointerEvent) => {
    event.preventDefault()
    dragRef.current = { startY: event.clientY, startH: inputHeight }
    const onMove = (moveEvent: PointerEvent) => {
      if (!dragRef.current) return
      const delta = dragRef.current.startY - moveEvent.clientY
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

  const autoResize = () => {
    const element = inputRef.current
    if (!element) return
    element.style.height = 'auto'
    const scrollHeight = element.scrollHeight
    if (scrollHeight > inputHeight) {
      setInputHeight(Math.min(scrollHeight, MAX_INPUT_H))
    }
    element.style.height = `${Math.min(scrollHeight, MAX_INPUT_H)}px`
  }

  const mentionItems: MentionItem[] = useMemo(() => {
    if (mentionQuery === null) return []

    const query = mentionQuery.toLowerCase()
    const items: MentionItem[] = []

    for (const shortcut of MENTION_SHORTCUTS) {
      if (shortcut.id.toLowerCase().includes(query) || shortcut.name.toLowerCase().includes(query)) {
        items.push({
          kind: 'shortcut',
          id: shortcut.id,
          name: shortcut.name,
          description: shortcut.description,
        })
      }
    }

    for (const role of PICKABLE_ROLES) {
      const display = getRoleDisplay(role)
      if (role.toLowerCase().includes(query) || display.name.toLowerCase().includes(query)) {
        items.push({ kind: 'role', id: role, name: display.name })
      }
    }

    if (characters) {
      for (const character of characters) {
        if (
          character.id.toLowerCase().includes(query)
          || character.name.toLowerCase().includes(query)
        ) {
          items.push({ kind: 'character', id: character.id, name: character.name })
        }
      }
    }

    return items
  }, [mentionQuery, characters])

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value
    onInputTextChange(value)

    const cursorPos = event.target.selectionStart ?? value.length
    const textBefore = value.slice(0, cursorPos)
    const atIdx = textBefore.lastIndexOf('@')
    if (atIdx !== -1 && !textBefore.slice(atIdx).includes(' ')) {
      const query = textBefore.slice(atIdx + 1)
      mentionStartRef.current = atIdx
      setMentionQuery(query)
      setMentionIndex(0)

      const element = inputRef.current
      if (element) {
        const rect = element.getBoundingClientRect()
        const lines = textBefore.split('\n')
        const currentLine = lines.length - 1
        setMentionAnchor({
          top: rect.top - 4,
          left: rect.left + Math.min((lines[currentLine]?.length ?? 0) * 7.5, rect.width - 100),
        })
      }
    } else {
      setMentionQuery(null)
      setMentionAnchor(null)
    }
  }

  const insertMention = (roleId: string) => {
    const start = mentionStartRef.current
    if (start < 0) return

    const cursorPos = inputRef.current?.selectionStart ?? inputText.length
    const before = inputText.slice(0, start)
    const after = inputText.slice(cursorPos)
    const newText = `${before}@${roleId} ${after}`
    onInputTextChange(newText)
    setMentionQuery(null)
    setMentionAnchor(null)
    mentionStartRef.current = -1

    requestAnimationFrame(() => {
      const element = inputRef.current
      if (!element) return
      element.focus()
      const pos = start + roleId.length + 2
      element.setSelectionRange(pos, pos)
    })
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (mentionQuery !== null && mentionItems.length > 0) {
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        setMentionIndex((index) => (index + 1) % mentionItems.length)
        return
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault()
        setMentionIndex((index) => (index - 1 + mentionItems.length) % mentionItems.length)
        return
      }
      if (event.key === 'Tab' || event.key === 'Enter') {
        event.preventDefault()
        insertMention(mentionItems[mentionIndex].id)
        return
      }
      if (event.key === 'Escape') {
        event.preventDefault()
        setMentionQuery(null)
        setMentionAnchor(null)
        return
      }
    }

    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSend()
    }
  }

  return (
    <>
      {mentionQuery !== null && mentionItems.length > 0 && mentionAnchor && (
        <div
          className="fixed z-50 rounded-lg border border-border bg-popover shadow-lg py-1 min-w-[220px] max-w-[300px] max-h-[320px] overflow-y-auto"
          style={{ bottom: `calc(100vh - ${mentionAnchor.top}px)`, left: mentionAnchor.left }}
        >
          {mentionItems.map((item, index) => {
            const prevKind = index > 0 ? mentionItems[index - 1].kind : null
            const showHeader = item.kind !== prevKind
            const iconForItem = item.kind === 'shortcut'
              ? { Icon: Users, cls: 'text-violet-400' }
              : item.kind === 'character'
                ? { Icon: User, cls: 'text-amber-200' }
                : (() => {
                    const config = getRoleDisplay(item.id)
                    return { Icon: config.icon, cls: config.iconClass }
                  })()
            return (
              <div key={`${item.kind}-${item.id}`}>
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
                    index === mentionIndex ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50',
                  )}
                  onMouseDown={(event) => {
                    event.preventDefault()
                    insertMention(item.id)
                  }}
                  onMouseEnter={() => setMentionIndex(index)}
                >
                  <iconForItem.Icon className={cn('h-4 w-4 shrink-0', iconForItem.cls)} />
                  <span className="truncate">{item.name}</span>
                  <span className="text-xs text-muted-foreground ml-auto">@{item.id}</span>
                </button>
              </div>
            )
          })}
        </div>
      )}

      <div className="shrink-0 relative pb-2" style={{ height: inputHeight }}>
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
          {entityContext && (() => {
            const ContextIcon = SECTION_ICONS[entityContext.section] ?? Sparkles
            return (
              <div className="absolute top-1.5 left-2 z-10 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-muted/60">
                <ContextIcon className="h-3 w-3 text-muted-foreground/70 shrink-0" />
                <span
                  className="text-[11px] text-muted-foreground/80 hover:text-muted-foreground cursor-pointer truncate transition-colors max-w-[160px]"
                  onClick={() => {
                    if (projectId) {
                      navigate(`/${projectId}/${entityContext.section}/${entityContext.entityId}`)
                    }
                  }}
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
          {isStreaming ? (
            <Button
              size="icon"
              variant="destructive"
              onClick={onCancel}
              className="absolute bottom-2 right-2 h-7 w-7 rounded-lg z-10"
              title="Stop response"
            >
              <Square className="h-3 w-3 fill-current" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={onSend}
              disabled={!inputText.trim()}
              className="absolute bottom-2 right-2 h-7 w-7 rounded-lg z-10"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </>
  )
}
