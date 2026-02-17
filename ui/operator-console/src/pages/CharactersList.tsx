import { useParams, useNavigate } from 'react-router-dom'
import { Users, AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ListSkeleton, EmptyState, ErrorState } from '@/components/StateViews'
import { useArtifactGroups } from '@/lib/hooks'
import { cn } from '@/lib/utils'

function formatEntityName(entityId: string | null): string {
  if (!entityId) return 'Unknown'
  return entityId
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export default function CharactersList() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data: groups, isLoading, error } = useArtifactGroups(projectId!)

  if (isLoading) {
    return <ListSkeleton />
  }

  if (error) {
    return <ErrorState message="Failed to load characters" />
  }

  const characters = groups?.filter(g => g.artifact_type === 'character_bible') || []

  if (characters.length === 0) {
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
            {characters.length}
          </Badge>
        </div>
        <p className="text-muted-foreground">
          All characters discovered in your screenplay
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {characters.map(char => (
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
                    <div className="flex items-center gap-2 mt-2">
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
    </div>
  )
}
