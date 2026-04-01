import { Plus, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

interface IntentTasteStackFieldsProps {
  moodTags: string[]
  moodInput: string
  onMoodInputChange: (value: string) => void
  onAddMoodTag: (value: string) => void
  onRemoveMoodTag: (value: string) => void
  moodSuggestions: string[]
  refFilms: string[]
  filmInput: string
  onFilmInputChange: (value: string) => void
  onAddFilm: (value: string) => void
  onRemoveFilm: (value: string) => void
  filmmakerAnchors: string[]
  filmmakerInput: string
  onFilmmakerInputChange: (value: string) => void
  onAddFilmmaker: (value: string) => void
  onRemoveFilmmaker: (value: string) => void
  nlIntent: string
  onNlIntentChange: (value: string) => void
  lookNotes: string
  onLookNotesChange: (value: string) => void
}

function TagInputSection({
  title,
  placeholder,
  values,
  inputValue,
  onInputChange,
  onAdd,
  onRemove,
}: {
  title: string
  placeholder: string
  values: string[]
  inputValue: string
  onInputChange: (value: string) => void
  onAdd: (value: string) => void
  onRemove: (value: string) => void
}) {
  return (
    <section>
      <h3 className="text-sm font-medium text-muted-foreground mb-3">{title}</h3>
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {values.map(value => (
            <Badge key={value} variant="outline" className="gap-1 pr-1 text-sm">
              {value}
              <button
                onClick={() => onRemove(value)}
                className="ml-0.5 rounded-full p-0.5 hover:bg-destructive/20 cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && inputValue.trim()) {
              e.preventDefault()
              onAdd(inputValue)
            }
          }}
          placeholder={placeholder}
          className="text-sm"
        />
        {inputValue.trim() && (
          <Button size="sm" variant="ghost" className="h-8 px-2" onClick={() => onAdd(inputValue)}>
            <Plus className="h-3 w-3" />
          </Button>
        )}
      </div>
    </section>
  )
}

export function IntentTasteStackFields({
  moodTags,
  moodInput,
  onMoodInputChange,
  onAddMoodTag,
  onRemoveMoodTag,
  moodSuggestions,
  refFilms,
  filmInput,
  onFilmInputChange,
  onAddFilm,
  onRemoveFilm,
  filmmakerAnchors,
  filmmakerInput,
  onFilmmakerInputChange,
  onAddFilmmaker,
  onRemoveFilmmaker,
  nlIntent,
  onNlIntentChange,
  lookNotes,
  onLookNotesChange,
}: IntentTasteStackFieldsProps) {
  return (
    <>
      <section>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Mood Descriptors</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {moodTags.map(tag => (
            <Badge
              key={tag}
              variant="secondary"
              className="gap-1 pr-1 text-sm"
            >
              {tag}
              <button
                onClick={() => onRemoveMoodTag(tag)}
                className="ml-0.5 rounded-full p-0.5 hover:bg-destructive/20 cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          <div className="flex gap-1">
            <Input
              value={moodInput}
              onChange={e => onMoodInputChange(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && moodInput.trim()) {
                  e.preventDefault()
                  onAddMoodTag(moodInput)
                }
              }}
              placeholder="Add mood..."
              className="h-7 w-32 text-sm"
            />
            {moodInput.trim() && (
              <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => onAddMoodTag(moodInput)}>
                <Plus className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {moodSuggestions.filter(s => !moodTags.includes(s)).slice(0, 10).map(s => (
            <button
              key={s}
              onClick={() => onAddMoodTag(s)}
              className="text-xs px-2 py-0.5 rounded-full border border-dashed border-border text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors cursor-pointer"
            >
              + {s}
            </button>
          ))}
        </div>
      </section>

      <TagInputSection
        title="Reference Films"
        placeholder="Add film..."
        values={refFilms}
        inputValue={filmInput}
        onInputChange={onFilmInputChange}
        onAdd={onAddFilm}
        onRemove={onRemoveFilm}
      />

      <TagInputSection
        title="Filmmaker Anchors"
        placeholder="Add director or cinematographer..."
        values={filmmakerAnchors}
        inputValue={filmmakerInput}
        onInputChange={onFilmmakerInputChange}
        onAdd={onAddFilmmaker}
        onRemove={onRemoveFilmmaker}
      />

      <section>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Creative Direction</h3>
        <Textarea
          value={nlIntent}
          onChange={e => onNlIntentChange(e.target.value)}
          placeholder="Describe the feeling you want... e.g., 'Make this feel like a fading memory — warm but unreliable, with a sense of things slipping away'"
          className="min-h-[80px] text-sm"
        />
      </section>

      <section>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Look Notes</h3>
        <Textarea
          value={lookNotes}
          onChange={e => onLookNotesChange(e.target.value)}
          placeholder="Call out the visual taste that doesn't fit neatly into tags yet: lens mood, costume weathering, texture, palette drift, camera restraint, or anything else the brief should preserve."
          className="min-h-[96px] text-sm"
        />
      </section>
    </>
  )
}

