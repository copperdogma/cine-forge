/**
 * SceneWorkspacePage — Per-scene production control surface (ADR-002 View 2, ADR-003).
 *
 * Replaces EntityDetailPage for scenes. Shows five concern group tabs with
 * red/yellow readiness indicators, entity roster, and intent/mood panel.
 * Story 099.
 */
import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Clapperboard,
  Drama,
  Eye,
  FileText,
  Globe,
  Loader2,
  MapPin,
  Scissors,
  Share,
  Users,
  Volume2,
  Wrench,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { DirectionAnnotation, type ConcernGroupType } from '@/components/DirectionAnnotation'
import { SceneIntentPanel } from '@/components/DirectionTab'
import { RolePresenceIndicators } from '@/components/DirectionTab'
import { SceneViewer } from '@/components/ArtifactViewers'
import { ExportModal } from '@/components/ExportModal'
import { PrevizPanel } from '@/components/PrevizPanel'
import { GeneratedVideoPanel } from '@/components/GeneratedVideoPanel'
import { SceneActionControls } from '@/components/SceneActionControls'
import { ShotPlanningPanel } from '@/components/ShotPlanningPanel'
import { StoryboardPanel } from '@/components/StoryboardPanel'
import { ReferenceLibrarySection } from '@/components/assets/ReferenceLibrarySection'
import { EmptyState, ErrorState } from '@/components/StateViews'
import { HealthBadge } from '@/components/HealthBadge'
import { useHistoryBack } from '@/lib/use-history-back'
import { cn, formatEntityName } from '@/lib/utils'
import {
  isRunActive,
  useArtifact,
  useArtifactGroups,
  useEntityNavigation,
  useEntityDetails,
  useEntityResolver,
  useRunState,
  useSceneActionPreflight,
  useStartRun,
  useProjectInputs,
  type ResolvedLink,
} from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import type { ArtifactGroupSummary, SceneScopeMode } from '@/lib/types'
import { buildSceneScope, getSceneScopeLabel, getSceneScopeTargetLabel } from '@/lib/constants'

// ---------------------------------------------------------------------------
// Concern group config
// ---------------------------------------------------------------------------

type ConcernGroupDef = {
  id: string
  concernGroup: ConcernGroupType
  artifactType: string
  label: string
  icon: typeof Scissors
  color: string
  /** true = artifact entity_id is projectId (project-scoped), false = sceneId */
  projectScoped?: boolean
  /** true = generation is not yet implemented */
  placeholder?: boolean
}

const CONCERN_GROUPS: ConcernGroupDef[] = [
  {
    id: 'look_and_feel',
    concernGroup: 'look_and_feel',
    artifactType: 'look_and_feel',
    label: 'Look & Feel',
    icon: Eye,
    color: 'text-sky-400',
  },
  {
    id: 'sound_and_music',
    concernGroup: 'sound_and_music',
    artifactType: 'sound_and_music',
    label: 'Sound & Music',
    icon: Volume2,
    color: 'text-emerald-400',
  },
  {
    id: 'rhythm_and_flow',
    concernGroup: 'rhythm_and_flow',
    artifactType: 'rhythm_and_flow',
    label: 'Rhythm & Flow',
    icon: Scissors,
    color: 'text-pink-400',
  },
  {
    id: 'character_and_performance',
    concernGroup: 'character_and_performance',
    artifactType: 'character_and_performance',
    label: 'Performance',
    icon: Drama,
    color: 'text-amber-400',
    placeholder: true,
  },
  {
    id: 'story_world',
    concernGroup: 'story_world' as ConcernGroupType,
    artifactType: 'story_world',
    label: 'Story World',
    icon: Globe,
    color: 'text-teal-400',
    projectScoped: true,
    placeholder: true,
  },
]

// ---------------------------------------------------------------------------
// Readiness indicator
// ---------------------------------------------------------------------------

type ReadinessLevel = 'red' | 'yellow'

function getReadiness(
  groups: ArtifactGroupSummary[] | undefined,
  artifactType: string,
  entityId: string,
): ReadinessLevel {
  const match = groups?.find(
    g => g.artifact_type === artifactType && g.entity_id === entityId,
  )
  return match ? 'yellow' : 'red'
}

