/**
 * Unified entity list page — parameterized by section.
 * Replaces CharactersList, LocationsList, PropsList, and ScenesList.
 * Follows the same config-driven pattern as EntityDetailPage.
 */
import { useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Users, MapPin, Wrench, Clapperboard, Share } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ListSkeleton, EmptyState, ErrorState } from '@/components/StateViews'
import { EntityListControls } from '@/components/EntityListControls'
import { ExportModal } from '@/components/ExportModal'
import { HealthBadge } from '@/components/HealthBadge'
import { type SortMode, type ViewDensity, type SortDirection } from '@/lib/types'
import { useEntityDetails, useEntityGraph, useScenes, useStickyPreference } from '@/lib/hooks'
import { cn, formatEntityName } from '@/lib/utils'
import type { ExportScope } from '@/lib/api'

// --- Config ---

export type EntitySection = 'characters' | 'locations' | 'props' | 'scenes'

type BibleArtifactType = 'character_bible' | 'location_bible' | 'prop_bible'

const sectionConfig: Record<EntitySection, {
  icon: typeof Users
  color: string
  label: string
  description: string
  artifactType: BibleArtifactType | 'scene'
  exportScope: ExportScope
  emptyTitle: string
  emptyDescription: string
}> = {
  characters: {
    icon: Users,
    color: 'text-amber-400',
    label: 'Characters',
    description: 'All characters discovered in your screenplay',
    artifactType: 'character_bible',
    exportScope: 'characters',
    emptyTitle: 'No characters yet',
    emptyDescription: 'Run the world-building pipeline to extract character profiles',
  },
  locations: {
    icon: MapPin,
    color: 'text-rose-400',
    label: 'Locations',
    description: 'All locations discovered in your screenplay',
    artifactType: 'location_bible',
    exportScope: 'locations',
    emptyTitle: 'No locations yet',
    emptyDescription: 'Run the world-building pipeline to extract location profiles',
  },
  props: {
    icon: Wrench,
    color: 'text-orange-400',
    label: 'Props',
    description: 'All props discovered in your screenplay',
    artifactType: 'prop_bible',
    exportScope: 'props',
    emptyTitle: 'No props yet',
    emptyDescription: 'Run the world-building pipeline to extract prop details',
  },
  scenes: {
    icon: Clapperboard,
    color: 'text-primary',
    label: 'Scenes',
    description: 'All scenes extracted from your screenplay',
    artifactType: 'scene',
    exportScope: 'scenes',
    emptyTitle: 'No scenes yet',
    emptyDescription: 'Run the pipeline to extract scenes from your screenplay',
  },
}

// --- Sort helpers ---

function sortBibleEntities(
  items: Array<{ entity_id: string; sceneCount: number; firstSceneNumber: number | null }>,
  sortMode: SortMode,
): Array<typeof items[number]> {
  const sorted = [...items]
  switch (sortMode) {
    case 'script-order':
      sorted.sort((a, b) => {
        if (a.firstSceneNumber === null && b.firstSceneNumber === null) return 0
        if (a.firstSceneNumber === null) return 1
        if (b.firstSceneNumber === null) return -1
        return a.firstSceneNumber - b.firstSceneNumber
      })
      break
    case 'alphabetical':
      sorted.sort((a, b) =>
        formatEntityName(a.entity_id).localeCompare(
          formatEntityName(b.entity_id),
          undefined,
          { sensitivity: 'base' },
        ),
      )
      break
    case 'prominence':
      sorted.sort((a, b) => (b.sceneCount || 0) - (a.sceneCount || 0))
      break
  }
  return sorted
}

function sortScenes(
  items: Array<{ index: number; heading: string }>,
  sortMode: SortMode,
): Array<typeof items[number]> {
  const sorted = [...items]
  switch (sortMode) {
    case 'script-order':
      sorted.sort((a, b) => a.index - b.index)
      break
    case 'alphabetical':
      sorted.sort((a, b) =>
        a.heading.toLowerCase().localeCompare(b.heading.toLowerCase()),
      )
      break
    case 'prominence':
      sorted.sort((a, b) => {
        const lenDiff = b.heading.length - a.heading.length
        return lenDiff !== 0 ? lenDiff : a.index - b.index
      })
      break
  }
  return sorted
}

