import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { useExportData } from '@/lib/hooks'
import { generateProjectMarkdown, generateSceneMarkdown, generateCharacterMarkdown, generateLocationMarkdown, generatePropMarkdown, generateScenesMarkdown, generateCharactersMarkdown, generateLocationsMarkdown, generatePropsMarkdown } from '@/lib/export/markdown'
import { exportProjectPDF, exportCallSheet } from '@/lib/export/pdf'
import { toast } from 'sonner'
import { Loader2, FileDown, Copy, FileText } from 'lucide-react'

type ExportScope = 'everything' | 'scenes' | 'characters' | 'locations' | 'props' | 'single'
type ExportFormat = 'markdown-clipboard' | 'markdown-file' | 'pdf' | 'one-sheet' | 'call-sheet'

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
  const [scope, setScope] = useState<ExportScope>(defaultScope)
  const [format, setFormat] = useState<ExportFormat>('markdown-clipboard')
  const { data, isLoading } = useExportData(projectId)

  const handleExport = async () => {
    if (!data) return

    let content = ''
    let filename = `export-${projectId}.md`

    // Markdown Generation
    if (format === 'markdown-clipboard' || format === 'markdown-file') {
      switch (scope) {
        case 'everything':
          content = generateProjectMarkdown(data.summary, data.scenes, data.characters, data.locations, data.props)
          break
        case 'scenes':
          content = generateScenesMarkdown(data.scenes)
          filename = `scenes-${projectId}.md`
          break
        case 'characters':
          content = generateCharactersMarkdown(data.characters)
          filename = `characters-${projectId}.md`
          break
        case 'locations':
          content = generateLocationsMarkdown(data.locations)
          filename = `locations-${projectId}.md`
          break
        case 'props':
          content = generatePropsMarkdown(data.props)
          filename = `props-${projectId}.md`
          break
        case 'single':
          if (entityType === 'scene' && entityId) {
            const scene = data.scenes.find(s => s.entityId === entityId)
            if (scene) content = generateSceneMarkdown(scene)
          } else if (entityType === 'character' && entityId) {
            const char = data.characters.find(c => c.entity_id === entityId)
            if (char) content = generateCharacterMarkdown(char)
          } else if (entityType === 'location' && entityId) {
            const loc = data.locations.find(l => l.entity_id === entityId)
            if (loc) content = generateLocationMarkdown(loc)
          } else if (entityType === 'prop' && entityId) {
            const prop = data.props.find(p => p.entity_id === entityId)
            if (prop) content = generatePropMarkdown(prop)
          }
          break
      }

      if (format === 'markdown-clipboard') {
        await navigator.clipboard.writeText(content)
        toast.success('Copied to clipboard')
      } else {
        const blob = new Blob([content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        a.click()
        URL.revokeObjectURL(url)
        toast.success('Download started')
      }
      onClose()
      return
    }

    // PDF Generation
    if (format === 'pdf') {
      exportProjectPDF(data.summary, data.scenes, data.characters, data.locations, data.props)
      onClose()
      return
    }

    // Call Sheet
    if (format === 'call-sheet') {
      exportCallSheet(data.summary, data.scenes, data.characters, data.locations)
      onClose()
      return
    }
    
    // One Sheet (Placeholder for now, just does Markdown summary)
    if (format === 'one-sheet') {
        // reuse project markdown but maybe filtered?
        content = generateProjectMarkdown(data.summary, [], [], [], []) // Just summary?
        // Actually, let's just dump the project summary for now as MVP
         const blob = new Blob([content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `one-sheet-${projectId}.md`
        a.click()
        URL.revokeObjectURL(url)
        toast.success('One-sheet download started')
        onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Project Data</DialogTitle>
          <DialogDescription>
            Choose what to export and the format.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="space-y-3">
              <Label>Scope</Label>
              <RadioGroup value={scope} onValueChange={(v) => setScope(v as ExportScope)}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="everything" id="everything" />
                  <Label htmlFor="everything">Everything (Full Project)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="scenes" id="scenes" />
                  <Label htmlFor="scenes">All Scenes</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="characters" id="characters" />
                  <Label htmlFor="characters">All Characters</Label>
                </div>
                {entityId && (
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="single" id="single" />
                    <Label htmlFor="single">Current {entityType}</Label>
                  </div>
                )}
              </RadioGroup>
            </div>

            <div className="space-y-3">
              <Label>Format</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={format === 'markdown-clipboard' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4"
                  onClick={() => setFormat('markdown-clipboard')}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">Copy Markdown</div>
                    <div className="text-xs opacity-70">To clipboard</div>
                  </div>
                </Button>
                <Button
                  variant={format === 'markdown-file' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4"
                  onClick={() => setFormat('markdown-file')}
                >
                  <FileDown className="mr-2 h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">Download MD</div>
                    <div className="text-xs opacity-70">Text file</div>
                  </div>
                </Button>
                <Button
                  variant={format === 'pdf' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4"
                  onClick={() => setFormat('pdf')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">PDF Report</div>
                    <div className="text-xs opacity-70">Formatted doc</div>
                  </div>
                </Button>
                <Button
                  variant={format === 'call-sheet' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4"
                  onClick={() => setFormat('call-sheet')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">Call Sheet</div>
                    <div className="text-xs opacity-70">Industry format</div>
                  </div>
                </Button>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleExport} disabled={isLoading}>Export</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
