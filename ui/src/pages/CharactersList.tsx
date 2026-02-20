import { useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Users, AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ListSkeleton, EmptyState, ErrorState } from '@/components/StateViews'
import { EntityListControls } from '@/components/EntityListControls'
import { type SortMode, type ViewDensity, type SortDirection } from '@/lib/types'
import { useEntityDetails, useStickyPreference } from '@/lib/hooks'
import { cn, formatEntityName } from '@/lib/utils'

export default function CharactersList() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  
  const [sortMode, setSortMode] = useStickyPreference<SortMode>(projectId, 'characters.sort', 'script-order')
  const [viewDensity, setViewDensity] = useStickyPreference<ViewDensity>(projectId, 'characters.density', 'medium')
  const [direction, setDirection] = useStickyPreference<SortDirection>(projectId, 'characters.direction', 'asc')
  
  const { data, isLoading, error } = useEntityDetails(projectId!, 'character_bible')

  const sortedCharacters = useMemo(() => {
    if (!data) return []
    
    const sorted = [...data]

    switch (sortMode) {
      case 'alphabetical':
        sorted.sort((a, b) =>
          formatEntityName(a.entity_id).localeCompare(formatEntityName(b.entity_id), undefined, { sensitivity: 'base' })
        )
        break
      case 'prominence':
        sorted.sort((a, b) => b.sceneCount - a.sceneCount)
        break
      case 'script-order':
      default:
        sorted.sort((a, b) => {
          if (a.firstSceneNumber === null) return 1
          if (b.firstSceneNumber === null) return -1
          return a.firstSceneNumber - b.firstSceneNumber
        })
        break
    }

    if (direction === 'desc') {
      sorted.reverse()
    }

    return sorted
  }, [data, sortMode, direction])

  if (isLoading) {
    return <ListSkeleton />
  }

  if (error) {
    return <ErrorState message="Failed to load characters" />
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No characters yet"
        description="Run the world-building pipeline to extract character profiles"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Users className="h-6 w-6 text-amber-400" />
          <h1 className="text-2xl font-semibold">Characters</h1>
          <Badge variant="outline" className="ml-2">
            {data.length}
          </Badge>
        </div>
        <p className="text-muted-foreground">
          All characters discovered in your screenplay
        </p>
      </div>

      <EntityListControls
        sort={sortMode}
        density={viewDensity}
        direction={direction}
        onSortChange={setSortMode}
        onDensityChange={setViewDensity}
        onDirectionChange={setDirection}
      />

      {viewDensity === 'compact' && (
        <div className="space-y-1">
          {sortedCharacters.map(char => (
            <div
              key={char.entity_id}
              className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/characters/${char.entity_id}`)}
            >
              <Users className="h-4 w-4 text-amber-400 flex-shrink-0" />
              <span className="font-medium flex-1 truncate">
                {formatEntityName(char.entity_id)}
              </span>
              {char.sceneCount > 0 && (
                <span className="text-xs text-muted-foreground">
                  {char.sceneCount} scene{char.sceneCount !== 1 ? 's' : ''}
                </span>
              )}
              <Badge variant="outline" className="text-xs">
                v{char.latest_version}
              </Badge>
              {char.health && (
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    (char.health === 'valid' || char.health === 'healthy') && 'text-green-400 border-green-400/30',
                    char.health === 'stale' && 'text-amber-400 border-amber-400/30',
                    char.health === 'needs_review' && 'text-red-400 border-red-400/30',
                  )}
                >
                  {char.health === 'stale' && <AlertTriangle className="h-3 w-3 mr-1" />}
                  {char.health}
                </Badge>
              )}
            </div>
          ))}
        </div>
      )}

      {viewDensity === 'medium' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedCharacters.map(char => (
            <Card
              key={char.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/characters/${char.entity_id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Users className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">
                      {formatEntityName(char.entity_id)}
                    </h3>
                    {char.description && (
                      <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                        {char.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-3">
                      {char.sceneCount > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {char.sceneCount} scene{char.sceneCount !== 1 ? 's' : ''}
                        </span>
                      )}
                      <Badge variant="outline" className="text-xs">
                        v{char.latest_version}
                      </Badge>
                      {char.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (char.health === 'valid' || char.health === 'healthy') && 'text-green-400 border-green-400/30',
                            char.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            char.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {char.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {char.health}
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

      {viewDensity === 'large' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sortedCharacters.map(char => (
            <Card
              key={char.entity_id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => navigate(`/${projectId}/characters/${char.entity_id}`)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <Users className="h-6 w-6 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-lg truncate">
                      {formatEntityName(char.entity_id)}
                    </h3>
                    {char.description && (
                      <p className="text-sm text-muted-foreground mt-2">
                        {char.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-4">
                      {char.sceneCount > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {char.sceneCount} scene{char.sceneCount !== 1 ? 's' : ''}
                        </span>
                      )}
                      {char.firstSceneNumber !== null && (
                        <span className="text-xs text-muted-foreground">
                          First: Scene {char.firstSceneNumber}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <Badge variant="outline" className="text-xs">
                        v{char.latest_version}
                      </Badge>
                      {char.health && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            (char.health === 'valid' || char.health === 'healthy') && 'text-green-400 border-green-400/30',
                            char.health === 'stale' && 'text-amber-400 border-amber-400/30',
                            char.health === 'needs_review' && 'text-red-400 border-red-400/30',
                          )}
                        >
                          {char.health === 'stale' && <AlertTriangle className="h-3 w-3" />}
                          {char.health}
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
