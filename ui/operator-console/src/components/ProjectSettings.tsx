import * as React from "react"
import { Settings, Cpu, Workflow } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
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

interface ProjectSettingsProps {
  projectId: string
  projectName: string
  children?: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function ProjectSettings({
  projectId,
  projectName,
  children,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: ProjectSettingsProps) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const open = controlledOpen ?? internalOpen
  const setOpen = controlledOnOpenChange ?? setInternalOpen

  // Mock initial values
  const [generalSettings, setGeneralSettings] = React.useState({
    name: projectName,
    path: `/Users/cam/Documents/Projects/cine-forge/projects/${projectId}`,
    created: "2026-02-15T10:30:00Z",
  })

  const [modelSettings, setModelSettings] = React.useState({
    defaultModel: "claude-sonnet-4-5",
    workModel: "claude-sonnet-4-5",
    verifyModel: "claude-opus-4",
    escalateModel: "claude-opus-4",
  })

  const [pipelineSettings, setPipelineSettings] = React.useState({
    defaultRecipe: "mvp-ingest",
    skipQA: false,
    forceRerun: false,
  })

  const modelOptions = [
    { value: "claude-sonnet-4-5", label: "Claude Sonnet 4.5" },
    { value: "claude-opus-4", label: "Claude Opus 4" },
    { value: "gpt-4o", label: "GPT-4o" },
  ]

  const recipeOptions = [
    { value: "mvp-ingest", label: "MVP Ingest" },
    { value: "world-building", label: "World Building" },
    { value: "narrative-analysis", label: "Narrative Analysis" },
  ]

  const handleSaveGeneral = () => {
    toast.success("Settings saved")
  }

  const handleSaveModels = () => {
    toast.success("Settings saved")
  }

  const handleSavePipeline = () => {
    toast.success("Settings saved")
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {children && <DialogTrigger asChild>{children}</DialogTrigger>}
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="size-5" />
            Project Settings
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general" className="w-full">
          <TabsList variant="line">
            <TabsTrigger value="general">
              <Settings className="size-4" />
              General
            </TabsTrigger>
            <TabsTrigger value="models">
              <Cpu className="size-4" />
              Models
            </TabsTrigger>
            <TabsTrigger value="pipeline">
              <Workflow className="size-4" />
              Pipeline
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
                  value={generalSettings.name}
                  onChange={(e) =>
                    setGeneralSettings({
                      ...generalSettings,
                      name: e.target.value,
                    })
                  }
                  placeholder="Enter project name"
                />
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="project-path"
                  className="text-sm font-medium text-muted-foreground"
                >
                  Project Path
                </label>
                <Input
                  id="project-path"
                  value={generalSettings.path}
                  readOnly
                  className="bg-muted/50 cursor-not-allowed"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Created
                </label>
                <div className="text-sm px-3 py-2 rounded-md bg-muted/50">
                  {formatDate(generalSettings.created)}
                </div>
              </div>
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button onClick={handleSaveGeneral}>Save</Button>
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
                    {modelOptions.map((option) => (
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
                    {modelOptions.map((option) => (
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
                    {modelOptions.map((option) => (
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
                    {modelOptions.map((option) => (
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
              <Button onClick={handleSaveModels}>Save</Button>
            </div>
          </TabsContent>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline" className="space-y-4 mt-4">
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label htmlFor="default-recipe" className="text-sm font-medium">
                  Default Recipe
                </label>
                <Select
                  value={pipelineSettings.defaultRecipe}
                  onValueChange={(value) =>
                    setPipelineSettings({
                      ...pipelineSettings,
                      defaultRecipe: value,
                    })
                  }
                >
                  <SelectTrigger id="default-recipe" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {recipeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pipelineSettings.skipQA}
                    onChange={(e) =>
                      setPipelineSettings({
                        ...pipelineSettings,
                        skipQA: e.target.checked,
                      })
                    }
                    className={cn(
                      "size-4 rounded border-input bg-transparent cursor-pointer",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                      "disabled:cursor-not-allowed disabled:opacity-50"
                    )}
                  />
                  <span className="text-sm font-medium">Skip QA</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pipelineSettings.forceRerun}
                    onChange={(e) =>
                      setPipelineSettings({
                        ...pipelineSettings,
                        forceRerun: e.target.checked,
                      })
                    }
                    className={cn(
                      "size-4 rounded border-input bg-transparent cursor-pointer",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                      "disabled:cursor-not-allowed disabled:opacity-50"
                    )}
                  />
                  <span className="text-sm font-medium">Force re-run</span>
                </label>
              </div>
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button onClick={handleSavePipeline}>Save</Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
