import type { PreferenceProfile } from '../types'
import { request } from './core'

export function getProjectPreferenceProfile(projectId: string): Promise<PreferenceProfile> {
  return request<PreferenceProfile>(`/api/projects/${projectId}/preferences/profile`)
}

export function clearProjectPreferenceProfile(projectId: string): Promise<PreferenceProfile> {
  return request<PreferenceProfile>(`/api/projects/${projectId}/preferences/clear`, {
    method: 'POST',
  })
}
