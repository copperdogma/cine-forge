import { Link } from 'react-router-dom'
import { Clapperboard, ExternalLink, Film, Loader2, RefreshCw, TriangleAlert, Wand2 } from 'lucide-react'
import { toast } from 'sonner'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { AnimaticViewer } from '@/components/AnimaticViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { formatConsistencyStrategy, formatLatencyMs } from '@/components/preview-provenance'
import { formatDuration, formatMoney } from '@/components/render-utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  isRunActive,
  useArtifact,
  usePrevizAdoptionStatus,
  useProjectInputs,
  useRunState,
  useStartRun,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary, PrevizLaneStatus } from '@/lib/types'

type PrevizPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  storyboardGroup?: ArtifactGroupSummary
  animaticGroup?: ArtifactGroupSummary
  keyframeGroup?: ArtifactGroupSummary
  previzGroup?: ArtifactGroupSummary
  aiPrevizGroup?: ArtifactGroupSummary
  aiPrevizPromptGroup?: ArtifactGroupSummary
}

function formatAdoptionState(value: PrevizLaneStatus['adoption_state'] | null | undefined): string {
  switch (value) {
    case 'default':
      return 'Default'
    case 'recommended_optional':
      return 'Recommended Optional'
    case 'experimental_manual':
      return 'Experimental / Manual'
    default:
      return 'Manual Lane'
  }
}

function defaultLaneLabel(defaultLane: 'annotated_animatic' | 'ai_previz' | undefined): string {
  return defaultLane === 'ai_previz' ? 'AI Previz' : 'Annotated Animatic'
}

function previzDescription(
  defaultLane: 'annotated_animatic' | 'ai_previz' | undefined,
  aiPreviz: PrevizLaneStatus | null | undefined,
): string {
  const base =
    'Previz is for camera placement, blocking, motion, pacing, and location readability.'
  if (!aiPreviz) {
    return `${base} Annotated animatic remains the current default while AI previz stays a separate low-fidelity lane. Final footage still lives in the Render tab.`
  }
  if (defaultLane === 'ai_previz') {
    return `${base} AI previz currently clears the adoption gate and is the default lane. Annotated animatic remains available as a deterministic fallback. Final footage still lives in the Render tab.`
  }
  if (aiPreviz.adoption_state === 'recommended_optional') {
    return `${base} Annotated animatic stays the default, but AI previz is now a recommended optional lane for fast motion and staging review. Final footage still lives in the Render tab.`
  }
  return `${base} Annotated animatic remains the default while AI previz stays manual until the remaining blockers clear. Final footage still lives in the Render tab.`
}

function aiPrevizCostBadge(status: PrevizLaneStatus | null | undefined): string | null {
  if (!status) return null
  const amount = formatMoney(status.cost.estimated_cost_usd ?? null)
  if (status.cost.status === 'verified' && amount) return amount
  if (status.cost.status === 'estimated' && amount) return `Est. ${amount}`
  if (status.cost.status === 'blocked') return 'Cost blocked'
  return null
}

