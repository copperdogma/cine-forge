import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getAssetFileUrl } from '@/lib/api/assets'
import { Clock, Film } from 'lucide-react'

type PrevizReelViewerProps = {
  data: Record<string, unknown>
  projectId: string
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

function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null
  if (Number.isInteger(seconds)) return `${seconds}s`
  return `${seconds.toFixed(1)}s`
}

export function PrevizReelViewer({ data, projectId }: PrevizReelViewerProps) {
  const reelVideo = asRecord(data.reel_video)
  const reelPath = asString(reelVideo?.relative_path)
  const reelUrl = reelPath ? getAssetFileUrl(projectId, reelPath) : null
  const scenes = asArray(data.scenes)
    .map(item => {
      const record = asRecord(item)
      const video = asRecord(record?.video)
      if (!record) return null
      return {
        sceneId: asString(record.scene_id),
        heading: asString(record.scene_heading),
        sourceTrackType: asString(record.source_track_type),
        durationSeconds: asNumber(record.duration_seconds),
        videoPath: asString(video?.relative_path),
      }
    })
    .filter(Boolean)

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>Previz Reel</CardTitle>
              <CardDescription>
                Project-level playable assembly built from the best available scene representation.
              </CardDescription>
            </div>
            {asNumber(data.total_duration_seconds) !== null && (
              <Badge variant="outline" className="gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(asNumber(data.total_duration_seconds))}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {reelUrl ? (
            <video
              controls
              preload="metadata"
              className="w-full rounded-xl border border-border bg-black"
              src={reelUrl}
            />
          ) : (
            <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
              Previz reel video is missing from this artifact.
            </div>
          )}

          <div className="grid gap-2">
            {scenes.map(scene => (
              <div
                key={`${scene?.sceneId}-${scene?.heading}`}
                className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-sm"
              >
                <Film className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{scene?.heading ?? scene?.sceneId ?? 'Scene'}</span>
                {scene?.sourceTrackType && <Badge variant="secondary">{scene.sourceTrackType}</Badge>}
                {scene?.durationSeconds !== null && (
                  <Badge variant="outline">{formatDuration(scene?.durationSeconds ?? null)}</Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
