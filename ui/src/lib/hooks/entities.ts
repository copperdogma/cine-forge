import { useMemo } from 'react'
import { useQueries } from '@tanstack/react-query'
import { getArtifact } from '../api'
import type { ArtifactDetailResponse, ArtifactHealthDetails } from '../types'
import { useArtifactGroups, useSceneIndex } from './artifacts'

export interface Scene {
  entityId: string
  index: number
  heading: string
  location: string
  intExt: 'INT' | 'EXT' | 'INT/EXT'
  timeOfDay: string
  summary: string
  startLine?: number
  endLine?: number
  data?: Record<string, unknown>
}

export interface EnrichedEntity {
  entity_id: string | null
  artifact_type: string
  latest_version: number
  health: string | null
  health_details?: ArtifactHealthDetails | null
  description: string | null
  sceneCount: number
  firstSceneNumber: number | null
  isLoaded: boolean
  data?: Record<string, unknown>
}

export interface ResolvedLink {
  path: string
  label: string
}

type EntityType = 'character' | 'location' | 'prop' | 'scene'

const ARTIFACT_TYPE_MAP: Record<EntityType, string> = {
  character: 'character_bible',
  location: 'location_bible',
  prop: 'prop_bible',
  scene: 'scene',
}

const SECTION_MAP: Record<EntityType, string> = {
  character: 'characters',
  location: 'locations',
  prop: 'props',
  scene: 'scenes',
}

const normalize = (value: string) => value.toLowerCase().replace(/[^a-z0-9]/g, '')

function stripDescription(heading: string): string {
  const colonIdx = heading.indexOf(':')
  return colonIdx > 0 ? heading.slice(0, colonIdx).trim() : heading
}

