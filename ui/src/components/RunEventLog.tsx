import { useState, useEffect, useRef } from 'react'
import {
  Play,
  CheckCircle2,
  Brain,
  Package,
  XCircle,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface RunEvent {
  timestamp: number // Unix ms
  type: 'stage_start' | 'stage_end' | 'ai_call' | 'artifact_produced' | 'error' | 'info' | 'warning'
  stage?: string // e.g., "normalize"
  message: string // Human-readable message
  details?: Record<string, unknown> // Expandable metadata (model used, cost, duration, etc.)
}

export interface RunEventLogProps {
  events: RunEvent[]
  autoScroll?: boolean // Default true - scroll to bottom on new events
  maxHeight?: string // Default "400px"
  className?: string
}

const eventConfig = {
  stage_start: {
    icon: Play,
    color: 'text-primary',
    bgColor: 'bg-primary/10',
  },
  stage_end: {
    icon: CheckCircle2,
    color: 'text-primary',
    bgColor: 'bg-primary/10',
  },
  ai_call: {
    icon: Brain,
    color: 'text-violet-400',
    bgColor: 'bg-violet-400/10',
  },
  artifact_produced: {
    icon: Package,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
  },
  error: {
    icon: XCircle,
    color: 'text-destructive',
    bgColor: 'bg-destructive/10',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bgColor: 'bg-amber-400/10',
  },
  info: {
    icon: Info,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted',
  },
} as const

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

interface EventItemProps {
  event: RunEvent
}

function EventItem({ event }: EventItemProps) {
  const [expanded, setExpanded] = useState(false)
  const config = eventConfig[event.type]
  const Icon = config.icon
  const hasDetails = event.details && Object.keys(event.details).length > 0

  return (
    <div className="flex gap-3 group">
      {/* Timeline line and icon */}
      <div className="flex flex-col items-center">
        <div className={cn('rounded-full p-1.5', config.bgColor)}>
          <Icon className={cn('w-3.5 h-3.5', config.color)} />
        </div>
        <div className="flex-1 w-px bg-border mt-2" />
      </div>

      {/* Event content */}
      <div className="flex-1 pb-4">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-xs font-mono text-muted-foreground">
            {formatTimestamp(event.timestamp)}
          </span>
          {event.stage && (
            <>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs font-medium text-muted-foreground">
                {event.stage}
              </span>
            </>
          )}
        </div>

        <div
          className={cn(
            'text-sm mt-1',
            event.type === 'error' && 'text-destructive',
            event.type === 'warning' && 'text-amber-400'
          )}
        >
          {event.message}
        </div>

        {hasDetails && (
          <div className="mt-2">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {expanded ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
              Details
            </button>

            {expanded && (
              <div className="mt-2 rounded-md bg-muted/50 border border-border p-3">
                <dl className="space-y-1.5">
                  {Object.entries(event.details!).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <dt className="text-xs font-mono text-muted-foreground min-w-[100px]">
                        {key}:
                      </dt>
                      <dd className="text-xs font-mono text-foreground">
                        {typeof value === 'object'
                          ? JSON.stringify(value, null, 2)
                          : String(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export function RunEventLog({
  events,
  autoScroll = true,
  maxHeight = '400px',
  className,
}: RunEventLogProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const prevEventCountRef = useRef(events.length)

  useEffect(() => {
    if (!autoScroll || !scrollContainerRef.current) return

    // Only auto-scroll if new events were added
    if (events.length > prevEventCountRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
    }

    prevEventCountRef.current = events.length
  }, [events, autoScroll])

  if (events.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-sm text-muted-foreground border rounded-md',
          className
        )}
        style={{ height: maxHeight }}
      >
        No events yet
      </div>
    )
  }

  return (
    <div className={cn('relative', className)}>
      {/* Fade overlay at top */}
      <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-background to-transparent pointer-events-none z-10" />

      <div
        ref={scrollContainerRef}
        className="overflow-y-auto scroll-smooth"
        style={{ maxHeight }}
      >
        <div className="p-4 pt-6">
          {events.map((event, index) => (
            <EventItem key={index} event={event} />
          ))}
        </div>
      </div>
    </div>
  )
}