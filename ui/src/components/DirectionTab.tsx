/**
 * DirectionTab — Tab content for scene creative direction.
 *
 * Shows direction annotations from all creative roles for a given scene,
 * with generate buttons and convergence actions.
 */
import { Scissors, Sparkles, Users as UsersIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { DirectionAnnotation, type DirectionType } from './DirectionAnnotation'
import { useRightPanel } from '@/lib/right-panel'
import { askChatQuestion } from '@/lib/glossary'
import { useArtifactGroups, useArtifact } from '@/lib/hooks'
import type { ArtifactGroupSummary } from '@/lib/types'

// --- Role presence indicator ---

const DIRECTION_ROLES: Array<{
  directionType: DirectionType
  artifactType: string
  roleId: string
  roleName: string
  icon: typeof Scissors
  color: string
}> = [
  { directionType: 'editorial', artifactType: 'editorial_direction', roleId: 'editorial_architect', roleName: 'Editorial', icon: Scissors, color: 'text-pink-400' },
  // Future roles plug in here:
  // { directionType: 'visual', artifactType: 'visual_direction', roleId: 'visual_architect', roleName: 'Visual', icon: Eye, color: 'text-sky-400' },
  // { directionType: 'sound', artifactType: 'sound_direction', roleId: 'sound_designer', roleName: 'Sound', icon: Volume2, color: 'text-emerald-400' },
  // { directionType: 'performance', artifactType: 'performance_direction', roleId: 'story_editor', roleName: 'Story', icon: Drama, color: 'text-amber-400' },
]

export function RolePresenceIndicators({
  groups,
  entityId,
}: {
  groups: ArtifactGroupSummary[] | undefined
  entityId: string
}) {
  if (!groups) return null

  const present = DIRECTION_ROLES.filter(role =>
    groups.some(g => g.artifact_type === role.artifactType && g.entity_id === entityId),
  )

  if (present.length === 0) return null

  return (
    <div className="flex items-center gap-1">
      {present.map(role => {
        const Icon = role.icon
        return (
          <Tooltip key={role.roleId}>
            <TooltipTrigger asChild>
              <div className={`rounded-md border border-border p-1 ${role.color}`}>
                <Icon className="h-3 w-3" />
              </div>
            </TooltipTrigger>
            <TooltipContent>{role.roleName} direction available</TooltipContent>
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

  // Find editorial direction group for this scene
  const editorialGroup = groups?.find(
    g => g.artifact_type === 'editorial_direction' && g.entity_id === entityId,
  )

  const handleGenerate = (roleId: string, roleName: string) => {
    if (!panel.state.open) panel.openChat()
    panel.setTab('chat')
    const sceneCtx = sceneHeading ? ` for scene "${sceneHeading}"` : ' for this scene'
    askChatQuestion(`@${roleId} Analyze this scene and provide ${roleName.toLowerCase()} direction${sceneCtx}.`)
  }

  const handleConverge = () => {
    if (!panel.state.open) panel.openChat()
    panel.setTab('chat')
    askChatQuestion(
      `@director Review all creative direction for this scene and identify any conflicts or opportunities for convergence.`,
    )
  }

  const hasAnyDirection = !!editorialGroup

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant={editorialGroup ? 'outline' : 'default'}
            size="sm"
            className="gap-1.5"
            onClick={() => handleGenerate('editorial_architect', 'Editorial')}
          >
            <Scissors className="h-3.5 w-3.5" />
            {editorialGroup ? 'Regenerate Editorial' : 'Get Editorial Direction'}
          </Button>
          {/* Future: visual, sound, performance generate buttons */}
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
      {editorialGroup ? (
        <EditorialDirectionCard
          projectId={projectId}
          entityId={entityId}
          version={editorialGroup.latest_version}
          sceneHeading={sceneHeading}
        />
      ) : (
        <DirectionEmptyState />
      )}
    </div>
  )
}

// --- Editorial direction card (fetches and renders) ---

function EditorialDirectionCard({
  projectId,
  entityId,
  version,
  sceneHeading,
}: {
  projectId: string
  entityId: string
  version: number
  sceneHeading?: string
}) {
  const { data: artifact, isLoading } = useArtifact(projectId, 'editorial_direction', entityId, version)

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
      directionType="editorial"
      data={data}
      sceneHeading={sceneHeading}
    />
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
          Click &quot;Get Editorial Direction&quot; above, or type{' '}
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 font-mono">
            @editorial_architect
          </Badge>{' '}
          in chat to get editing advice for this scene.
        </p>
      </div>
    </div>
  )
}
