/**
 * DirectionTab — Tab content for scene creative direction.
 *
 * Shows direction annotations from all concern groups for a given scene,
 * with generate buttons and convergence actions.
 * ADR-003: concern groups replace role-based direction types.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Compass, Scissors, Sparkles, Users as UsersIcon } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { DirectionAnnotation, type ConcernGroupType } from './DirectionAnnotation'
import { useRightPanel } from '@/lib/right-panel'
import { askChatQuestion } from '@/lib/glossary'
import { useArtifactGroups, useArtifact } from '@/lib/hooks'
import { getIntentMood } from '@/lib/api'
import type { ArtifactGroupSummary } from '@/lib/types'

// --- Concern group definitions ---

const CONCERN_GROUPS: Array<{
  concernGroup: ConcernGroupType
  artifactType: string
  roleId: string
  roleName: string
  icon: typeof Scissors
  color: string
}> = [
  { concernGroup: 'rhythm_and_flow', artifactType: 'rhythm_and_flow', roleId: 'editorial_architect', roleName: 'Rhythm & Flow', icon: Scissors, color: 'text-pink-400' },
  // Future concern groups plug in here as their modules land:
  // { concernGroup: 'look_and_feel', artifactType: 'look_and_feel', roleId: 'visual_architect', roleName: 'Look & Feel', icon: Eye, color: 'text-sky-400' },
  // { concernGroup: 'sound_and_music', artifactType: 'sound_and_music', roleId: 'sound_designer', roleName: 'Sound & Music', icon: Volume2, color: 'text-emerald-400' },
  // { concernGroup: 'character_and_performance', artifactType: 'character_and_performance', roleId: 'story_editor', roleName: 'Character', icon: Drama, color: 'text-amber-400' },
]

export function RolePresenceIndicators({
  groups,
  entityId,
}: {
  groups: ArtifactGroupSummary[] | undefined
  entityId: string
}) {
  if (!groups) return null

  const present = CONCERN_GROUPS.filter(cg =>
    groups.some(g => g.artifact_type === cg.artifactType && g.entity_id === entityId),
  )

  if (present.length === 0) return null

  return (
    <div className="flex items-center gap-1">
      {present.map(cg => {
        const Icon = cg.icon
        return (
          <Tooltip key={cg.concernGroup}>
            <TooltipTrigger asChild>
              <div className={`rounded-md border border-border p-1 ${cg.color}`}>
                <Icon className="h-3 w-3" />
              </div>
            </TooltipTrigger>
            <TooltipContent>{cg.roleName} direction available</TooltipContent>
          </Tooltip>
        )
      })}
    </div>
  )
}

// --- Main DirectionTab ---

export function DirectionTab({
  projectId,
  entityId,
  sceneHeading,
}: {
  projectId: string
  entityId: string
  sceneHeading?: string
}) {
  const panel = useRightPanel()
  const { data: groups } = useArtifactGroups(projectId)

  // Find rhythm & flow direction group for this scene
  const rhythmGroup = groups?.find(
    g => g.artifact_type === 'rhythm_and_flow' && g.entity_id === entityId,
  )

  const handleGenerate = (roleId: string, roleName: string) => {
    if (!panel.state.open) panel.openChat()
    const sceneCtx = sceneHeading ? ` for scene "${sceneHeading}"` : ' for this scene'
    askChatQuestion(`@${roleId} Analyze this scene and provide ${roleName.toLowerCase()} direction${sceneCtx}.`)
  }

  const handleConverge = () => {
    if (!panel.state.open) panel.openChat()
    askChatQuestion(
      `@director Review all creative direction for this scene and identify any conflicts or opportunities for convergence.`,
    )
  }

  const hasAnyDirection = !!rhythmGroup

  return (
    <div className="space-y-4">
      {/* Scene intent panel */}
      <SceneIntentPanel projectId={projectId} entityId={entityId} />

      {/* Action bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant={rhythmGroup ? 'outline' : 'default'}
            size="sm"
            className="gap-1.5"
            onClick={() => handleGenerate('editorial_architect', 'Rhythm & Flow')}
          >
            <Scissors className="h-3.5 w-3.5" />
            {rhythmGroup ? 'Regenerate Rhythm & Flow' : 'Get Rhythm & Flow Direction'}
          </Button>
          {/* Future: look_and_feel, sound_and_music, character_and_performance buttons */}
        </div>

        {hasAnyDirection && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={handleConverge}
          >
            <UsersIcon className="h-3.5 w-3.5" />
            Review with Director
          </Button>
        )}
      </div>

      {/* Direction annotations */}
      {rhythmGroup ? (
        <ConcernGroupCard
          projectId={projectId}
          entityId={entityId}
          artifactType="rhythm_and_flow"
          concernGroup="rhythm_and_flow"
          version={rhythmGroup.latest_version}
          sceneHeading={sceneHeading}
        />
      ) : (
        <DirectionEmptyState />
      )}
    </div>
  )
}