// --- Scene INT/EXT badge helper ---

function getIntExtVariant(intExt: string): 'default' | 'secondary' | 'outline' {
  if (intExt === 'INT') return 'default'
  if (intExt === 'EXT') return 'secondary'
  return 'outline'
}

function IntExtBadge({ intExt }: { intExt: string }) {
  return (
    <Badge
      variant={getIntExtVariant(intExt)}
      className={cn(
        intExt === 'INT' && 'bg-blue-500/20 text-blue-400',
        intExt === 'EXT' && 'bg-green-500/20 text-green-400',
        intExt === 'INT/EXT' && 'bg-amber-500/20 text-amber-400',
      )}
    >
      {intExt}
    </Badge>
  )
}

// --- Bible entity card renderers (characters, locations, props) ---

interface BibleEntity {
  entity_id: string
  latest_version: number
  health: string | null
  description?: string
  sceneCount: number
  firstSceneNumber: number | null
}

function OwnerPills({ owners, projectId }: { owners: string[]; projectId: string }) {
  if (owners.length === 0) return null
  return (
    <>
      {owners.map(charId => (
        <Link
          key={charId}
          to={`/${projectId}/characters/${charId}`}
          onClick={e => e.stopPropagation()}
          className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-xs font-medium hover:bg-accent/50 transition-colors shrink-0"
        >
          <Users className="h-3 w-3 text-amber-400 shrink-0" />
          {formatEntityName(charId)}
        </Link>
      ))}
    </>
  )
}

function BibleCompactRow({
  item, icon: Icon, color, section, projectId, navigate, owners,
}: {
  item: BibleEntity; icon: typeof Users; color: string; section: string
  projectId: string; navigate: (path: string) => void; owners: string[]
}) {
  return (
    <div
      className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
      onClick={() => navigate(`/${projectId}/${section}/${item.entity_id}`)}
    >
      <Icon className={`h-4 w-4 ${color} flex-shrink-0`} />
      <span className="font-medium flex-1 truncate">
        {formatEntityName(item.entity_id)}
      </span>
      <OwnerPills owners={owners} projectId={projectId} />
      {item.sceneCount != null && item.sceneCount > 0 && (
        <span className="text-xs text-muted-foreground">
          {item.sceneCount} {item.sceneCount === 1 ? 'scene' : 'scenes'}
        </span>
      )}
      <Badge variant="outline" className="text-xs">
        v{item.latest_version}
      </Badge>
      <HealthBadge health={item.health} />
    </div>
  )
}

