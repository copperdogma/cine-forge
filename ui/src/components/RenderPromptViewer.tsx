import { useRef } from 'react'
import { Sparkles, Wand2 } from 'lucide-react'
import { RenderInputUsageCard } from '@/components/RenderInputUsageCard'
import { SelectionChatButton } from '@/components/SelectionChatButton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  const sceneLabel =
    prompt.sceneNumber !== null ? `Scene ${prompt.sceneNumber}` : 'Render Prompt'
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
                {prompt.sceneHeading ?? 'Compiled provider-ready render prompt'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
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
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border border-border bg-card/60 px-4 py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Final Prompt
              </p>
              {prompt.promptText && (
                <SelectionChatButton
                  roleId="director"
                  prompt="I'd like to discuss this compiled render prompt."
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
