import { useEffect, useRef, useState, Suspense, lazy } from 'react'
// Chat loading moved to useChatLoader in AppShell — runs on every page.
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Film,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Package,
  Inbox,
  Pencil,
  Share,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ExportModal } from '@/components/ExportModal'
import { ProductionFormatPill } from '@/components/ProductionFormatPill'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  useProject,
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
import { actionableHealthGroups, healthLabel } from '@/lib/health'
import { cn } from '@/lib/utils'
import type { ProjectState, ProjectSummary } from '@/lib/types'

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
      const updatedProject = await updateProjectSettings(projectId, { display_name: trimmed })
      queryClient.setQueryData<ProjectSummary>(['projects', projectId], updatedProject)
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
  const { hash } = useLocation()
  const scrolledToHashRef = useRef<string | null>(null)
  const { data: project } = useProject(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)
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
  const attentionGroups = actionableHealthGroups(artifactGroups)
  const attentionArtifacts = attentionGroups.length
  const totalArtifacts = artifactGroups?.length ?? 0
  const currentArtifacts = Math.max(totalArtifacts - attentionArtifacts, 0)

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

  // Scroll to scene heading when the URL hash targets one (e.g. #INT.%20CABIN).
  // Retries with backoff until CodeMirror has loaded content.
  // Tracks which hash was last scrolled so re-fetches don't re-jump after the user scrolls away.
  useEffect(() => {
    if (!hash || !content) return
    if (hash === scrolledToHashRef.current) return

    const heading = decodeURIComponent(hash.slice(1))
    const delays = [200, 400, 800]
    const timers: ReturnType<typeof setTimeout>[] = []

    const tryScroll = (attempt: number) => {
      const scrolled = editorRef.current?.scrollToHeading(heading) ?? false
      if (scrolled) {
        scrolledToHashRef.current = hash
        return
      }
      const nextDelay = delays[attempt + 1]
      if (nextDelay !== undefined) {
        timers.push(setTimeout(() => tryScroll(attempt + 1), nextDelay))
      }
    }

    timers.push(setTimeout(() => tryScroll(0), delays[0]))
    return () => timers.forEach(clearTimeout)
  }, [hash, content])

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
        <div className="flex items-start gap-3">
          <FileText className="h-6 w-6 text-primary shrink-0 mt-1" />
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
              {project?.production_format && (
                <ProductionFormatPill
                  projectId={projectId}
                  value={project.production_format}
                  mode="intent-link"
                  className="h-7 rounded-full px-2.5 text-xs"
                />
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

      {totalArtifacts > 0 && (
        <Card className={cn(attentionArtifacts > 0 && 'border-amber-500/30 bg-amber-500/5')}>
          <CardContent className="flex flex-col gap-4 py-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="rounded-full border border-border bg-muted/30 p-2">
                  {attentionArtifacts > 0 ? (
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                  )}
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-semibold">Artifact Health</div>
                  <p className="text-sm text-muted-foreground">
                    {attentionArtifacts > 0
                      ? `${attentionArtifacts} artifact${attentionArtifacts === 1 ? '' : 's'} need attention. ${currentArtifacts} current.`
                      : `All ${totalArtifacts} artifact${totalArtifacts === 1 ? '' : 's'} are current.`}
                  </p>
                </div>
              </div>

              {attentionArtifacts > 0 && (
                <div className="flex flex-wrap gap-2">
                  {attentionGroups.slice(0, 3).map((group) => (
                    <Button
                      key={`${group.artifact_type}-${group.entity_id ?? 'project'}`}
                      variant="outline"
                      size="sm"
                      className="justify-start text-left"
                      onClick={() => navigate(`/${projectId}/artifacts/${group.artifact_type}/${group.entity_id ?? 'project'}/${group.latest_version}`)}
                    >
                      {(group.entity_id ?? 'Project')}
                      {' · '}
                      {healthLabel(group.health).toLowerCase()}
                    </Button>
                  ))}
                  {attentionArtifacts > 3 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/${projectId}/inbox`)}
                    >
                      +{attentionArtifacts - 3} more
                    </Button>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {attentionArtifacts > 0 && (
                <Button onClick={() => navigate(`/${projectId}/inbox`)}>
                  <Inbox className="mr-2 h-4 w-4" />
                  Open Inbox
                </Button>
              )}
              <Button variant="outline" onClick={() => navigate(`/${projectId}/artifacts`)}>
                <Package className="mr-2 h-4 w-4" />
                Browse Artifacts
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

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
