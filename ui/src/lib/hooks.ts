// TanStack React Query hooks for CineForge API client.

import { useEffect, useMemo, useRef, useCallback } from 'react'
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query'
import type {
  ArtifactDetailResponse,
  ArtifactEditRequest,
  ArtifactEditResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  InputFileSummary,
  ProjectSummary,
  ProjectState,
  RecentProjectSummary,
  RecipeSummary,
  RunEventsResponse,
  RunStartPayload,
  RunStateResponse,
  RunSummary,
  SearchResponse,
  UploadedInputResponse,
  SortMode,
  SortDirection,
} from './types'
import * as api from './api'
import { useChatStore } from './chat-store'
import { getWelcomeMessages } from './chat-messages'
import { formatEntityName } from './utils'

// Scene data types for UI components
export interface Scene {
  entityId: string
  index: number
  heading: string
  location: string
  intExt: 'INT' | 'EXT' | 'INT/EXT'
  timeOfDay: string
  summary: string
  data?: Record<string, unknown>
}

// --- Search ---

export function useSearch(projectId: string | undefined, query: string) {
  return useQuery<SearchResponse>({
    queryKey: ['search', projectId, query],
    queryFn: () => api.searchProject(projectId!, query),
    enabled: !!projectId && query.length > 0,
    staleTime: 30_000,
  })
}

// --- Recipes ---

export function useRecipes() {
  return useQuery<RecipeSummary[]>({
    queryKey: ['recipes'],
    queryFn: api.listRecipes,
  })
}

// --- Projects ---

export function useRecentProjects() {
  return useQuery<RecentProjectSummary[]>({
    queryKey: ['projects', 'recent'],
    queryFn: api.listRecentProjects,
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery<ProjectSummary>({
    queryKey: ['projects', projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  })
}

/**
 * Returns a [value, setValue] tuple that reads from project ui_preferences
 * and persists changes back via the settings API. Falls back to defaultValue
 * while loading or if the key hasn't been set yet.
 */
export function useStickyPreference<T extends string>(
  projectId: string | undefined,
  key: string,
  defaultValue: T,
): [T, (value: T) => void] {
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const currentValue = (project?.ui_preferences?.[key] as T) ?? defaultValue

  const setValue = useCallback((value: T) => {
    if (!projectId) return
    // Optimistic update
    queryClient.setQueryData<ProjectSummary>(['projects', projectId], old => {
      if (!old) return old
      return {
        ...old,
        ui_preferences: { ...old.ui_preferences, [key]: value },
      }
    })
    // Fire-and-forget persist
    api.updateProjectSettings(projectId, {
      ui_preferences: { [key]: value },
    }).catch(() => {
      // Revert on failure
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    })
  }, [projectId, key, queryClient])

  return [currentValue, setValue]
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, { slug: string; displayName: string }>({
    mutationFn: ({ slug, displayName }) => api.createProject(slug, displayName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useOpenProject() {
  const queryClient = useQueryClient()
  return useMutation<ProjectSummary, Error, string>({
    mutationFn: api.openProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUploadInput(projectId: string) {
  return useMutation<UploadedInputResponse, Error, File>({
    mutationFn: (file: File) => api.uploadProjectInput(projectId, file),
  })
}

// --- Inputs ---

export function useProjectInputs(projectId: string | undefined) {
  return useQuery<InputFileSummary[]>({
    queryKey: ['projects', projectId, 'inputs'],
    queryFn: () => api.listProjectInputs(projectId!),
    enabled: !!projectId,
  })
}

export function useProjectInputContent(projectId: string | undefined, filename: string | undefined) {
  return useQuery<string>({
    queryKey: ['projects', projectId, 'inputs', filename, 'content'],
    queryFn: () => api.getProjectInputContent(projectId!, filename!),
    enabled: !!(projectId && filename),
    staleTime: Infinity,
  })
}

// --- Runs ---

export function useRuns(projectId: string | undefined) {
  return useQuery<RunSummary[]>({
    queryKey: ['projects', projectId, 'runs'],
    queryFn: () => api.listRuns(projectId!),
    enabled: !!projectId,
  })
}

export function useStartRun() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, RunStartPayload>({
    mutationFn: api.startRun,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.project_id, 'runs'],
      })
    },
  })
}

export function useRetryFailedStage() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, { runId: string; projectId?: string }>({
    mutationFn: ({ runId }) => api.retryFailedStage(runId),
    onSuccess: (_data, variables) => {
      if (variables.projectId) {
        queryClient.invalidateQueries({
          queryKey: ['projects', variables.projectId, 'runs'],
        })
      }
    },
  })
}

export function useResumeRun() {
  const queryClient = useQueryClient()
  return useMutation<{ run_id: string }, Error, { runId: string; projectId?: string }>({
    mutationFn: ({ runId }) => api.resumeRun(runId),
    onSuccess: (_data, variables) => {
      if (variables.projectId) {
        queryClient.invalidateQueries({
          queryKey: ['projects', variables.projectId, 'runs'],
        })
      }
    },
  })
}

export function useRespondToReview() {
  const queryClient = useQueryClient()
  return useMutation<
    ArtifactEditResponse,
    Error,
    {
      projectId: string
      sceneId: string
      stageId: string
      approved: boolean
      feedback?: string
    }
  >({
    mutationFn: ({ projectId, sceneId, stageId, approved, feedback }) =>
      api.respondToReview(projectId, sceneId, stageId, approved, feedback),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'artifacts'],
      })
    },
  })
}

