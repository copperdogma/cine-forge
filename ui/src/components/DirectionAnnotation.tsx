/**
 * DirectionAnnotation — Word/Google Docs style comment thread for creative direction.
 *
 * Renders a concern group's direction as an annotation card with:
 * - Role avatar/name and concern group badge
 * - Structured direction fields
 * - Confidence indicator
 * - "Chat about this" button that opens chat with @role context
 *
 * Supports all concern groups: rhythm_and_flow, look_and_feel, sound_and_music,
 * character_and_performance (ADR-003).
 */
import { Scissors, Eye, Volume2, Drama, MessageSquare } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { useRightPanel } from '@/lib/right-panel'
import { askChatQuestion } from '@/lib/glossary'

// --- Concern group config ---

export type ConcernGroupType = 'rhythm_and_flow' | 'look_and_feel' | 'sound_and_music' | 'character_and_performance'

const CONCERN_GROUP_CONFIG: Record<ConcernGroupType, {
  icon: typeof Scissors
  color: string
  roleId: string
  roleName: string
  label: string
  badgeClass: string
}> = {
  rhythm_and_flow: {
    icon: Scissors,
    color: 'text-pink-400',
    roleId: 'editorial_architect',
    roleName: 'Editorial Architect',
    label: 'Rhythm & Flow',
    badgeClass: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  },
  look_and_feel: {
    icon: Eye,
    color: 'text-sky-400',
    roleId: 'visual_architect',
    roleName: 'Visual Architect',
    label: 'Look & Feel',
    badgeClass: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  },
  sound_and_music: {
    icon: Volume2,
    color: 'text-emerald-400',
    roleId: 'sound_designer',
    roleName: 'Sound Designer',
    label: 'Sound & Music',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  character_and_performance: {
    icon: Drama,
    color: 'text-amber-400',
    roleId: 'story_editor',
    roleName: 'Story Editor',
    label: 'Character & Performance',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
}

// --- Component ---

export function DirectionAnnotation({
  concernGroup,
  data,
  sceneHeading,
}: {
  concernGroup: ConcernGroupType
  data: Record<string, unknown>
  sceneHeading?: string
}) {
  const panel = useRightPanel()
  const config = CONCERN_GROUP_CONFIG[concernGroup]
  const Icon = config.icon

  const handleChatAbout = (topic: string) => {
    if (!panel.state.open) panel.openChat()
    const sceneCtx = sceneHeading ? ` for scene "${sceneHeading}"` : ''
    askChatQuestion(
      `@${config.roleId} I'd like to discuss your ${config.label.toLowerCase()} direction${sceneCtx}: ${topic}`,
    )
  }

  const confidencePct = typeof data.confidence === 'number' ? Math.round(data.confidence * 100) : null

  // Build field list from data — render non-null string/list fields
  const fields = Object.entries(data).filter(([key, value]) => {
    if (['scope', 'scene_id', 'act_number', 'user_approved', 'confidence', 'character_id'].includes(key)) return false
    if (value === null || value === undefined || value === '') return false
    if (Array.isArray(value) && value.length === 0) return false
    return true
  })

  return (
    <Card className="border-l-2" style={{ borderLeftColor: `var(--color-${concernGroup === 'rhythm_and_flow' ? 'pink' : concernGroup === 'look_and_feel' ? 'sky' : concernGroup === 'sound_and_music' ? 'emerald' : 'amber'}-500, hsl(var(--border)))` }}>
      <CardContent className="pt-4 space-y-3">
        {/* Header: role + type badge + confidence */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`rounded-md bg-card border border-border p-1.5 ${config.color}`}>
              <Icon className="h-3.5 w-3.5" />
            </div>
            <span className="text-sm font-medium">{config.roleName}</span>
            <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${config.badgeClass}`}>
              {config.label}
            </Badge>
          </div>
          {confidencePct != null && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className={`text-xs font-mono ${confidencePct >= 80 ? 'text-emerald-400' : confidencePct >= 60 ? 'text-amber-400' : 'text-rose-400'}`}>
                  {confidencePct}%
                </span>
              </TooltipTrigger>
              <TooltipContent>Confidence score</TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Direction fields */}
        <div className="space-y-2.5 text-sm">
          {fields.map(([key, value]) => {
            const label = formatFieldLabel(key)
            if (Array.isArray(value)) {
              if (value.length === 0) return null
              // Check if array contains objects (motifs) vs strings
              if (typeof value[0] === 'object') {
                return (
                  <div key={key}>
                    <span className="text-xs text-muted-foreground">{label}</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {value.map((item, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {typeof item === 'object' && item !== null
                            ? (item as Record<string, unknown>).motif_name as string || JSON.stringify(item)
                            : String(item)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )
              }
              return (
                <div key={key}>
                  <span className="text-xs text-muted-foreground">{label}</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {value.map((v, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">{String(v)}</Badge>
                    ))}
                  </div>
                </div>
              )
            }
            return (
              <DirectionField
                key={key}
                label={label}
                value={String(value)}
                onChat={handleChatAbout}
              />
            )
          })}
        </div>

        {/* Chat action */}
        <div className="pt-1">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => handleChatAbout(config.label.toLowerCase())}
          >
            <MessageSquare className="h-3 w-3" />
            Chat about this
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Helpers ---

function formatFieldLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function DirectionField({
  label,
  value,
  onChat,
}: {
  label: string
  value: string
  onChat: (topic: string) => void
}) {
  return (
    <div className="group/field">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground shrink-0">{label}</span>
        <button
          onClick={() => onChat(`the ${label.toLowerCase()}: "${value}"`)}
          className="opacity-0 group-hover/field:opacity-100 transition-opacity text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
        >
          discuss
        </button>
      </div>
      <p className="text-foreground/90 leading-relaxed">{value}</p>
    </div>
  )
}
