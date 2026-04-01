import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { DesignStudyRound } from '@/lib/api'

const SOURCE_LABELS: Record<string, string> = {
  entity_bible: 'Entity Bible',
  directive: 'Directive',
  positive_refs: 'Positive Refs',
  negative_refs: 'Negative Refs',
  seed_image: 'Seed Image',
  learned_preferences: 'Learned Preferences',
  look_and_feel: 'Look & Feel',
  project_config: 'Project Config',
  intent_mood: 'Intent & Mood',
  project_references: 'Project References',
}

const SOURCE_ORDER = [
  'entity_bible',
  'look_and_feel',
  'project_config',
  'intent_mood',
  'project_references',
  'directive',
  'positive_refs',
  'negative_refs',
  'learned_preferences',
  'seed_image',
]

function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source.replaceAll('_', ' ')
}

function sortSources(sources: string[]): string[] {
  return [...sources].sort((left, right) => {
    const leftIndex = SOURCE_ORDER.indexOf(left)
    const rightIndex = SOURCE_ORDER.indexOf(right)
    const normalizedLeft = leftIndex === -1 ? SOURCE_ORDER.length : leftIndex
    const normalizedRight = rightIndex === -1 ? SOURCE_ORDER.length : rightIndex
    if (normalizedLeft !== normalizedRight) {
      return normalizedLeft - normalizedRight
    }
    return left.localeCompare(right)
  })
}

interface Props {
  round: DesignStudyRound
  defaultOpen?: boolean
}

export function DesignStudySourcesPanel({ round, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  const sources = sortSources(round.sources_used.length > 0 ? round.sources_used : ['entity_bible'])

  return (
    <div className="rounded-lg border border-border/70 bg-muted/20">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
      >
        <div>
          <p className="text-xs font-medium text-foreground">Sources used</p>
          <p className="text-xs text-muted-foreground">
            Prompt inputs captured for round {round.round_number}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px]">
            {sources.length}
          </Badge>
          {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </div>
      </button>
      {open && (
        <div className="space-y-3 border-t border-border/60 px-3 py-3">
          <div className="flex flex-wrap gap-1.5">
            {sources.map(source => (
              <Badge key={source} variant="secondary" className="text-[10px] tracking-wide">
                {sourceLabel(source)}
              </Badge>
            ))}
          </div>
          {round.creative_brief_preview && (
            <div className="space-y-2 rounded-md border border-border/60 bg-background/60 p-3">
              <p className="text-xs font-medium text-foreground">Compiled creative brief</p>
              <p className="text-xs text-muted-foreground">
                {round.creative_brief_preview.operator_preview}
              </p>
              {round.creative_brief_preview.summary_lines.length > 0 && (
                <div className="space-y-1">
                  {round.creative_brief_preview.summary_lines.map((line) => (
                    <p key={line} className="text-xs text-muted-foreground">
                      {line}
                    </p>
                  ))}
                </div>
              )}
              {round.creative_brief_preview.active_project_references.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-foreground">Active project references</p>
                  <div className="flex flex-wrap gap-1.5">
                    {round.creative_brief_preview.active_project_references.map((reference) => (
                      <Badge key={reference.asset_id} variant="outline" className="text-[10px]">
                        {reference.filename} · {reference.purpose}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {round.directive && (
            <p className="text-xs text-muted-foreground">
              Directive: <span className="text-foreground">"{round.directive}"</span>
            </p>
          )}
          {round.positive_refs.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-foreground">Positive references</p>
              <div className="flex flex-wrap gap-1.5">
                {round.positive_refs.map(filename => (
                  <Badge key={filename} variant="outline" className="font-mono text-[10px]">
                    {filename}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {round.negative_refs.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-foreground">Negative references</p>
              <div className="flex flex-wrap gap-1.5">
                {round.negative_refs.map(filename => (
                  <Badge key={filename} variant="outline" className="font-mono text-[10px]">
                    {filename}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {round.seed_image_filename && (
            <p className="text-xs text-muted-foreground">
              Seed image: <span className="font-mono text-foreground">{round.seed_image_filename}</span>
            </p>
          )}
          {round.learned_preferences_used.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-foreground">Applied learned preferences</p>
              {round.learned_preferences_used.map((line) => (
                <p key={line} className="text-xs text-muted-foreground">
                  {line}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
