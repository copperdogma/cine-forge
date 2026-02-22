/**
 * Shared pipeline status badge and icon — single source of truth.
 * Consolidates statusBadge(), statusIcon(), and getStatusConfig() from
 * ProjectRuns, RunDetail, and ProjectHome.
 */
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

/** Config object for status — icon, label, className. Used by ProjectHome. */
export function getStatusConfig(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return {
        icon: CheckCircle2,
        label: status === 'done' ? 'Done' : 'Reused',
        className: 'bg-green-500/20 text-green-400 border-green-500/30',
      }
    case 'failed':
      return {
        icon: XCircle,
        label: 'Failed',
        className: 'bg-red-500/20 text-red-400 border-red-500/30',
      }
    case 'running':
      return {
        icon: Loader2,
        label: 'Running',
        className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      }
    case 'paused':
      return {
        icon: PauseCircle,
        label: 'Paused',
        className: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      }
    default:
      return {
        icon: Clock,
        label: 'Pending',
        className: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
      }
  }
}
