import { useRef } from 'react'
import { Sparkles, Timer, TriangleAlert, Wand2 } from 'lucide-react'
import { CreativeBriefPreviewCard } from '@/components/intent/CreativeBriefPreviewCard'
import {
  formatConsistencyStrategy,
  formatLatencyMs,
  formatPrerequisiteStrategy,
  formatPreviewIntent,
  formatPreviewMode,
  parsePreviewProvenance,
} from '@/components/preview-provenance'
import { RenderInputUsageCard } from '@/components/RenderInputUsageCard'
import { SelectionChatButton } from '@/components/SelectionChatButton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { VisualCreativeBrief } from '@/lib/api/intent-mood'
import {
  asArray,
  asNumber,
  asRecord,
  asString,
  asStringArray,
  formatDuration,
  formatToken,
  normalizeChatRole,
  parseRenderInputUsage,
  type RenderInputUsageView,
} from '@/components/render-utils'

type RenderPromptViewerProps = {
  data: Record<string, unknown>
}

type RenderPromptSectionView = {
  sectionId: string
  title: string
  body: string
  sourceRoleId: string | null
  sourceArtifactTypes: string[]
}

type RenderPromptView = {
  sceneHeading: string | null
  sceneNumber: number | null
  targetProvider: string | null
  targetModel: string | null
  enginePackId: string | null
  compilerModel: string | null
  requestedDurationSeconds: number | null
  resolvedDurationSeconds: number | null
  resolution: string | null
  aspectRatio: string | null
  promptText: string | null
  sections: RenderPromptSectionView[]
  includedCategories: string[]
  missingCategories: string[]
  notes: string[]
  promptSourcesUsed: string[]
  resolvedInputs: RenderInputUsageView[]
  providerParams: Record<string, unknown>
  previewProvenance: ReturnType<typeof parsePreviewProvenance>
  creativeBrief: VisualCreativeBrief | null
}

function parseSection(value: unknown, index: number): RenderPromptSectionView | null {
  const record = asRecord(value)
  if (!record) return null
  const body = asString(record.body)
  if (!body) return null
  return {
    sectionId: asString(record.section_id) ?? `section_${index + 1}`,
    title: asString(record.title) ?? `Section ${index + 1}`,
    body,
    sourceRoleId: asString(record.source_role_id),
    sourceArtifactTypes: asStringArray(record.source_artifact_types),
  }
}

function parseCreativeBrief(value: unknown): VisualCreativeBrief | null {
  const record = asRecord(value)
  if (!record) return null
  const activeProjectReferences = asArray(record.active_project_references)
    .map(item => {
      const reference = asRecord(item)
      if (!reference) return null
      const assetId = asString(reference.asset_id)
      const filename = asString(reference.filename)
      const purpose = asString(reference.purpose)
      const lockStatus = asString(reference.lock_status)
      const transparencyNote = asString(reference.transparency_note)
      if (!assetId || !filename || !purpose || !lockStatus || !transparencyNote) return null
      return {
        asset_id: assetId,
        filename,
        purpose,
        lock_status: lockStatus as VisualCreativeBrief['active_project_references'][number]['lock_status'],
        transparency_note: transparencyNote,
      }
    })
    .filter((reference): reference is VisualCreativeBrief['active_project_references'][number] => reference !== null)

  return {
    visual_medium: asString(record.visual_medium),
    mood_descriptors: asStringArray(record.mood_descriptors),
    reference_films: asStringArray(record.reference_films),
    filmmaker_anchors: asStringArray(record.filmmaker_anchors),
    style_preset_id: asString(record.style_preset_id),
    natural_language_intent: asString(record.natural_language_intent),
    look_notes: asString(record.look_notes),
    active_project_references: activeProjectReferences,
    summary_lines: asStringArray(record.summary_lines),
    operator_preview: asString(record.operator_preview) ?? '',
    sources_used: asStringArray(record.sources_used),
  }
}

function parseRenderPrompt(data: Record<string, unknown>): RenderPromptView {
  const completeness = asRecord(data.completeness)
  const providerParams = asRecord(data.provider_params) ?? {}
  return {
    sceneHeading: asString(data.scene_heading),
    sceneNumber: asNumber(data.scene_number),
    targetProvider: asString(data.target_provider),
    targetModel: asString(data.target_model),
    enginePackId: asString(data.engine_pack_id),
    compilerModel: asString(data.compiler_model),
    requestedDurationSeconds: asNumber(data.requested_duration_seconds),
    resolvedDurationSeconds: asNumber(data.resolved_duration_seconds),
    resolution: asString(data.resolution),
    aspectRatio: asString(data.aspect_ratio),
    promptText: asString(data.prompt_text),
    sections: asArray(data.sections)
      .map(parseSection)
      .filter((section): section is RenderPromptSectionView => section !== null),
    includedCategories: asStringArray(completeness?.included_categories),
    missingCategories: asStringArray(completeness?.missing_categories),
    notes: asStringArray(completeness?.notes),
    promptSourcesUsed: asStringArray(data.prompt_sources_used),
    resolvedInputs: asArray(data.resolved_inputs)
      .map(parseRenderInputUsage)
      .filter((input): input is RenderInputUsageView => input !== null),
    providerParams,
    previewProvenance: parsePreviewProvenance(data.preview_provenance),
    creativeBrief: parseCreativeBrief(data.creative_brief_preview),
  }
}

