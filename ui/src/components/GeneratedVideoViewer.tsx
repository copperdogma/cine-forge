import { Link } from 'react-router-dom'
import { Clock, DollarSign, Film, Video } from 'lucide-react'
import {
  formatLatencyMs,
  formatPreviewIntent,
  formatPreviewMode,
  parsePreviewProvenance,
} from '@/components/preview-provenance'
import { RenderInputUsageCard } from '@/components/RenderInputUsageCard'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  asArray,
  asNumber,
  asRecord,
  asString,
  asStringArray,
  formatDuration,
  formatMoney,
  formatToken,
  parseRenderInputUsage,
  type RenderArtifactRefView,
  type RenderInputUsageView,
} from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'

type GeneratedVideoViewerProps = {
  data: Record<string, unknown>
  projectId: string
}

type GeneratedVideoView = {
  sceneHeading: string | null
  sceneNumber: number | null
  renderUnit: string | null
  renderClipId: string | null
  renderClipStartSeconds: number | null
  renderClipEndSeconds: number | null
  videoPath: string | null
  durationSeconds: number | null
  resolution: string | null
  aspectRatio: string | null
  targetProvider: string | null
  targetModel: string | null
  enginePackId: string | null
  requestId: string | null
  estimatedCostUsd: number | null
  notes: string[]
  resolvedInputs: RenderInputUsageView[]
  providerParams: Record<string, unknown>
  previewProvenance: ReturnType<typeof parsePreviewProvenance>
  promptRef: RenderArtifactRefView | null
}

function parseGeneratedVideo(data: Record<string, unknown>): GeneratedVideoView {
  const video = asRecord(data.video)
  const cost = asRecord(data.cost)
  const generationParams = asRecord(data.generation_params)
  const providerParams = asRecord(generationParams?.provider_params) ?? {}
  const promptRef = asRecord(data.prompt_ref)
  return {
    sceneHeading: asString(data.scene_heading),
    sceneNumber: asNumber(data.scene_number),
    renderUnit: asString(data.render_unit),
    renderClipId: asString(data.render_clip_id),
    renderClipStartSeconds: asNumber(data.render_clip_start_time_seconds),
    renderClipEndSeconds: asNumber(data.render_clip_end_time_seconds),
    videoPath: asString(video?.relative_path),
    durationSeconds: asNumber(data.duration_seconds),
    resolution: asString(data.resolution),
    aspectRatio: asString(data.aspect_ratio),
    targetProvider: asString(data.target_provider),
    targetModel: asString(data.target_model),
    enginePackId: asString(data.engine_pack_id),
    requestId: asString(data.request_id),
    estimatedCostUsd: asNumber(cost?.estimated_cost_usd),
    notes: asStringArray(data.notes),
    resolvedInputs: asArray(data.resolved_inputs)
      .map(parseRenderInputUsage)
      .filter((input): input is RenderInputUsageView => input !== null),
    providerParams,
    previewProvenance: parsePreviewProvenance(data.preview_provenance),
    promptRef: promptRef
      ? {
          artifactType: asString(promptRef.artifact_type),
          entityId: asString(promptRef.entity_id),
          version: asNumber(promptRef.version),
        }
      : null,
  }
}

function formatClipWindow(startSeconds: number | null, endSeconds: number | null): string | null {
  if (startSeconds === null || endSeconds === null) return null
  const start = formatDuration(startSeconds) ?? `${startSeconds}s`
  const end = formatDuration(endSeconds) ?? `${endSeconds}s`
  return `${start} - ${end}`
}

