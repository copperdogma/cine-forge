import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Play,
  Upload,
  ChevronDown,
  ChevronRight,
  Loader2,
  CheckCircle2,
  Circle,
  XCircle,
  FileText,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { SceneStrip } from '@/components/SceneStrip'
import { RunEventLog } from '@/components/RunEventLog'
import type { RunEvent } from '@/components/RunEventLog'
import { 
  useUploadInput, 
  useStartRun, 
  useRunState, 
  useRunEvents, 
  useRecipes, 
  useScenes, 
  useProjectInputs,
  useProject
} from '@/lib/hooks'
import { toast } from 'sonner'
import { getOrderedStageIds } from '@/lib/constants'
import { humanizeStageName } from '@/lib/chat-messages'

// Fallback recipes in case API fails
const fallbackRecipes = [
  { recipe_id: 'mvp_ingest', name: 'MVP Ingest', description: 'Full intake pipeline: ingest, normalize, extract', stage_count: 4 },
  { recipe_id: 'world_building', name: 'World Building', description: 'Synthesis pipeline: world, characters, locations', stage_count: 7 },
  { recipe_id: 'narrative_analysis', name: 'Narrative Analysis', description: 'Analysis pipeline: themes, arcs, structure', stage_count: 5 },
]

/** Transform backend pipeline events into RunEvent format for the event log UI. */
function transformBackendEvents(events?: Array<Record<string, unknown>>): RunEvent[] {
  if (!events || events.length === 0) return []
  return events.map((evt) => {
    const backendEvent = (evt.event as string) ?? ''
    const type = (evt.type as string) ?? 'info'
    const stageId = (evt.stage as string) ?? (evt.stage_id as string) ?? undefined
    const eventTypeMap: Record<string, RunEvent['type']> = {
      stage_started: 'stage_start',
      stage_finished: 'stage_end',
      stage_failed: 'error',
      stage_retrying: 'warning',
      stage_fallback: 'warning',
      stage_paused: 'warning',
    }
    const validTypes = ['stage_start', 'stage_end', 'ai_call', 'artifact_produced', 'error', 'warning', 'info']
    const mappedType = eventTypeMap[backendEvent] ?? type
    let message = (evt.message as string) ?? (evt.event as string) ?? type
    if (backendEvent === 'stage_retrying') {
      const delay = typeof evt.retry_delay_seconds === 'number'
        ? ` in ~${evt.retry_delay_seconds.toFixed(1)}s`
        : ''
      message = `Retrying ${stageId ?? 'stage'} after transient failure${delay}`
    } else if (backendEvent === 'stage_fallback') {
      message = `Fallback model selected: ${(evt.to_model as string) ?? 'unknown'}`
    } else if (backendEvent === 'stage_failed') {
      message = (evt.error as string) ?? `Stage ${stageId ?? ''} failed`
    }
    return {
      timestamp: typeof evt.timestamp === 'number'
        ? evt.timestamp * 1000 // backend uses seconds, UI uses ms
        : Date.now(),
      type: (validTypes.includes(mappedType) ? mappedType : 'info') as RunEvent['type'],
      stage: stageId,
      message,
      details: (evt.details as Record<string, unknown>) ?? undefined,
    }
  })
}

type RunView = 'config' | 'progress'

type UploadedInputResponse = {
  original_name: string
  stored_path: string
  size_bytes: number
}

