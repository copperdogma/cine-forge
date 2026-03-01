import { useEffect, useRef, useState, Suspense, lazy } from 'react'
// Chat loading moved to useChatLoader in AppShell — runs on every page.
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
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
  Share,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ExportModal } from '@/components/ExportModal'
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
  useEntityResolver,
  useProjectInputs,
  useProjectInputContent,
  useCanonicalScript,
  useScriptBible,
  useProjectState,
} from '@/lib/hooks'
import { updateProjectSettings } from '@/lib/api'
import { cn } from '@/lib/utils'
import { timeAgo, formatDuration } from '@/lib/format'
import { getStatusConfig } from '@/components/StatusBadge'
import type { ProjectState } from '@/lib/types'

import type { ScreenplayEditorHandle, SceneDividerData } from '@/components/ScreenplayEditor'

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

// --- Script Bible Panel (expandable) ---

interface ScriptBibleData {
  logline?: string
  synopsis?: string
  genre?: string
  tone?: string
  narrative_arc?: string
  protagonist_journey?: string
  central_conflict?: string
  setting_overview?: string
  act_structure?: { act_number: number; title: string; summary: string; turning_points: string[] }[]
  themes?: { theme: string; description: string; evidence: string[] }[]
}

function ScriptBiblePanel({
  bible,
  expanded,
  onToggle,
}: {
  bible: ScriptBibleData
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/50">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 w-full px-3 py-2 text-left text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <BookOpen className="h-3.5 w-3.5 shrink-0 text-indigo-400" />
        <span className="font-medium">Script Bible</span>
        {expanded ? <ChevronUp className="h-3.5 w-3.5 ml-auto" /> : <ChevronDown className="h-3.5 w-3.5 ml-auto" />}
      </button>
      {expanded && (
        <div className="border-t border-border/40 max-h-[50vh] overflow-y-auto">
          <div className="px-4 pb-4 space-y-4 text-sm pt-4 max-w-3xl">
            {bible.tone && (
              <p className="text-muted-foreground italic">{bible.tone}</p>
            )}
            {bible.themes && bible.themes.length > 0 && (
              <TooltipProvider delayDuration={200}>
                <div className="flex flex-wrap gap-2">
                  {bible.themes.map(t => (
                    <Tooltip key={t.theme}>
                      <TooltipTrigger asChild>
                        <Badge variant="outline" className="text-indigo-300 border-indigo-500/20 cursor-default">
                          {t.theme}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-xs text-xs">
                        {t.description}
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              </TooltipProvider>
            )}
            {bible.synopsis && (
              <>
                <Separator className="opacity-30" />
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Synopsis</h4>
                  <p className="text-foreground/90 whitespace-pre-line leading-relaxed">{bible.synopsis}</p>
                </div>
              </>
            )}
            <Separator className="opacity-30" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {bible.central_conflict && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Central Conflict</h4>
                  <p className="text-foreground/90 leading-relaxed">{bible.central_conflict}</p>
                </div>
              )}
              {bible.protagonist_journey && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Protagonist Journey</h4>
                  <p className="text-foreground/90 leading-relaxed">{bible.protagonist_journey}</p>
                </div>
              )}
              {bible.narrative_arc && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Narrative Arc</h4>
                  <p className="text-foreground/90 leading-relaxed">{bible.narrative_arc}</p>
                </div>
              )}
              {bible.setting_overview && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Setting</h4>
                  <p className="text-foreground/90 leading-relaxed">{bible.setting_overview}</p>
                </div>
              )}
            </div>
            <Separator className="opacity-30" />
            {bible.act_structure && bible.act_structure.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Act Structure</h4>
                <div className="space-y-3">
                  {bible.act_structure.map(act => (
                    <div key={act.act_number} className="rounded-md border border-border/40 p-3">
                      <div className="font-medium text-foreground/90">
                        Act {act.act_number}: {act.title}
                      </div>
                      <p className="text-muted-foreground text-sm mt-1 leading-relaxed">{act.summary}</p>
                      {act.turning_points.length > 0 && (
                        <ul className="mt-1.5 text-sm text-muted-foreground list-disc list-inside space-y-0.5">
                          {act.turning_points.map((tp, i) => <li key={i}>{tp}</li>)}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// --- Fresh Import View: Screenplay displayed in CodeMirror ---

function FreshImportView({ projectId }: { projectId: string }) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: project } = useProject(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const { data: scenes } = useScenes(projectId)
  const { resolve } = useEntityResolver(projectId)
  const { data: canonicalScript, isLoading: canonicalLoading } = useCanonicalScript(projectId)
  const { data: scriptBibleArtifact } = useScriptBible(projectId)
  const latestInput = inputs?.[inputs.length - 1]
  const { data: rawContent, isLoading: rawLoading } = useProjectInputContent(projectId, latestInput?.filename)
  const editorRef = useRef<ScreenplayEditorHandle>(null)
  const [isExportOpen, setIsExportOpen] = useState(false)
  const [bibleExpanded, setBibleExpanded] = useState(false)

  // Extract script bible data
  const bible = scriptBibleArtifact?.payload?.data as {
    logline?: string
    synopsis?: string
    genre?: string
    tone?: string
    narrative_arc?: string
    protagonist_journey?: string
    central_conflict?: string
    setting_overview?: string
    act_structure?: { act_number: number; title: string; summary: string; turning_points: string[] }[]
    themes?: { theme: string; description: string; evidence: string[] }[]
  } | undefined

  // Favor normalized script over raw input
  const scriptData = canonicalScript?.payload?.data as { script_text?: string } | undefined
  const content = scriptData?.script_text ?? rawContent
  const isLoading = canonicalLoading || rawLoading

  const isNormalized = !!scriptData?.script_text

  // Build scene divider data for the editor
  const sceneDividers: SceneDividerData[] = (scenes ?? [])
    .filter(s => s.startLine != null && s.startLine > 0)
    .map(s => ({
      entityId: s.entityId,
      heading: s.heading,
      sceneNumber: s.index,
      startLine: s.startLine!,
    }))

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

  // When a scene heading line is clicked, navigate to its detail page
  const handleSceneHeadingClick = (heading: string) => {
    if (!scenes) return
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

  // When a character name line is clicked, navigate to that character's detail page
  const handleCharacterNameClick = (name: string) => {
    const resolved = resolve(name, 'character')
    if (resolved) navigate(resolved.path)
  }

  // When a scene divider bar is clicked, navigate directly by entityId
  const handleSceneDividerClick = (entityId: string) => {
    navigate(`/${projectId}/scenes/${entityId}`)
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4">
      {/* Header */}
      <div className="shrink-0 space-y-2">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-primary shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <EditableTitle
                projectId={projectId}
                displayName={project?.display_name ?? 'Your Screenplay'}
                className="text-2xl"
              />
              {isNormalized ? (
                <Badge variant="secondary" className="bg-green-500/10 text-green-400 border-green-500/20">
                  Canonical
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">
                  Raw Import
                </Badge>
              )}
              {bible?.genre && (
                <Badge variant="outline" className="text-indigo-400 border-indigo-500/30">
                  {bible.genre}
                </Badge>
              )}
            </div>
            {bible?.logline ? (
              <p className="text-sm text-muted-foreground italic">{bible.logline}</p>
            ) : latestInput ? (
              <p className="text-sm text-muted-foreground">
                {latestInput.original_name} — {(latestInput.size_bytes / 1024).toFixed(1)} KB
              </p>
            ) : null}
          </div>
          <Button variant="outline" onClick={() => setIsExportOpen(true)}>
            <Share className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
        {bible && (
          <ScriptBiblePanel bible={bible} expanded={bibleExpanded} onToggle={() => setBibleExpanded(e => !e)} />
        )}
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
              scenes={sceneDividers}
              onSceneHeadingClick={handleSceneHeadingClick}
              onCharacterNameClick={handleCharacterNameClick}
              onSceneDividerClick={handleSceneDividerClick}
            />
          </Suspense>
        </div>
      ) : (
        <div className="text-center py-20 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No screenplay content found.</p>
        </div>
      )}

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId}
        defaultScope="everything"
      />
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
                          {timeAgo(run.started_at * 1000)}
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
    case 'fresh_import':
    case 'analyzed':
    case 'complete':
      // OperationBanner (in AppShell) handles run status display globally.
      return <FreshImportView projectId={projectId} />
    default:
      return <EmptyView />
  }
}
