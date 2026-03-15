/**
 * Shared page header — renders title + subtitle once.
 * Avoids the pattern of duplicating headers across loading/error/data states.
 */
import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  accessory?: ReactNode
}

export function PageHeader({ title, subtitle, accessory }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h1 className="mb-1 text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {accessory && <div className="shrink-0">{accessory}</div>}
    </div>
  )
}
