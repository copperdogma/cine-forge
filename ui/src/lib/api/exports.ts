import { API_BASE, ApiRequestError } from './core'

export type ExportScope = 'everything' | 'scenes' | 'characters' | 'locations' | 'props' | 'single'
export type ExportFormat =
  | 'markdown'
  | 'pdf'
  | 'call-sheet'
  | 'fountain'
  | 'docx'
  | 'shot-list-csv'
  | 'shot-list-pdf'

export type CostExportFormat = 'cost-report-csv' | 'cost-report-json'

export function getExportUrl(
  projectId: string,
  format: ExportFormat,
  scope: ExportScope = 'everything',
  entityId?: string,
  entityType?: string,
  include?: string[],
): string {
  const params = new URLSearchParams()

  if (format === 'markdown') {
    params.set('scope', scope)
    if (entityId) params.set('entity_id', entityId)
    if (entityType) params.set('entity_type', entityType)
    if (include && include.length > 0) {
      include.forEach((item) => params.append('include', item))
    }
    return `${API_BASE}/api/projects/${projectId}/export/markdown?${params.toString()}`
  }

  if (format === 'fountain') {
    return `${API_BASE}/api/projects/${projectId}/export/fountain`
  }

  if (format === 'docx') {
    return `${API_BASE}/api/projects/${projectId}/export/docx`
  }

  if (format === 'shot-list-csv') {
    return `${API_BASE}/api/projects/${projectId}/export/shot-list.csv`
  }

  if (format === 'shot-list-pdf') {
    return `${API_BASE}/api/projects/${projectId}/export/shot-list.pdf`
  }

  const layout = format === 'call-sheet'
    ? 'call-sheet'
    : (format === 'pdf' && scope === 'single' && entityType === 'scene')
        || (format === 'pdf' && include?.length === 1 && include[0] === 'script')
      ? 'screenplay'
      : 'report'

  let effectiveLayout = layout
  if (format === 'pdf' && include && include.length === 1 && include[0] === 'script') {
    effectiveLayout = 'screenplay'
  }

  params.set('layout', effectiveLayout)
  return `${API_BASE}/api/projects/${projectId}/export/pdf?${params.toString()}`
}

export async function exportMarkdown(
  projectId: string,
  scope: ExportScope = 'everything',
  entityId?: string,
  entityType?: string,
  include?: string[],
): Promise<string> {
  const url = getExportUrl(projectId, 'markdown', scope, entityId, entityType, include)
  const response = await fetch(url)
  if (!response.ok) {
    throw new ApiRequestError(`Export failed (${response.status})`)
  }
  return response.text()
}

export function getCostExportUrl(
  projectId: string,
  format: CostExportFormat,
  runId?: string,
): string {
  const params = new URLSearchParams()
  if (runId) {
    params.set('run_id', runId)
  }
  const path = format === 'cost-report-csv' ? 'costs.csv' : 'costs.json'
  const query = params.toString()
  return `${API_BASE}/api/projects/${projectId}/export/${path}${query ? `?${query}` : ''}`
}
