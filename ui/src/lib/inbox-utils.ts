/**
 * Shared inbox item ID builders — used by both ProjectInbox and AppShell
 * to ensure read/unread IDs match across components. Story 069.
 */

export function staleItemId(artifactType: string, entityId: string | null): string {
  return `stale-${artifactType}-${entityId ?? 'null'}`
}

export function errorItemId(runId: string): string {
  return `error-${runId}`
}

export function reviewItemId(artifactType: string, entityId: string | null, version: number): string {
  return `review-${artifactType}-${entityId ?? 'null'}-v${version}`
}

export function gateItemId(entityId: string | null): string {
  return `gate-${entityId ?? 'null'}`
}

/** Parse read inbox IDs from project ui_preferences (JSON string → string[]). */
export function parseReadIds(raw: string | undefined): string[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const READ_INBOX_KEY = 'read_inbox_ids'

export type InboxFilter = 'unread' | 'read' | 'all'
