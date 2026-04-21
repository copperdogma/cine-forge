import type { LucideIcon } from 'lucide-react'
import {
  Clapperboard,
  Drama,
  Eye,
  Film,
  Globe,
  Image as ImageIcon,
  Scissors,
  Volume2,
  Wand2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { SceneWorkspaceTab } from '@/lib/constants'

type FocusTab = Exclude<SceneWorkspaceTab, 'overview'>

type FocusMeta = {
  label: string
  description: string
  icon: LucideIcon
  iconClassName: string
}

const FOCUS_META: Record<FocusTab, FocusMeta> = {
  look_and_feel: {
    label: 'Look & Feel',
    description:
      'This scene is already focused on visual direction. The selected panel below is where you review and generate the scene’s look, lighting, and framing cues.',
    icon: Eye,
    iconClassName: 'text-sky-400',
  },
  sound_and_music: {
    label: 'Sound & Music',
    description:
      'This scene is already focused on sound direction. The selected panel below is where you review and generate atmosphere, score, and sound-story decisions.',
    icon: Volume2,
    iconClassName: 'text-emerald-400',
  },
  rhythm_and_flow: {
    label: 'Rhythm & Flow',
    description:
      'This scene is already focused on pacing and editorial intent. The selected panel below is where you review and generate camera-energy and cut-shape guidance.',
    icon: Scissors,
    iconClassName: 'text-pink-400',
  },
  character_and_performance: {
    label: 'Performance',
    description:
      'This scene is already focused on character and performance direction. The selected panel below is where you review emotional beats, blocking, and acting guidance.',
    icon: Drama,
    iconClassName: 'text-amber-400',
  },
  story_world: {
    label: 'Story World',
    description:
      'This scene is already focused on story-world context. The selected panel below is where you review continuity, setting logic, and project-wide narrative support for this moment.',
    icon: Globe,
    iconClassName: 'text-teal-400',
  },
  shots: {
    label: 'Shots',
    description:
      'This scene is already focused on shot planning. The selected panel below is where CineForge builds and reviews the cuttable shot list for this scene.',
    icon: Clapperboard,
    iconClassName: 'text-violet-400',
  },
  storyboard: {
    label: 'Storyboard',
    description:
      'This scene is already focused on storyboards. The selected panel below is where shot plans turn into fast visual review frames.',
    icon: ImageIcon,
    iconClassName: 'text-fuchsia-400',
  },
  previz: {
    label: 'Previz',
    description:
      'This scene is already focused on AI previz. The selected panel below is where you review low-fidelity planning clips for pacing, blocking, and camera movement.',
    icon: Wand2,
    iconClassName: 'text-sky-300',
  },
  render: {
    label: 'Production',
    description:
      'This scene is already focused on final scene generation. The selected panel below is where CineForge shows render preflight, scene video, and trust artifacts.',
    icon: Film,
    iconClassName: 'text-rose-400',
  },
}

type SceneWorkspaceFocusBannerProps = {
  tab: FocusTab
  onJumpToPanel?: () => void
}

export function SceneWorkspaceFocusBanner({
  tab,
  onJumpToPanel,
}: SceneWorkspaceFocusBannerProps) {
  const meta = FOCUS_META[tab]
  const Icon = meta.icon

  return (
    <div className="rounded-2xl border border-border bg-card/80 px-4 py-4 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-border bg-muted/40 p-2.5">
            <Icon className={cn('h-5 w-5', meta.iconClassName)} />
          </div>
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Focused workspace</Badge>
              <span className="text-sm font-semibold text-foreground">{meta.label}</span>
            </div>
            <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
              {meta.description}
            </p>
          </div>
        </div>
        {onJumpToPanel && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="shrink-0 self-start"
            onClick={onJumpToPanel}
          >
            Jump to selected panel
          </Button>
        )}
      </div>
    </div>
  )
}
