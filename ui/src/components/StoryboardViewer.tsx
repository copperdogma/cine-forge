import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Separator } from '@/components/ui/separator'
import { getAssetFileUrl } from '@/lib/api/assets'
import {
  Camera,
  ChevronDown,
  Clock,
  DollarSign,
  Image as ImageIcon,
  MessageSquare,
  Users,
} from 'lucide-react'

type StoryboardViewerProps = {
  data: Record<string, unknown>
  projectId: string
}

type StoryboardOverlayView = {
  shotIds: string[]
  shotSize: string | null
  cameraAngle: string | null
  cameraMovement: string | null
  characterLabels: string[]
  blockingIndicator: string | null
  cameraIndicator: string | null
  editIntent: string | null
}

type StoryboardFrameView = {
  frameId: string
  shotIds: string[]
  primaryShotId: string | null
  imagePath: string | null
  imageMediaType: string | null
  promptUsed: string | null
  promptSourcesUsed: string[]
  visualReferenceImages: string[]
  overlay: StoryboardOverlayView
  durationEstimateSeconds: number | null
  estimatedCostUsd: number | null
  model: string | null
  notes: string | null
}

type StoryboardView = {
  sceneId: string | null
  sceneNumber: number | null
  sceneHeading: string | null
  style: string | null
  aspectRatio: string | null
  totalEstimatedCostUsd: number | null
  frames: StoryboardFrameView[]
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

function formatToken(value: string | null): string | null {
  if (!value) return null
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null
  if (Number.isInteger(seconds)) return `${seconds}s`
  return `${seconds.toFixed(1)}s`
}

function formatMoney(amount: number | null): string | null {
  if (amount === null) return null
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function basename(path: string): string {
  const parts = path.split('/')
  return parts[parts.length - 1] || path
}

function toCssAspectRatio(value: string | null): string | undefined {
  if (!value) return undefined
  const parts = value.split(':').map((part) => part.trim())
  if (parts.length !== 2) return undefined
  const width = Number(parts[0])
  const height = Number(parts[1])
  if (!Number.isFinite(width) || !Number.isFinite(height) || height <= 0) return undefined
  return `${width} / ${height}`
}

function parseOverlay(value: unknown, shotIds: string[]): StoryboardOverlayView {
  const record = asRecord(value)
  return {
    shotIds: asStringArray(record?.shot_ids).length > 0 ? asStringArray(record?.shot_ids) : shotIds,
    shotSize: asString(record?.shot_size),
    cameraAngle: asString(record?.camera_angle),
    cameraMovement: asString(record?.camera_movement),
    characterLabels: asStringArray(record?.character_labels),
    blockingIndicator: asString(record?.blocking_indicator),
    cameraIndicator: asString(record?.camera_indicator),
    editIntent: asString(record?.edit_intent),
  }
}

function parseFrame(value: unknown, index: number): StoryboardFrameView {
  const record = asRecord(value)
  const shotIds = asStringArray(record?.shot_ids)
  const image = asRecord(record?.image)
  const cost = asRecord(record?.cost)

  return {
    frameId: asString(record?.frame_id) ?? `frame_${index + 1}`,
    shotIds,
    primaryShotId: asString(record?.primary_shot_id),
    imagePath: asString(image?.relative_path),
    imageMediaType: asString(image?.media_type),
    promptUsed: asString(record?.prompt_used),
    promptSourcesUsed: asStringArray(record?.prompt_sources_used),
    visualReferenceImages: asStringArray(record?.visual_reference_images),
    overlay: parseOverlay(record?.overlay, shotIds),
    durationEstimateSeconds: asNumber(record?.duration_estimate_seconds),
    estimatedCostUsd: asNumber(cost?.estimated_cost_usd),
    model: asString(cost?.model),
    notes: asString(record?.notes),
  }
}

function parseStoryboard(data: Record<string, unknown>): StoryboardView {
  return {
    sceneId: asString(data.scene_id),
    sceneNumber: asNumber(data.scene_number),
    sceneHeading: asString(data.scene_heading),
    style: asString(data.style),
    aspectRatio: asString(data.aspect_ratio),
    totalEstimatedCostUsd: asNumber(data.total_estimated_cost_usd),
    frames: asArray(data.frames).map(parseFrame),
  }
}

export function StoryboardViewer({ data, projectId }: StoryboardViewerProps) {
  const storyboard = parseStoryboard(data)
  const sceneLabel =
    storyboard.sceneNumber !== null ? `Scene ${storyboard.sceneNumber}` : 'Storyboard'
  const heading = storyboard.sceneHeading ?? storyboard.sceneId ?? 'Scene storyboard'
  const totalDuration = storyboard.frames.reduce((sum, frame) => {
    return sum + (frame.durationEstimateSeconds ?? 0)
  }, 0)
  const aspectRatioStyle = toCssAspectRatio(storyboard.aspectRatio)

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
                <ImageIcon className="h-3 w-3" />
                {storyboard.frames.length} {storyboard.frames.length === 1 ? 'frame' : 'frames'}
              </Badge>
              {formatToken(storyboard.style) && (
                <Badge variant="outline">{formatToken(storyboard.style)}</Badge>
              )}
              {storyboard.aspectRatio && (
                <Badge variant="outline">{storyboard.aspectRatio}</Badge>
              )}
              {storyboard.frames.length > 0 && (
                <Badge variant="outline" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(totalDuration)}
                </Badge>
              )}
              {formatMoney(storyboard.totalEstimatedCostUsd) && (
                <Badge variant="outline" className="gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatMoney(storyboard.totalEstimatedCostUsd)}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Storyboards turn the shot plan into fast visual review. Frame imagery is model-made;
            shot labels, blocking notes, and camera markers stay deterministic.
          </p>
        </CardContent>
      </Card>

      {storyboard.frames.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-sm text-muted-foreground">
              This storyboard artifact does not contain any frames yet.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {storyboard.frames.map((frame, index) => {
            const imageUrl = frame.imagePath ? getAssetFileUrl(projectId, frame.imagePath) : null
            const cameraBadges = [
              frame.overlay.shotSize,
              frame.overlay.cameraAngle,
              frame.overlay.cameraMovement,
            ].filter(Boolean) as string[]

            return (
              <Card key={frame.frameId} className="gap-0 overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <CardTitle className="text-base">Frame {index + 1}</CardTitle>
                        {frame.primaryShotId && (
                          <Badge variant="secondary">{frame.primaryShotId}</Badge>
                        )}
                        {formatDuration(frame.durationEstimateSeconds) && (
                          <Badge variant="outline" className="gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDuration(frame.durationEstimateSeconds)}
                          </Badge>
                        )}
                        {formatMoney(frame.estimatedCostUsd) && (
                          <Badge variant="outline" className="gap-1">
                            <DollarSign className="h-3 w-3" />
                            {formatMoney(frame.estimatedCostUsd)}
                          </Badge>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-xs text-muted-foreground">
                        <span className="font-mono">{frame.frameId}</span>
                        {frame.overlay.shotIds.length > 0 && (
                          <>
                            <span>&middot;</span>
                            <span>{frame.overlay.shotIds.join(', ')}</span>
                          </>
                        )}
                      </div>
                      {cameraBadges.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {cameraBadges.map((badge) => (
                            <Badge key={`${frame.frameId}-${badge}`} variant="outline" className="gap-1">
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
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,1fr)]">
                    <div className="space-y-2">
                      <div
                        className="overflow-hidden rounded-xl border border-border bg-muted/20"
                        style={aspectRatioStyle ? { aspectRatio: aspectRatioStyle } : undefined}
                      >
                        {imageUrl ? (
                          <img
                            src={imageUrl}
                            alt={`${heading} storyboard frame ${index + 1}`}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full min-h-56 items-center justify-center px-6 py-10 text-center text-sm text-muted-foreground">
                            Storyboard frame image is missing from this artifact version.
                          </div>
                        )}
                      </div>
                      {frame.imagePath && (
                        <p className="text-xs text-muted-foreground">{frame.imagePath}</p>
                      )}
                    </div>

                    <div className="space-y-4">
                      {frame.overlay.characterLabels.length > 0 && (
                        <div className="rounded-lg border border-border/70 bg-muted/20 p-3">
                          <div className="flex items-start gap-2">
                            <Users className="mt-0.5 h-4 w-4 text-muted-foreground" />
                            <div className="space-y-1">
                              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Characters In Frame
                              </p>
                              <p className="text-sm">
                                {frame.overlay.characterLabels.join(', ')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {[
                        ['Blocking', frame.overlay.blockingIndicator],
                        ['Camera Indicator', frame.overlay.cameraIndicator],
                        ['Edit Intent', frame.overlay.editIntent],
                        ['Notes', frame.notes],
                      ]
                        .filter(([, value]) => value)
                        .map(([label, value]) => (
                          <div key={`${frame.frameId}-${label}`} className="space-y-1">
                            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              {label}
                            </p>
                            <p className="text-sm leading-relaxed">{value}</p>
                          </div>
                        ))}

                      <Collapsible>
                        <div className="rounded-lg border border-border/70 bg-muted/20 p-3">
                          <CollapsibleTrigger className="flex w-full items-center justify-between gap-3 text-left">
                            <div className="space-y-1">
                              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Generation Context
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Prompt sources, references, and the exact frame prompt.
                              </p>
                            </div>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          </CollapsibleTrigger>
                          <CollapsibleContent className="space-y-3 pt-3">
                            {frame.promptSourcesUsed.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                  Prompt Sources
                                </p>
                                <div className="flex flex-wrap gap-1.5">
                                  {frame.promptSourcesUsed.map((source) => (
                                    <Badge key={`${frame.frameId}-${source}`} variant="outline">
                                      {formatToken(source) ?? source}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {frame.visualReferenceImages.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                  Reference Images
                                </p>
                                <div className="flex flex-wrap gap-1.5">
                                  {frame.visualReferenceImages.map((path) => (
                                    <Badge key={`${frame.frameId}-${path}`} variant="secondary">
                                      {basename(path)}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {frame.model && (
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <MessageSquare className="h-3.5 w-3.5" />
                                <span>Generated with {frame.model}</span>
                                {frame.imageMediaType && (
                                  <>
                                    <span>&middot;</span>
                                    <span>{frame.imageMediaType}</span>
                                  </>
                                )}
                              </div>
                            )}

                            {frame.promptUsed && (
                              <>
                                <Separator />
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Prompt Used
                                  </p>
                                  <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-border/70 bg-background px-3 py-2 text-xs leading-relaxed text-foreground">
                                    {frame.promptUsed}
                                  </pre>
                                </div>
                              </>
                            )}
                          </CollapsibleContent>
                        </div>
                      </Collapsible>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
