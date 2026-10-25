import { PrevizClipCard, MissingPrevizClipCard } from '@/components/PrevizClipCards'
import { useRef } from 'react'
import { MediaGenerationControls } from '@/components/MediaGenerationControls'
import type { MediaGenerationControlsHandle } from '@/components/MediaGenerationControls'
import { usePrevizArtifacts, matchingPromptGroup } from '@/components/use-previz-artifacts'
import { PrevizLaneEvidence } from '@/components/PrevizLaneEvidence'
import { AiPrevizViewer } from '@/components/AiPrevizViewer'
import { MediaValidationViewer } from '@/components/MediaValidationViewer'
import {
  formatAdoptionState,
  hasRenderClipPrevizScope,
  previzDescription,
  previzPlaybackSummary,
} from '@/components/previz-panel-support'
import { ScenePlanUnitSummary } from '@/components/ScenePlanUnitSummary'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  isRunActive,
  useArtifact,
  usePrevizAdoptionStatus,
  useRunState,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import { mediaValidationStatus } from '@/lib/health'
import { getSceneScopeLabel } from '@/lib/constants'
import type {
  ArtifactGroupSummary,
} from '@/lib/types'

type PrevizPanelProps = {
  projectId: string
  sceneId: string
  sceneHeading: string
  shotPlanGroup?: ArtifactGroupSummary
  renderClipPlanGroup?: ArtifactGroupSummary
  aiPrevizGroup?: ArtifactGroupSummary
  aiPrevizGroups?: ArtifactGroupSummary[]
  aiPrevizPromptGroup?: ArtifactGroupSummary
  aiPrevizPromptGroups?: ArtifactGroupSummary[]
}

