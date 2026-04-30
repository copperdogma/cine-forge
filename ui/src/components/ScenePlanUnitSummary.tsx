import { Clapperboard, Film, Scissors } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  asArray,
  asNumber,
  asRecord,
  asString,
  asStringArray,
  formatDuration,
  formatToken,
} from '@/components/render-utils'

type ScenePlanUnitSummaryProps = {
  mode: 'previz' | 'render'
  sceneHeading: string
  shotPlanData?: Record<string, unknown>
  renderClipPlanData?: Record<string, unknown>
  currentOutputData?: Record<string, unknown>
  generatedVideoCount?: number
}

type ShotRow = {
  id: string
  label: string
  shotSize: string | null
  cameraMovement: string | null
  coverageRole: string | null
  action: string | null
  dialogue: string[]
  durationSeconds: number | null
}

type RenderClipRow = {
  id: string
  label: string
  startSeconds: number | null
  endSeconds: number | null
  durationSeconds: number | null
  sourceShotIds: string[]
  dialogue: string[]
  actionBeats: string[]
  derivation: string | null
}

function normalizeDialogueLine(line: string): string {
  const normalized = line
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .trim()
  const [speaker, ...rest] = normalized.split(':')
  const utterance = (rest.length > 0 ? rest.join(':') : speaker).replace(/\([^)]*\)/g, ' ')
  const speakerKey = rest.length > 0 ? speaker.toLowerCase().replace(/[^a-z0-9']+/g, ' ').trim() : ''
  const utteranceKey = utterance.toLowerCase().replace(/[^a-z0-9']+/g, ' ').trim()
  return speakerKey ? `${speakerKey}:${utteranceKey}` : utteranceKey
}

function displayShotRows(rows: ShotRow[]): ShotRow[] {
  const lastOccurrence = new Map<string, number>()
  rows.forEach((row, rowIndex) => {
    row.dialogue.forEach(line => {
      const key = normalizeDialogueLine(line)
      if (key) lastOccurrence.set(key, rowIndex)
    })
  })
  return rows.map((row, rowIndex) => {
    const seen = new Set<string>()
    const dialogue = row.dialogue.filter(line => {
      const key = normalizeDialogueLine(line)
      if (!key || seen.has(key) || lastOccurrence.get(key) !== rowIndex) return false
      seen.add(key)
      return true
    })
    return {
      ...row,
      action: row.action ? stripDialogueQuotesFromAction(row.action, row.dialogue) : row.action,
      dialogue,
    }
  })
}

function dialogueQuoteCandidates(dialogue: string[]): string[] {
  const candidates = new Set<string>()
  dialogue.forEach(line => {
    const parts = line.replace(/[‘’]/g, "'").replace(/[“”]/g, '"').split(':')
    const utterance = (parts.length > 1 ? parts.slice(1).join(':') : parts[0])
      .replace(/\([^)]*\)/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
    if (!utterance) return
    candidates.add(utterance)
    const stripped = utterance.replace(/[.!?]+$/g, '').trim()
    if (stripped) candidates.add(stripped)
  })
  return Array.from(candidates).sort((a, b) => b.length - a.length)
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function stripDialogueQuotesFromAction(action: string, dialogue: string[]): string {
  return dialogueQuoteCandidates(dialogue).reduce((current, candidate) => {
    const quoted = new RegExp(`(['"‘’“”])${escapeRegExp(candidate)}([.!?])?\\1`, 'gi')
    return current.replace(quoted, 'the planned dialogue line')
  }, action)
}

function parseShots(data: Record<string, unknown> | undefined): ShotRow[] {
  const rows = asArray(data?.shots).map((item, index) => {
    const record = asRecord(item) ?? {}
    const id = asString(record.shot_id) ?? `shot_${index + 1}`
    return {
      id,
      label: `Shot ${index + 1}`,
      shotSize: asString(record.shot_size),
      cameraMovement: asString(record.camera_movement),
      coverageRole: asString(record.coverage_role),
      action: asString(record.action_description),
      dialogue: asStringArray(record.dialogue_lines),
      durationSeconds: asNumber(record.duration_estimate_seconds),
    }
  })
  return displayShotRows(rows)
}

function parseRenderClips(data: Record<string, unknown> | undefined): RenderClipRow[] {
  return asArray(data?.clips).map((item, index) => {
    const record = asRecord(item) ?? {}
    const id = asString(record.clip_id) ?? `clip_${index + 1}`
    const dialogue = asStringArray(record.dialogue_lines)
    return {
      id,
      label: `Clip ${index + 1}`,
      startSeconds: asNumber(record.start_time_seconds),
      endSeconds: asNumber(record.end_time_seconds),
      durationSeconds: asNumber(record.target_duration_seconds),
      sourceShotIds: asStringArray(record.source_shot_ids),
      dialogue,
      actionBeats: asStringArray(record.action_beats).map(action =>
        stripDialogueQuotesFromAction(action, dialogue),
      ),
      derivation: asString(record.derivation),
    }
  })
}

function timeWindow(startSeconds: number | null, endSeconds: number | null): string | null {
  if (startSeconds === null || endSeconds === null) return null
  return `${formatDuration(startSeconds)}-${formatDuration(endSeconds)}`
}

function outputScopeLabel(
  data: Record<string, unknown> | undefined,
  generatedVideoCount: number,
  mode: 'previz' | 'render',
): string {
  if (generatedVideoCount > 1) {
    const noun = mode === 'previz' ? 'previz clips' : 'generated videos'
    return `Current saved output set: ${generatedVideoCount} render-clip ${noun} for this scene.`
  }
  const renderUnit = asString(data?.render_unit)
  const renderClipId = asString(data?.render_clip_id)
  const sourceShotIds = asStringArray(data?.source_shot_ids)
  if (renderUnit === 'render_clip' && renderClipId) {
    const source = sourceShotIds.length ? ` from ${sourceShotIds.join(', ')}` : ''
    return `Current saved output: render clip ${renderClipId}${source}.`
  }
  if (renderUnit === 'scene') {
    return sourceShotIds.length
      ? `Current saved output: scene-level clip using ${sourceShotIds.join(', ')}.`
      : 'Current saved output: scene-level clip; no per-shot source ids are recorded.'
  }
  return 'No saved output scope recorded yet.'
}

function planDescription(mode: 'previz' | 'render', sceneHeading: string): string {
  if (mode === 'previz') {
    return (
      `AI Previz uses the render clip plan for ${sceneHeading} and generates low-fidelity `
      + 'planning clips for those provider-bounded units.'
    )
  }
  return (
    `Render turns ${sceneHeading} into provider-bounded render clips when a render clip plan exists. `
    + 'A render clip may map to one shot, multiple shots, or a fallback beat.'
  )
}

export function ScenePlanUnitSummary({
  mode,
  sceneHeading,
  shotPlanData,
  renderClipPlanData,
  currentOutputData,
  generatedVideoCount = 0,
}: ScenePlanUnitSummaryProps) {
  const shots = parseShots(shotPlanData)
  const renderClips = parseRenderClips(renderClipPlanData)
  const targetDuration = asNumber(renderClipPlanData?.target_dramatic_duration_seconds)
  const engineMax = asNumber(renderClipPlanData?.engine_max_clip_duration_seconds)

  return (
    <Card className="gap-0">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base">
            {mode === 'previz' ? 'Shot Sequence' : 'Shot / Render Units'}
          </CardTitle>
          {shots.length > 0 && <Badge variant="secondary">{shots.length} shots</Badge>}
          {renderClips.length > 0 && <Badge variant="secondary">{renderClips.length} render clips</Badge>}
          {generatedVideoCount > 0 && (
            <Badge variant="outline">
              {generatedVideoCount} {mode === 'previz' ? 'previz clips' : 'generated videos'}
            </Badge>
          )}
        </div>
        <CardDescription>{planDescription(mode, sceneHeading)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {currentOutputData && (
          <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
            {outputScopeLabel(currentOutputData, generatedVideoCount, mode)}
          </div>
        )}

        {shots.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
            No shot plan is available for this scene yet. Run Shots first so downstream generation
            has visible coverage to work from.
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <Clapperboard className="h-3.5 w-3.5" />
              Planned Shots
            </div>
            {shots.map(shot => (
              <div key={shot.id} className="rounded-lg border border-border bg-card/60 px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium">{shot.label}</p>
                  <Badge variant="outline">{shot.id}</Badge>
                  {shot.shotSize && <Badge variant="secondary">{shot.shotSize}</Badge>}
                  {shot.durationSeconds !== null && (
                    <Badge variant="outline">{formatDuration(shot.durationSeconds)}</Badge>
                  )}
                </div>
                <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {shot.coverageRole && <p>{shot.coverageRole}</p>}
                  {shot.action && <p>{shot.action}</p>}
                  {shot.cameraMovement && <p>Camera: {shot.cameraMovement}</p>}
                  {shot.dialogue.length > 0 && (
                    <p>Dialogue: {shot.dialogue.slice(0, 4).join(' / ')}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {(mode === 'previz' || mode === 'render') && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <Scissors className="h-3.5 w-3.5" />
              {mode === 'previz' ? 'Previz Clip Plan' : 'Render Clip Plan'}
            </div>
            {renderClips.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
                {mode === 'previz'
                  ? 'No render clip plan exists yet. The Previz action will estimate scene duration and split this scene into provider-bounded clips before generating low-fidelity previz.'
                  : 'No render clip plan exists yet. The Render action will estimate scene duration and split this scene into provider-bounded clips before final video generation.'}
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  {targetDuration !== null && (
                    <Badge variant="outline">Target {formatDuration(targetDuration)}</Badge>
                  )}
                  {engineMax !== null && (
                    <Badge variant="outline">Max clip {formatDuration(engineMax)}</Badge>
                  )}
                </div>
                {renderClips.map(clip => (
                  <div key={clip.id} className="rounded-lg border border-border bg-card/60 px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-medium">{clip.label}</p>
                      <Badge variant="outline">{clip.id}</Badge>
                      {timeWindow(clip.startSeconds, clip.endSeconds) && (
                        <Badge variant="secondary">{timeWindow(clip.startSeconds, clip.endSeconds)}</Badge>
                      )}
                      {clip.durationSeconds !== null && (
                        <Badge variant="outline">{formatDuration(clip.durationSeconds)}</Badge>
                      )}
                      {clip.derivation && (
                        <Badge variant="outline">{formatToken(clip.derivation) ?? clip.derivation}</Badge>
                      )}
                    </div>
                    <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {clip.sourceShotIds.length > 0 && (
                        <p>Source shots: {clip.sourceShotIds.join(', ')}</p>
                      )}
                      {clip.actionBeats.length > 0 && (
                        <p>Action: {clip.actionBeats.slice(0, 3).join(' / ')}</p>
                      )}
                      {clip.dialogue.length > 0 && (
                        <p>Dialogue: {clip.dialogue.slice(0, 4).join(' / ')}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {mode === 'render' && generatedVideoCount > 0 && (
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
            <Film className="h-4 w-4 text-muted-foreground" />
            Latest render artifacts include {generatedVideoCount} generated video
            {generatedVideoCount === 1 ? '' : 's'} for this scene.
          </div>
        )}
      </CardContent>
    </Card>
  )
}
