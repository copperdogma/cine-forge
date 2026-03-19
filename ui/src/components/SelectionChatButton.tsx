import type { MouseEvent, RefObject } from 'react'
import { MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { buildQuotedChatDraft, insertChatDraft } from '@/lib/chat-intents'
import { useRightPanel } from '@/lib/right-panel'

type SelectionChatButtonProps = {
  roleId: string
  prompt: string
  fallbackQuote: string
  selectionRootRef: RefObject<HTMLElement | null>
  label?: string
  className?: string
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

function selectedTextWithin(root: HTMLElement | null): string {
  if (!root || typeof window === 'undefined') return ''
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return ''
  const anchorNode = selection.anchorNode
  const focusNode = selection.focusNode
  if (!anchorNode || !focusNode) return ''
  if (!root.contains(anchorNode) || !root.contains(focusNode)) return ''
  return selection.toString().trim()
}

export function SelectionChatButton({
  roleId,
  prompt,
  fallbackQuote,
  selectionRootRef,
  label = 'Chat about this',
  className,
  variant = 'ghost',
  size = 'sm',
}: SelectionChatButtonProps) {
  const panel = useRightPanel()

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    const quote = selectedTextWithin(selectionRootRef.current) || fallbackQuote
    const draft = buildQuotedChatDraft({ roleId, prompt, quote })
    if (!panel.state.open) {
      panel.openChatWithIntent({ mode: 'draft', text: draft })
      return
    }
    insertChatDraft(draft)
  }

  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      onClick={handleClick}
    >
      <MessageSquare className="h-3 w-3" />
      {label}
    </Button>
  )
}
