import { useMemo } from 'react'
import type { SortDirection, SortMode } from '../types'
import { formatEntityName } from '../utils'
import { useEntityDetails, useScenes } from './entities'
import { useStickyPreference } from './projects'

export interface EntityNavigation {
  prev: string | null
  next: string | null
  prevChronological?: string | null
  nextChronological?: string | null
  sortMode: SortMode
  sortDirection: SortDirection
}

export function useEntityNavigation(
  projectId: string | undefined,
  section: string,
  currentEntityId: string | undefined,
): EntityNavigation {
  const isScene = section === 'scenes'
  const { data: scenes, isLoading: scenesLoading } = useScenes(isScene ? projectId : undefined)
  const bibleType = section === 'characters'
    ? 'character_bible'
    : section === 'locations'
      ? 'location_bible'
      : 'prop_bible'
  const { data: entities, isLoading: entitiesLoading } = useEntityDetails(
    !isScene ? projectId : undefined,
    bibleType as 'character_bible' | 'location_bible' | 'prop_bible',
  )

  const [sort] = useStickyPreference<SortMode>(projectId, `${section}.sort`, 'script-order')
  const [direction] = useStickyPreference<SortDirection>(projectId, `${section}.direction`, 'asc')

  return useMemo(() => {
    if (scenesLoading || entitiesLoading || !projectId || !currentEntityId) {
      return { prev: null, next: null, sortMode: sort, sortDirection: direction }
    }

    let items: Array<{ id: string; scriptOrder: number; label: string; prominence: number }> = []

    if (isScene && scenes) {
      items = scenes.map((scene) => ({
        id: scene.entityId,
        scriptOrder: scene.index,
        label: scene.heading,
        prominence: scene.heading.length,
      }))
    } else if (entities) {
      items = entities.map((entity) => ({
        id: entity.entity_id!,
        scriptOrder: entity.firstSceneNumber ?? Infinity,
        label: formatEntityName(entity.entity_id!),
        prominence: entity.sceneCount,
      }))
    }

    if (items.length === 0) {
      return { prev: null, next: null, sortMode: sort, sortDirection: direction }
    }

    const sortFn = (a: typeof items[0], b: typeof items[0]) => {
      let cmp = 0
      switch (sort) {
        case 'alphabetical':
          cmp = a.label.toLowerCase().localeCompare(b.label.toLowerCase())
          break
        case 'prominence':
          cmp = b.prominence - a.prominence
          if (cmp === 0) cmp = a.scriptOrder - b.scriptOrder
          break
        case 'script-order':
        default:
          cmp = a.scriptOrder - b.scriptOrder
          break
      }
      if (cmp === 0) cmp = a.id.localeCompare(b.id)
      return direction === 'asc' ? cmp : -cmp
    }

    const sorted = [...items].sort(sortFn)
    const currentIndex = sorted.findIndex((item) => item.id === currentEntityId)

    const prev = currentIndex > 0 ? sorted[currentIndex - 1].id : null
    const next = currentIndex < sorted.length - 1 && currentIndex !== -1
      ? sorted[currentIndex + 1].id
      : null

    let prevChronological = null
    let nextChronological = null

    if (isScene) {
      const chronological = [...items].sort((a, b) => a.scriptOrder - b.scriptOrder)
      const chronIndex = chronological.findIndex((item) => item.id === currentEntityId)
      prevChronological = chronIndex > 0 ? chronological[chronIndex - 1].id : null
      nextChronological = chronIndex < chronological.length - 1 && chronIndex !== -1
        ? chronological[chronIndex + 1].id
        : null
    }

    return {
      prev,
      next,
      prevChronological: isScene && (sort !== 'script-order' || direction !== 'asc')
        ? prevChronological
        : undefined,
      nextChronological: isScene && (sort !== 'script-order' || direction !== 'asc')
        ? nextChronological
        : undefined,
      sortMode: sort,
      sortDirection: direction,
    }
  }, [
    scenes,
    entities,
    scenesLoading,
    entitiesLoading,
    projectId,
    currentEntityId,
    isScene,
    sort,
    direction,
  ])
}
