import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  RefreshCw,
  Eye,
  XCircle,
  CheckCircle2,
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
import { useState, useMemo } from 'react'
import { VariationalReview, mockVariations } from '@/components/VariationalReview'
import { toast } from 'sonner'
import { useArtifactGroups } from '@/lib/hooks'
import { ErrorState } from '@/components/StateViews'

type InboxItemType = 'stale' | 'review' | 'error'

interface InboxItem {
  id: string
  type: InboxItemType
  title: string
  description: string
  artifact_type?: string
  entity_id?: string
  timestamp: number
}

// Mock items for types not yet backed by API
// TODO: Wire to run events API for errors, review requests
const mockNonStaleItems: InboxItem[] = [
  {
    id: 'mock-error-1',
    type: 'error',
    title: 'Narrative Analysis failed at theme extraction',
    description: 'LLM returned malformed JSON. May need to re-run with a stronger model.',
    timestamp: Date.now() - 14_400_000,
  },
  {
    id: 'mock-review-1',
    type: 'review',
    title: 'World Bible ready for review',
    description: 'First version generated. Review for accuracy before downstream stages use it.',
    artifact_type: 'world_bible',
    entity_id: 'project',
    timestamp: Date.now() - 28_800_000,
  },
]

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
  }
}

function itemAction(type: InboxItemType, itemId: string, onReview: (id: string) => void) {
  switch (type) {
    case 'stale':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="Re-run pipeline to regenerate stale artifact"
          onClick={(e) => { e.stopPropagation(); toast.info('Re-run triggered') }}
        >
          <RefreshCw className="h-3 w-3" />
          Re-run
        </Button>
      )
    case 'error':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="Retry failed pipeline stage"
          onClick={(e) => { e.stopPropagation(); toast.info('Retry triggered') }}
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </Button>
      )
    case 'review':
      return (
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1.5"
          aria-label="Review artifact variations"
          onClick={(e) => { e.stopPropagation(); onReview(itemId) }}
        >
          <Eye className="h-3 w-3" />
          Review
        </Button>
      )
  }
}

function timeAgo(ms: number): string {
  const seconds = Math.floor((Date.now() - ms) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function ProjectInbox() {
  const { projectId } = useParams<{ projectId: string }>()
  const [reviewingId, setReviewingId] = useState<string | null>(null)

  const { data: artifactGroups, isLoading, error, refetch } = useArtifactGroups(projectId)

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
        timestamp: 0, // No real timestamp available from API yet
      }))
  }, [artifactGroups])

  // Combine real stale items with mock items for other types
  const allItems = useMemo(() => [...staleItems, ...mockNonStaleItems], [staleItems])

  const staleCount = staleItems.length
  const errorCount = mockNonStaleItems.filter(i => i.type === 'error').length
  const reviewCount = mockNonStaleItems.filter(i => i.type === 'review').length

  // Loading state
  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Inbox</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Items that need your attention
        </p>
        <Card>
          <CardContent className="py-12 text-center space-y-3">
            <Skeleton className="h-4 w-48 mx-auto" />
            <Skeleton className="h-4 w-64 mx-auto" />
            <Skeleton className="h-4 w-32 mx-auto" />
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Inbox</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Items that need your attention
        </p>
        <ErrorState
          title="Failed to load inbox"
          message={error instanceof Error ? error.message : 'An unknown error occurred'}
          onRetry={refetch}
        />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Inbox</h1>
      <p className="text-muted-foreground text-sm mb-6">
        Items that need your attention
      </p>

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
                    {itemAction(item.type, item.id, setReviewingId)}
                  </div>
                </div>
                {i < allItems.length - 1 && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Variational Review Panel */}
      {reviewingId && (() => {
        const item = allItems.find(i => i.id === reviewingId)
        return (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">AI Review</h2>
              <Button variant="ghost" size="sm" aria-label="Dismiss review panel" onClick={() => setReviewingId(null)}>
                Dismiss
              </Button>
            </div>
            <VariationalReview
              title={item?.title ?? 'Artifact Review'}
              artifactType={item?.artifact_type ?? 'unknown'}
              variations={mockVariations}
              onRegenerate={(id) => toast.info(`Regenerating variation ${id}`)}
              onApprove={() => {
                toast.success('Variation approved!')
                setReviewingId(null)
              }}
            />
          </div>
        )
      })()}
    </div>
  )
}
