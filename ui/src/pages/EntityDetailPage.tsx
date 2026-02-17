import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Users,
  MapPin,
  Wrench,
  Clapperboard,
  FileText,
  GitBranch,
  AlertTriangle,
  Code,
  Globe,
  ArrowRight,
} from 'lucide-react'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import {
  ProfileViewer,
  SceneViewer,
  DefaultViewer,
} from '@/components/ArtifactViewers'
import { ProvenanceBadge } from '@/components/ProvenanceBadge'
import {
  useArtifact,
  useArtifactGroups,
  useEntityGraph,
  useEntityResolver,
  type ResolvedLink,
} from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'

// --- Config ---

const sectionConfig: Record<string, {
  artifactType: string
  icon: typeof FileText
  label: string
  color: string
  backLabel: string
  backPath: string
}> = {
  characters: {
    artifactType: 'character_bible',
    icon: Users,
    label: 'Character',
    color: 'text-amber-400',
    backLabel: 'Characters',
    backPath: 'characters',
  },
  locations: {
    artifactType: 'location_bible',
    icon: MapPin,
    label: 'Location',
    color: 'text-rose-400',
    backLabel: 'Locations',
    backPath: 'locations',
  },
  props: {
    artifactType: 'prop_bible',
    icon: Wrench,
    label: 'Prop',
    color: 'text-orange-400',
    backLabel: 'Props',
    backPath: 'props',
  },
  scenes: {
    artifactType: 'scene',
    icon: Clapperboard,
    label: 'Scene',
    color: 'text-violet-400',
    backLabel: 'Scenes',
    backPath: 'scenes',
  },
}

// --- Helpers ---