export function PrevizPanel({
  projectId,
  sceneId,
  shotPlanGroup,
  storyboardGroup,
  animaticGroup,
  keyframeGroup,
  previzGroup,
  aiPrevizGroup,
  aiPrevizPromptGroup,
}: PrevizPanelProps) {
  const { data: animaticArtifact, isLoading: animaticLoading } = useArtifact(
    projectId,
    'animatic',
    sceneId,
    animaticGroup?.latest_version,
  )
  const { data: aiPrevizArtifact, isLoading: aiPrevizLoading } = useArtifact(
    projectId,
    'ai_previz_video',
    sceneId,
    aiPrevizGroup?.latest_version,
  )
  const { data: previzStatus } = usePrevizAdoptionStatus(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const startRun = useStartRun()
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const deterministicRunActive = hasActiveRun && runState?.state.recipe_id === 'animatics_generation'
  const aiPrevizRunActive = hasActiveRun && runState?.state.recipe_id === 'ai_previz_generation'
  const anotherRunActive =
    hasActiveRun
    && !!runState
    && !['animatics_generation', 'ai_previz_generation'].includes(runState.state.recipe_id)
  const canStart = !!latestInputPath && !!shotPlanGroup && !hasActiveRun

  const animaticData = animaticArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizData = aiPrevizArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizStatus = previzStatus?.ai_previz
  const aiPrevizCostLabel = aiPrevizCostBadge(aiPrevizStatus)
  const aiPrevizExtraBlockers = (aiPrevizStatus?.blocker_reasons ?? [])
    .filter(blocker => blocker !== aiPrevizStatus?.reason)
    .slice(0, 2)
  const animaticDetailHref = animaticGroup
    ? `/${projectId}/artifacts/animatic/${sceneId}/${animaticGroup.latest_version}`
    : null
  const keyframeDetailHref = keyframeGroup
    ? `/${projectId}/artifacts/keyframe/${sceneId}/${keyframeGroup.latest_version}`
    : null
  const previzDetailHref = previzGroup
    ? `/${projectId}/artifacts/previz_reel/${previzGroup.entity_id ?? 'project'}/${previzGroup.latest_version}`
    : null
  const aiPrevizDetailHref = aiPrevizGroup
    ? `/${projectId}/artifacts/ai_previz_video/${sceneId}/${aiPrevizGroup.latest_version}`
    : null
  const aiPrevizPromptHref = aiPrevizPromptGroup
    ? `/${projectId}/artifacts/ai_previz_prompt/${sceneId}/${aiPrevizPromptGroup.latest_version}`
    : null
  const validationRef = aiPrevizGroup?.health_details?.source_kind === 'media_validation'
    ? aiPrevizGroup.health_details.source_artifact_ref
    : null
  const { data: validationArtifact, isLoading: validationLoading } = useArtifact(
    projectId,
    validationRef?.artifact_type,
    validationRef?.entity_id ?? undefined,
    validationRef?.version,
  )
  const validationData = validationArtifact?.payload?.data as Record<string, unknown> | undefined
  const validationDetailHref = validationRef?.entity_id && validationRef.version
    ? `/${projectId}/artifacts/${validationRef.artifact_type}/${validationRef.entity_id}/${validationRef.version}`
    : null

  async function handleStartDeterministicPreviz() {
    if (!latestInputPath || !shotPlanGroup) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'animatics_generation',
        accept_config: true,
        force: !!animaticGroup || !!keyframeGroup,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        animaticGroup || keyframeGroup
          ? 'Refreshing deterministic previz for all scenes'
          : 'Started deterministic previz for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start deterministic previz')
    }
  }

  async function handleStartAiPreviz() {
    if (!latestInputPath || !shotPlanGroup) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'ai_previz_generation',
        accept_config: true,
        force: !!aiPrevizGroup || !!aiPrevizPromptGroup,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        aiPrevizGroup || aiPrevizPromptGroup
          ? 'Refreshing AI previz for all scenes'
          : 'Started AI previz for all scenes',
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start AI previz')
    }
  }

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Previz</CardTitle>
                <Badge variant="outline">Runs for all scenes</Badge>
                <Badge variant="secondary">
                  Default: {defaultLaneLabel(previzStatus?.default_lane)}
                </Badge>
                {aiPrevizStatus && (
                  <Badge
                    variant={aiPrevizStatus.adoption_state === 'experimental_manual' ? 'outline' : 'secondary'}
                  >
                    AI lane: {formatAdoptionState(aiPrevizStatus.adoption_state)}
                  </Badge>
                )}
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                {previzDescription(previzStatus?.default_lane, aiPrevizStatus)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {!shotPlanGroup && (
            <p>
              Previz depends on shot plans. Open the <span className="font-medium">Shots</span>{' '}
              tab first and generate coverage for this scene before running previz.
            </p>
          )}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              deterministic or AI previz.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="gap-0">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-lg">Annotated Animatic</CardTitle>
                <Badge variant="secondary">
                  {previzStatus?.default_lane === 'annotated_animatic' ? 'Default' : 'Deterministic fallback'}
                </Badge>
                {storyboardGroup && <Badge variant="outline">Storyboard-informed</Badge>}
                {animaticGroup && <Badge variant="outline">v{animaticGroup.latest_version}</Badge>}
                {keyframeGroup && <Badge variant="outline">Keyframes ready</Badge>}
              </div>
              <CardDescription>
                Deterministic previz with on-screen camera and blocking guidance. This is the
                current baseline and the default operator path.
              </CardDescription>
              <div className="flex flex-wrap gap-2">
                {animaticDetailHref && (
                  <Button asChild variant="outline" size="sm">
                    <Link to={animaticDetailHref}>
                      <ExternalLink className="h-3.5 w-3.5" />
                      Animatic Detail
                    </Link>
                  </Button>
                )}
                {keyframeDetailHref && (
                  <Button asChild variant="outline" size="sm">
                    <Link to={keyframeDetailHref}>
                      <ExternalLink className="h-3.5 w-3.5" />
                      Keyframe Detail
                    </Link>
                  </Button>
                )}
                {previzDetailHref && (
                  <Button asChild variant="outline" size="sm">
                    <Link to={previzDetailHref}>
                      <Film className="h-3.5 w-3.5" />
                      Previz Reel
                    </Link>
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={handleStartDeterministicPreviz}
                  disabled={!canStart || startRun.isPending}
                >
                  {startRun.isPending && deterministicRunActive ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : animaticGroup || keyframeGroup ? (
                    <RefreshCw className="h-3.5 w-3.5" />
                  ) : (
                    <Clapperboard className="h-3.5 w-3.5" />
                  )}
                  {animaticGroup || keyframeGroup
                    ? 'Refresh Deterministic Previz'
                    : 'Run Deterministic Previz'}
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card className="gap-0 border-sky-500/30">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-lg">AI Previz</CardTitle>
                {aiPrevizStatus && (
                  <Badge
                    variant={aiPrevizStatus.adoption_state === 'experimental_manual' ? 'outline' : 'secondary'}
                  >
                    {formatAdoptionState(aiPrevizStatus.adoption_state)}
                  </Badge>
                )}
                {aiPrevizStatus?.candidate_label && (
                  <Badge variant="outline">{aiPrevizStatus.candidate_label}</Badge>
                )}
                {aiPrevizCostLabel && (
                  <Badge variant="outline">{aiPrevizCostLabel}</Badge>
                )}
                {aiPrevizStatus?.latency_ms && (
                  <Badge variant="outline">Avg {formatLatencyMs(aiPrevizStatus.latency_ms)}</Badge>
                )}
                {aiPrevizGroup && (
                  <>
                    <Badge variant="outline">v{aiPrevizGroup.latest_version}</Badge>
                    <HealthBadge
                      health={aiPrevizGroup.health}
                      details={aiPrevizGroup.health_details}
                    />
                  </>
                )}
              </div>
              <CardDescription>
                {aiPrevizStatus?.reason
                  ?? 'Low-fidelity AI video for planning review, separate from the final render path.'}
              </CardDescription>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
                <div className="flex items-start gap-2">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                  <div className="space-y-1">
                    <p>
                      Preflight:{' '}
                      {aiPrevizStatus?.engine_pack_id ?? 'ai_previz_generation'} /{' '}
                      {aiPrevizStatus?.target_model ?? 'configured model'}
                    </p>
                    <p>
                      {aiPrevizStatus?.resolution ?? 'Configured resolution'},{' '}
                      {formatDuration(aiPrevizStatus?.duration_seconds ?? null) ?? 'configured duration'},{' '}
                      {formatConsistencyStrategy(aiPrevizStatus?.consistency_strategy ?? null)
                        ?? 'configured consistency'}.
                    </p>
                    <p>
                      {aiPrevizStatus?.reason
                        ?? 'Keep AI previz blocking-first, low-detail, and explicitly non-final.'}
                    </p>
                    {aiPrevizStatus?.validation_stage_enabled === false && (
                      <p>Validation artifacts are not currently wired for this lane.</p>
                    )}
                    {aiPrevizStatus?.cost.status === 'estimated' && (
                      <p>
                        Estimated cost for the active recipe defaults:{' '}
                        {formatMoney(aiPrevizStatus.cost.estimated_cost_usd ?? null) ?? 'n/a'}.
                      </p>
                    )}
                    {aiPrevizStatus?.cost.status === 'blocked' && aiPrevizStatus.cost.reason && (
                      <p>Cost blocker: {aiPrevizStatus.cost.reason}</p>
                    )}
                    {aiPrevizStatus?.cost.status === 'verified' && (
                      <p>Current cost status: provider-backed runtime cost is available.</p>
                    )}
                    {aiPrevizExtraBlockers.length > 0 && (
                      <ul className="list-disc space-y-1 pl-5">
                        {aiPrevizExtraBlockers.map(blocker => (
                          <li key={blocker}>{blocker}</li>
                        ))}
                      </ul>
                    )}
                    <p>
                      Final footage still belongs in the Render tab. Keep this lane focused on
                      motion, staging, and operator-readable planning feedback.
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {aiPrevizDetailHref && (
                  <Button asChild variant="outline" size="sm">
                    <Link to={aiPrevizDetailHref}>
                      <ExternalLink className="h-3.5 w-3.5" />
                      AI Previz Detail
                    </Link>
                  </Button>
                )}
                {aiPrevizPromptHref && (
                  <Button asChild variant="outline" size="sm">
                    <Link to={aiPrevizPromptHref}>
                      <ExternalLink className="h-3.5 w-3.5" />
                      Prompt Detail
                    </Link>
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="default"
                  onClick={handleStartAiPreviz}
                  disabled={!canStart || startRun.isPending}
                >
                  {startRun.isPending && aiPrevizRunActive ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : aiPrevizGroup || aiPrevizPromptGroup ? (
                    <RefreshCw className="h-3.5 w-3.5" />
                  ) : (
                    <Wand2 className="h-3.5 w-3.5" />
                  )}
                  {aiPrevizGroup || aiPrevizPromptGroup
                    ? 'Refresh AI Previz'
                    : 'Generate AI Previz'}
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {(deterministicRunActive || aiPrevizRunActive) && (
        <Card className="gap-0 border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium">
                {deterministicRunActive
                  ? 'Refreshing deterministic previz for all scenes'
                  : 'Refreshing AI previz for all scenes'}
              </p>
              <p className="text-sm text-muted-foreground">
                You can keep reviewing the current previz while CineForge rebuilds the latest
                version in the background.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!animaticData && !aiPrevizData && !animaticLoading && !aiPrevizLoading && !!shotPlanGroup && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center">
          <div className="mx-auto flex max-w-2xl flex-col items-center gap-4">
            <div className="rounded-full bg-muted p-3">
              <Film className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">No previz for this scene yet</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Start with deterministic previz for the default blocking read, then use AI previz
                when you want an experimental motion pass in the shared low-fidelity house style.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              <Button onClick={handleStartDeterministicPreviz} disabled={!canStart || startRun.isPending}>
                <Clapperboard className="h-4 w-4" />
                Run Deterministic Previz
              </Button>
              <Button variant="outline" onClick={handleStartAiPreviz} disabled={!canStart || startRun.isPending}>
                <Wand2 className="h-4 w-4" />
                Generate AI Previz
              </Button>
            </div>
          </div>
        </div>
      )}

      {animaticLoading && animaticGroup && !animaticData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}
      {aiPrevizLoading && aiPrevizGroup && !aiPrevizData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}
      {validationLoading && validationRef && !validationArtifact && (
        <div className="h-36 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {animaticData && <AnimaticViewer data={animaticData} projectId={projectId} />}
      {validationData && (
        <MediaValidationViewer
          data={validationData}
          projectId={projectId}
          compact
          detailHref={validationDetailHref}
        />
      )}
      {aiPrevizData && <AiPrevizViewer data={aiPrevizData} projectId={projectId} />}
    </div>
  )
}
