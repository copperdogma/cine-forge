import { useImperativeHandle, useRef } from 'react'
import type { Ref } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { MediaGenerationInspection } from '@/components/MediaGenerationInspection'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useMediaGeneration } from '@/lib/hooks/media-generation'
import type { MediaRecipeId } from '@/lib/media-generation-types'

export type MediaGenerationControlsHandle = { selectClip: (clipId: string) => void }
type Props = {
  projectId: string
  sceneId: string
  recipeId: MediaRecipeId
  ref?: Ref<MediaGenerationControlsHandle>
}

export function MediaGenerationControls({ projectId, sceneId, recipeId, ref }: Props) {
  const controls = useMediaGeneration(projectId, sceneId, recipeId)
  const container = useRef<HTMLDivElement>(null)
  useImperativeHandle(ref, () => ({ selectClip(clipId: string) {
    controls.setSelection([clipId])
    container.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    container.current?.focus({ preventScroll: true })
  } }))
  return (
    <Card ref={container} tabIndex={-1} className="gap-0 scroll-mt-4" aria-label="Prepare, inspect and confirm video generation">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Prepare, inspect, then generate</CardTitle>
        <CardDescription>
          Prepare this scene’s clip plan, inspect the actual work and video estimate, then confirm the clips to generate.
          Review and confirm one scene at a time.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {controls.generationPreflight.data?.status === 'soft_block' && <div className="space-y-1 rounded-lg border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-200">
          <p className="font-medium">Video generation is currently blocked</p>
          <p>{controls.generationPreflight.data.summary}</p>
          {controls.generationPreflight.data.items.filter(item => item.kind === 'soft_block').map((item, index) => <p key={index}>{item.label}: {item.detail}</p>)}
          <p>You can prepare and inspect clips when preparation prerequisites allow it; this does not clear the video blocker.</p>
        </div>}
        {controls.generationPreflight.isPending && <p className="text-sm text-muted-foreground">Checking video generation availability…</p>}
        {controls.generationPreflight.error && <p role="alert" className="text-sm text-destructive">Video availability check failed: {controls.generationPreflight.error.message}</p>}
        <div className="space-y-2">
          <Button variant="outline" onClick={() => void controls.prepare()} disabled={!controls.canPrepare}>
            {controls.preparing && <Loader2 className="h-4 w-4 animate-spin" />}
            {controls.preparing ? 'Preparing clip plan…' : controls.reusesExistingPlan ? 'Inspect existing clip plan' : 'Prepare clip plan'}
          </Button>
          <p className="text-sm text-muted-foreground">Preparation may use paid text AI. It stops before video generation.</p>
          {controls.preflight.isPending && <p className="text-sm text-muted-foreground">Checking preparation prerequisites…</p>}
          {controls.preflight.error && <p role="alert" className="text-sm text-destructive">{controls.preflight.error.message}</p>}
          {controls.preflight.data && <p className="text-sm text-muted-foreground">
            {controls.preflight.data.status === 'soft_block'
              ? 'Clip preparation is blocked. Resolve the prerequisites below.'
              : 'Clip preparation is ready. Video generation requires separate inspection and confirmation.'}
          </p>}
          {controls.preflight.data?.items.filter(item => item.kind === 'soft_block').map((item, index) => (
            <p key={`blocker-${index}`} className="text-sm text-amber-200">{item.label}: {item.detail}</p>
          ))}
          {controls.preflight.data?.items.some(item => item.kind !== 'soft_block') && <details className="group">
            <summary className="cursor-pointer rounded-md border border-border bg-muted/30 p-2.5 text-sm font-medium transition-colors hover:bg-muted/50">
              Preparation prerequisites and optional context
            </summary>
            <div className="space-y-2 px-3 pt-2">
              {controls.preflight.data.items.filter(item => item.kind !== 'soft_block').map((item, index) => (
                <p key={`${item.kind}-${index}`} className="text-sm text-muted-foreground">{item.label}: {item.detail}</p>
              ))}
            </div>
          </details>}
          {(controls.preparationPaused || controls.preparationIncomplete) && <div className="space-y-2 text-sm text-amber-200" role="status">
            <p>{controls.preparationPaused
              ? 'Clip preparation is paused. Review the run and use Resume when ready.'
              : 'Clip preparation stopped before the selected work completed. Review the run before continuing.'}</p>
            {controls.preparationRunId && <Button asChild variant="outline" size="sm">
              <Link to={`/${projectId}/runs/${controls.preparationRunId}`}>{controls.preparationPaused ? 'Open run to resume' : 'Open preparation run'}</Link>
            </Button>}
          </div>}
          {controls.preparationFailed && <p role="alert" className="text-sm text-destructive">Preparation failed. Inspect any saved work and the run details before trying again.</p>}
        </div>
        <MediaGenerationInspection review={controls.review} catalog={controls.catalog} selection={controls.selection}
          onSelectionChange={controls.setSelection} disabled={controls.busy} stale={controls.stale} />
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <Button variant="outline" onClick={controls.inspect} disabled={!controls.canInspect}>
            {controls.inspecting && <Loader2 className="h-4 w-4 animate-spin" />}
            Inspect {controls.selection === null ? 'all current' : 'selected'} clips
          </Button>
          <Button onClick={() => void controls.confirm()} disabled={!controls.canConfirm}>
            {controls.confirming && <Loader2 className="h-4 w-4 animate-spin" />}
            Confirm and generate {controls.selection?.length ?? controls.review?.plan.units.length ?? 0} clip{(controls.selection?.length ?? controls.review?.plan.units.length ?? 0) === 1 ? '' : 's'}
          </Button>
        </div>
        {controls.error && <p role="alert" className="text-sm text-destructive">{controls.error.message}</p>}
        {!controls.review && <p className="text-sm text-muted-foreground">Inspect the prepared clip plan before video generation. Saved clips below remain available to review.</p>}
      </CardContent>
    </Card>
  )
}
