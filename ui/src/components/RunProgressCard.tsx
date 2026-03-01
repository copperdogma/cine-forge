import { CheckCircle2, Loader2, Circle, AlertCircle, SkipForward, PauseCircle } from 'lucide-react'
import { useRunState, useArtifactGroups } from '@/lib/hooks'
import { STAGE_DESCRIPTIONS, humanizeStageName } from '@/lib/chat-messages'
import type { StageState } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  ARTIFACT_NAMES, SKIP_TYPES, getOrderedStageIds,
  CONCERN_GROUP_META, countSceneProgress, countTotalScenes,
} from '@/lib/constants'

/** Parse the content prop: new format is JSON with runId + projectId, old format is plain runId string. */
function parseContent(content: string): { runId: string; projectId: string | null } {
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed.runId === 'string') {
      return { runId: parsed.runId, projectId: parsed.projectId ?? null }
    }
  } catch {
    // plain string (backwards compat)
  }
  return { runId: content, projectId: null }
}

/** Summarize artifact counts from a completed stage's refs. */
function stageArtifactSummary(stage: StageState): string | null {
  const refs = stage.artifact_refs
  if (!refs || refs.length === 0) return null

  const counts: Record<string, number> = {}
  for (const ref of refs) {
    const t = ref.artifact_type as string
    if (t && !SKIP_TYPES.has(t)) counts[t] = (counts[t] ?? 0) + 1
  }

  const parts: string[] = []
  for (const [type, count] of Object.entries(counts)) {
    const [singular, plural] = ARTIFACT_NAMES[type] ?? [type.replace(/_/g, ' '), type.replace(/_/g, ' ') + 's']
    parts.push(`${count} ${count === 1 ? singular : plural}`)
  }

  return parts.length > 0 ? parts.join(', ') : null
}

function StageIcon({ status }: { status: string }) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0" />
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-primary shrink-0 animate-spin" />
    case 'failed':
      return <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
    case 'paused':
      return <PauseCircle className="h-3.5 w-3.5 text-warning shrink-0" />
    default: // pending
      return <Circle className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
  }
}

function stageLabel(stageId: string, status: string): string {
  const desc = STAGE_DESCRIPTIONS[stageId]
  if (!desc) return humanizeStageName(stageId)
  if (status === 'done' || status === 'skipped_reused') return desc.done
  if (status === 'running') return desc.start
  if (status === 'paused') return "Paused for review"
  return humanizeStageName(stageId)
}

export function RunProgressCard({ content }: { content: string }) {
  const { runId, projectId } = parseContent(content)
  const { data: runState } = useRunState(runId)
  const { data: artifactGroups } = useArtifactGroups(projectId ?? undefined)
  const totalScenes = countTotalScenes(artifactGroups)

  if (!runState) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground py-1">
        <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
        <span>Loading run progress...</span>
      </div>
    )
  }

  const stages = runState.state.stages
  // Use stage_order as authoritative list — it reflects start_from/end_at slicing.
  // Only show stages that are in the execution range, not all recipe stages.
  const stageOrder = runState.state.stage_order as string[] | undefined
  const stageIds = stageOrder && stageOrder.length > 0
    ? stageOrder.filter(id => id in stages)
    : getOrderedStageIds(Object.keys(stages), stageOrder)

  return (
    <div className="space-y-0.5 py-1">
      {stageIds.map((stageId) => {
        const stage = stages[stageId]
        const status = stage.status
        const isDone = status === 'done' || status === 'skipped_reused'
        const isRunning = status === 'running'
        const isFailed = status === 'failed'
        const isPending = !isDone && !isRunning && !isFailed
        const summary = isDone ? stageArtifactSummary(stage) : null

        // Per-scene progress for running concern group stages
        const isConcernGroup = stageId in CONCERN_GROUP_META
        const scenesDone = isConcernGroup ? countSceneProgress(stage, stageId) : 0
        const sceneProgress = isRunning && isConcernGroup && totalScenes > 0
          ? ` (${scenesDone}/${totalScenes} scenes)`
          : ''

        return (
          <div
            key={stageId}
            className={cn(
              'flex items-center gap-2 text-sm py-0.5 transition-opacity duration-300',
              isPending && 'text-muted-foreground/40',
              isDone && 'text-muted-foreground',
              isRunning && 'text-foreground',
              isFailed && 'text-destructive',
            )}
          >
            <StageIcon status={status} />
            <span>{stageLabel(stageId, status)}{sceneProgress}</span>
            {summary && (
              <span className="text-xs text-muted-foreground/50">— {summary}</span>
            )}
            {status === 'skipped_reused' && (
              <span className="text-xs text-muted-foreground/60 flex items-center gap-0.5">
                <SkipForward className="h-3 w-3" />cached
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
