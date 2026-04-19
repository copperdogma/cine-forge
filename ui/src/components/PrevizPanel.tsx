import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ExternalLink, Loader2, RefreshCw, Wand2 } from 'lucide-react'
import { toast } from 'sonner'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { HealthBadge } from '@/components/HealthBadge'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import {
  aiPrevizCostBadge,
  formatAdoptionState,
  previzDescription,
} from '@/components/previz-panel-support'
import { SceneActionControls } from '@/components/SceneActionControls'
import { formatConsistencyStrategy, formatLatencyMs } from '@/components/preview-provenance'
import { formatDuration, formatToken } from '@/components/render-utils'
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
import { mediaValidationStatus } from '@/lib/health'
import {
  buildSceneScope,
  getSceneScopeLabel,
  getSceneScopeTargetLabel,
} from '@/lib/constants'
import type {
  ArtifactGroupSummary,
  SceneScopeMode,
} from '@/lib/types'

type PrevizPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  aiPrevizGroup?: ArtifactGroupSummary
  aiPrevizPromptGroup?: ArtifactGroupSummary
}

export function PrevizPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  aiPrevizGroup,
  aiPrevizPromptGroup,
}: PrevizPanelProps) {
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
  const { data: aiPreflight } = useSceneActionPreflight(projectId, {
    recipe_id: 'ai_previz_generation',
    scene_scope: sceneScope,
  })

  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const hasActiveRun = isRunActive(activeRunId, runState)
  const aiPrevizRunActive = hasActiveRun && runState?.state.recipe_id === 'ai_previz_generation'
  const anotherRunActive = hasActiveRun
    && !!runState
    && runState.state.recipe_id !== 'ai_previz_generation'
  const runBlocked = startRun.isPending || hasActiveRun
  const canStartAiPreviz = !!latestInputPath
    && !runBlocked
    && aiPreflight?.status !== 'soft_block'

  const aiPrevizData = aiPrevizArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizStatus = previzStatus?.ai_previz
  const aiPrevizCostLabel = aiPrevizCostBadge(aiPrevizStatus)
  const aiPrevizStartFrom = aiPreflight?.start_from ?? undefined
  const aiPrevizReusesShotPlan = aiPrevizStartFrom === 'ai_previz'
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)

  const aiPrevizDetailHref = aiPrevizGroup
    ? `/${projectId}/artifacts/ai_previz_video/${sceneId}/${aiPrevizGroup.latest_version}`
    : null
  const aiPrevizPromptHref = aiPrevizPromptGroup
    ? `/${projectId}/artifacts/ai_previz_prompt/${sceneId}/${aiPrevizPromptGroup.latest_version}`
    : null
  const validationRef = (
    aiPrevizGroup?.health_details?.source_kind === 'media_validation'
    || aiPrevizGroup?.health_details?.source_kind === 'media_validation_stale'
  )
    ? aiPrevizGroup.health_details.source_artifact_ref
    : null
  const validationStatus = mediaValidationStatus(
    aiPrevizGroup?.health,
    aiPrevizGroup?.health_details,
  )
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
                <Badge variant="secondary">Shipped lane: {aiPrevizStatus?.label ?? 'AI Previz'}</Badge>
                {aiPrevizStatus && (
                  <Badge
                    variant={aiPrevizStatus.blocker_reasons.length > 0 ? 'outline' : 'secondary'}
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
              AI previz.
            </p>
          )}
          {aiPrevizRunActive && (
            <p>AI previz is currently running for {activeRunScopeLabel.toLowerCase()}.</p>
          )}
          <SceneActionControls
            scope={scope}
            onScopeChange={setScope}
            preflight={aiPreflight}
            disabled={runBlocked}
          />
        </CardContent>
      </Card>

      <Card className="gap-0 border-sky-500/30">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-lg">{aiPrevizStatus?.label ?? 'AI Previz'}</CardTitle>
              <Badge variant="secondary">Only shipped previz lane</Badge>
              {aiPrevizStatus && (
                <Badge
                  variant={aiPrevizStatus.blocker_reasons.length > 0 ? 'outline' : 'secondary'}
                >
                  {formatAdoptionState(aiPrevizStatus.adoption_state)}
                </Badge>
              )}
              <Badge variant="outline">AI video lane</Badge>
              {aiPrevizStatus?.candidate_label && (
                <Badge variant="outline">{aiPrevizStatus.candidate_label}</Badge>
              )}
              {aiPrevizCostLabel && <Badge variant="outline">{aiPrevizCostLabel}</Badge>}
              {aiPrevizStatus?.latency_ms && (
                <Badge variant="outline">Avg {formatLatencyMs(aiPrevizStatus.latency_ms)}</Badge>
              )}
              {aiPrevizStatus?.latency_budget_ms && (
                <Badge variant="outline">Target ≤ {formatLatencyMs(aiPrevizStatus.latency_budget_ms)}</Badge>
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
                ?? 'Provider-generated low-fidelity AI video for planning review, distinct from final render output.'}
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
              {aiPreflight?.prerequisite_strategy && (
                <p>
                  Prep strategy: {aiPreflight.prerequisite_strategy === 'reuse_existing_shot_plan'
                    ? 'Reuse current shot plan'
                    : 'One-pass previz prep'}.
                </p>
              )}
              {aiPrevizReusesShotPlan && (
                <p>
                  Reuse path: CineForge will keep the current shot plan and rerun only AI video
                  generation plus media validation.
                </p>
              )}
              {(aiPreflight?.reused_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Reused:{' '}
                  {aiPreflight?.reused_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
              {(aiPreflight?.auto_build_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Auto-built:{' '}
                  {aiPreflight?.auto_build_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
              {(aiPreflight?.missing_optional_artifact_types?.length ?? 0) > 0 && (
                <p>
                  Missing optional context:{' '}
                  {aiPreflight?.missing_optional_artifact_types
                    ?.map(token => formatToken(token) ?? token)
                    .join(', ')}.
                </p>
              )}
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
              {validationStatus?.label === 'Validation Pending'
                ? `Latest AI previz clip is playable for ${sceneHeading}. Validation is still pending.`
                : validationStatus?.label === 'Validation Failed'
                  ? `Latest AI previz clip is playable for ${sceneHeading}, but validation flagged it for follow-up.`
                  : `Latest AI previz clip is ready for ${sceneHeading}. The viewer appears below.`}
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

      {aiPrevizLoading && aiPrevizGroup && !aiPrevizData && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}
      {validationLoading && validationRef && !validationArtifact && (
        <div className="h-36 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {aiPrevizData && (
        <AiPrevizViewer
          data={aiPrevizData}
          projectId={projectId}
          health={aiPrevizGroup?.health}
          healthDetails={aiPrevizGroup?.health_details}
        />
      )}
      {validationData && (
        <MediaValidationViewer
          data={validationData}
          projectId={projectId}
          compact
          detailHref={validationDetailHref}
        />
      )}
    </div>
  )
}