function RenderPromptSectionCard({ section }: { section: RenderPromptSectionView }) {
  const bodyRef = useRef<HTMLParagraphElement>(null)

  return (
    <Card key={section.sectionId} className="gap-0">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">{section.title}</CardTitle>
              {section.sourceRoleId && (
                <Badge variant="secondary">{formatToken(section.sourceRoleId)}</Badge>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {section.sourceArtifactTypes.map(source => (
                <Badge key={source} variant="outline">
                  {source}
                </Badge>
              ))}
            </div>
          </div>
          <SelectionChatButton
            roleId={normalizeChatRole(section.sourceRoleId)}
            prompt={`I'd like to discuss how this ${section.title.toLowerCase()} section is shaping the render.`}
            fallbackQuote={section.body}
            selectionRootRef={bodyRef}
            label="Discuss Section"
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          />
        </div>
      </CardHeader>
      <CardContent>
        <p
          ref={bodyRef}
          className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90"
        >
          {section.body}
        </p>
      </CardContent>
    </Card>
  )
}

export function RenderPromptViewer({ data }: RenderPromptViewerProps) {
  const prompt = parseRenderPrompt(data)
  const isAiPrevizPrompt = prompt.previewProvenance?.mode === 'ai_previz'
  const sceneLabel =
    prompt.sceneNumber !== null
      ? `Scene ${prompt.sceneNumber}`
      : isAiPrevizPrompt
        ? 'AI Previz Prompt'
        : 'Render Prompt'
  const providerParamsJson = JSON.stringify(prompt.providerParams, null, 2)
  const promptBodyRef = useRef<HTMLParagraphElement>(null)

  return (
    <div className="space-y-4">
      <Card className="gap-0">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-1">
              <CardTitle>{sceneLabel}</CardTitle>
              <CardDescription>
                {prompt.sceneHeading
                  ?? (isAiPrevizPrompt
                    ? 'Compiled low-fidelity AI previz prompt'
                    : 'Compiled provider-ready render prompt')}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {formatPreviewMode(prompt.previewProvenance?.mode ?? null) && (
                <Badge variant="secondary">
                  {formatPreviewMode(prompt.previewProvenance?.mode ?? null)}
                </Badge>
              )}
              {formatPreviewIntent(prompt.previewProvenance?.fidelityIntent ?? null) && (
                <Badge variant="outline">
                  {formatPreviewIntent(prompt.previewProvenance?.fidelityIntent ?? null)}
                </Badge>
              )}
              {prompt.targetProvider && (
                <Badge variant="secondary">{formatToken(prompt.targetProvider)}</Badge>
              )}
              {prompt.targetModel && <Badge variant="outline">{prompt.targetModel}</Badge>}
              {prompt.compilerModel && (
                <Badge variant="outline" className="gap-1">
                  <Sparkles className="h-3 w-3" />
                  {prompt.compilerModel}
                </Badge>
              )}
              {prompt.enginePackId && (
                <Badge variant="outline" className="gap-1">
                  <Wand2 className="h-3 w-3" />
                  {prompt.enginePackId}
                </Badge>
              )}
              {formatDuration(prompt.resolvedDurationSeconds) && (
                <Badge variant="outline">{formatDuration(prompt.resolvedDurationSeconds)}</Badge>
              )}
              {prompt.resolution && <Badge variant="outline">{prompt.resolution}</Badge>}
              {prompt.aspectRatio && <Badge variant="outline">{prompt.aspectRatio}</Badge>}
              {formatConsistencyStrategy(prompt.previewProvenance?.consistencyStrategy ?? null) && (
                <Badge variant="outline">
                  {formatConsistencyStrategy(prompt.previewProvenance?.consistencyStrategy ?? null)}
                </Badge>
              )}
              {formatPrerequisiteStrategy(prompt.previewProvenance?.prerequisiteStrategy ?? null) && (
                <Badge variant="outline">
                  {formatPrerequisiteStrategy(prompt.previewProvenance?.prerequisiteStrategy ?? null)}
                </Badge>
              )}
              {formatLatencyMs(prompt.previewProvenance?.generationLatencyMs ?? null) && (
                <Badge variant="outline" className="gap-1">
                  <Timer className="h-3 w-3" />
                  {formatLatencyMs(prompt.previewProvenance?.generationLatencyMs ?? null)}
                </Badge>
              )}
              {isAiPrevizPrompt && !prompt.previewProvenance?.estimatedCostUsd && (
                <Badge variant="outline">Cost unverified</Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {(prompt.previewProvenance?.prerequisiteStrategy
            || (prompt.previewProvenance?.reusedArtifactTypes?.length ?? 0) > 0
            || (prompt.previewProvenance?.autoBuildArtifactTypes?.length ?? 0) > 0
            || (prompt.previewProvenance?.missingOptionalArtifactTypes?.length ?? 0) > 0) && (
            <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
              <div className="space-y-1">
                {formatPrerequisiteStrategy(prompt.previewProvenance?.prerequisiteStrategy ?? null) && (
                  <p>
                    Prep strategy:{' '}
                    {formatPrerequisiteStrategy(prompt.previewProvenance?.prerequisiteStrategy ?? null)}
                  </p>
                )}
                {(prompt.previewProvenance?.reusedArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Reused:{' '}
                    {prompt.previewProvenance?.reusedArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
                {(prompt.previewProvenance?.autoBuildArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Auto-built:{' '}
                    {prompt.previewProvenance?.autoBuildArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
                {(prompt.previewProvenance?.missingOptionalArtifactTypes?.length ?? 0) > 0 && (
                  <p>
                    Missing optional context:{' '}
                    {prompt.previewProvenance?.missingOptionalArtifactTypes
                      .map(token => formatToken(token) ?? token)
                      .join(', ')}
                  </p>
                )}
              </div>
            </div>
          )}

          {isAiPrevizPrompt && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-100">
              <div className="flex items-start gap-2">
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                <p>
                  This prompt is for low-fidelity previz, not final render output. Keep the result
                  focused on camera placement, blocking, motion, pacing, and location readability.
                </p>
              </div>
            </div>
          )}

          <div className="rounded-xl border border-border bg-card/60 px-4 py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {isAiPrevizPrompt ? 'Previz Prompt' : 'Final Prompt'}
              </p>
              {prompt.promptText && (
                <SelectionChatButton
                  roleId="director"
                  prompt={
                    isAiPrevizPrompt
                      ? "I'd like to discuss this compiled AI previz prompt."
                      : "I'd like to discuss this compiled render prompt."
                  }
                  fallbackQuote={prompt.promptText}
                  selectionRootRef={promptBodyRef}
                  label="Discuss Prompt"
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                />
              )}
            </div>
            <p
              ref={promptBodyRef}
              className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90"
            >
              {prompt.promptText ?? 'Prompt text is missing from this artifact.'}
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Coverage
              </p>
              <div className="flex flex-wrap gap-2">
                {prompt.includedCategories.length > 0 ? (
                  prompt.includedCategories.map(category => (
                    <Badge key={category} variant="secondary">
                      {formatToken(category) ?? category}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">No completeness categories recorded.</span>
                )}
              </div>
              {prompt.missingCategories.length > 0 && (
                <div className="mt-3 space-y-2 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2">
                  <p className="text-xs font-medium text-amber-300">Missing categories</p>
                  <div className="flex flex-wrap gap-2">
                    {prompt.missingCategories.map(category => (
                      <Badge key={category} variant="outline">
                        {formatToken(category) ?? category}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Provenance
              </p>
              <div className="flex flex-wrap gap-2">
                {prompt.promptSourcesUsed.length > 0 ? (
                  prompt.promptSourcesUsed.map(source => (
                    <Badge key={source} variant="outline">
                      {source}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">No prompt-source list recorded.</span>
                )}
              </div>
              {prompt.notes.length > 0 && (
                <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                  {prompt.notes.map(note => (
                    <p key={note}>{note}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {prompt.creativeBrief && <CreativeBriefPreviewCard brief={prompt.creativeBrief} />}

          {Object.keys(prompt.providerParams).length > 0 && (
            <div className="rounded-lg border border-border bg-card/60 px-4 py-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Provider Params
              </p>
              <pre className="overflow-x-auto rounded-md bg-muted/40 p-3 text-xs text-foreground/85">
                {providerParamsJson}
              </pre>
            </div>
          )}

          {(prompt.requestedDurationSeconds !== null || prompt.resolvedDurationSeconds !== null) && (
            <p className="text-sm text-muted-foreground">
              Requested {formatDuration(prompt.requestedDurationSeconds)} and compiled for{' '}
              {formatDuration(prompt.resolvedDurationSeconds)}.
            </p>
          )}
        </CardContent>
      </Card>

      {prompt.sections.length > 0 && (
        <div className="space-y-3">
          {prompt.sections.map(section => (
            <RenderPromptSectionCard key={section.sectionId} section={section} />
          ))}
        </div>
      )}

      <RenderInputUsageCard inputs={prompt.resolvedInputs} />
    </div>
  )
}
