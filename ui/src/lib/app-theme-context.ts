import { createContext, useContext } from 'react'

import type { ResolvedThemeMode, ThemeMode, ThemePaletteId } from '@/lib/theme'

export type AppThemeContextValue = {
  mode: ThemeMode
  resolvedMode: ResolvedThemeMode
  palette: ThemePaletteId
  setMode: (mode: ThemeMode) => void
  setPalette: (palette: ThemePaletteId) => void
  previewPalette: (palette: ThemePaletteId) => void
  clearPalettePreview: () => void
}

export const AppThemeContext = createContext<AppThemeContextValue | null>(null)

export function useAppTheme() {
  const context = useContext(AppThemeContext)
  if (!context) {
    throw new Error('useAppTheme must be used within AppThemeProvider')
  }
  return context
}
