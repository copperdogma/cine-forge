import { useMemo, useState } from 'react'
import { toast } from 'sonner'
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
import { Textarea } from '@/components/ui/textarea'
import { ArtifactReviewControls } from '@/components/ArtifactReviewControls'
import { useEditArtifact } from '@/lib/hooks'
import { Drama, Pencil, Plus, Trash2 } from 'lucide-react'

type CharacterPerformancePanelProps = {
  data: Record<string, unknown>
  projectId: string
  entityId: string
  sceneHeading?: string
  editable?: boolean
}

type PerformanceEntry = {
  character_id: string
  emotional_state_entering: string | null
  emotional_arc: string | null
  motivation: string | null
  subtext: string | null
  physical_notes: string | null
  key_beats: string[]
  relationship_dynamics: string | null
  dialogue_delivery_notes: string | null
  blocking_notes: string | null
}

type EntryFormState = {
  character_id: string
  emotional_state_entering: string
  emotional_arc: string
  motivation: string
  subtext: string
  physical_notes: string
  key_beats: string
  relationship_dynamics: string
  dialogue_delivery_notes: string
  blocking_notes: string
}

const EMPTY_FORM: EntryFormState = {
  character_id: '',
  emotional_state_entering: '',
  emotional_arc: '',
  motivation: '',
  subtext: '',
  physical_notes: '',
  key_beats: '',
  relationship_dynamics: '',
  dialogue_delivery_notes: '',
  blocking_notes: '',
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

function parseEntry(value: unknown): PerformanceEntry | null {
  const record = asRecord(value)
  const character_id = asString(record?.character_id)
  if (!character_id) return null
  return {
    character_id,
    emotional_state_entering: asString(record?.emotional_state_entering),
    emotional_arc: asString(record?.emotional_arc),
    motivation: asString(record?.motivation),
    subtext: asString(record?.subtext),
    physical_notes: asString(record?.physical_notes),
    key_beats: asStringArray(record?.key_beats),
    relationship_dynamics: asString(record?.relationship_dynamics),
    dialogue_delivery_notes: asString(record?.dialogue_delivery_notes),
    blocking_notes: asString(record?.blocking_notes),
  }
}

function toFormState(entry: PerformanceEntry): EntryFormState {
  return {
    character_id: entry.character_id,
    emotional_state_entering: entry.emotional_state_entering ?? '',
    emotional_arc: entry.emotional_arc ?? '',
    motivation: entry.motivation ?? '',
    subtext: entry.subtext ?? '',
    physical_notes: entry.physical_notes ?? '',
    key_beats: entry.key_beats.join(', '),
    relationship_dynamics: entry.relationship_dynamics ?? '',
    dialogue_delivery_notes: entry.dialogue_delivery_notes ?? '',
    blocking_notes: entry.blocking_notes ?? '',
  }
}

function toPayloadEntry(form: EntryFormState, sceneId: string): Record<string, unknown> {
  const normalized = (value: string) => value.trim() || null
  return {
    scene_id: sceneId,
    character_id: form.character_id.trim(),
    emotional_state_entering: normalized(form.emotional_state_entering),
    emotional_arc: normalized(form.emotional_arc),
    motivation: normalized(form.motivation),
    subtext: normalized(form.subtext),
    physical_notes: normalized(form.physical_notes),
    key_beats: form.key_beats
      .split(',')
      .map(item => item.trim())
      .filter(Boolean),
    relationship_dynamics: normalized(form.relationship_dynamics),
    dialogue_delivery_notes: normalized(form.dialogue_delivery_notes),
    blocking_notes: normalized(form.blocking_notes),
    user_approved: false,
  }
}

function EntryCard({
  entry,
  editable,
  onEdit,
  onDelete,
}: {
  entry: PerformanceEntry
  editable: boolean
  onEdit: () => void
  onDelete: () => void
}) {
  const sections = [
    ['Emotional Entry', entry.emotional_state_entering],
    ['Emotional Arc', entry.emotional_arc],
    ['Motivation', entry.motivation],
    ['Subtext', entry.subtext],
    ['Physical Notes', entry.physical_notes],
    ['Relationship Dynamics', entry.relationship_dynamics],
    ['Dialogue Delivery', entry.dialogue_delivery_notes],
    ['Blocking', entry.blocking_notes],
  ].filter(([, value]) => value) as Array<[string, string]>

  return (
    <div className="rounded-xl border border-border bg-card/60 p-4 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{entry.character_id}</Badge>
            {entry.key_beats.length > 0 && (
              <Badge variant="outline">{entry.key_beats.length} key beat{entry.key_beats.length === 1 ? '' : 's'}</Badge>
            )}
          </div>
          {sections.length === 0 ? (
            <p className="text-sm text-muted-foreground">No directed notes yet.</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {sections.map(([label, value]) => (
                <div key={label} className="space-y-1">
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-sm leading-relaxed text-foreground/90">{value}</p>
                </div>
              ))}
            </div>
          )}
          {entry.key_beats.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Key Beats</p>
              <div className="flex flex-wrap gap-1.5">
                {entry.key_beats.map((beat, index) => (
                  <Badge key={`${entry.character_id}-${index}`} variant="outline">
                    {beat}
                  </Badge>
                ))}
              </div>
            </div>
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

export function CharacterPerformancePanel({
  data,
  projectId,
  entityId,
  sceneHeading,
  editable = true,
}: CharacterPerformancePanelProps) {
  const editArtifact = useEditArtifact()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [form, setForm] = useState<EntryFormState>(EMPTY_FORM)

  const entries = useMemo(
    () => (Array.isArray(data.entries) ? data.entries : [])
      .map(parseEntry)
      .filter((item): item is PerformanceEntry => item !== null),
    [data],
  )
  const userApproved = Boolean(data.user_approved)
  const sceneId = asString(data.scene_id) ?? entityId

  function openCreate() {
    setEditingIndex(null)
    setForm(EMPTY_FORM)
    setDialogOpen(true)
  }

  function openEdit(index: number) {
    const entry = entries[index]
    if (!entry) return
    setEditingIndex(index)
    setForm(toFormState(entry))
    setDialogOpen(true)
  }

  async function persist(nextEntries: Record<string, unknown>[], rationale: string, nextApproved = userApproved) {
    await editArtifact.mutateAsync({
      projectId,
      artifactType: 'character_and_performance',
      entityId,
      payload: {
        data: {
          ...data,
          scene_id: sceneId,
          entries: nextEntries,
          user_approved: nextApproved,
        },
        rationale,
      },
    })
  }

  async function handleSave() {
    if (!form.character_id.trim()) return
    const nextEntry = toPayloadEntry(form, sceneId)
    const nextEntries = entries.map((entry) => toPayloadEntry(toFormState(entry), sceneId))
    if (editingIndex === null) nextEntries.push(nextEntry)
    else nextEntries[editingIndex] = nextEntry

    try {
      await persist(
        nextEntries,
        editingIndex === null
          ? `Add Character & Performance entry for ${form.character_id.trim()}`
          : `Update Character & Performance entry for ${form.character_id.trim()}`,
      )
      toast.success(editingIndex === null ? 'Performance entry added' : 'Performance entry updated')
      setDialogOpen(false)
      setEditingIndex(null)
      setForm(EMPTY_FORM)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save performance entry')
    }
  }

  async function handleDelete(index: number) {
    const entry = entries[index]
    if (!entry) return
    const nextEntries = entries
      .filter((_, currentIndex) => currentIndex !== index)
      .map((item) => toPayloadEntry(toFormState(item), sceneId))

    try {
      await persist(nextEntries, `Remove Character & Performance entry for ${entry.character_id}`)
      toast.success('Performance entry removed')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to remove performance entry')
    }
  }

  const canSave = form.character_id.trim().length > 0

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Drama className="h-4 w-4 text-amber-400" />
                Character & Performance
              </CardTitle>
              <CardDescription>
                {sceneHeading
                  ? `Scene-level playable direction for ${sceneHeading}.`
                  : 'Scene-level playable direction for the current scene.'}
              </CardDescription>
            </div>
            <ArtifactReviewControls
              projectId={projectId}
              artifactType="character_and_performance"
              entityId={entityId}
              data={data}
              label="Character & Performance"
              editable={editable}
              extraBadges={(
                <Badge variant="outline">
                  {entries.length} character entr{entries.length === 1 ? 'y' : 'ies'}
                </Badge>
              )}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {editable && (
            <Button variant="outline" size="sm" className="gap-1.5" onClick={openCreate}>
              <Plus className="h-3.5 w-3.5" />
              Add character direction
            </Button>
          )}
          {entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No performance entries yet. Generate the stage or add a character note manually.
            </p>
          ) : (
            entries.map((entry, index) => (
              <EntryCard
                key={`${entry.character_id}-${index}`}
                entry={entry}
                editable={editable}
                onEdit={() => openEdit(index)}
                onDelete={() => handleDelete(index)}
              />
            ))
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingIndex === null ? 'Add character direction' : 'Edit character direction'}
            </DialogTitle>
            <DialogDescription>
              Capture playable performance notes for one character in this scene.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3">
            <Input
              value={form.character_id}
              onChange={event => setForm(current => ({ ...current, character_id: event.target.value }))}
              placeholder="character_id"
            />
            <Textarea
              value={form.emotional_state_entering}
              onChange={event => setForm(current => ({ ...current, emotional_state_entering: event.target.value }))}
              placeholder="Emotional state entering"
            />
            <Textarea
              value={form.emotional_arc}
              onChange={event => setForm(current => ({ ...current, emotional_arc: event.target.value }))}
              placeholder="Emotional arc through the scene"
            />
            <Textarea
              value={form.motivation}
              onChange={event => setForm(current => ({ ...current, motivation: event.target.value }))}
              placeholder="Motivation"
            />
            <Textarea
              value={form.subtext}
              onChange={event => setForm(current => ({ ...current, subtext: event.target.value }))}
              placeholder="Subtext"
            />
            <Textarea
              value={form.physical_notes}
              onChange={event => setForm(current => ({ ...current, physical_notes: event.target.value }))}
              placeholder="Physical notes"
            />
            <Input
              value={form.key_beats}
              onChange={event => setForm(current => ({ ...current, key_beats: event.target.value }))}
              placeholder="Key beats, comma separated"
            />
            <Textarea
              value={form.relationship_dynamics}
              onChange={event => setForm(current => ({ ...current, relationship_dynamics: event.target.value }))}
              placeholder="Relationship dynamics"
            />
            <Textarea
              value={form.dialogue_delivery_notes}
              onChange={event => setForm(current => ({ ...current, dialogue_delivery_notes: event.target.value }))}
              placeholder="Dialogue delivery notes"
            />
            <Textarea
              value={form.blocking_notes}
              onChange={event => setForm(current => ({ ...current, blocking_notes: event.target.value }))}
              placeholder="Blocking notes"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button disabled={!canSave || editArtifact.isPending} onClick={handleSave}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
