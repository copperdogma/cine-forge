import { useParams, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Eye,
  XCircle,
  CheckCircle2,
  Lock,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useMemo } from 'react'
import { useArtifactGroups, useRuns } from '@/lib/hooks'
import { ErrorState } from '@/components/StateViews'
import { timeAgo } from '@/lib/format'
import { PageHeader } from '@/components/PageHeader'

type InboxItemType = 'stale' | 'review' | 'error' | 'gate_review'

interface InboxItem {
  id: string
  type: InboxItemType
  title: string
  description: string
  artifact_type?: string
  entity_id?: string
  version?: number
  run_id?: string
  stage_id?: string
  scene_id?: string
  timestamp: number
}

const BIBLE_TYPES = ['character_bible', 'location_bible', 'prop_bible']



function formatArtifactType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getItemTooltip(type: InboxItemType): string {
  switch (type) {
    case 'stale':
      return 'This artifact is stale because upstream inputs have changed. Re-run to regenerate it.'
    case 'error':
      return 'This pipeline stage failed during execution. Review the error and retry.'
    case 'review':
      return 'This artifact was generated successfully but needs human review before use in downstream stages.'
    case 'gate_review':
      return 'This pipeline stage is paused and requires human approval before proceeding.'
  }
}

function itemIcon(type: InboxItemType) {
  const tooltipText = getItemTooltip(type)

  switch (type) {
    case 'stale':
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    case 'error':
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <XCircle className="h-4 w-4 text-destructive" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    case 'review':
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <Eye className="h-4 w-4 text-primary" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    case 'gate_review':
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <Lock className="h-4 w-4 text-primary" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltipText}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
  }
}

