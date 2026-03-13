import type { RecipeSummary } from '../types'
import { API_BASE, request } from './core'

export function fetchHealth(): Promise<{ status: string; version: string }> {
  return request<{ status: string; version: string }>('/api/health')
}

export async function fetchChangelog(): Promise<string> {
  const response = await fetch(`${API_BASE}/api/changelog`)
  if (!response.ok) return 'Changelog unavailable.'
  return response.text()
}

export function listRecipes(): Promise<RecipeSummary[]> {
  return request<RecipeSummary[]>('/api/recipes')
}
