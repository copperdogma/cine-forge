import * as React from "react"
import { Settings, Cpu, Workflow, Fingerprint, Palette, Sparkles } from "lucide-react"
import { toast } from "sonner"
import { useQueryClient } from "@tanstack/react-query"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import {
  ProjectBudgetSettingsSection,
  type BudgetSettingsFormState,
} from "@/components/ProjectBudgetSettingsSection"
import { ProjectPreferenceLearningSection } from "@/components/ProjectPreferenceLearningSection"
import { ProjectAppearanceSection } from "@/components/ProjectAppearanceSection"
import { ProjectStylePacksSection } from "@/components/ProjectStylePacksSection"
import { updateProjectSettings } from "@/lib/api"
import type { ProjectSummary } from "@/lib/types"
import {
  getPersistedProjectModelState,
  getProjectModelFormState,
  normalizeProjectModelSettings,
  OPTIONAL_PROJECT_MODEL_OPTIONS,
  PROJECT_MODEL_OPTIONS,
} from "@/lib/project-models"

interface ProjectSettingsProps {
  projectId: string
  project: ProjectSummary | undefined
  children?: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

function getBudgetSettingsFormState(project?: ProjectSummary): BudgetSettingsFormState {
  return {
    projectBudgetLimitUsd:
      project?.project_budget_limit_usd != null ? String(project.project_budget_limit_usd) : "",
    defaultRunBudgetLimitUsd:
      project?.default_run_budget_limit_usd != null
        ? String(project.default_run_budget_limit_usd)
        : "",
    budgetWarningThresholdRatio: String(project?.budget_warning_threshold_ratio ?? 0.8),
  }
}

export function ProjectSettings({
  projectId,
  project,
  children,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: ProjectSettingsProps) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const open = controlledOpen ?? internalOpen
  const setOpen = controlledOnOpenChange ?? setInternalOpen
  const queryClient = useQueryClient()

  const projectName = project?.display_name ?? ""
  const controlMode = project?.human_control_mode ?? "autonomous"

  // Track the editable display name — sync from prop when dialog opens
  const [editName, setEditName] = React.useState(projectName)
  const [editMode, setEditMode] = React.useState(controlMode)
  const [saving, setSaving] = React.useState(false)
  const [savingModels, setSavingModels] = React.useState(false)
  const [savingBudget, setSavingBudget] = React.useState(false)

  React.useEffect(() => {
    if (open) {
      setEditName(projectName)
      setEditMode(controlMode)
      setModelSettings(getProjectModelFormState(project))
      setBudgetSettings(getBudgetSettingsFormState(project))
    }
  }, [open, project, projectName, controlMode])

  const [modelSettings, setModelSettings] = React.useState(() => getProjectModelFormState(project))
  const [budgetSettings, setBudgetSettings] = React.useState<BudgetSettingsFormState>(() =>
    getBudgetSettingsFormState(project)
  )

  const controlModeOptions = [
    { value: "autonomous", label: "Autonomous", description: "Director makes progression decisions." },
    { value: "checkpoint", label: "Checkpoint", description: "Pause for human approval at each stage." },
    { value: "advisory", label: "Advisory", description: "Human drives, AI provides feedback." },
  ]

  const handleSaveGeneral = async () => {
    const changes: Parameters<typeof updateProjectSettings>[1] = {}
    if (editName.trim() !== projectName) changes.display_name = editName.trim()
    if (editMode !== controlMode) changes.human_control_mode = editMode

    if (Object.keys(changes).length === 0) {
      toast.info("No changes to save")
      return
    }

    setSaving(true)
    try {
      const updatedProject = await updateProjectSettings(projectId, changes)
      queryClient.setQueryData(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success("Project settings updated")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save"
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveModels = async () => {
    const normalized = normalizeProjectModelSettings(modelSettings)
    const persisted = getPersistedProjectModelState(project)
    const changes: Parameters<typeof updateProjectSettings>[1] = {}

    for (const [key, value] of Object.entries(normalized)) {
      if (persisted[key as keyof typeof persisted] !== value) {
        changes[key as keyof typeof normalized] = value
      }
    }

    if (Object.keys(changes).length === 0) {
      toast.info("No changes to save")
      return
    }

    setSavingModels(true)
    try {
      const updatedProject = await updateProjectSettings(projectId, changes)
      queryClient.setQueryData(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success("Model defaults updated")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save"
      toast.error(message)
    } finally {
      setSavingModels(false)
    }
  }

  const handleSaveBudget = async () => {
    const parseOptionalNumber = (raw: string): number | null => {
      if (!raw.trim()) return null
      const value = Number(raw)
      if (!Number.isFinite(value) || value < 0) {
        throw new Error("Budget limits must be zero or greater.")
      }
      return value
    }

    const thresholdValue = Number(budgetSettings.budgetWarningThresholdRatio)
    if (!Number.isFinite(thresholdValue) || thresholdValue < 0 || thresholdValue > 1) {
      toast.error("Budget warning threshold must be between 0 and 1.")
      return
    }

    let projectBudgetLimitUsd: number | null
    let defaultRunBudgetLimitUsd: number | null
    try {
      projectBudgetLimitUsd = parseOptionalNumber(budgetSettings.projectBudgetLimitUsd)
      defaultRunBudgetLimitUsd = parseOptionalNumber(budgetSettings.defaultRunBudgetLimitUsd)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid budget settings"
      toast.error(message)
      return
    }

    const changes: Parameters<typeof updateProjectSettings>[1] = {}
    if ((project?.project_budget_limit_usd ?? null) !== projectBudgetLimitUsd) {
      changes.project_budget_limit_usd = projectBudgetLimitUsd
    }
    if ((project?.default_run_budget_limit_usd ?? null) !== defaultRunBudgetLimitUsd) {
      changes.default_run_budget_limit_usd = defaultRunBudgetLimitUsd
    }
    if ((project?.budget_warning_threshold_ratio ?? 0.8) !== thresholdValue) {
      changes.budget_warning_threshold_ratio = thresholdValue
    }

    if (Object.keys(changes).length === 0) {
      toast.info("No changes to save")
      return
    }

    setSavingBudget(true)
    try {
      const updatedProject = await updateProjectSettings(projectId, changes)
      queryClient.setQueryData(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'costs'] })
      toast.success("Budget settings updated")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save"
      toast.error(message)
    } finally {
      setSavingBudget(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {children && <DialogTrigger asChild>{children}</DialogTrigger>}
      <DialogContent className="max-h-[85vh] max-w-[calc(100vw-1rem)] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="size-5" />
            Project Settings
          </DialogTitle>
          <DialogDescription className="sr-only">
            Configure project metadata, model defaults, and pipeline budget settings.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="general" className="w-full">
          <TabsList variant="line" scrollable className="pb-1">
            <TabsTrigger value="general">
              <Settings className="size-4" />
              General
            </TabsTrigger>
            <TabsTrigger value="models">
              <Cpu className="size-4" />
              Models
            </TabsTrigger>
            <TabsTrigger value="appearance">
              <Palette className="size-4" />
              Appearance
            </TabsTrigger>
            <TabsTrigger value="style-packs">
              <Sparkles className="size-4" />
              Style Packs
            </TabsTrigger>
            <TabsTrigger value="pipeline">
              <Workflow className="size-4" />
              Pipeline
            </TabsTrigger>
            <TabsTrigger value="preferences">
              <Fingerprint className="size-4" />
              Preferences
            </TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general" className="space-y-4 mt-4">
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label
                  htmlFor="project-name"
                  className="text-sm font-medium"
                >
                  Project Name
                </label>
                <Input
                  id="project-name"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Enter project name"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="control-mode" className="text-sm font-medium">
                  Human Control Mode
                </label>
                <Select
                  value={editMode}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  onValueChange={(value: any) => setEditMode(value)}
                >
                  <SelectTrigger id="control-mode" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {controlModeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex flex-col text-left">
                          <span className="font-medium">{option.label}</span>
                          <span className="text-xs text-muted-foreground">{option.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Slug
                </label>
                <div className="text-sm px-3 py-2 rounded-md bg-muted/50 font-mono text-muted-foreground">
                  {projectId}
                </div>
                <p className="text-xs text-muted-foreground">
                  Used in URLs and as the project folder name. Cannot be changed.
                </p>
              </div>
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button onClick={handleSaveGeneral} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
            </div>
          </TabsContent>

          {/* Models Tab */}
          <TabsContent value="models" className="space-y-4 mt-4">
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label htmlFor="default-model" className="text-sm font-medium">
                  Default Model
                </label>
                <Select
                  value={modelSettings.defaultModel}
                  onValueChange={(value) =>
                    setModelSettings({
                      ...modelSettings,
                      defaultModel: value,
                    })
                  }
                >
                  <SelectTrigger id="default-model" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PROJECT_MODEL_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="work-model" className="text-sm font-medium">
                  Work Model
                </label>
                <Select
                  value={modelSettings.workModel}
                  onValueChange={(value) =>
                    setModelSettings({
                      ...modelSettings,
                      workModel: value,
                    })
                  }
                >
                  <SelectTrigger id="work-model" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {OPTIONAL_PROJECT_MODEL_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="verify-model" className="text-sm font-medium">
                  Verify Model
                </label>
                <Select
                  value={modelSettings.verifyModel}
                  onValueChange={(value) =>
                    setModelSettings({
                      ...modelSettings,
                      verifyModel: value,
                    })
                  }
                >
                  <SelectTrigger id="verify-model" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {OPTIONAL_PROJECT_MODEL_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="escalate-model" className="text-sm font-medium">
                  Escalate Model
                </label>
                <Select
                  value={modelSettings.escalateModel}
                  onValueChange={(value) =>
                    setModelSettings({
                      ...modelSettings,
                      escalateModel: value,
                    })
                  }
                >
                  <SelectTrigger id="escalate-model" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {OPTIONAL_PROJECT_MODEL_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button onClick={handleSaveModels} disabled={savingModels}>
                {savingModels ? "Saving..." : "Save"}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="appearance" className="space-y-4 mt-4">
            <ProjectAppearanceSection projectId={projectId} project={project} />
          </TabsContent>

          <TabsContent value="style-packs" className="space-y-4 mt-4">
            <ProjectStylePacksSection projectId={projectId} project={project} />
          </TabsContent>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline" className="space-y-4 mt-4">
            <ProjectBudgetSettingsSection
              value={budgetSettings}
              onChange={setBudgetSettings}
            />

            <Separator />

            <div className="flex justify-end">
              <Button onClick={handleSaveBudget} disabled={savingBudget}>
                {savingBudget ? "Saving..." : "Save"}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="preferences" className="space-y-4 mt-4">
            <ProjectPreferenceLearningSection projectId={projectId} project={project} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
