import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

export interface ScriptBibleData {
  logline?: string
  synopsis?: string
  genre?: string
  tone?: string
  narrative_arc?: string
  protagonist_journey?: string
  central_conflict?: string
  setting_overview?: string
  act_structure?: { act_number: number; title: string; summary: string; turning_points: string[] }[]
  themes?: { theme: string; description: string; evidence: string[] }[]
}

function BibleThemes({ themes }: { themes: NonNullable<ScriptBibleData['themes']> }) {
  if (themes.length === 0) return null
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex flex-wrap gap-2">
        {themes.map(theme => (
          <Tooltip key={theme.theme}>
            <TooltipTrigger asChild>
              <Badge variant="outline" className="cursor-default border-indigo-500/20 text-indigo-300">
                {theme.theme}
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-xs text-xs">
              {theme.description}
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  )
}

function BibleStoryDetails({ bible }: { bible: ScriptBibleData }) {
  const details = [
    ['Central Conflict', bible.central_conflict],
    ['Protagonist Journey', bible.protagonist_journey],
    ['Narrative Arc', bible.narrative_arc],
    ['Setting', bible.setting_overview],
  ] as const
  if (!details.some(([, value]) => value)) return null
  return (
    <>
      <Separator className="opacity-30" />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {details.map(([label, value]) => value && (
          <div key={label}>
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</h3>
            <p className="leading-relaxed text-foreground/90">{value}</p>
          </div>
        ))}
      </div>
    </>
  )
}

function BibleActStructure({ acts }: { acts: NonNullable<ScriptBibleData['act_structure']> }) {
  if (acts.length === 0) return null
  return (
    <>
      <Separator className="opacity-30" />
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Act Structure</h3>
        <div className="space-y-3">
          {acts.map(act => (
            <div key={act.act_number} className="rounded-md border border-border/40 p-3">
              <div className="font-medium text-foreground/90">Act {act.act_number}: {act.title}</div>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{act.summary}</p>
              {act.turning_points.length > 0 && (
                <ul className="mt-1.5 list-inside list-disc space-y-0.5 text-sm text-muted-foreground">
                  {act.turning_points.map((point, index) => <li key={index}>{point}</li>)}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

export function ScriptBiblePanel({ bible }: { bible: ScriptBibleData }) {
  return (
    <div className="space-y-4 text-sm">
      {bible.tone && <p className="italic text-muted-foreground">{bible.tone}</p>}
      {bible.themes && <BibleThemes themes={bible.themes} />}
      {bible.synopsis && (
        <>
          <Separator className="opacity-30" />
          <div>
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Synopsis</h3>
            <p className="whitespace-pre-line break-words leading-relaxed text-foreground/90">{bible.synopsis}</p>
          </div>
        </>
      )}
      <BibleStoryDetails bible={bible} />
      {bible.act_structure && <BibleActStructure acts={bible.act_structure} />}
    </div>
  )
}
