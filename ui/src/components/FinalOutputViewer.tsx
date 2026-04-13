import { Link } from 'react-router-dom'
import { Download, ExternalLink, Film, Layers3 } from 'lucide-react'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  asArray,
  asBoolean,
  asNumber,
  asRecord,
  asString,
  formatDuration,
} from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'
import { useArtifact } from '@/lib/hooks'
import type { ArtifactHealthDetails } from '@/lib/types'

type FinalOutputViewerProps = {
  data: Record<string, unknown>
  projectId: string
  healthDetails?: ArtifactHealthDetails | null
}

type FinalOutputSceneView = {
  sceneId: string
  sceneNumber: number | null
  sceneHeading: string | null
  generatedVideoVersion: number | null
  clipPath: string | null
  durationSeconds: number | null
  outputStartSeconds: number | null
  outputEndSeconds: number | null
}

type FinalOutputOmittedSceneView = {
  sceneId: string
  sceneNumber: number | null
  sceneHeading: string | null
  reason: string | null
  detail: string | null
}

type FinalOutputView = {
  videoPath: string | null
  durationSeconds: number | null
  coverageState: string | null
  totalSceneCount: number | null
  includedSceneIds: string[]
  omittedSceneIds: string[]
  includedScenes: FinalOutputSceneView[]
  omittedScenes: FinalOutputOmittedSceneView[]
  normalizationApplied: boolean
  normalizationNotes: string[]
  timelineVersion: number | null
  trackManifestVersion: number | null
}

type ArtifactLinkView = {
  artifactType: string
  entityId: string | null
  version: number | null
}

function parseIncludedScene(value: unknown): FinalOutputSceneView | null {
  const record = asRecord(value)
  if (!record) return null
  const generatedVideoRef = asRecord(record.generated_video_ref)
  return {
    sceneId: asString(record.scene_id) ?? 'scene',
    sceneNumber: asNumber(record.scene_number),
    sceneHeading: asString(record.scene_heading),
    generatedVideoVersion: asNumber(generatedVideoRef?.version),
    clipPath: asString(record.clip_relative_path),
    durationSeconds: asNumber(record.duration_seconds),
    outputStartSeconds: asNumber(record.output_start_seconds),
    outputEndSeconds: asNumber(record.output_end_seconds),
  }
}

