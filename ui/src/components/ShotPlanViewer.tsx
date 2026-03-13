import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Camera, Clock, Clapperboard, MessageSquare, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

type ShotPlanViewerProps = {
  data: Record<string, unknown>
}

type AuditView = {
  rationale: string | null
  confidence: number | null
  source: string | null
}

type CoverageView = {
  coverageApproach: string | null
  rhythmAndFlowIntent: string | null
  lookAndFeelIntent: string | null
  soundAndMusicIntent: string | null
  characterAndPerformanceNotes: string | null
  coveragePatterns: string[]
  adequacyVerdict: string | null
  adequacyRationale: string | null
  audit: AuditView
}

type ShotView = {
  shotId: string
  coverageRole: string | null
  shotSize: string | null
  cameraAngle: string | null
  cameraMovement: string | null
  lensFocalLength: string | null
  charactersInFrame: string[]
  pointOfViewCharacter: string | null
  blocking: string | null
  actionDescription: string | null
  dialogueLines: string[]
  durationEstimateSeconds: number | null
  editIntent: string | null
  audit: AuditView
}

type ShotPlanView = {
  sceneId: string | null
  sceneNumber: number | null
  sceneHeading: string | null
  totalEstimatedDurationSeconds: number | null
  coverage: CoverageView | null
  shots: ShotView[]
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
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

function parseAudit(value: unknown): AuditView {
  const record = asRecord(value)
  return {
    rationale: asString(record?.rationale),
    confidence: asNumber(record?.confidence),
    source: asString(record?.source),
  }
}

function parseCoverage(value: unknown): CoverageView | null {
  const record = asRecord(value)
  if (!record) return null

  const adequacyCheck = asRecord(record.adequacy_check)
  return {
    coverageApproach: asString(record.coverage_approach),
    rhythmAndFlowIntent: asString(record.rhythm_and_flow_intent),
    lookAndFeelIntent: asString(record.look_and_feel_intent),
    soundAndMusicIntent: asString(record.sound_and_music_intent),
    characterAndPerformanceNotes: asString(record.character_and_performance_notes),
    coveragePatterns: asStringArray(record.coverage_patterns),
    adequacyVerdict: asString(adequacyCheck?.verdict),
    adequacyRationale: asString(adequacyCheck?.rationale),
    audit: parseAudit(record.audit),
  }
}

function parseShot(value: unknown, index: number): ShotView {
  const record = asRecord(value)
  return {
    shotId: asString(record?.shot_id) ?? `Shot ${index + 1}`,
    coverageRole: asString(record?.coverage_role),
    shotSize: asString(record?.shot_size),
    cameraAngle: asString(record?.camera_angle),
    cameraMovement: asString(record?.camera_movement),
    lensFocalLength: asString(record?.lens_focal_length),
    charactersInFrame: asStringArray(record?.characters_in_frame),
    pointOfViewCharacter: asString(record?.point_of_view_character),
    blocking: asString(record?.blocking),
    actionDescription: asString(record?.action_description),
    dialogueLines: asStringArray(record?.dialogue_lines),
    durationEstimateSeconds: asNumber(record?.duration_estimate_seconds),
    editIntent: asString(record?.edit_intent),
    audit: parseAudit(record?.audit),
  }
}

function parseShotPlan(data: Record<string, unknown>): ShotPlanView {
  return {
    sceneId: asString(data.scene_id),
    sceneNumber: asNumber(data.scene_number),
    sceneHeading: asString(data.scene_heading),
    totalEstimatedDurationSeconds: asNumber(data.total_estimated_duration_seconds),
    coverage: parseCoverage(data.coverage_strategy),
    shots: asArray(data.shots).map(parseShot),
  }
}

function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null
  if (Number.isInteger(seconds)) return `${seconds}s`
  return `${seconds.toFixed(1)}s`
}

function formatConfidence(confidence: number | null): string | null {
  if (confidence === null) return null
  return `${Math.round(confidence * 100)}% confidence`
}

function adequacyBadgeClass(verdict: string | null): string {
  switch (verdict) {
    case 'adequate':
      return 'border-emerald-500/30 text-emerald-400'
    case 'borderline':
      return 'border-amber-500/30 text-amber-400'
    case 'inadequate':
      return 'border-red-500/30 text-red-400'
    default:
      return 'border-border text-muted-foreground'
  }
}