export function useRunState(runId: string | undefined) {
  return useQuery<RunStateResponse>({
    queryKey: ['runs', runId, 'state'],
    queryFn: () => api.getRunState(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.state?.finished_at ? false : 2000
    },
    refetchIntervalInBackground: true,
    structuralSharing: false,
  })
}

export function useRunEvents(runId: string | undefined) {
  return useQuery<RunEventsResponse>({
    queryKey: ['runs', runId, 'events'],
    queryFn: () => api.getRunEvents(runId!),
    enabled: !!runId,
    refetchInterval: 3000,
    refetchIntervalInBackground: true,
  })
}

// --- Artifacts ---

export function useArtifactGroups(projectId: string | undefined) {
  return useQuery<ArtifactGroupSummary[]>({
    queryKey: ['projects', projectId, 'artifacts'],
    queryFn: () => api.listArtifactGroups(projectId!),
    enabled: !!projectId,
  })
}

export function useArtifactVersions(
  projectId: string | undefined,
  artifactType: string | undefined,
  entityId: string | undefined,
) {
  return useQuery<ArtifactVersionSummary[]>({
    queryKey: ['projects', projectId, 'artifacts', artifactType, entityId],
    queryFn: () => api.listArtifactVersions(projectId!, artifactType!, entityId!),
    enabled: !!(projectId && artifactType && entityId),
  })
}

export function useArtifact(
  projectId: string | undefined,
  artifactType: string | undefined,
  entityId: string | undefined,
  version: number | undefined,
) {
  return useQuery<ArtifactDetailResponse>({
    queryKey: ['projects', projectId, 'artifacts', artifactType, entityId, version],
    queryFn: () => api.getArtifact(projectId!, artifactType!, entityId!, version!),
    enabled: !!(projectId && artifactType && entityId && version !== undefined),
  })
}

export function useEditArtifact() {
  const queryClient = useQueryClient()
  return useMutation<
    ArtifactEditResponse,
    Error,
    {
      projectId: string
      artifactType: string
      entityId: string
      payload: ArtifactEditRequest
    }
  >({
    mutationFn: ({ projectId, artifactType, entityId, payload }) =>
      api.editArtifact(projectId, artifactType, entityId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'artifacts', variables.artifactType],
      })
    },
  })
}

// --- Project State ---

