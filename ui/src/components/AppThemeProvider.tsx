import {
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import { ThemeProvider, useTheme } from 'next-themes'
import { matchPath, useLocation } from 'react-router-dom'

import { useProject } from '@/lib/hooks'
import { AppThemeContext, type AppThemeContextValue } from '@/lib/app-theme-context'
import {
  DEFAULT_THEME_MODE,
  DEFAULT_THEME_PALETTE,
  THEME_MODE_PREFERENCE_KEY,
  THEME_MODE_STORAGE_KEY,
  THEME_PALETTE_PREFERENCE_KEY,
  THEME_PALETTE_STORAGE_KEY,
  sanitizeResolvedThemeMode,
  sanitizeThemeMode,
  sanitizeThemePaletteId,
  type ThemePaletteId,
} from '@/lib/theme'

const NON_PROJECT_ROUTES = new Set(['new', 'theme'])

function readCachedPalette(): ThemePaletteId {
  if (typeof document !== 'undefined') {
    const attrValue = document.documentElement.dataset.themePalette
    if (attrValue) {
      return sanitizeThemePaletteId(attrValue)
    }
  }

  if (typeof window !== 'undefined') {
    try {
      return sanitizeThemePaletteId(window.localStorage.getItem(THEME_PALETTE_STORAGE_KEY))
    } catch {
      return DEFAULT_THEME_PALETTE
    }
  }

  return DEFAULT_THEME_PALETTE
}

function getProjectIdFromPath(pathname: string): string | undefined {
  const exactMatch = matchPath('/:projectId', pathname)
  const nestedMatch = matchPath('/:projectId/*', pathname)
  const projectId = exactMatch?.params.projectId ?? nestedMatch?.params.projectId
  if (!projectId || NON_PROJECT_ROUTES.has(projectId)) {
    return undefined
  }
  return projectId
}

function ThemeStateController({ children }: PropsWithChildren) {
  const location = useLocation()
  const projectId = useMemo(() => getProjectIdFromPath(location.pathname), [location.pathname])
  const { data: project, isFetched, isError } = useProject(projectId)
  const { theme, resolvedTheme, setTheme } = useTheme()
  const [palette, setPaletteState] = useState<ThemePaletteId>(() => readCachedPalette())
  const [previewPalette, setPreviewPalette] = useState<ThemePaletteId | null>(null)

  const mode = sanitizeThemeMode(theme)
  const resolvedMode = sanitizeResolvedThemeMode(resolvedTheme)
  const appliedPalette = previewPalette ?? palette

  useEffect(() => {
    document.documentElement.dataset.themePalette = appliedPalette
  }, [appliedPalette])

  useEffect(() => {
    document.documentElement.style.colorScheme = resolvedMode
  }, [resolvedMode])

  useEffect(() => {
    try {
      window.localStorage.setItem(THEME_PALETTE_STORAGE_KEY, palette)
    } catch {
      // Local storage is only a fast cache for bootstrap restore.
    }
  }, [palette])

  useEffect(() => {
    if (!projectId) {
      return
    }
    if (!isFetched && !isError) {
      return
    }

    const nextMode = sanitizeThemeMode(
      project?.ui_preferences?.[THEME_MODE_PREFERENCE_KEY],
      DEFAULT_THEME_MODE,
    )
    const nextPalette = sanitizeThemePaletteId(
      project?.ui_preferences?.[THEME_PALETTE_PREFERENCE_KEY],
      DEFAULT_THEME_PALETTE,
    )

    if (mode !== nextMode) {
      setTheme(nextMode)
    }
    if (palette !== nextPalette || previewPalette !== null) {
      const raf = requestAnimationFrame(() => {
        if (palette !== nextPalette) {
          setPaletteState(nextPalette)
        }
        if (previewPalette !== null) {
          setPreviewPalette(null)
        }
      })
      return () => cancelAnimationFrame(raf)
    }
  }, [
    isError,
    isFetched,
    mode,
    palette,
    previewPalette,
    project?.ui_preferences,
    projectId,
    setTheme,
  ])

  const value = useMemo<AppThemeContextValue>(
    () => ({
      mode,
      resolvedMode,
      palette,
      setMode: (nextMode) => setTheme(sanitizeThemeMode(nextMode)),
      setPalette: (nextPalette) => {
        setPreviewPalette(null)
        setPaletteState(sanitizeThemePaletteId(nextPalette))
      },
      previewPalette: (nextPalette) => setPreviewPalette(sanitizeThemePaletteId(nextPalette)),
      clearPalettePreview: () => setPreviewPalette(null),
    }),
    [mode, palette, resolvedMode, setTheme],
  )

  return <AppThemeContext.Provider value={value}>{children}</AppThemeContext.Provider>
}

export function AppThemeProvider({ children }: PropsWithChildren) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme={DEFAULT_THEME_MODE}
      disableTransitionOnChange
      enableSystem
      storageKey={THEME_MODE_STORAGE_KEY}
    >
      <ThemeStateController>{children}</ThemeStateController>
    </ThemeProvider>
  )
}
