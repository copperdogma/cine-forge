/**
 * Shared health status badge — single source of truth for artifact health rendering.
 * Used by entity list pages, detail pages, and artifact pages.
 */
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { healthDescription, healthLabel, mediaValidationStatus } from '@/lib/health'
import type { ArtifactHealthDetails } from '@/lib/types'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface HealthBadgeProps {
  health: string | null | undefined
  details?: ArtifactHealthDetails | null
  className?: string
}

/** Renders a health status badge. Returns null if health is falsy. */
export function HealthBadge({ health, details, className }: HealthBadgeProps) {
  if (!health) return null

  const validationStatus = mediaValidationStatus(health, details)
  const label = healthLabel(health, details)
  const description = healthDescription(health, details)

  if (validationStatus?.tone === 'pending') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={cn('text-xs text-amber-400 border-amber-400/30 gap-1', className)}>
              <AlertTriangle className="h-3 w-3" />
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (validationStatus?.tone === 'validated') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={cn('text-xs text-green-400 border-green-400/30', className)}>
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (validationStatus?.tone === 'failed') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="destructive" className={cn('text-xs gap-1', className)}>
              <AlertTriangle className="h-3 w-3" />
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (health === 'valid' || health === 'healthy') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={cn('text-xs text-green-400 border-green-400/30', className)}>
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (health === 'stale') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={cn('text-xs text-amber-400 border-amber-400/30 gap-1', className)}>
              <AlertTriangle className="h-3 w-3" />
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (health === 'needs_revision') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="destructive" className={cn('text-xs gap-1', className)}>
              <AlertTriangle className="h-3 w-3" />
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (health === 'confirmed_valid') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={cn('text-xs text-sky-300 border-sky-300/30 gap-1', className)}>
              <CheckCircle2 className="h-3 w-3" />
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (health === 'needs_review') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="destructive" className={cn('text-xs', className)}>
              {label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>{description}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="destructive" className={cn('text-xs', className)}>
            {label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p>{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
