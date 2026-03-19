export type RenderArtifactRefView = {
  artifactType: string | null
  entityId: string | null
  version: number | null
}

export type RenderInputUsageView = {
  inputId: string
  kind: string | null
  label: string | null
  relativePath: string | null
  mediaType: string | null
  lockStatus: string | null
  required: boolean
  usedAs: string | null
  notes: string | null
  sourceRef: RenderArtifactRefView | null
}

const CHAT_ROLE_IDS = new Set([
  'assistant',
  'director',
  'editorial_architect',
  'visual_architect',
  'sound_designer',
  'story_editor',
])

export function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

export function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

export function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

export function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

export function asBoolean(value: unknown): boolean {
  return value === true
}

export function asStringArray(value: unknown): string[] {
  return asArray(value)
    .map(item => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

export function formatToken(value: string | null): string | null {
  if (!value) return null
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null
  if (Number.isInteger(seconds)) return `${seconds}s`
  return `${seconds.toFixed(1)}s`
}

export function formatMoney(amount: number | null): string | null {
  if (amount === null) return null
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function normalizeChatRole(roleId: string | null): string {
  if (roleId && CHAT_ROLE_IDS.has(roleId)) return roleId
  return 'director'
}

export function parseRenderInputUsage(value: unknown): RenderInputUsageView | null {
  const record = asRecord(value)
  if (!record) return null
  const sourceRef = asRecord(record.source_ref)
  return {
    inputId: asString(record.input_id) ?? 'input',
    kind: asString(record.kind),
    label: asString(record.label),
    relativePath: asString(record.relative_path),
    mediaType: asString(record.media_type),
    lockStatus: asString(record.lock_status),
    required: asBoolean(record.required),
    usedAs: asString(record.used_as),
    notes: asString(record.notes),
    sourceRef: sourceRef
      ? {
          artifactType: asString(sourceRef.artifact_type),
          entityId: asString(sourceRef.entity_id),
          version: asNumber(sourceRef.version),
        }
      : null,
  }
}
