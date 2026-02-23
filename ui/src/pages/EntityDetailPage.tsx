import React from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useHistoryBack } from '@/lib/use-history-back'
import {
  ArrowLeft,
  Users,
  MapPin,
  Wrench,
  Clapperboard,
  FileText,
  GitBranch,
  Code,
  Globe,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Share,
  Star,
} from 'lucide-react'
import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ExportModal } from '@/components/ExportModal'
import { cn, formatEntityName } from '@/lib/utils'
import {
  ProfileViewer,
  SceneViewer,
  DefaultViewer,
} from '@/components/ArtifactViewers'
import { ProvenanceBadge } from '@/components/ProvenanceBadge'
import {
  useArtifact,
  useArtifactGroups,
  useEntityDetails,
  useEntityGraph,
  useEntityResolver,
  useEntityNavigation,
  useSceneIndex,
  type ResolvedLink,
} from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { HealthBadge } from '@/components/HealthBadge'

// --- Config ---

const sectionConfig: Record<string, {
  artifactType: string
  icon: typeof FileText
  label: string
  color: string
  backPath: string
}> = {
  characters: {
    artifactType: 'character_bible',
    icon: Users,
    label: 'Character',
    color: 'text-amber-400',
    backPath: 'characters',
  },
  locations: {
    artifactType: 'location_bible',
    icon: MapPin,
    label: 'Location',
    color: 'text-rose-400',
    backPath: 'locations',
  },
  props: {
    artifactType: 'prop_bible',
    icon: Wrench,
    label: 'Prop',
    color: 'text-orange-400',
    backPath: 'props',
  },
  scenes: {
    artifactType: 'scene',
    icon: Clapperboard,
    label: 'Scene',
    color: 'text-violet-400',
    backPath: 'scenes',
  },
}

// --- Helpers ---

/** Renders a name as a link if resolvable, plain text otherwise */
function EntityLink({
  resolved,
  label,
  icon: Icon,
  iconColor,
  showArrow,
  compact,
  suffix,
}: {
  resolved: ResolvedLink | null
  label: string
  icon?: typeof Users
  iconColor?: string
  showArrow?: boolean
  /** If true, renders as an inline chip. If false, renders full-width with truncation. */
  compact?: boolean
  /** Optional element rendered after the label (e.g. ownership badge). */
  suffix?: React.ReactNode
}) {
  const ArrowRight = ChevronRight
  const baseClass = compact
    ? 'inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium hover:bg-accent/50 transition-colors'
    : 'flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-accent/50 transition-colors min-w-0 max-w-full'

  if (resolved) {
    return (
      <Link to={resolved.path} className={baseClass}>
        {Icon && <Icon className={cn('h-3 w-3 shrink-0', iconColor)} />}
        <span className={compact ? undefined : 'truncate'}>{label}</span>
        {suffix}
        {showArrow && <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />}
      </Link>
    )
  }
  return (
    <span
      className={cn(baseClass, 'opacity-50 cursor-default hover:bg-transparent')}
      title="Reference not yet linked"
    >
      {Icon && <Icon className="h-3 w-3 shrink-0" />}
      <span className={compact ? undefined : 'truncate'}>{label}</span>
      {suffix}
    </span>
  )
}

// --- Cross-Reference Components ---

type CrossRefPanel = {
  type: string
  label: string
  Icon: typeof Users
  color: string
  items: Array<{ id: string; label: string; resolved: ResolvedLink | null; sceneCount: number; relType: string }>
}

/**
 * Unified cross-reference grid: Characters, Locations, Props, Scene Appearances.
 * Each group is a panel card; panels flow in a 2-column grid.
 * Replaces the old separate RelationshipsSection + SceneAppearances.
 */
const normalizeHeading = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')

