/**
 * EntityTimelineView — per-entity continuity state visualization.
 *
 * Loads all continuity_state artifacts for a given entity and renders
 * a scene-by-scene timeline: properties, change events (diff-style),
 * and gap warnings.
 */
import { useQueries } from '@tanstack/react-query'
import { AlertTriangle, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import * as api from '@/lib/api'
import type { ArtifactGroupSummary } from '@/lib/types'
import { cn } from '@/lib/utils'

// ---- Domain types (mirrors backend continuity schema) -------------------

interface StateProperty {
  key: string
  value: string
  confidence: number
}

interface ContinuityEvent {
  property_key: string
  previous_value: string | null
  new_value: string
  reason: string
  evidence: string
  is_explicit: boolean
  confidence: number
}

interface ContinuityStateData {
  entity_type: string
  entity_id: string
  scene_id: string
  story_time_position: number
  properties: StateProperty[]
  change_events: ContinuityEvent[]
  overall_confidence: number
}

export interface EntityTimelineData {
  entity_type: 'character' | 'location' | 'prop'
  entity_id: string
  states: string[]  // state artifact entity_ids
  gaps: string[]    // scene_ids with gaps
}

// ---- Props ---------------------------------------------------------------

interface EntityTimelineViewProps {
  projectId: string
  timeline: EntityTimelineData
  groups: ArtifactGroupSummary[]
}

// ---- Helpers -------------------------------------------------------------

// GAP_CONFIDENCE_THRESHOLD mirrors the backend constant (continuity_tracking_v1/main.py)
const GAP_CONFIDENCE_THRESHOLD = 0.4

function confidenceBadge(confidence: number) {
  const pct = `${Math.round(confidence * 100)}%`
  if (confidence >= 0.8) return <Badge variant="secondary" className="text-xs text-emerald-400 border-emerald-400/30" title="Extraction confidence — how precisely the AI read this scene's text">{pct}</Badge>
  if (confidence >= 0.5) return <Badge variant="secondary" className="text-xs text-amber-400 border-amber-400/30" title="Extraction confidence — how precisely the AI read this scene's text">{pct}</Badge>
  return <Badge variant="secondary" className="text-xs text-red-400 border-red-400/30" title="Extraction confidence — how precisely the AI read this scene's text">{pct}</Badge>
}

// Infer the gap reason from state data, mirroring the three backend gap conditions.
// The backend doesn't store the reason, so we approximate from available fields.
function gapMessage(stateData: ContinuityStateData): string {
  if (stateData.properties.length === 0) return 'No state extracted for this scene'
  if (stateData.overall_confidence < GAP_CONFIDENCE_THRESHOLD)
    return `Low extraction confidence (${Math.round(stateData.overall_confidence * 100)}%)`
  // Condition 3: a property value changed from the previous scene without a change_event.
  // We can't identify the specific property without comparing to prior states, but we know
  // the scene is clean (high confidence, has properties) yet still flagged.
  return 'A property may conflict with the previous scene — check adjacent scenes'
}

// Returns true when a change_event previous_value is a sentinel meaning "not previously known"
// rather than an actual prior value. The backend LLM uses these when a property first appears.
function isFirstMention(previousValue: string | null | undefined): boolean {
  if (!previousValue) return true
  const v = previousValue.toLowerCase().trim()
  return (
    v === 'none' ||
    v === 'unknown' ||
    v === 'n/a' ||
    v.startsWith('not described') ||
    v.startsWith('not mentioned') ||
    v.startsWith('not specified') ||
    v.startsWith('not previously') ||
    v.startsWith('no specific') ||
    v.startsWith('no props') ||
    v.startsWith('no ')
  )
}

function humanizeSceneId(sceneId: string): string {
  // "scene_006" → "Scene 6", "scene_014" → "Scene 14"
  const match = sceneId.match(/scene[_-]?(\d+)/i)
  if (match) return `Scene ${parseInt(match[1], 10)}`
  return sceneId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ---- Scene state card ----------------------------------------------------

function SceneStateCard({
  stateData,
  isGap,
  defaultOpen,
}: {
  stateData: ContinuityStateData
  isGap: boolean
  defaultOpen: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <Card className={cn(
      'border',
      isGap ? 'border-amber-500/40 bg-amber-500/5' : 'border-border',
    )}>
      <CardHeader
        className="py-3 px-4 cursor-pointer select-none"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex items-center gap-2 min-w-0">
          {isGap && <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />}
          <span className="text-sm font-medium truncate">{humanizeSceneId(stateData.scene_id)}</span>
          {confidenceBadge(stateData.overall_confidence)}
          {stateData.change_events.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {stateData.change_events.length} change{stateData.change_events.length !== 1 ? 's' : ''}
            </Badge>
          )}
          <div className="flex-1" />
          {open ? <ChevronUp className="h-3.5 w-3.5 text-muted-foreground shrink-0" /> : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />}
        </div>
        {isGap && (
          <p className="text-xs text-amber-400/80 mt-1 ml-5">
            {gapMessage(stateData)}
          </p>
        )}
      </CardHeader>

      {open && (
        <CardContent className="px-4 pb-4 pt-0 space-y-4">
          {/* Properties */}
          {stateData.properties.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">State</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {stateData.properties.map(prop => (
                  <div
                    key={prop.key}
                    className={cn(
                      'flex items-start gap-2 text-sm rounded px-2 py-1 bg-muted/30',
                      prop.confidence < 0.5 && 'opacity-50',
                    )}
                  >
                    <span className="text-muted-foreground font-mono text-xs shrink-0 mt-0.5">
                      {prop.key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-foreground">{prop.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stateData.properties.length === 0 && (
            <p className="text-xs text-muted-foreground italic">No properties extracted for this scene.</p>
          )}

          {/* Change events */}
          {stateData.change_events.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Changes</p>
              <div className="space-y-2">
                {stateData.change_events.map((evt, i) => {
                  const firstMention = isFirstMention(evt.previous_value)
                  return (
                    <div key={i} className="rounded border border-border bg-card/50 p-3 space-y-1.5">
                      <div className="flex items-center gap-2 text-sm flex-wrap">
                        <span className="font-mono text-xs text-muted-foreground">{evt.property_key.replace(/_/g, ' ')}</span>
                        {firstMention ? (
                          <Badge variant="outline" className="text-[10px] py-0 text-sky-400 border-sky-400/30">first mention</Badge>
                        ) : (
                          <>
                            <span className="text-muted-foreground line-through text-xs">{evt.previous_value}</span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                          </>
                        )}
                        <span className="text-foreground font-medium text-xs">{evt.new_value}</span>
                        {evt.is_explicit ? (
                          <Badge variant="outline" className="text-[10px] py-0 text-emerald-400 border-emerald-400/30">explicit</Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] py-0 text-muted-foreground">inferred</Badge>
                        )}
                      </div>
                      {evt.evidence && (
                        <p className="text-xs text-muted-foreground italic border-l-2 border-border pl-2">
                          &ldquo;{evt.evidence}&rdquo;
                        </p>
                      )}
                      {evt.reason && (
                        <p className="text-xs text-muted-foreground">{evt.reason}</p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

// ---- Main component ------------------------------------------------------

export function EntityTimelineView({
  projectId,
  timeline,
  groups,
}: EntityTimelineViewProps) {
  // Build a map: entity_id → latest_version for continuity_state artifacts
  const stateVersionMap = new Map<string, number>()
  for (const g of groups) {
    if (g.artifact_type === 'continuity_state' && g.entity_id) {
      stateVersionMap.set(g.entity_id, g.latest_version)
    }
  }

  // Load each state artifact in the timeline
  const stateQueries = useQueries({
    queries: timeline.states.map(stateId => {
      const version = stateVersionMap.get(stateId)
      return {
        queryKey: ['projects', projectId, 'artifacts', 'continuity_state', stateId, version],
        queryFn: () => api.getArtifact(projectId, 'continuity_state', stateId, version!),
        enabled: !!projectId && version !== undefined,
        staleTime: 60_000,
      }
    }),
  })

  const isLoading = stateQueries.some(q => q.isLoading)
  const gapSet = new Set(timeline.gaps)

  if (isLoading) {
    return (
      <div className="space-y-2 pt-2">
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full rounded" />)}
      </div>
    )
  }

  // Collect loaded states and sort by story_time_position
  const states: ContinuityStateData[] = []
  for (const q of stateQueries) {
    if (!q.data) continue
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = q.data.payload?.data as any
    if (data) states.push(data as ContinuityStateData)
  }
  states.sort((a, b) => a.story_time_position - b.story_time_position)

  if (states.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        No state snapshots found for this entity.
      </p>
    )
  }

  // Auto-expand scenes with changes or gaps; collapse stable ones
  return (
    <div className="space-y-2 pt-2">
      {states.map((state, idx) => (
        <SceneStateCard
          key={state.scene_id}
          stateData={state}
          isGap={gapSet.has(state.scene_id)}
          defaultOpen={idx === 0 || gapSet.has(state.scene_id) || state.change_events.length > 0}
        />
      ))}
    </div>
  )
}
