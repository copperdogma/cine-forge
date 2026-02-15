import { useParams, useNavigate } from 'react-router-dom'
import {
  FileText,
  Users,
  MapPin,
  Globe,
  Clapperboard,
  MessageSquare,
  AlertTriangle,
  RefreshCw,
  Package,
  Eye,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { useArtifactGroups } from '@/lib/hooks'
import { ErrorState, EmptyState } from '@/components/StateViews'
import { toast } from 'sonner'

// Artifact type display config — keys must match backend artifact_type values
const artifactMeta: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  raw_input: { icon: FileText, label: 'Screenplay', color: 'text-blue-400' },
  canonical_script: { icon: FileText, label: 'Canonical Script', color: 'text-blue-300' },
  project_config: { icon: Package, label: 'Project Config', color: 'text-slate-400' },
  entity_graph: { icon: Globe, label: 'Entity Graph', color: 'text-emerald-400' },
  character_bible: { icon: Users, label: 'Character Bible', color: 'text-amber-400' },
  location_bible: { icon: MapPin, label: 'Location Bible', color: 'text-rose-400' },
  prop_bible: { icon: Package, label: 'Prop Bible', color: 'text-orange-400' },
  bible_manifest: { icon: FileText, label: 'Bible Manifest', color: 'text-teal-400' },
  scene: { icon: Clapperboard, label: 'Scene', color: 'text-violet-400' },
  scene_index: { icon: Clapperboard, label: 'Scene Index', color: 'text-violet-300' },
  continuity_index: { icon: Globe, label: 'Continuity Index', color: 'text-cyan-400' },
  continuity_state: { icon: Globe, label: 'Continuity State', color: 'text-cyan-300' },
  dialogue_analysis: { icon: MessageSquare, label: 'Dialogue Analysis', color: 'text-orange-400' },
}

function getArtifactMeta(type: string) {
  return artifactMeta[type] ?? { icon: FileText, label: type, color: 'text-muted-foreground' }
}

type ArtifactGroupSummary = {
  artifact_type: string
  entity_id: string | null
  latest_version: number
  health: string | null
}

function getHealthTooltip(health: string | null): string {
  switch (health) {
    case 'valid':
      return 'This artifact is up to date and has passed all quality checks.'
    case 'stale':
      return 'Upstream artifacts have changed. This artifact needs to be regenerated.'
    case 'needs_review':
      return 'AI flagged this artifact for human review before use in downstream stages.'
    case null:
      return 'Health status not yet determined.'
    default:
      return 'Unknown health status.'
  }
}

interface HealthBadgeProps {
  health: string | null
  projectId?: string
}

function HealthBadge({ health, projectId }: HealthBadgeProps) {
  const navigate = useNavigate()

  if (!health) return null

  // Valid/healthy artifacts get a green badge
  if (health === 'valid' || health === 'healthy') {
    return (
      <Badge variant="outline" className="text-xs text-green-400 border-green-400/30">
        <span className="sr-only">Health status: </span>
        {health}
      </Badge>
    )
  }

  const tooltipText = getHealthTooltip(health)

  if (health === 'stale') {
    return (
      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30 gap-1">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                <span className="sr-only">Health status: </span>
                Stale
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5"
          aria-label="Re-run pipeline to regenerate artifact"
          onClick={() => {
            navigate(`/${projectId}/run`)
            toast.info('Navigate to Pipeline to re-run the relevant recipe')
          }}
        >
          <RefreshCw className="h-3 w-3 text-amber-400" />
        </Button>
      </div>
    )
  }

  if (health === 'needs_review') {
    return (
      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="destructive" className="text-xs gap-1">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                <span className="sr-only">Health status: </span>
                Needs Review
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5"
          aria-label="View artifact details"
          onClick={() => {
            toast.info('Click the artifact card to review')
          }}
        >
          <Eye className="h-3 w-3 text-destructive" />
        </Button>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="destructive" className="text-xs">
            {health}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

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

  function navigateToArtifact(item: ArtifactGroupSummary) {
    navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id ?? 'project'}/${item.latest_version}`)
  }

  // Loading state
  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Artifacts</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Browse all artifacts produced by the pipeline
        </p>
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
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Artifacts</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Browse all artifacts produced by the pipeline
        </p>
        <ErrorState
          message={error instanceof Error ? error.message : 'Failed to load artifacts'}
          onRetry={refetch}
        />
      </div>
    )
  }

  // Empty state
  if (!groups || groups.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Artifacts</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Browse all artifacts produced by the pipeline
        </p>
        <EmptyState
          icon={Package}
          title="No artifacts yet"
          description="Run the pipeline to produce artifacts"
        />
      </div>
    )
  }

  // Group by artifact_type for display
  const grouped = new Map<string, ArtifactGroupSummary[]>()
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
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Artifacts</h1>
      <p className="text-muted-foreground text-sm mb-6">
        Browse all artifacts produced by the pipeline
      </p>

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
                      <HealthBadge health={item.health} projectId={projectId} />
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
