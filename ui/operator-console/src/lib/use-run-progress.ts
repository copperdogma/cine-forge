// Hook that tracks active run progress and adds chat messages for stage transitions.
// Must be called from a component that's always mounted (e.g., AppShell).

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useChatStore } from './chat-store'
import { streamAutoInsight } from './api'
import { getStageStartMessage, getStageCompleteMessage, humanizeStageName } from './chat-messages'
import { useRunState } from './hooks'
import type { StageState } from './types'

/** Build a human-readable summary of what was produced (e.g. "13 scenes and a standardized script"). */
function summarizeArtifacts(stages: Record<string, StageState>): string {
  const counts: Record<string, number> = {}
  for (const stage of Object.values(stages)) {
    for (const ref of stage.artifact_refs) {
      const t = ref.artifact_type as string
      if (t) counts[t] = (counts[t] ?? 0) + 1
    }
  }

  // Skip internal/boring types the user doesn't care about
  const skip = new Set(['raw_input', 'project_config', 'scene_index'])
  const names: Record<string, [string, string]> = {
    scene: ['scene', 'scenes'],
    canonical_script: ['standardized script', 'standardized scripts'],
    scene_breakdown: ['scene breakdown', 'scene breakdowns'],
    entity_graph: ['story graph', 'story graphs'],
    character_bible: ['character bible', 'character bibles'],
    location_bible: ['location bible', 'location bibles'],
    world_overview: ['world overview', 'world overviews'],
    bible_manifest: ['creative bible', 'creative bibles'],
  }

  const parts: string[] = []
  for (const [type, count] of Object.entries(counts)) {
    if (skip.has(type)) continue
    const [singular, plural] = names[type] ?? [type.replace(/_/g, ' '), type.replace(/_/g, ' ') + 's']
    parts.push(count === 1 ? `a ${singular}` : `${count} ${plural}`)
  }

  if (parts.length === 0) return ''
  if (parts.length === 1) return parts[0]
  return parts.slice(0, -1).join(', ') + ' and ' + parts[parts.length - 1]
}

