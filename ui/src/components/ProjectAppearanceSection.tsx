import { useQueryClient } from '@tanstack/react-query'
import { Monitor, Moon, Sun, Palette } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { updateProjectSettings } from '@/lib/api'
import { useAppTheme } from '@/lib/app-theme-context'
import {
  THEME_MODE_OPTIONS,
  THEME_MODE_PREFERENCE_KEY,
  THEME_PALETTES,
  THEME_PALETTE_ORDER,
  THEME_PALETTE_PREFERENCE_KEY,
  resolveThemeMode,
  type ThemeMode,
} from '@/lib/theme'
import type { ProjectSummary } from '@/lib/types'
import { cn } from '@/lib/utils'

type ProjectAppearanceSectionProps = {
  projectId: string
  project: ProjectSummary | undefined
}

const MODE_ICONS: Record<ThemeMode, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
}

export function ProjectAppearanceSection({
  projectId,
  project,
}: ProjectAppearanceSectionProps) {
  const queryClient = useQueryClient()
  const {
    mode,
    resolvedMode,
    palette,
    setMode,
    setPalette,
    previewPalette,
    clearPalettePreview,
  } = useAppTheme()

  const swatchMode = resolveThemeMode(mode, resolvedMode)

  async function persistPreference(update: Record<string, string>) {
    queryClient.setQueryData<ProjectSummary>(['projects', projectId], (old) => {
      if (!old) return old
      return {
        ...old,
        ui_preferences: {
          ...old.ui_preferences,
          ...update,
        },
      }
    })

    try {
      const updatedProject = await updateProjectSettings(projectId, {
        ui_preferences: update,
      })
      queryClient.setQueryData(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    } catch (error) {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      const message = error instanceof Error ? error.message : 'Failed to save appearance settings'
      toast.error(message)
    }
  }

  async function handleModeChange(nextMode: ThemeMode) {
    setMode(nextMode)
    await persistPreference({
      [THEME_MODE_PREFERENCE_KEY]: nextMode,
    })
  }

  async function handlePaletteChange(nextPalette: keyof typeof THEME_PALETTES) {
    setPalette(nextPalette)
    await persistPreference({
      [THEME_PALETTE_PREFERENCE_KEY]: nextPalette,
    })
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Palette className="size-4 text-primary" />
          <h3 className="text-sm font-semibold">Appearance</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Theme changes save directly to this project. If no project preference exists yet,
          CineForge falls back to Auto mode with the Slate palette.
        </p>
        {!project && (
          <Badge variant="outline">Project settings still loading</Badge>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Mode</label>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {THEME_MODE_OPTIONS.map((option) => {
            const Icon = MODE_ICONS[option.value]
            const active = mode === option.value
            return (
              <Button
                key={option.value}
                type="button"
                variant={active ? 'default' : 'outline'}
                className="h-auto items-start justify-start px-3 py-3 text-left"
                onClick={() => void handleModeChange(option.value)}
              >
                <span className="flex items-start gap-3">
                  <Icon className="mt-0.5 size-4 shrink-0" />
                  <span className="space-y-0.5">
                    <span className="block text-sm font-medium">{option.label}</span>
                    <span
                      className={cn(
                        'block text-xs',
                        active ? 'text-primary-foreground/80' : 'text-muted-foreground',
                      )}
                    >
                      {option.description}
                    </span>
                  </span>
                </span>
              </Button>
            )
          })}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <label className="text-sm font-medium">Palette</label>
          <p className="text-xs text-muted-foreground">
            Hover to preview, click to save.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {THEME_PALETTE_ORDER.map((paletteId) => {
            const definition = THEME_PALETTES[paletteId]
            const active = palette === paletteId

            return (
              <button
                key={paletteId}
                type="button"
                className={cn(
                  'rounded-xl border p-3 text-left transition-colors',
                  active
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'border-border hover:border-primary/40 hover:bg-accent/30',
                )}
                onClick={() => void handlePaletteChange(paletteId)}
                onMouseEnter={() => previewPalette(paletteId)}
                onMouseLeave={clearPalettePreview}
                onFocus={() => previewPalette(paletteId)}
                onBlur={clearPalettePreview}
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{definition.name}</span>
                      {active && <Badge>Selected</Badge>}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {swatchMode === 'dark' ? definition.darkLabel : definition.lightLabel}
                    </p>
                  </div>
                  <Badge variant="outline">{swatchMode === 'dark' ? 'Dark' : 'Light'}</Badge>
                </div>

                <div
                  data-theme-palette={paletteId}
                  className={cn(
                    'rounded-lg border border-border/70 bg-background p-3 text-foreground shadow-sm',
                    swatchMode === 'dark' && 'dark',
                  )}
                  style={{ colorScheme: swatchMode }}
                >
                  <div className="mb-3 flex items-center gap-2">
                    <span
                      className="size-4 rounded-md border"
                      style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
                    />
                    <span
                      className="size-4 rounded-md border"
                      style={{ backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' }}
                    />
                    <span
                      className="size-4 rounded-md border"
                      style={{ backgroundColor: 'var(--accent)', borderColor: 'var(--border)' }}
                    />
                    <span
                      className="size-4 rounded-md border"
                      style={{ backgroundColor: 'var(--sidebar)', borderColor: 'var(--sidebar-border)' }}
                    />
                  </div>

                  <div className="space-y-3">
                    <div className="rounded-md border border-border bg-card p-3">
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">Scene Workspace</span>
                        <Badge variant="secondary">Ready</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Quick check of surface, accent, and badge contrast.
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2 text-xs font-medium">
                      <span className="inline-flex h-8 items-center justify-center rounded-md bg-primary px-3 text-primary-foreground">
                        Generate
                      </span>
                      <span className="inline-flex h-8 items-center justify-center rounded-md bg-secondary px-3 text-secondary-foreground">
                        Review
                      </span>
                      <span className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-background px-3 text-foreground">
                        Outline
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
