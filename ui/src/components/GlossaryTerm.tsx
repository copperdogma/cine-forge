import { HelpCircle } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { FILM_GLOSSARY, askChatQuestion } from '@/lib/glossary'
import { useRightPanel } from '@/lib/right-panel'

/**
 * GlossaryTerm — wraps text with a dotted underline and hover tooltip.
 * Click opens the chat panel and sends a contextual question to the AI.
 *
 * Usage:
 *   <GlossaryTerm term="narrative beats">Narrative Beats</GlossaryTerm>
 *   <GlossaryTerm term="INT">INT</GlossaryTerm>
 */
export function GlossaryTerm({
  term,
  context,
  children,
  className,
}: {
  /** The glossary key to look up (case-insensitive). */
  term: string
  /** Optional context for the AI question (e.g., "in scene 3"). */
  context?: string
  children: React.ReactNode
  className?: string
}) {
  const panel = useRightPanel()
  const definition = FILM_GLOSSARY[term] ?? FILM_GLOSSARY[term.toLowerCase()]

  if (!definition) {
    // No glossary entry — render children as-is
    return <>{children}</>
  }

  const handleClick = () => {
    // Open chat panel if closed
    if (!panel.state.open) panel.openChat()
    // Send a contextual question
    const q = context
      ? `What does "${term}" mean ${context}?`
      : `What does "${term}" mean in the context of this project?`
    askChatQuestion(q)
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={handleClick}
          className={`inline cursor-help border-b border-dotted border-muted-foreground/40 hover:border-muted-foreground transition-colors ${className ?? ''}`}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <div className="space-y-1">
          <p className="text-xs">{definition}</p>
          <p className="text-[10px] text-muted-foreground">Click to ask the AI more</p>
        </div>
      </TooltipContent>
    </Tooltip>
  )
}

/**
 * SectionHelp — a small ? icon that sends a contextual question to the chat.
 * Place next to section headers for "explain this section" affordance.
 *
 * Usage:
 *   <SectionHelp question="What are narrative beats and why do they matter?" />
 */
export function SectionHelp({
  question,
  tooltip,
}: {
  /** The question to send to the AI when clicked. */
  question: string
  /** Optional custom tooltip text. Defaults to "Ask the AI about this". */
  tooltip?: string
}) {
  const panel = useRightPanel()

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation() // Don't toggle the collapsible
    if (!panel.state.open) panel.openChat()
    askChatQuestion(question)
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={handleClick}
          className="inline-flex items-center justify-center h-4 w-4 rounded-full text-muted-foreground/40 hover:text-muted-foreground hover:bg-muted transition-colors cursor-help"
        >
          <HelpCircle className="h-3 w-3" />
        </button>
      </TooltipTrigger>
      <TooltipContent>
        <p className="text-xs">{tooltip ?? 'Ask the AI about this'}</p>
      </TooltipContent>
    </Tooltip>
  )
}