function parseOmittedScene(value: unknown): FinalOutputOmittedSceneView | null {
  const record = asRecord(value)
  if (!record) return null
  return {
    sceneId: asString(record.scene_id) ?? 'scene',
    sceneNumber: asNumber(record.scene_number),
    sceneHeading: asString(record.scene_heading),
    reason: asString(record.reason),
    detail: asString(record.detail),
  }
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

function parseFinalOutput(data: Record<string, unknown>): FinalOutputView {
  const video = asRecord(data.video)
  const timelineRef = asRecord(data.timeline_ref)
  const trackManifestRef = asRecord(data.track_manifest_ref)
  return {
    videoPath: asString(video?.relative_path),
    durationSeconds: asNumber(video?.duration_seconds),
    coverageState: asString(data.coverage_state),
    totalSceneCount: asNumber(data.total_scene_count),
    includedSceneIds: asArray(data.included_scene_ids)
      .map(item => (typeof item === 'string' ? item : ''))
      .filter(Boolean),
    omittedSceneIds: asArray(data.omitted_scene_ids)
      .map(item => (typeof item === 'string' ? item : ''))
      .filter(Boolean),
    includedScenes: asArray(data.included_scenes)
      .map(parseIncludedScene)
      .filter((scene): scene is FinalOutputSceneView => scene !== null),
    omittedScenes: asArray(data.omitted_scenes)
      .map(parseOmittedScene)
      .filter((scene): scene is FinalOutputOmittedSceneView => scene !== null),
    normalizationApplied: asBoolean(data.normalization_applied),
    normalizationNotes: asArray(data.normalization_notes)
      .map(item => (typeof item === 'string' ? item.trim() : ''))
      .filter(Boolean),
    timelineVersion: asNumber(timelineRef?.version),
    trackManifestVersion: asNumber(trackManifestRef?.version),
  }
}

function formatCoverageLabel(coverageState: string | null): string {
  if (coverageState === 'complete') return 'Complete Coverage'
  if (coverageState === 'partial') return 'Partial Coverage'
  return 'Coverage Unknown'
}

function formatOmissionReason(reason: string | null): string {
  if (reason === 'missing_generated_video_track') return 'Missing generated-video track'
  if (reason === 'missing_generated_video_artifact') return 'Missing generated-video media'
  return 'Omitted'
}

function formatTimelineRange(
  startSeconds: number | null,
  endSeconds: number | null,
): string | null {
  if (startSeconds === null || endSeconds === null) return null
  return `${formatDuration(startSeconds) ?? `${startSeconds}s`} - ${formatDuration(endSeconds) ?? `${endSeconds}s`}`
}

function validationStatusCopy(details: ArtifactHealthDetails | null | undefined): string | null {
  if (!details?.source_kind) return null
  if (details.source_kind === 'media_validation_missing') {
    return 'This assembled cut has not been validated yet.'
  }
  if (details.source_kind === 'media_validation_stale') {
    return 'The latest validation artifact still points at an older assembled cut.'
  }
  if (details.source_kind === 'media_validation') {
    return details.reason ?? 'Validation is available for this assembled cut.'
  }
  return details.reason ?? null
}

export function FinalOutputViewer({ data, projectId, healthDetails }: FinalOutputViewerProps) {
  const finalOutput = parseFinalOutput(data)
  const videoUrl = finalOutput.videoPath
    ? getAssetFileUrl(projectId, finalOutput.videoPath)
    : null
  const includedCount = finalOutput.includedScenes.length
  const totalCount = finalOutput.totalSceneCount ?? includedCount + finalOutput.omittedScenes.length
  const validationRef =
    healthDetails?.source_kind === 'media_validation'
      || healthDetails?.source_kind === 'media_validation_stale'
      ? parseArtifactLink(healthDetails.source_artifact_ref)
      : null
  const validationDetailHref = artifactHref(projectId, validationRef)
  const { data: validationArtifact } = useArtifact(
    projectId,
    validationRef?.artifactType,
    validationRef?.entityId ?? undefined,
    validationRef?.version ?? undefined,
  )
  const validationData = validationArtifact?.payload?.data as Record<string, unknown> | undefined

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>Final Output</CardTitle>
              <CardDescription>
                Project-level playable cut assembled only from generated scene renders.
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={finalOutput.coverageState === 'complete' ? 'secondary' : 'outline'}>
                {formatCoverageLabel(finalOutput.coverageState)}
              </Badge>
              <Badge variant="outline">
                {includedCount}/{totalCount} scenes included
              </Badge>
              {formatDuration(finalOutput.durationSeconds) && (
                <Badge variant="outline">
                  <Film className="mr-1 h-3 w-3" />
                  {formatDuration(finalOutput.durationSeconds)}
                </Badge>
              )}
              {finalOutput.timelineVersion !== null && (
                <Badge variant="outline">Timeline v{finalOutput.timelineVersion}</Badge>
              )}
              {finalOutput.trackManifestVersion !== null && (
                <Badge variant="outline">Tracks v{finalOutput.trackManifestVersion}</Badge>
              )}
              {finalOutput.normalizationApplied && (
                <Badge variant="outline">
                  <Layers3 className="mr-1 h-3 w-3" />
                  Normalized
                </Badge>
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
              Final output media is missing from this artifact.
            </div>
          )}

          {videoUrl && (
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline" size="sm">
                <a href={videoUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open Media
                </a>
              </Button>
              <Button asChild variant="outline" size="sm">
                <a href={videoUrl} download="final_output.mp4">
                  <Download className="h-3.5 w-3.5" />
                  Download
                </a>
              </Button>
              {validationDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={validationDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Validation Detail
                  </Link>
                </Button>
              )}
            </div>
          )}

          {validationStatusCopy(healthDetails) && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              <p>{validationStatusCopy(healthDetails)}</p>
            </div>
          )}

          {finalOutput.normalizationNotes.length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3 text-sm text-muted-foreground">
              {finalOutput.normalizationNotes.map(note => (
                <p key={note}>{note}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {validationData && healthDetails?.source_kind === 'media_validation' && (
        <MediaValidationViewer
          data={validationData}
          projectId={projectId}
          compact
          detailHref={validationDetailHref}
        />
      )}

      <Card className="gap-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Included Scenes</CardTitle>
          <CardDescription>
            Scenes appear in timeline edit order using the latest generated-video track.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {finalOutput.includedScenes.length === 0 ? (
            <p className="text-sm text-muted-foreground">No rendered scenes were included.</p>
          ) : (
            finalOutput.includedScenes.map(scene => (
              <div
                key={scene.sceneId}
                className="rounded-lg border border-border bg-card/60 px-4 py-3"
              >
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      {scene.sceneNumber !== null ? `Scene ${scene.sceneNumber}` : scene.sceneId}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {scene.sceneHeading ?? scene.sceneId}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formatDuration(scene.durationSeconds) && (
                      <Badge variant="outline">{formatDuration(scene.durationSeconds)}</Badge>
                    )}
                    {formatTimelineRange(scene.outputStartSeconds, scene.outputEndSeconds) && (
                      <Badge variant="outline">
                        {formatTimelineRange(scene.outputStartSeconds, scene.outputEndSeconds)}
                      </Badge>
                    )}
                    {scene.generatedVideoVersion !== null && (
                      <Badge variant="secondary">Render v{scene.generatedVideoVersion}</Badge>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {finalOutput.omittedScenes.length > 0 && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Omitted Scenes</CardTitle>
            <CardDescription>
              Final Output never fills missing scenes with storyboards, previz, or other fallback media.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {finalOutput.omittedScenes.map(scene => (
              <div
                key={scene.sceneId}
                className="rounded-lg border border-amber-500/20 bg-background/70 px-4 py-3"
              >
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium">
                    {scene.sceneNumber !== null ? `Scene ${scene.sceneNumber}` : scene.sceneId}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {scene.sceneHeading ?? scene.sceneId}
                  </p>
                  <p className="text-sm text-amber-300">{formatOmissionReason(scene.reason)}</p>
                  {scene.detail && (
                    <p className="text-sm text-muted-foreground">{scene.detail}</p>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
