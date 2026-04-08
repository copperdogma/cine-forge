import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Clapperboard, ExternalLink, Film, Loader2, RefreshCw, Wand2 } from 'lucide-react'
import { toast } from 'sonner'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { AnimaticViewer } from '@/components/AnimaticViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import { SceneActionControls } from '@/components/SceneActionControls'
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
  useSceneActionPreflight,
  useStartRun,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import {
  buildSceneScope,
  getSceneScopeLabel,
  getSceneScopeTargetLabel,
} from '@/lib/constants'
import type {
  ArtifactGroupSummary,
  PrevizAdoptionStatus,
  PrevizLaneStatus,
  SceneActionPreflight,
  SceneActionPreflightItem,
  SceneScopeMode,
} from '@/lib/types'

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

function defaultLaneLabel(status: PrevizAdoptionStatus | null | undefined): string {
  if (!status) return 'Fast Previz'
  return status.default_lane === 'ai_previz'
    ? status.ai_previz.label
    : status.fast_previz.label
}

function previzDescription(status: PrevizAdoptionStatus | null | undefined): string {
  const base =
    'Previz is for camera placement, blocking, motion, pacing, and location readability.'
  if (!status) {
    return `${base} Fast Previz remains the quick default while AI Previz stays a separate slower low-fidelity lane. Final footage still lives in the Render tab.`
  }
  return `${base} ${status.policy_summary} Final footage still lives in the Render tab.`
}

function aiPrevizCostBadge(status: PrevizLaneStatus | null | undefined): string | null {
  if (!status) return null
  const amount = formatMoney(status.cost.estimated_cost_usd ?? null)
  if (status.cost.status === 'verified' && amount) return amount
  if (status.cost.status === 'estimated' && amount) return `Est. ${amount}`
  if (status.cost.status === 'blocked') return 'Cost blocked'
  return null
}

function mergePrevizPreflight(
  sceneScope: ReturnType<typeof buildSceneScope>,
  preflights: Array<SceneActionPreflight | null | undefined>,
): SceneActionPreflight | null {
  const available = preflights.filter((item): item is SceneActionPreflight => !!item)
  if (available.length === 0) return null

  const deduped = new Map<string, SceneActionPreflightItem>()
  for (const preflight of available) {
    for (const item of preflight.items) {
      const key = `${item.kind}:${item.label}:${item.detail}`
      if (!deduped.has(key)) {
        deduped.set(key, item)
      }
    }
  }

  const items = [...deduped.values()]
  const allSoftBlocked = available.every((item) => item.status === 'soft_block')
  const status = allSoftBlocked ? 'soft_block' : items.length > 0 ? 'warn' : 'ready'
  const scopeTarget = getSceneScopeTargetLabel(sceneScope)
  const summary = status === 'soft_block'
    ? `Previz can't run for ${scopeTarget} yet.`
    : status === 'warn'
      ? `Previz can run for ${scopeTarget} with warnings.`
      : `Previz is ready for ${scopeTarget}.`

  return {
    recipe_id: 'previz',
    recipe_name: 'Previz',
    scene_scope: sceneScope,
    status,
    summary,
    items,
  }
}