function ReadinessDot({ level, label }: { level: ReadinessLevel; label: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            'h-2.5 w-2.5 rounded-full shrink-0',
            level === 'yellow' ? 'bg-yellow-400' : 'bg-red-500/70',
          )}
        />
      </TooltipTrigger>
      <TooltipContent>
        {label}: {level === 'yellow' ? 'AI draft' : 'Not started'}
      </TooltipContent>
    </Tooltip>
  )
}

// ---------------------------------------------------------------------------
// Entity roster (character / location / prop links for this scene)
// ---------------------------------------------------------------------------

function EntityLink({
  resolved,
  label,
  icon: Icon,
  iconColor,
  showArrow,
}: {
  resolved: ResolvedLink | null
  label: string
  icon?: typeof Users
  iconColor?: string
  showArrow?: boolean
}) {
  const cls =
    'inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium hover:bg-accent/50 transition-colors'

  if (resolved) {
    return (
      <Link to={resolved.path} className={cls}>
        {Icon && <Icon className={cn('h-3 w-3 shrink-0', iconColor)} />}
        <span>{label}</span>
        {showArrow && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
      </Link>
    )
  }
  return (
    <span className={cn(cls, 'opacity-50 cursor-default hover:bg-transparent')}>
      {Icon && <Icon className="h-3 w-3 shrink-0" />}
      <span>{label}</span>
    </span>
  )
}

function SceneEntityRoster({
  sceneData,
  resolve,
  propsInScene,
}: {
  sceneData: Record<string, unknown>
  resolve: (name: string, type?: 'character' | 'location' | 'prop') => ResolvedLink | null
  propsInScene: Array<{ entity_id: string | null; name: string; path: string }>
}) {
  const characters = (sceneData.characters_present as string[] | undefined) ?? []
  const location = sceneData.location as string | undefined

  if (characters.length === 0 && !location && propsInScene.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 items-center rounded-lg border border-border bg-card/50 px-4 py-2.5">
      {location && (
        <EntityLink
          resolved={resolve(location, 'location')}
          label={location}
          icon={MapPin}
          iconColor="text-rose-400"
          showArrow
        />
      )}
      {characters.map(name => (
        <EntityLink
          key={name}
          resolved={resolve(name, 'character')}
          label={name}
          icon={Users}
          iconColor="text-amber-400"
          showArrow
        />
      ))}
      {propsInScene.map(prop => (
        <EntityLink
          key={prop.entity_id}
          resolved={{ path: prop.path, label: prop.name }}
          label={prop.name}
          icon={Wrench}
          iconColor="text-orange-400"
          showArrow
        />
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Per concern group tab content
// ---------------------------------------------------------------------------

function ConcernGroupTabContent({
  projectId,
  sceneId,
  sceneHeading,
  cg,
  groups,
}: {
  projectId: string
  sceneId: string
  sceneHeading: string
  cg: ConcernGroupDef
  groups: ArtifactGroupSummary[] | undefined
}) {
  const entityId = cg.projectScoped ? projectId : sceneId
  const existing = groups?.find(
    g => g.artifact_type === cg.artifactType && g.entity_id === entityId,
  )

  const { data: artifact, isLoading } = useArtifact(
    projectId,
    cg.artifactType,
    entityId,
    existing?.latest_version,
  )

  const { data: inputs } = useProjectInputs(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const startRun = useStartRun()
  const activeRunId = useChatStore(s => s.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)
  const hasActiveRun = isRunActive(activeRunId, runState)
  const runActive = hasActiveRun || startRun.isPending
  const [scope, setScope] = useState<SceneScopeMode>('current_scene')
  const sceneScope = buildSceneScope(scope, sceneId)
  const configuredScopeLabel = getSceneScopeLabel(sceneScope)
  const configuredScopeTarget = getSceneScopeTargetLabel(sceneScope)
  const activeRunScopeLabel = getSceneScopeLabel(runState?.state.runtime_params?.scene_scope)
  const concernRunActive = hasActiveRun
    && runState?.state.recipe_id === 'creative_direction'
    && Array.isArray(runState.state.stage_order)
    && runState.state.stage_order.length === 1
    && runState.state.stage_order[0] === cg.id
  const anotherRunActive = hasActiveRun && !concernRunActive
  const { data: preflight } = useSceneActionPreflight(
    projectId,
    cg.placeholder
      ? null
      : {
          recipe_id: 'creative_direction',
          start_from: cg.id,
          end_at: cg.id,
          scene_scope: sceneScope,
        },
    !cg.placeholder,
  )
  const canGenerate = !!latestInputPath && !runActive && preflight?.status !== 'soft_block'

  const [isGenerating, setIsGenerating] = useState(false)
  if (!runActive && isGenerating) setIsGenerating(false)

  const handleGenerate = async () => {
    if (!latestInputPath || cg.placeholder) return
    setIsGenerating(true)
    try {
      const { run_id } = await startRun.mutateAsync({
        project_id: projectId,
        input_file: latestInputPath,
        default_model: 'claude-sonnet-4-6',
        recipe_id: 'creative_direction',
        start_from: cg.id,
        end_at: cg.id,
        accept_config: true,
        skip_qa: true,
        force: !!existing,
        scene_scope: sceneScope,
      })
      useChatStore.getState().setActiveRun(projectId, run_id)
      setIsGenerating(false)
    } catch {
      setIsGenerating(false)
      // Error handled by run tracking
    }
  }

  const Icon = cg.icon
  const generateButtonLabel = scope === 'current_scene'
    ? (existing ? `Regenerate ${cg.label} for Current Scene` : `Get ${cg.label} for Current Scene`)
    : (existing ? `Regenerate ${cg.label} for All Scenes` : `Get ${cg.label} for All Scenes`)

  const generateBtn = (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">Selected: {configuredScopeLabel}</Badge>
          {existing && <Badge variant="secondary">v{existing.latest_version}</Badge>}
        </div>
        <Button
          size="sm"
          variant={existing ? 'outline' : 'default'}
          className="gap-1.5"
          disabled={!canGenerate}
          onClick={handleGenerate}
        >
          {isGenerating ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Icon className="h-3.5 w-3.5" />
          )}
          {generateButtonLabel}
        </Button>
      </div>
      {!latestInputPath && (
        <p className="text-sm text-muted-foreground">
          No screenplay input is available for this project yet.
        </p>
      )}
      {anotherRunActive && (
        <p className="text-sm text-muted-foreground">
          Another pipeline run is already in progress. Wait for it to finish before starting
          {` ${cg.label.toLowerCase()}`} direction.
        </p>
      )}
      {concernRunActive && (
        <p className="text-sm text-muted-foreground">
          {cg.label} direction is currently running for {activeRunScopeLabel.toLowerCase()}.
        </p>
      )}
      <SceneActionControls
        scope={scope}
        onScopeChange={setScope}
        preflight={preflight}
        disabled={runActive}
      />
    </div>
  )

  if (cg.placeholder) {
    const placeholderMessage = cg.id === 'story_world'
      ? 'Project-level story-world baselines are coming in a future update.'
      : 'Per-character performance direction is coming in a future update.'
    return (
      <div className="rounded-lg border border-dashed border-border py-12 flex flex-col items-center gap-4">
        <Icon className={cn('h-10 w-10', cg.color)} />
        <div className="text-center space-y-1">
          <p className="text-sm font-medium">{cg.label} direction</p>
          <p className="text-xs text-muted-foreground">
            {placeholderMessage}
          </p>
          <p className="text-xs text-muted-foreground">
            This placeholder should warn, not block. You can keep moving into shots, previz, and
            render without it.
          </p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return <div className="h-32 rounded-lg bg-muted animate-pulse" />
  }

  const data = artifact?.payload?.data as Record<string, unknown> | undefined

  if (!data) {
    return (
      <div className="space-y-4">
        {generateBtn}
        <div className="rounded-lg border border-dashed border-border py-12 flex flex-col items-center gap-4">
          <Icon className={cn('h-10 w-10', cg.color)} />
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-foreground/80">No {cg.label} direction yet</p>
            <p className="text-xs text-muted-foreground">
              Generate direction for {configuredScopeTarget} and this tab will resolve back to
              {` ${sceneHeading}`}.
            </p>
          </div>
          <Button
            size="sm"
            variant="default"
            className="gap-1.5"
            disabled={!canGenerate}
            onClick={handleGenerate}
          >
            {isGenerating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Icon className="h-3.5 w-3.5" />
            )}
            {generateButtonLabel}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {generateBtn}
      <DirectionAnnotation
        concernGroup={cg.concernGroup}
        data={data}
        sceneHeading={sceneHeading}
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function SceneWorkspacePage() {
  const { projectId, entityId } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [isExportOpen, setIsExportOpen] = useState(false)

  const nav = useEntityNavigation(projectId, 'scenes', entityId)
  const goBack = useHistoryBack(`/${projectId}/scenes`)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 'ArrowLeft' && nav.prev) navigate(`/${projectId}/scenes/${nav.prev}`)
      else if (e.key === 'ArrowRight' && nav.next) navigate(`/${projectId}/scenes/${nav.next}`)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [projectId, nav.prev, nav.next, navigate])

  const { resolve } = useEntityResolver(projectId)
  const { data: groups, isLoading: groupsLoading } = useArtifactGroups(projectId)

  // Find the scene artifact
  const group = groups?.find(
    g => g.artifact_type === 'scene' && g.entity_id === entityId,
  )
  const { data: artifact, isLoading: artifactLoading, error } = useArtifact(
    projectId,
    'scene',
    entityId,
    group?.latest_version,
  )

  // Infer props in this scene from all prop bibles
  const { data: propEntities } = useEntityDetails(projectId, 'prop_bible')
  const propsInScene = useMemo(() => {
    if (!entityId || !propEntities) return []
    return propEntities
      .filter(p => (p.data?.scene_presence as string[] | undefined)?.includes(entityId))
      .map(p => ({
        entity_id: p.entity_id,
        name: (p.data?.name as string | undefined) ?? formatEntityName(p.entity_id ?? ''),
        path: `/${projectId}/props/${p.entity_id}`,
      }))
  }, [propEntities, entityId, projectId])

  if (!projectId || !entityId) return <ErrorState message="Invalid scene route" />

  const isLoading = groupsLoading || artifactLoading

  if (isLoading) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-4">
        <BackNavigation projectId={projectId} nav={nav} goBack={goBack} />
        <ErrorState message={error instanceof Error ? error.message : 'Failed to load scene'} />
      </div>
    )
  }

  if (!artifact || !group) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-4">
        <BackNavigation projectId={projectId} nav={nav} goBack={goBack} />
        <EmptyState
          icon={Clapperboard}
          title="Scene not found"
          description={`No scene artifact found for "${formatEntityName(entityId)}".`}
        />
      </div>
    )
  }

  const data = artifact.payload?.data as Record<string, unknown> | undefined
  const displayName = (
    data?.display_name ??
    data?.heading ??
    data?.scene_heading ??
    formatEntityName(entityId)
  ) as string
  const shotPlanGroup = groups?.find(
    g => g.artifact_type === 'shot_plan' && g.entity_id === entityId,
  )
  const shotPlanLevel = getReadiness(groups, 'shot_plan', entityId)
  const storyboardGroup = groups?.find(
    g => g.artifact_type === 'storyboard' && g.entity_id === entityId,
  )
  const storyboardLevel = getReadiness(groups, 'storyboard', entityId)
  const keyframeGroup = groups?.find(
    g => g.artifact_type === 'keyframe' && g.entity_id === entityId,
  )
  const aiPrevizPromptGroup = groups?.find(
    g => g.artifact_type === 'ai_previz_prompt' && g.entity_id === entityId,
  )
  const aiPrevizGroup = groups?.find(
    g => g.artifact_type === 'ai_previz_video' && g.entity_id === entityId,
  )
  const renderPromptGroup = groups?.find(
    g => g.artifact_type === 'render_prompt' && g.entity_id === entityId,
  )
  const generatedVideoGroup = groups?.find(
    g => g.artifact_type === 'generated_video' && g.entity_id === entityId,
  )
  const previzLevel = aiPrevizGroup ? 'yellow' : 'red'
  const renderLevel = getReadiness(groups, 'generated_video', entityId)
  const validTabs = new Set([
    'overview',
    ...CONCERN_GROUPS.map((cg) => cg.id),
    'shots',
    'storyboard',
    'previz',
    'render',
  ])
  const requestedTab = searchParams.get('tab')
  const activeTab = requestedTab && validTabs.has(requestedTab) ? requestedTab : 'overview'

  return (
    <div className="w-full max-w-5xl mx-auto space-y-5">
      {/* Navigation row */}
      <div className="flex items-center justify-between">
        <BackNavigation projectId={projectId} nav={nav} goBack={goBack} />
        <Button
          variant="outline"
          size="icon"
          className="h-11 w-11 shrink-0 rounded-full sm:hidden"
          onClick={() => setIsExportOpen(true)}
          aria-label="Export scene"
          title="Export scene"
        >
          <Share className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="hidden sm:inline-flex"
          onClick={() => setIsExportOpen(true)}
        >
          <Share className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Scene header */}
      <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-start">
        <div className="rounded-lg bg-card border border-border p-2.5 shrink-0">
          <Clapperboard className="h-6 w-6 text-violet-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight truncate">{displayName}</h1>
            <HealthBadge health={group.health} details={group.health_details} />
            <RolePresenceIndicators groups={groups} entityId={entityId} />
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>Scene</span>
            {typeof data?.scene_number === 'number' && (
              <>
                <span className="text-muted-foreground/50">&middot;</span>
                <span>#{data.scene_number}</span>
              </>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="self-start gap-1.5 shrink-0"
          onClick={() => navigate(`/${projectId}#${encodeURIComponent(displayName)}`)}
        >
          <FileText className="h-3.5 w-3.5" />
          View in Script
        </Button>
      </div>

      {/* Entity roster — characters, location, props */}
      {data && (
        <SceneEntityRoster sceneData={data} resolve={resolve} propsInScene={propsInScene} />
      )}

      <ReferenceLibrarySection
        projectId={projectId}
        targetKind="scene"
        targetId={entityId}
        title="Scene Reference Stack"
        description="Attach dialogue takes, temp score, blocking clips, and script-side PDFs directly to this scene. These assets stay scene-scoped and merge with project references downstream."
        purposePresets={['dialogue_audio', 'temp_music', 'blocking_video', 'reference_doc']}
        activeReferenceHint="Sound & Music and the track system read project + scene audio from this stack. Visual entity design-study picks remain inherited from the linked character/location/prop pages."
      />

      {/* Intent & Mood panel */}
      <SceneIntentPanel projectId={projectId} entityId={entityId} />

      {/* Main workspace tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => {
          const nextParams = new URLSearchParams(searchParams)
          if (value === 'overview') {
            nextParams.delete('tab')
          } else {
            nextParams.set('tab', value)
          }
          setSearchParams(nextParams, { replace: true })
        }}
        className="w-full"
      >
        <TabsList variant="line" scrollable className="w-full border-b border-border pb-1">
          <TabsTrigger value="overview">
            Overview
          </TabsTrigger>
          {CONCERN_GROUPS.map(cg => {
            const entityId2 = cg.projectScoped ? projectId : entityId
            const level = getReadiness(groups, cg.artifactType, entityId2)
            return (
              <TabsTrigger key={cg.id} value={cg.id} className="gap-1.5">
                <ReadinessDot level={level} label={cg.label} />
                {cg.label}
              </TabsTrigger>
            )
          })}
          <TabsTrigger value="shots" className="gap-1.5">
            <ReadinessDot level={shotPlanLevel} label="Shots" />
            Shots
          </TabsTrigger>
          <TabsTrigger value="storyboard" className="gap-1.5">
            <ReadinessDot level={storyboardLevel} label="Storyboard" />
            Storyboard
          </TabsTrigger>
          <TabsTrigger value="previz" className="gap-1.5">
            <ReadinessDot level={previzLevel} label="Previz" />
            Previz
          </TabsTrigger>
          <TabsTrigger value="render" className="gap-1.5">
            <ReadinessDot level={renderLevel} label="Render" />
            Render
          </TabsTrigger>
        </TabsList>

        {/* Overview — scene data (text summary = current "best available preview") */}
        <TabsContent value="overview" className="mt-4">
          {data ? <SceneViewer data={data} /> : null}
        </TabsContent>

        {/* Concern group tabs */}
        {CONCERN_GROUPS.map(cg => (
          <TabsContent key={cg.id} value={cg.id} className="mt-4">
            <ConcernGroupTabContent
              projectId={projectId}
              sceneId={entityId}
              sceneHeading={displayName}
              cg={cg}
              groups={groups}
            />
          </TabsContent>
        ))}

        <TabsContent value="shots" className="mt-4">
          <ShotPlanningPanel
            projectId={projectId}
            sceneId={entityId}
            sceneHeading={displayName}
            shotPlanGroup={shotPlanGroup}
          />
        </TabsContent>

        <TabsContent value="storyboard" className="mt-4">
          <StoryboardPanel
            projectId={projectId}
            sceneId={entityId}
            sceneHeading={displayName}
            storyboardGroup={storyboardGroup}
            shotPlanGroup={shotPlanGroup}
          />
        </TabsContent>

        <TabsContent value="previz" className="mt-4">
          <PrevizPanel
            projectId={projectId}
            sceneId={entityId}
            sceneHeading={displayName}
            shotPlanGroup={shotPlanGroup}
            aiPrevizGroup={aiPrevizGroup}
            aiPrevizPromptGroup={aiPrevizPromptGroup}
          />
        </TabsContent>

        <TabsContent value="render" className="mt-4">
          <GeneratedVideoPanel
            projectId={projectId}
            sceneId={entityId}
            sceneHeading={displayName}
            shotPlanGroup={shotPlanGroup}
            renderPromptGroup={renderPromptGroup}
            generatedVideoGroup={generatedVideoGroup}
            keyframeGroup={keyframeGroup}
          />
        </TabsContent>
      </Tabs>

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId}
        defaultScope="single"
        entityId={entityId}
        entityType="scene"
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Shared navigation component
// ---------------------------------------------------------------------------

function BackNavigation({
  projectId,
  nav,
  goBack,
}: {
  projectId: string
  nav: ReturnType<typeof useEntityNavigation>
  goBack: () => void
}) {
  const navigate = useNavigate()

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5 text-muted-foreground hover:text-foreground"
        onClick={goBack}
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>

      {/* Script-order nav */}
      <div className="flex items-center bg-card border border-border rounded-lg overflow-hidden h-9">
        <Button
          variant="ghost"
          size="sm"
          className="h-full rounded-none px-2 border-r border-border"
          disabled={!nav.prev}
          onClick={() => navigate(`/${projectId}/scenes/${nav.prev}`)}
          title="Previous scene [Left Arrow]"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="px-3 text-xs font-medium text-muted-foreground bg-muted/30 h-full flex items-center">
          {nav.sortMode === 'script-order' ? 'Script Order' : nav.sortMode === 'alphabetical' ? 'A–Z' : 'Prominence'}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-full rounded-none px-2 border-l border-border"
          disabled={!nav.next}
          onClick={() => navigate(`/${projectId}/scenes/${nav.next}`)}
          title="Next scene [Right Arrow]"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Chronological nav */}
      {(nav.prevChronological || nav.nextChronological) && (
        <div className="flex items-center bg-card border border-border rounded-lg overflow-hidden h-9">
          <Button
            variant="ghost"
            size="sm"
            className="h-full rounded-none px-2 border-r border-border"
            disabled={!nav.prevChronological}
            onClick={() => navigate(`/${projectId}/scenes/${nav.prevChronological}`)}
            title="Previous chronological scene"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <div className="px-3 text-xs font-medium text-muted-foreground bg-muted/30 h-full flex items-center">
            Chronological
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-full rounded-none px-2 border-l border-border"
            disabled={!nav.nextChronological}
            onClick={() => navigate(`/${projectId}/scenes/${nav.nextChronological}`)}
            title="Next chronological scene"
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
