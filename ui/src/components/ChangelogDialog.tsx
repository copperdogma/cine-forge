import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { fetchChangelog } from '@/lib/api'

export function ChangelogDialog({
  open,
  onOpenChange,
  version,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  version?: string
}) {
  const { data: content } = useQuery({
    queryKey: ['changelog'],
    queryFn: fetchChangelog,
    enabled: open,
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Changelog {version && `— v${version}`}</DialogTitle>
        </DialogHeader>
        <div className="prose prose-sm prose-invert max-w-none break-words prose-code:break-all">
          <ReactMarkdown>{content ?? 'Loading...'}</ReactMarkdown>
        </div>
      </DialogContent>
    </Dialog>
  )
}
