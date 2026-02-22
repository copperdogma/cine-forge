import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { exportMarkdown, getExportUrl, type ExportScope, type ExportFormat } from '@/lib/api'
import { toast } from 'sonner'
import { FileDown, Copy, FileText, CheckSquare, Square, FileCode } from 'lucide-react'

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

  const handleCopyMarkdown = async (includeOverride?: ExportComponent[]) => {
    try {
      const content = await exportMarkdown(projectId, scope, entityId, entityType, includeOverride || selectedComponents)
      await navigator.clipboard.writeText(content)
      toast.success('Copied Markdown to clipboard')
      onClose()
    } catch (error) {
      toast.error('Failed to copy markdown')
      console.error(error)
    }
  }

  const handleDownload = (format: ExportFormat, includeOverride?: ExportComponent[]) => {
    const url = getExportUrl(projectId, format, scope, entityId, entityType, includeOverride || selectedComponents)
    window.location.href = url
    toast.success(`${format.toUpperCase()} export started`)
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
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{getTitle()}</DialogTitle>
          <DialogDescription>
            Choose what to export and the format.
          </DialogDescription>
        </DialogHeader>

        {scope === 'everything' ? (
          <Tabs defaultValue="screenplay" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="screenplay">Screenplay</TabsTrigger>
              <TabsTrigger value="project">Project Data</TabsTrigger>
            </TabsList>
            
            <TabsContent value="screenplay" className="space-y-4 py-4">
              <div className="grid grid-cols-1 gap-3">
                <Button variant="outline" className="justify-start h-auto py-3 px-4" onClick={() => handleDownload('pdf', ['script'])}>
                  <FileText className="mr-3 h-5 w-5 text-red-400" />
                  <div className="text-left">
                    <div className="font-medium">Standard PDF</div>
                    <div className="text-xs text-muted-foreground">Industry standard formatting (12pt Courier)</div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto py-3 px-4" onClick={() => handleDownload('docx')}>
                  <FileText className="mr-3 h-5 w-5 text-blue-400" />
                  <div className="text-left">
                    <div className="font-medium">Microsoft Word (.docx)</div>
                    <div className="text-xs text-muted-foreground">Standard screenplay format</div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto py-3 px-4" onClick={() => handleDownload('fountain')}>
                  <FileCode className="mr-3 h-5 w-5 text-amber-400" />
                  <div className="text-left">
                    <div className="font-medium">Fountain File (.fountain)</div>
                    <div className="text-xs text-muted-foreground">Raw plaintext screenplay format</div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto py-3 px-4" onClick={() => handleCopyMarkdown(['script'])}>
                  <Copy className="mr-3 h-5 w-5 text-muted-foreground" />
                  <div className="text-left">
                    <div className="font-medium">Copy as Markdown</div>
                    <div className="text-xs text-muted-foreground">Fountain syntax in code block</div>
                  </div>
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="project" className="space-y-4 py-2">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <span className="text-sm font-semibold">Included Components:</span>
                  <Button variant="ghost" size="sm" onClick={toggleAll} className="h-7 text-xs px-2">
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

              <div className="space-y-3 pt-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Export Formats</p>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    className="justify-start h-auto py-2 px-3"
                    onClick={() => handleCopyMarkdown()}
                    disabled={selectedComponents.length === 0}
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    <div className="text-left">
                      <div className="font-medium text-sm">Copy MD</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="justify-start h-auto py-2 px-3"
                    onClick={() => handleDownload('markdown')}
                    disabled={selectedComponents.length === 0}
                  >
                    <FileDown className="mr-2 h-4 w-4" />
                    <div className="text-left">
                      <div className="font-medium text-sm">Download MD</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="justify-start h-auto py-2 px-3"
                    onClick={() => handleDownload('pdf')}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    <div className="text-left">
                      <div className="font-medium text-sm">PDF Report</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="justify-start h-auto py-2 px-3"
                    onClick={() => handleDownload('call-sheet')}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    <div className="text-left">
                      <div className="font-medium text-sm">Call Sheet</div>
                    </div>
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <div className="flex flex-col gap-3 py-4">
            <Button
              variant="outline"
              className="justify-start h-auto py-3 px-4"
              onClick={() => handleCopyMarkdown()}
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
              onClick={() => handleDownload('markdown')}
            >
              <FileDown className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-medium">Download Markdown</div>
                <div className="text-xs opacity-70">.md file</div>
              </div>
            </Button>
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
