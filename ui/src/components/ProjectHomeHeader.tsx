import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, BookOpen, FileText, Film, Inbox, Pencil, Share } from 'lucide-react'
import { toast } from 'sonner'
import { FinalOutputCard, useFinalOutputController } from '@/components/FinalOutputCard'
import { ProductionFormatPill } from '@/components/ProductionFormatPill'
import { ScriptBiblePanel } from '@/components/ScriptBiblePanel'
import type { ScriptBibleData } from '@/components/ScriptBiblePanel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { updateProjectSettings } from '@/lib/api'
import { actionableHealthGroups } from '@/lib/health'
import type { ArtifactGroupSummary, ProjectSummary } from '@/lib/types'
import { cn } from '@/lib/utils'

type ProjectHomeHeaderProps = {
  projectId: string
  project?: ProjectSummary
  isNormalized: boolean
  bible?: ScriptBibleData
  inputDescription?: string
  latestInputPath: string | null
  sceneCount: number
  artifactGroups?: ArtifactGroupSummary[]
  onExport: () => void
}

// Keep the existing inline rename and query-cache behavior near the title it owns.
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

  useEffect(() => {
    if (!editing) setValue(displayName)
  }, [displayName, editing])

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
      toast.error(error instanceof Error ? error.message : 'Failed to rename')
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
        onChange={event => setValue(event.target.value)}
        onBlur={save}
        onKeyDown={event => {
          if (event.key === 'Enter') save()
          if (event.key === 'Escape') cancel()
        }}
        disabled={saving}
        aria-label="Project title"
        className={cn('w-full truncate border-b border-primary bg-transparent font-bold tracking-tight outline-none', className)}
      />
    )
  }

  return (
    <h1
      role="button"
      tabIndex={0}
      onClick={() => setEditing(true)}
      onKeyDown={event => { if (event.key === 'Enter') setEditing(true) }}
      className={cn('group flex min-w-0 cursor-pointer items-start gap-2 font-bold tracking-tight', className)}
    >
      {displayName}
      <Pencil className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
    </h1>
  )
}

function SupportingActions({
  projectId,
  bible,
  latestInputPath,
  sceneCount,
  artifactGroups,
  onExport,
}: Pick<ProjectHomeHeaderProps, 'projectId' | 'bible' | 'latestInputPath' | 'sceneCount' | 'artifactGroups' | 'onExport'>) {
  const [bibleOpen, setBibleOpen] = useState(false)
  const [cutOpen, setCutOpen] = useState(false)
  const hasCut = sceneCount > 0 || artifactGroups?.some(group => group.artifact_type === 'final_output')
  const finalOutputController = useFinalOutputController({
    projectId,
    latestInputPath,
    sceneCount,
    artifactGroups,
  })

  return (
    <div className="flex flex-wrap items-center gap-2">
      {sceneCount > 0 && (
        <Button asChild variant="outline" size="sm">
          <Link to={`/${projectId}/scenes`}>Scenes</Link>
        </Button>
      )}
      {bible && (
        <Dialog open={bibleOpen} onOpenChange={setBibleOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm"><BookOpen className="h-4 w-4" />Script Bible</Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-3xl">
            <DialogHeader>
              <DialogTitle>Script Bible</DialogTitle>
              <DialogDescription>Story overview, themes, and structure for this screenplay.</DialogDescription>
            </DialogHeader>
            {bibleOpen && <ScriptBiblePanel bible={bible} />}
            <DialogFooter showCloseButton />
          </DialogContent>
        </Dialog>
      )}
      {hasCut && (
        <Dialog open={cutOpen} onOpenChange={setCutOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm"><Film className="h-4 w-4" />Project Cut</Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-4xl">
            <DialogHeader>
              <DialogTitle>Project Cut</DialogTitle>
              <DialogDescription>Review, assemble, and validate the playable cut for this project.</DialogDescription>
            </DialogHeader>
            {cutOpen && (
              <FinalOutputCard controller={finalOutputController} />
            )}
            <DialogFooter showCloseButton />
          </DialogContent>
        </Dialog>
      )}
      <Button variant="outline" size="sm" onClick={onExport}>
        <Share className="h-4 w-4" />Export
      </Button>
    </div>
  )
}

export function ProjectHomeHeader({
  projectId,
  project,
  isNormalized,
  bible,
  inputDescription,
  latestInputPath,
  sceneCount,
  artifactGroups,
  onExport,
}: ProjectHomeHeaderProps) {
  const attentionCount = actionableHealthGroups(artifactGroups).length

  return (
    <header className="shrink-0 space-y-3">
      <div className="flex items-start gap-3">
        <FileText className="mt-1 h-6 w-6 shrink-0 text-primary" />
        <div className="min-w-0 flex-1 space-y-2">
          <EditableTitle
            projectId={projectId}
            displayName={project?.display_name ?? 'Your Screenplay'}
            className="text-2xl leading-tight break-words"
          />
          <div className="flex flex-wrap items-center gap-2">
            {isNormalized ? (
              <Badge variant="secondary" className="border-green-500/20 bg-green-500/10 text-green-400">Canonical</Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground">Raw Import</Badge>
            )}
            {bible?.genre && <Badge variant="outline" className="border-indigo-500/30 text-indigo-400">{bible.genre}</Badge>}
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
            <p className="break-words text-sm italic text-muted-foreground">{bible.logline}</p>
          ) : inputDescription ? (
            <p className="break-words text-sm text-muted-foreground">{inputDescription}</p>
          ) : null}
          <SupportingActions
            projectId={projectId}
            bible={bible}
            latestInputPath={latestInputPath}
            sceneCount={sceneCount}
            artifactGroups={artifactGroups}
            onExport={onExport}
          />
        </div>
      </div>
      {attentionCount > 0 && (
        <div role="status" className="flex flex-wrap items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>{attentionCount} artifact{attentionCount === 1 ? '' : 's'} need review.</span>
          <Button asChild variant="link" size="sm" className="h-auto px-0">
            <Link to={`/${projectId}/inbox`}><Inbox className="h-4 w-4" />Open Inbox</Link>
          </Button>
        </div>
      )}
    </header>
  )
}