export function useProjectState(projectId: string | undefined): ProjectState {
  const { data: project } = useProject(projectId)
  const { data: runs } = useRuns(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)

  if (!project) return 'empty'

  const hasInputs = project.has_inputs
  const hasArtifacts = (artifactGroups?.length ?? 0) > 0
  const hasRuns = (runs?.length ?? 0) > 0
  const hasActiveRun = runs?.some(r => r.status === 'running' || r.status === 'pending') ?? false

  if (!hasInputs) return 'empty'
  if (hasActiveRun) return 'processing'
  if (hasArtifacts) {
    const hasCreativeArtifacts = artifactGroups?.some(
      g => g.artifact_type === 'bible_manifest' || g.artifact_type === 'entity_graph'
    ) ?? false
    return hasCreativeArtifacts ? 'complete' : 'analyzed'
  }
  if (hasRuns && !hasArtifacts) return 'analyzed'
  return 'fresh_import'
}

// --- Specialized Hooks ---

export function useSceneIndex(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const sceneIndexGroup = groups?.find(g => g.artifact_type === 'scene_index')

  return useArtifact(
    projectId,
    'scene_index',
    sceneIndexGroup?.entity_id ?? 'project',
    sceneIndexGroup?.latest_version,
  )
}

export function useCanonicalScript(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const group = groups?.find(g => g.artifact_type === 'canonical_script')

  return useArtifact(
    projectId,
    'canonical_script',
    group?.entity_id ?? 'project',
    group?.latest_version,
  )
}

export interface EnrichedEntity {
  entity_id: string | null
  artifact_type: string
  latest_version: number
  health: string | null
  description: string | null
  sceneCount: number
  firstSceneNumber: number | null
  isLoaded: boolean
  data?: Record<string, unknown>
}

const normalize = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')

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

