import { Link } from 'react-router-dom'
import { Clock, ExternalLink, Film, Timer, TriangleAlert } from 'lucide-react'
import {
  formatConsistencyStrategy,
  formatLatencyMs,
  formatPromptProfile,
  formatPrerequisiteStrategy,
  formatPreviewIntent,
  formatPreviewMode,
  parsePreviewProvenance,
} from '@/components/preview-provenance'
import {
  aiPrevizCostBadge,
  formatAdoptionState,
} from '@/components/previz-panel-support'
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
  type RenderInputUsageView,
} from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'
import { mediaValidationStatus } from '@/lib/health'
import { usePrevizAdoptionStatus } from '@/lib/hooks'
import type { ArtifactHealthDetails } from '@/lib/types'

type AiPrevizViewerProps = {
  data: Record<string, unknown>
  projectId: string
  health?: string | null
  healthDetails?: ArtifactHealthDetails | null
}

type ArtifactLinkView = {
  artifactType: string
  entityId: string | null
  version: number | null
}

type AiPrevizView = {
  sceneHeading: string | null
  sceneNumber: number | null
  videoPath: string | null
  durationSeconds: number | null
  resolution: string | null
  aspectRatio: string | null
  targetProvider: string | null
  targetModel: string | null
  enginePackId: string | null
  requestId: string | null
  notes: string[]
  resolvedInputs: RenderInputUsageView[]
  previewProvenance: ReturnType<typeof parsePreviewProvenance>
  promptRef: ArtifactLinkView | null
}

function parseArtifactLink(value: unknown): ArtifactLinkView | null {
  const record = asRecord(value)
  const artifactType = asString(record?.artifact_type)
  if (!artifactType) return null
  return {
    artifactType,
    entityId: asString(record?.entity_id),
    version: asNumber(record?.version),
  }
}

function artifactHref(projectId: string, ref: ArtifactLinkView | null): string | null {
  if (!ref || ref.version === null) return null
  const entityId = ref.entityId ?? 'project'
  return `/${projectId}/artifacts/${ref.artifactType}/${entityId}/${ref.version}`
}

function parseAiPreviz(data: Record<string, unknown>): AiPrevizView {
  const video = asRecord(data.video)
  return {
    sceneHeading: asString(data.scene_heading),
    sceneNumber: asNumber(data.scene_number),
    videoPath: asString(video?.relative_path),
    durationSeconds: asNumber(data.duration_seconds),
    resolution: asString(data.resolution),
    aspectRatio: asString(data.aspect_ratio),
    targetProvider: asString(data.target_provider),
    targetModel: asString(data.target_model),
    enginePackId: asString(data.engine_pack_id),
    requestId: asString(data.request_id),
    notes: asStringArray(data.notes),
    resolvedInputs: asArray(data.resolved_inputs)
      .map(parseRenderInputUsage)
      .filter((input): input is RenderInputUsageView => input !== null),
    previewProvenance: parsePreviewProvenance(data.preview_provenance),
    promptRef: parseArtifactLink(data.prompt_ref),
  }
}

function validationToneClass(label: string | null): string {
  if (label === 'Validated') {
    return 'border-emerald-500/20 bg-emerald-500/5 text-foreground/90'
  }
  if (label === 'Validation Failed') {
    return 'border-red-500/20 bg-red-500/5 text-foreground/90'
  }
  return 'border-amber-500/30 bg-amber-500/5 text-amber-100'
}

