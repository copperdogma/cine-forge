import { useQuery } from '@tanstack/react-query'
import { listRecipes, searchProject } from '../api'
import type { RecipeSummary, SearchResponse } from '../types'

export function useSearch(projectId: string | undefined, query: string) {
  return useQuery<SearchResponse>({
    queryKey: ['search', projectId, query],
    queryFn: () => searchProject(projectId!, query),
    enabled: !!projectId && query.length > 0,
    staleTime: 30_000,
  })
}

export function useRecipes() {
  return useQuery<RecipeSummary[]>({
    queryKey: ['recipes'],
    queryFn: listRecipes,
  })
}
