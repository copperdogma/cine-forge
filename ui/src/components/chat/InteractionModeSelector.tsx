import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { updateProjectSettings } from '@/lib/api'
import { useProject } from '@/lib/hooks'
import type { ProjectSummary, InteractionMode } from '@/lib/types'
import { cn } from '@/lib/utils'
import { MODE_OPTIONS } from './config'

export function InteractionModeSelector({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const current: InteractionMode = project?.interaction_mode ?? 'balanced'

  const setMode = useCallback((mode: InteractionMode) => {
    if (mode === current) return

    queryClient.setQueryData<ProjectSummary>(['projects', projectId], (old) => {
      if (!old) return old
      return { ...old, interaction_mode: mode }
    })

    updateProjectSettings(projectId, { interaction_mode: mode }).catch(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    })
  }, [projectId, current, queryClient])

  return (
    <div className="flex items-center rounded-md bg-muted/50 p-0.5">
      {MODE_OPTIONS.map((option) => (
        <Tooltip key={option.value}>
          <TooltipTrigger asChild>
            <button
              onClick={() => setMode(option.value)}
              className={cn(
                'px-2 py-0.5 text-[11px] font-medium rounded-sm transition-colors cursor-pointer',
                option.value === current
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {option.label}
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">{option.tip}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}
