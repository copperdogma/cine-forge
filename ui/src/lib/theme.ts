export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedThemeMode = 'light' | 'dark'
export type ThemePaletteId = 'obsidian' | 'ember' | 'slate' | 'noir'

export const DEFAULT_THEME_MODE: ThemeMode = 'system'
export const DEFAULT_THEME_PALETTE: ThemePaletteId = 'slate'

export const THEME_MODE_STORAGE_KEY = 'cineforge-mode'
export const THEME_PALETTE_STORAGE_KEY = 'cineforge-palette'
export const THEME_MODE_PREFERENCE_KEY = 'theme_mode'
export const THEME_PALETTE_PREFERENCE_KEY = 'theme_palette'

export const THEME_MODE_OPTIONS: Array<{
  value: ThemeMode
  label: string
  description: string
}> = [
  {
    value: 'light',
    label: 'Light',
    description: 'Use the selected light palette at all times.',
  },
  {
    value: 'dark',
    label: 'Dark',
    description: 'Use the selected dark palette at all times.',
  },
  {
    value: 'system',
    label: 'Auto',
    description: 'Follow your operating system appearance.',
  },
]

export const THEME_PALETTES: Record<
  ThemePaletteId,
  {
    id: ThemePaletteId
    name: string
    description: string
    lightLabel: string
    darkLabel: string
  }
> = {
  obsidian: {
    id: 'obsidian',
    name: 'Obsidian',
    description: 'Blue-steel contrast with cool slate neutrals.',
    lightLabel: 'Cool whites with blue-steel accents',
    darkLabel: 'Cool dark with blue-steel accents',
  },
  ember: {
    id: 'ember',
    name: 'Ember',
    description: 'Warm copper tones with amber highlights.',
    lightLabel: 'Warm whites with amber and copper accents',
    darkLabel: 'Warm dark with amber and copper accents',
  },
  slate: {
    id: 'slate',
    name: 'Slate',
    description: 'Neutral sage-teal baseline for the operator console.',
    lightLabel: 'Neutral whites with sage and teal accents',
    darkLabel: 'Neutral dark with sage and teal accents',
  },
  noir: {
    id: 'noir',
    name: 'Noir',
    description: 'Crisp monochrome with restrained gold emphasis.',
    lightLabel: 'Crisp whites with gold accents',
    darkLabel: 'Deep blacks with gold accents',
  },
}

export const THEME_PALETTE_ORDER = Object.keys(THEME_PALETTES) as ThemePaletteId[]

export function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system'
}

export function isResolvedThemeMode(value: unknown): value is ResolvedThemeMode {
  return value === 'light' || value === 'dark'
}

export function isThemePaletteId(value: unknown): value is ThemePaletteId {
  return value === 'obsidian' || value === 'ember' || value === 'slate' || value === 'noir'
}

export function sanitizeThemeMode(
  value: unknown,
  fallback: ThemeMode = DEFAULT_THEME_MODE,
): ThemeMode {
  return isThemeMode(value) ? value : fallback
}

export function sanitizeResolvedThemeMode(
  value: unknown,
  fallback: ResolvedThemeMode = 'light',
): ResolvedThemeMode {
  return isResolvedThemeMode(value) ? value : fallback
}

export function sanitizeThemePaletteId(
  value: unknown,
  fallback: ThemePaletteId = DEFAULT_THEME_PALETTE,
): ThemePaletteId {
  return isThemePaletteId(value) ? value : fallback
}

export function resolveThemeMode(mode: ThemeMode, systemMode: ResolvedThemeMode): ResolvedThemeMode {
  return mode === 'system' ? systemMode : mode
}