export function useRunProgressChat(projectId: string | undefined) {
  const activeRunId = useChatStore(
    (s) => (projectId ? s.activeRunId?.[projectId] ?? null : null),
  )
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const prevStagesRef = useRef<Record<string, string> | null>(null)
  const queryClient = useQueryClient()

  // Reset ref when active run changes
  useEffect(() => {
    prevStagesRef.current = null
  }, [activeRunId])

  useEffect(() => {
    if (!runState || !activeRunId || !projectId) return

    const stages = runState.state.stages
    const currentStages: Record<string, string> = {}
    for (const [name, s] of Object.entries(stages)) {
      currentStages[name] = s.status
    }

    const store = useChatStore.getState()

    // First poll — initialize ref and report any currently running stages
    if (prevStagesRef.current === null) {
      prevStagesRef.current = currentStages
      for (const [stageName, status] of Object.entries(currentStages)) {
        if (status === 'running') {
          store.addMessage(projectId, {
            id: `progress_${activeRunId}_${stageName}_start`,
            type: 'ai_status',
            content: getStageStartMessage(stageName),
            timestamp: Date.now(),
          })
        }
      }
      // Still check completion in case run finished before first poll
      if (!runState.state.finished_at) return
    }

    const prev = prevStagesRef.current

    // Report stage transitions
    for (const [stageName, status] of Object.entries(currentStages)) {
      const prevStatus = prev[stageName]

      // Stage just started running
      if (status === 'running' && prevStatus !== 'running') {
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_${stageName}_start`,
          type: 'ai_status',
          content: getStageStartMessage(stageName),
          timestamp: Date.now(),
        })
      }

      // Stage just completed
      if (
        (status === 'done' || status === 'skipped_reused') &&
        prevStatus !== 'done' &&
        prevStatus !== 'skipped_reused'
      ) {
        // Resolve the start message spinner → checkmark
        store.updateMessageType(projectId, `progress_${activeRunId}_${stageName}_start`, 'ai_status_done')
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_${stageName}_done`,
          type: 'ai_status_done',
          content: getStageCompleteMessage(stageName),
          timestamp: Date.now(),
        })
      }

      // Stage failed
      if (status === 'failed' && prevStatus !== 'failed') {
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_${stageName}_fail`,
          type: 'ai_suggestion',
          content: `Something went wrong during "${humanizeStageName(stageName)}". You can view the run details or try again.`,
          timestamp: Date.now(),
          actions: [
            {
              id: 'view_run',
              label: 'View Details',
              variant: 'outline',
              route: `runs/${activeRunId}`,
            },
          ],
        })
      }
    }

    // Update ref
    prevStagesRef.current = currentStages

    // Check if run finished
    if (runState.state.finished_at) {
      // Resolve the "run started" spinner
      store.updateMessageType(projectId, `run_started_${activeRunId}`, 'ai_status_done')

      const hasFailed = Object.values(stages).some(
        (s) => s.status === 'failed',
      )

      if (!hasFailed) {
        const summary = summarizeArtifacts(stages)
        const recipeId = runState.state.recipe_id

        // Completion summary with persistent navigation links
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_complete`,
          type: 'ai_suggestion',
          content: summary
            ? `Analysis complete! I found ${summary} in your screenplay.`
            : 'Analysis complete!',
          timestamp: Date.now(),
          actions: [
            {
              id: 'view_results',
              label: 'View Results',
              variant: 'default',
              route: 'artifacts',
            },
            {
              id: 'view_run_detail',
              label: 'Run Details',
              variant: 'outline',
              route: `runs/${activeRunId}`,
            },
          ],
          // No needsAction — these are navigation links that should persist
        })

        // Guide to next step (only after MVP ingest, not after world_building)
        if (recipeId === 'mvp_ingest') {
          store.addMessage(projectId, {
            id: `progress_${activeRunId}_next_steps`,
            type: 'ai_suggestion',
            content: 'You can review what I found, or I can go deeper — building character bibles, creative world details, and visual style guides.',
            timestamp: Date.now() + 1,
            actions: [
              { id: 'review', label: 'Review Scenes', variant: 'default', route: 'artifacts' },
              { id: 'go_deeper', label: 'Go Deeper', variant: 'secondary' },
            ],
            needsAction: true,
          })
        }

        // Trigger AI commentary — proactive insight about what was produced
        requestPostRunInsight(projectId, recipeId, summary)
      }

      // Invalidate project data so UI reflects new state
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'artifacts'],
      })
      queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'runs'],
      })

      store.clearActiveRun(projectId)
    }
  }, [runState, activeRunId, projectId, queryClient])
}

/**
 * Fire-and-forget AI insight after a run completes.
 * Adds a streaming AI message to the chat with creative commentary
 * about the artifacts that were just produced.
 */
function requestPostRunInsight(
  projectId: string,
  recipeId: string,
  artifactSummary: string,
) {
  const store = useChatStore.getState()
  const aiMsgId = `ai_insight_${Date.now()}`

  // Add streaming placeholder
  store.addMessage(projectId, {
    id: aiMsgId,
    type: 'ai_response',
    content: '',
    timestamp: Date.now() + 2, // After the completion messages
    streaming: true,
  })

  let fullContent = ''

  streamAutoInsight(
    projectId,
    'run_completed',
    {
      recipe_id: recipeId,
      artifact_summary: artifactSummary || 'various artifacts',
    },
    (chunk) => {
      if (chunk.type === 'text') {
        fullContent += chunk.content ?? ''
        useChatStore.getState().updateMessageContent(projectId, aiMsgId, fullContent)
      }
      // tool_start/tool_result from insight are silent — the AI uses tools
      // internally to read artifacts but we don't show those indicators
    },
    () => {
      // Done — finalize the streaming message
      useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
    },
    () => {
      // Error — silently remove the placeholder if nothing was produced
      if (!fullContent) {
        // Remove the empty streaming message by finalizing with a fallback
        useChatStore.getState().updateMessageContent(
          projectId, aiMsgId,
          'I can tell you more about what was produced — just ask!',
        )
      }
      useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
    },
  )
}
