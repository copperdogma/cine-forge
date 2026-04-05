import { useQuery } from '@tanstack/react-query'
import { getSceneActionPreflight } from '../api'
import type { SceneActionPreflight, SceneExecutionScope } from '../types'

export function useSceneActionPreflight(
  projectId: string | undefined,
  payload: {
    recipe_id: string
    start_from?: string
    end_at?: string
    scene_scope: SceneExecutionScope
  } | null,
  enabled = true,
) {
  return useQuery<SceneActionPreflight>({
    queryKey: ['projects', projectId, 'scene-action-preflight', payload],
    queryFn: () => getSceneActionPreflight(projectId!, payload!),
    enabled: !!projectId && !!payload && enabled,
    staleTime: 5000,
  })
}
