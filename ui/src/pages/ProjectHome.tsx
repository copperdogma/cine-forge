import { useEffect, useRef, useState, Suspense, lazy } from 'react'
// Chat loading moved to useChatLoader in AppShell — runs on every page.
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  Film,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  Package,
  Inbox,
  History,
  ExternalLink,
  Calendar,
  Pencil,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { SceneStrip } from '@/components/SceneStrip'
import {
  useProject,
  useRuns,
  useArtifactGroups,
  useScenes,
  useProjectInputs,
  useProjectInputContent,
  useProjectState,
} from '@/lib/hooks'
import { updateProjectSettings } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useChatStore } from '@/lib/chat-store'
import { useRunState } from '@/lib/hooks'
import { getStageStartMessage } from '@/lib/chat-messages'
import type { ProjectState } from '@/lib/types'

import type { ScreenplayEditorHandle } from '@/components/ScreenplayEditor'

const ScreenplayEditor = lazy(() =>
  import('@/components/ScreenplayEditor').then(m => ({ default: m.ScreenplayEditor })),
)

// --- Editable inline title ---

function EditableTitle({
  projectId,
  displayName,
  className,
}: {
  projectId: string
  displayName: string
  className?: string
}) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(displayName)
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  // Sync from prop when not editing
  useEffect(() => {
    if (!editing) setValue(displayName)
  }, [displayName, editing])

  // Focus + select all when entering edit mode
  useEffect(() => {
    if (editing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [editing])

  const save = async () => {
    const trimmed = value.trim()
    if (!trimmed || trimmed === displayName) {
      setValue(displayName)
      setEditing(false)
      return
    }
    setSaving(true)
    try {
      await updateProjectSettings(projectId, { display_name: trimmed })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setEditing(false)
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to rename'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  const cancel = () => {
    setValue(displayName)
    setEditing(false)
  }

  if (editing) {
    return (
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          if (e.key === 'Enter') save()
          if (e.key === 'Escape') cancel()
        }}
        disabled={saving}
        className={cn(
          'bg-transparent border-b border-primary outline-none font-bold tracking-tight truncate w-full',
          className,
        )}
      />
    )
  }

  return (
    <h1
      role="button"
      tabIndex={0}
      onClick={() => setEditing(true)}
      onKeyDown={(e) => { if (e.key === 'Enter') setEditing(true) }}
      className={cn(
        'font-bold tracking-tight truncate cursor-pointer group flex items-center gap-2',
        className,
      )}
    >
      {displayName}
      <Pencil className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
    </h1>
  )
}

// --- Shared helpers ---

function getStatusConfig(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return {
        icon: CheckCircle2,
        label: status === 'done' ? 'Done' : 'Reused',
        className: 'bg-green-500/20 text-green-400 border-green-500/30',
      }
    case 'failed':
      return {
        icon: AlertTriangle,
        label: 'Failed',
        className: 'bg-red-500/20 text-red-400 border-red-500/30',
      }
    case 'running':
      return {
        icon: Clock,
        label: 'Running',
        className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      }
    default:
      return {
        icon: Clock,
        label: 'Pending',
        className: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
      }
  }
}