function BibleMediumCard({
  item, icon: Icon, color, section, projectId, navigate, owners,
}: {
  item: BibleEntity; icon: typeof Users; color: string; section: string
  projectId: string; navigate: (path: string) => void; owners: string[]
}) {
  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent/50"
      onClick={() => navigate(`/${projectId}/${section}/${item.entity_id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Icon className={`h-5 w-5 ${color} mt-0.5 flex-shrink-0`} />
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate mb-2">
              {formatEntityName(item.entity_id)}
            </h3>
            {item.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                {item.description}
              </p>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <OwnerPills owners={owners} projectId={projectId} />
              {item.sceneCount != null && item.sceneCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {item.sceneCount} {item.sceneCount === 1 ? 'scene' : 'scenes'}
                </Badge>
              )}
              <Badge variant="outline" className="text-xs">
                v{item.latest_version}
              </Badge>
              <HealthBadge health={item.health} />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function BibleLargeCard({
  item, icon: Icon, color, section, projectId, navigate, owners,
}: {
  item: BibleEntity; icon: typeof Users; color: string; section: string
  projectId: string; navigate: (path: string) => void; owners: string[]
}) {
  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent/50"
      onClick={() => navigate(`/${projectId}/${section}/${item.entity_id}`)}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-3">
          <Icon className={`h-5 w-5 ${color} mt-0.5 flex-shrink-0`} />
          <div className="flex-1 min-w-0">
            <h3 className="font-medium mb-3">
              {formatEntityName(item.entity_id)}
            </h3>
            {item.description && (
              <p className="text-sm text-muted-foreground mb-4">
                {item.description}
              </p>
            )}
            <div className="flex items-center gap-2 flex-wrap mb-3">
              <OwnerPills owners={owners} projectId={projectId} />
              {item.sceneCount != null && item.sceneCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {item.sceneCount} {item.sceneCount === 1 ? 'scene' : 'scenes'}
                </Badge>
              )}
              {item.firstSceneNumber !== null && (
                <span className="text-xs text-muted-foreground">
                  First appearance: Scene {item.firstSceneNumber}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                v{item.latest_version}
              </Badge>
              <HealthBadge health={item.health} />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Scene card renderers ---

interface SceneItem {
  index: number
  heading: string
  intExt: string
  timeOfDay: string | null
  summary: string
  entityId: string
}

function SceneCompactRow({
  item, projectId, navigate,
}: { item: SceneItem; projectId: string; navigate: (path: string) => void }) {
  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg border border-border cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={() => navigate(`/${projectId}/scenes/${item.entityId}`)}
    >
      <Badge variant="outline">Scene {item.index}</Badge>
      <span className="font-medium flex-1 truncate">{item.heading}</span>
      <IntExtBadge intExt={item.intExt} />
      {item.timeOfDay && (
        <span className="text-sm text-muted-foreground">{item.timeOfDay}</span>
      )}
    </div>
  )
}

function SceneMediumCard({
  item, projectId, navigate,
}: { item: SceneItem; projectId: string; navigate: (path: string) => void }) {
  return (
    <Card
      className="cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={() => navigate(`/${projectId}/scenes/${item.entityId}`)}
    >
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline">Scene {item.index}</Badge>
          <IntExtBadge intExt={item.intExt} />
        </div>
        <h3 className="font-semibold text-lg line-clamp-1">{item.heading}</h3>
        {item.timeOfDay && (
          <p className="text-sm text-muted-foreground">{item.timeOfDay}</p>
        )}
        <p className="text-sm text-muted-foreground line-clamp-2">{item.summary}</p>
      </CardContent>
    </Card>
  )
}

function SceneLargeCard({
  item, projectId, navigate,
}: { item: SceneItem; projectId: string; navigate: (path: string) => void }) {
  return (
    <Card
      className="cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={() => navigate(`/${projectId}/scenes/${item.entityId}`)}
    >
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline">Scene {item.index}</Badge>
          <IntExtBadge intExt={item.intExt} />
        </div>
        <h3 className="font-semibold text-xl">{item.heading}</h3>
        {item.timeOfDay && (
          <p className="text-sm text-muted-foreground">{item.timeOfDay}</p>
        )}
        <p className="text-sm text-muted-foreground">{item.summary}</p>
      </CardContent>
    </Card>
  )
}

// --- Grid layouts per density ---

const gridClass: Record<ViewDensity, string> = {
  compact: 'space-y-2',
  medium: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4',
  large: 'grid grid-cols-1 md:grid-cols-2 gap-4',
}

// --- Main component ---

export default function EntityListPage({ section }: { section: EntitySection }) {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [isExportOpen, setIsExportOpen] = useState(false)

  const config = sectionConfig[section]
  const Icon = config.icon

  const [sortMode, setSortMode] = useStickyPreference<SortMode>(projectId, `${section}.sort`, 'script-order')
  const [density, setDensity] = useStickyPreference<ViewDensity>(projectId, `${section}.density`, 'medium')
  const [direction, setDirection] = useStickyPreference<SortDirection>(projectId, `${section}.direction`, 'asc')

  // Data hooks — bible entities vs scenes
  const isBible = section !== 'scenes'
  const bibleResult = useEntityDetails(isBible ? projectId! : '', isBible ? config.artifactType as BibleArtifactType : 'character_bible')
  const scenesResult = useScenes(isBible ? '' : projectId!)

  // Prop ownership map — only loaded for the props section
  const { data: graphArtifact } = useEntityGraph(section === 'props' ? projectId : undefined)
  const propOwners = useMemo<Record<string, string[]>>(() => {
    if (section !== 'props' || !graphArtifact) return {}
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const edges = ((graphArtifact as any)?.payload?.data?.edges as Array<Record<string, unknown>> | undefined) ?? []
    const map: Record<string, string[]> = {}
    for (const edge of edges) {
      if (edge.relationship_type === 'signature_prop_of') {
        const propId = edge.source_id as string
        const charId = edge.target_id as string
        if (propId && charId) {
          ;(map[propId] ??= []).push(charId)
        }
      }
    }
    return map
  }, [graphArtifact, section])

  const data = isBible ? bibleResult.data : scenesResult.data
  const isLoading = isBible ? bibleResult.isLoading : scenesResult.isLoading
  const error = isBible ? bibleResult.error : null

  // Sort
  const sortedItems = useMemo(() => {
    if (!data) return [] as unknown[]
    let sorted: unknown[]
    if (isBible) {
      sorted = sortBibleEntities(data as BibleEntity[], sortMode)
    } else {
      sorted = sortScenes(data as SceneItem[], sortMode)
    }
    if (direction === 'desc') {
      sorted = [...sorted].reverse()
    }
    return sorted
  }, [data, sortMode, direction, isBible])

  // Guards
  if (isLoading) return <ListSkeleton />

  if (error) {
    return <ErrorState message={`Failed to load ${config.label.toLowerCase()}`} />
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={config.icon}
        title={config.emptyTitle}
        description={config.emptyDescription}
      />
    )
  }

  // Render card list
  function renderItems() {
    if (isBible) {
      const items = sortedItems as BibleEntity[]
      const CardComponent = density === 'compact' ? BibleCompactRow
        : density === 'medium' ? BibleMediumCard
        : BibleLargeCard
      return (
        <div className={density === 'compact' ? 'space-y-1' : gridClass[density]}>
          {items.map(item => (
            <CardComponent
              key={item.entity_id}
              item={item}
              icon={Icon}
              color={config.color}
              section={section}
              projectId={projectId!}
              navigate={navigate}
              owners={propOwners[item.entity_id] ?? []}
            />
          ))}
        </div>
      )
    }

    // Scenes
    const items = sortedItems as SceneItem[]
    return (
      <div className={gridClass[density]}>
        {items.map(item => {
          if (density === 'compact') {
            return <SceneCompactRow key={item.index} item={item} projectId={projectId!} navigate={navigate} />
          }
          if (density === 'medium') {
            return <SceneMediumCard key={item.index} item={item} projectId={projectId!} navigate={navigate} />
          }
          return <SceneLargeCard key={item.index} item={item} projectId={projectId!} navigate={navigate} />
        })}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Icon className={`h-6 w-6 ${config.color}`} />
            <h1 className="text-2xl font-semibold">{config.label}</h1>
            <Badge variant="outline" className="ml-2">
              {data.length}
            </Badge>
          </div>
          <p className="text-muted-foreground">{config.description}</p>
        </div>
        <Button variant="outline" onClick={() => setIsExportOpen(true)}>
          <Share className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Controls */}
      <EntityListControls
        sort={sortMode}
        onSortChange={setSortMode}
        density={density}
        onDensityChange={setDensity}
        direction={direction}
        onDirectionChange={setDirection}
      />

      {/* Items */}
      {renderItems()}

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId!}
        defaultScope={config.exportScope}
      />
    </div>
  )
}
