/**
 * DirectionAnnotation — Word/Google Docs style comment thread for creative direction.
 *
 * Renders a role's direction as an annotation card with:
 * - Role avatar/name and direction type badge
 * - Structured direction fields (pacing, transitions, coverage, etc.)
 * - Confidence indicator
 * - "Chat about this" button that opens chat with @role context
 *
 * Reusable for all direction types: editorial, visual, sound, performance.
 */
import { Scissors, Eye, Volume2, Drama, MessageSquare } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { useRightPanel } from '@/lib/right-panel'
import { askChatQuestion } from '@/lib/glossary'

// --- Direction type config ---

export type DirectionType = 'editorial' | 'visual' | 'sound' | 'performance'

const DIRECTION_CONFIG: Record<DirectionType, {
  icon: typeof Scissors
  color: string
  roleId: string
  roleName: string
  badgeClass: string
}> = {
  editorial: {
    icon: Scissors,
    color: 'text-pink-400',
    roleId: 'editorial_architect',
    roleName: 'Editorial Architect',
    badgeClass: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  },
  visual: {
    icon: Eye,
    color: 'text-sky-400',
    roleId: 'visual_architect',
    roleName: 'Visual Architect',
    badgeClass: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  },
  sound: {
    icon: Volume2,
    color: 'text-emerald-400',
    roleId: 'sound_designer',
    roleName: 'Sound Designer',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  performance: {
    icon: Drama,
    color: 'text-amber-400',
    roleId: 'actor_agent',
    roleName: 'Actor Agent',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
}

// --- Editorial direction fields ---

interface EditorialDirectionData {
  scene_function?: string
  pacing_intent?: string
  transition_in?: string
  transition_in_rationale?: string
  transition_out?: string
  transition_out_rationale?: string
  coverage_priority?: string
  montage_candidates?: string[]
  parallel_editing_notes?: string | null
  act_level_notes?: string | null
  confidence?: number
}

// --- Component ---

export function DirectionAnnotation({
  directionType,
  data,
  sceneHeading,
}: {
  directionType: DirectionType
  data: EditorialDirectionData
  sceneHeading?: string
}) {
  const panel = useRightPanel()
  const config = DIRECTION_CONFIG[directionType]
  const Icon = config.icon

  const handleChatAbout = (topic: string) => {
    if (!panel.state.open) panel.openChat()
    panel.setTab('chat')
    const sceneCtx = sceneHeading ? ` for scene "${sceneHeading}"` : ''
    askChatQuestion(
      `@${config.roleId} I'd like to discuss your ${directionType} direction${sceneCtx}: ${topic}`,
    )
  }

  const confidencePct = data.confidence != null ? Math.round(data.confidence * 100) : null

  return (
    <Card className="border-l-2" style={{ borderLeftColor: `var(--color-${directionType === 'editorial' ? 'pink' : directionType === 'visual' ? 'sky' : directionType === 'sound' ? 'emerald' : 'amber'}-500, hsl(var(--border)))` }}>
      <CardContent className="pt-4 space-y-3">
        {/* Header: role + type badge + confidence */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`rounded-md bg-card border border-border p-1.5 ${config.color}`}>
              <Icon className="h-3.5 w-3.5" />
            </div>
            <span className="text-sm font-medium">{config.roleName}</span>
            <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${config.badgeClass}`}>
              {directionType}
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
          {data.scene_function && (
            <DirectionField label="Scene Function" value={data.scene_function} onChat={handleChatAbout} />
          )}
          {data.pacing_intent && (
            <DirectionField label="Pacing" value={data.pacing_intent} onChat={handleChatAbout} />
          )}
          {data.coverage_priority && (
            <DirectionField label="Coverage Priority" value={data.coverage_priority} onChat={handleChatAbout} />
          )}
          {data.transition_in && (
            <TransitionField
              direction="in"
              type={data.transition_in}
              rationale={data.transition_in_rationale}
              onChat={handleChatAbout}
            />
          )}
          {data.transition_out && (
            <TransitionField
              direction="out"
              type={data.transition_out}
              rationale={data.transition_out_rationale}
              onChat={handleChatAbout}
            />
          )}
          {data.montage_candidates && data.montage_candidates.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Montage Candidates</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.montage_candidates.map((m, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">{m}</Badge>
                ))}
              </div>
            </div>
          )}
          {data.parallel_editing_notes && (
            <DirectionField label="Parallel Editing" value={data.parallel_editing_notes} onChat={handleChatAbout} />
          )}
          {data.act_level_notes && (
            <DirectionField label="Act Notes" value={data.act_level_notes} onChat={handleChatAbout} />
          )}
        </div>

        {/* Chat action */}
        <div className="pt-1">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => handleChatAbout(data.scene_function ?? 'this direction')}
          >
            <MessageSquare className="h-3 w-3" />
            Chat about this
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Sub-components ---

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

function TransitionField({
  direction,
  type,
  rationale,
  onChat,
}: {
  direction: 'in' | 'out'
  type: string
  rationale?: string
  onChat: (topic: string) => void
}) {
  const label = direction === 'in' ? 'Transition In' : 'Transition Out'
  return (
    <div className="group/field">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground shrink-0">{label}</span>
        <button
          onClick={() => onChat(`the ${label.toLowerCase()}: "${type}"`)}
          className="opacity-0 group-hover/field:opacity-100 transition-opacity text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
        >
          discuss
        </button>
      </div>
      <p className="text-foreground/90">
        <Badge variant="outline" className="text-xs mr-2 align-middle">{type}</Badge>
        {rationale && <span className="text-muted-foreground">{rationale}</span>}
      </p>
    </div>
  )
}
