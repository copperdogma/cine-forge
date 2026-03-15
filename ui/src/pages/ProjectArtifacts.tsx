import { useParams, useNavigate } from 'react-router-dom'
import {
  Package,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { useArtifactGroups } from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { PageHeader } from '@/components/PageHeader'
import { getArtifactMeta } from '@/lib/artifact-meta'
import { HealthBadge } from '@/components/HealthBadge'

function CardSkeleton() {
  return (
    <Card>
      <CardContent className="py-2.5 px-3">
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/4" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function ProjectArtifacts() {
  const { projectId } = useParams()
  const { data: groups, isLoading, error, refetch } = useArtifactGroups(projectId!)

  const navigate = useNavigate()

  function navigateToArtifact(item: { artifact_type: string; entity_id: string | null; latest_version: number }) {
    navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id ?? 'project'}/${item.latest_version}`)
  }

  function renderContent() {
    if (isLoading) {
      return (
        <div className="space-y-6">
          <div>
            <Skeleton className="h-5 w-48 mb-2" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          </div>
          <div>
            <Skeleton className="h-5 w-48 mb-2" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          </div>
        </div>
      )
    }

    if (error) {
      return (
        <ErrorState
          message={error instanceof Error ? error.message : 'Failed to load artifacts'}
          onRetry={refetch}
        />
      )
    }

    if (!groups || groups.length === 0) {
      return (
        <EmptyState
          icon={Package}
          title="No artifacts yet"
          description="Run the pipeline to produce artifacts"
        />
      )
    }

    // Group by artifact_type for display
    const grouped = new Map<string, typeof groups>()
    for (const g of groups) {
      const list = grouped.get(g.artifact_type) ?? []
      list.push(g)
      grouped.set(g.artifact_type, list)
    }

    // Sort type groups: important types first, then alphabetical
    const typeOrder: Record<string, number> = {
      raw_input: 0,
      canonical_script: 1,
      project_config: 2,
      entity_graph: 3,
      scene: 4,
      scene_index: 5,
      character_bible: 10,
      location_bible: 11,
      prop_bible: 12,
      bible_manifest: 13,
      continuity_index: 20,
      continuity_state: 21,
    }
    const sortedEntries = Array.from(grouped.entries()).sort(
      ([a], [b]) => (typeOrder[a] ?? 99) - (typeOrder[b] ?? 99)
    )

    return (
      <div className="space-y-6">
        {sortedEntries.map(([type, items]) => {
          const meta = getArtifactMeta(type)
          const Icon = meta.icon
          return (
            <div key={type}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cn('h-4 w-4', meta.color)} />
                <h2 className="text-sm font-semibold">{meta.label}</h2>
                <span className="text-xs text-muted-foreground">({items.length})</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {items.map(item => (
                  <Card
                    key={`${item.artifact_type}-${item.entity_id ?? 'project'}`}
                    role="button"
                    tabIndex={0}
                    aria-label={`View ${item.entity_id ?? 'project'} artifact, version ${item.latest_version}, health: ${item.health ?? 'unknown'}`}
                    className="cursor-pointer transition-colors hover:bg-accent/50"
                    onClick={() => navigateToArtifact(item)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        navigateToArtifact(item)
                      }
                    }}
                  >
                    <CardContent className="flex items-center gap-3 py-2.5 px-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{item.entity_id ?? 'project'}</p>
                        <p className="text-xs text-muted-foreground">v{item.latest_version}</p>
                      </div>
                      <HealthBadge health={item.health} details={item.health_details} />
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Artifacts" subtitle="Browse all artifacts produced by the pipeline" />
      {renderContent()}
    </div>
  )
}
