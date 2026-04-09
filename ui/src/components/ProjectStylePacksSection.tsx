import * as React from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { LibraryBig, Sparkles, WandSparkles } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import {
  generateStylePackDraft,
  getManualStylePackPrompt,
  getProjectStylePackLibrary,
  importManualStylePackDraft,
  saveStylePackDraft,
  updateProjectSettings,
} from '@/lib/api'
import type {
  ProjectSummary,
  RoleStylePackLibrary,
  StylePackDraft,
  StylePackDraftFile,
  StylePackLibraryItem,
  StylePackManualPromptResponse,
  StylePackProvider,
  StylePackResearchCost,
} from '@/lib/types'
import { useLongRunningAction } from '@/lib/use-long-running-action'

type ProjectStylePacksSectionProps = {
  projectId: string
  project: ProjectSummary | undefined
}

type DraftSaveMode = 'save' | 'assign' | null

function findSelectedPack(role: RoleStylePackLibrary): StylePackLibraryItem | undefined {
  return role.style_packs.find((pack) => pack.style_pack_id === role.selected_style_pack_id)
}

function formatCurrency(value: number | null | undefined): string | null {
  if (value == null) return null
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value)
}

function formatTokens(value: number): string {
  return new Intl.NumberFormat('en-US').format(value)
}

function updateDraftFile(
  files: StylePackDraftFile[],
  index: number,
  content: string,
): StylePackDraftFile[] {
  return files.map((file, fileIndex) => (fileIndex === index ? { ...file, content } : file))
}

