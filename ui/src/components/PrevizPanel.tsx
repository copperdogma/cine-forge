import { Link } from 'react-router-dom'
import { Clapperboard, ExternalLink, Film, Loader2, RefreshCw, TriangleAlert, Wand2 } from 'lucide-react'
import { toast } from 'sonner'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { AnimaticViewer } from '@/components/AnimaticViewer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { isRunActive, useArtifact, useProjectInputs, useRunState, useStartRun } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary } from '@/lib/types'

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

const AI_PREVIZ_CONFIG = {
  enginePackLabel: 'google_veo31_lite',
  modelLabel: 'veo-3.1-lite-generate-preview',
  resolution: '1280x720',
  duration: '8s',
  consistency: 'Prompt-only consistency',
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
                <Badge variant="secondary">Default: Annotated Animatic</Badge>
                <Badge variant="secondary">AI lane: experimental</Badge>
                {shotPlanGroup && (
                  <Badge variant="secondary">From shot plan v{shotPlanGroup.latest_version}</Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                Previz is for camera placement, blocking, motion, pacing, and location readability.
                The deterministic annotated animatic remains the default because it is the most
                trustworthy lane today. AI previz is available here as an explicit experimental
                lane, not as a disguised final render. Final footage still lives in the separate
                <span className="font-medium"> Render</span> tab for {sceneHeading}.
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
                <Badge variant="secondary">Default</Badge>
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
                <Badge variant="secondary">Experimental</Badge>
                <Badge variant="outline">Best quality candidate: Veo Lite</Badge>
                <Badge variant="outline">Cost unverified</Badge>
                {aiPrevizGroup && <Badge variant="outline">v{aiPrevizGroup.latest_version}</Badge>}
              </div>
              <CardDescription>
                Low-fidelity AI video for planning review. This lane is manual on purpose: it gives
                you motion and staging feedback without changing the default previz path.
              </CardDescription>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
                <div className="flex items-start gap-2">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                  <div className="space-y-1">
                    <p>
                      Preflight: {AI_PREVIZ_CONFIG.enginePackLabel} / {AI_PREVIZ_CONFIG.modelLabel}
                    </p>
                    <p>
                      {AI_PREVIZ_CONFIG.resolution}, {AI_PREVIZ_CONFIG.duration},{' '}
                      {AI_PREVIZ_CONFIG.consistency}. Keep it blocking-first and non-final.
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

      {animaticData && <AnimaticViewer data={animaticData} projectId={projectId} />}
      {aiPrevizData && <AiPrevizViewer data={aiPrevizData} projectId={projectId} />}
    </div>
  )
}
