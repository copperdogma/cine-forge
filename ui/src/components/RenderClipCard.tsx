import { Link } from 'react-router-dom'
import { ExternalLink, Film, Loader2, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { asNumber, asRecord, asString, asStringArray, formatDuration } from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'
import { useArtifact } from '@/lib/hooks'
import type { ArtifactGroupSummary } from '@/lib/types'

type RenderClipCardProps = {
  projectId: string
  clipId: string
  videoGroup?: ArtifactGroupSummary
  promptGroup?: ArtifactGroupSummary
  canStartRender: boolean
  pendingClipId: string | null
  onRegenerateClip: (clipId: string) => void
}

function clipWindowLabel(startSeconds: number | null, endSeconds: number | null): string | null {
  if (startSeconds === null || endSeconds === null) return null
  return `${formatDuration(startSeconds) ?? `${startSeconds}s`} - ${formatDuration(endSeconds) ?? `${endSeconds}s`}`
}

export function RenderClipCard({
  projectId,
  clipId,
  videoGroup,
  promptGroup,
  canStartRender,
  pendingClipId,
  onRegenerateClip,
}: RenderClipCardProps) {
  const { data: videoArtifact, isLoading } = useArtifact(
    projectId,
    'generated_video',
    videoGroup?.entity_id ?? undefined,
    videoGroup?.latest_version,
  )
  const data = videoArtifact?.payload?.data as Record<string, unknown> | undefined
  const video = asRecord(data?.video)
  const videoPath = asString(video?.relative_path)
  const videoUrl = videoPath ? getAssetFileUrl(projectId, videoPath) : null
  const startSeconds = asNumber(data?.render_clip_start_time_seconds)
  const endSeconds = asNumber(data?.render_clip_end_time_seconds)
  const durationSeconds = asNumber(data?.duration_seconds)
  const sourceShots = asStringArray(data?.source_shot_ids)
  const clipWindow = clipWindowLabel(startSeconds, endSeconds)
  const hasClipOutput = !!videoGroup || !!promptGroup
  const videoHref = videoGroup?.entity_id
    ? `/${projectId}/artifacts/generated_video/${videoGroup.entity_id}/${videoGroup.latest_version}`
    : null
  const promptHref = promptGroup?.entity_id
    ? `/${projectId}/artifacts/render_prompt/${promptGroup.entity_id}/${promptGroup.latest_version}`
    : null

  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/60 px-4 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{clipId}</p>
            {videoGroup ? (
              <Badge variant="outline">video v{videoGroup.latest_version}</Badge>
            ) : (
              <Badge variant="outline">Missing video</Badge>
            )}
            {promptGroup ? (
              <Badge variant="outline">prompt v{promptGroup.latest_version}</Badge>
            ) : (
              <Badge variant="outline">Missing prompt</Badge>
            )}
            {clipWindow && <Badge variant="secondary">{clipWindow}</Badge>}
            {formatDuration(durationSeconds) && (
              <Badge variant="outline">{formatDuration(durationSeconds)}</Badge>
            )}
            {sourceShots.length > 0 && (
              <Badge variant="outline">Shots {sourceShots.join(', ')}</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {hasClipOutput
              ? 'Generated video for this render clip.'
              : 'No generated video has been saved for this render clip yet.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRegenerateClip(clipId)}
            disabled={!canStartRender}
          >
            {pendingClipId === clipId ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : hasClipOutput ? (
              <RefreshCw className="h-3.5 w-3.5" />
            ) : (
              <Film className="h-3.5 w-3.5" />
            )}
            {hasClipOutput ? 'Review Clip to Regenerate' : 'Review Clip to Generate'}
          </Button>
          {videoHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={videoHref}>
                <Film className="h-3.5 w-3.5" />
                Detail
              </Link>
            </Button>
          )}
          {promptHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={promptHref}>
                <ExternalLink className="h-3.5 w-3.5" />
                Prompt
              </Link>
            </Button>
          )}
        </div>
      </div>
      {isLoading && videoGroup && (
        <div className="aspect-video w-full rounded-lg border border-border bg-muted/20 animate-pulse" />
      )}
      {!isLoading && videoUrl && (
        <video
          controls
          preload="metadata"
          className="aspect-video w-full rounded-lg border border-border bg-black"
          src={videoUrl}
        />
      )}
      {!isLoading && !videoUrl && (
        <div className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
          {videoGroup
            ? 'Generated video media is missing for this clip.'
            : `Generate ${clipId} to create its render video.`}
        </div>
      )}
    </div>
  )
}
