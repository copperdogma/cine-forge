// Global banner showing active long-running operations.
// Reads from operation store (direct API calls) and chat store activeRunId (pipeline runs).
// Rendered in AppShell between PipelineBar and content area.

import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { useOperationStore, type Operation } from '@/lib/operation-store'
import { useChatStore } from '@/lib/chat-store'
import { useRunState, useArtifactGroups } from '@/lib/hooks'
import { getStageStartMessage } from '@/lib/chat-messages'
import { cn } from '@/lib/utils'
import { detectConcernGroupRun, countSceneProgress, countTotalScenes } from '@/lib/constants'

const EMPTY_OPS: Operation[] = []

function RunBannerContent({ projectId }: { projectId: string }) {
  const activeRunId = useChatStore((s) => s.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const totalScenes = countTotalScenes(artifactGroups)

  if (!activeRunId) return null

  let statusText = 'Processing your screenplay...'
  if (runState) {
    const recipeId = runState.state.recipe_id
    if (recipeId === 'world_building') {
      statusText = 'Running Deep Breakdown...'
    } else if (recipeId === 'creative_direction') {
      statusText = 'Running Creative Direction...'
    } else if (recipeId === 'mvp_ingest') {
      statusText = 'Running Script Breakdown...'
    }
    const stages = runState.state.stages
    // Use stage_order as authoritative list — it reflects start_from/end_at slicing.
    const stageOrder = (runState.state.stage_order as string[] | undefined) ?? Object.keys(stages)
    const executedStages = stageOrder.filter((id) => id in stages)

    const runningStage = executedStages
      .map((id) => [id, stages[id]] as const)
      .find(([, s]) => s.status === 'running')
    if (runningStage) {
      statusText = getStageStartMessage(runningStage[0])
    }

    // For single-stage concern group runs: show per-scene progress
    const cg = detectConcernGroupRun(recipeId, executedStages)
    if (cg && runningStage && totalScenes > 0) {
      const scenesDone = countSceneProgress(runningStage[1], runningStage[0])
      statusText = `${statusText} (${scenesDone}/${totalScenes} scenes)`
    } else {
      // Multi-stage runs: show stage progress (but only when there are 2+ stages)
      const total = executedStages.length
      const done = executedStages.filter((id) => stages[id].status === 'done').length
      if (total > 1) {
        statusText = `${statusText} (${done}/${total} stages)`
      }
    }
  }

  return (
    <BannerRow status="running" label={statusText} />
  )
}

function OperationBannerContent({ op }: { op: Operation }) {
  let label = op.label
  if (op.progress) {
    label = `${label} (${op.progress.current}/${op.progress.total})`
  }
  return <BannerRow status={op.status} label={label} />
}

function BannerRow({ status, label }: { status: 'running' | 'done' | 'failed'; label: string }) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border p-2.5 px-4 text-sm shrink-0 transition-colors duration-300',
        status === 'running' && 'border-blue-500/30 bg-blue-500/10',
        status === 'done' && 'border-primary/30 bg-primary/10',
        status === 'failed' && 'border-destructive/30 bg-destructive/10',
      )}
    >
      {status === 'running' && <Loader2 className="h-4 w-4 text-blue-400 animate-spin shrink-0" />}
      {status === 'done' && <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />}
      {status === 'failed' && <AlertCircle className="h-4 w-4 text-destructive shrink-0" />}
      <span className={cn(
        'font-medium',
        status === 'running' && 'text-blue-400',
        status === 'done' && 'text-primary',
        status === 'failed' && 'text-destructive',
      )}>
        {label}
      </span>
    </div>
  )
}

export function OperationBanner({ projectId }: { projectId: string }) {
  const operations = useOperationStore((s) => s.operations[projectId] ?? EMPTY_OPS)
  const hasActiveRun = useChatStore((s) => !!s.activeRunId?.[projectId])

  if (operations.length === 0 && !hasActiveRun) return null

  return (
    <div className="flex flex-col gap-2 px-6 pt-2">
      {hasActiveRun && <RunBannerContent projectId={projectId} />}
      {operations.map((op) => (
        <OperationBannerContent key={op.id} op={op} />
      ))}
    </div>
  )
}
