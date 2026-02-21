import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { exportMarkdown, getExportUrl, type ExportScope } from '@/lib/api'
import { toast } from 'sonner'
import { FileDown, Copy, FileText } from 'lucide-react'

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
  // Determine effective scope based on props (no user selection anymore)
  const scope = defaultScope

  const handleCopyMarkdown = async () => {
    try {
      const content = await exportMarkdown(projectId, scope, entityId, entityType)
      await navigator.clipboard.writeText(content)
      toast.success('Copied Markdown to clipboard')
      onClose()
    } catch (error) {
      toast.error('Failed to copy markdown')
      console.error(error)
    }
  }

  const handleDownloadMarkdown = () => {
    // Trigger browser download by navigating to the API endpoint
    window.location.href = getExportUrl(projectId, 'markdown', scope, entityId, entityType)
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
            Select an export format.
          </DialogDescription>
        </DialogHeader>

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

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