// --- Generic concern group card (fetches and renders) ---

function ConcernGroupCard({
  projectId,
  entityId,
  artifactType,
  concernGroup,
  version,
  sceneHeading,
}: {
  projectId: string
  entityId: string
  artifactType: string
  concernGroup: ConcernGroupType
  version: number
  sceneHeading?: string
}) {
  const { data: artifact, isLoading } = useArtifact(projectId, artifactType, entityId, version)

  if (isLoading) {
    return (
      <div className="space-y-2">
        <div className="h-32 rounded-lg bg-muted animate-pulse" />
      </div>
    )
  }

  const data = artifact?.payload?.data as Record<string, unknown> | undefined
  if (!data) return null

  return (
    <DirectionAnnotation
      concernGroup={concernGroup}
      data={data}
      sceneHeading={sceneHeading}
    />
  )
}

// --- Scene intent panel ---

function SceneIntentPanel({
  projectId,
  entityId,
}: {
  projectId: string
  entityId: string
}) {
  const [showCustomize, setShowCustomize] = useState(false)

  // Load project-level intent
  const { data: projectIntent } = useQuery({
    queryKey: ['intent-mood', projectId],
    queryFn: () => getIntentMood(projectId),
    enabled: !!projectId,
  })

  // Load scene-level override (if any)
  const { data: sceneIntent } = useQuery({
    queryKey: ['intent-mood', projectId, entityId],
    queryFn: () => getIntentMood(projectId, entityId),
    enabled: !!projectId && !!entityId,
  })

  const intent = sceneIntent ?? projectIntent
  const isOverride = !!sceneIntent
  const hasMood = intent && (intent.mood_descriptors.length > 0 || intent.style_preset_id || intent.natural_language_intent)

  if (!hasMood && !showCustomize) return null

  return (
    <div className="rounded-lg border border-border bg-card/50 p-3 space-y-2">
      <div className="flex items-center gap-2">
        <Compass className="h-4 w-4 text-purple-400" />
        <span className="text-sm font-medium">Intent & Mood</span>
        {isOverride ? (
          <Badge variant="secondary" className="text-[10px]">Scene override</Badge>
        ) : hasMood ? (
          <Badge variant="outline" className="text-[10px]">Inherited from project</Badge>
        ) : null}
        <div className="flex-1" />
        {!isOverride && hasMood && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={() => setShowCustomize(true)}
          >
            Customize for this scene
          </Button>
        )}
        {isOverride && (
          <a
            href={`/${projectId}/intent`}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Edit project intent
          </a>
        )}
      </div>

      {hasMood && (
        <div className="flex flex-wrap gap-1.5">
          {intent!.mood_descriptors.map(tag => (
            <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
          ))}
          {intent!.natural_language_intent && (
            <p className="text-xs text-muted-foreground italic w-full mt-1">
              &ldquo;{intent!.natural_language_intent}&rdquo;
            </p>
          )}
        </div>
      )}

      {showCustomize && !isOverride && (
        <p className="text-xs text-muted-foreground">
          Scene-level overrides will be available in a future update. For now,{' '}
          <a
            href={`/${projectId}/intent`}
            className="text-primary underline underline-offset-2"
          >
            edit intent at the project level
          </a>.
        </p>
      )}
    </div>
  )
}

// --- Empty state ---

function DirectionEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border p-8 text-center space-y-3">
      <Sparkles className="h-8 w-8 text-muted-foreground/40 mx-auto" />
      <div>
        <p className="text-sm font-medium text-foreground/80">No direction yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Click &quot;Get Rhythm &amp; Flow Direction&quot; above, or type{' '}
          <span className="inline-flex items-center rounded-md bg-secondary px-1.5 py-0 text-[10px] font-mono">
            @editorial_architect
          </span>{' '}
          in chat to get editing advice for this scene.
        </p>
      </div>
    </div>
  )
}
