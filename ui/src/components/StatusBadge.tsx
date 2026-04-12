/** Shared pipeline status badge and icon — single source of truth. */
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  PauseCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'

/** Returns the appropriate icon component for a pipeline status. */
export function StatusIcon({ status, className }: { status: string; className?: string }) {
  const size = className ?? 'h-4 w-4'
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return <CheckCircle2 className={`${size} text-primary`} />
    case 'failed':
      return <XCircle className={`${size} text-destructive`} />
    case 'running':
      return <Loader2 className={`${size} text-primary animate-spin`} />
    case 'paused':
      return <PauseCircle className={`${size} text-amber-400`} />
    default:
      return <Clock className={`${size} text-muted-foreground`} />
  }
}

/** Returns a styled Badge for a pipeline run/stage status. */
export function StatusBadge({ status }: { status: string }) {
  if (status === 'done' || status === 'skipped_reused') {
    return (
      <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-primary/20">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        {status === 'done' ? 'Done' : 'Reused'}
      </Badge>
    )
  }
  if (status === 'failed') {
    return (
      <Badge variant="destructive" className="text-xs">
        <XCircle className="h-3 w-3 mr-1" />
        Failed
      </Badge>
    )
  }
  if (status === 'running') {
    return (
      <Badge variant="secondary" className="text-xs">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Running
      </Badge>
    )
  }
  if (status === 'paused') {
    return (
      <Badge variant="secondary" className="text-xs bg-amber-400/10 text-amber-400 border-amber-400/20">
        <PauseCircle className="h-3 w-3 mr-1" />
        Paused
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="text-xs">
      <Clock className="h-3 w-3 mr-1" />
      {status}
    </Badge>
  )
}
