import type { SceneActionPreflight, SceneExecutionScope } from '../types'
import { request } from './core'

export function getSceneActionPreflight(
  projectId: string,
  payload: {
    recipe_id: string
    start_from?: string
    end_at?: string
    scene_scope: SceneExecutionScope
  },
): Promise<SceneActionPreflight> {
  return request<SceneActionPreflight>(`/api/projects/${projectId}/scene-actions/preflight`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