export function ShotPlanViewer({ data }: ShotPlanViewerProps) {
  const plan = parseShotPlan(data)
  const sceneLabel = plan.sceneNumber !== null ? `Scene ${plan.sceneNumber}` : 'Shot Plan'
  const heading = plan.sceneHeading ?? plan.sceneId ?? 'Scene shot plan'

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>{sceneLabel}</CardTitle>
              <CardDescription>{heading}</CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="gap-1">
                <Clapperboard className="h-3 w-3" />
                {plan.shots.length} {plan.shots.length === 1 ? 'shot' : 'shots'}
              </Badge>
              {formatDuration(plan.totalEstimatedDurationSeconds) && (
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(plan.totalEstimatedDurationSeconds)}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {plan.coverage ? (
            <>
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold">Coverage Strategy</h3>
                  {plan.coverage.adequacyVerdict && (
                    <Badge
                      variant="outline"
                      className={cn('capitalize', adequacyBadgeClass(plan.coverage.adequacyVerdict))}
                    >
                      {plan.coverage.adequacyVerdict}
                    </Badge>
                  )}
                </div>
                {plan.coverage.coverageApproach && (
                  <p className="text-sm leading-relaxed">{plan.coverage.coverageApproach}</p>
                )}
                {plan.coverage.adequacyRationale && (
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {plan.coverage.adequacyRationale}
                  </p>
                )}
                {plan.coverage.coveragePatterns.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {plan.coverage.coveragePatterns.map((pattern) => (
                      <Badge key={pattern} variant="outline" className="text-xs">
                        {pattern}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ['Rhythm & Flow', plan.coverage.rhythmAndFlowIntent],
                  ['Look & Feel', plan.coverage.lookAndFeelIntent],
                  ['Sound & Music', plan.coverage.soundAndMusicIntent],
                  ['Performance', plan.coverage.characterAndPerformanceNotes],
                ]
                  .filter(([, value]) => value)
                  .map(([label, value]) => (
                    <div key={label} className="rounded-lg border border-border/70 bg-muted/20 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        {label}
                      </p>
                      <p className="mt-1 text-sm leading-relaxed">{value}</p>
                    </div>
                  ))}
              </div>

              {(plan.coverage.audit.rationale || plan.coverage.audit.source || plan.coverage.audit.confidence !== null) && (
                <>
                  <Separator />
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {plan.coverage.audit.source && (
                      <Badge variant="outline" className="capitalize">
                        {plan.coverage.audit.source}
                      </Badge>
                    )}
                    {formatConfidence(plan.coverage.audit.confidence) && (
                      <span>{formatConfidence(plan.coverage.audit.confidence)}</span>
                    )}
                    {plan.coverage.audit.rationale && (
                      <span className="max-w-2xl leading-relaxed">{plan.coverage.audit.rationale}</span>
                    )}
                  </div>
                </>
              )}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Coverage strategy details are not available on this artifact version.
            </p>
          )}
        </CardContent>
      </Card>

      {plan.shots.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-sm text-muted-foreground">
              This shot plan does not contain any ordered shots yet.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {plan.shots.map((shot) => {
            const cameraBadges = [
              shot.shotSize,
              shot.cameraAngle,
              shot.cameraMovement,
              shot.lensFocalLength,
            ].filter(Boolean) as string[]

            return (
              <Card key={shot.shotId} className="gap-0">
                <CardHeader className="pb-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <CardTitle className="text-base">{shot.shotId}</CardTitle>
                        {shot.coverageRole && <Badge variant="secondary">{shot.coverageRole}</Badge>}
                        {formatDuration(shot.durationEstimateSeconds) && (
                          <Badge variant="outline" className="gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDuration(shot.durationEstimateSeconds)}
                          </Badge>
                        )}
                      </div>
                      {cameraBadges.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {cameraBadges.map((badge) => (
                            <Badge key={`${shot.shotId}-${badge}`} variant="outline" className="gap-1">
                              <Camera className="h-3 w-3" />
                              {badge}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {(shot.charactersInFrame.length > 0 || shot.pointOfViewCharacter) && (
                    <div className="flex flex-col gap-2 rounded-lg border border-border/70 bg-muted/20 p-3 text-sm">
                      {shot.charactersInFrame.length > 0 && (
                        <div className="flex items-start gap-2">
                          <Users className="mt-0.5 h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              In Frame
                            </p>
                            <p>{shot.charactersInFrame.join(', ')}</p>
                          </div>
                        </div>
                      )}
                      {shot.pointOfViewCharacter && (
                        <div className="flex items-start gap-2">
                          <Camera className="mt-0.5 h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              Point of View
                            </p>
                            <p>{shot.pointOfViewCharacter}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {[
                    ['Blocking', shot.blocking],
                    ['Action', shot.actionDescription],
                    ['Edit Intent', shot.editIntent],
                  ]
                    .filter(([, value]) => value)
                    .map(([label, value]) => (
                      <div key={`${shot.shotId}-${label}`} className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          {label}
                        </p>
                        <p className="text-sm leading-relaxed">{value}</p>
                      </div>
                    ))}

                  {shot.dialogueLines.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Dialogue
                        </p>
                      </div>
                      <div className="space-y-2">
                        {shot.dialogueLines.map((line, index) => (
                          <div
                            key={`${shot.shotId}-dialogue-${index}`}
                            className="rounded-lg border border-border/70 bg-muted/20 px-3 py-2 text-sm leading-relaxed"
                          >
                            {line}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {(shot.audit.rationale || shot.audit.source || shot.audit.confidence !== null) && (
                    <>
                      <Separator />
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        {shot.audit.source && (
                          <Badge variant="outline" className="capitalize">
                            {shot.audit.source}
                          </Badge>
                        )}
                        {formatConfidence(shot.audit.confidence) && (
                          <span>{formatConfidence(shot.audit.confidence)}</span>
                        )}
                        {shot.audit.rationale && (
                          <span className="max-w-2xl leading-relaxed">{shot.audit.rationale}</span>
                        )}
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
