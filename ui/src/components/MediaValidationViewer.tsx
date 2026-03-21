import { Link } from 'react-router-dom'
import { CheckCircle2, ExternalLink, ShieldAlert, ShieldCheck } from 'lucide-react'
import { HealthBadge } from '@/components/HealthBadge'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { asArray, asBoolean, asNumber, asRecord, asString, formatDuration } from '@/components/render-utils'
import { getAssetFileUrl } from '@/lib/api/assets'

type Props = {
  data: Record<string, unknown>
  projectId: string
  compact?: boolean
  detailHref?: string | null
}

type FindingView = {
  code: string
  severity: string
  message: string
}

type SampleFrameView = {
  relativePath: string
  timestampSeconds: number | null
}

type ValidationView = {
  recommendedHealth: string | null
  summary: string | null
  validatorId: string | null
  validationMode: string | null
  samplingPolicy: string | null
  targetRefLabel: string | null
  durationSeconds: number | null
  decodeSucceeded: boolean
  videoStreamPresent: boolean
  audioStreamPresent: boolean
  sampleCountRequested: number | null
  sampleCountExtracted: number | null
  deterministicFindings: FindingView[]
  semanticStatus: string | null
  semanticModel: string | null
  semanticSummary: string | null
  semanticConfidence: number | null
  semanticFindings: FindingView[]
  sampleFrames: SampleFrameView[]
}

function parseFinding(value: unknown): FindingView | null {
  const record = asRecord(value)
  if (!record) return null
  return {
    code: asString(record.code) ?? 'finding',
    severity: asString(record.severity) ?? 'warning',
    message: asString(record.message) ?? 'Validation finding',
  }
}

function parseSampleFrame(value: unknown): SampleFrameView | null {
  const record = asRecord(value)
  if (!record) return null
  const image = asRecord(record.image)
  const relativePath = asString(image?.relative_path)
  if (!relativePath) return null
  return {
    relativePath,
    timestampSeconds: asNumber(record.timestamp_seconds),
  }
}

function parseValidation(data: Record<string, unknown>): ValidationView {
  const targetRef = asRecord(data.target_ref)
  const validatedMedia = asRecord(data.validated_media)
  const deterministicProbe = asRecord(data.deterministic_probe)
  const semanticReview = asRecord(data.semantic_review)
  const targetType = asString(targetRef?.artifact_type)
  const targetEntity = asString(targetRef?.entity_id) ?? 'project'
  const targetVersion = asNumber(targetRef?.version)

  return {
    recommendedHealth: asString(data.recommended_health),
    summary: asString(data.summary),
    validatorId: asString(data.validator_id),
    validationMode: asString(data.validation_mode),
    samplingPolicy: asString(data.sampling_policy),
    targetRefLabel: targetType && targetVersion !== null
      ? `${targetType}:${targetEntity}:v${targetVersion}`
      : null,
    durationSeconds: asNumber(validatedMedia?.duration_seconds) ?? asNumber(deterministicProbe?.duration_seconds),
    decodeSucceeded: asBoolean(deterministicProbe?.decode_succeeded),
    videoStreamPresent: asBoolean(deterministicProbe?.video_stream_present),
    audioStreamPresent: asBoolean(deterministicProbe?.audio_stream_present),
    sampleCountRequested: asNumber(deterministicProbe?.sample_count_requested),
    sampleCountExtracted: asNumber(deterministicProbe?.sample_count_extracted),
    deterministicFindings: asArray(deterministicProbe?.findings)
      .map(parseFinding)
      .filter((finding): finding is FindingView => finding !== null),
    semanticStatus: asString(semanticReview?.status),
    semanticModel: asString(semanticReview?.model),
    semanticSummary: asString(semanticReview?.summary) ?? asString(semanticReview?.reason_skipped),
    semanticConfidence: asNumber(semanticReview?.confidence),
    semanticFindings: asArray(semanticReview?.findings)
      .map(parseFinding)
      .filter((finding): finding is FindingView => finding !== null),
    sampleFrames: asArray(deterministicProbe?.sample_frames)
      .map(parseSampleFrame)
      .filter((frame): frame is SampleFrameView => frame !== null),
  }
}

function FindingsList({ findings }: { findings: FindingView[] }) {
  if (findings.length === 0) {
    return <p className="text-sm text-muted-foreground">No findings recorded.</p>
  }

  return (
    <div className="space-y-2">
      {findings.map(finding => (
        <div key={`${finding.code}-${finding.message}`} className="rounded-lg border border-border bg-card/60 px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={finding.severity === 'error' ? 'destructive' : 'outline'}>
              {finding.severity}
            </Badge>
            <span className="text-xs font-mono text-muted-foreground">{finding.code}</span>
          </div>
          <p className="mt-2 text-sm text-foreground/90">{finding.message}</p>
        </div>
      ))}
    </div>
  )
}

