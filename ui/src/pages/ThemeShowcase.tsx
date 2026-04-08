import { Monitor, Moon, Palette, Sun } from 'lucide-react'

import { useAppTheme } from '@/lib/app-theme-context'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
  THEME_MODE_OPTIONS,
  THEME_PALETTES,
  THEME_PALETTE_ORDER,
  resolveThemeMode,
  type ResolvedThemeMode,
  type ThemeMode,
  type ThemePaletteId,
} from '@/lib/theme'
import { cn } from '@/lib/utils'

const MODE_ICONS: Record<ThemeMode, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
}

function ThemePreview({
  paletteId,
  mode,
  title,
}: {
  paletteId: ThemePaletteId
  mode: ResolvedThemeMode
  title: string
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          {title}
        </span>
        <Badge variant="outline">{mode === 'dark' ? 'Dark' : 'Light'}</Badge>
      </div>

      <div
        data-theme-palette={paletteId}
        className={cn(
          'overflow-hidden rounded-xl border border-border/70 bg-background text-foreground shadow-sm',
          mode === 'dark' && 'dark',
        )}
        style={{ colorScheme: mode }}
      >
        <div className="flex items-center gap-2 border-b border-border bg-sidebar px-4 py-3">
          <span className="text-sm font-semibold">CineForge</span>
          <Badge variant="secondary">Inbox 3</Badge>
          <div className="ml-auto flex items-center gap-2">
            <span
              className="size-3 rounded-full border"
              style={{ backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' }}
            />
            <span
              className="size-3 rounded-full border"
              style={{ backgroundColor: 'var(--accent)', borderColor: 'var(--border)' }}
            />
          </div>
        </div>

        <div className="grid gap-4 p-4 lg:grid-cols-[0.7fr_1fr]">
          <div className="space-y-2 rounded-lg border border-border bg-card p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Navigator
            </p>
            {['Script', 'Scenes', 'Characters', 'Inbox'].map((item, index) => (
              <div
                key={item}
                className={cn(
                  'rounded-md px-3 py-2 text-sm',
                  index === 1 ? 'bg-accent text-accent-foreground' : 'text-muted-foreground',
                )}
              >
                {item}
              </div>
            ))}
          </div>

          <div className="space-y-3">
            <Card className="border-border shadow-none">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">Scene Workspace</CardTitle>
                    <CardDescription>Generate → react → refine loop</CardDescription>
                  </div>
                  <Badge>Ready</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input defaultValue="The confession needs more tension." />
                <div className="flex flex-wrap gap-2">
                  <Button size="sm">Generate</Button>
                  <Button size="sm" variant="secondary">
                    Review
                  </Button>
                  <Button size="sm" variant="outline">
                    Explain
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Background
                </p>
                <div
                  className="mt-3 h-12 rounded-md border"
                  style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
                />
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Primary
                </p>
                <div
                  className="mt-3 h-12 rounded-md border"
                  style={{ backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' }}
                />
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Accent
                </p>
                <div
                  className="mt-3 h-12 rounded-md border"
                  style={{ backgroundColor: 'var(--accent)', borderColor: 'var(--border)' }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ThemeShowcase() {
  const {
    mode,
    resolvedMode,
    palette,
    setMode,
    setPalette,
    previewPalette,
    clearPalettePreview,
  } = useAppTheme()

  const effectiveMode = resolveThemeMode(mode, resolvedMode)

  return (
    <div className="min-h-screen bg-background px-4 py-8 text-foreground sm:px-8">
      <div className="mx-auto max-w-7xl space-y-10">
        <section className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Palette className="size-5 text-primary" />
                <Badge variant="outline">Shared Theme System</Badge>
              </div>
              <h1 className="text-3xl font-semibold tracking-tight">CineForge Appearance</h1>
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                This page now previews the same palette system the app uses. Project settings are
                still the canonical source of truth on project routes; this screen is a shared
                visual reference and live smoke surface.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">Current:</span>
                <Badge>{THEME_PALETTES[palette].name}</Badge>
                <Badge variant="secondary">
                  {mode === 'system' ? `Auto → ${effectiveMode}` : effectiveMode}
                </Badge>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Mode</CardTitle>
                <CardDescription>Switch the live shell between light, dark, and auto.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-3">
                {THEME_MODE_OPTIONS.map((option) => {
                  const Icon = MODE_ICONS[option.value]
                  const active = option.value === mode

                  return (
                    <Button
                      key={option.value}
                      type="button"
                      variant={active ? 'default' : 'outline'}
                      className="h-auto items-start justify-start px-3 py-3 text-left"
                      onClick={() => setMode(option.value)}
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
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Palette</CardTitle>
                <CardDescription>
                  Hover to preview the live shell, click to keep this palette in the local cache.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
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
                      onClick={() => setPalette(paletteId)}
                      onMouseEnter={() => previewPalette(paletteId)}
                      onMouseLeave={clearPalettePreview}
                      onFocus={() => previewPalette(paletteId)}
                      onBlur={clearPalettePreview}
                    >
                      <div className="mb-3 flex items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{definition.name}</span>
                            {active && <Badge>Selected</Badge>}
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
                        </div>
                        <Badge variant="outline">{effectiveMode}</Badge>
                      </div>

                      <div
                        data-theme-palette={paletteId}
                        className={cn(
                          'rounded-lg border border-border/70 bg-background p-3',
                          effectiveMode === 'dark' && 'dark',
                        )}
                        style={{ colorScheme: effectiveMode }}
                      >
                        <div className="flex items-center gap-2">
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
                      </div>
                    </button>
                  )
                })}
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        <section className="space-y-5">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold tracking-tight">Palette Matrix</h2>
            <p className="text-sm text-muted-foreground">
              Every palette previews both the light and dark treatment from the same shared token
              source.
            </p>
          </div>

          <div className="grid gap-6">
            {THEME_PALETTE_ORDER.map((paletteId) => {
              const definition = THEME_PALETTES[paletteId]

              return (
                <section key={paletteId} className="space-y-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">{definition.name}</h3>
                      {palette === paletteId && <Badge>Active</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">{definition.description}</p>
                  </div>

                  <div className="grid gap-4 xl:grid-cols-2">
                    <ThemePreview paletteId={paletteId} mode="light" title={definition.lightLabel} />
                    <ThemePreview paletteId={paletteId} mode="dark" title={definition.darkLabel} />
                  </div>
                </section>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}
