import { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  CircleCheckBig,
  Sparkles,
  Wand2,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import {
  useOverrideArtifactHealth,
  usePreviewImpactScope,
  useRunImpactAssessment,
} from '@/lib/hooks'
import { healthDescription, healthLabel } from '@/lib/health'
import { useChatStore } from '@/lib/chat-store'
import { useLongRunningAction } from '@/lib/use-long-running-action'
import type {
  ArtifactHealthDetails,
  ArtifactRef,
  ImpactAssessmentResponse,
  ImpactPreviewResponse,
} from '@/lib/types'

type Props = {
  projectId: string
  artifactRef: ArtifactRef
  health: string | null | undefined
  details?: ArtifactHealthDetails | null
  isLatestVersion: boolean
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value)
}

function formatArtifactRef(ref?: ArtifactRef | null): string {
  if (!ref) return 'Unknown artifact'
  const entity = ref.entity_id ?? 'project'
  return `${ref.artifact_type}:${entity}:v${ref.version}`
}

function renderPreviewTargets(preview: ImpactPreviewResponse, currentRef: ArtifactRef) {
  const targets = preview.targets.slice(0, 6)
  return (
    <div className="space-y-2">
      {targets.map((target) => {
        const isCurrent = target.artifact_ref.path === currentRef.path
        return (
          <div
            key={target.artifact_ref.path}
            className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
          >
            <div>
              <div className="font-medium">
                {target.artifact_type}
                {target.entity_id ? ` · ${target.entity_id}` : ''}
              </div>
              <div className="text-xs text-muted-foreground">
                {formatArtifactRef(target.artifact_ref)}
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              {isCurrent ? 'Current artifact' : target.current_health}
            </div>
          </div>
        )
      })}
      {preview.targets.length > targets.length && (
        <p className="text-xs text-muted-foreground">
          Showing {targets.length} of {preview.targets.length} affected artifacts.
        </p>
      )}
    </div>
  )
}