function formatEntityName(entityId: string): string {
  return entityId
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function healthBadge(health: string | null) {
  if (!health) return null
  if (health === 'valid' || health === 'healthy') {
    return (
      <Badge variant="outline" className="text-xs text-green-400 border-green-400/30">
        {health}
      </Badge>
    )
  }
  if (health === 'stale') {
    return (
      <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30 gap-1">
        <AlertTriangle className="h-3 w-3" />
        Stale
      </Badge>
    )
  }
  return (
    <Badge variant="destructive" className="text-xs">
      {health}
    </Badge>
  )
}

/** Renders a name as a link if resolvable, plain text otherwise */
function EntityLink({
  resolved,
  label,
  icon: Icon,
  iconColor,
  showArrow,
  compact,
}: {
  resolved: ResolvedLink | null
  label: string
  icon?: typeof Users
  iconColor?: string
  showArrow?: boolean
  /** If true, renders as an inline chip. If false, renders full-width with truncation. */
  compact?: boolean
}) {
  const baseClass = compact
    ? 'inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium hover:bg-accent/50 transition-colors'
    : 'flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-accent/50 transition-colors min-w-0 max-w-full'

  if (resolved) {
    return (
      <Link to={resolved.path} className={baseClass}>
        {Icon && <Icon className={cn('h-3 w-3 shrink-0', iconColor)} />}
        <span className={compact ? undefined : 'truncate'}>{label}</span>
        {showArrow && <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />}
      </Link>
    )
  }
  return (
    <span className={baseClass}>
      {Icon && <Icon className="h-3 w-3 shrink-0" />}
      <span className={compact ? undefined : 'truncate'}>{label}</span>
    </span>
  )
}

// --- Cross-Reference Components ---

/** Clickable scene appearance links — resolves headings, IDs, etc. via global resolver */
function SceneAppearances({
  sceneRefs,
  resolve,
}: {
  sceneRefs: string[]
  resolve: (name: string, type?: 'scene') => ResolvedLink | null
}) {
  if (sceneRefs.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Clapperboard className="h-4 w-4 text-violet-400" />
          Scene Appearances ({sceneRefs.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {sceneRefs.map(ref => {
            const resolved = resolve(ref, 'scene')
            return (
              <EntityLink
                key={ref}
                resolved={resolved}
                label={ref}
                icon={Clapperboard}
                iconColor="text-violet-400"
              />
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

/** Relationship edges from entity graph */
function RelationshipsSection({
  entityId,
  graphData,
  resolve,
}: {
  entityId: string
  graphData: Record<string, unknown> | undefined
  resolve: (name: string, type?: 'character' | 'location' | 'prop') => ResolvedLink | null
}) {
  if (!graphData) return null

  const edges = (graphData.edges as Array<Record<string, unknown>> | undefined) ?? []

  // Filter edges involving this entity
  const relevantEdges = edges.filter(edge => {
    const sourceId = edge.source_id as string
    const targetId = edge.target_id as string
    const normalizedEntity = entityId.toLowerCase()
    return sourceId?.toLowerCase() === normalizedEntity || targetId?.toLowerCase() === normalizedEntity
  })

  if (relevantEdges.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Globe className="h-4 w-4 text-emerald-400" />
          Relationships ({relevantEdges.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {relevantEdges.map((edge, i) => {
            const sourceId = edge.source_id as string
            const targetId = edge.target_id as string
            const sourceType = edge.source_type as string
            const targetType = edge.target_type as string
            const relType = edge.relationship_type as string
            const confidence = edge.confidence as number | undefined
            const sceneRefs = (edge.scene_refs as string[]) ?? []

            const isSource = sourceId?.toLowerCase() === entityId.toLowerCase()
            const otherId = isSource ? targetId : sourceId
            const otherType = isSource ? targetType : sourceType

            const resolved = resolve(otherId, otherType as 'character' | 'location' | 'prop')

            const TypeIcon = otherType === 'character' ? Users : otherType === 'location' ? MapPin : Wrench
            const typeColor = otherType === 'character' ? 'text-amber-400' : otherType === 'location' ? 'text-rose-400' : 'text-orange-400'

            return (
              <div
                key={i}
                className="flex items-center gap-3 rounded-md border border-border p-2.5 hover:bg-accent/30 transition-colors"
              >
                <TypeIcon className={cn('h-4 w-4 shrink-0', typeColor)} />
                <div className="flex-1 min-w-0">
                  {resolved ? (
                    <Link
                      to={resolved.path}
                      className="text-sm font-medium hover:underline"
                    >
                      {formatEntityName(otherId)}
                    </Link>
                  ) : (
                    <span className="text-sm font-medium">{formatEntityName(otherId)}</span>
                  )}
                  <p className="text-xs text-muted-foreground">{relType}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {sceneRefs.length > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {sceneRefs.length} scene{sceneRefs.length !== 1 ? 's' : ''}
                    </span>
                  )}
                  {confidence != null && (
                    <Badge variant="outline" className="text-xs">
                      {Math.round(confidence * 100)}%
                    </Badge>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

/** Entity roster for a scene — lists characters, location, with clickable links */
function SceneEntityRoster({
  sceneData,
  resolve,
}: {
  sceneData: Record<string, unknown>
  resolve: (name: string, type?: 'character' | 'location' | 'prop') => ResolvedLink | null
}) {
  const characters = (sceneData.characters_present as string[] | undefined) ?? []
  const location = sceneData.location as string | undefined

  if (characters.length === 0 && !location) return null

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
      </CardContent>
    </Card>
  )
}

// --- Main Component ---

export default function EntityDetailPage({ section }: { section: string }) {
  const { projectId, entityId } = useParams()
  const navigate = useNavigate()
  const [showRawJson, setShowRawJson] = useState(false)

  const config = sectionConfig[section]
  if (!config || !projectId || !entityId) {
    return <ErrorState message="Invalid entity route" />
  }

  const Icon = config.icon

  // Global entity resolver for all cross-reference links
  const { resolve } = useEntityResolver(projectId)

  // Resolve latest version from artifact groups
  const { data: groups, isLoading: groupsLoading } = useArtifactGroups(projectId)
  const group = groups?.find(
    g => g.artifact_type === config.artifactType && g.entity_id === entityId
  )
  const latestVersion = group?.latest_version

  // Fetch artifact detail
  const {
    data: artifact,
    isLoading: artifactLoading,
    error: artifactError,
  } = useArtifact(projectId, config.artifactType, entityId, latestVersion)

  // Fetch entity graph for cross-references (characters, locations, props)
  const { data: graphArtifact } = useEntityGraph(
    section !== 'scenes' ? projectId : undefined,
  )
  const graphData = graphArtifact?.payload?.data as Record<string, unknown> | undefined

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
        <BackButton section={config.backPath} projectId={projectId} label={config.backLabel} />
        <ErrorState message={artifactError instanceof Error ? artifactError.message : 'Failed to load'} />
      </div>
    )
  }

  if (!artifact || !group) {
    return (
      <div>
        <BackButton section={config.backPath} projectId={projectId} label={config.backLabel} />
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
      <BackButton section={config.backPath} projectId={projectId} label={config.backLabel} />

      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="rounded-lg bg-card border border-border p-2.5">
          <Icon className={cn('h-6 w-6', config.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight truncate">{displayName}</h1>
            {healthBadge(group.health)}
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
      </div>

      {/* Scene-specific: Jump to Script button + Entity roster */}
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
          <SceneEntityRoster sceneData={data} resolve={resolve} />
        </>
      )}

      {/* Bible-type: Scene appearances */}
      {section !== 'scenes' && scenePresence.length > 0 && (
        <SceneAppearances sceneRefs={scenePresence} resolve={resolve} />
      )}

      {/* Bible-type: Relationships from entity graph */}
      {section !== 'scenes' && graphData && (
        <RelationshipsSection
          entityId={entityId}
          graphData={graphData}
          resolve={resolve}
        />
      )}

      {/* Main content (bible viewer / scene viewer) */}
      <Card>
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <h2 className="text-sm font-semibold">Content</h2>
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
    </div>
  )
}

function BackButton({ section, projectId, label }: { section: string; projectId: string; label: string }) {
  const navigate = useNavigate()
  return (
    <div className="mb-3">
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5 text-muted-foreground hover:text-foreground"
        onClick={() => navigate(`/${projectId}/${section}`)}
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {label}
      </Button>
    </div>
  )
}