export default function ProjectRun() {
  const { projectId, runId } = useParams()
  const navigate = useNavigate()
  const [view, setView] = useState<RunView>(runId ? 'progress' : 'config')
  const [selectedRecipe, setSelectedRecipe] = useState('mvp_ingest')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [selectedScene, setSelectedScene] = useState<number | undefined>(undefined)
  const [uploadedFile, setUploadedFile] = useState<UploadedInputResponse | null>(null)
  const [defaultModel, setDefaultModel] = useState('claude-sonnet-4-6')
  const [workModel, setWorkModel] = useState('claude-haiku-4-5-20251001')
  const [verifyModel, setVerifyModel] = useState('')
  const [startFrom, setStartFrom] = useState('')

  // API hooks
  const uploadMutation = useUploadInput(projectId || '')
  const startRunMutation = useStartRun()
  const { data: runStateData, isLoading: runStateLoading } = useRunState(runId || '')
  const { data: runEventsData } = useRunEvents(runId || '')
  const { data: recipesData, isLoading: recipesLoading } = useRecipes()
  const { data: scenesData = [] } = useScenes(projectId)
  const { data: existingInputs } = useProjectInputs(projectId)
  const { data: projectData } = useProject(projectId)

  // Use real recipes from API, fallback to hardcoded list if API fails
  const recipes = recipesData || fallbackRecipes

  // Auto-populate from existing project inputs (screenplay already uploaded during project creation)
  useEffect(() => {
    if (uploadedFile || !existingInputs?.length) return
    const latest = existingInputs[existingInputs.length - 1]
    // Use a small timeout to avoid synchronous setState during render/effect cycle
    const t = setTimeout(() => {
      setUploadedFile({
        original_name: latest.original_name,
        stored_path: latest.stored_path,
        size_bytes: latest.size_bytes,
      })
    }, 0)
    return () => clearTimeout(t)
  }, [existingInputs, uploadedFile])

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return

    const file = files[0]
    uploadMutation.mutate(file, {
      onSuccess: (data) => {
        setUploadedFile(data)
        toast.success(`Uploaded ${data.original_name} (${(data.size_bytes / 1024).toFixed(1)} KB)`)
      },
      onError: (error) => {
        toast.error(`Upload failed: ${error.message}`)
      }
    })
  }

  const handleStartRun = () => {
    if (!projectId || !uploadedFile) {
      toast.error('Please upload a screenplay first')
      return
    }

    const payload = {
      project_id: projectId,
      input_file: uploadedFile.stored_path,
      default_model: defaultModel,
      ...(workModel && { work_model: workModel }),
      ...(verifyModel && { verify_model: verifyModel }),
      human_control_mode: projectData?.human_control_mode ?? 'autonomous',
      recipe_id: selectedRecipe,
      accept_config: true,
      ...(startFrom && { start_from: startFrom }),
    }

    startRunMutation.mutate(payload, {
      onSuccess: (data) => {
        toast.success(`Started run ${data.run_id}`)
        navigate(`/${projectId}/run/${data.run_id}`)
      },
      onError: (error) => {
        toast.error(`Failed to start run: ${error.message}`)
      }
    })
  }

  // If we have a runId in the URL, show progress
  if (runId || view === 'progress') {
    const stages = runStateData?.state.stages || {}
    const recipeId = runStateData?.state.recipe_id || 'mvp_ingest'
    const stageIds = getOrderedStageIds(recipeId, Object.keys(stages))

    const isRunning = Object.values(stages).some((s) => s.status === 'running')
    const isCompleted = stageIds.length > 0 && stageIds.every((id) => stages[id]?.status === 'done' || stages[id]?.status === 'skipped_reused')
    const hasFailed = Object.values(stages).some((s) => s.status === 'failed')

    const getBadgeVariant = () => {
      if (hasFailed) return 'destructive'
      if (isCompleted) return 'default'
      return 'secondary'
    }

    const getBadgeLabel = () => {
      if (runStateLoading) return 'Loading...'
      if (hasFailed) return 'Failed'
      if (isCompleted) return 'Done'
      if (isRunning) return 'In Progress'
      return 'Pending'
    }

    const getBadgeIcon = () => {
      if (hasFailed) return <XCircle className="h-3 w-3 mr-1" />
      if (isCompleted) return <CheckCircle2 className="h-3 w-3 mr-1" />
      if (isRunning) return <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      return null
    }

    const getStageStatus = (status: string) => {
      if (status === 'done' || status === 'skipped_reused') return 'done'
      if (status === 'running') return 'running'
      if (status === 'failed') return 'failed'
      if (status === 'paused') return 'paused'
      return 'pending'
    }

    const formatDuration = (seconds: number) => {
      if (!seconds || seconds <= 0) return null
      const rounded = Math.round(seconds)
      if (rounded < 60) return `${rounded}s`
      const mins = Math.floor(rounded / 60)
      const secs = rounded % 60
      return `${mins}m ${secs}s`
    }

    const formatCost = (cost?: number) => {
      if (!cost) return null
      return `$${cost.toFixed(4)}`
    }

    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight mb-1">Pipeline Running</h1>
            <p className="text-muted-foreground text-sm">
              {runStateData?.run_id || runId}
            </p>
          </div>
          <Badge variant={getBadgeVariant()} className="text-xs">
            {getBadgeIcon()}
            <span aria-live="polite" aria-atomic="true">
              {getBadgeLabel()}
            </span>
          </Badge>
        </div>

        {runStateData?.background_error && (
          <Card className="mb-4 border-destructive" role="alert" aria-live="assertive">
            <CardContent className="py-3">
              <p className="text-sm text-destructive">{runStateData.background_error}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="py-4 px-0">
            {stageIds.length === 0 && (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                {runStateLoading ? 'Loading run state...' : 'No stages found'}
              </div>
            )}
            {stageIds.map((stageId, i) => {
              const stage = stages[stageId]
              if (!stage) return null
              const status = getStageStatus(stage.status)
              const duration = formatDuration(stage.duration_seconds)
              const cost = formatCost(stage.cost_usd)

              return (
                <div key={stageId}>
                  <div className="flex items-center gap-3 px-4 py-2.5">
                    {status === 'done' && (
                      <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                    )}
                    {status === 'running' && (
                      <Loader2 className="h-4 w-4 text-primary shrink-0 animate-spin" />
                    )}
                    {status === 'failed' && (
                      <XCircle className="h-4 w-4 text-destructive shrink-0" />
                    )}
                    {status === 'pending' && (
                      <Circle className="h-4 w-4 text-muted-foreground/40 shrink-0" />
                    )}
                    <span
                      className={cn(
                        'text-sm font-medium flex-1',
                        status === 'pending' && 'text-muted-foreground',
                        status === 'failed' && 'text-destructive',
                      )}
                    >
                      {humanizeStageName(stageId)}
                    </span>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {cost && <span>{cost}</span>}
                      {duration && <span>{duration}</span>}
                    </div>
                  </div>
                  {i < stageIds.length - 1 && <Separator />}
                </div>
              )
            })}
          </CardContent>
        </Card>

        {/* Scene overview strip */}
        {scenesData.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold text-muted-foreground mb-2">Scene Overview</h2>
            <SceneStrip scenes={scenesData} selectedIndex={selectedScene} onSelect={setSelectedScene} />
          </div>
        )}

        {/* Event log */}
        <div className="mt-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Event Log</h2>
          <Card>
            <CardContent className="p-0">
              <RunEventLog events={transformBackendEvents(runEventsData?.events)} maxHeight="300px" />
            </CardContent>
          </Card>
        </div>

        <div className="mt-4">
          <Button variant="outline" size="sm" onClick={() => setView('config')}>
            Configure New Run
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold tracking-tight mb-1">Pipeline</h1>
      <p className="text-muted-foreground text-sm mb-6">
        Configure and run the CineForge pipeline
      </p>

      <div className="space-y-4">
        {/* Input file */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Input</CardTitle>
          </CardHeader>
          <CardContent>
            {uploadedFile ? (
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-primary shrink-0" />
                    <div>
                      <p className="text-sm font-medium">{uploadedFile.original_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(uploadedFile.size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setUploadedFile(null)}
                    disabled={uploadMutation.isPending || startRunMutation.isPending}
                  >
                    Replace
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div
                  role="button"
                  tabIndex={0}
                  aria-label="Drop screenplay file here or press Enter to browse files"
                  className={cn(
                    'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
                    dragOver
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-muted-foreground/40',
                    uploadMutation.isPending && 'opacity-50 pointer-events-none',
                  )}
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleFileDrop}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      document.getElementById('screenplay-file-input')?.click()
                    }
                  }}
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="h-8 w-8 text-muted-foreground mx-auto mb-3 animate-spin" />
                      <p className="text-sm font-medium mb-1">Uploading...</p>
                    </>
                  ) : (
                    <>
                      <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                      <p className="text-sm font-medium mb-1">Drop a screenplay here</p>
                      <p className="text-xs text-muted-foreground">
                        PDF, Final Draft (.fdx), Fountain, Markdown, TXT, or DOCX
                      </p>
                    </>
                  )}
                </div>
                <input
                  id="screenplay-file-input"
                  type="file"
                  accept=".fountain,.fdx,.txt,.md,.pdf,.docx"
                  className="sr-only"
                  onChange={(e) => {
                    const files = e.target.files
                    if (files && files.length > 0) {
                      const file = files[0]
                      uploadMutation.mutate(file, {
                        onSuccess: (data) => {
                          setUploadedFile(data)
                          toast.success(`Uploaded ${data.original_name} (${(data.size_bytes / 1024).toFixed(1)} KB)`)
                        },
                        onError: (error) => {
                          toast.error(`Upload failed: ${error.message}`)
                        }
                      })
                    }
                  }}
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => document.getElementById('screenplay-file-input')?.click()}
                  disabled={uploadMutation.isPending}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Browse Files
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recipe selector */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Recipe</CardTitle>
          </CardHeader>
          <CardContent>
            {recipesLoading ? (
              <div className="py-8 text-center">
                <Loader2 className="h-6 w-6 text-muted-foreground mx-auto mb-2 animate-spin" />
                <p className="text-sm text-muted-foreground">Loading recipes...</p>
              </div>
            ) : (
              <div className="space-y-2">
                {recipes.map(recipe => (
                  <label
                    key={recipe.recipe_id}
                    className={cn(
                      'flex items-start gap-3 rounded-md border px-3 py-2.5 cursor-pointer transition-colors',
                      selectedRecipe === recipe.recipe_id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-accent/50',
                    )}
                  >
                    <input
                      type="radio"
                      name="recipe"
                      value={recipe.recipe_id}
                      checked={selectedRecipe === recipe.recipe_id}
                      onChange={() => setSelectedRecipe(recipe.recipe_id)}
                      aria-label={`Select ${recipe.name} recipe`}
                      className="mt-0.5 accent-[oklch(0.68_0.12_175)]"
                    />
                    <div>
                      <p className="text-sm font-medium">{recipe.name}</p>
                      <p className="text-xs text-muted-foreground">{recipe.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Advanced settings */}
        <Card>
          <CardHeader className="pb-0">
            <button
              aria-expanded={showAdvanced}
              aria-controls="advanced-settings-panel"
              aria-label="Toggle advanced settings"
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setShowAdvanced(v => !v)}
            >
              {showAdvanced ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              Advanced Settings
            </button>
          </CardHeader>
          {showAdvanced && (
            <CardContent id="advanced-settings-panel" className="pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="default-model" className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Default Model
                  </label>
                  <Input
                    id="default-model"
                    value={defaultModel}
                    onChange={e => setDefaultModel(e.target.value)}
                    className="text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="work-model" className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Work Model
                  </label>
                  <Input
                    id="work-model"
                    value={workModel}
                    onChange={e => setWorkModel(e.target.value)}
                    className="text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="verify-model" className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Verify Model
                  </label>
                  <Input
                    id="verify-model"
                    value={verifyModel}
                    onChange={e => setVerifyModel(e.target.value)}
                    placeholder="Same as default"
                    className="text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="start-from" className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Start From Stage
                  </label>
                  <Input
                    id="start-from"
                    value={startFrom}
                    onChange={e => setStartFrom(e.target.value)}
                    placeholder="Beginning"
                    className="text-sm"
                  />
                </div>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Run button */}
        <Button
          size="lg"
          className="w-full"
          onClick={handleStartRun}
          disabled={!uploadedFile || uploadMutation.isPending || startRunMutation.isPending}
        >
          {startRunMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Start Run
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
