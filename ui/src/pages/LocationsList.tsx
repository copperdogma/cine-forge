import { useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapPin, AlertTriangle, Share } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ListSkeleton, EmptyState, ErrorState } from '@/components/StateViews'
import { EntityListControls } from '@/components/EntityListControls'
import { ExportModal } from '@/components/ExportModal'
import { type SortMode, type ViewDensity, type SortDirection } from '@/lib/types'
import { useEntityDetails, useStickyPreference } from '@/lib/hooks'
import { cn, formatEntityName } from '@/lib/utils'

export default function LocationsList() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [isExportOpen, setIsExportOpen] = useState(false)
  const [sort, setSort] = useStickyPreference<SortMode>(projectId, 'locations.sort', 'script-order')
  const [density, setDensity] = useStickyPreference<ViewDensity>(projectId, 'locations.density', 'medium')
  const [direction, setDirection] = useStickyPreference<SortDirection>(projectId, 'locations.direction', 'asc')
  
  const { data, isLoading, error } = useEntityDetails(projectId!, 'location_bible')

  const sortedLocations = useMemo(() => {
    if (!data) return []
    
    const list = [...data]

    switch (sort) {
      case 'script-order':
        list.sort((a, b) => {
          if (a.firstSceneNumber === null && b.firstSceneNumber === null) return 0
          if (a.firstSceneNumber === null) return 1
          if (b.firstSceneNumber === null) return -1
          return a.firstSceneNumber - b.firstSceneNumber
        })
        break
      case 'alphabetical':
        list.sort((a, b) =>
          formatEntityName(a.entity_id).localeCompare(formatEntityName(b.entity_id), undefined, { sensitivity: 'base' })
        )
        break
      case 'prominence':
        list.sort((a, b) => (b.sceneCount || 0) - (a.sceneCount || 0))
        break
    }

    if (direction === 'desc') {
      list.reverse()
    }

    return list
  }, [data, sort, direction])

  if (isLoading) {
    return <ListSkeleton />
  }

  if (error) {
    return <ErrorState message="Failed to load locations" />
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No locations yet"
        description="Run the world-building pipeline to extract location profiles"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="h-6 w-6 text-rose-400" />
            <h1 className="text-2xl font-semibold">Locations</h1>
            <Badge variant="outline" className="ml-2">
              {data.length}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            All locations discovered in your screenplay
          </p>
        </div>
        <Button variant="outline" onClick={() => setIsExportOpen(true)}>
          <Share className="mr-2 h-4 w-4" />
          Export
        </Button>
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
        <div className="space-y-1">
          {sortedLocations.map(loc => (
            <div
              key={loc.entity_id}
              className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/locations/${loc.entity_id}`)}
            >
              <MapPin className="h-4 w-4 text-rose-400 flex-shrink-0" />
              <span className="flex-1 font-medium truncate">
                {formatEntityName(loc.entity_id)}
              </span>
              {loc.sceneCount !== null && loc.sceneCount > 0 && (
                <span className="text-sm text-muted-foreground">
                  {loc.sceneCount} {loc.sceneCount === 1 ? 'scene' : 'scenes'}
                </span>
              )}
              <Badge variant="outline" className="text-xs">
                v{loc.latest_version}
              </Badge>
              {loc.health && (
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    (loc.health === 'valid' || loc.health === 'healthy') && 'text-green-400 border-green-400/30',
                    loc.health === 'stale' && 'text-amber-400 border-amber-400/30',
                    loc.health === 'needs_review' && 'text-red-400 border-red-400/30',
                  )}
                >
                  {loc.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                  {loc.health}
                </Badge>
              )}
            </div>
          ))}
        </div>
      ) : density === 'medium' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedLocations.map(loc => (
            <Card
              key={loc.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/locations/${loc.entity_id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-rose-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate mb-2">
                      {formatEntityName(loc.entity_id)}
                    </h3>
                    {loc.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {loc.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      {loc.sceneCount !== null && loc.sceneCount > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          {loc.sceneCount} {loc.sceneCount === 1 ? 'scene' : 'scenes'}
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        v{loc.latest_version}
                      </Badge>
                      {loc.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (loc.health === 'valid' || loc.health === 'healthy') && 'text-green-400 border-green-400/30',
                            loc.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            loc.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {loc.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {loc.health}
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sortedLocations.map(loc => (
            <Card
              key={loc.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/locations/${loc.entity_id}`)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-rose-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium mb-3">
                      {formatEntityName(loc.entity_id)}
                    </h3>
                    {loc.description && (
                      <p className="text-sm text-muted-foreground mb-4">
                        {loc.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 flex-wrap mb-3">
                      {loc.sceneCount !== null && loc.sceneCount > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          {loc.sceneCount} {loc.sceneCount === 1 ? 'scene' : 'scenes'}
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        v{loc.latest_version}
                      </Badge>
                      {loc.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (loc.health === 'valid' || loc.health === 'healthy') && 'text-green-400 border-green-400/30',
                            loc.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            loc.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {loc.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {loc.health}
                        </Badge>
                      )}
                    </div>
                    {loc.firstSceneNumber !== null && (
                      <p className="text-xs text-muted-foreground">
                        First appearance: Scene {loc.firstSceneNumber}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId!}
        defaultScope="locations"
      />
    </div>
  )
}