export function ImpactAssessmentCard({
  projectId,
  artifactRef,
  health,
  details,
  isLatestVersion,
}: Props) {
  const [manualRationale, setManualRationale] = useState('')
  const [budgetCapUsd, setBudgetCapUsd] = useState('')
  const previewMutation = usePreviewImpactScope()
  const assessMutation = useRunImpactAssessment()
  const overrideMutation = useOverrideArtifactHealth()

  function getBudgetCapUsd(): number | null {
    const trimmed = budgetCapUsd.trim()
    if (!trimmed) {
      return null
    }
    const parsed = Number(trimmed)
    if (!Number.isFinite(parsed) || parsed <= 0) {
      throw new Error('Budget cap must be a positive USD amount, or leave it blank.')
    }
    return parsed
  }

  function updateAssessmentChat(
    title: string,
    result: ImpactAssessmentResponse,
    chatMessageId: string,
  ) {
    const store = useChatStore.getState()
    store.updateMessageContent(
      projectId,
      chatMessageId,
      `${title} — complete: ${result.assessment.assessments.length} artifact${result.assessment.assessments.length === 1 ? '' : 's'} assessed, ${result.assessment.total_needs_revision} need revision, ${result.assessment.total_confirmed_valid} confirmed valid.`,
    )
  }

  const assessCurrentAction = useLongRunningAction({
    projectId,
    label: 'Assessing artifact impact',
    action: async () =>
      assessMutation.mutateAsync({
        projectId,
        payload: {
          artifact_ref: artifactRef,
          selected_artifact_refs: [artifactRef],
          budget_cap_usd: getBudgetCapUsd(),
        },
      }),
    onSuccess: (result, { chatMessageId }) => {
      updateAssessmentChat('Assessing artifact impact', result, chatMessageId)
      toast.success(
        `Assessment recorded: ${result.assessment.total_needs_revision} need revision, ${result.assessment.total_confirmed_valid} confirmed valid.`,
      )
    },
    onError: (error) => toast.error(error.message),
  })

  const assessAllAction = useLongRunningAction({
    projectId,
    label: 'Assessing affected artifacts',
    action: async () =>
      assessMutation.mutateAsync({
        projectId,
        payload: {
          artifact_ref: artifactRef,
          budget_cap_usd: getBudgetCapUsd(),
        },
      }),
    onSuccess: (result, { chatMessageId }) => {
      updateAssessmentChat('Assessing affected artifacts', result, chatMessageId)
      toast.success(
        `Assessed ${result.assessment.assessments.length} artifact${result.assessment.assessments.length === 1 ? '' : 's'}.`,
      )
    },
    onError: (error) => toast.error(error.message),
  })

  const isBusy =
    previewMutation.isPending ||
    overrideMutation.isPending ||
    assessCurrentAction.isRunning ||
    assessAllAction.isRunning

  if (!health || !['stale', 'needs_revision', 'confirmed_valid'].includes(health)) {
    return null
  }
  if (details?.source_kind === 'media_validation') {
    return null
  }

  function handleBudgetCapChange(value: string) {
    setBudgetCapUsd(value)
    previewMutation.reset()
  }

  function canStartAssessment(): boolean {
    try {
      getBudgetCapUsd()
      return true
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Invalid budget cap')
      return false
    }
  }

  async function handlePreview() {
    try {
      const budgetCap = getBudgetCapUsd()
      await previewMutation.mutateAsync({
        projectId,
        payload: {
          artifact_ref: artifactRef,
          budget_cap_usd: budgetCap,
        },
      })
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to preview impact scope')
    }
  }

  function handleAssessCurrent() {
    if (!canStartAssessment()) {
      return
    }
    void assessCurrentAction.start()
  }

  function handleAssessAll() {
    if (!canStartAssessment()) {
      return
    }
    void assessAllAction.start()
  }

  async function handleOverride(targetHealth: 'valid' | 'needs_revision' | 'confirmed_valid') {
    if (!manualRationale.trim()) {
      toast.error('Add a short note before applying a manual override.')
      return
    }
    try {
      const result = await overrideMutation.mutateAsync({
        projectId,
        payload: {
          artifact_ref: artifactRef,
          target_health: targetHealth,
          rationale: manualRationale.trim(),
        },
      })
      setManualRationale('')
      toast.success(`Artifact marked ${healthLabel(result.health)}.`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update artifact health')
    }
  }

  const title =
    health === 'stale'
      ? 'Impact Assessment'
      : health === 'needs_revision'
        ? 'Revision Required'
        : 'Assessment Confirmed Valid'
  const subtitle =
    health === 'stale'
      ? 'Preview the affected scope, run semantic triage, or resolve it manually.'
      : health === 'needs_revision'
        ? 'This artifact was assessed against an upstream change and still needs work.'
        : 'This artifact survived the upstream change. Acknowledge it to clear the attention state.'
  const preview = previewMutation.data
  const sourceLabel = formatArtifactRef(details?.trigger_ref)

  if (!isLatestVersion) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <h2 className="text-sm font-semibold">{title}</h2>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Impact actions only apply to the latest version of an artifact. Open the newest version
            to preview or resolve this state.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <div className="rounded-full border border-border bg-muted/30 p-2">
            {health === 'confirmed_valid' ? (
              <CheckCircle2 className="h-4 w-4 text-sky-300" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-400" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-semibold">{title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
          <div className="font-medium">{healthLabel(health)}</div>
          <div className="mt-1 text-muted-foreground">{healthDescription(health, details)}</div>
          {details?.trigger_ref && (
            <div className="mt-2 text-xs text-muted-foreground">
              Triggered by {sourceLabel}
            </div>
          )}
        </div>

        {(details?.upstream_change_summary || details?.suggested_revision) && (
          <>
            <div className="grid gap-3 md:grid-cols-2">
              {details?.upstream_change_summary && (
                <div className="rounded-md border border-border px-3 py-2 text-sm">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Upstream Change
                  </div>
                  <p className="mt-1">{details.upstream_change_summary}</p>
                </div>
              )}
              {details?.suggested_revision && (
                <div className="rounded-md border border-border px-3 py-2 text-sm">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Suggested Revision
                  </div>
                  <p className="mt-1">{details.suggested_revision}</p>
                </div>
              )}
            </div>
            <Separator />
          </>
        )}

        {health === 'stale' && (
          <>
            <div className="grid gap-3 md:grid-cols-[minmax(0,220px)_1fr]">
              <div className="space-y-2">
                <label className="block text-sm font-medium">Assessment Budget Cap</label>
                <Input
                  type="number"
                  inputMode="decimal"
                  min="0"
                  step="0.0001"
                  value={budgetCapUsd}
                  onChange={(event) => handleBudgetCapChange(event.target.value)}
                  placeholder="Leave blank for no cap"
                  disabled={isBusy}
                />
              </div>
              <div className="rounded-md border border-border bg-muted/10 px-3 py-2 text-sm text-muted-foreground">
                Preview compares the estimated AI cost against this per-run cap before an
                assessment starts. Leave it blank to allow the full selected scope.
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                className="gap-1.5"
                onClick={handlePreview}
                disabled={isBusy}
              >
                <Sparkles className="h-4 w-4" />
                {previewMutation.isPending ? 'Previewing…' : 'Preview Scope'}
              </Button>
              <Button
                className="gap-1.5"
                onClick={handleAssessCurrent}
                disabled={isBusy}
              >
                <Wand2 className="h-4 w-4" />
                {assessCurrentAction.isRunning ? 'Assessing…' : 'Assess This Artifact'}
              </Button>
              <Button
                variant="secondary"
                onClick={handleAssessAll}
                disabled={isBusy}
              >
                {assessAllAction.isRunning ? 'Assessing…' : 'Assess All Affected'}
              </Button>
            </div>

            {preview && (
              <div
                className={`space-y-3 rounded-md border p-3 ${
                  preview.within_budget
                    ? 'border-border bg-muted/10'
                    : 'border-destructive/30 bg-destructive/5'
                }`}
              >
                <div className="grid gap-3 md:grid-cols-4">
                  <div>
                    <div className="text-xs uppercase tracking-wide text-muted-foreground">
                      Pending Stale
                    </div>
                    <div className="text-lg font-semibold">{preview.total_stale}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-muted-foreground">
                      Artifact Types
                    </div>
                    <div className="text-sm">{preview.affected_types.join(', ') || 'None'}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-muted-foreground">
                      Estimated Cost
                    </div>
                    <div className="text-sm">
                      {formatCurrency(preview.estimated_cost.estimated_cost_usd)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-muted-foreground">
                      Budget Cap
                    </div>
                    <div className="text-sm">
                      {preview.budget_cap_usd == null
                        ? 'No cap'
                        : formatCurrency(preview.budget_cap_usd)}
                    </div>
                  </div>
                </div>
                {preview.budget_cap_usd != null && (
                  <p
                    className={`text-xs ${
                      preview.within_budget
                        ? 'text-muted-foreground'
                        : 'text-destructive'
                    }`}
                  >
                    {preview.within_budget
                      ? 'Preview stays within the configured budget cap.'
                      : 'Preview exceeds the configured budget cap. Reduce scope or raise the cap before assessing.'}
                  </p>
                )}
                {renderPreviewTargets(preview, artifactRef)}
              </div>
            )}
          </>
        )}

        <div>
          <label className="mb-2 block text-sm font-medium">Manual note</label>
          <Textarea
            value={manualRationale}
            onChange={(event) => setManualRationale(event.target.value)}
            className="min-h-[90px] text-sm"
            placeholder={
              health === 'stale'
                ? 'Explain why you are marking this manually instead of running assessment...'
                : 'Explain why this state should be cleared...'
            }
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {health === 'stale' && (
            <>
              <Button
                variant="outline"
                onClick={() => handleOverride('needs_revision')}
                disabled={isBusy}
              >
                Mark Needs Revision
              </Button>
              <Button
                variant="outline"
                onClick={() => handleOverride('confirmed_valid')}
                disabled={isBusy}
              >
                Mark Still Valid
              </Button>
            </>
          )}
          {health === 'needs_revision' && (
            <Button onClick={() => handleOverride('valid')} disabled={isBusy} className="gap-1.5">
              <CircleCheckBig className="h-4 w-4" />
              Mark Current
            </Button>
          )}
          {health === 'confirmed_valid' && (
            <Button onClick={() => handleOverride('valid')} disabled={isBusy} className="gap-1.5">
              <CircleCheckBig className="h-4 w-4" />
              Acknowledge as Current
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
