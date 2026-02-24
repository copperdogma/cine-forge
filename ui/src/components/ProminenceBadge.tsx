/**
 * Prominence tier badge for character entities.
 * Renders primary/secondary/minor with tier-appropriate styling.
 */
import { Crown, Star, User } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ProminenceBadgeProps {
  prominence: string | null | undefined
  className?: string
}

const config: Record<string, { label: string; icon: typeof Star; className: string }> = {
  primary: {
    label: 'Primary',
    icon: Crown,
    className: 'text-amber-400 border-amber-400/30',
  },
  secondary: {
    label: 'Secondary',
    icon: Star,
    className: 'text-blue-400 border-blue-400/30',
  },
  minor: {
    label: 'Minor',
    icon: User,
    className: 'text-muted-foreground border-muted-foreground/30',
  },
}

/** Renders a prominence tier badge. Returns null if prominence is falsy. */
export function ProminenceBadge({ prominence, className }: ProminenceBadgeProps) {
  if (!prominence) return null
  const tier = config[prominence]
  if (!tier) return null
  const Icon = tier.icon
  return (
    <Badge variant="outline" className={cn('text-xs gap-1', tier.className, className)}>
      <Icon className="h-3 w-3" />
      {tier.label}
    </Badge>
  )
}