export function AiPrevizViewer({ data, projectId, health, healthDetails }: AiPrevizViewerProps) {
  const previz = parseAiPreviz(data)
  const { data: previzStatus } = usePrevizAdoptionStatus(projectId)
  const aiPrevizStatus = previzStatus?.ai_previz
  const sceneLabel = previz.sceneNumber !== null ? `Scene ${previz.sceneNumber}` : 'AI Previz'
  const videoUrl = previz.videoPath ? getAssetFileUrl(projectId, previz.videoPath) : null
  const promptHref = artifactHref(projectId, previz.promptRef)
  const validationHref = (
    healthDetails?.source_kind === 'media_validation'
    || healthDetails?.source_kind === 'media_validation_stale'
  )
    ? artifactHref(projectId, parseArtifactLink(healthDetails.source_artifact_ref))
    : null
  const validationStatus = mediaValidationStatus(health, healthDetails)
  const costBadge = aiPrevizCostBadge(aiPrevizStatus)
  const extraBlockers = (aiPrevizStatus?.blocker_reasons ?? [])
    .filter(blocker => blocker !== aiPrevizStatus?.reason)
    .slice(0, 2)

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>{sceneLabel}</CardTitle>
              <CardDescription>
                {previz.sceneHeading ?? 'Low-fidelity AI previz clip for planning review'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {aiPrevizStatus && (
                <Badge
                  variant={aiPrevizStatus.adoption_state === 'experimental_manual' ? 'outline' : 'secondary'}
                >
                  {formatAdoptionState(aiPrevizStatus.adoption_state)}
                </Badge>
              )}
              {formatPreviewMode(previz.previewProvenance?.mode ?? null) && (
                <Badge variant="secondary">
                  {formatPreviewMode(previz.previewProvenance?.mode ?? null)}
                </Badge>
              )}
              {formatPreviewIntent(previz.previewProvenance?.fidelityIntent ?? null) && (
                <Badge variant="outline">
                  {formatPreviewIntent(previz.previewProvenance?.fidelityIntent ?? null)}
                </Badge>
              )}
              {previz.targetProvider && (
                <Badge variant="outline">{formatToken(previz.targetProvider)}</Badge>
              )}
              {previz.targetModel && <Badge variant="outline">{previz.targetModel}</Badge>}
              {previz.enginePackId && (
                <Badge variant="outline" className="gap-1">
                  <Film className="h-3 w-3" />
                  {previz.enginePackId}
                </Badge>
              )}
              {formatDuration(previz.durationSeconds) && (
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(previz.durationSeconds)}
                </Badge>
              )}
              {previz.resolution && <Badge variant="outline">{previz.resolution}</Badge>}
              {previz.aspectRatio && <Badge variant="outline">{previz.aspectRatio}</Badge>}
              {formatConsistencyStrategy(previz.previewProvenance?.consistencyStrategy ?? null) && (
                <Badge variant="outline">
                  {formatConsistencyStrategy(previz.previewProvenance?.consistencyStrategy ?? null)}
                </Badge>
              )}
              {formatPromptProfile(previz.previewProvenance?.promptProfile ?? null) && (
                <Badge variant="outline">
                  {formatPromptProfile(previz.previewProvenance?.promptProfile ?? null)}
                </Badge>
              )}
              {formatPrerequisiteStrategy(previz.previewProvenance?.prerequisiteStrategy ?? null) && (
                <Badge variant="outline">
                  {formatPrerequisiteStrategy(previz.previewProvenance?.prerequisiteStrategy ?? null)}
                </Badge>
              )}
              {formatLatencyMs(previz.previewProvenance?.generationLatencyMs ?? null) && (
                <Badge variant="outline" className="gap-1">
                  <Timer className="h-3 w-3" />
                  {formatLatencyMs(previz.previewProvenance?.generationLatencyMs ?? null)}
                </Badge>
              )}
              {costBadge && <Badge variant="outline">{costBadge}</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
            <div className="flex items-start gap-2">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
              <p>
                This clip is previz, not final footage. Use it to judge camera placement,
                blocking, motion, pacing, and location readability without obsessing over polish.
              </p>
            </div>
          </div>

          {(previz.previewProvenance?.prerequisiteStrategy
            || (previz.previewProvenance?.reusedArtifactTypes?.length ?? 0) > 0
            || (previz.previewProvenance?.autoBuildArtifactTypes?.length ?? 0) > 0
            || (previz.previewProvenance?.missingOptionalArtifactTypes?.length ?? 0) > 0) && (
            <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
              <div className="space-y-1">
                {formatPrerequisiteStrategy(previz.previewProvenance?.prerequisiteStrategy ?? null) && (
                  <p>
                    Prep strategy:{' '}
                    {formatPrerequisiteStrategy(previz.previewProvenance?.prerequisiteStrategy ?? null)}
                  </p>
                )}
                {(previz.previewProvenance?.reusedArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Reused:{' '}
                    {previz.previewProvenance?.reusedArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
                {(previz.previewProvenance?.autoBuildArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Auto-built:{' '}
                    {previz.previewProvenance?.autoBuildArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
                {(previz.previewProvenance?.missingOptionalArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Missing optional context:{' '}
                    {previz.previewProvenance?.missingOptionalArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
              </div>
            </div>
          )}

          {validationStatus && (
            <div className={`rounded-lg border px-4 py-3 text-sm ${validationToneClass(validationStatus.label)}`}>
              <div className="space-y-1">
                <p className="font-medium">{validationStatus.label}</p>
                <p>{validationStatus.description}</p>
              </div>
            </div>
          )}

          {aiPrevizStatus && (
            <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
              <div className="space-y-1">
                <p>{aiPrevizStatus.reason}</p>
                {aiPrevizStatus.cost.status === 'blocked' && aiPrevizStatus.cost.reason && (
                  <p>Cost blocker: {aiPrevizStatus.cost.reason}</p>
                )}
                {aiPrevizStatus.cost.status === 'estimated' && (
                  <p>
                    Estimated cost for the active recipe defaults:{' '}
                    {formatMoney(aiPrevizStatus.cost.estimated_cost_usd ?? null) ?? 'n/a'}.
                  </p>
                )}
                {extraBlockers.map(blocker => (
                  <p key={blocker}>{blocker}</p>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {promptHref && (
              <Button asChild variant="outline" size="sm">
                <Link to={promptHref}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  Prompt Detail
                </Link>
              </Button>
            )}
            {validationHref && (
              <Button asChild variant="outline" size="sm">
                <Link to={validationHref}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  Validation Detail
                </Link>
              </Button>
            )}
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
              AI previz media is missing from this artifact.
            </div>
          )}

          {previz.notes.length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              {previz.notes.map(note => (
                <p key={note}>{note}</p>
              ))}
            </div>
          )}

          {previz.previewProvenance?.upstreamInputs.length ? (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              Inputs: {previz.previewProvenance.upstreamInputs.join(', ')}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <RenderInputUsageCard inputs={previz.resolvedInputs} />
    </div>
  )
}