function computeFirstSceneNumber(
  scenePresence: string[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sceneIndexData: any,
): number | null {
  if (!scenePresence?.length || !sceneIndexData) return null

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const entries: any[] = sceneIndexData?.payload?.data?.entries ?? []
  if (!entries.length) return null

  const headingToNumber = new Map<string, number>()
  for (const entry of entries) {
    if (entry.heading) {
      headingToNumber.set(normalize(entry.heading), entry.scene_number)
    }
  }

  let minScene: number | null = null
  for (const presence of scenePresence) {
    const key = normalize(presence)
    let num = headingToNumber.get(key)
    if (num == null) {
      num = headingToNumber.get(normalize(stripDescription(presence)))
    }
    if (num == null) {
      for (const [normHeading, sceneNum] of headingToNumber) {
        if (key.startsWith(normHeading)) {
          num = sceneNum
          break
        }
      }
    }
    if (num != null && (minScene == null || num < minScene)) {
      minScene = num
    }
  }

  return minScene
}

function transformArtifactToScene(
  artifact: ArtifactDetailResponse,
  entityId: string,
  fallbackIndex: number,
): Scene | null {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = artifact.payload.data as any
  const sceneNumber = data?.scene_number ?? fallbackIndex
  const heading = data?.heading ?? data?.scene_heading ?? `Scene ${sceneNumber}`
  const location = data?.location ?? data?.scene_location ?? heading
  const intExtRaw = data?.int_ext ?? data?.interior_exterior ?? 'INT'
  const timeOfDay = data?.time_of_day ?? data?.time ?? 'DAY'
  const summary = data?.summary ?? data?.description ?? heading
  let intExt: 'INT' | 'EXT' | 'INT/EXT' = 'INT'
  const normalized = intExtRaw.toUpperCase().trim()
  if (normalized === 'EXT' || normalized === 'EXTERIOR') {
    intExt = 'EXT'
  } else if (normalized === 'INT/EXT' || normalized === 'INT./EXT.' || normalized === 'BOTH') {
    intExt = 'INT/EXT'
  }
  return {
    entityId,
    index: sceneNumber,
    heading,
    location,
    intExt,
    timeOfDay: timeOfDay.toUpperCase(),
    summary,
    startLine: data?.source_span?.start_line ?? undefined,
    endLine: data?.source_span?.end_line ?? undefined,
    data,
  }
}

export function useEntityDetails(
  projectId: string | undefined,
  artifactType: 'character_bible' | 'location_bible' | 'prop_bible',
) {
  const { data: groups, isLoading: groupsLoading, error: groupsError } = useArtifactGroups(projectId)
  const { data: sceneIndexData } = useSceneIndex(projectId)

  const entities = useMemo(
    () => groups?.filter((group) => group.artifact_type === artifactType) ?? [],
    [groups, artifactType],
  )

  const detailQueries = useQueries({
    queries: entities.map((entity) => ({
      queryKey: ['projects', projectId, 'artifacts', artifactType, entity.entity_id, entity.latest_version],
      queryFn: () => getArtifact(projectId!, artifactType, entity.entity_id!, entity.latest_version),
      enabled: !!projectId && entities.length > 0,
      staleTime: 60_000,
    })),
  })

  const enriched: EnrichedEntity[] = useMemo(() => {
    return entities.map((group, index) => {
      const detail = detailQueries[index]?.data
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = detail?.payload?.data as any

      return {
        entity_id: group.entity_id,
        artifact_type: group.artifact_type,
        latest_version: group.latest_version,
        health: group.health,
        health_details: group.health_details,
        description: data?.description ?? null,
        sceneCount: data?.scene_presence?.length ?? 0,
        firstSceneNumber: computeFirstSceneNumber(
          data?.scene_presence ?? [],
          sceneIndexData,
        ),
        isLoaded: !!detail,
        data: data || undefined,
      }
    })
  }, [entities, detailQueries, sceneIndexData])

  const detailsLoading = detailQueries.some((query) => query.isLoading)

  return {
    data: enriched,
    isLoading: groupsLoading,
    detailsLoading,
    error: groupsError,
  }
}

export function useScenes(projectId: string | undefined) {
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const sceneGroups = artifactGroups?.filter(
    (group) => group.artifact_type === 'scene' || group.artifact_type === 'scene_breakdown',
  ) ?? []
  const sceneQueries = useQueries({
    queries: sceneGroups.map((group) => ({
      queryKey: ['projects', projectId, 'artifacts', group.artifact_type, group.entity_id, group.latest_version],
      queryFn: () => getArtifact(projectId!, group.artifact_type, group.entity_id ?? 'project', group.latest_version),
      enabled: !!projectId && sceneGroups.length > 0,
    })),
  })

  const scenes: Scene[] = []
  sceneQueries.forEach((query, index) => {
    if (!query.data) return

    const artifact = query.data
    const group = sceneGroups[index]
    if (group.artifact_type === 'scene_breakdown') {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = artifact.payload.data as any
      const sceneList = data?.scenes ?? []
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      sceneList.forEach((sceneData: any, sceneIndex: number) => {
        const sceneNumber = sceneData?.scene_number ?? sceneIndex + 1
        const sceneEntityId = sceneData?.scene_id ?? `scene_${String(sceneNumber).padStart(3, '0')}`
        const heading = sceneData?.heading ?? sceneData?.scene_heading ?? `Scene ${sceneNumber}`
        const location = sceneData?.location ?? sceneData?.scene_location ?? heading
        const intExtRaw = sceneData?.int_ext ?? sceneData?.interior_exterior ?? 'INT'
        const timeOfDay = sceneData?.time_of_day ?? sceneData?.time ?? 'DAY'
        const summary = sceneData?.summary ?? sceneData?.description ?? heading
        let intExt: 'INT' | 'EXT' | 'INT/EXT' = 'INT'
        const normalized = intExtRaw.toUpperCase().trim()
        if (normalized === 'EXT' || normalized === 'EXTERIOR') {
          intExt = 'EXT'
        } else if (
          normalized === 'INT/EXT'
          || normalized === 'INT./EXT.'
          || normalized === 'BOTH'
        ) {
          intExt = 'INT/EXT'
        }
        scenes.push({
          entityId: sceneEntityId,
          index: sceneNumber,
          heading,
          location,
          intExt,
          timeOfDay: timeOfDay.toUpperCase(),
          summary,
          startLine: sceneData?.source_span?.start_line ?? undefined,
          endLine: sceneData?.source_span?.end_line ?? undefined,
          data: sceneData,
        })
      })
    } else {
      const scene = transformArtifactToScene(
        artifact,
        group.entity_id ?? `scene_${String(index + 1).padStart(3, '0')}`,
        index + 1,
      )
      if (scene) {
        scenes.push(scene)
      }
    }
  })

  scenes.sort((a, b) => a.index - b.index)
  const isLoading = sceneQueries.some((query) => query.isLoading)
  return { data: scenes, isLoading }
}

export function useEntityResolver(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const { data: scenes } = useScenes(projectId)

  const resolver = useMemo(() => {
    const entityMap = new Map<string, { entityId: string; section: string }>()

    for (const group of groups ?? []) {
      if (!group.entity_id) continue
      for (const [type, artifactType] of Object.entries(ARTIFACT_TYPE_MAP)) {
        if (group.artifact_type !== artifactType) continue
        const section = SECTION_MAP[type as EntityType]
        const entry = { entityId: group.entity_id, section }
        entityMap.set(normalize(group.entity_id), entry)
        entityMap.set(group.entity_id.toLowerCase(), entry)
      }
    }

    const sceneHeadingMap = new Map<string, string>()
    const sceneHeadingPrefixes: Array<{ norm: string; entityId: string }> = []

    for (const scene of scenes ?? []) {
      if (scene.heading) {
        const headingNorm = normalize(scene.heading)
        sceneHeadingMap.set(headingNorm, scene.entityId)
        sceneHeadingMap.set(scene.heading.toLowerCase(), scene.entityId)
        sceneHeadingPrefixes.push({ norm: headingNorm, entityId: scene.entityId })
      }
      if (scene.location && !sceneHeadingMap.has(normalize(scene.location))) {
        sceneHeadingMap.set(normalize(scene.location), scene.entityId)
      }
      sceneHeadingMap.set(`scene${scene.index}`, scene.entityId)
      sceneHeadingMap.set(`scene_${String(scene.index).padStart(3, '0')}`, scene.entityId)
    }
    sceneHeadingPrefixes.sort((a, b) => b.norm.length - a.norm.length)

    function resolveScene(input: string): string | null {
      const inputNorm = normalize(input)
      const inputLower = input.toLowerCase()
      const exact = sceneHeadingMap.get(inputNorm) ?? sceneHeadingMap.get(inputLower)
      if (exact) return exact

      const colonIdx = input.indexOf(':')
      if (colonIdx > 0) {
        const beforeColon = input.slice(0, colonIdx).trim()
        const match = sceneHeadingMap.get(normalize(beforeColon))
          ?? sceneHeadingMap.get(beforeColon.toLowerCase())
        if (match) return match
      }

      for (const prefix of sceneHeadingPrefixes) {
        if (inputNorm.startsWith(prefix.norm)) return prefix.entityId
      }
      return null
    }

    function resolve(name: string, type?: EntityType): ResolvedLink | null {
      if (!projectId || !name) return null

      const normalized = normalize(name)
      const lowered = name.toLowerCase()
      if (type) {
        if (type === 'scene') {
          const sceneId = resolveScene(name)
          if (sceneId) {
            return { path: `/${projectId}/scenes/${sceneId}`, label: name }
          }
          const entry = entityMap.get(normalized) ?? entityMap.get(lowered)
          if (entry?.section === 'scenes') {
            return { path: `/${projectId}/scenes/${entry.entityId}`, label: name }
          }
          return null
        }

        const artifactType = ARTIFACT_TYPE_MAP[type]
        const section = SECTION_MAP[type]
        for (const group of groups ?? []) {
          if (group.artifact_type !== artifactType || !group.entity_id) continue
          if (normalize(group.entity_id) === normalized || group.entity_id.toLowerCase() === lowered) {
            return { path: `/${projectId}/${section}/${group.entity_id}`, label: name }
          }
        }

        for (const group of groups ?? []) {
          if (group.artifact_type !== artifactType || !group.entity_id) continue
          if (normalize(group.entity_id).includes(normalized)) {
            return { path: `/${projectId}/${section}/${group.entity_id}`, label: name }
          }
        }
        return null
      }

      const sceneId = resolveScene(name)
      if (sceneId) {
        return { path: `/${projectId}/scenes/${sceneId}`, label: name }
      }
      const entry = entityMap.get(normalized) ?? entityMap.get(lowered)
      if (entry) {
        return { path: `/${projectId}/${entry.section}/${entry.entityId}`, label: name }
      }
      return null
    }

    return { resolve }
  }, [projectId, groups, scenes])

  return resolver
}
