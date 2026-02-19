import { CheckCircle2, Loader2, Circle, AlertCircle, SkipForward } from 'lucide-react'
import { useRunState } from '@/lib/hooks'
import { STAGE_DESCRIPTIONS, humanizeStageName } from '@/lib/chat-messages'
import type { StageState } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Canonical stage order per recipe. Unknown stages go at the end. */
const RECIPE_STAGE_ORDER: Record<string, string[]> = {
  mvp_ingest: ['ingest', 'normalize', 'extract_scenes', 'project_config'],
  world_building: ['character_bible', 'location_bible', 'prop_bible'],
}

/** Human-readable names for artifact types produced by stages. */
const ARTIFACT_NAMES: Record<string, [string, string]> = {
  scene: ['scene', 'scenes'],
  canonical_script: ['script', 'scripts'],
  character_bible: ['character', 'characters'],
  location_bible: ['location', 'locations'],
  prop_bible: ['prop', 'props'],
  scene_breakdown: ['scene breakdown', 'scene breakdowns'],
  entity_graph: ['story graph', 'story graphs'],
  world_overview: ['world overview', 'world overviews'],
}

/** Skip internal artifact types the user doesn't care about. */
const SKIP_TYPES = new Set(['raw_input', 'project_config', 'scene_index'])

function getOrderedStageIds(recipeId: string, stageKeys: string[]): string[] {
  const knownOrder = RECIPE_STAGE_ORDER[recipeId]
  if (!knownOrder) return stageKeys
  const ordered = knownOrder.filter(id => stageKeys.includes(id))
  const extras = stageKeys.filter(id => !knownOrder.includes(id))
  return [...ordered, ...extras]
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
    default: // pending
      return <Circle className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
  }
}

function stageLabel(stageId: string, status: string): string {
  const desc = STAGE_DESCRIPTIONS[stageId]
  if (!desc) return humanizeStageName(stageId)
  if (status === 'done' || status === 'skipped_reused') return desc.done
  if (status === 'running') return desc.start
  return humanizeStageName(stageId)
}

export function RunProgressCard({ runId }: { runId: string }) {
  const { data: runState } = useRunState(runId)

  if (!runState) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground py-1">
        <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
        <span>Loading run progress...</span>
      </div>
    )
  }

  const stages = runState.state.stages
  const recipeId = runState.state.recipe_id
  const stageIds = getOrderedStageIds(recipeId, Object.keys(stages))

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
            <span>{stageLabel(stageId, status)}</span>
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
