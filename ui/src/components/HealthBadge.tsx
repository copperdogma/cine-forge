/**
 * Shared health status badge — single source of truth for artifact health rendering.
 * Used by entity list pages, detail pages, and artifact pages.
 */
import { AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface HealthBadgeProps {
  health: string | null | undefined
  className?: string
}

/** Renders a health status badge. Returns null if health is falsy. */
export function HealthBadge({ health, className }: HealthBadgeProps) {
  if (!health) return null

  if (health === 'valid' || health === 'healthy') {
    return (
      <Badge variant="outline" className={cn('text-xs text-green-400 border-green-400/30', className)}>
        {health}
      </Badge>
    )
  }

  if (health === 'stale') {
    return (
      <Badge variant="outline" className={cn('text-xs text-amber-400 border-amber-400/30 gap-1', className)}>
        <AlertTriangle className="h-3 w-3" />
        Stale
      </Badge>
    )
  }

  if (health === 'needs_review') {
    return (
      <Badge variant="destructive" className={cn('text-xs', className)}>
        {health}
      </Badge>
    )
  }

  return (
    <Badge variant="destructive" className={cn('text-xs', className)}>
      {health}
    </Badge>
  )
}
