import { CheckCircle2, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToolCallStatus } from '@/lib/types'

export function ToolIndicator({ tool }: { tool: ToolCallStatus }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Wrench className={cn('h-3.5 w-3.5 shrink-0', !tool.done && 'animate-pulse')} />
      <span>{tool.displayName}{tool.done ? '' : '...'}</span>
      {tool.done && <CheckCircle2 className="h-3 w-3 text-primary shrink-0" />}
    </div>
  )
}