export function GeneratedVideoViewer({ data, projectId }: GeneratedVideoViewerProps) {
  const render = parseGeneratedVideo(data)
  const sceneLabel =
    render.sceneNumber !== null ? `Scene ${render.sceneNumber}` : 'Generated Video'
  const videoUrl = render.videoPath ? getAssetFileUrl(projectId, render.videoPath) : null
  const providerParamsJson = JSON.stringify(render.providerParams, null, 2)
  const promptHref =
    render.promptRef?.artifactType && render.promptRef.entityId && render.promptRef.version !== null
      ? `/${projectId}/artifacts/${render.promptRef.artifactType}/${render.promptRef.entityId}/${render.promptRef.version}`
      : null

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>{sceneLabel}</CardTitle>
              <CardDescription>
                {render.sceneHeading ?? 'Scene-level generated render'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {render.targetProvider && (
                <Badge variant="secondary">{formatToken(render.targetProvider)}</Badge>
              )}
              {render.renderUnit === 'render_clip' && (
                <Badge variant="secondary">Render Clip</Badge>
              )}
              {render.renderClipId && (
                <Badge variant="outline">{render.renderClipId}</Badge>
              )}
              {formatClipWindow(render.renderClipStartSeconds, render.renderClipEndSeconds) && (
                <Badge variant="outline">
                  {formatClipWindow(render.renderClipStartSeconds, render.renderClipEndSeconds)}
                </Badge>
              )}
              {formatPreviewMode(render.previewProvenance?.mode ?? null) && (
                <Badge variant="secondary">{formatPreviewMode(render.previewProvenance?.mode ?? null)}</Badge>
              )}
              {formatPreviewIntent(render.previewProvenance?.fidelityIntent ?? null) && (
                <Badge variant="outline">{formatPreviewIntent(render.previewProvenance?.fidelityIntent ?? null)}</Badge>
              )}
              {render.targetModel && <Badge variant="outline">{render.targetModel}</Badge>}
              {render.enginePackId && (
                <Badge variant="outline" className="gap-1">
                  <Film className="h-3 w-3" />
                  {render.enginePackId}
                </Badge>
              )}
              {formatDuration(render.durationSeconds) && (
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(render.durationSeconds)}
                </Badge>
              )}
              {render.resolution && <Badge variant="outline">{render.resolution}</Badge>}
              {render.aspectRatio && <Badge variant="outline">{render.aspectRatio}</Badge>}
              {formatMoney(render.estimatedCostUsd) && (
                <Badge variant="outline" className="gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatMoney(render.estimatedCostUsd)}
                </Badge>
              )}
              {formatLatencyMs(render.previewProvenance?.generationLatencyMs ?? null) && (
                <Badge variant="outline">{formatLatencyMs(render.previewProvenance?.generationLatencyMs ?? null)}</Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {videoUrl ? (
            <video
              controls
              preload="metadata"
              className="w-full rounded-xl border border-border bg-black"
              src={videoUrl}
            />
          ) : (
            <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
              Generated video media is missing from this artifact.
            </div>
          )}

          <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
            {render.requestId && (
              <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1">
                <Video className="h-3 w-3" />
                Request ID: {render.requestId}
              </span>
            )}
          </div>

          {render.notes.length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              {render.notes.map(note => (
                <p key={note}>{note}</p>
              ))}
            </div>
          )}

          {render.previewProvenance?.upstreamInputs.length ? (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              Inputs: {render.previewProvenance.upstreamInputs.join(', ')}
            </div>
          ) : null}

          {promptHref && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Prompt Provenance
              </p>
              <p className="text-sm text-muted-foreground">
                This render was generated from the linked prompt artifact. Open it to inspect the
                compiled creative brief, resolved reference usage, and demotion notes.
              </p>
              <Button asChild variant="outline" size="sm" className="mt-3">
                <Link to={promptHref}>Open Prompt Artifact</Link>
              </Button>
            </div>
          )}

          {Object.keys(render.providerParams).length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Provider Params
              </p>
              <pre className="overflow-x-auto rounded-md bg-muted/40 p-3 text-xs text-foreground/85">
                {providerParamsJson}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      <RenderInputUsageCard inputs={render.resolvedInputs} />
    </div>
  )
}