export function PrevizPanel({
  projectId,
  sceneId,
  sceneHeading,
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
  const [scope, setScope] = useState<SceneScopeMode>('current_scene')
  const sceneScope = buildSceneScope(scope, sceneId)
  const { data: deterministicPreflight } = useSceneActionPreflight(projectId, {
    recipe_id: 'animatics_generation',
    scene_scope: sceneScope,
  })
  const { data: aiPreflight } = useSceneActionPreflight(projectId, {
    recipe_id: 'ai_previz_generation',
    scene_scope: sceneScope,
  })

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const deterministicRunActive = hasActiveRun && runState?.state.recipe_id === 'animatics_generation'
  const aiPrevizRunActive = hasActiveRun && runState?.state.recipe_id === 'ai_previz_generation'
  const anotherRunActive = hasActiveRun
    && !!runState
    && !['animatics_generation', 'ai_previz_generation'].includes(runState.state.recipe_id)
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartDeterministic = !!latestInputPath
    && !runBlocked
    && deterministicPreflight?.status !== 'soft_block'
  const canStartAiPreviz = !!latestInputPath
    && !runBlocked
    && aiPreflight?.status !== 'soft_block'

  const animaticData = animaticArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizData = aiPrevizArtifact?.payload?.data as Record<string, unknown> | undefined
  const fastPrevizStatus = previzStatus?.fast_previz
  const aiPrevizStatus = previzStatus?.ai_previz
  const aiPrevizCostLabel = aiPrevizCostBadge(aiPrevizStatus)
  const aiPrevizStartFrom = aiPreflight?.start_from ?? undefined
  const aiPrevizReusesShotPlan = aiPrevizStartFrom === 'ai_previz'
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)
  const sharedPrevizPreflight = useMemo(
    () => mergePrevizPreflight(sceneScope, [deterministicPreflight, aiPreflight]),
    [aiPreflight, deterministicPreflight, sceneScope],
  )

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
    if (!latestInputPath) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'animatics_generation',
        accept_config: true,
        force: !!animaticGroup || !!keyframeGroup,
        scene_scope: sceneScope,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        animaticGroup || keyframeGroup
          ? `Refreshing fast previz for ${configuredScopeLabel.toLowerCase()}`
          : `Started fast previz for ${configuredScopeLabel.toLowerCase()}`,
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start fast previz')
    }
  }

  async function handleStartAiPreviz() {
    if (!latestInputPath) return
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'gpt-5.4-mini',
        recipe_id: 'ai_previz_generation',
        accept_config: true,
        force: !!aiPrevizGroup || !!aiPrevizPromptGroup,
        start_from: aiPrevizStartFrom,
        scene_scope: sceneScope,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      toast.success(
        aiPrevizGroup || aiPrevizPromptGroup
          ? aiPrevizReusesShotPlan
            ? `Regenerating AI previz from the current shot plan for ${configuredScopeLabel.toLowerCase()}`
            : `Refreshing AI previz for ${configuredScopeLabel.toLowerCase()}`
          : aiPrevizReusesShotPlan
            ? `Started AI previz from the current shot plan for ${configuredScopeLabel.toLowerCase()}`
            : `Started AI previz for ${configuredScopeLabel.toLowerCase()}`,
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
                <Badge variant="outline">Selected: {configuredScopeLabel}</Badge>
                <Badge variant="secondary">
                  Default: {defaultLaneLabel(previzStatus)}
                </Badge>
                {fastPrevizStatus?.candidate_label && (
                  <Badge variant="outline">Fast lane: {fastPrevizStatus.candidate_label}</Badge>
                )}
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
                {previzDescription(previzStatus)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          {!latestInputPath && <p>No screenplay input is available for this project yet.</p>}
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              deterministic or AI previz.
            </p>
          )}
          {(deterministicRunActive || aiPrevizRunActive) && (
            <p>
              {deterministicRunActive
                ? `Fast previz is currently running for ${activeRunScopeLabel.toLowerCase()}.`
                : `AI previz is currently running for ${activeRunScopeLabel.toLowerCase()}.`}
            </p>
          )}
          <SceneActionControls
            scope={scope}
            onScopeChange={setScope}
            preflight={sharedPrevizPreflight}
            disabled={runBlocked}
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="gap-0">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-lg">{fastPrevizStatus?.label ?? 'Fast Previz'}</CardTitle>
                <Badge variant="secondary">
                  {previzStatus?.default_lane === 'annotated_animatic' ? 'Default quick lane' : 'Deterministic fallback'}
                </Badge>
                {fastPrevizStatus?.candidate_label && (
                  <Badge variant="outline">{fastPrevizStatus.candidate_label}</Badge>
                )}
                {fastPrevizStatus?.latency_ms !== null && fastPrevizStatus?.latency_ms !== undefined && (
                  <Badge variant="outline">Measured {formatLatencyMs(fastPrevizStatus.latency_ms)}</Badge>
                )}
                {fastPrevizStatus?.latency_budget_ms && (
                  <Badge variant="outline">Budget ≤ {formatLatencyMs(fastPrevizStatus.latency_budget_ms)}</Badge>
                )}
                {storyboardGroup && <Badge variant="outline">Storyboard-informed</Badge>}
                {animaticGroup && <Badge variant="outline">v{animaticGroup.latest_version}</Badge>}
                {keyframeGroup && <Badge variant="outline">Keyframes ready</Badge>}
              </div>
              <CardDescription>
                {fastPrevizStatus?.fidelity_disclosure
                  ?? 'Deterministic annotated animatic for planning, not final render quality.'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {fastPrevizStatus && (
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-foreground/90">
                <div className="space-y-1">
                  <p>{fastPrevizStatus.reason}</p>
                  <p>{fastPrevizStatus.intended_use}</p>
                  {fastPrevizStatus.upgrade_description && <p>{fastPrevizStatus.upgrade_description}</p>}
                </div>
              </div>
            )}
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
                disabled={!canStartDeterministic}
              >
                {startRun.isPending && deterministicRunActive ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : animaticGroup || keyframeGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Clapperboard className="h-3.5 w-3.5" />
                )}
                {scope === 'current_scene'
                  ? animaticGroup || keyframeGroup
                    ? 'Regenerate Fast Previz for Current Scene'
                    : 'Generate Fast Previz for Current Scene'
                  : animaticGroup || keyframeGroup
                    ? 'Regenerate Fast Previz for All Scenes'
                    : 'Generate Fast Previz for All Scenes'}
              </Button>
            </div>

            {animaticData && (
              <p className="text-sm text-muted-foreground">
                Latest fast previz is ready for {sceneHeading}. The viewer appears below.
              </p>
            )}
            {!animaticData && !deterministicRunActive && !animaticLoading && (
              <div className="rounded-lg border border-dashed border-border bg-card/50 px-5 py-8 text-center">
                <div className="mx-auto flex max-w-md flex-col items-center gap-3">
                  <div className="rounded-full bg-muted p-3">
                    <Clapperboard className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium">No fast previz yet</p>
                    <p className="text-sm text-muted-foreground">
                      Run fast previz for {configuredScopeTarget}. CineForge will build
                      any missing storyboard or shot-planning substrate first when needed.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {!animaticData && deterministicRunActive && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-5 py-6">
                <div className="flex items-start gap-3">
                  <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      Fast previz is running for {activeRunScopeLabel.toLowerCase()}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      This tab will resolve back to {sceneHeading} as soon as the updated fast-previz clip lands.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="gap-0 border-sky-500/30">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-lg">{aiPrevizStatus?.label ?? 'AI Previz'}</CardTitle>
                {previzStatus?.default_lane !== 'ai_previz' && (
                  <Badge variant="secondary">Slower upgrade</Badge>
                )}
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
                {aiPrevizStatus?.fidelity_disclosure
                  ?? 'Low-fidelity AI video for planning review, separate from the final render path.'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {aiPrevizStatus && (
              <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
                <div className="space-y-1">
                  <p>{aiPrevizStatus.reason}</p>
                  <p>{aiPrevizStatus.intended_use}</p>
                </div>
              </div>
            )}
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
              <div className="space-y-1">
                <p>
                  Preflight: {aiPrevizStatus?.engine_pack_id ?? 'ai_previz_generation'} /{' '}
                  {aiPrevizStatus?.target_model ?? 'configured model'}
                </p>
                <p>
                  {aiPrevizStatus?.resolution ?? 'Configured resolution'},{' '}
                  {formatDuration(aiPrevizStatus?.duration_seconds ?? null) ?? 'configured duration'},{' '}
                  {formatConsistencyStrategy(aiPrevizStatus?.consistency_strategy ?? null)
                    ?? 'configured consistency'}.
                </p>
                <p>
                  Final footage still belongs in the Render tab. Keep this lane focused on motion,
                  staging, and operator-readable planning feedback.
                </p>
                {aiPrevizReusesShotPlan && (
                  <p>
                    Reuse path: CineForge will keep the current shot plan and rerun only AI video
                    generation plus media validation.
                  </p>
                )}
                {fastPrevizStatus?.upgrade_description && <p>{fastPrevizStatus.upgrade_description}</p>}
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
              {validationDetailHref && (
                <Button asChild variant="outline" size="sm">
                  <Link to={validationDetailHref}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Validation Detail
                  </Link>
                </Button>
              )}
              <Button
                size="sm"
                variant="default"
                onClick={handleStartAiPreviz}
                disabled={!canStartAiPreviz}
              >
                {startRun.isPending && aiPrevizRunActive ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : aiPrevizGroup || aiPrevizPromptGroup ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Wand2 className="h-3.5 w-3.5" />
                )}
                {scope === 'current_scene'
                  ? aiPrevizGroup || aiPrevizPromptGroup
                    ? 'Regenerate AI Previz for Current Scene'
                    : 'Generate AI Previz for Current Scene'
                  : aiPrevizGroup || aiPrevizPromptGroup
                    ? 'Regenerate AI Previz for All Scenes'
                    : 'Generate AI Previz for All Scenes'}
              </Button>
            </div>

            {aiPrevizData && (
              <p className="text-sm text-muted-foreground">
                Latest AI previz clip is ready for {sceneHeading}. The viewer appears below.
              </p>
            )}
            {!aiPrevizData && !aiPrevizRunActive && !aiPrevizLoading && (
              <div className="rounded-lg border border-dashed border-border bg-card/50 px-5 py-8 text-center">
                <div className="mx-auto flex max-w-md flex-col items-center gap-3">
                  <div className="rounded-full bg-muted p-3">
                    <Wand2 className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium">No AI previz yet</p>
                    <p className="text-sm text-muted-foreground">
                      {aiPrevizReusesShotPlan
                        ? `Generate an AI motion pass for ${configuredScopeTarget} from the current shot plan. CineForge keeps this lane intentionally low-fidelity and explicitly non-final.`
                        : `Generate an AI motion pass for ${configuredScopeTarget}. CineForge keeps this lane intentionally low-fidelity and explicitly non-final.`}
                    </p>
                  </div>
                </div>
              </div>
            )}
            {!aiPrevizData && aiPrevizRunActive && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-5 py-6">
                <div className="flex items-start gap-3">
                  <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-amber-400" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      AI previz is running for {activeRunScopeLabel.toLowerCase()}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      This tab will resolve back to {sceneHeading} as soon as the updated clip lands.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