function timeAgo(timestamp: number): string {
  const seconds = Math.floor(Date.now() / 1000 - timestamp)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

// --- Fresh Import View: Screenplay displayed in CodeMirror ---

function FreshImportView({ projectId }: { projectId: string }) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: project } = useProject(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const { data: scenes } = useScenes(projectId)
  const latestInput = inputs?.[inputs.length - 1]
  const { data: content, isLoading } = useProjectInputContent(projectId, latestInput?.filename)
  const editorRef = useRef<ScreenplayEditorHandle>(null)

  // Handle ?scene= query param — scroll to that scene heading after editor mounts
  useEffect(() => {
    const sceneParam = searchParams.get('scene')
    if (sceneParam && editorRef.current) {
      // Small delay to let CodeMirror finish rendering
      const timer = setTimeout(() => {
        editorRef.current?.scrollToHeading(sceneParam)
      }, 200)
      // Clear the param so it doesn't re-scroll on re-renders
      setSearchParams({}, { replace: true })
      return () => clearTimeout(timer)
    }
  }, [searchParams, setSearchParams, content])

  // When a scene heading is clicked in the editor, navigate to its detail page
  const handleSceneHeadingClick = (heading: string) => {
    if (!scenes) return
    // Normalize for matching
    const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')
    const headingNorm = norm(heading)
    const scene = scenes.find(s => {
      const sNorm = norm(s.heading)
      return sNorm === headingNorm || headingNorm.includes(sNorm) || sNorm.includes(headingNorm)
    })
    if (scene) {
      navigate(`/${projectId}/scenes/${scene.entityId}`)
    }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4">
      {/* Header */}
      <div className="flex items-center gap-3 shrink-0">
        <FileText className="h-6 w-6 text-primary shrink-0" />
        <div className="min-w-0 flex-1">
          <EditableTitle
            projectId={projectId}
            displayName={project?.display_name ?? 'Your Screenplay'}
            className="text-2xl"
          />
          {latestInput && (
            <p className="text-sm text-muted-foreground">
              {latestInput.original_name} — {(latestInput.size_bytes / 1024).toFixed(1)} KB
            </p>
          )}
        </div>
      </div>

      {/* Screenplay content — fills remaining space */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading screenplay...</span>
        </div>
      ) : content ? (
        <div className="flex-1 min-h-0 overflow-hidden">
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            }
          >
            <ScreenplayEditor
              ref={editorRef}
              content={content}
              readOnly
              onSceneHeadingClick={handleSceneHeadingClick}
            />
          </Suspense>
        </div>
      ) : (
        <div className="text-center py-20 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No screenplay content found.</p>
        </div>
      )}
    </div>
  )
}

// --- Analyzed / Complete View: Dashboard with scenes, artifacts, runs ---

