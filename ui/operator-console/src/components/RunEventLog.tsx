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

// Mock data for development and testing
export const mockRunEvents: RunEvent[] = [
  {
    timestamp: Date.now() - 120000,
    type: 'info',
    message: 'Pipeline execution started',
    details: {
      run_id: 'run-20260215-143022',
      recipe: 'recipe-synthesis.yaml',
      project_id: 'shadowrun-revival',
    },
  },
  {
    timestamp: Date.now() - 118000,
    type: 'stage_start',
    stage: 'ingest',
    message: 'Stage started: ingest',
  },
  {
    timestamp: Date.now() - 115000,
    type: 'info',
    stage: 'ingest',
    message: 'Detected screenplay format: Final Draft XML',
    details: {
      file_size: '2.4 MB',
      pages: 112,
    },
  },
  {
    timestamp: Date.now() - 112000,
    type: 'stage_end',
    stage: 'ingest',
    message: 'Stage completed: ingest',
    details: {
      duration_ms: 6234,
      output_type: 'IngestedDocument',
    },
  },
  {
    timestamp: Date.now() - 110000,
    type: 'stage_start',
    stage: 'normalize',
    message: 'Stage started: normalize',
  },
  {
    timestamp: Date.now() - 108000,
    type: 'ai_call',
    stage: 'normalize',
    message: 'AI classification: detected screenplay',
    details: {
      model: 'claude-sonnet-4.5',
      input_tokens: 42180,
      output_tokens: 156,
      cost_usd: 0.127,
      confidence: 0.98,
    },
  },
  {
    timestamp: Date.now() - 105000,
    type: 'artifact_produced',
    stage: 'normalize',
    message: 'Produced artifact: ScreenplayStructured v1',
    details: {
      artifact_id: 'screenplay-structured-001',
      version: 1,
      scenes_count: 87,
    },
  },
  {
    timestamp: Date.now() - 104000,
    type: 'stage_end',
    stage: 'normalize',
    message: 'Stage completed: normalize',
    details: {
      duration_ms: 6182,
    },
  },
  {
    timestamp: Date.now() - 102000,
    type: 'stage_start',
    stage: 'extract_entities',
    message: 'Stage started: extract_entities',
  },
  {
    timestamp: Date.now() - 98000,
    type: 'ai_call',
    stage: 'extract_entities',
    message: 'Extracting characters and locations',
    details: {
      model: 'claude-opus-4.6',
      input_tokens: 58420,
      output_tokens: 3240,
      cost_usd: 1.456,
    },
  },
  {
    timestamp: Date.now() - 95000,
    type: 'error',
    stage: 'extract_entities',
    message: 'AI response truncated - retrying with increased token limit',
    details: {
      original_max_tokens: 4096,
      new_max_tokens: 8192,
    },
  },
  {
    timestamp: Date.now() - 92000,
    type: 'ai_call',
    stage: 'extract_entities',
    message: 'Retry: Extracting characters and locations',
    details: {
      model: 'claude-opus-4.6',
      input_tokens: 58420,
      output_tokens: 6840,
      cost_usd: 2.912,
      retry_attempt: 1,
    },
  },
  {
    timestamp: Date.now() - 88000,
    type: 'artifact_produced',
    stage: 'extract_entities',
    message: 'Produced artifact: EntityGraph v1',
    details: {
      artifact_id: 'entity-graph-001',
      version: 1,
      characters: 24,
      locations: 18,
      relationships: 67,
    },
  },
  {
    timestamp: Date.now() - 87000,
    type: 'stage_end',
    stage: 'extract_entities',
    message: 'Stage completed: extract_entities',
    details: {
      duration_ms: 15203,
    },
  },
  {
    timestamp: Date.now() - 85000,
    type: 'info',
    message: 'Pipeline execution completed successfully',
    details: {
      total_duration_ms: 35412,
      total_cost_usd: 4.495,
      artifacts_produced: 3,
    },
  },
]
