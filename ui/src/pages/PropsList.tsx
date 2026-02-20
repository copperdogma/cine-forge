import { useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Wrench, AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ListSkeleton, EmptyState, ErrorState } from '@/components/StateViews'
import { EntityListControls } from '@/components/EntityListControls'
import { type SortMode, type ViewDensity, type SortDirection } from '@/lib/types'
import { useEntityDetails, useStickyPreference } from '@/lib/hooks'
import { cn, formatEntityName } from '@/lib/utils'

export default function PropsList() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [sort, setSort] = useStickyPreference<SortMode>(projectId, 'props.sort', 'script-order')
  const [density, setDensity] = useStickyPreference<ViewDensity>(projectId, 'props.density', 'medium')
  const [direction, setDirection] = useStickyPreference<SortDirection>(projectId, 'props.direction', 'asc')

  const { data, isLoading, error } = useEntityDetails(projectId!, 'prop_bible')

  const sortedProps = useMemo(() => {
    if (!data) return []

    const sorted = [...data]

    if (sort === 'script-order') {
      sorted.sort((a, b) => {
        if (a.firstSceneNumber === null && b.firstSceneNumber === null) return 0
        if (a.firstSceneNumber === null) return 1
        if (b.firstSceneNumber === null) return -1
        return a.firstSceneNumber - b.firstSceneNumber
      })
    } else if (sort === 'alphabetical') {
      sorted.sort((a, b) =>
        formatEntityName(a.entity_id).localeCompare(
          formatEntityName(b.entity_id),
          undefined,
          { sensitivity: 'base' }
        )
      )
    } else if (sort === 'prominence') {
      sorted.sort((a, b) => b.sceneCount - a.sceneCount)
    }

    if (direction === 'desc') {
      sorted.reverse()
    }

    return sorted
  }, [data, sort, direction])

  if (isLoading) {
    return <ListSkeleton />
  }

  if (error) {
    return <ErrorState message="Failed to load props" />
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No props yet"
        description="Run the world-building pipeline to extract prop details"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Wrench className="h-6 w-6 text-orange-400" />
          <h1 className="text-2xl font-semibold">Props</h1>
          <Badge variant="outline" className="ml-2">
            {data.length}
          </Badge>
        </div>
        <p className="text-muted-foreground">
          All props discovered in your screenplay
        </p>
      </div>

      <EntityListControls
        sort={sort}
        onSortChange={setSort}
        density={density}
        onDensityChange={setDensity}
        direction={direction}
        onDirectionChange={setDirection}
      />

      {density === 'compact' ? (
        <div className="space-y-2">
          {sortedProps.map(prop => (
            <div
              key={prop.entity_id}
              className="flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/props/${prop.entity_id}`)}
            >
              <Wrench className="h-4 w-4 text-orange-400 flex-shrink-0" />
              <span className="font-medium truncate flex-1">
                {formatEntityName(prop.entity_id)}
              </span>
              <span className="text-sm text-muted-foreground flex-shrink-0">
                {prop.sceneCount} {prop.sceneCount === 1 ? 'scene' : 'scenes'}
              </span>
              <Badge variant="outline" className="text-xs">
                v{prop.latest_version}
              </Badge>
              {prop.health && (
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    (prop.health === 'valid' || prop.health === 'healthy') && 'text-green-400 border-green-400/30',
                    prop.health === 'stale' && 'text-amber-400 border-amber-400/30',
                    prop.health === 'needs_review' && 'text-red-400 border-red-400/30',
                  )}
                >
                  {prop.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                  {prop.health}
                </Badge>
              )}
            </div>
          ))}
        </div>
      ) : density === 'medium' ? (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {sortedProps.map(prop => (
            <Card
              key={prop.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/props/${prop.entity_id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Wrench className="h-5 w-5 text-orange-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">
                      {formatEntityName(prop.entity_id)}
                    </h3>
                    {prop.description && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {prop.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-3">
                      <Badge variant="secondary" className="text-xs">
                        {prop.sceneCount} {prop.sceneCount === 1 ? 'scene' : 'scenes'}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        v{prop.latest_version}
                      </Badge>
                      {prop.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (prop.health === 'valid' || prop.health === 'healthy') && 'text-green-400 border-green-400/30',
                            prop.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            prop.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {prop.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {prop.health}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
          {sortedProps.map(prop => (
            <Card
              key={prop.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/props/${prop.entity_id}`)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-3">
                  <Wrench className="h-5 w-5 text-orange-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">
                      {formatEntityName(prop.entity_id)}
                    </h3>
                    {prop.description && (
                      <p className="text-sm text-muted-foreground mt-2">
                        {prop.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-4">
                      <Badge variant="secondary" className="text-xs">
                        {prop.sceneCount} {prop.sceneCount === 1 ? 'scene' : 'scenes'}
                      </Badge>
                      {prop.firstSceneNumber !== null && (
                        <span className="text-xs text-muted-foreground">
                          First appears in Scene {prop.firstSceneNumber}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <Badge variant="outline" className="text-xs">
                        v{prop.latest_version}
                      </Badge>
                      {prop.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (prop.health === 'valid' || prop.health === 'healthy') && 'text-green-400 border-green-400/30',
                            prop.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            prop.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {prop.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {prop.health}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