// TODO: Wire AnalyzedView into project state switch (Story 041 Phase 3)
export function AnalyzedView({ projectId }: { projectId: string }) {
  const navigate = useNavigate()
  const { data: project } = useProject(projectId)
  const { data: runs } = useRuns(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const { data: scenes, isLoading: scenesLoading } = useScenes(projectId)

  const totalRuns = runs?.length ?? 0
  const completedRuns = runs?.filter(r => r.status === 'done').length ?? 0
  const failedRuns = runs?.filter(r => r.status === 'failed').length ?? 0
  const totalArtifacts = artifactGroups?.length ?? 0
  const staleArtifacts = artifactGroups?.filter(g => g.health === 'stale').length ?? 0

  const recentRuns = runs
    ? [...runs].sort((a, b) => (b.started_at ?? 0) - (a.started_at ?? 0)).slice(0, 5)
    : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Film className="h-8 w-8 text-primary" />
        <div className="min-w-0 flex-1">
          <EditableTitle
            projectId={projectId}
            displayName={project?.display_name ?? projectId}
            className="text-3xl"
          />
          <p className="text-sm text-muted-foreground">
            {totalArtifacts} artifacts · {totalRuns} runs
          </p>
        </div>
      </div>

      <Separator />

      {/* Scene overview */}
      {scenes && scenes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Scenes</CardTitle>
            <CardDescription>
              {scenes.length} scene{scenes.length !== 1 ? 's' : ''} detected
            </CardDescription>
          </CardHeader>
          <CardContent className="px-0">
            {scenesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <SceneStrip scenes={scenes} />
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="cursor-pointer hover:bg-accent/30 transition-colors" onClick={() => navigate('artifacts')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Package className="h-5 w-5 text-muted-foreground" />
              <div>
                <div className="text-2xl font-bold">{totalArtifacts}</div>
                <p className="text-xs text-muted-foreground">
                  {staleArtifacts > 0
                    ? <><span className="text-amber-400">{staleArtifacts} stale</span> · {totalArtifacts - staleArtifacts} healthy</>
                    : 'All healthy'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-accent/30 transition-colors" onClick={() => navigate('runs')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <History className="h-5 w-5 text-muted-foreground" />
              <div>
                <div className="text-2xl font-bold">{totalRuns}</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-400">{completedRuns} completed</span>
                  {failedRuns > 0 && <> · <span className="text-red-400">{failedRuns} failed</span></>}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-accent/30 transition-colors" onClick={() => navigate('inbox')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Inbox className="h-5 w-5 text-muted-foreground" />
              <div>
                <div className="text-2xl font-bold">{staleArtifacts}</div>
                <p className="text-xs text-muted-foreground">
                  {staleArtifacts > 0 ? 'Items need attention' : 'Inbox clear'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent runs */}
      {recentRuns.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Runs</CardTitle>
              <Button variant="outline" size="sm" onClick={() => navigate('runs')} className="gap-2">
                View All <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentRuns.map(run => {
                const statusConfig = getStatusConfig(run.status)
                const StatusIcon = statusConfig.icon
                const duration = run.finished_at && run.started_at
                  ? formatDuration(run.finished_at - run.started_at)
                  : null
                return (
                  <div
                    key={run.run_id}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer"
                    onClick={() => navigate(`runs/${run.run_id}`)}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <StatusIcon className={cn('h-4 w-4 shrink-0', statusConfig.className)} />
                      <span className="font-mono text-sm truncate">{run.run_id}</span>
                      <Badge variant="outline" className={cn('text-xs px-1.5 py-0', statusConfig.className)}>
                        {statusConfig.label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground shrink-0">
                      {run.started_at && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {timeAgo(run.started_at)}
                        </span>
                      )}
                      {duration && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {duration}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Artifact health */}
      {totalArtifacts > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Artifact Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center justify-between cursor-help">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-400" />
                        <span className="text-sm">Healthy</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono text-muted-foreground">
                          {totalArtifacts - staleArtifacts}
                        </span>
                        <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500"
                            style={{ width: `${((totalArtifacts - staleArtifacts) / totalArtifacts) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>Up to date and passed all quality checks.</TooltipContent>
                </Tooltip>
              </TooltipProvider>
              {staleArtifacts > 0 && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center justify-between cursor-help">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-400" />
                          <span className="text-sm">Stale</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono text-muted-foreground">{staleArtifacts}</span>
                          <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500"
                              style={{ width: `${(staleArtifacts / totalArtifacts) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>Upstream changes detected. Regeneration recommended.</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// --- Processing View: Screenplay with processing banner ---

function ProcessingView({ projectId }: { projectId: string }) {
  const activeRunId = useChatStore(s => s.activeRunId?.[projectId] ?? null)
  const { data: runState } = useRunState(activeRunId ?? undefined)

  // Find the currently running stage to show its description
  let statusText = 'Processing your screenplay...'
  let detailText = 'Extracting scenes, characters, and locations.'
  if (runState) {
    const stages = runState.state.stages
    const runningStage = Object.entries(stages).find(([, s]) => s.status === 'running')
    if (runningStage) {
      statusText = getStageStartMessage(runningStage[0])
      detailText = ''
    }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4">
      <div className="flex items-center gap-3 rounded-lg border border-blue-500/30 bg-blue-500/10 p-3 shrink-0">
        <Loader2 className="h-5 w-5 text-blue-400 animate-spin shrink-0" />
        <div>
          <p className="text-sm font-medium text-blue-400">{statusText}</p>
          {detailText && <p className="text-xs text-muted-foreground">{detailText}</p>}
        </div>
      </div>
      <FreshImportView projectId={projectId} />
    </div>
  )
}

// --- Empty View: No inputs uploaded ---

function EmptyView() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Film className="h-16 w-16 text-muted-foreground/30 mb-4" />
      <h2 className="text-xl font-semibold mb-2">No screenplay yet</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Upload a screenplay to begin building your story world.
      </p>
      <Button onClick={() => navigate('/new')}>Upload Screenplay</Button>
    </div>
  )
}

// --- Main component ---

export default function ProjectHome() {
  const { projectId } = useParams()
  const projectState = useProjectState(projectId)
  const { isLoading } = useProject(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading project...</span>
      </div>
    )
  }

  if (!projectId) return <EmptyView />

  return <HomeContent projectId={projectId} projectState={projectState} />
}

function HomeContent({ projectId, projectState }: { projectId: string; projectState: ProjectState }) {
  switch (projectState) {
    case 'empty':
      return <EmptyView />
    case 'processing':
      return <ProcessingView projectId={projectId} />
    case 'fresh_import':
    case 'analyzed':
    case 'complete':
      return <FreshImportView projectId={projectId} />
    default:
      return <EmptyView />
  }
}
