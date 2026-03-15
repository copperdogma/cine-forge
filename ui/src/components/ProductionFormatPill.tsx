import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowUpRight, ChevronDown, Film, Loader2, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { ProductionFormatModal } from '@/components/ProductionFormatModal'
import { getVisualMediumLabel } from '@/lib/production-format'
import { updateProjectSettings } from '@/lib/api'
import type { ProductionFormat, ProjectSummary } from '@/lib/types'

interface ProductionFormatPillProps {
  projectId: string
  value: ProductionFormat | null
  mode?: 'edit' | 'intent-link'
  className?: string
}

export function ProductionFormatPill({
  projectId,
  value,
  mode = 'edit',
  className,
}: ProductionFormatPillProps) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const updateFormatMutation = useMutation({
    mutationFn: (format: ProductionFormat) =>
      updateProjectSettings(projectId, { production_format: format }),
    onSuccess: (updatedProject) => {
      queryClient.setQueryData<ProjectSummary>(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Visual medium updated')
      setOpen(false)
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to update visual medium'
      toast.error(message)
    },
  })

  const handleSelect = (format: ProductionFormat) => {
    if (value && format === value) {
      setOpen(false)
      return
    }
    updateFormatMutation.mutate(format)
  }

  if (mode === 'intent-link') {
    if (!value) return null

    return (
      <Button
        asChild
        variant="outline"
        size="sm"
        className={className ?? 'h-7 rounded-full px-2.5 text-xs'}
      >
        <Link
          to={`/${projectId}/intent#visual-medium`}
          aria-label={`Edit visual medium in Intent & Mood. Current value: ${getVisualMediumLabel(value)}`}
          title="Edit visual medium in Intent & Mood"
        >
          <Film className="size-3.5" />
          {getVisualMediumLabel(value)}
          <ArrowUpRight className="size-3.5 opacity-70" />
        </Link>
      </Button>
    )
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className={className ?? 'h-8 rounded-full px-3 text-xs'}
        onClick={() => setOpen(true)}
        disabled={updateFormatMutation.isPending}
      >
        {updateFormatMutation.isPending ? (
          <Loader2 className="mr-1.5 size-3.5 animate-spin" />
        ) : value ? (
          <Film className="mr-1.5 size-3.5" />
        ) : (
          <Plus className="mr-1.5 size-3.5" />
        )}
        {value ? getVisualMediumLabel(value) : 'Choose visual medium'}
        <ChevronDown className="ml-1 size-3.5 opacity-70" />
      </Button>

      <ProductionFormatModal
        open={open}
        onOpenChange={setOpen}
        selectedFormat={value}
        pending={updateFormatMutation.isPending}
        title={value ? 'Change visual medium' : 'Choose a visual medium'}
        description="Set the project's base visual medium here, then use Intent & Mood to ground it with references and creative direction."
        onSelect={handleSelect}
      />
    </>
  )
}
