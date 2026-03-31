import { API_BASE, ApiRequestError } from './core'

export type ExportScope = 'everything' | 'scenes' | 'characters' | 'locations' | 'props' | 'single'
export type ExportFormat =
  | 'markdown'
  | 'pdf'
  | 'call-sheet'
  | 'fcpxml'
  | 'fountain'
  | 'docx'
  | 'shot-list-csv'
  | 'shot-list-pdf'

export type CostExportFormat = 'cost-report-csv' | 'cost-report-json'

function appendIncludeParams(params: URLSearchParams, include?: string[]) {
  if (!include || include.length === 0) return
  include.forEach((item) => params.append('include', item))
}

function buildProjectExportUrl(projectId: string, path: string, params: URLSearchParams): string {
  const query = params.toString()
  return `${API_BASE}/api/projects/${projectId}/export/${path}${query ? `?${query}` : ''}`
}

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
    appendIncludeParams(params, include)
    return buildProjectExportUrl(projectId, 'markdown', params)
  }

  if (format === 'fountain') {
    return buildProjectExportUrl(projectId, 'fountain', params)
  }

  if (format === 'fcpxml') {
    return buildProjectExportUrl(projectId, 'fcpxml', params)
  }

  if (format === 'docx') {
    appendIncludeParams(params, include)
    return buildProjectExportUrl(projectId, 'docx', params)
  }

  if (format === 'shot-list-csv') {
    return buildProjectExportUrl(projectId, 'shot-list.csv', params)
  }

  if (format === 'shot-list-pdf') {
    return buildProjectExportUrl(projectId, 'shot-list.pdf', params)
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
  appendIncludeParams(params, include)
  return buildProjectExportUrl(projectId, 'pdf', params)
}

export async function exportMarkdown(
  projectId: string,
  scope: ExportScope = 'everything',
  entityId?: string,
  entityType?: string,
  include?: string[],
): Promise<string> {
  const url = getExportUrl(projectId, 'markdown', scope, entityId, entityType, include)
  let response: Response
  try {
    response = await fetch(url)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(
        `Cannot reach API at ${API_BASE}. Start the backend with: PYTHONPATH=src python -m cine_forge.api`,
      )
    }
    throw error
  }
  if (!response.ok) {
    throw await readExportError(response, `Export failed (${response.status})`)
  }
  return response.text()
}

function readErrorMessage(payload: unknown): { message?: string; hint?: string } {
  if (!payload || typeof payload !== 'object') {
    return {}
  }
  const record = payload as Record<string, unknown>
  const message =
    typeof record.message === 'string'
      ? record.message
      : typeof record.detail === 'string'
        ? record.detail
        : undefined
  const hint = typeof record.hint === 'string' ? record.hint : undefined
  return { message, hint }
}

async function readExportError(response: Response, fallbackMessage: string): Promise<ApiRequestError> {
  const contentType = response.headers.get('content-type') ?? ''
  try {
    if (contentType.includes('application/json')) {
      const payload = await response.json()
      const { message, hint } = readErrorMessage(payload)
      return new ApiRequestError(message ?? fallbackMessage, hint)
    }

    const text = (await response.text()).trim()
    return new ApiRequestError(text || fallbackMessage)
  } catch {
    return new ApiRequestError(fallbackMessage)
  }
}

function parseDownloadFilename(
  headerValue: string | null,
  fallbackFilename: string,
): string {
  if (!headerValue) return fallbackFilename
  const match = /filename="?([^";]+)"?/i.exec(headerValue)
  return match?.[1] ?? fallbackFilename
}

function defaultExportFilename(projectId: string, format: ExportFormat): string {
  switch (format) {
    case 'fcpxml':
      return `${projectId}-timeline.fcpxml`
    case 'fountain':
      return `${projectId}.fountain`
    case 'docx':
      return `${projectId}-screenplay.docx`
    case 'shot-list-csv':
      return `${projectId}-shot-list.csv`
    case 'shot-list-pdf':
      return `${projectId}-shot-list.pdf`
    case 'call-sheet':
      return `${projectId}-call-sheet.pdf`
    case 'markdown':
      return `${projectId}-export.md`
    case 'pdf':
    default:
      return `${projectId}-export.pdf`
  }
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const objectUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 0)
}

export async function downloadExport(
  projectId: string,
  format: ExportFormat,
  scope: ExportScope = 'everything',
  entityId?: string,
  entityType?: string,
  include?: string[],
): Promise<void> {
  const url = getExportUrl(projectId, format, scope, entityId, entityType, include)

  let response: Response
  try {
    response = await fetch(url)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(
        `Cannot reach API at ${API_BASE}. Start the backend with: PYTHONPATH=src python -m cine_forge.api`,
      )
    }
    throw error
  }

  if (!response.ok) {
    throw await readExportError(response, `Export failed (${response.status})`)
  }

  const blob = await response.blob()
  const filename = parseDownloadFilename(
    response.headers.get('content-disposition'),
    defaultExportFilename(projectId, format),
  )
  triggerBrowserDownload(blob, filename)
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
