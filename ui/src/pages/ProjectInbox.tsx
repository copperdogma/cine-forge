import { useParams, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Eye,
  XCircle,
  CheckCircle2,
  Lock,
  Circle,
  CheckCircle,
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
import { useMemo, useCallback, useState } from 'react'
import { useArtifactGroups, useRuns, useProject } from '@/lib/hooks'
import { useQueryClient } from '@tanstack/react-query'
import { ErrorState } from '@/components/StateViews'
import { timeAgo } from '@/lib/format'
import { PageHeader } from '@/components/PageHeader'
import * as api from '@/lib/api'
import {
  artifactAttentionItemId,
  errorItemId,
  reviewItemId,
  gateItemId,
  parseReadIds,
  READ_INBOX_KEY,
} from '@/lib/inbox-utils'
import type { InboxFilter } from '@/lib/inbox-utils'
import type { ArtifactRef, ProjectSummary } from '@/lib/types'
import {
  actionableHealthGroups,
  gateReviewGroups,
  healthDescription,
  healthLabel,
  reviewableBibleGroups,
} from '@/lib/health'

type InboxItemType = 'attention' | 'review' | 'error' | 'gate_review'

interface InboxItem {
  id: string
  type: InboxItemType
  title: string
  description: string
  health?: string | null
  artifact_type?: string
  entity_id?: string
  version?: number
  source_artifact_ref?: ArtifactRef | null
  run_id?: string
  stage_id?: string
  scene_id?: string
  timestamp: number
}

const FILTER_LABELS: Record<InboxFilter, string> = {
  unread: 'Unread',
  read: 'Read',
  all: 'All',
}

function formatArtifactType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function parseTimestamp(value: string | null | undefined): number {
  if (!value) return 0
  const parsed = Date.parse(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function getItemTooltip(type: InboxItemType): string {
  switch (type) {
    case 'attention':
      return 'This artifact has a live health state that needs attention.'
    case 'error':
      return 'This pipeline stage failed during execution. Review the error and retry.'
    case 'review':
      return 'This artifact was generated successfully but needs human review before use in downstream stages.'
    case 'gate_review':
      return 'This pipeline stage is paused and requires human approval before proceeding.'
  }
}

function itemIcon(item: InboxItem) {
  const tooltipText = item.type === 'attention'
    ? healthDescription(item.health)
    : getItemTooltip(item.type)

  const iconMap = {
    attention: item.health === 'confirmed_valid'
      ? <CheckCircle className="h-4 w-4 text-sky-300" />
      : <AlertTriangle className="h-4 w-4 text-amber-400" />,
    error: <XCircle className="h-4 w-4 text-destructive" />,
    review: <Eye className="h-4 w-4 text-primary" />,
    gate_review: <Lock className="h-4 w-4 text-primary" />,
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="cursor-help">{iconMap[item.type]}</div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

function itemAction(
  item: InboxItem,
  projectId: string | undefined,
  navigate: (path: string) => void,
  markRead: (id: string) => void,
) {
  const actionLabel = item.type === 'error' ? 'View Run'
    : item.type === 'gate_review' ? 'Review Stage'
    : item.type === 'attention' ? 'View'
    : 'Review'

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    markRead(item.id)
    if (item.type === 'error') {
      if (projectId && item.run_id) navigate(`/${projectId}/run/${item.run_id}`)
    } else {
      if (projectId && item.artifact_type && item.entity_id) {
        navigate(`/${projectId}/artifacts/${item.artifact_type}/${item.entity_id}/${item.version ?? 1}`)
      }
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className="w-full justify-center gap-1.5 text-xs sm:w-auto"
      aria-label={actionLabel}
      onClick={handleClick}
    >
      <Eye className="h-3 w-3" />
      {actionLabel}
    </Button>
  )
}


export default function ProjectInbox() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<InboxFilter>('unread')

  const { data: artifactGroups, isLoading, error, refetch } = useArtifactGroups(projectId)
  const { data: runs } = useRuns(projectId)
  const { data: project } = useProject(projectId)

  // Read inbox item IDs from project ui_preferences
  const readIds = useMemo(
    () => new Set(parseReadIds(project?.ui_preferences?.[READ_INBOX_KEY])),
    [project?.ui_preferences],
  )

  const persistReadIds = useCallback((updated: string[]) => {
    if (!projectId) return
    const serialized = JSON.stringify(updated)
    // Optimistic update
    queryClient.setQueryData<ProjectSummary>(['projects', projectId], old => {
      if (!old) return old
      return {
        ...old,
        ui_preferences: { ...old.ui_preferences, [READ_INBOX_KEY]: serialized },
      }
    })
    // Persist (fire-and-forget)
    api.updateProjectSettings(projectId, {
      ui_preferences: { [READ_INBOX_KEY]: serialized },
    }).catch(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    })
  }, [projectId, queryClient])

  const markRead = useCallback((id: string) => {
    if (readIds.has(id)) return
    persistReadIds([...readIds, id])
  }, [readIds, persistReadIds])

  // Derive actionable health items from artifact groups (stable IDs via inbox-utils)
  const attentionItems = useMemo<InboxItem[]>(() => {
    return actionableHealthGroups(artifactGroups)
      .map((group) => {
        const sourceRef = group.health_details?.source_artifact_ref
        const targetArtifactType = sourceRef?.artifact_type ?? group.artifact_type
        const targetEntityId = sourceRef?.entity_id ?? group.entity_id ?? 'project'
        const targetVersion = sourceRef?.version ?? group.latest_version
        return {
          id: artifactAttentionItemId(group.health, group.artifact_type, group.entity_id),
          type: 'attention' as const,
          title: `${group.entity_id ?? 'Unknown'} — ${formatArtifactType(group.artifact_type)} is ${healthLabel(group.health).toLowerCase()}`,
          description: healthDescription(group.health, group.health_details),
          health: group.health,
          artifact_type: targetArtifactType,
          entity_id: targetEntityId,
          version: targetVersion,
          source_artifact_ref: sourceRef,
          timestamp: parseTimestamp(group.health_details?.updated_at),
        }
      })
  }, [artifactGroups])

  // Derive error items from failed runs
  const errorItems = useMemo<InboxItem[]>(() => {
    if (!runs) return []
    return runs
      .filter(run => run.status === 'failed')
      .map(run => ({
        id: errorItemId(run.run_id),
        type: 'error' as const,
        title: `Run ${run.run_id} failed`,
        description: 'Pipeline execution failed. Review the run details and retry.',
        run_id: run.run_id,
        timestamp: (run.finished_at ?? run.started_at ?? 0) * 1000,
      }))
  }, [runs])

  // Derive review items from new (v1) bible artifacts that may need human review
  const reviewItems = useMemo<InboxItem[]>(() => {
    return reviewableBibleGroups(artifactGroups)
      .map((group) => ({
        id: reviewItemId(group.artifact_type, group.entity_id, group.latest_version),
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
    return gateReviewGroups(artifactGroups)
      .map((group) => {
        const [sceneId, stageId] = (group.entity_id ?? '').split('_')
        return {
          id: gateItemId(group.entity_id),
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

  // All items (no filtering — we show read/unread based on filter)
  const allItems = useMemo(
    () => [...attentionItems, ...errorItems, ...reviewItems, ...gateReviewItems],
    [attentionItems, errorItems, reviewItems, gateReviewItems],
  )

  const unreadCount = allItems.filter(i => !readIds.has(i.id)).length

  const markAllRead = useCallback(() => {
    const newIds = allItems.filter(i => !readIds.has(i.id)).map(i => i.id)
    if (newIds.length === 0) return
    persistReadIds([...readIds, ...newIds])
  }, [allItems, readIds, persistReadIds])

  // Apply filter
  const visibleItems = useMemo(() => {
    switch (filter) {
      case 'unread': return allItems.filter(i => !readIds.has(i.id))
      case 'read': return allItems.filter(i => readIds.has(i.id))
      case 'all': return allItems
    }
  }, [allItems, readIds, filter])

  // Counts by type (from visible items)
  const attentionCount = visibleItems.filter(i => i.type === 'attention').length
  const errorCount = visibleItems.filter(i => i.type === 'error').length
  const reviewCount = visibleItems.filter(i => i.type === 'review').length
  const gateReviewCount = visibleItems.filter(i => i.type === 'gate_review').length

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
          {/* Filter tabs + summary badges */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            {/* Filter toggle */}
            <div className="flex items-center gap-0.5 rounded-md border border-border p-0.5 mr-2">
              {(['unread', 'read', 'all'] as InboxFilter[]).map(f => (
                <Button
                  key={f}
                  variant={filter === f ? 'secondary' : 'ghost'}
                  size="sm"
                  className="text-xs h-6 px-2"
                  onClick={() => setFilter(f)}
                >
                  {FILTER_LABELS[f]}
                  {f === 'unread' && unreadCount > 0 && (
                    <span className="ml-1 text-muted-foreground">({unreadCount})</span>
                  )}
                </Button>
              ))}
            </div>

            {attentionCount > 0 && (
              <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30 gap-1">
                <AlertTriangle className="h-3 w-3" />
                {attentionCount} attention
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
            {filter === 'unread' && unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start px-0 text-xs text-muted-foreground sm:ml-auto sm:w-auto sm:px-3"
                onClick={markAllRead}
              >
                Mark All Read
              </Button>
            )}
          </div>

          {visibleItems.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="h-8 w-8 text-primary mx-auto mb-3" />
                <p className="text-sm font-medium">
                  {filter === 'unread' ? 'All caught up' : filter === 'read' ? 'No read items' : 'No items'}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {filter === 'unread'
                    ? 'No unread items need attention right now.'
                    : filter === 'read'
                      ? 'No items have been marked as read yet.'
                      : 'No items need attention right now.'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-2 px-0">
                {visibleItems.map((item, i) => {
                  const isRead = readIds.has(item.id)
                  return (
                    <div key={item.id}>
                      <div className={`flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-start ${isRead ? 'opacity-60' : ''}`}>
                        <div className="flex min-w-0 items-start gap-3">
                          {/* Read/unread indicator */}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  className="mt-1 shrink-0"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (isRead) {
                                      // Toggle back to unread: remove from read set
                                      persistReadIds([...readIds].filter(id => id !== item.id))
                                    } else {
                                      markRead(item.id)
                                    }
                                  }}
                                  aria-label={isRead ? 'Mark as unread' : 'Mark as read'}
                                >
                                  {isRead
                                    ? <CheckCircle className="h-3.5 w-3.5 text-muted-foreground" />
                                    : <Circle className="h-3.5 w-3.5 text-primary fill-primary" />}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{isRead ? 'Mark as unread' : 'Mark as read'}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <div className="mt-0.5 shrink-0">{itemIcon(item)}</div>
                          <div className="min-w-0 flex-1">
                            <p className={`text-sm ${isRead ? 'font-normal' : 'font-medium'}`}>{item.title}</p>
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {item.description}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {item.timestamp > 0 ? timeAgo(item.timestamp) : 'Recently'}
                            </p>
                          </div>
                        </div>
                        <div className="w-full sm:mt-0.5 sm:w-auto sm:shrink-0">
                          {itemAction(item, projectId, navigate, markRead)}
                        </div>
                      </div>
                      {i < visibleItems.length - 1 && <Separator />}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
