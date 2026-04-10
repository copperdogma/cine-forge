import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  Film,
  Globe,
  Music4,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { useEditArtifact } from '@/lib/hooks'

type StoryWorldPanelProps = {
  data: Record<string, unknown>
  projectId: string
  entityId: string
  editable?: boolean
}

type MotifScope = 'world' | 'character' | 'location' | 'prop' | 'scene'
type MotifKind = 'visual' | 'audio'

type MotifItem = {
  motif_name: string
  description: string
  scope: MotifScope
  entity_id: string | null
  scene_refs: string[]
}

type MotifFormState = {
  motif_name: string
  description: string
  scope: MotifScope
  entity_id: string
  scene_refs: string
}

const EMPTY_FORM: MotifFormState = {
  motif_name: '',
  description: '',
  scope: 'world',
  entity_id: '',
  scene_refs: '',
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map(item => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

function parseMotif(value: unknown): MotifItem | null {
  const record = asRecord(value)
  const motif_name = asString(record?.motif_name)
  const description = asString(record?.description)
  const rawScope = asString(record?.scope)
  const scope: MotifScope = (
    rawScope === 'world'
    || rawScope === 'character'
    || rawScope === 'location'
    || rawScope === 'prop'
    || rawScope === 'scene'
  )
    ? rawScope
    : 'world'
  if (!motif_name || !description) return null
  return {
    motif_name,
    description,
    scope,
    entity_id: asString(record?.entity_id),
    scene_refs: asStringArray(record?.scene_refs),
  }
}

function toFormState(motif: MotifItem): MotifFormState {
  return {
    motif_name: motif.motif_name,
    description: motif.description,
    scope: motif.scope,
    entity_id: motif.entity_id ?? '',
    scene_refs: motif.scene_refs.join(', '),
  }
}

function toPayloadMotif(form: MotifFormState): MotifItem {
  return {
    motif_name: form.motif_name.trim(),
    description: form.description.trim(),
    scope: form.scope,
    entity_id: form.entity_id.trim() || null,
    scene_refs: form.scene_refs
      .split(',')
      .map(item => item.trim())
      .filter(Boolean),
  }
}

function MotifCard({
  motif,
  kind,
  onEdit,
  onDelete,
  editable,
}: {
  motif: MotifItem
  kind: MotifKind
  onEdit: () => void
  onDelete: () => void
  editable: boolean
}) {
  return (
    <div className="rounded-xl border border-border bg-card/60 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{motif.motif_name}</Badge>
            <Badge variant="outline" className="capitalize">{motif.scope}</Badge>
            {motif.entity_id && <Badge variant="outline">{motif.entity_id}</Badge>}
            <Badge variant="outline">{kind === 'visual' ? 'Visual' : 'Audio'}</Badge>
          </div>
          <p className="text-sm leading-relaxed text-foreground/90">{motif.description}</p>
          {motif.scene_refs.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Scene refs: {motif.scene_refs.join(', ')}
            </p>
          )}
        </div>

        {editable && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1.5" onClick={onEdit}>
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={onDelete}>
              <Trash2 className="h-3.5 w-3.5" />
              Remove
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

function MotifSection({
  title,
  description,
  kind,
  motifs,
  editable,
  onAdd,
  onEdit,
  onDelete,
}: {
  title: string
  description: string
  kind: MotifKind
  motifs: MotifItem[]
  editable: boolean
  onAdd: () => void
  onEdit: (index: number) => void
  onDelete: (index: number) => void
}) {
  const Icon = kind === 'visual' ? Film : Music4

  return (
    <Card className="gap-0">
      <CardHeader className="pb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base">
              <Icon className="h-4 w-4" />
              {title}
            </CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {editable && (
            <Button variant="outline" size="sm" className="gap-1.5" onClick={onAdd}>
              <Plus className="h-3.5 w-3.5" />
              Add motif
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {motifs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No {kind} motifs tracked yet.
          </p>
        ) : (
          motifs.map((motif, index) => (
            <MotifCard
              key={`${kind}-${motif.motif_name}-${index}`}
              motif={motif}
              kind={kind}
              editable={editable}
              onEdit={() => onEdit(index)}
              onDelete={() => onDelete(index)}
            />
          ))
        )}
      </CardContent>
    </Card>
  )
}

export function StoryWorldPanel({
  data,
  projectId,
  entityId,
  editable = true,
}: StoryWorldPanelProps) {
  const editArtifact = useEditArtifact()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingKind, setEditingKind] = useState<MotifKind>('visual')
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [form, setForm] = useState<MotifFormState>(EMPTY_FORM)

  const storyWorld = useMemo(() => ({
    characterDesignBaselines: asStringArray(data.character_design_baselines),
    locationDesignBaselines: asStringArray(data.location_design_baselines),
    propDesignBaselines: asStringArray(data.prop_design_baselines),
    continuityOverrideNotes: asString(data.continuity_override_notes),
    characterBehavioralConsistencyNotes: asString(data.character_behavioral_consistency_notes),
    narrativeRhythmNotes: asString(data.narrative_rhythm_notes),
    userApproved: Boolean(data.user_approved),
  }), [data])

  const visualMotifs = useMemo(
    () => (Array.isArray(data.visual_motif_annotations) ? data.visual_motif_annotations : [])
      .map(parseMotif)
      .filter((item): item is MotifItem => item !== null),
    [data],
  )
  const audioMotifs = useMemo(
    () => (Array.isArray(data.audio_motif_annotations) ? data.audio_motif_annotations : [])
      .map(parseMotif)
      .filter((item): item is MotifItem => item !== null),
    [data],
  )

  function openCreate(kind: MotifKind) {
    setEditingKind(kind)
    setEditingIndex(null)
    setForm(EMPTY_FORM)
    setDialogOpen(true)
  }

  function openEdit(kind: MotifKind, index: number) {
    const source = kind === 'visual' ? visualMotifs : audioMotifs
    const motif = source[index]
    if (!motif) return
    setEditingKind(kind)
    setEditingIndex(index)
    setForm(toFormState(motif))
    setDialogOpen(true)
  }

  async function persistMotifs(
    nextVisualMotifs: MotifItem[],
    nextAudioMotifs: MotifItem[],
    rationale: string,
  ) {
    await editArtifact.mutateAsync({
      projectId,
      artifactType: 'story_world',
      entityId,
      payload: {
        data: {
          ...data,
          visual_motif_annotations: nextVisualMotifs,
          audio_motif_annotations: nextAudioMotifs,
        },
        rationale,
      },
    })
  }

  async function handleSaveMotif() {
    const nextMotif = toPayloadMotif(form)
    if (!nextMotif.motif_name || !nextMotif.description) return

    const nextVisualMotifs = [...visualMotifs]
    const nextAudioMotifs = [...audioMotifs]
    const target = editingKind === 'visual' ? nextVisualMotifs : nextAudioMotifs

    if (editingIndex === null) {
      target.push(nextMotif)
    } else {
      target[editingIndex] = nextMotif
    }

    try {
      await persistMotifs(
        nextVisualMotifs,
        nextAudioMotifs,
        editingIndex === null
          ? `Add ${editingKind} motif "${nextMotif.motif_name}" to Story World`
          : `Update ${editingKind} motif "${nextMotif.motif_name}" in Story World`,
      )
      toast.success(editingIndex === null ? 'Motif added' : 'Motif updated')
      setDialogOpen(false)
      setForm(EMPTY_FORM)
      setEditingIndex(null)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save motif')
    }
  }

  async function handleDelete(kind: MotifKind, index: number) {
    const source = kind === 'visual' ? visualMotifs : audioMotifs
    const nextVisualMotifs = [...visualMotifs]
    const nextAudioMotifs = [...audioMotifs]
    const motif = source[index]
    if (!motif) return

    if (kind === 'visual') nextVisualMotifs.splice(index, 1)
    else nextAudioMotifs.splice(index, 1)

    try {
      await persistMotifs(
        nextVisualMotifs,
        nextAudioMotifs,
        `Remove ${kind} motif "${motif.motif_name}" from Story World`,
      )
      toast.success('Motif removed')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to remove motif')
    }
  }

  const canSave = form.motif_name.trim().length > 0 && form.description.trim().length > 0
  const noteBlocks = [
    storyWorld.continuityOverrideNotes && {
      label: 'Continuity Overrides',
      value: storyWorld.continuityOverrideNotes,
    },
    storyWorld.characterBehavioralConsistencyNotes && {
      label: 'Behavioral Consistency',
      value: storyWorld.characterBehavioralConsistencyNotes,
    },
    storyWorld.narrativeRhythmNotes && {
      label: 'Narrative Rhythm',
      value: storyWorld.narrativeRhythmNotes,
    },
  ].filter(Boolean) as Array<{ label: string; value: string }>

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-teal-400" />
                Story World
              </CardTitle>
              <CardDescription>
                Project-wide baselines and recurring motifs that downstream visual, audio, and
                shot-planning passes should keep carrying forward.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={storyWorld.userApproved ? 'default' : 'outline'}>
                {storyWorld.userApproved ? 'Approved' : 'Draft'}
              </Badge>
              <Badge variant="outline">
                {visualMotifs.length + audioMotifs.length} tracked motif
                {visualMotifs.length + audioMotifs.length === 1 ? '' : 's'}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-xl border border-border bg-card/50 p-3">
              <p className="text-xs text-muted-foreground">Character baselines</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {storyWorld.characterDesignBaselines.length > 0 ? (
                  storyWorld.characterDesignBaselines.map(item => (
                    <Badge key={item} variant="secondary">{item}</Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">None linked yet</span>
                )}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card/50 p-3">
              <p className="text-xs text-muted-foreground">Location baselines</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {storyWorld.locationDesignBaselines.length > 0 ? (
                  storyWorld.locationDesignBaselines.map(item => (
                    <Badge key={item} variant="secondary">{item}</Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">None linked yet</span>
                )}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card/50 p-3">
              <p className="text-xs text-muted-foreground">Prop baselines</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {storyWorld.propDesignBaselines.length > 0 ? (
                  storyWorld.propDesignBaselines.map(item => (
                    <Badge key={item} variant="secondary">{item}</Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">None linked yet</span>
                )}
              </div>
            </div>
          </div>

          {noteBlocks.length > 0 && (
            <>
              <Separator />
              <div className="grid gap-3 md:grid-cols-3">
                {noteBlocks.map(note => (
                  <div key={note.label} className="rounded-xl border border-border bg-card/50 p-3">
                    <p className="text-xs text-muted-foreground">{note.label}</p>
                    <p className="mt-2 text-sm leading-relaxed text-foreground/90">{note.value}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <MotifSection
        title="Visual Motifs"
        description="Recurring images, objects, textures, or design ideas with thematic weight."
        kind="visual"
        motifs={visualMotifs}
        editable={editable}
        onAdd={() => openCreate('visual')}
        onEdit={(index) => openEdit('visual', index)}
        onDelete={(index) => handleDelete('visual', index)}
      />

      <MotifSection
        title="Audio Motifs"
        description="Recurring sounds, hums, silences, or sonic signatures that should persist."
        kind="audio"
        motifs={audioMotifs}
        editable={editable}
        onAdd={() => openCreate('audio')}
        onEdit={(index) => openEdit('audio', index)}
        onDelete={(index) => handleDelete('audio', index)}
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingIndex === null ? 'Add motif' : 'Edit motif'}
            </DialogTitle>
            <DialogDescription>
              Save through the normal artifact edit path so Story World remains versioned and
              traceable.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">Motif type</p>
                <Select
                  value={editingKind}
                  onValueChange={(value) => setEditingKind(value as MotifKind)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="visual">Visual</SelectItem>
                    <SelectItem value="audio">Audio</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">Scope</p>
                <Select
                  value={form.scope}
                  onValueChange={(value) =>
                    setForm(prev => ({ ...prev, scope: value as MotifScope }))
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="world">World</SelectItem>
                    <SelectItem value="character">Character</SelectItem>
                    <SelectItem value="location">Location</SelectItem>
                    <SelectItem value="prop">Prop</SelectItem>
                    <SelectItem value="scene">Scene</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground">Motif name</p>
              <Input
                value={form.motif_name}
                onChange={event => setForm(prev => ({ ...prev, motif_name: event.target.value }))}
                placeholder="Threshold Glass"
              />
            </div>

            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground">Thematic meaning</p>
              <Textarea
                value={form.description}
                onChange={event => setForm(prev => ({ ...prev, description: event.target.value }))}
                placeholder="Transparent barriers mark the line between control and consequence."
                rows={4}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">Entity or scene ID</p>
                <Input
                  value={form.entity_id}
                  onChange={event => setForm(prev => ({ ...prev, entity_id: event.target.value }))}
                  placeholder="Optional unless scope is entity- or scene-specific"
                />
              </div>
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">Scene refs</p>
                <Input
                  value={form.scene_refs}
                  onChange={event => setForm(prev => ({ ...prev, scene_refs: event.target.value }))}
                  placeholder="scene_001, scene_004"
                />
              </div>
            </div>

            <div className="rounded-xl border border-dashed border-border bg-muted/30 p-3 text-xs text-muted-foreground">
              <div className="flex items-start gap-2">
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <p>
                  Keep motifs specific and repeatable. A good motif is something downstream tools
                  can deliberately carry forward, not just a general mood adjective.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveMotif}
              disabled={!canSave || editArtifact.isPending}
            >
              {editingIndex === null ? 'Add motif' : 'Save changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
