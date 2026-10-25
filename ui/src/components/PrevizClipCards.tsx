import { Link } from 'react-router-dom'
import { ExternalLink, Loader2, RefreshCw, Wand2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { asNumber, asRecord, asString, formatDuration } from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'
import { useArtifact } from '@/lib/hooks'
import type { ArtifactGroupSummary } from '@/lib/types'

type PrevizClipCardProps = {
  projectId: string
  videoGroup: ArtifactGroupSummary
  promptGroup?: ArtifactGroupSummary
  canRegenerateClip: boolean
  isRegeneratingClip: boolean
  onRegenerateClip: (clipId: string) => void
}

export function PrevizClipCard({
  projectId,
  videoGroup,
  promptGroup,
  canRegenerateClip,
  isRegeneratingClip,
  onRegenerateClip,
}: PrevizClipCardProps) {
  const { data: artifact, isLoading } = useArtifact(
    projectId,
    'ai_previz_video',
    videoGroup.entity_id ?? undefined,
    videoGroup.latest_version,
  )
  const data = artifact?.payload?.data as Record<string, unknown> | undefined
  const video = asRecord(data?.video)
  const videoPath = asString(video?.relative_path)
  const videoUrl = videoPath ? getAssetFileUrl(projectId, videoPath) : null
  const renderClipId = asString(data?.render_clip_id) ?? videoGroup.entity_id ?? null
  const renderClipLabel = renderClipId ?? 'AI previz clip'
  const startSeconds = asNumber(data?.render_clip_start_time_seconds)
  const endSeconds = asNumber(data?.render_clip_end_time_seconds)
  const durationSeconds = asNumber(data?.duration_seconds)
  const sourceShots = Array.isArray(data?.source_shot_ids)
    ? data.source_shot_ids.filter((item): item is string => typeof item === 'string')
    : []
  const promptRef = asRecord(data?.prompt_ref)
  const promptEntityId = asString(promptRef?.entity_id) ?? promptGroup?.entity_id
  const promptVersion = asNumber(promptRef?.version) ?? promptGroup?.latest_version
  const promptHref = promptEntityId && promptVersion
    ? `/${projectId}/artifacts/ai_previz_prompt/${promptEntityId}/${promptVersion}`
    : null
  const detailHref = videoGroup.entity_id
    ? `/${projectId}/artifacts/ai_previz_video/${videoGroup.entity_id}/${videoGroup.latest_version}`
    : null
  const clipWindow = startSeconds !== null && endSeconds !== null
    ? `${formatDuration(startSeconds) ?? `${startSeconds}s`} - ${formatDuration(endSeconds) ?? `${endSeconds}s`}`
    : null

  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/60 px-4 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{renderClipLabel}</p>
            <Badge variant="outline">video v{videoGroup.latest_version}</Badge>
            {promptVersion && <Badge variant="outline">prompt v{promptVersion}</Badge>}
            {clipWindow && <Badge variant="secondary">{clipWindow}</Badge>}
            {formatDuration(durationSeconds) && (
              <Badge variant="outline">{formatDuration(durationSeconds)}</Badge>
            )}
            {sourceShots.length > 0 && (
              <Badge variant="outline">Shots {sourceShots.join(', ')}</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            Low-fidelity previz video for this render clip.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => renderClipId && onRegenerateClip(renderClipId)}
            disabled={!renderClipId || !canRegenerateClip}
          >
            {isRegeneratingClip ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            Review Clip to Regenerate
          </Button>
          {detailHref && (
            <Button asChild variant="outline" size="sm">
              <Link to={detailHref}>
                <ExternalLink className="h-3.5 w-3.5" />
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
      {isLoading && (
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
          Previz media is missing for this clip.
        </div>
      )}
    </div>
  )
}

type MissingPrevizClipCardProps = {
  clipId: string
  renderClipPlanVersion?: number
  staleGroup?: ArtifactGroupSummary
  canGenerateClip: boolean
  isGeneratingClip: boolean
  onGenerateClip: (clipId: string) => void
}

export function MissingPrevizClipCard({
  clipId,
  renderClipPlanVersion,
  staleGroup,
  canGenerateClip,
  isGeneratingClip,
  onGenerateClip,
}: MissingPrevizClipCardProps) {
  return (
    <div className="rounded-lg border border-dashed border-amber-500/40 bg-amber-500/5 px-4 py-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{clipId}</p>
            <Badge variant="outline">Missing current previz</Badge>
            {renderClipPlanVersion && (
              <Badge variant="secondary">render clips v{renderClipPlanVersion}</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {staleGroup
              ? `Latest saved video v${staleGroup.latest_version} belongs to an older render clip plan and is hidden here.`
              : 'No playable previz video has been saved for this current render clip yet.'}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onGenerateClip(clipId)}
          disabled={!canGenerateClip}
        >
          {isGeneratingClip ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
          Review Clip to Generate
        </Button>
      </div>
    </div>
  )
}