function CrossReferencesGrid({
  entityId,
  graphData,
  sceneRefs,
  sceneIndexData,
  resolve,
}: {
  entityId: string
  graphData: Record<string, unknown> | undefined
  sceneRefs: string[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sceneIndexData: any
  resolve: (name: string, type?: 'character' | 'location' | 'prop' | 'scene') => ResolvedLink | null
}) {
  const edges = graphData
    ? ((graphData.edges as Array<Record<string, unknown>> | undefined) ?? [])
    : []

  // Collect edges involving this entity, annotated with the "other" side
  type RawEdge = { otherId: string; otherType: string; relType: string; sceneRefs: string[] }
  const relevantEdges: RawEdge[] = edges
    .filter(e => {
      const src = (e.source_id as string)?.toLowerCase()
      const tgt = (e.target_id as string)?.toLowerCase()
      const eid = entityId.toLowerCase()
      return src === eid || tgt === eid
    })
    .map(e => {
      const isSource = (e.source_id as string)?.toLowerCase() === entityId.toLowerCase()
      return {
        otherId: isSource ? (e.target_id as string) : (e.source_id as string),
        otherType: isSource ? (e.target_type as string) : (e.source_type as string),
        relType: e.relationship_type as string,
        sceneRefs: (e.scene_refs as string[] | undefined) ?? [],
      }
    })

  // Deduplicate: one entry per entity — prefer named relationship over co-occurrence
  // Accumulate all scene_refs across duplicate edges so count is maximally accurate
  const deduped = new Map<string, RawEdge>()
  for (const edge of relevantEdges) {
    const existing = deduped.get(edge.otherId)
    if (!existing) {
      deduped.set(edge.otherId, { ...edge })
    } else {
      // Prefer named relationship type; merge scene refs for accurate count
      const preferNamed = existing.relType === 'co-occurrence' && edge.relType !== 'co-occurrence'
      const mergedRefs = Array.from(new Set([...existing.sceneRefs, ...edge.sceneRefs]))
      deduped.set(edge.otherId, {
        ...preferNamed ? edge : existing,
        sceneRefs: mergedRefs,
      })
    }
  }
  const uniqueEdges = Array.from(deduped.values())

  // Sort helper: by scene count desc, then alphabetically
  const bySceneCount = (
    a: { sceneCount: number; label: string },
    b: { sceneCount: number; label: string },
  ) => b.sceneCount - a.sceneCount || a.label.localeCompare(b.label)

  // Build panels in display order
  const knownTypes = new Set(['character', 'location', 'prop'])
  const groupDefs: Array<{ type: string; label: string; Icon: typeof Users; color: string }> = [
    { type: 'character', label: 'Characters', Icon: Users, color: 'text-amber-400' },
    { type: 'location', label: 'Locations', Icon: MapPin, color: 'text-rose-400' },
    { type: 'prop', label: 'Props', Icon: Wrench, color: 'text-orange-400' },
    { type: 'other', label: 'Other', Icon: Globe, color: 'text-emerald-400' },
  ]

  const panels: CrossRefPanel[] = []
  for (const def of groupDefs) {
    const group = uniqueEdges.filter(e =>
      def.type === 'other' ? !knownTypes.has(e.otherType) : e.otherType === def.type,
    )
    if (group.length === 0) continue
    const items = group.map(e => ({
      id: e.otherId,
      label: formatEntityName(e.otherId),
      resolved: resolve(e.otherId, e.otherType as 'character' | 'location' | 'prop'),
      sceneCount: e.sceneRefs.length,
      relType: e.relType,
    }))
    if (def.type === 'prop') {
      // Signature props first (sorted within), then co-occurrence props (sorted within)
      const signature = items.filter(i => i.relType === 'signature_prop_of').sort(bySceneCount)
      const encountered = items.filter(i => i.relType !== 'signature_prop_of').sort(bySceneCount)
      panels.push({ ...def, items: [...signature, ...encountered] })
    } else {
      panels.push({ ...def, items: items.sort(bySceneCount) })
    }
  }

  // Scene appearances panel — sorted by script order (scene_number ascending)
  if (sceneRefs.length > 0) {
    // Build heading → scene_number lookup from the scene index artifact
    const headingToNumber = new Map<string, number>()
    const entries: Array<{ heading?: string; scene_number?: number }> =
      sceneIndexData?.payload?.data?.entries ?? []
    for (const entry of entries) {
      if (entry.heading) {
        headingToNumber.set(normalizeHeading(entry.heading), entry.scene_number ?? 0)
      }
    }
    const getSceneNum = (ref: string): number => {
      const key = normalizeHeading(ref)
      if (headingToNumber.has(key)) return headingToNumber.get(key)!
      // Fallback: prefix match (handles colon-suffixed headings)
      for (const [h, n] of headingToNumber) {
        if (key.startsWith(h)) return n
      }
      return 9999 // unknown scenes go to end
    }
    const sortedRefs = [...sceneRefs].sort((a, b) => getSceneNum(a) - getSceneNum(b))
    panels.push({
      type: 'scene',
      label: 'Scene Appearances',
      Icon: Clapperboard,
      color: 'text-violet-400',
      items: sortedRefs.map(ref => ({
        id: ref,
        label: ref,
        resolved: resolve(ref, 'scene'),
        sceneCount: 0,
        relType: 'presence',
      })),
    })
  }

  if (panels.length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-4">
      {panels.map(panel => (
        <Card key={panel.type}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <panel.Icon className={cn('h-4 w-4', panel.color)} />
              {panel.label} ({panel.items.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              {panel.items.map(item => (
                <EntityLink
                  key={item.id}
                  resolved={item.resolved}
                  label={item.label}
                  icon={panel.Icon}
                  iconColor={panel.color}
                  suffix={panel.type === 'prop' && item.relType === 'signature_prop_of'
                    ? <span title="Signature prop" className="ml-auto shrink-0"><Star className="h-3 w-3 text-amber-400 fill-amber-400" /></span>
                    : undefined}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/** Entity roster for a scene — lists characters, location, and inferred props */
function SceneEntityRoster({
  sceneData,
  resolve,
  propsInScene,
}: {
  sceneData: Record<string, unknown>
  resolve: (name: string, type?: 'character' | 'location' | 'prop') => ResolvedLink | null
  propsInScene: Array<{ entity_id: string | null; name: string; path: string }>
}) {
  const characters = (sceneData.characters_present as string[] | undefined) ?? []
  const location = sceneData.location as string | undefined

  if (characters.length === 0 && !location && propsInScene.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Users className="h-4 w-4 text-amber-400" />
          Entity Roster
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {characters.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-2">Characters ({characters.length})</p>
            <div className="flex flex-wrap gap-1.5">
              {characters.map(charName => (
                <EntityLink
                  key={charName}
                  resolved={resolve(charName, 'character')}
                  label={charName}
                  icon={Users}
                  iconColor="text-amber-400"
                  showArrow
                  compact
                />
              ))}
            </div>
          </div>
        )}

        {location && (
          <div>
            <p className="text-xs text-muted-foreground mb-2">Location</p>
            <EntityLink
              resolved={resolve(location, 'location')}
              label={location}
              icon={MapPin}
              iconColor="text-rose-400"
              showArrow
              compact
            />
          </div>
        )}

        {propsInScene.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-2">Props ({propsInScene.length})</p>
            <div className="flex flex-wrap gap-1.5">
              {propsInScene.map(prop => (
                <EntityLink
                  key={prop.entity_id}
                  resolved={{ path: prop.path, label: prop.name }}
                  label={prop.name}
                  icon={Wrench}
                  iconColor="text-orange-400"
                  showArrow
                  compact
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// --- Main Component ---

export default function EntityDetailPage({ section }: { section: string }) {
  const { projectId, entityId } = useParams()
  const navigate = useNavigate()
  const [showRawJson, setShowRawJson] = useState(false)
  const [isExportOpen, setIsExportOpen] = useState(false)

  const config = sectionConfig[section]
  const Icon = config?.icon || FileText

  // Navigation and keyboard shortcuts
  const nav = useEntityNavigation(projectId, section, entityId)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      if (e.key === 'ArrowLeft' && nav.prev) {
        navigate(`/${projectId}/${section}/${nav.prev}`)
      } else if (e.key === 'ArrowRight' && nav.next) {
        navigate(`/${projectId}/${section}/${nav.next}`)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [projectId, section, nav.prev, nav.next, navigate])

  // Global entity resolver for all cross-reference links
  const { resolve } = useEntityResolver(projectId)

  // Scene index for script-order sorting of Scene Appearances
  const { data: sceneIndexData } = useSceneIndex(projectId)

  // Resolve latest version from artifact groups
  const { data: groups, isLoading: groupsLoading } = useArtifactGroups(projectId)
  const group = groups?.find(
    g => g.artifact_type === config?.artifactType && g.entity_id === entityId
  )
  const latestVersion = group?.latest_version

  // Fetch artifact detail
  const {
    data: artifact,
    isLoading: artifactLoading,
    error: artifactError,
  } = useArtifact(projectId, config?.artifactType, entityId, latestVersion)

  // Fetch entity graph for cross-references (characters, locations, props)
  const { data: graphArtifact } = useEntityGraph(
    section !== 'scenes' ? projectId : undefined,
  )
  const graphData = graphArtifact?.payload?.data as Record<string, unknown> | undefined

  // Infer props for scene detail pages: filter all prop bibles by scene_presence
  const { data: propEntities } = useEntityDetails(
    section === 'scenes' ? projectId : undefined,
    'prop_bible',
  )
  const propsInScene = useMemo(() => {
    if (!entityId || !propEntities) return []
    return propEntities
      .filter(p => (p.data?.scene_presence as string[] | undefined)?.includes(entityId))
      .map(p => ({
        entity_id: p.entity_id,
        name: (p.data?.name as string | undefined) ?? formatEntityName(p.entity_id ?? ''),
        path: `/${projectId}/props/${p.entity_id}`,
      }))
  }, [propEntities, entityId, projectId])

  if (!config || !projectId || !entityId) {
    return <ErrorState message="Invalid entity route" />
  }

  const isLoading = groupsLoading || artifactLoading

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (artifactError) {
    return (
      <div>
        <BackButton section={config.backPath} projectId={projectId} />
        <ErrorState message={artifactError instanceof Error ? artifactError.message : 'Failed to load'} />
      </div>
    )
  }

  if (!artifact || !group) {
    return (
      <div>
        <BackButton section={config.backPath} projectId={projectId} />
        <EmptyState
          icon={config.icon}
          title={`${config.label} not found`}
          description={`No ${config.label.toLowerCase()} artifact found for "${formatEntityName(entityId)}".`}
        />
      </div>
    )
  }

  const data = artifact.payload?.data as Record<string, unknown> | undefined
  const displayName = (
    data?.display_name ??
    data?.name ??
    data?.heading ??
    data?.scene_heading ??
    data?.title ??
    formatEntityName(entityId)
  ) as string

  const meta = artifact.payload?.metadata as Record<string, unknown> | undefined

  // Extract cross-reference data from artifact
  const scenePresence = (data?.scene_presence as string[] | undefined) ?? []

  // Section header label for the main content card
  const profileLabel = section === 'scenes' ? 'Scene' : 'Profile'

  // Render appropriate viewer
  function renderContent() {
    if (!data) return null

    if (showRawJson) return <DefaultViewer data={data} />

    switch (config.artifactType) {
      case 'character_bible':
        return <ProfileViewer data={data} profileType="character" />
      case 'location_bible':
        return <ProfileViewer data={data} profileType="location" />
      case 'prop_bible':
        return <ProfileViewer data={data} profileType="prop" />
      case 'scene':
        return <SceneViewer data={data} />
      default:
        return <DefaultViewer data={data} />
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back navigation */}
      <div className="flex items-center justify-between">
        <BackButton section={config.backPath} projectId={projectId} />

        <div className="flex items-center gap-2">
          {/* Main sequence nav (respects current sort) */}
          <div className="flex items-center bg-card border border-border rounded-lg overflow-hidden h-9">
            <Button
              variant="ghost"
              size="sm"
              className="h-full rounded-none px-2 border-r border-border"
              disabled={!nav.prev}
              onClick={() => navigate(`/${projectId}/${section}/${nav.prev}`)}
              title={`Previous ${config.label} (${nav.sortMode} ${nav.sortDirection}) [Left Arrow]`}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="px-3 text-xs font-medium text-muted-foreground bg-muted/30 h-full flex items-center">
              {nav.sortMode === 'script-order' ? 'Script Order' : nav.sortMode === 'alphabetical' ? 'A–Z' : 'Prominence'}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-full rounded-none px-2 border-l border-border"
              disabled={!nav.next}
              onClick={() => navigate(`/${projectId}/${section}/${nav.next}`)}
              title={`Next ${config.label} (${nav.sortMode} ${nav.sortDirection}) [Right Arrow]`}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Scene-specific chronological nav (always script order) */}
          {section === 'scenes' && (nav.prevChronological || nav.nextChronological) && (
            <div className="flex items-center bg-card border border-border rounded-lg overflow-hidden h-9">
              <Button
                variant="ghost"
                size="sm"
                className="h-full rounded-none px-2 border-r border-border"
                disabled={!nav.prevChronological}
                onClick={() => navigate(`/${projectId}/${section}/${nav.prevChronological}`)}
                title="Previous Chronological Scene"
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <div className="px-3 text-xs font-medium text-muted-foreground bg-muted/30 h-full flex items-center">
                Chronological
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-full rounded-none px-2 border-l border-border"
                disabled={!nav.nextChronological}
                onClick={() => navigate(`/${projectId}/${section}/${nav.nextChronological}`)}
                title="Next Chronological Scene"
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="rounded-lg bg-card border border-border p-2.5">
          <Icon className={cn('h-6 w-6', config.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight truncate">{displayName}</h1>
            <HealthBadge health={group.health} />
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground flex-wrap">
            <span>{config.label}</span>
            <span className="text-muted-foreground/50">&middot;</span>
            <span className="flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5" />
              v{group.latest_version}
            </span>
            {meta && (
              <>
                <span className="text-muted-foreground/50">&middot;</span>
                <ProvenanceBadge
                  model={
                    (meta.producing_role as string) ||
                    (meta.producing_module as string) ||
                    'unknown'
                  }
                  confidence={
                    typeof meta.confidence === 'number'
                      ? Math.round(meta.confidence * 100)
                      : 0
                  }
                  rationale={
                    (meta.rationale as string) ||
                    (meta.intent as string) ||
                    undefined
                  }
                />
              </>
            )}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => setIsExportOpen(true)}>
          <Share className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* === Bible-type pages (character / location / prop) === */}
      {section !== 'scenes' && (
        <>
          {/* 1. Profile — most important: who/what this entity is */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <h2 className="text-sm font-semibold">{profileLabel}</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRawJson(!showRawJson)}
                className="gap-1.5"
              >
                <Code className="h-3.5 w-3.5" />
                {showRawJson ? 'View Formatted' : 'View Raw JSON'}
              </Button>
            </CardHeader>
            <CardContent>
              {renderContent()}
              {/* Ownership row — only for props with signature_prop_of edges */}
              {section === 'props' && (() => {
                const edges = (graphData?.edges as Array<Record<string, unknown>> | undefined) ?? []
                const owners = edges
                  .filter(e =>
                    (e.source_id as string)?.toLowerCase() === entityId.toLowerCase() &&
                    e.relationship_type === 'signature_prop_of',
                  )
                  .map(e => e.target_id as string)
                if (owners.length === 0) return null
                return (
                  <div className="mt-4 pt-4 border-t border-border flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground shrink-0">Owned by</span>
                    {owners.map(charId => (
                      <EntityLink
                        key={charId}
                        resolved={resolve(charId, 'character')}
                        label={formatEntityName(charId)}
                        icon={Users}
                        iconColor="text-amber-400"
                        compact
                      />
                    ))}
                  </div>
                )
              })()}
            </CardContent>
          </Card>

          {/* 2. Cross-references: Characters, Locations, Props, Scene Appearances */}
          <CrossReferencesGrid
            entityId={entityId}
            graphData={graphData}
            sceneRefs={scenePresence}
            sceneIndexData={sceneIndexData}
            resolve={resolve}
          />
        </>
      )}

      {/* === Scene pages === */}
      {section === 'scenes' && data && (
        <>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => navigate(`/${projectId}?scene=${encodeURIComponent(displayName)}`)}
          >
            <FileText className="h-3.5 w-3.5" />
            View in Script
          </Button>

          {/* 1. Entity Roster — who's in the scene */}
          <SceneEntityRoster sceneData={data} resolve={resolve} propsInScene={propsInScene} />

          {/* 2. Scene details */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <h2 className="text-sm font-semibold">{profileLabel}</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRawJson(!showRawJson)}
                className="gap-1.5"
              >
                <Code className="h-3.5 w-3.5" />
                {showRawJson ? 'View Formatted' : 'View Raw JSON'}
              </Button>
            </CardHeader>
            <CardContent>
              {renderContent()}
            </CardContent>
          </Card>
        </>
      )}

      {/* Bible Files (if present) */}
      {artifact.bible_files && Object.keys(artifact.bible_files).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <h2 className="text-sm font-semibold">Bible Files</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(artifact.bible_files).map(([filename, content]) => (
                <details key={filename} className="group">
                  <summary className="cursor-pointer rounded-md border border-border bg-muted/30 p-2 text-sm font-medium hover:bg-muted/50 transition-colors">
                    <span className="font-mono text-xs">{filename}</span>
                  </summary>
                  <div className="mt-2 rounded-md bg-muted p-3">
                    <pre className="font-mono text-xs text-foreground whitespace-pre-wrap overflow-x-auto">
                      {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                    </pre>
                  </div>
                </details>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId!}
        defaultScope="single"
        entityId={entityId}
        entityType={section === 'scenes' ? 'scene' : section === 'characters' ? 'character' : section === 'locations' ? 'location' : 'prop'}
      />
    </div>
  )
}

function BackButton({ section, projectId }: { section: string; projectId: string }) {
  const goBack = useHistoryBack(`/${projectId}/${section}`)
  return (
    <div>
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5 text-muted-foreground hover:text-foreground"
        onClick={goBack}
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>
    </div>
  )
}
