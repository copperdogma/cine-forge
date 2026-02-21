import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { exportMarkdown, getExportUrl, type ExportScope } from '@/lib/api'
import { toast } from 'sonner'
import { FileDown, Copy, FileText, CheckSquare, Square } from 'lucide-react'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  projectId: string
  defaultScope?: ExportScope
  entityId?: string
  entityType?: 'scene' | 'character' | 'location' | 'prop'
}

type ExportComponent = 'script' | 'scenes' | 'characters' | 'locations' | 'props'

export function ExportModal({
  isOpen,
  onClose,
  projectId,
  defaultScope = 'everything',
  entityId,
  entityType
}: ExportModalProps) {
  const scope = defaultScope
  const [selectedComponents, setSelectedComponents] = useState<ExportComponent[]>([
    'script', 'scenes', 'characters', 'locations', 'props'
  ])

  const toggleComponent = (comp: ExportComponent) => {
    setSelectedComponents(prev => 
      prev.includes(comp) ? prev.filter(c => c !== comp) : [...prev, comp]
    )
  }

  const toggleAll = () => {
    if (selectedComponents.length === 5) {
      setSelectedComponents([])
    } else {
      setSelectedComponents(['script', 'scenes', 'characters', 'locations', 'props'])
    }
  }

  const handleCopyMarkdown = async () => {
    try {
      const content = await exportMarkdown(projectId, scope, entityId, entityType, selectedComponents)
      await navigator.clipboard.writeText(content)
      toast.success('Copied Markdown to clipboard')
      onClose()
    } catch (error) {
      toast.error('Failed to copy markdown')
      console.error(error)
    }
  }

  const handleDownloadMarkdown = () => {
    window.location.href = getExportUrl(projectId, 'markdown', scope, entityId, entityType, selectedComponents)
    toast.success('Download started')
    onClose()
  }

  const handleDownloadPDF = () => {
    window.location.href = getExportUrl(projectId, 'pdf', 'everything')
    toast.success('PDF generation started')
    onClose()
  }

  const handleDownloadCallSheet = () => {
    window.location.href = getExportUrl(projectId, 'call-sheet', 'everything')
    toast.success('Call sheet generation started')
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
            Select content and format.
          </DialogDescription>
        </DialogHeader>

        {scope === 'everything' && (
          <div className="space-y-3 py-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Include:</span>
              <Button variant="ghost" size="sm" onClick={toggleAll} className="h-6 text-xs px-2">
                {selectedComponents.length === 5 ? 'Check None' : 'Check All'}
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {(['script', 'scenes', 'characters', 'locations', 'props'] as ExportComponent[]).map(comp => (
                <div 
                  key={comp} 
                  className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-accent/50 border border-transparent hover:border-border transition-colors"
                  onClick={() => toggleComponent(comp)}
                >
                  {selectedComponents.includes(comp) 
                    ? <CheckSquare className="h-4 w-4 text-primary" /> 
                    : <Square className="h-4 w-4 text-muted-foreground" />
                  }
                  <span className="text-sm capitalize">{comp}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3 py-2">
          <Button
            variant="outline"
            className="justify-start h-auto py-3 px-4"
            onClick={handleCopyMarkdown}
            disabled={scope === 'everything' && selectedComponents.length === 0}
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
            disabled={scope === 'everything' && selectedComponents.length === 0}
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

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
