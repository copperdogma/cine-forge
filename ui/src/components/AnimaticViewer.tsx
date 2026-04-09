import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  formatLatencyMs,
  formatMoney,
  formatPreviewIntent,
  formatPreviewMode,
  parsePreviewProvenance,
} from '@/components/preview-provenance'
import { getAssetFileUrl } from '@/lib/api/assets'
import { usePrevizAdoptionStatus } from '@/lib/hooks'
import { Clock, DollarSign, Film, Timer, TriangleAlert, Volume2 } from 'lucide-react'

type AnimaticViewerProps = {
  data: Record<string, unknown>
  projectId: string
}

type SegmentView = {
  segmentId: string
  shotId: string | null
  videoPath: string | null
  durationSeconds: number | null
  shotSize: string | null
  cameraAngle: string | null
  cameraMovement: string | null
  characters: string[]
  editIntent: string | null
  sourceKind: string | null
}

type AnimaticView = {
  sceneHeading: string | null
  sceneNumber: number | null
  videoPath: string | null
  durationSeconds: number | null
  audioRefs: Array<{ relativePath: string; label: string | null }>
  sourceMix: string[]
  segments: SegmentView[]
  previewProvenance: ReturnType<typeof parsePreviewProvenance>
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function asStringArray(value: unknown): string[] {
  return asArray(value)
    .map(item => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null
  if (Number.isInteger(seconds)) return `${seconds}s`
  return `${seconds.toFixed(1)}s`
}

function parseSegment(value: unknown, index: number): SegmentView {
  const record = asRecord(value)
  const video = asRecord(record?.video)
  return {
    segmentId: asString(record?.segment_id) ?? `segment_${index + 1}`,
    shotId: asString(record?.shot_id),
    videoPath: asString(video?.relative_path),
    durationSeconds: asNumber(record?.duration_seconds),
    shotSize: asString(record?.shot_size),
    cameraAngle: asString(record?.camera_angle),
    cameraMovement: asString(record?.camera_movement),
    characters: asStringArray(record?.characters_in_frame),
    editIntent: asString(record?.edit_intent),
    sourceKind: asString(record?.source_kind),
  }
}

function parseAnimatic(data: Record<string, unknown>): AnimaticView {
  const video = asRecord(data.video)
  return {
    sceneHeading: asString(data.scene_heading),
    sceneNumber: asNumber(data.scene_number),
    videoPath: asString(video?.relative_path),
    durationSeconds: asNumber(data.total_duration_seconds),
    audioRefs: asArray(data.audio_refs)
      .map(item => {
        const record = asRecord(item)
        const relativePath = asString(record?.relative_path)
        if (!relativePath) return null
        return {
          relativePath,
          label: asString(record?.label),
        }
      })
      .filter((item): item is { relativePath: string; label: string | null } => item !== null),
    sourceMix: asStringArray(data.source_mix),
    segments: asArray(data.segments).map(parseSegment),
    previewProvenance: parsePreviewProvenance(data.preview_provenance),
  }
}

export function AnimaticViewer({ data, projectId }: AnimaticViewerProps) {
  const animatic = parseAnimatic(data)
  const { data: previzStatus } = usePrevizAdoptionStatus(projectId)
  const deterministicPrevizStatus = previzStatus?.deterministic_previz
  const aiPrevizStatus = previzStatus?.ai_previz
  const sceneLabel =
    animatic.sceneNumber !== null ? `Scene ${animatic.sceneNumber}` : 'Scene Animatic'
  const videoUrl = animatic.videoPath ? getAssetFileUrl(projectId, animatic.videoPath) : null
  const hasPlaceholderSegments = animatic.sourceMix.includes('placeholder')
    || animatic.segments.some(segment => segment.sourceKind === 'placeholder')

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>{sceneLabel}</CardTitle>
              <CardDescription>{animatic.sceneHeading ?? 'Animatic preview'}</CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {animatic.durationSeconds !== null && (
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(animatic.durationSeconds)}
                </Badge>
              )}
              {formatPreviewMode(animatic.previewProvenance?.mode ?? null) && (
                <Badge variant="secondary">
                  {formatPreviewMode(animatic.previewProvenance?.mode ?? null)}
                </Badge>
              )}
              <Badge variant="outline">Deterministic animatic</Badge>
              <Badge variant="secondary">Fallback / control</Badge>
              {formatPreviewIntent(animatic.previewProvenance?.fidelityIntent ?? null) && (
                <Badge variant="outline">
                  {formatPreviewIntent(animatic.previewProvenance?.fidelityIntent ?? null)}
                </Badge>
              )}
              {animatic.audioRefs.length > 0 && (
                <Badge variant="secondary" className="gap-1">
                  <Volume2 className="h-3 w-3" />
                  Temp audio
                </Badge>
              )}
              {formatLatencyMs(animatic.previewProvenance?.generationLatencyMs ?? null) && (
                <Badge variant="outline" className="gap-1">
                  <Timer className="h-3 w-3" />
                  {formatLatencyMs(animatic.previewProvenance?.generationLatencyMs ?? null)}
                </Badge>
              )}
              {formatMoney(animatic.previewProvenance?.estimatedCostUsd ?? null) && (
                <Badge variant="outline" className="gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatMoney(animatic.previewProvenance?.estimatedCostUsd ?? null)}
                </Badge>
              )}
              {animatic.sourceMix.map(source => (
                <Badge key={source} variant="outline">
                  {source}
                </Badge>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
            <div className="flex items-start gap-2">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
              <div className="space-y-1">
                <p>
                  This is the deterministic baseline: an annotated animatic assembled from shot
                  plans and storyboard frames. It is intentionally not AI-generated video and is
                  only a fallback/control surface.
                </p>
                {hasPlaceholderSegments && (
                  <p>
                    Placeholder frames are active in this clip, so some segments render as
                    annotated cards with text and guide lines instead of generated imagery.
                  </p>
                )}
                {aiPrevizStatus?.upgrade_description && <p>{aiPrevizStatus.upgrade_description}</p>}
              </div>
            </div>
          </div>

          {videoUrl ? (
            <video
              controls
              preload="metadata"
              className="w-full rounded-xl border border-border bg-black"
              src={videoUrl}
            />
          ) : (
            <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
              Animatic video is missing from this artifact.
            </div>
          )}

          {animatic.audioRefs.length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              Audio sources: {animatic.audioRefs.map(item => item.label ?? item.relativePath).join(', ')}
            </div>
          )}

          {animatic.previewProvenance && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              {deterministicPrevizStatus && <p>{deterministicPrevizStatus.reason}</p>}
              <p>
                Intended use: {animatic.previewProvenance.intendedUse.join(', ') || 'human review'}
              </p>
              {animatic.previewProvenance.upstreamInputs.length > 0 && (
                <p>
                  Inputs: {animatic.previewProvenance.upstreamInputs.join(', ')}
                </p>
              )}
              {aiPrevizStatus?.reason && <p>AI upgrade: {aiPrevizStatus.reason}</p>}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-3">
        {animatic.segments.map(segment => {
          const segmentUrl = segment.videoPath ? getAssetFileUrl(projectId, segment.videoPath) : null
          return (
            <Card key={segment.segmentId} className="gap-0">
              <CardHeader className="pb-3">
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle className="text-base">{segment.shotId ?? segment.segmentId}</CardTitle>
                  {segment.durationSeconds !== null && (
                    <Badge variant="outline">{formatDuration(segment.durationSeconds)}</Badge>
                  )}
                  {segment.sourceKind && <Badge variant="secondary">{segment.sourceKind}</Badge>}
                </div>
                <CardDescription>
                  {[segment.shotSize, segment.cameraAngle, segment.cameraMovement]
                    .filter(Boolean)
                    .join(' • ') || 'Shot metadata unavailable'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {segmentUrl && (
                  <video
                    controls
                    preload="metadata"
                    className="w-full rounded-lg border border-border bg-black"
                    src={segmentUrl}
                  />
                )}
                <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                  {segment.characters.map(character => (
                    <Badge key={character} variant="outline">
                      {character}
                    </Badge>
                  ))}
                  {segment.editIntent && (
                    <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1">
                      <Film className="h-3 w-3" />
                      {segment.editIntent}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
