/**
 * Shared page header — renders title + subtitle once.
 * Avoids the pattern of duplicating headers across loading/error/data states.
 */
interface PageHeaderProps {
  title: string
  subtitle?: string
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight mb-1">{title}</h1>
      {subtitle && (
        <p className="text-muted-foreground text-sm">{subtitle}</p>
      )}
    </div>
  )
}
