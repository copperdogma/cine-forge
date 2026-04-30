import { AlertTriangle, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  formatDesignStudyFailureSummary,
  getDesignStudyFailureRows,
  getDesignStudyProgressText,
  getDesignStudyRoundStatus,
} from '@/lib/design-study-status'
import type { DesignStudyRound } from '@/lib/api'

interface Props {
  round: DesignStudyRound
}

export function DesignStudyRoundStatusPanel({ round }: Props) {
  const status = getDesignStudyRoundStatus(round)

  if (status === 'completed') {
    return null
  }

  if (status === 'generating') {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-sky-500/30 bg-sky-500/10 p-3 text-sm text-sky-100">
        <Loader2 className="mt-0.5 h-4 w-4 animate-spin" />
        <div>
          <p className="font-medium">{getDesignStudyProgressText(round)}</p>
          <p className="text-xs text-sky-100/75">
            This round is saved and will update here as provider images finish.
          </p>
        </div>
      </div>
    )
  }

  const failure = round.failure
  if (!failure) {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 h-4 w-4" />
        <div>
          <p className="font-medium">{getDesignStudyProgressText(round)}</p>
          <p className="text-xs opacity-80">No provider failure metadata was saved.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3">
      <div className="flex items-start gap-2 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 h-4 w-4" />
        <div>
          <p className="font-medium">{getDesignStudyProgressText(round)}</p>
          <p className="text-xs opacity-90">{formatDesignStudyFailureSummary(failure)}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {getDesignStudyFailureRows(failure).map(row => (
          <Badge key={row.label} variant="outline" className="text-[10px]">
            {row.label}: {row.value}
          </Badge>
        ))}
      </div>

      <div className="space-y-1.5 rounded-md border border-border/50 bg-background/60 p-2">
        <p className="text-xs font-medium text-foreground">Provider message</p>
        <p className="whitespace-pre-wrap text-xs text-muted-foreground">
          {failure.operator_message}
        </p>
      </div>

      <div className="space-y-1.5 rounded-md border border-border/50 bg-background/60 p-2">
        <p className="text-xs font-medium text-foreground">Prompt context</p>
        <p className="whitespace-pre-wrap font-mono text-xs text-muted-foreground">
          {failure.prompt_excerpt}
        </p>
      </div>
    </div>
  )
}
