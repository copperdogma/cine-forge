/**
 * ContinuityPage — visualizes entity state timelines and continuity gaps.
 *
 * Loads the continuity_index artifact, shows overview stats (score, gaps,
 * tracked entities), and an expandable list of entity timelines.
 *
 * Depends on Story 092 backend (continuity_tracking_v1 module).
 */
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Activity, AlertTriangle, MapPin, Package, Users } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PageHeader } from '@/components/PageHeader'
import { EmptyState, ListSkeleton } from '@/components/StateViews'
import { EntityTimelineView, type EntityTimelineData } from '@/components/EntityTimelineView'
import { useArtifactGroups, useArtifact } from '@/lib/hooks'
import { formatEntityName } from '@/lib/utils'
import { cn } from '@/lib/utils'

// ---- Domain types --------------------------------------------------------

interface ContinuityIndexData {
  timelines: Record<string, EntityTimelineData>
  total_gaps: number
  overall_continuity_score: number
}

// ---- Helpers -------------------------------------------------------------

function scoreColor(score: number): string {
  if (score >= 0.8) return 'text-emerald-400'
  if (score >= 0.6) return 'text-amber-400'
  return 'text-red-400'
}

function entityTypeIcon(type: string) {
  if (type === 'character') return <Users className="h-4 w-4 shrink-0 text-amber-400" />
  if (type === 'location') return <MapPin className="h-4 w-4 shrink-0 text-rose-400" />
  return <Package className="h-4 w-4 shrink-0 text-orange-400" />
}

// ---- Entity row ----------------------------------------------------------

function EntityRow({
  entityKey,
  timeline,
  isExpanded,
  onToggle,
  projectId,
  groups,
}: {
  entityKey: string
  timeline: EntityTimelineData
  isExpanded: boolean
  onToggle: () => void
  projectId: string
  groups: import('@/lib/types').ArtifactGroupSummary[]
}) {
  const [, entityId] = entityKey.split(':')
  const name = formatEntityName(entityId)
  const hasGaps = timeline.gaps.length > 0

  return (
    <div className="border border-border rounded-md overflow-hidden">
      {/* Row header — always visible */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-accent/40 transition-colors text-left cursor-pointer"
      >
        {entityTypeIcon(timeline.entity_type)}
        <span className="font-medium text-sm flex-1 truncate">{name}</span>
        <span className="text-xs text-muted-foreground shrink-0">
          {timeline.states.length} scene{timeline.states.length !== 1 ? 's' : ''}
        </span>
        {hasGaps && (
          <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30 gap-1 shrink-0">
            <AlertTriangle className="h-3 w-3" />
            {timeline.gaps.length} gap{timeline.gaps.length !== 1 ? 's' : ''}
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-1">{isExpanded ? '▲' : '▼'}</span>
      </button>

      {/* Expanded timeline */}
      {isExpanded && (
        <div className="border-t border-border px-4 pb-4">
          <EntityTimelineView
            projectId={projectId}
            timeline={timeline}
            groups={groups}
          />
        </div>
      )}
    </div>
  )
}

// ---- Main page -----------------------------------------------------------

export default function ContinuityPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [expandedEntity, setExpandedEntity] = useState<string | null>(null)

  const { data: groups, isLoading: groupsLoading } = useArtifactGroups(projectId)

  const indexGroup = groups?.find(g => g.artifact_type === 'continuity_index')
  const { data: indexArtifact, isLoading: indexLoading } = useArtifact(
    projectId,
    'continuity_index',
    indexGroup?.entity_id ?? 'project',
    indexGroup?.latest_version,
  )

  const isLoading = groupsLoading || (!!indexGroup && indexLoading)

  const indexData = indexArtifact?.payload?.data as ContinuityIndexData | undefined

  const handleToggle = (key: string) => {
    setExpandedEntity(prev => (prev === key ? null : key))
  }

  // Sort entities: characters first, then locations, then props; alphabetical within type
  const sortedEntities = Object.entries(indexData?.timelines ?? {}).sort(([aKey, a], [bKey, b]) => {
    const typeOrder = { character: 0, location: 1, prop: 2 }
    const aOrder = typeOrder[a.entity_type] ?? 3
    const bOrder = typeOrder[b.entity_type] ?? 3
    if (aOrder !== bOrder) return aOrder - bOrder
    return aKey.localeCompare(bKey)
  })

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Continuity"
        subtitle="Track entity state across scenes — costume, injuries, emotional state, and more."
      />

      {isLoading && <ListSkeleton rows={6} />}

      {!isLoading && !indexData && (
        <EmptyState
          icon={Activity}
          title="No continuity data yet"
          description="Run World Building to track entity states across your screenplay."
          action={{
            label: 'Run World Building',
            onClick: () => navigate(`/${projectId}/run`),
          }}
        />
      )}

      {!isLoading && indexData && (
        <>
          {/* Stats overview */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground mb-1">Score</p>
                <p className={cn('text-2xl font-bold tabular-nums', scoreColor(indexData.overall_continuity_score))}>
                  {Math.round(indexData.overall_continuity_score * 100)}%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground mb-1">Gaps</p>
                <p className={cn('text-2xl font-bold tabular-nums', indexData.total_gaps > 0 ? 'text-amber-400' : 'text-emerald-400')}>
                  {indexData.total_gaps}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground mb-1">Entities</p>
                <p className="text-2xl font-bold tabular-nums">
                  {sortedEntities.length}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Entity list */}
          {sortedEntities.length === 0 ? (
            <p className="text-sm text-muted-foreground">No entity timelines found in this index.</p>
          ) : (
            <div className="space-y-2">
              {sortedEntities.map(([entityKey, timeline]) => (
                <EntityRow
                  key={entityKey}
                  entityKey={entityKey}
                  timeline={timeline}
                  isExpanded={expandedEntity === entityKey}
                  onToggle={() => handleToggle(entityKey)}
                  projectId={projectId!}
                  groups={groups ?? []}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
