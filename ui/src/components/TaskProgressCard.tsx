import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Compact progress card for multi-item operations (propagation, export, etc.).
 * Rendered inside chat messages of type `task_progress`.
 *
 * Content format (JSON string):
 * {
 *   "heading": "Propagating creative intent",
 *   "items": [
 *     { "label": "Look & Feel", "status": "done", "detail": "draft created" },
 *     { "label": "Sound & Music", "status": "running" },
 *     { "label": "Rhythm & Flow", "status": "pending" }
 *   ]
 * }
 *
 * Statuses: "pending" | "running" | "done" | "failed"
 */

export type TaskProgressItem = {
  label: string
  status: 'pending' | 'running' | 'done' | 'failed'
  detail?: string
}

export type TaskProgressData = {
  heading: string
  items: TaskProgressItem[]
}

function ItemIcon({ status }: { status: string }) {
  switch (status) {
    case 'done':
      return <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0" />
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-primary shrink-0 animate-spin" />
    case 'failed':
      return <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
    default:
      return <Circle className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
  }
}

export function TaskProgressCard({ content }: { content: string }) {
  let data: TaskProgressData
  try {
    data = JSON.parse(content)
  } catch {
    return <span className="text-sm text-muted-foreground">{content}</span>
  }

  return (
    <div className="space-y-1 py-1">
      <p className="text-xs font-medium text-muted-foreground">{data.heading}</p>
      <div className="space-y-0.5">
        {data.items.map((item) => (
          <div
            key={item.label}
            className={cn(
              'flex items-center gap-2 text-sm py-0.5 transition-opacity duration-300',
              item.status === 'pending' && 'text-muted-foreground/40',
              item.status === 'done' && 'text-muted-foreground',
              item.status === 'running' && 'text-foreground',
              item.status === 'failed' && 'text-destructive',
            )}
          >
            <ItemIcon status={item.status} />
            <span>{item.label}</span>
            {item.detail && (
              <span className="text-xs text-muted-foreground/50">— {item.detail}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