export function useEntityDetails(
  projectId: string | undefined,
  artifactType: 'character_bible' | 'location_bible' | 'prop_bible',
) {
  const { data: groups, isLoading: groupsLoading, error: groupsError } = useArtifactGroups(projectId)
  const { data: sceneIndexData } = useSceneIndex(projectId)

  const entities = useMemo(
    () => groups?.filter(g => g.artifact_type === artifactType) ?? [],
    [groups, artifactType],
  )

  const detailQueries = useQueries({
    queries: entities.map(e => ({
      queryKey: ['projects', projectId, 'artifacts', artifactType, e.entity_id, e.latest_version],
      queryFn: () => api.getArtifact(projectId!, artifactType, e.entity_id!, e.latest_version),
      enabled: !!projectId && entities.length > 0,
      staleTime: 60_000,
    })),
  })

  const enriched: EnrichedEntity[] = useMemo(() => {
    return entities.map((group, idx) => {
      const detail = detailQueries[idx]?.data
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = detail?.payload?.data as any

      return {
        entity_id: group.entity_id,
        artifact_type: group.artifact_type,
        latest_version: group.latest_version,
        health: group.health,
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

  const detailsLoading = detailQueries.some(q => q.isLoading)

  return {
    data: enriched,
    isLoading: groupsLoading,
    detailsLoading,
    error: groupsError,
  }
}

export function useEntityGraph(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const graphGroup = groups?.find(g => g.artifact_type === 'entity_graph')

  return useArtifact(
    projectId,
    'entity_graph',
    graphGroup?.entity_id ?? 'project',
    graphGroup?.latest_version,
  )
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

export function useEntityResolver(projectId: string | undefined) {
  const { data: groups } = useArtifactGroups(projectId)
  const { data: scenes } = useScenes(projectId)

  const resolver = useMemo(() => {
    const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')
    const entityMap = new Map<string, { entityId: string; section: string }>()

    for (const g of groups ?? []) {
      if (!g.entity_id) continue
      for (const [type, artifactType] of Object.entries(ARTIFACT_TYPE_MAP)) {
        if (g.artifact_type !== artifactType) continue
        const section = SECTION_MAP[type as EntityType]
        const entry = { entityId: g.entity_id, section }
        entityMap.set(norm(g.entity_id), entry)
        entityMap.set(g.entity_id.toLowerCase(), entry)
      }
    }

    const sceneHeadingMap = new Map<string, string>()
    const sceneHeadingPrefixes: Array<{ norm: string; entityId: string }> = []

    for (const scene of scenes ?? []) {
      if (scene.heading) {
        const headingNorm = norm(scene.heading)
        sceneHeadingMap.set(headingNorm, scene.entityId)
        sceneHeadingMap.set(scene.heading.toLowerCase(), scene.entityId)
        sceneHeadingPrefixes.push({ norm: headingNorm, entityId: scene.entityId })
      }
      if (scene.location) {
        if (!sceneHeadingMap.has(norm(scene.location))) {
          sceneHeadingMap.set(norm(scene.location), scene.entityId)
        }
      }
      sceneHeadingMap.set(`scene${scene.index}`, scene.entityId)
      sceneHeadingMap.set(`scene_${String(scene.index).padStart(3, '0')}`, scene.entityId)
    }
    sceneHeadingPrefixes.sort((a, b) => b.norm.length - a.norm.length)

    function resolveScene(input: string): string | null {
      const inputNorm = norm(input)
      const inputLower = input.toLowerCase()
      const exact = sceneHeadingMap.get(inputNorm) ?? sceneHeadingMap.get(inputLower)
      if (exact) return exact
      const colonIdx = input.indexOf(':')
      if (colonIdx > 0) {
        const beforeColon = input.slice(0, colonIdx).trim()
        const match = sceneHeadingMap.get(norm(beforeColon)) ?? sceneHeadingMap.get(beforeColon.toLowerCase())
        if (match) return match
      }
      for (const prefix of sceneHeadingPrefixes) {
        if (inputNorm.startsWith(prefix.norm)) return prefix.entityId
      }
      return null
    }

    function resolve(name: string, type?: EntityType): ResolvedLink | null {
      if (!projectId || !name) return null
      const normalized = norm(name)
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
        for (const g of groups ?? []) {
          if (g.artifact_type !== artifactType || !g.entity_id) continue
          if (norm(g.entity_id) === normalized || g.entity_id.toLowerCase() === lowered) {
            return { path: `/${projectId}/${section}/${g.entity_id}`, label: name }
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

function transformArtifactToScene(artifact: ArtifactDetailResponse, entityId: string, fallbackIndex: number): Scene | null {
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
    data: data,
  }
}

export function useScenes(projectId: string | undefined) {
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const sceneGroups = artifactGroups?.filter(
    (g) => g.artifact_type === 'scene' || g.artifact_type === 'scene_breakdown'
  ) ?? []
  const sceneQueries = useQueries({
    queries: sceneGroups.map((group) => ({
      queryKey: ['projects', projectId, 'artifacts', group.artifact_type, group.entity_id, group.latest_version],
      queryFn: () => api.getArtifact(projectId!, group.artifact_type, group.entity_id ?? 'project', group.latest_version),
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
      sceneList.forEach((sceneData: any, idx: number) => {
        const sceneNumber = sceneData?.scene_number ?? idx + 1
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
        } else if (normalized === 'INT/EXT' || normalized === 'INT./EXT.' || normalized === 'BOTH') {
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
          data: sceneData,
        })
      })
    } else {
      const scene = transformArtifactToScene(artifact, group.entity_id ?? `scene_${String(index + 1).padStart(3, '0')}`, index + 1)
      if (scene) {
        scenes.push(scene)
      }
    }
  })
  scenes.sort((a, b) => a.index - b.index)
  const isLoading = sceneQueries.some((q) => q.isLoading)
  return { data: scenes, isLoading }
}

export function useChatLoader(projectId: string | undefined) {
  const projectState = useProjectState(projectId)
  const { data: project, isLoading } = useProject(projectId)
  const initializedRef = useRef<string | null>(null)

  useEffect(() => {
    if (!projectId || !project || isLoading) return
    if (initializedRef.current === projectId) return
    const store = useChatStore.getState()
    if (store.isLoaded(projectId)) {
      initializedRef.current = projectId
      return
    }
    initializedRef.current = projectId
    api.getChatMessages(projectId)
      .then((backendMessages) => {
        if (useChatStore.getState().isLoaded(projectId)) return
        if (backendMessages.length > 0) {
          useChatStore.getState().loadMessages(projectId, backendMessages)
        } else {
          const welcomeMessages = getWelcomeMessages(projectState, project)
          useChatStore.getState().loadMessages(projectId, [])
          for (const msg of welcomeMessages) {
            useChatStore.getState().addMessage(projectId, msg)
          }
        }
      })
      .catch(() => {
        const store = useChatStore.getState()
        if (!store.hasMessages(projectId)) {
          const welcomeMessages = getWelcomeMessages(projectState, project)
          store.loadMessages(projectId, welcomeMessages)
        }
      })
  }, [projectId, projectState, project, isLoading])
}

// --- Navigation ---

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
  currentEntityId: string | undefined
): EntityNavigation {
  const isScene = section === 'scenes'
  
  // 1. Get entities
  const { data: scenes, isLoading: scenesLoading } = useScenes(isScene ? projectId : undefined)
  const bibleType = section === 'characters' ? 'character_bible' : section === 'locations' ? 'location_bible' : 'prop_bible'
  const { data: entities, isLoading: entitiesLoading } = useEntityDetails(
    !isScene ? projectId : undefined,
    bibleType as 'character_bible' | 'location_bible' | 'prop_bible'
  )

  // 2. Get preferences
  const [sort] = useStickyPreference<SortMode>(projectId, `${section}.sort`, 'script-order')
  const [direction] = useStickyPreference<SortDirection>(projectId, `${section}.direction`, 'asc')

  return useMemo(() => {
    if (scenesLoading || entitiesLoading || !projectId || !currentEntityId) {
      return { prev: null, next: null, sortMode: sort, sortDirection: direction }
    }

    let items: Array<{ id: string; scriptOrder: number; label: string; prominence: number }> = []

    if (isScene && scenes) {
      items = scenes.map(s => ({
        id: s.entityId,
        scriptOrder: s.index,
        label: s.heading,
        prominence: s.heading.length,
      }))
    } else if (entities) {
      items = entities.map(e => ({
        id: e.entity_id!,
        scriptOrder: e.firstSceneNumber ?? Infinity,
        label: formatEntityName(e.entity_id!),
        prominence: e.sceneCount,
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
      // Stable sort fallback
      if (cmp === 0) cmp = a.id.localeCompare(b.id)
      return direction === 'asc' ? cmp : -cmp
    }

    const sorted = [...items].sort(sortFn)
    const currentIndex = sorted.findIndex(item => item.id === currentEntityId)
    
    const prev = currentIndex > 0 ? sorted[currentIndex - 1].id : null
    const next = currentIndex < sorted.length - 1 && currentIndex !== -1 ? sorted[currentIndex + 1].id : null

    let prevChronological = null
    let nextChronological = null

    if (isScene) {
      const chronological = [...items].sort((a, b) => a.scriptOrder - b.scriptOrder)
      const chronIndex = chronological.findIndex(item => item.id === currentEntityId)
      prevChronological = chronIndex > 0 ? chronological[chronIndex - 1].id : null
      nextChronological = chronIndex < chronological.length - 1 && chronIndex !== -1 ? chronological[chronIndex + 1].id : null
    }

    return {
      prev,
      next,
      prevChronological: isScene && (sort !== 'script-order' || direction !== 'asc') ? prevChronological : undefined,
      nextChronological: isScene && (sort !== 'script-order' || direction !== 'asc') ? nextChronological : undefined,
      sortMode: sort,
      sortDirection: direction,
    }
  }, [scenes, entities, scenesLoading, entitiesLoading, projectId, currentEntityId, isScene, sort, direction])
}

// --- Export ---

export function useExportData(projectId: string | undefined) {
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: scenes, isLoading: scenesLoading } = useScenes(projectId)
  const { data: characters, isLoading: charactersLoading } = useEntityDetails(projectId, 'character_bible')
  const { data: locations, isLoading: locationsLoading } = useEntityDetails(projectId, 'location_bible')
  const { data: props, isLoading: propsLoading } = useEntityDetails(projectId, 'prop_bible')

  const isLoading = projectLoading || scenesLoading || charactersLoading || locationsLoading || propsLoading

  return {
    data: {
      summary: project,
      scenes: scenes ?? [],
      characters: characters ?? [],
      locations: locations ?? [],
      props: props ?? [],
    },
    isLoading,
  }
}