export function PrevizPanel({
  projectId,
  sceneId,
  sceneHeading,
  shotPlanGroup,
  renderClipPlanGroup,
  aiPrevizGroup,
  aiPrevizGroups = [],
  aiPrevizPromptGroup,
  aiPrevizPromptGroups = [],
}: PrevizPanelProps) {
  const { shotPlanData, renderClipPlanData, plannedClipIds, primaryAiPrevizGroup, primaryAiPrevizPromptGroup, allClipAiPrevizPromptGroups, displayedAiPrevizGroups, displayedAiPrevizPromptGroups, hasAnyClipPrevizArtifacts, hasClipPrevizOutputs, sceneAiPrevizGroup, sceneAiPrevizPromptGroup, clipVideoDetailsLoading, staleClipVideoDetails, missingClipIds, staleGroupByRenderClipId } = usePrevizArtifacts({
    projectId, sceneId, shotPlanGroup, renderClipPlanGroup, aiPrevizGroup,
    aiPrevizGroups, aiPrevizPromptGroup, aiPrevizPromptGroups,
  })
  const { data: aiPrevizArtifact, isLoading: aiPrevizLoading } = useArtifact(
    projectId,
    'ai_previz_video',
    primaryAiPrevizGroup?.entity_id ?? sceneId,
    primaryAiPrevizGroup?.latest_version,
  )
  const { data: previzStatus } = usePrevizAdoptionStatus(projectId)
  const activeRunId = useChatStore((store) => store.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const controlsRef = useRef<MediaGenerationControlsHandle>(null)
  const hasActiveRun = isRunActive(activeRunId, runState)
  const aiPrevizRunActive = hasActiveRun && runState?.state.recipe_id === 'ai_previz_generation'
    && runState.state.runtime_params.end_at !== 'render_clip_planning'
  const anotherRunActive = hasActiveRun
    && !!runState
    && runState.state.recipe_id !== 'ai_previz_generation'
  const aiPrevizData = aiPrevizArtifact?.payload?.data as Record<string, unknown> | undefined
  const aiPrevizStatus = previzStatus?.ai_previz
  const hasSavedPrevizOutput = hasAnyClipPrevizArtifacts
    || allClipAiPrevizPromptGroups.length > 0
    || displayedAiPrevizGroups.length > 0
    || displayedAiPrevizPromptGroups.length > 0
    || !!primaryAiPrevizGroup
    || !!primaryAiPrevizPromptGroup
    || !!sceneAiPrevizGroup
    || !!sceneAiPrevizPromptGroup
  const showClipPreviz = hasRenderClipPrevizScope(plannedClipIds.length, hasAnyClipPrevizArtifacts)
  const previzClipArtifactCount = displayedAiPrevizGroups.length
  const plannedClipCount = plannedClipIds.length
  const hasIncompleteCurrentClipSet = plannedClipCount > 0
    && !clipVideoDetailsLoading
    && previzClipArtifactCount < plannedClipCount
  const hiddenStaleClipCount = staleClipVideoDetails.length
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)

  const aiPrevizDetailHref = primaryAiPrevizGroup
    ? `/${projectId}/artifacts/ai_previz_video/${primaryAiPrevizGroup.entity_id ?? sceneId}/${primaryAiPrevizGroup.latest_version}`
    : null
  const aiPrevizPromptHref = primaryAiPrevizPromptGroup
    ? `/${projectId}/artifacts/ai_previz_prompt/${primaryAiPrevizPromptGroup.entity_id ?? sceneId}/${primaryAiPrevizPromptGroup.latest_version}`
    : null
  const validationRef = (
    primaryAiPrevizGroup?.health_details?.source_kind === 'media_validation'
    || primaryAiPrevizGroup?.health_details?.source_kind === 'media_validation_stale'
  )
    ? primaryAiPrevizGroup.health_details.source_artifact_ref
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

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>Previz</CardTitle>
                <Badge variant="outline">Current scene</Badge>
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
                {renderClipPlanGroup && (
                  <Badge variant="secondary">
                    Render clips v{renderClipPlanGroup.latest_version}
                  </Badge>
                )}
              </div>
              <CardDescription className="max-w-3xl leading-relaxed">
                {previzDescription(previzStatus)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          {anotherRunActive && (
            <p>
              Another pipeline run is already in progress. Wait for it to finish before starting
              AI previz.
            </p>
          )}
          {aiPrevizRunActive && (
            <p>AI previz is currently running for {activeRunScopeLabel.toLowerCase()}.</p>
          )}

        </CardContent>
      </Card>

      <MediaGenerationControls key={`${projectId}-${sceneId}`} ref={controlsRef} projectId={projectId} sceneId={sceneId} recipeId="ai_previz_generation" />
      <PrevizLaneEvidence status={aiPrevizStatus} primaryGroup={primaryAiPrevizGroup}
        detailHref={aiPrevizDetailHref} promptHref={aiPrevizPromptHref} validationHref={validationDetailHref}
        hasSavedOutput={hasSavedPrevizOutput} running={aiPrevizRunActive} />

      {aiPrevizData && <p className="text-sm text-muted-foreground">{previzPlaybackSummary({
        sceneHeading, hasIncompleteCurrentClipSet, previzClipArtifactCount, plannedClipCount,
        hasClipPrevizOutputs, validationStatus: mediaValidationStatus(primaryAiPrevizGroup?.health, primaryAiPrevizGroup?.health_details),
      })}</p>}

      <ScenePlanUnitSummary
        mode="previz"
        sceneHeading={sceneHeading}
        shotPlanData={shotPlanData}
        renderClipPlanData={renderClipPlanData}
        currentOutputData={aiPrevizData}
        generatedVideoCount={displayedAiPrevizGroups.length}
      />

      {showClipPreviz && (
        <Card className="gap-0">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">AI Previz Clips</CardTitle>
            <CardDescription>
              {plannedClipCount > 0
                ? `${sceneHeading} has ${previzClipArtifactCount} of ${plannedClipCount} current low-fidelity previz clips.`
                : `${sceneHeading} has ${previzClipArtifactCount} low-fidelity previz clips.`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {hasIncompleteCurrentClipSet && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
                Current previz is incomplete for render clips v{renderClipPlanGroup?.latest_version}.
                {missingClipIds.length > 0 && ` Missing: ${missingClipIds.join(', ')}.`}
                {hiddenStaleClipCount > 0 && ` ${hiddenStaleClipCount} stale prior-plan clip${hiddenStaleClipCount === 1 ? ' is' : 's are'} hidden.`}
              </div>
            )}
            {hasClipPrevizOutputs && sceneAiPrevizGroup && (
              <p className="text-sm text-muted-foreground">
                A previous scene-level previz artifact exists for {sceneId}, but this scene now uses
                render-clip previz. The scene-level artifact is hidden here to avoid mixing old and
                current output models.
              </p>
            )}
            {displayedAiPrevizGroups.map(group => (
              <PrevizClipCard
                key={`previz-${group.entity_id}`}
                projectId={projectId}
                videoGroup={group}
                promptGroup={matchingPromptGroup(displayedAiPrevizPromptGroups, group.entity_id)}
                canRegenerateClip={!hasActiveRun}
                isRegeneratingClip={false}
                onRegenerateClip={clipId => controlsRef.current?.selectClip(clipId)}
              />
            ))}
            {missingClipIds.map(clipId => (
              <MissingPrevizClipCard
                key={`missing-previz-${clipId}`}
                clipId={clipId}
                renderClipPlanVersion={renderClipPlanGroup?.latest_version}
                staleGroup={staleGroupByRenderClipId.get(clipId)}
                canGenerateClip={!hasActiveRun}
                isGeneratingClip={false}
                onGenerateClip={clipId => controlsRef.current?.selectClip(clipId)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {aiPrevizLoading && primaryAiPrevizGroup && !aiPrevizData && !hasClipPrevizOutputs && (
        <div className="h-80 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}
      {validationLoading && validationRef && !validationArtifact && (
        <div className="h-36 rounded-xl border border-border bg-muted/20 animate-pulse" />
      )}

      {aiPrevizData && !hasClipPrevizOutputs && (
        <AiPrevizViewer
          data={aiPrevizData}
          projectId={projectId}
          health={primaryAiPrevizGroup?.health}
          healthDetails={primaryAiPrevizGroup?.health_details}
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
