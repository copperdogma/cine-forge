import { ArrowDownAZ, ArrowUpDown, BarChart3, ChevronDown, ChevronUp, LayoutGrid, LayoutList, Rows3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { type SortMode, type SortDirection, type ViewDensity } from '@/lib/types'

interface EntityListControlsProps {
  sort: SortMode
  direction: SortDirection
  onSortChange: (sort: SortMode) => void
  onDirectionChange: (direction: SortDirection) => void
  density: ViewDensity
  onDensityChange: (density: ViewDensity) => void
}

const sortOptions: Array<{ value: SortMode; label: string; icon: typeof ArrowUpDown }> = [
  { value: 'script-order', label: 'Script Order', icon: ArrowUpDown },
  { value: 'alphabetical', label: 'A\u2013Z', icon: ArrowDownAZ },
  { value: 'prominence', label: 'Prominence', icon: BarChart3 },
]

const densityOptions: Array<{ value: ViewDensity; icon: typeof LayoutList }> = [
  { value: 'compact', icon: LayoutList },
  { value: 'medium', icon: Rows3 },
  { value: 'large', icon: LayoutGrid },
]

export function EntityListControls({
  sort,
  direction,
  onSortChange,
  onDirectionChange,
  density,
  onDensityChange,
}: EntityListControlsProps) {
  function handleSortClick(mode: SortMode) {
    if (mode === sort) {
      onDirectionChange(direction === 'asc' ? 'desc' : 'asc')
    } else {
      onSortChange(mode)
      onDirectionChange('asc')
    }
  }

  return (
    <div className="flex items-center justify-between gap-4">
      {/* Sort toggles */}
      <div className="flex items-center gap-1 rounded-lg border border-border p-0.5">
        {sortOptions.map(opt => {
          const Icon = opt.icon
          const isActive = sort === opt.value
          const DirIcon = direction === 'asc' ? ChevronUp : ChevronDown
          return (
            <Button
              key={opt.value}
              variant="ghost"
              size="sm"
              className={cn(
                'h-7 gap-1.5 px-2.5 text-xs',
                isActive && 'bg-accent text-accent-foreground',
              )}
              onClick={() => handleSortClick(opt.value)}
            >
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{opt.label}</span>
              {isActive && <DirIcon className="h-3 w-3 opacity-60" />}
            </Button>
          )
        })}
      </div>

      {/* Density toggles */}
      <div className="flex items-center gap-1 rounded-lg border border-border p-0.5">
        {densityOptions.map(opt => {
          const Icon = opt.icon
          return (
            <Button
              key={opt.value}
              variant="ghost"
              size="sm"
              className={cn(
                'h-7 w-7 p-0',
                density === opt.value && 'bg-accent text-accent-foreground',
              )}
              onClick={() => onDensityChange(opt.value)}
            >
              <Icon className="h-3.5 w-3.5" />
            </Button>
          )
        })}
      </div>
    </div>
  )
}
