import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { Compass, Sparkles, Loader2, ChevronDown, ChevronRight, Check, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { PageHeader } from '@/components/PageHeader'
import { ProjectReferencesSection } from '@/components/ProjectReferencesSection'
import { CreativeBriefPreviewCard } from '@/components/intent/CreativeBriefPreviewCard'
import { IntentTasteStackFields } from '@/components/intent/IntentTasteStackFields'
import { VisualMediumCard } from '@/components/VisualMediumCard'
import { toast } from 'sonner'
import { useChatStore } from '@/lib/chat-store'
import { getRunningRunLabel, getUserFacingRecipeName } from '@/lib/constants'
import { useLongRunningAction } from '@/lib/use-long-running-action'
import { useActiveProjectRun, useArtifactGroups, useProject, useProjectInputs, useStartRun } from '@/lib/hooks'
import {
  getStylePresets,
  getIntentMood,
  getCreativeBriefPreview,
  getScriptContext,
  suggestIntentMood,
  saveIntentMood,
  propagateMood,
  type StylePresetResponse,
  type PropagationResponse,
  type PropagatedGroupResponse,
} from '@/lib/api'
import { startTrackedRun } from '@/lib/run-actions'
import { cn } from '@/lib/utils'

/** Concern group display config. */
const CONCERN_GROUP_META: Record<string, { label: string; color: string }> = {
  look_and_feel: { label: 'Look & Feel', color: 'text-sky-400' },
  sound_and_music: { label: 'Sound & Music', color: 'text-emerald-400' },
  rhythm_and_flow: { label: 'Rhythm & Flow', color: 'text-pink-400' },
  character_and_performance: { label: 'Character & Performance', color: 'text-amber-400' },
  story_world: { label: 'Story World', color: 'text-teal-400' },
}

/** Common mood descriptor suggestions. */
const MOOD_SUGGESTIONS = [
  'tense', 'warm', 'chaotic', 'dreamy', 'epic', 'intimate', 'raw',
  'unsettling', 'nostalgic', 'kinetic', 'melancholic', 'luminous',
  'gritty', 'playful', 'ominous', 'serene',
]

export default function IntentMoodPage() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const { data: project } = useProject(projectId)
  const { isRunning: hasActiveRun, recipeId: activeRecipeId } = useActiveProjectRun(projectId)

  // --- Deep breakdown gate ---
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const hasDeepBreakdown = artifactGroups?.some(
    g => g.artifact_type === 'character_bible' || g.artifact_type === 'entity_graph'
  ) ?? false
  const hasBreakdownArtifacts = artifactGroups?.some(
    g => g.artifact_type === 'canonical_script' || g.artifact_type === 'script_bible' || g.artifact_type === 'scene',
  ) ?? false
  const { data: inputs } = useProjectInputs(projectId)
  const latestInputPath = inputs?.[inputs.length - 1]?.stored_path
  const startRun = useStartRun()

  // --- Data fetching ---
  const { data: presets } = useQuery({
    queryKey: ['style-presets', projectId],
    queryFn: () => getStylePresets(projectId!),
    enabled: !!projectId,
  })

  const { data: currentIntent } = useQuery({
    queryKey: ['intent-mood', projectId],
    queryFn: () => getIntentMood(projectId!),
    enabled: !!projectId,
  })

  const { data: creativeBrief, isLoading: creativeBriefLoading } = useQuery({
    queryKey: ['creative-brief', projectId],
    queryFn: () => getCreativeBriefPreview(projectId!),
    enabled: !!projectId,
  })

  const { data: scriptContext } = useQuery({
    queryKey: ['script-context', projectId],
    queryFn: () => getScriptContext(projectId!),
    enabled: !!projectId,
  })
  const hasScriptBreakdown = !!scriptContext || hasBreakdownArtifacts
  const requiredRecipeId = hasScriptBreakdown ? 'world_building' : 'mvp_ingest'
  const requiredRunLabel = hasScriptBreakdown ? 'Deep Breakdown' : 'Script Breakdown'
  const deepBreakdownBlocked = startRun.isPending || hasActiveRun
  const deepBreakdownLabel = startRun.isPending
    ? `Starting ${requiredRunLabel}...`
    : hasActiveRun
      ? getRunningRunLabel(activeRecipeId)
      : `Run ${requiredRunLabel}`
  const activeRunLabel = getUserFacingRecipeName(activeRecipeId)
  const gateTitle = hasActiveRun
    ? `${activeRunLabel} in progress`
    : hasScriptBreakdown
      ? 'Deep Breakdown needed first'
      : 'Script Breakdown needed first'
  const gateDescription = hasActiveRun
    ? activeRecipeId === 'mvp_ingest'
      ? 'We are standardizing your screenplay and extracting the script foundation now. When this finishes, the next step becomes Deep Breakdown.'
      : activeRecipeId === 'world_building'
        ? 'We are building character, location, and world artifacts now. This page unlocks fully as soon as the run finishes.'
        : `We are currently running ${activeRunLabel}. Additional creative controls will unlock when that run completes.`
    : hasScriptBreakdown
      ? 'To do that meaningfully, the system still needs your characters, locations, and story world. Run a Deep Breakdown next — it builds character bibles, location bibles, and an entity relationship graph that the creative direction can reference.'
      : 'To do that meaningfully, the system first needs a clean script foundation. Run a Script Breakdown first — it standardizes your screenplay, extracts scenes, and builds the script context that Deep Breakdown depends on.'
  const gateFootnote = hasActiveRun
    ? activeRecipeId === 'world_building'
      ? 'Building character, location, and world bibles from your screenplay'
      : 'Standardizing your screenplay and extracting the script foundation Deep Breakdown needs'
    : hasScriptBreakdown
      ? 'Builds character, location, and world bibles from your screenplay'
      : 'Standardizes your screenplay and extracts the script foundation Deep Breakdown needs'

  // --- Local form state ---
  const [moodTags, setMoodTags] = useState<string[]>([])
  const [refFilms, setRefFilms] = useState<string[]>([])
  const [filmmakerAnchors, setFilmmakerAnchors] = useState<string[]>([])
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [nlIntent, setNlIntent] = useState('')
  const [lookNotes, setLookNotes] = useState('')
  const [filmInput, setFilmInput] = useState('')
  const [filmmakerInput, setFilmmakerInput] = useState('')
  const [moodInput, setMoodInput] = useState('')
  const [propagation, setPropagation] = useState<PropagationResponse | null>(null)
  const [initialized, setInitialized] = useState(false)

  // Sync form from server data on first load
  if (currentIntent && !initialized) {
    setMoodTags(currentIntent.mood_descriptors)
    setRefFilms(currentIntent.reference_films)
    setFilmmakerAnchors(currentIntent.filmmaker_anchors)
    setSelectedPreset(currentIntent.style_preset_id)
    setNlIntent(currentIntent.natural_language_intent ?? '')
    setLookNotes(currentIntent.look_notes ?? '')
    setInitialized(true)
  }

  // --- Mutations ---
  const saveMutation = useMutation({
    mutationFn: () =>
      saveIntentMood(projectId!, {
        mood_descriptors: moodTags,
        reference_films: refFilms,
        filmmaker_anchors: filmmakerAnchors,
        style_preset_id: selectedPreset,
        natural_language_intent: nlIntent || null,
        look_notes: lookNotes || null,
        scope: 'project',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent-mood', projectId] })
      queryClient.invalidateQueries({ queryKey: ['creative-brief', projectId] })
      queryClient.invalidateQueries({ queryKey: ['artifact-groups', projectId] })
      toast.success('Intent saved')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const suggestMutation = useMutation({
    mutationFn: () => suggestIntentMood(projectId!),
    onSuccess: (data) => {
      setMoodTags(data.mood_descriptors)
      setRefFilms(data.reference_films)
      setFilmmakerAnchors(data.filmmaker_anchors)
      setSelectedPreset(data.style_preset_id)
      setNlIntent(data.natural_language_intent ?? '')
      setLookNotes(data.look_notes ?? '')
      toast.success('Suggestion applied — review and save when ready')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const propagateAction = useLongRunningAction({
    projectId: projectId!,
    label: 'Propagating creative intent',
    items: Object.values(CONCERN_GROUP_META).map(meta => ({ label: meta.label })),
    action: () => propagateMood(projectId!),
    onSuccess: (data, { chatMessageId }) => {
      setPropagation(data)
      queryClient.invalidateQueries({ queryKey: ['artifact-groups', projectId] })
      const created = data.artifacts_created
      toast.success(`Propagated to ${created.length} concern groups`)
      // Override default "all done" with per-group detail
      const store = useChatStore.getState()
      const items = Object.entries(CONCERN_GROUP_META).map(([groupId, meta]) => ({
        label: meta.label,
        status: 'done' as const,
        detail: created.includes(groupId) ? 'draft created' : 'skipped',
      }))
      store.updateMessageContent(
        projectId!,
        chatMessageId,
        JSON.stringify({ heading: 'Propagating creative intent', items }),
      )
      // Post summary
      const groupNames = created
        .map(id => CONCERN_GROUP_META[id]?.label ?? id)
        .join(', ')
      const summary = created.length > 0
        ? `Creative intent propagated to **${created.length} concern groups**: ${groupNames}. Review the suggestions below, or visit each scene's Direction tab to see how the mood shapes its visual and audio direction.`
        : 'Propagation complete — no concern group drafts were created. Try adjusting the mood or adding reference films.'
      store.addMessage(projectId!, {
        id: `propagate_summary_${Date.now()}`,
        type: 'ai_status_done',
        content: summary,
        timestamp: Date.now(),
        speaker: 'director',
      })
    },
    onError: (err) => toast.error(err.message),
  })

  // --- Handlers ---
  const selectPreset = useCallback((preset: StylePresetResponse) => {
    setSelectedPreset(preset.preset_id)
    setMoodTags(preset.mood_descriptors)
    setRefFilms(preset.reference_films)
  }, [])

  const addMoodTag = useCallback((tag: string) => {
    const clean = tag.trim().toLowerCase()
    if (clean && !moodTags.includes(clean)) {
      setMoodTags(prev => [...prev, clean])
    }
    setMoodInput('')
  }, [moodTags])

  const removeMoodTag = useCallback((tag: string) => {
    setMoodTags(prev => prev.filter(t => t !== tag))
  }, [])

  const addFilm = useCallback((film: string) => {
    const clean = film.trim()
    if (clean && !refFilms.includes(clean)) {
      setRefFilms(prev => [...prev, clean])
    }
    setFilmInput('')
  }, [refFilms])

  const removeFilm = useCallback((film: string) => {
    setRefFilms(prev => prev.filter(f => f !== film))
  }, [])

  const addFilmmaker = useCallback((name: string) => {
    const clean = name.trim()
    if (clean && !filmmakerAnchors.includes(clean)) {
      setFilmmakerAnchors(prev => [...prev, clean])
    }
    setFilmmakerInput('')
  }, [filmmakerAnchors])

  const removeFilmmaker = useCallback((name: string) => {
    setFilmmakerAnchors(prev => prev.filter(anchor => anchor !== name))
  }, [])

  const handleSaveAndPropagate = useCallback(async () => {
    await saveMutation.mutateAsync()
    propagateAction.start()
  }, [saveMutation, propagateAction])

  const hasChanges = (() => {
    if (!currentIntent) {
      return (
        moodTags.length > 0
        || refFilms.length > 0
        || filmmakerAnchors.length > 0
        || nlIntent.length > 0
        || lookNotes.length > 0
        || selectedPreset !== null
      )
    }
    return (
      JSON.stringify(moodTags) !== JSON.stringify(currentIntent.mood_descriptors) ||
      JSON.stringify(refFilms) !== JSON.stringify(currentIntent.reference_films) ||
      JSON.stringify(filmmakerAnchors) !== JSON.stringify(currentIntent.filmmaker_anchors) ||
      selectedPreset !== currentIntent.style_preset_id ||
      (nlIntent || null) !== (currentIntent.natural_language_intent || null) ||
      (lookNotes || null) !== (currentIntent.look_notes || null)
    )
  })()

  // --- Deep breakdown gate UI ---
  if (!hasDeepBreakdown) {
    return (
      <div className="w-full min-w-0 max-w-4xl space-y-8">
        <PageHeader
          title="Intent & Mood"
          subtitle="Set the creative vision for your project. Pick a vibe, describe the feeling, and let AI propagate it across all concern groups."
        />
        {projectId && (
          <VisualMediumCard
            projectId={projectId}
            value={project?.production_format ?? null}
          />
        )}
        <Card className="border-dashed border-amber-500/30 bg-amber-500/5">
          <CardContent className="py-8 space-y-5">
            <div className="flex items-start gap-4">
              <BookOpen className="h-10 w-10 text-amber-400 mt-0.5 shrink-0" />
              <div className="space-y-3">
                <CardTitle className="text-lg">{gateTitle}</CardTitle>
                <CardDescription className="text-sm leading-relaxed max-w-2xl">
                  Intent & Mood is the bridge between your <span className="text-foreground font-medium">story</span> and
                  the <span className="text-foreground font-medium">visual film</span>. It translates your creative
                  vision into direction for cinematography, sound, pacing, performance, and world-building.
                </CardDescription>
                <CardDescription className="text-sm leading-relaxed max-w-2xl">
                  {gateDescription}
                </CardDescription>
                {scriptContext && (
                  <p className="text-xs text-muted-foreground italic">
                    Your script: &ldquo;{scriptContext.title}&rdquo; — {scriptContext.genre.toLowerCase()}, {scriptContext.tone.toLowerCase()}
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-col items-start gap-3 pl-0 sm:flex-row sm:items-center sm:pl-14">
              <Button
                onClick={async () => {
                  if (!latestInputPath) {
                    toast.error('No script uploaded yet. Upload a screenplay first.')
                    return
                  }
                  try {
                    await startTrackedRun({
                      projectId: projectId!,
                      actionLabel: `Run ${requiredRunLabel}`,
                      startRun: startRun.mutateAsync,
                      payload: {
                        project_id: projectId!,
                        input_file: latestInputPath,
                        default_model: 'claude-sonnet-4-6',
                        recipe_id: requiredRecipeId,
                        accept_config: true,
                      },
                    })
                    toast.success(`${requiredRunLabel} started — this may take a few minutes`)
                  } catch (err) {
                    toast.error(err instanceof Error ? err.message : 'Failed to start run')
                  }
                }}
                disabled={deepBreakdownBlocked || !latestInputPath}
              >
                {deepBreakdownBlocked ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <BookOpen className="h-4 w-4 mr-2" />
                )}
                {deepBreakdownLabel}
              </Button>
              <span className="text-xs text-muted-foreground">
                {gateFootnote}
              </span>
            </div>
          </CardContent>
        </Card>
        {projectId && <ProjectReferencesSection projectId={projectId} />}
      </div>
    )
  }

  return (
      <div className="w-full min-w-0 max-w-4xl space-y-8">
      <PageHeader
        title="Intent & Mood"
        subtitle="Set the creative vision for your project. Pick a vibe, describe the feeling, and let AI propagate it across all concern groups."
      />
      {projectId && (
        <VisualMediumCard
          projectId={projectId}
          value={project?.production_format ?? null}
        />
      )}
      {projectId && <ProjectReferencesSection projectId={projectId} />}

      {/* Warm invitation — script context + suggest */}
      {!currentIntent && scriptContext && (
        <Card className="border-dashed border-purple-500/30 bg-purple-500/5">
          <CardContent className="py-6 space-y-4">
            <div className="flex items-start gap-3">
              <Compass className="h-8 w-8 text-purple-400 mt-0.5 shrink-0" />
              <div className="space-y-2">
                <CardTitle className="text-base">Ready to start the visual side?</CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  Your script analysis found that <span className="text-foreground font-medium">{scriptContext.title}</span> is
                  a <span className="text-foreground">{scriptContext.genre.toLowerCase()}</span> with
                  a <span className="text-foreground">{scriptContext.tone.toLowerCase()}</span> tone.
                  {scriptContext.themes.length > 0 && (
                    <> Themes include {scriptContext.themes.slice(0, 3).map((t, i, arr) => (
                      <span key={t}>
                        <span className="text-foreground">{t.toLowerCase()}</span>
                        {i < arr.length - 1 ? (i === arr.length - 2 ? ' and ' : ', ') : ''}
                      </span>
                    ))}.</>
                  )}
                </CardDescription>
                <p className="text-xs text-muted-foreground italic">
                  &ldquo;{scriptContext.logline}&rdquo;
                </p>
              </div>
            </div>
            <div className="flex flex-col items-start gap-3 pl-0 sm:flex-row sm:items-center sm:pl-11">
              <Button
                onClick={() => suggestMutation.mutate()}
                disabled={suggestMutation.isPending}
                size="sm"
              >
                {suggestMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-2" />
                )}
                Suggest a Vibe
              </Button>
              <span className="text-xs text-muted-foreground">
                or pick a style preset below
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fallback empty state — no script bible */}
      {!currentIntent && !scriptContext && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Compass className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <CardTitle className="text-lg mb-2">No intent set yet</CardTitle>
            <CardDescription>
              Pick a style preset below to get started, or describe your creative vision manually.
            </CardDescription>
          </CardContent>
        </Card>
      )}

      {/* Style Presets */}
      <section>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Style Presets</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {presets?.map(preset => (
            <button
              key={preset.preset_id}
              onClick={() => selectPreset(preset)}
              className={cn(
                'text-left rounded-lg border p-4 transition-all cursor-pointer',
                selectedPreset === preset.preset_id
                  ? 'border-primary bg-primary/5 ring-1 ring-primary'
                  : 'border-border hover:border-primary/50 hover:bg-accent/30',
              )}
            >
              <div className="text-2xl mb-2">{preset.thumbnail_emoji}</div>
              <div className="font-medium text-sm">{preset.display_name}</div>
              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {preset.description}
              </div>
            </button>
          ))}
        </div>
      </section>

      <Separator />

      <IntentTasteStackFields
        moodTags={moodTags}
        moodInput={moodInput}
        onMoodInputChange={setMoodInput}
        onAddMoodTag={addMoodTag}
        onRemoveMoodTag={removeMoodTag}
        moodSuggestions={MOOD_SUGGESTIONS}
        refFilms={refFilms}
        filmInput={filmInput}
        onFilmInputChange={setFilmInput}
        onAddFilm={addFilm}
        onRemoveFilm={removeFilm}
        filmmakerAnchors={filmmakerAnchors}
        filmmakerInput={filmmakerInput}
        onFilmmakerInputChange={setFilmmakerInput}
        onAddFilmmaker={addFilmmaker}
        onRemoveFilmmaker={removeFilmmaker}
        nlIntent={nlIntent}
        onNlIntentChange={setNlIntent}
        lookNotes={lookNotes}
        onLookNotesChange={setLookNotes}
      />

      <CreativeBriefPreviewCard brief={creativeBrief} isLoading={creativeBriefLoading} />

      {/* Action buttons */}
      <div className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || (!hasChanges && !!currentIntent)}
            variant="secondary"
          >
            {saveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Save
          </Button>
          <Button
            onClick={handleSaveAndPropagate}
            disabled={propagateAction.isRunning || saveMutation.isPending}
          >
            {propagateAction.isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Sparkles className="h-4 w-4 mr-2" />
            )}
            {propagateAction.isRunning
              ? 'Generating suggestions for all concern groups...'
              : 'Save & Propagate'}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Propagate uses AI to translate your mood and intent into specific creative direction
          for each concern group — Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, and Story World.
        </p>
      </div>

      {/* Propagation Preview */}
      {propagation && (
        <section className="space-y-4">
          <Separator />
          <div>
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Compass className="h-4 w-4 text-purple-400" />
              Propagation Results
            </h3>
            <p className="text-xs text-muted-foreground mt-1">{propagation.overall_rationale}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Confidence: {Math.round(propagation.confidence * 100)}%
            </p>
          </div>

          {Object.entries(CONCERN_GROUP_META).map(([groupId, meta]) => {
            const group = propagation[groupId as keyof PropagationResponse] as PropagatedGroupResponse | null
            if (!group) return null
            return (
              <PropagatedGroupCard
                key={groupId}
                groupId={groupId}
                label={meta.label}
                color={meta.color}
                group={group}
                created={propagation.artifacts_created.includes(groupId)}
              />
            )
          })}
        </section>
      )}

    </div>
  )
}

/** Expandable card showing propagated concern group suggestions. */
function PropagatedGroupCard({
  label,
  color,
  group,
  created,
}: {
  groupId?: string
  label: string
  color: string
  group: PropagatedGroupResponse
  created: boolean
}) {
  const [open, setOpen] = useState(true)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger className="w-full cursor-pointer">
          <CardHeader className="py-3 px-4">
            <div className="flex items-center gap-2">
              {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span className={cn('text-sm font-medium', color)}>{label}</span>
              <div className="flex-1" />
              {created && (
                <Badge variant="secondary" className="text-xs gap-1">
                  <Check className="h-3 w-3" />
                  Draft created
                </Badge>
              )}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 px-4 pb-4">
            <p className="text-xs text-muted-foreground mb-3 italic">{group.rationale}</p>
            <div className="space-y-2">
              {Object.entries(group.fields).map(([field, value]) => {
                if (field === 'user_approved' || field === 'scope' || field === 'scene_id') return null
                return (
                  <div key={field} className="text-sm">
                    <span className="text-muted-foreground font-mono text-xs">
                      {field.replace(/_/g, ' ')}:
                    </span>
                    <span className="ml-2 text-foreground">
                      {typeof value === 'string' ? value : JSON.stringify(value)}
                    </span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
