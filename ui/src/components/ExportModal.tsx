import { useEffect, useRef, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { downloadExport, exportMarkdown, type ExportFormat, type ExportScope } from '@/lib/api'
import { useArtifactGroups } from '@/lib/hooks'
import { toast } from 'sonner'
import { FileDown, Copy, FileText, CheckSquare, Square, FileCode, Clapperboard } from 'lucide-react'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  projectId: string
  defaultScope?: ExportScope
  entityId?: string
  entityType?: 'scene' | 'character' | 'location' | 'prop'
}

type ExportComponent = 'script' | 'scenes' | 'characters' | 'locations' | 'props'

function ExportButton({
  children,
  className,
  ...props
}: React.ComponentProps<typeof Button>) {
  return (
    <Button
      variant="outline"
      className={`h-auto justify-start px-3 py-2 text-left whitespace-normal ${className ?? ''}`.trim()}
      {...props}
    >
      {children}
    </Button>
  )
}

export function ExportModal({
  isOpen,
  onClose,
  projectId,
  defaultScope = 'everything',
  entityId,
  entityType,
}: ExportModalProps) {
  const bodyRef = useRef<HTMLDivElement>(null)
  const scope = defaultScope
  const [selectedComponents, setSelectedComponents] = useState<ExportComponent[]>([
    'script',
    'scenes',
    'characters',
    'locations',
    'props',
  ])
  const { data: artifactGroups } = useArtifactGroups(projectId)

  useEffect(() => {
    if (!isOpen) return
    bodyRef.current?.scrollTo({ top: 0, left: 0 })
  }, [entityId, entityType, isOpen, scope])

  const hasShotPlans = (artifactGroups ?? []).some((group) => group.artifact_type === 'shot_plan')
  const hasTimeline = (artifactGroups ?? []).some((group) => group.artifact_type === 'timeline')
  const hasScenes = (artifactGroups ?? []).some((group) => group.artifact_type === 'scene')
  const hasCharacters = (artifactGroups ?? []).some((group) => group.artifact_type === 'character_bible')
  const hasLocations = (artifactGroups ?? []).some((group) => group.artifact_type === 'location_bible')
  const hasProps = (artifactGroups ?? []).some((group) => group.artifact_type === 'prop_bible')
  const hasStructuredProjectData = hasScenes || hasCharacters || hasLocations || hasProps
  const onlyScriptSelected =
    selectedComponents.length === 1 && selectedComponents[0] === 'script'
  const canExportProjectPdf =
    selectedComponents.length > 0 && (onlyScriptSelected || hasStructuredProjectData)
  const showShotListExports =
    scope === 'everything'
      || scope === 'scenes'
      || (scope === 'single' && entityType === 'scene')

  const formatLabels: Record<ExportFormat, string> = {
    markdown: 'Markdown',
    pdf: 'PDF',
    'call-sheet': 'Call Sheet',
    fcpxml: 'FCPXML',
    fountain: 'Fountain',
    docx: 'DOCX',
    'shot-list-csv': 'Shot List CSV',
    'shot-list-pdf': 'Shot List PDF',
  }

  const toggleComponent = (comp: ExportComponent) => {
    setSelectedComponents((prev) =>
      prev.includes(comp) ? prev.filter((c) => c !== comp) : [...prev, comp],
    )
  }

  const toggleAll = () => {
    if (selectedComponents.length === 5) {
      setSelectedComponents([])
      return
    }
    setSelectedComponents(['script', 'scenes', 'characters', 'locations', 'props'])
  }

  const handleCopyMarkdown = async (includeOverride?: ExportComponent[]) => {
    try {
      const content = await exportMarkdown(
        projectId,
        scope,
        entityId,
        entityType,
        includeOverride || selectedComponents,
      )
      await navigator.clipboard.writeText(content)
      toast.success('Copied Markdown to clipboard')
      onClose()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to copy markdown')
      console.error(error)
    }
  }

  const handleDownload = async (format: ExportFormat, includeOverride?: ExportComponent[]) => {
    try {
      await downloadExport(
        projectId,
        format,
        scope,
        entityId,
        entityType,
        includeOverride || selectedComponents,
      )
      toast.success(`${formatLabels[format]} export downloaded`)
      onClose()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Export failed')
      console.error(error)
    }
  }

  const renderShotListExports = () => {
    if (!showShotListExports) return null

    const description = hasShotPlans
      ? 'Project-wide export built from the latest shot plans across all scenes.'
      : 'Run shot planning first to enable shot-list exports.'

    return (
      <div className="space-y-3 pt-2">
        <Separator />
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Shot List</p>
          <p className={`text-xs ${hasShotPlans ? 'text-muted-foreground' : 'text-amber-500'}`}>
            {description}
          </p>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <ExportButton onClick={() => handleDownload('shot-list-csv')} disabled={!hasShotPlans}>
            <Clapperboard className="mr-2 h-4 w-4" />
            <div className="min-w-0 text-left">
              <div className="font-medium text-sm">Shot List CSV</div>
              <div className="text-xs text-muted-foreground">Crew-friendly spreadsheet export</div>
            </div>
          </ExportButton>
          <ExportButton onClick={() => handleDownload('shot-list-pdf')} disabled={!hasShotPlans}>
            <FileText className="mr-2 h-4 w-4" />
            <div className="min-w-0 text-left">
              <div className="font-medium text-sm">Shot List PDF</div>
              <div className="text-xs text-muted-foreground">Readable formatted shot list</div>
            </div>
          </ExportButton>
        </div>
      </div>
    )
  }

  const renderInterchangeExports = () => {
    const description = hasTimeline
      ? 'Timeline-backed interchange with scene markers, beats, character entrances/exits, and mood notes.'
      : 'Run timeline generation first to enable FCPXML interchange export.'

    return (
      <div className="space-y-3 pt-2">
        <Separator />
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Interchange</p>
          <p className={`text-xs ${hasTimeline ? 'text-muted-foreground' : 'text-amber-500'}`}>
            {description}
          </p>
        </div>
        <ExportButton className="w-full" onClick={() => handleDownload('fcpxml')} disabled={!hasTimeline}>
          <FileCode className="mr-2 h-4 w-4" />
          <div className="min-w-0 text-left">
            <div className="font-medium text-sm">FCPXML</div>
            <div className="text-xs text-muted-foreground">Narrative timeline interchange export</div>
          </div>
        </ExportButton>
      </div>
    )
  }

  const getTitle = () => {
    switch (scope) {
      case 'everything':
        return 'Export Project'
      case 'scenes':
        return 'Export Scenes'
      case 'characters':
        return 'Export Characters'
      case 'locations':
        return 'Export Locations'
      case 'props':
        return 'Export Props'
      case 'single':
        return 'Export Entity'
      default:
        return 'Export'
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="flex max-h-[calc(100vh-1rem)] w-[calc(100vw-1rem)] max-w-[calc(100vw-1rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-[500px]">
        <DialogHeader className="shrink-0 px-4 pb-4 pt-5 sm:px-6">
          <DialogTitle>{getTitle()}</DialogTitle>
          <DialogDescription>
            Choose what to export and the format.
          </DialogDescription>
        </DialogHeader>

        <div ref={bodyRef} className="min-h-0 flex-1 overflow-y-auto px-4 pb-4 sm:px-6">
          {scope === 'everything' ? (
            <Tabs defaultValue="screenplay" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="screenplay">Screenplay</TabsTrigger>
                <TabsTrigger value="project">Project Data</TabsTrigger>
              </TabsList>

              <TabsContent value="screenplay" className="space-y-4 py-4">
                <div className="grid grid-cols-1 gap-3">
                  <ExportButton className="px-4 py-3" onClick={() => handleDownload('pdf', ['script'])}>
                    <FileText className="mr-3 h-5 w-5 text-red-400" />
                    <div className="min-w-0 text-left">
                      <div className="font-medium">Standard PDF</div>
                      <div className="text-xs text-muted-foreground">
                        Industry standard formatting (12pt Courier)
                      </div>
                    </div>
                  </ExportButton>
                  <ExportButton className="px-4 py-3" onClick={() => handleDownload('docx')}>
                    <FileText className="mr-3 h-5 w-5 text-blue-400" />
                    <div className="min-w-0 text-left">
                      <div className="font-medium">Microsoft Word (.docx)</div>
                      <div className="text-xs text-muted-foreground">Standard screenplay format</div>
                    </div>
                  </ExportButton>
                  <ExportButton className="px-4 py-3" onClick={() => handleDownload('fountain')}>
                    <FileCode className="mr-3 h-5 w-5 text-amber-400" />
                    <div className="min-w-0 text-left">
                      <div className="font-medium">Fountain File (.fountain)</div>
                      <div className="text-xs text-muted-foreground">Raw plaintext screenplay format</div>
                    </div>
                  </ExportButton>
                  <ExportButton className="px-4 py-3" onClick={() => handleCopyMarkdown(['script'])}>
                    <Copy className="mr-3 h-5 w-5 text-muted-foreground" />
                    <div className="min-w-0 text-left">
                      <div className="font-medium">Copy as Markdown</div>
                      <div className="text-xs text-muted-foreground">Fountain syntax in code block</div>
                    </div>
                  </ExportButton>
                </div>
              </TabsContent>

              <TabsContent value="project" className="space-y-4 py-2">
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-sm font-semibold">Included Components:</span>
                    <Button variant="ghost" size="sm" onClick={toggleAll} className="h-7 px-2 text-xs">
                      {selectedComponents.length === 5 ? 'Check None' : 'Check All'}
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {(['script', 'scenes', 'characters', 'locations', 'props'] as ExportComponent[]).map((comp) => (
                      <div
                        key={comp}
                        className="flex cursor-pointer items-center gap-2 rounded border border-transparent p-2 transition-colors hover:border-border hover:bg-accent/50"
                        onClick={() => toggleComponent(comp)}
                      >
                        {selectedComponents.includes(comp)
                          ? <CheckSquare className="h-4 w-4 text-primary" />
                          : <Square className="h-4 w-4 text-muted-foreground" />}
                        <span className="text-sm capitalize">{comp}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-3 pt-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Export Formats</p>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <ExportButton onClick={() => handleCopyMarkdown()} disabled={selectedComponents.length === 0}>
                      <Copy className="mr-2 h-4 w-4" />
                      <div className="min-w-0 text-left">
                        <div className="font-medium text-sm">Copy MD</div>
                      </div>
                    </ExportButton>
                    <ExportButton onClick={() => handleDownload('markdown')} disabled={selectedComponents.length === 0}>
                      <FileDown className="mr-2 h-4 w-4" />
                      <div className="min-w-0 text-left">
                        <div className="font-medium text-sm">Download MD</div>
                      </div>
                    </ExportButton>
                    <ExportButton onClick={() => void handleDownload('pdf')} disabled={!canExportProjectPdf}>
                      <FileText className="mr-2 h-4 w-4" />
                      <div className="min-w-0 text-left">
                        <div className="font-medium text-sm">
                          {onlyScriptSelected ? 'Screenplay PDF' : 'PDF Report'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {onlyScriptSelected
                            ? 'Only Script is selected, so this downloads the screenplay.'
                            : hasStructuredProjectData
                              ? 'Project report built from the latest breakdown artifacts.'
                              : 'Run basic breakdown first to enable this export.'}
                        </div>
                      </div>
                    </ExportButton>
                    <ExportButton onClick={() => void handleDownload('call-sheet')} disabled={!hasScenes}>
                      <FileText className="mr-2 h-4 w-4" />
                      <div className="min-w-0 text-left">
                        <div className="font-medium text-sm">Call Sheet</div>
                        <div className="text-xs text-muted-foreground">
                          {hasScenes
                            ? 'Narrative call sheet built from scene breakdown data.'
                            : 'Run basic breakdown first to enable call sheets.'}
                        </div>
                      </div>
                    </ExportButton>
                  </div>
                </div>

                {renderShotListExports()}
                {renderInterchangeExports()}
              </TabsContent>
            </Tabs>
          ) : (
            <div className="space-y-3 py-4">
              <div className="flex flex-col gap-3">
                <ExportButton className="px-4 py-3" onClick={() => handleCopyMarkdown()}>
                  <Copy className="mr-2 h-4 w-4" />
                  <div className="min-w-0 text-left">
                    <div className="font-medium">Copy Markdown</div>
                    <div className="text-xs opacity-70">To clipboard</div>
                  </div>
                </ExportButton>
                <ExportButton className="px-4 py-3" onClick={() => handleDownload('markdown')}>
                  <FileDown className="mr-2 h-4 w-4" />
                  <div className="min-w-0 text-left">
                    <div className="font-medium">Download Markdown</div>
                    <div className="text-xs opacity-70">.md file</div>
                  </div>
                </ExportButton>
              </div>

              {renderShotListExports()}
            </div>
          )}
        </div>

        <DialogFooter className="shrink-0 border-t px-4 py-3 sm:px-6">
          <Button variant="ghost" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
