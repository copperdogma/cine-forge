// Hook that tracks active run progress and adds chat messages for stage transitions.
// Must be called from a component that's always mounted (e.g., AppShell).

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useChatStore } from './chat-store'
import { streamAutoInsight } from './api'
import { humanizeStageName } from './chat-messages'
import { detectConcernGroupRun, countTotalScenes } from './constants'
import { useRunState, useRunEvents } from './hooks'
import type { StageState, ArtifactGroupSummary } from './types'

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
  const { data: runEvents } = useRunEvents(activeRunId ?? undefined)
  const completedRef = useRef<Set<string>>(new Set())
  const processedEventIdsRef = useRef<Set<string>>(new Set())
  const queryClient = useQueryClient()

  // Track which stages we've already notified as paused
  const pausedRef = useRef<Set<string>>(new Set())

  // Bible extraction progress: track per-type found counts for in-place chat messages
  const bibleFoundCountsRef = useRef<Record<string, number>>({})

  // Reset refs when active run changes
  useEffect(() => {
    completedRef.current = new Set()
    processedEventIdsRef.current = new Set()
    pausedRef.current = new Set()
    bibleFoundCountsRef.current = {}
  }, [activeRunId])

  useEffect(() => {
    if (!runState || !activeRunId || !projectId) return

    const stages = runState.state.stages
    const store = useChatStore.getState()

    // --- Ensure a single progress card message exists for this run ---
    const progressMsgId = `run_progress_${activeRunId}`
    const existingMessages = store.messages[projectId] ?? []
    if (!existingMessages.some(m => m.id === progressMsgId)) {
      // Resolve the "run started" spinner — the progress card replaces it
      store.updateMessageType(projectId, `run_started_${activeRunId}`, 'ai_status_done')

      // For single-concern-group runs, add a role-attributed intro message
      // so the user sees who's working and what they're about to do.
      const stageOrder = (runState.state.stage_order as string[] | undefined) ?? Object.keys(stages)
      const cg = detectConcernGroupRun(runState.state.recipe_id, stageOrder)
      if (cg) {
        const cachedGroups = queryClient.getQueryData<ArtifactGroupSummary[]>(
          ['projects', projectId, 'artifacts'],
        )
        const totalScenes = countTotalScenes(cachedGroups)
        const scenePart = totalScenes > 0 ? `your ${totalScenes} scenes` : 'your scenes'
        store.addMessage(projectId, {
          id: `concern_intro_${activeRunId}`,
          type: 'ai_suggestion',
          content: `Analyzing ${scenePart} and writing ${cg.label} direction for each one.`,
          timestamp: Date.now(),
          speaker: cg.roleId,
        })
      }

      store.addMessage(projectId, {
        id: progressMsgId,
        type: 'ai_progress',
        content: JSON.stringify({ runId: activeRunId, projectId }),
        timestamp: Date.now(),
      })
    }

    // --- Invalidate artifacts every poll while a run is active (live sidebar counts) ---
    // Artifacts are written to the store individually as each entity completes,
    // so counts can tick up mid-stage — not just on stage completion.
    if (!runState.state.finished_at) {
      queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'artifacts'],
      })

      // Check for newly paused stages
      for (const [stageId, stage] of Object.entries(stages)) {
        if (stage.status === 'paused' && !pausedRef.current.has(stageId)) {
          pausedRef.current.add(stageId)
          
          // Find the review artifact ref
          const reviewRef = stage.artifact_refs.find(r => r.artifact_type === 'stage_review')
          const route = reviewRef 
            ? `artifacts/stage_review/${reviewRef.entity_id}/${reviewRef.version}`
            : 'inbox'

          store.addMessage(projectId, {
            id: `progress_${activeRunId}_${stageId}_paused`,
            type: 'ai_suggestion',
            content: `The "${humanizeStageName(stageId)}" stage is paused for your review.`,
            timestamp: Date.now(),
            actions: [
              { id: `review_${stageId}`, label: 'Review Stage', variant: 'default', route },
            ],
            needsAction: true,
          })
        }
      }
    }

    // --- Surface resilience events (retries/fallbacks) as inline notifications ---
    const backendEvents = runEvents?.events ?? []
    for (let i = 0; i < backendEvents.length; i += 1) {
      const evt = backendEvents[i]
      const evtType = (evt.event as string) ?? ''
      if (evtType !== 'stage_retrying' && evtType !== 'stage_fallback') continue
      const stageName = ((evt.stage_id as string) || (evt.stage as string) || 'stage')
      const dedupeKey = `${activeRunId}:${i}:${evtType}:${stageName}`
      if (processedEventIdsRef.current.has(dedupeKey)) continue
      processedEventIdsRef.current.add(dedupeKey)

      if (evtType === 'stage_retrying') {
        const retryDelay = typeof evt.retry_delay_seconds === 'number'
          ? evt.retry_delay_seconds
          : null
        const delayText = retryDelay !== null
          ? ` Retrying in ~${retryDelay.toFixed(1)}s.`
          : ''
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_${stageName}_retry_${i}`,
          type: 'ai_status',
          content: `Retrying "${humanizeStageName(stageName)}" after transient provider error...${delayText}`,
          timestamp: Date.now(),
        })
      } else {
        const toModel = (evt.to_model as string) || 'fallback model'
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_${stageName}_fallback_${i}`,
          type: 'ai_suggestion',
          content: `Switched "${humanizeStageName(stageName)}" to ${toModel} to keep your run moving.`,
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

    // --- Bible extraction live progress (artifact_saved events from world-building pipeline) ---
    // Each character/location/prop bible artifact emits artifact_saved when saved mid-stage.
    // We update ONE in-place message per type ("Writing 3 character bibles...") and immediately
    // invalidate the sidebar artifact count so the badge ticks up as each entity lands.
    const entityTypeLabel: Record<string, string> = {
      character_bible: 'character',
      location_bible: 'location',
      prop_bible: 'prop',
    }
    for (let i = 0; i < backendEvents.length; i += 1) {
      const evt = backendEvents[i]
      const evtType = (evt.event as string) ?? ''
      if (evtType !== 'artifact_saved') continue
      const artifactType = (evt.artifact_type as string) ?? ''
      if (!entityTypeLabel[artifactType]) continue

      const entityId = (evt.entity_id as string) ?? ''
      const dedupeKey = `${activeRunId}:artifact_saved:${artifactType}:${entityId}:${i}`
      if (processedEventIdsRef.current.has(dedupeKey)) continue
      processedEventIdsRef.current.add(dedupeKey)

      // Immediately refresh sidebar counts so the badge ticks up as each entity lands
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'artifacts'] })

      // Increment per-type count and update in-place chat message
      bibleFoundCountsRef.current[artifactType] = (bibleFoundCountsRef.current[artifactType] ?? 0) + 1
      const found = bibleFoundCountsRef.current[artifactType]
      const typeLabel = entityTypeLabel[artifactType]
      const msgId = `bible_progress_${activeRunId}_${artifactType}`
      const content = `Writing ${found} ${typeLabel} bible${found !== 1 ? 's' : ''}...`
      const existingMsg = useChatStore.getState().messages[projectId]?.find(m => m.id === msgId)
      if (!existingMsg) {
        store.addMessage(projectId, { id: msgId, type: 'ai_status', content, timestamp: Date.now() })
      } else {
        store.updateMessageContent(projectId, msgId, content)
      }
    }

    // --- Check if run finished ---
    if (runState.state.finished_at && !completedRef.current.has(activeRunId)) {
      completedRef.current.add(activeRunId)

      // Resolve all in-flight spinners from this run
      store.updateMessageType(projectId, `run_started_${activeRunId}`, 'ai_status_done')
      for (const t of ['character_bible', 'location_bible', 'prop_bible']) {
        store.updateMessageType(projectId, `bible_progress_${activeRunId}_${t}`, 'ai_status_done')
      }

      const hasFailed = Object.values(stages).some(
        (s) => s.status === 'failed',
      )

      if (hasFailed) {
        store.addMessage(projectId, {
          id: `progress_${activeRunId}_failed`,
          type: 'ai_suggestion',
          content: 'Some stages failed. You can view the run details to see what went wrong.',
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
      } else {
        const summary = summarizeArtifacts(stages)
        const recipeId = runState.state.recipe_id
        const completionStageOrder = (runState.state.stage_order as string[] | undefined) ?? Object.keys(stages)
        const cgComplete = detectConcernGroupRun(recipeId, completionStageOrder)

        if (cgComplete) {
          // --- Concern group run completion: role-attributed friendly message ---
          // Count per-scene artifacts (exclude index/project-level artifacts)
          const cgStage = stages[completionStageOrder[0]]
          const sceneRefs = cgStage?.artifact_refs.filter(
            (r) => r.artifact_type === completionStageOrder[0]
              && String(r.entity_id ?? '').startsWith('scene_'),
          ) ?? []
          const sceneCount = sceneRefs.length
          const firstSceneId = sceneRefs
            .map((r) => String(r.entity_id))
            .sort()[0] ?? 'scene_001'

          store.addMessage(projectId, {
            id: `progress_${activeRunId}_complete`,
            type: 'ai_suggestion',
            content: sceneCount > 0
              ? `I've analyzed ${sceneCount === 1 ? '1 scene' : `all ${sceneCount} scenes`} and added ${cgComplete.label} direction to each Direction tab.`
              : `${cgComplete.label} direction is ready.`,
            timestamp: Date.now(),
            speaker: cgComplete.roleId,
            actions: [
              {
                id: 'browse_scene',
                label: 'Browse in Scene 1',
                variant: 'default',
                route: `scenes/${firstSceneId}`,
              },
              {
                id: 'view_run_detail',
                label: 'Run Details',
                variant: 'outline',
                route: `runs/${activeRunId}`,
              },
            ],
          })
          // Skip requestPostRunInsight and addNextStepCta —
          // the role intro + completion messages are sufficient context.
        } else {
          // --- Generic (non-concern-group) run completion ---
          store.addMessage(projectId, {
            id: `progress_${activeRunId}_complete`,
            type: 'ai_suggestion',
            content: summary
              ? `Breakdown complete! I found ${summary} in your screenplay.`
              : 'Breakdown complete!',
            timestamp: Date.now(),
            actions: [
              {
                id: 'view_results',
                label: 'Browse Results',
                variant: 'outline',
                route: 'artifacts',
              },
              {
                id: 'view_run_detail',
                label: 'Run Details',
                variant: 'outline',
                route: `runs/${activeRunId}`,
              },
            ],
          })

          // Insight placeholder goes first so it streams in above the CTA.
          // CTA goes last so the button stays at the bottom while insight fills in above it.
          requestPostRunInsight(projectId, recipeId, summary)
          addNextStepCta(projectId, recipeId, activeRunId)
        }
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
  }, [runState, runEvents, activeRunId, projectId, queryClient])
}

/** Add the golden-path next-step CTA immediately on run completion. */
function addNextStepCta(projectId: string, recipeId: string, runId: string) {
  if (recipeId === 'mvp_ingest') {
    useChatStore.getState().addMessage(projectId, {
      id: `progress_${runId}_next_steps`,
      type: 'ai_suggestion',
      content: 'Next up: a deep breakdown — detailed character profiles, location guides, and a map of every relationship in your story.',
      timestamp: Date.now(),
      actions: [
        { id: 'go_deeper', label: 'Deep Breakdown', variant: 'default' },
        { id: 'review', label: 'Browse Results', variant: 'outline', route: 'artifacts' },
      ],
      needsAction: true,
    })
  }
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

  const recipeDisplayName =
    recipeId === 'mvp_ingest' ? 'Script Breakdown'
    : recipeId === 'world_building' ? 'Deep Breakdown'
    : recipeId

  streamAutoInsight(
    projectId,
    'run_completed',
    {
      recipe_id: recipeId,
      recipe_display_name: recipeDisplayName,
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
      useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
    },
    () => {
      // Error — finalize with fallback content
      if (!fullContent) {
        useChatStore.getState().updateMessageContent(
          projectId, aiMsgId,
          'I can tell you more about what was produced — just ask!',
        )
      }
      useChatStore.getState().finalizeStreamingMessage(projectId, aiMsgId)
    },
  )
}
