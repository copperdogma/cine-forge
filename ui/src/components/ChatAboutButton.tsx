import type { MouseEvent } from 'react'
import { MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { buildQuotedChatDraft, insertChatDraft } from '@/lib/chat-intents'
import { useRightPanel } from '@/lib/use-right-panel'

type ChatAboutButtonProps = {
  roleId: string
  prompt: string
  quote: string
  label?: string
  className?: string
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  stopPropagation?: boolean
}

export function ChatAboutButton({
  roleId,
  prompt,
  quote,
  label = 'Chat about this',
  className,
  variant = 'ghost',
  size = 'sm',
  stopPropagation = false,
}: ChatAboutButtonProps) {
  const panel = useRightPanel()

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    if (stopPropagation) event.stopPropagation()
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
