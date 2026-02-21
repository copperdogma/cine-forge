import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useExportData } from '@/lib/hooks'
import { generateProjectMarkdown, generateSceneMarkdown, generateCharacterMarkdown, generateLocationMarkdown, generatePropMarkdown, generateScenesMarkdown, generateCharactersMarkdown, generateLocationsMarkdown, generatePropsMarkdown } from '@/lib/export/markdown'
import { exportProjectPDF, exportCallSheet } from '@/lib/export/pdf'
import { toast } from 'sonner'
import { Loader2, FileDown, Copy, FileText } from 'lucide-react'

type ExportScope = 'everything' | 'scenes' | 'characters' | 'locations' | 'props' | 'single'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  projectId: string
  defaultScope?: ExportScope
  entityId?: string
  entityType?: 'scene' | 'character' | 'location' | 'prop'
}

export function ExportModal({
  isOpen,
  onClose,
  projectId,
  defaultScope = 'everything',
  entityId,
  entityType
}: ExportModalProps) {
  const { data, isLoading } = useExportData(projectId)

  // Determine effective scope based on props (no user selection anymore)
  const scope = defaultScope

  const getMarkdownContent = () => {
    if (!data) return ''
    switch (scope) {
      case 'everything':
        return generateProjectMarkdown(data.summary, data.scenes, data.characters, data.locations, data.props)
      case 'scenes':
        return generateScenesMarkdown(data.scenes)
      case 'characters':
        return generateCharactersMarkdown(data.characters)
      case 'locations':
        return generateLocationsMarkdown(data.locations)
      case 'props':
        return generatePropsMarkdown(data.props)
      case 'single':
        if (entityType === 'scene' && entityId) {
          const scene = data.scenes.find(s => s.entityId === entityId)
          if (scene) return generateSceneMarkdown(scene)
        } else if (entityType === 'character' && entityId) {
          const char = data.characters.find(c => c.entity_id === entityId)
          if (char) return generateCharacterMarkdown(char)
        } else if (entityType === 'location' && entityId) {
          const loc = data.locations.find(l => l.entity_id === entityId)
          if (loc) return generateLocationMarkdown(loc)
        } else if (entityType === 'prop' && entityId) {
          const prop = data.props.find(p => p.entity_id === entityId)
          if (prop) return generatePropMarkdown(prop)
        }
        return ''
      default:
        return ''
    }
  }

  const getFilename = (ext: string) => {
    const base = scope === 'single' && entityId ? entityId : scope
    return `${base}-${projectId}.${ext}`
  }

  const handleCopyMarkdown = async () => {
    const content = getMarkdownContent()
    if (!content) {
        toast.error('No content to export')
        return
    }
    await navigator.clipboard.writeText(content)
    toast.success('Copied Markdown to clipboard')
    onClose()
  }

  const handleDownloadMarkdown = () => {
    const content = getMarkdownContent()
    if (!content) {
        toast.error('No content to export')
        return
    }
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = getFilename('md')
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Download started')
    onClose()
  }

  const handleDownloadPDF = () => {
    if (!data) return
    exportProjectPDF(data.summary, data.scenes, data.characters, data.locations, data.props)
    onClose()
  }

  const handleDownloadCallSheet = () => {
    if (!data) return
    exportCallSheet(data.summary, data.scenes, data.characters, data.locations)
    onClose()
  }

  const getTitle = () => {
      switch(scope) {
          case 'everything': return 'Export Project'
          case 'scenes': return 'Export Scenes'
          case 'characters': return 'Export Characters'
          case 'locations': return 'Export Locations'
          case 'props': return 'Export Props'
          case 'single': return 'Export Entity'
          default: return 'Export'
      }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>{getTitle()}</DialogTitle>
          <DialogDescription>
            Select an export format.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="flex flex-col gap-3 py-4">
            <Button
              variant="outline"
              className="justify-start h-auto py-3 px-4"
              onClick={handleCopyMarkdown}
            >
              <Copy className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-medium">Copy Markdown</div>
                <div className="text-xs opacity-70">To clipboard</div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="justify-start h-auto py-3 px-4"
              onClick={handleDownloadMarkdown}
            >
              <FileDown className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-medium">Download Markdown</div>
                <div className="text-xs opacity-70">.md file</div>
              </div>
            </Button>
            {scope === 'everything' && (
                <>
                <Button
                variant="outline"
                className="justify-start h-auto py-3 px-4"
                onClick={handleDownloadPDF}
                >
                <FileText className="mr-2 h-4 w-4" />
                <div className="text-left">
                    <div className="font-medium">Download PDF Report</div>
                    <div className="text-xs opacity-70">Formatted document</div>
                </div>
                </Button>
                <Button
                variant="outline"
                className="justify-start h-auto py-3 px-4"
                onClick={handleDownloadCallSheet}
                >
                <FileText className="mr-2 h-4 w-4" />
                <div className="text-left">
                    <div className="font-medium">Download Call Sheet</div>
                    <div className="text-xs opacity-70">Grouped by location</div>
                </div>
                </Button>
                </>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
