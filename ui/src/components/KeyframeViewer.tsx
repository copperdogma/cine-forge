import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getAssetFileUrl } from '@/lib/api/assets'
import { useEditArtifact } from '@/lib/hooks'
import { Image as ImageIcon, Lock, Unlock } from 'lucide-react'

type KeyframeViewerProps = {
  data: Record<string, unknown>
  projectId: string
  entityId?: string
  editable?: boolean
}

type KeyframeView = {
  keyframeId: string
  shotId: string | null
  position: string | null
  imagePath: string | null
  timestampSeconds: number | null
  sourceKind: string | null
  isLocked: boolean
  shotSize: string | null
  cameraAngle: string | null
  cameraMovement: string | null
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

function parseKeyframe(value: unknown): KeyframeView | null {
  const record = asRecord(value)
  const image = asRecord(record?.image)
  const keyframeId = asString(record?.keyframe_id)
  if (!keyframeId) return null
  return {
    keyframeId,
    shotId: asString(record?.shot_id),
    position: asString(record?.position),
    imagePath: asString(image?.relative_path),
    timestampSeconds: asNumber(record?.timestamp_seconds),
    sourceKind: asString(record?.source_kind),
    isLocked: Boolean(record?.is_locked),
    shotSize: asString(record?.shot_size),
    cameraAngle: asString(record?.camera_angle),
    cameraMovement: asString(record?.camera_movement),
  }
}

function formatSeconds(value: number | null): string | null {
  if (value === null) return null
  return `${value.toFixed(1)}s`
}

export function KeyframeViewer({
  data,
  projectId,
  entityId,
  editable = false,
}: KeyframeViewerProps) {
  const editArtifact = useEditArtifact()
  const keyframes = asArray(data.keyframes)
    .map(parseKeyframe)
    .filter((item): item is KeyframeView => item !== null)

  const grouped = new Map<string, KeyframeView[]>()
  for (const keyframe of keyframes) {
    const key = keyframe.shotId ?? 'Unlinked Shot'
    const current = grouped.get(key) ?? []
    current.push(keyframe)
    grouped.set(key, current)
  }

  async function handleToggleLock(keyframeId: string, nextLocked: boolean) {
    if (!editable || !entityId) return
    const nextKeyframes = asArray(data.keyframes).map(item => {
      const record = asRecord(item)
      if (!record || record.keyframe_id !== keyframeId) return item
      return {
        ...record,
        is_locked: nextLocked,
        locked_by: nextLocked ? 'director' : null,
        lock_reason: nextLocked ? 'Approved from the scene workspace.' : null,
      }
    })

    try {
      await editArtifact.mutateAsync({
        projectId,
        artifactType: 'keyframe',
        entityId,
        payload: {
          data: { ...data, keyframes: nextKeyframes },
          rationale: nextLocked
            ? `Lock keyframe ${keyframeId} from scene workspace`
            : `Unlock keyframe ${keyframeId} from scene workspace`,
        },
      })
      toast.success(nextLocked ? 'Keyframe locked' : 'Keyframe unlocked')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update keyframe lock')
    }
  }

  if (grouped.size === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-sm text-muted-foreground">
          This keyframe artifact does not contain any frames yet.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <CardTitle>Keyframes</CardTitle>
              <CardDescription>
                Start, mid, and end frames that can be locked as downstream render constraints.
              </CardDescription>
            </div>
            <Badge variant="outline">
              {keyframes.length} {keyframes.length === 1 ? 'frame' : 'frames'}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {Array.from(grouped.entries()).map(([shotId, shotKeyframes]) => (
        <Card key={shotId} className="gap-0">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{shotId}</CardTitle>
            <CardDescription>
              {[shotKeyframes[0]?.shotSize, shotKeyframes[0]?.cameraAngle, shotKeyframes[0]?.cameraMovement]
                .filter(Boolean)
                .join(' • ') || 'Shot metadata unavailable'}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {shotKeyframes.map(keyframe => {
              const imageUrl = keyframe.imagePath ? getAssetFileUrl(projectId, keyframe.imagePath) : null
              return (
                <div key={keyframe.keyframeId} className="rounded-xl border border-border bg-card/60 p-3">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">{keyframe.position ?? 'frame'}</Badge>
                    {keyframe.timestampSeconds !== null && (
                      <Badge variant="outline">{formatSeconds(keyframe.timestampSeconds)}</Badge>
                    )}
                    {keyframe.sourceKind && <Badge variant="outline">{keyframe.sourceKind}</Badge>}
                    {keyframe.isLocked && (
                      <Badge variant="default" className="gap-1">
                        <Lock className="h-3 w-3" />
                        Locked
                      </Badge>
                    )}
                  </div>

                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={`${shotId} ${keyframe.position ?? 'keyframe'}`}
                      className="aspect-video w-full rounded-lg border border-border object-cover"
                    />
                  ) : (
                    <div className="flex aspect-video items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
                      <ImageIcon className="mr-2 h-4 w-4" />
                      Missing image
                    </div>
                  )}

                  {editable && entityId && (
                    <Button
                      variant={keyframe.isLocked ? 'outline' : 'default'}
                      size="sm"
                      className="mt-3 w-full"
                      onClick={() => handleToggleLock(keyframe.keyframeId, !keyframe.isLocked)}
                      disabled={editArtifact.isPending}
                    >
                      {keyframe.isLocked ? (
                        <>
                          <Unlock className="h-3.5 w-3.5" />
                          Unlock
                        </>
                      ) : (
                        <>
                          <Lock className="h-3.5 w-3.5" />
                          Lock
                        </>
                      )}
                    </Button>
                  )}
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
