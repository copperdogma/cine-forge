import { useEffect, useRef, useState, Suspense, lazy } from 'react'
import type { RefObject } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { Film, FileText, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ExportModal } from '@/components/ExportModal'
import { ProjectHomeHeader } from '@/components/ProjectHomeHeader'
import type { ScriptBibleData } from '@/components/ScriptBiblePanel'
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
import type { ProjectState } from '@/lib/types'
import type { ScreenplayEditorHandle, SceneDividerData } from '@/components/ScreenplayEditor'

const ScreenplayEditor = lazy(() =>
  import('@/components/ScreenplayEditor').then(m => ({ default: m.ScreenplayEditor })),
)

function useSceneHashScroll(
  hash: string,
  content: string | undefined,
  editorRef: RefObject<ScreenplayEditorHandle | null>,
) {
  const scrolledToHashRef = useRef<string | null>(null)
  useEffect(() => {
    if (!hash || !content || hash === scrolledToHashRef.current) return
    const heading = decodeURIComponent(hash.slice(1))
    const delays = [200, 400, 800]
    const timers: ReturnType<typeof setTimeout>[] = []
    const tryScroll = (attempt: number) => {
      if (editorRef.current?.scrollToHeading(heading)) {
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
  }, [hash, content, editorRef])
}

function useHomeScript(projectId: string, editorRef: RefObject<ScreenplayEditorHandle | null>) {
  const navigate = useNavigate()
  const { hash } = useLocation()
  const { data: project } = useProject(projectId)
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const { data: inputs } = useProjectInputs(projectId)
  const { data: scenes } = useScenes(projectId)
  const { resolve } = useEntityResolver(projectId)
  const { data: canonicalScript, isLoading: canonicalLoading } = useCanonicalScript(projectId)
  const { data: scriptBibleArtifact } = useScriptBible(projectId)
  const latestInput = inputs?.[inputs.length - 1]
  const { data: rawContent, isLoading: rawLoading } = useProjectInputContent(projectId, latestInput?.filename)
  const bible = scriptBibleArtifact?.payload?.data as ScriptBibleData | undefined
  const scriptData = canonicalScript?.payload?.data as { script_text?: string } | undefined
  const content = scriptData?.script_text ?? rawContent
  const sceneDividers: SceneDividerData[] = (scenes ?? [])
    .filter(s => s.startLine != null && s.startLine > 0)
    .map(s => ({
      entityId: s.entityId,
      heading: s.heading,
      sceneNumber: s.index,
      startLine: s.startLine!,
    }))

  useSceneHashScroll(hash, content, editorRef)

  const onSceneHeadingClick = (heading: string) => {
    if (!scenes) return
    const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')
    const headingNorm = norm(heading)
    const scene = scenes.find(s => {
      const sceneNorm = norm(s.heading)
      return sceneNorm === headingNorm || headingNorm.includes(sceneNorm) || sceneNorm.includes(headingNorm)
    })
    if (scene) navigate(`/${projectId}/scenes/${scene.entityId}`)
  }
  const onCharacterNameClick = (name: string) => {
    const resolved = resolve(name, 'character')
    if (resolved) navigate(resolved.path)
  }
  const onSceneDividerClick = (entityId: string) => {
    navigate(`/${projectId}/scenes/${entityId}`)
  }

  return {
    project, artifactGroups, latestInput, bible, content, sceneDividers,
    sceneCount: scenes?.length ?? 0,
    isLoading: canonicalLoading || rawLoading,
    isNormalized: !!scriptData?.script_text,
    onSceneHeadingClick, onCharacterNameClick, onSceneDividerClick,
  }
}

function ScreenplayContent({ state, editorRef }: {
  state: ReturnType<typeof useHomeScript>
  editorRef: RefObject<ScreenplayEditorHandle | null>
}) {
  if (state.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading screenplay...</span>
      </div>
    )
  }
  if (!state.content) {
    return (
      <div className="text-center py-20 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p className="text-sm">No screenplay content found.</p>
      </div>
    )
  }
  return (
    <div className="flex-1 min-h-0 overflow-hidden">
      <Suspense fallback={<div className="flex items-center justify-center h-full"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
        <ScreenplayEditor
          ref={editorRef}
          content={state.content}
          readOnly
          scenes={state.sceneDividers}
          onSceneHeadingClick={state.onSceneHeadingClick}
          onCharacterNameClick={state.onCharacterNameClick}
          onSceneDividerClick={state.onSceneDividerClick}
        />
      </Suspense>
    </div>
  )
}

function FreshImportView({ projectId }: { projectId: string }) {
  const editorRef = useRef<ScreenplayEditorHandle>(null)
  const state = useHomeScript(projectId, editorRef)
  const [isExportOpen, setIsExportOpen] = useState(false)
  const inputDescription = state.latestInput
    ? `${state.latestInput.original_name} — ${(state.latestInput.size_bytes / 1024).toFixed(1)} KB`
    : undefined
  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4">
      <ProjectHomeHeader
        projectId={projectId}
        project={state.project}
        isNormalized={state.isNormalized}
        bible={state.bible}
        inputDescription={inputDescription}
        latestInputPath={state.latestInput?.stored_path ?? null}
        sceneCount={state.sceneCount}
        artifactGroups={state.artifactGroups}
        onExport={() => setIsExportOpen(true)}
      />
      <ScreenplayContent state={state} editorRef={editorRef} />
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId}
        defaultScope="everything"
      />
    </div>
  )
}

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
      return <FreshImportView projectId={projectId} />
    default:
      return <EmptyView />
  }
}