export function MediaValidationViewer({ data, projectId, compact = false, detailHref }: Props) {
  const validation = parseValidation(data)
  const sampleFrames = validation.sampleFrames.slice(0, compact ? 3 : 6)

  if (compact) {
    return (
      <Card className="gap-0 border-border/70">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">Validation</CardTitle>
                <HealthBadge health={validation.recommendedHealth} />
              </div>
              <CardDescription>
                {validation.summary ?? 'No validation summary recorded yet.'}
              </CardDescription>
            </div>
            {detailHref && (
              <Badge asChild variant="outline" className="gap-1">
                <Link to={detailHref}>
                  <ExternalLink className="h-3 w-3" />
                  Validation Detail
                </Link>
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {validation.validationMode && <Badge variant="secondary">{validation.validationMode}</Badge>}
            {validation.samplingPolicy && <Badge variant="outline">{validation.samplingPolicy}</Badge>}
            {validation.semanticStatus && <Badge variant="outline">semantic: {validation.semanticStatus}</Badge>}
            {validation.semanticModel && <Badge variant="outline">{validation.semanticModel}</Badge>}
          </div>
          {sampleFrames.length > 0 && (
            <div className="grid grid-cols-3 gap-2">
              {sampleFrames.map(frame => (
                <img
                  key={frame.relativePath}
                  src={getAssetFileUrl(projectId, frame.relativePath)}
                  alt={`Validation sample at ${frame.timestampSeconds ?? 0}s`}
                  className="aspect-video rounded-lg border border-border object-cover"
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CardTitle>Media Validation</CardTitle>
                <HealthBadge health={validation.recommendedHealth} />
              </div>
              <CardDescription>
                {validation.summary ?? 'No validation summary recorded yet.'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {validation.validatorId && (
                <Badge variant="secondary" className="gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  {validation.validatorId}
                </Badge>
              )}
              {validation.validationMode && <Badge variant="outline">{validation.validationMode}</Badge>}
              {validation.targetRefLabel && <Badge variant="outline">{validation.targetRefLabel}</Badge>}
              {formatDuration(validation.durationSeconds) && (
                <Badge variant="outline">{formatDuration(validation.durationSeconds)}</Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Deterministic
              </p>
              <div className="mt-2 flex items-center gap-2 text-sm">
                {validation.decodeSucceeded ? (
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                ) : (
                  <ShieldAlert className="h-4 w-4 text-red-400" />
                )}
                <span>{validation.decodeSucceeded ? 'Decode succeeded' : 'Decode failed'}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                video={String(validation.videoStreamPresent)} · audio={String(validation.audioStreamPresent)}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Samples
              </p>
              <p className="mt-2 text-sm">
                {validation.sampleCountExtracted ?? 0}/{validation.sampleCountRequested ?? 0} frames extracted
              </p>
            </div>
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Semantic Review
              </p>
              <p className="mt-2 text-sm">
                {validation.semanticStatus ?? 'skipped'}
              </p>
              {validation.semanticModel && (
                <p className="mt-1 text-xs text-muted-foreground">{validation.semanticModel}</p>
              )}
            </div>
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Confidence
              </p>
              <p className="mt-2 text-sm">
                {validation.semanticConfidence !== null ? `${Math.round(validation.semanticConfidence * 100)}%` : 'n/a'}
              </p>
            </div>
          </div>

          {validation.semanticSummary && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Semantic Summary
              </p>
              <p className="mt-2 text-sm text-foreground/90">{validation.semanticSummary}</p>
            </div>
          )}

          {sampleFrames.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Sample Frames
              </p>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {sampleFrames.map(frame => (
                  <div key={frame.relativePath} className="space-y-2">
                    <img
                      src={getAssetFileUrl(projectId, frame.relativePath)}
                      alt={`Validation sample at ${frame.timestampSeconds ?? 0}s`}
                      className="aspect-video rounded-lg border border-border object-cover"
                    />
                    <p className="text-xs text-muted-foreground">
                      {frame.timestampSeconds !== null ? `${frame.timestampSeconds.toFixed(2)}s` : 'Timestamp unavailable'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 xl:grid-cols-2">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Deterministic Findings
              </p>
              <FindingsList findings={validation.deterministicFindings} />
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Semantic Findings
              </p>
              <FindingsList findings={validation.semanticFindings} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