export function ProjectStylePacksSection({
  projectId,
  project,
}: ProjectStylePacksSectionProps) {
  const queryClient = useQueryClient()
  const [savingRoleId, setSavingRoleId] = React.useState<string | null>(null)
  const [saveMode, setSaveMode] = React.useState<DraftSaveMode>(null)
  const [draft, setDraft] = React.useState<StylePackDraft | null>(null)
  const [manualPrompt, setManualPrompt] = React.useState<StylePackManualPromptResponse | null>(null)
  const [manualOutput, setManualOutput] = React.useState('')
  const [manualPromptLoading, setManualPromptLoading] = React.useState(false)
  const [manualImportLoading, setManualImportLoading] = React.useState(false)
  const [form, setForm] = React.useState<{
    roleId: string
    provider: StylePackProvider
    subject: string
  }>({
    roleId: '',
    provider: 'openai',
    subject: '',
  })

  const libraryQuery = useQuery({
    queryKey: ['projects', projectId, 'style-packs'],
    queryFn: () => getProjectStylePackLibrary(projectId),
  })

  const generationRoles = React.useMemo(
    () => (libraryQuery.data?.roles ?? []).filter((role) => role.can_generate),
    [libraryQuery.data?.roles],
  )

  React.useEffect(() => {
    if (!form.roleId && generationRoles.length > 0) {
      setForm((current) => ({ ...current, roleId: generationRoles[0].role_id }))
    }
  }, [form.roleId, generationRoles])

  React.useEffect(() => {
    const providerOptions = libraryQuery.data?.providers ?? []
    if (providerOptions.length === 0) return
    if (providerOptions.some((option) => option.provider === form.provider)) return
    const nextProvider =
      providerOptions.find((option) => option.recommended)?.provider ?? providerOptions[0].provider
    setForm((current) => ({ ...current, provider: nextProvider }))
  }, [form.provider, libraryQuery.data?.providers])

  React.useEffect(() => {
    setManualPrompt(null)
    setManualOutput('')
  }, [form.roleId, form.subject])

  const generationAction = useLongRunningAction({
    projectId,
    label: 'Generating style pack draft',
    items: [
      { label: 'Preparing role prompt' },
      { label: 'Running deep research' },
      { label: 'Parsing draft for review' },
    ],
    action: () =>
      generateStylePackDraft(projectId, {
        role_id: form.roleId,
        provider: form.provider,
        subject: form.subject.trim(),
      }),
    onSuccess: (result) => {
      setDraft(result)
      toast.success('Draft ready for review')
    },
    onError: (error) => {
      toast.error(error.message)
    },
    speaker: 'director',
  })

  async function handleAssignmentChange(roleId: string, stylePackId: string) {
    const cachedProject =
      queryClient.getQueryData<ProjectSummary>(['projects', projectId]) ?? project
    const nextSelections = {
      ...(cachedProject?.style_packs ?? {}),
      [roleId]: stylePackId,
    }

    setSavingRoleId(roleId)
    try {
      const updatedProject = await updateProjectSettings(projectId, {
        style_packs: nextSelections,
      })
      queryClient.setQueryData(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'style-packs'] })
      toast.success('Style pack assignment updated')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update style pack'
      toast.error(message)
    } finally {
      setSavingRoleId(null)
    }
  }

  async function handleSaveDraft(assignToRole: boolean) {
    if (!draft) return
    setSaveMode(assignToRole ? 'assign' : 'save')
    try {
      const response = await saveStylePackDraft(projectId, {
        role_id: draft.role_id,
        style_pack_id: draft.style_pack_id.trim(),
        display_name: draft.display_name.trim(),
        summary: draft.summary.trim(),
        prompt_injection: draft.prompt_injection.trim(),
        style_markdown: draft.style_markdown.trim(),
        additional_files: draft.additional_files,
        assign_to_role: assignToRole,
      })
      queryClient.setQueryData(['projects', projectId], response.project_summary)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'style-packs'] })
      setDraft(null)
      setManualOutput('')
      toast.success(assignToRole ? 'Style pack saved and assigned' : 'Style pack saved')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save draft'
      toast.error(message)
    } finally {
      setSaveMode(null)
    }
  }

  async function handlePrepareManualPrompt() {
    setManualPromptLoading(true)
    try {
      const response = await getManualStylePackPrompt(projectId, {
        role_id: form.roleId,
        subject: form.subject.trim(),
      })
      setManualPrompt(response)
      toast.success('Manual prompt prepared')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to prepare manual prompt'
      toast.error(message)
    } finally {
      setManualPromptLoading(false)
    }
  }

  async function handleCopyManualPrompt() {
    if (!manualPrompt) return
    try {
      await navigator.clipboard.writeText(manualPrompt.prompt)
      toast.success('Manual prompt copied')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to copy prompt'
      toast.error(message)
    }
  }

  async function handleImportManualOutput() {
    setManualImportLoading(true)
    try {
      const result = await importManualStylePackDraft(projectId, {
        role_id: form.roleId,
        subject: form.subject.trim(),
        raw_output: manualOutput.trim(),
      })
      setDraft(result)
      toast.success('Manual draft parsed for review')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to parse manual output'
      toast.error(message)
    } finally {
      setManualImportLoading(false)
    }
  }

  const providerOptions = libraryQuery.data?.providers ?? []
  const libraryRoles = libraryQuery.data?.roles ?? []
  const currentResearchCost: StylePackResearchCost | null = draft?.research_cost ?? null
  const formattedCost = formatCurrency(currentResearchCost?.estimated_cost_usd ?? null)

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-primary" />
          <h3 className="text-sm font-semibold">Style Packs</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Build project-local taste packs, save them under this project, and assign them per role.
          Saved packs stay inside the project and immediately affect chat and role runtime.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <LibraryBig className="size-4" />
            Role Library
          </CardTitle>
          <CardDescription>
            Each role can keep a different style pack. Project packs override built-ins when ids
            collide.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {libraryQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading available style packs…</p>
          ) : libraryRoles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No style-pack-enabled roles are available for this project.
            </p>
          ) : (
            libraryRoles.map((role) => {
              const selectedPack = findSelectedPack(role)
              return (
                <div key={role.role_id} className="space-y-3 rounded-lg border p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{role.display_name}</span>
                        {role.can_generate && <Badge variant="secondary">Can generate</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {selectedPack?.summary ?? 'No style pack is currently selected.'}
                      </p>
                    </div>
                    <div className="w-full sm:max-w-xs">
                      <Select
                        value={role.selected_style_pack_id ?? ''}
                        onValueChange={(value) => void handleAssignmentChange(role.role_id, value)}
                        disabled={savingRoleId === role.role_id || role.style_packs.length === 0}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a style pack" />
                        </SelectTrigger>
                        <SelectContent>
                          {role.style_packs.map((pack) => (
                            <SelectItem key={pack.style_pack_id} value={pack.style_pack_id}>
                              {pack.display_name} {pack.source === 'project' ? '· Project' : '· Built-in'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {role.style_packs.map((pack) => (
                      <Badge
                        key={`${role.role_id}-${pack.style_pack_id}`}
                        variant={pack.source === 'project' ? 'default' : 'outline'}
                      >
                        {pack.display_name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )
            })
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <WandSparkles className="size-4" />
            Generate Draft
          </CardTitle>
          <CardDescription>
            Start with one role, one provider, and one freeform prompt. The draft comes back
            editable before anything is saved.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="style-pack-role" className="text-sm font-medium">
                Role
              </label>
              <Select
                value={form.roleId}
                onValueChange={(value) => setForm((current) => ({ ...current, roleId: value }))}
                disabled={generationRoles.length === 0}
              >
                <SelectTrigger id="style-pack-role">
                  <SelectValue placeholder="Choose a role" />
                </SelectTrigger>
                <SelectContent>
                  {generationRoles.map((role) => (
                    <SelectItem key={role.role_id} value={role.role_id}>
                      {role.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="style-pack-provider" className="text-sm font-medium">
                Provider
              </label>
              <Select
                value={form.provider}
                onValueChange={(value) =>
                  setForm((current) => ({ ...current, provider: value as StylePackProvider }))
                }
                disabled={providerOptions.length === 0}
              >
                <SelectTrigger id="style-pack-provider">
                  <SelectValue placeholder="Choose a provider" />
                </SelectTrigger>
                <SelectContent>
                  {providerOptions.map((provider) => (
                    <SelectItem key={provider.provider} value={provider.provider}>
                      {provider.display_name}
                      {provider.recommended ? ' · Recommended' : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="style-pack-subject" className="text-sm font-medium">
              Freeform prompt
            </label>
            <Textarea
              id="style-pack-subject"
              value={form.subject}
              onChange={(event) =>
                setForm((current) => ({ ...current, subject: event.target.value }))
              }
              placeholder="Tarantino's dialogue with Mann's night-world tension."
              className="min-h-24"
            />
            <p className="text-xs text-muted-foreground">
              Use a single name, a combination, a reference work, or an original taste brief.
            </p>
          </div>

          <div className="flex justify-end">
            <Button
              onClick={() => void generationAction.start()}
              disabled={
                generationAction.isRunning || !form.roleId || form.subject.trim().length < 2
              }
            >
              {generationAction.isRunning ? 'Generating…' : 'Generate Draft'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Manual Fallback</CardTitle>
          <CardDescription>
            If you want to run the prompt in another tool, prepare the exact creation prompt here,
            paste the result back, and review it in the same draft workflow.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <Button
              variant="outline"
              onClick={() => void handlePrepareManualPrompt()}
              disabled={manualPromptLoading || !form.roleId || form.subject.trim().length < 2}
            >
              {manualPromptLoading ? 'Preparing…' : 'Prepare Manual Prompt'}
            </Button>
            <Button variant="outline" onClick={() => void handleCopyManualPrompt()} disabled={!manualPrompt}>
              Copy Prompt
            </Button>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="style-pack-manual-prompt" className="text-sm font-medium">
              Creation prompt
            </label>
            <Textarea
              id="style-pack-manual-prompt"
              value={manualPrompt?.prompt ?? ''}
              readOnly
              placeholder="Prepare a manual prompt to copy the role-specific creation instructions."
              className="min-h-48 font-mono text-xs"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="style-pack-manual-output" className="text-sm font-medium">
              Paste external model output
            </label>
            <Textarea
              id="style-pack-manual-output"
              value={manualOutput}
              onChange={(event) => setManualOutput(event.target.value)}
              placeholder="Paste the model output containing the style-pack manifest and style markdown."
              className="min-h-48 font-mono text-xs"
            />
          </div>

          <div className="flex justify-end">
            <Button
              variant="outline"
              onClick={() => void handleImportManualOutput()}
              disabled={
                manualImportLoading ||
                !form.roleId ||
                form.subject.trim().length < 2 ||
                manualOutput.trim().length < 20
              }
            >
              {manualImportLoading ? 'Parsing…' : 'Parse Pasted Output'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Draft Review</CardTitle>
          <CardDescription>
            Review the generated pack before saving. Files will land under
            <span className="font-mono"> style_packs/&lt;role&gt;/&lt;style-pack-id&gt;/</span>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!draft ? (
            <p className="text-sm text-muted-foreground">
              Generate or import a draft to preview and edit it here.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">
                  {draft.generation_mode === 'manual_import' ? 'Manual import' : 'Deep research'}
                </Badge>
                {draft.provider && <Badge variant="outline">{draft.provider}</Badge>}
                {formattedCost && <Badge variant="outline">{formattedCost}</Badge>}
              </div>

              {currentResearchCost && (
                <div className="rounded-lg border bg-muted/30 p-3 text-sm">
                  <div className="font-medium">
                    Research cost
                    {formattedCost ? ` · ${formattedCost}` : ''}
                  </div>
                  <p className="text-muted-foreground">
                    {currentResearchCost.model}
                    {currentResearchCost.total_tokens > 0
                      ? ` · ${formatTokens(currentResearchCost.total_tokens)} tokens`
                      : ''}
                    {currentResearchCost.latency_seconds != null
                      ? ` · ${currentResearchCost.latency_seconds.toFixed(1)}s`
                      : ''}
                  </p>
                  {currentResearchCost.note && (
                    <p className="mt-1 text-xs text-muted-foreground">{currentResearchCost.note}</p>
                  )}
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label htmlFor="draft-display-name" className="text-sm font-medium">
                    Display Name
                  </label>
                  <Input
                    id="draft-display-name"
                    value={draft.display_name}
                    onChange={(event) =>
                      setDraft((current) =>
                        current ? { ...current, display_name: event.target.value } : current,
                      )
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="draft-style-pack-id" className="text-sm font-medium">
                    Style Pack Id
                  </label>
                  <Input
                    id="draft-style-pack-id"
                    value={draft.style_pack_id}
                    onChange={(event) =>
                      setDraft((current) =>
                        current ? { ...current, style_pack_id: event.target.value } : current,
                      )
                    }
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="draft-summary" className="text-sm font-medium">
                  Summary
                </label>
                <Textarea
                  id="draft-summary"
                  value={draft.summary}
                  onChange={(event) =>
                    setDraft((current) =>
                      current ? { ...current, summary: event.target.value } : current,
                    )
                  }
                  className="min-h-20"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="draft-prompt-injection" className="text-sm font-medium">
                  Prompt Injection
                </label>
                <Textarea
                  id="draft-prompt-injection"
                  value={draft.prompt_injection}
                  onChange={(event) =>
                    setDraft((current) =>
                      current ? { ...current, prompt_injection: event.target.value } : current,
                    )
                  }
                  className="min-h-24"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="draft-style-markdown" className="text-sm font-medium">
                  style.md
                </label>
                <Textarea
                  id="draft-style-markdown"
                  value={draft.style_markdown}
                  onChange={(event) =>
                    setDraft((current) =>
                      current ? { ...current, style_markdown: event.target.value } : current,
                    )
                  }
                  className="min-h-64 font-mono text-xs"
                />
              </div>

              {draft.additional_files.length > 0 && (
                <div className="space-y-3">
                  <div className="space-y-1">
                    <h4 className="text-sm font-medium">Supporting files</h4>
                    <p className="text-xs text-muted-foreground">
                      Preserved research notes and references save alongside the pack.
                    </p>
                  </div>
                  {draft.additional_files.map((file, index) => (
                    <div key={`${file.path}-${index}`} className="space-y-2 rounded-lg border p-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{file.kind}</Badge>
                        <span className="font-mono">{file.path}</span>
                        {file.caption ? <span>{file.caption}</span> : null}
                      </div>
                      <Textarea
                        value={file.content}
                        onChange={(event) =>
                          setDraft((current) =>
                            current
                              ? {
                                  ...current,
                                  additional_files: updateDraftFile(
                                    current.additional_files,
                                    index,
                                    event.target.value,
                                  ),
                                }
                              : current,
                          )
                        }
                        className="min-h-40 font-mono text-xs"
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-col justify-end gap-2 sm:flex-row">
                <Button
                  variant="outline"
                  onClick={() => void handleSaveDraft(false)}
                  disabled={saveMode !== null}
                >
                  {saveMode === 'save' ? 'Saving…' : 'Save Draft'}
                </Button>
                <Button onClick={() => void handleSaveDraft(true)} disabled={saveMode !== null}>
                  {saveMode === 'assign' ? 'Saving…' : 'Save & Assign'}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