function itemAction(
  item: InboxItem,
  projectId: string | undefined,
  navigate: (path: string) => void,
) {
  switch (item.type) {
    case 'stale':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="View stale artifact"
          onClick={(e) => {
            e.stopPropagation()
            if (projectId && item.artifact_type && item.entity_id) {
              navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id}/1`)
            }
          }}
        >
          <Eye className="h-3 w-3" />
          View
        </Button>
      )
    case 'error':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="View failed run details"
          onClick={(e) => {
            e.stopPropagation()
            if (projectId && item.run_id) {
              navigate(`/${projectId}/run/${item.run_id}`)
            }
          }}
        >
          <Eye className="h-3 w-3" />
          View Run
        </Button>
      )
    case 'review':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="Review artifact"
          onClick={(e) => {
            e.stopPropagation()
            if (projectId && item.artifact_type && item.entity_id) {
              navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id}/${item.version ?? 1}`)
            }
          }}
        >
          <Eye className="h-3 w-3" />
          Review
        </Button>
      )
    case 'gate_review':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="Review stage"
          onClick={(e) => {
            e.stopPropagation()
            if (projectId && item.artifact_type && item.entity_id) {
              navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id}/${item.version ?? 1}`)
            }
          }}
        >
          <Eye className="h-3 w-3" />
          Review Stage
        </Button>
      )
  }
}


export default function ProjectInbox() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const { data: artifactGroups, isLoading, error, refetch } = useArtifactGroups(projectId)
  const { data: runs } = useRuns(projectId)

  // Derive stale items from artifact groups
  const staleItems = useMemo<InboxItem[]>(() => {
    if (!artifactGroups) return []
    return artifactGroups
      .filter(group => group.health === 'stale')
      .map((group, index) => ({
        id: `stale-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}`,
        type: 'stale' as const,
        title: `${group.entity_id ?? 'Unknown'} — ${formatArtifactType(group.artifact_type)} is stale`,
        description: 'Upstream inputs have changed since this artifact was produced.',
        artifact_type: group.artifact_type,
        entity_id: group.entity_id ?? undefined,
        timestamp: 0,
      }))
  }, [artifactGroups])

  // Derive error items from failed runs
  const errorItems = useMemo<InboxItem[]>(() => {
    if (!runs) return []
    return runs
      .filter(run => run.status === 'failed')
      .map(run => ({
        id: `error-${run.run_id}`,
        type: 'error' as const,
        title: `Run ${run.run_id} failed`,
        description: 'Pipeline execution failed. Review the run details and retry.',
        run_id: run.run_id,
        timestamp: (run.finished_at ?? run.started_at ?? 0) * 1000,
      }))
  }, [runs])

  // Derive review items from new (v1) bible artifacts that may need human review
  const reviewItems = useMemo<InboxItem[]>(() => {
    if (!artifactGroups) return []
    return artifactGroups
      .filter(group =>
        BIBLE_TYPES.includes(group.artifact_type) &&
        group.latest_version === 1 &&
        group.health !== 'stale'
      )
      .map((group, index) => ({
        id: `review-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}`,
        type: 'review' as const,
        title: `${group.entity_id ?? 'Unknown'} — ${formatArtifactType(group.artifact_type)} ready for review`,
        description: 'First version generated. Review for accuracy before downstream stages use it.',
        artifact_type: group.artifact_type,
        entity_id: group.entity_id ?? undefined,
        version: group.latest_version,
        timestamp: 0,
      }))
  }, [artifactGroups])

  // Derive gate review items from stage_review artifacts
  const gateReviewItems = useMemo<InboxItem[]>(() => {
    if (!artifactGroups) return []
    return artifactGroups
      .filter(group => group.artifact_type === 'stage_review' && group.health === 'needs_review')
      .map((group, index) => {
        const [sceneId, stageId] = (group.entity_id ?? '').split('_')
        return {
          id: `gate-${group.entity_id}-${index}`,
          type: 'gate_review' as const,
          title: `Stage Review: ${formatArtifactType(stageId ?? 'unknown')} (${sceneId ?? 'project'})`,
          description: 'Pipeline is paused. Approve or reject this stage to proceed.',
          artifact_type: group.artifact_type,
          entity_id: group.entity_id ?? undefined,
          version: group.latest_version,
          stage_id: stageId,
          scene_id: sceneId,
          timestamp: 0,
        }
      })
  }, [artifactGroups])

  const allItems = useMemo(
    () => [...staleItems, ...errorItems, ...reviewItems, ...gateReviewItems],
    [staleItems, errorItems, reviewItems, gateReviewItems],
  )

  const staleCount = staleItems.length
  const errorCount = errorItems.length
  const reviewCount = reviewItems.length
  const gateReviewCount = gateReviewItems.length

  return (
    <div>
      <PageHeader title="Inbox" subtitle="Items that need your attention" />
      {isLoading ? (
        <Card>
          <CardContent className="py-12 text-center space-y-3">
            <Skeleton className="h-4 w-48 mx-auto" />
            <Skeleton className="h-4 w-64 mx-auto" />
            <Skeleton className="h-4 w-32 mx-auto" />
          </CardContent>
        </Card>
      ) : error ? (
        <ErrorState
          title="Failed to load inbox"
          message={error instanceof Error ? error.message : 'An unknown error occurred'}
          onRetry={refetch}
        />
      ) : (
        <>
          {/* Summary badges */}
          <div className="flex items-center gap-2 mb-4">
            {staleCount > 0 && (
              <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30 gap-1">
                <AlertTriangle className="h-3 w-3" />
                {staleCount} stale
              </Badge>
            )}
            {errorCount > 0 && (
              <Badge variant="destructive" className="text-xs gap-1">
                <XCircle className="h-3 w-3" />
                {errorCount} error{errorCount > 1 ? 's' : ''}
              </Badge>
            )}
            {reviewCount > 0 && (
              <Badge variant="secondary" className="text-xs gap-1">
                <Eye className="h-3 w-3" />
                {reviewCount} to review
              </Badge>
            )}
            {gateReviewCount > 0 && (
              <Badge variant="secondary" className="text-xs gap-1 bg-primary/10 text-primary border-primary/20">
                <Lock className="h-3 w-3" />
                {gateReviewCount} stage{gateReviewCount > 1 ? 's' : ''} paused
              </Badge>
            )}
          </div>

          {allItems.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="h-8 w-8 text-primary mx-auto mb-3" />
                <p className="text-sm font-medium">All clear</p>
                <p className="text-xs text-muted-foreground mt-1">
                  No items need attention right now.
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-2 px-0">
                {allItems.map((item, i) => (
                  <div key={item.id}>
                    <div className="flex items-start gap-3 px-4 py-3">
                      <div className="mt-0.5">{itemIcon(item.type)}</div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{item.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {item.description}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {timeAgo(item.timestamp)}
                        </p>
                      </div>
                      <div className="shrink-0 mt-0.5">
                        {itemAction(item, projectId, navigate)}
                      </div>
                    </div>
                    {i < allItems.length - 1 && <Separator />}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
