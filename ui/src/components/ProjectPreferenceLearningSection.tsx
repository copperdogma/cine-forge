import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  clearProjectPreferenceProfile,
  getProjectPreferenceProfile,
  updateProjectSettings,
} from '@/lib/api'
import type { PreferenceCue, PreferenceProfile, ProjectSummary } from '@/lib/types'
import { formatEntityName } from '@/lib/utils'

type Props = {
  projectId: string
  project: ProjectSummary | undefined
}

const DECISION_LABELS: Record<string, string> = {
  selected_final: 'Final',
  favorite: 'Favorite',
  rejected: 'Rejected',
  seed_for_variants: 'Seed',
}

function CueGroup({
  title,
  emptyLabel,
  cues,
}: {
  title: string
  emptyLabel: string
  cues: PreferenceCue[]
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">{title}</h4>
        <Badge variant="outline" className="text-[10px]">
          {cues.length}
        </Badge>
      </div>
      {cues.length === 0 ? (
        <p className="text-xs text-muted-foreground">{emptyLabel}</p>
      ) : (
        <div className="space-y-2">
          {cues.map((cue) => (
            <div key={`${cue.cue_type}-${cue.entity_id}-${cue.text}`} className="rounded-lg border border-border/70 bg-muted/20 px-3 py-2">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-foreground">{cue.text}</p>
                <Badge variant="secondary" className="text-[10px]">
                  {cue.signal_count} signal{cue.signal_count === 1 ? '' : 's'}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatEntityName(cue.entity_id)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function ProjectPreferenceLearningSection({ projectId, project }: Props) {
  const queryClient = useQueryClient()
  const enabled = project?.preference_learning_enabled ?? true

  const profileQuery = useQuery<PreferenceProfile>({
    queryKey: ['projects', projectId, 'preferences', 'profile'],
    queryFn: () => getProjectPreferenceProfile(projectId),
    enabled: !!projectId,
  })

  const toggleMutation = useMutation({
    mutationFn: (nextEnabled: boolean) =>
      updateProjectSettings(projectId, { preference_learning_enabled: nextEnabled }),
    onSuccess: (updatedProject) => {
      queryClient.setQueryData<ProjectSummary>(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'preferences', 'profile'] })
      toast.success(
        updatedProject.preference_learning_enabled
          ? 'Preference learning enabled'
          : 'Preference learning disabled',
      )
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to update preference-learning setting'
      toast.error(message)
    },
  })

  const clearMutation = useMutation({
    mutationFn: () => clearProjectPreferenceProfile(projectId),
    onSuccess: (profile) => {
      queryClient.setQueryData<PreferenceProfile>(
        ['projects', projectId, 'preferences', 'profile'],
        profile,
      )
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Learned preference state cleared')
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to clear learned preferences'
      toast.error(message)
    },
  })

  const profile = profileQuery.data

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border/70 bg-muted/20 px-4 py-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium">Transparent preference learning</h3>
              <Badge variant={enabled ? 'secondary' : 'outline'} className="text-[10px] uppercase tracking-wide">
                {enabled ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Design-study decisions can become project-backed taste signals. You can inspect what CineForge learned, turn it off, or clear the active learned state without deleting the artifact history.
            </p>
            {profile?.last_cleared_at && (
              <p className="text-xs text-muted-foreground">
                Cleared: {new Date(profile.last_cleared_at).toLocaleString()}
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={toggleMutation.isPending}
              onClick={() => toggleMutation.mutate(!enabled)}
            >
              {enabled ? 'Disable learning' : 'Enable learning'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={clearMutation.isPending}
              onClick={() => clearMutation.mutate()}
            >
              Clear learned state
            </Button>
          </div>
        </div>
      </div>

      {profileQuery.isLoading && !profile ? (
        <p className="text-sm text-muted-foreground">Loading learned preferences…</p>
      ) : null}

      {profile ? (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
              {profile.active_signal_count} active signal{profile.active_signal_count === 1 ? '' : 's'}
            </Badge>
            <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
              {profile.entity_count} entit{profile.entity_count === 1 ? 'y' : 'ies'}
            </Badge>
          </div>

          <div className="space-y-2">
            {profile.summary_lines.map((line) => (
              <p key={line} className="text-sm text-foreground">
                {line}
              </p>
            ))}
          </div>

          <Separator />

          <CueGroup
            title="Preferred cues"
            emptyLabel="No explicit positive direction cues yet."
            cues={profile.preferred_cues}
          />

          <CueGroup
            title="Variant refinements"
            emptyLabel="No explicit variation-direction cues yet."
            cues={profile.variation_cues}
          />

          <CueGroup
            title="Avoided cues"
            emptyLabel="No explicit avoided directions yet."
            cues={profile.avoid_cues}
          />

          <Separator />

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Recent active signals</h4>
              <Badge variant="outline" className="text-[10px]">
                {profile.recent_signals.length}
              </Badge>
            </div>
            {profile.recent_signals.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                No active preference signals are available for inspection yet.
              </p>
            ) : (
              <div className="space-y-2">
                {profile.recent_signals.map((signal) => {
                  const supportingText = signal.guidance ?? signal.round_guidance
                  return (
                    <div
                      key={signal.signal_id}
                      className="rounded-lg border border-border/70 bg-muted/20 px-3 py-2"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="secondary" className="text-[10px] uppercase tracking-wide">
                          {DECISION_LABELS[signal.decision] ?? signal.decision}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatEntityName(signal.entity_id)} · round {signal.round_number}
                        </span>
                      </div>
                      {supportingText ? (
                        <p className="mt-1 text-sm text-foreground">{supportingText}</p>
                      ) : (
                        <p className="mt-1 text-xs text-muted-foreground">
                          No explicit text cue; this signal records the user’s latest decision on the image.
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  )
}
