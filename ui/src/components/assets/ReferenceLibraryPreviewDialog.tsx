import {
  ExternalLink,
  Lock,
} from 'lucide-react'

import { AssetWaveform } from '@/components/assets/AssetWaveform'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { AssetLockStatus } from '@/lib/api'

import {
  assetTypeLabel,
  LOCK_LABELS,
} from './reference-library-model'
import type { ReferenceItem } from './reference-library-model'

function PreviewDialogMedia({
  item,
}: {
  item: ReferenceItem
}) {
  return (
    <div className="space-y-4">
      {item.assetType === 'image' && item.previewUrl && (
        <div className="overflow-hidden rounded-xl border border-border/60">
          <img src={item.previewUrl} alt={item.title} className="max-h-[70vh] w-full object-contain bg-muted/20" />
        </div>
      )}

      {item.assetType === 'audio' && (
        <div className="space-y-3">
          <AssetWaveform points={item.waveformPoints ?? []} className="bg-background" />
          <audio controls src={item.openUrl} className="w-full" preload="metadata" />
        </div>
      )}

      {item.assetType === 'video' && (
        <video
          controls
          src={item.openUrl}
          className="max-h-[70vh] w-full rounded-xl border border-border/60 bg-black"
          preload="metadata"
        />
      )}

      {item.assetType === 'document' && (
        <div className="rounded-xl border border-dashed border-border/60 bg-muted/20 p-6 text-sm text-muted-foreground">
          This reference opens in the browser or your default file handler.
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {item.badges.map(badge => (
          <Badge key={badge.label} variant="outline" className={badge.className}>
            {badge.label}
          </Badge>
        ))}
        <Badge variant="outline">{assetTypeLabel(item)}</Badge>
      </div>
    </div>
  )
}

function PreviewDialogFooter({
  item,
  onLockChange,
  isUpdatingLock,
}: {
  item: ReferenceItem
  onLockChange: (lockStatus: AssetLockStatus) => void
  isUpdatingLock: boolean
}) {
  return (
    <DialogFooter>
      <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {item.lockStatus ? (
          <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-muted/20 px-3 py-2">
            <Lock className="h-4 w-4 shrink-0 text-muted-foreground" />
            <Select
              value={item.lockStatus}
              onValueChange={(value) => onLockChange(value as AssetLockStatus)}
              disabled={isUpdatingLock}
            >
              <SelectTrigger className="min-w-[11rem] border-0 bg-transparent px-0 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(LOCK_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : (
          <div />
        )}

        <Button asChild variant="outline">
          <a href={item.openUrl} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            Open original
          </a>
        </Button>
      </div>
    </DialogFooter>
  )
}

export function ReferenceLibraryPreviewDialog({
  item,
  open,
  onOpenChange,
  onLockChange,
  isUpdatingLock,
}: {
  item: ReferenceItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onLockChange: (lockStatus: AssetLockStatus) => void
  isUpdatingLock: boolean
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        {item && (
          <>
            <DialogHeader>
              <DialogTitle>{item.detailTitle ?? item.title}</DialogTitle>
              <DialogDescription>{item.detailDescription ?? item.subtitle}</DialogDescription>
            </DialogHeader>
            <PreviewDialogMedia item={item} />
            <PreviewDialogFooter
              item={item}
              onLockChange={onLockChange}
              isUpdatingLock={isUpdatingLock}
            />
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
