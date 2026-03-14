import type { RefObject } from 'react'
import type { DragEvent } from 'react'
import {
  Loader2,
  Upload,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import type { AssetLockStatus } from '@/lib/api'

import {
  FORMAT_GROUPS,
  LOCK_LABELS,
  UPLOAD_ACCEPT,
} from './reference-library-model'
import type { UploadProgress } from './reference-library-model'

function UploadDropZoneHeader({
  isUploading,
  uploadProgress,
  onBrowse,
}: {
  isUploading: boolean
  uploadProgress: UploadProgress | null
  onBrowse: () => void
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border border-border/60 bg-background/80 p-2.5">
          <Upload className="h-5 w-5 text-sky-300" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium">Drag references here or browse</p>
          <p className="text-xs text-muted-foreground">
            Multi-select works for scout photos, mood boards, clips, and documents.
          </p>
          <p className="text-xs text-muted-foreground">
            {FORMAT_GROUPS.map(group => `${group.label} ${group.value}`).join(' · ')}
          </p>
        </div>
      </div>

      <Button
        type="button"
        onClick={onBrowse}
        disabled={isUploading}
        size="sm"
        className="shrink-0"
      >
        {isUploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {uploadProgress
              ? `Uploading ${uploadProgress.current}/${uploadProgress.total}`
              : 'Uploading'}
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Browse files
          </>
        )}
      </Button>
    </div>
  )
}

function UploadProgressNotice({
  uploadProgress,
  purpose,
  lockStatus,
}: {
  uploadProgress: UploadProgress | null
  purpose: string
  lockStatus: AssetLockStatus
}) {
  if (!uploadProgress) return null

  return (
    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/8 p-3">
      <div className="flex items-start gap-3">
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-emerald-300" />
        <div className="min-w-0 space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-emerald-200">
            Uploading {uploadProgress.current}/{uploadProgress.total}
          </p>
          <p className="truncate text-sm text-foreground">
            {uploadProgress.filename}
          </p>
          <p className="text-xs text-muted-foreground">
            Using {purpose.replace(/_/g, ' ')} with {LOCK_LABELS[lockStatus].toLowerCase()}.
          </p>
        </div>
      </div>
    </div>
  )
}

function UploadDefaultsSummary({
  purpose,
  lockStatus,
  purposePresets,
  isUploading,
  onPurposeChange,
  onLockStatusChange,
}: {
  purpose: string
  lockStatus: AssetLockStatus
  purposePresets: string[]
  isUploading: boolean
  onPurposeChange: (value: string) => void
  onLockStatusChange: (value: AssetLockStatus) => void
}) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-muted/15 p-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Next upload defaults
        </p>
        <p className="text-sm text-foreground">
          {purpose.replace(/_/g, ' ')} · {LOCK_LABELS[lockStatus].toLowerCase()}
        </p>
        <p className="text-xs text-muted-foreground">
          These apply immediately to the next files you drop or browse.
        </p>
      </div>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" disabled={isUploading}>
            Edit defaults
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-[min(92vw,24rem)] space-y-4">
          <PopoverHeader className="space-y-1">
            <PopoverTitle>Next upload defaults</PopoverTitle>
            <PopoverDescription>
              Set the purpose and lock before you drop or browse files.
            </PopoverDescription>
          </PopoverHeader>

          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {purposePresets.map(preset => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => onPurposeChange(preset)}
                  disabled={isUploading}
                  className={cn(
                    'rounded-full border px-2.5 py-1 text-xs transition-colors',
                    purpose === preset
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-background hover:bg-muted',
                    isUploading && 'cursor-not-allowed opacity-60',
                  )}
                >
                  {preset.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
            <Input
              value={purpose}
              onChange={(event) => onPurposeChange(event.target.value)}
              placeholder="Purpose, e.g. mood_board or dialogue_audio"
              disabled={isUploading}
            />
          </div>

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Default lock
            </p>
            <Select
              value={lockStatus}
              onValueChange={(value) => onLockStatusChange(value as AssetLockStatus)}
              disabled={isUploading}
            >
              <SelectTrigger>
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
        </PopoverContent>
      </Popover>
    </div>
  )
}

function UploadDropZone({
  fileInputRef,
  dragging,
  isUploading,
  uploadProgress,
  purpose,
  lockStatus,
  onBrowse,
  onDraggingChange,
  onFilesSelected,
}: {
  fileInputRef: RefObject<HTMLInputElement | null>
  dragging: boolean
  isUploading: boolean
  uploadProgress: UploadProgress | null
  purpose: string
  lockStatus: AssetLockStatus
  onBrowse: () => void
  onDraggingChange: (value: boolean) => void
  onFilesSelected: (files: FileList | File[]) => void
}) {
  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    onDraggingChange(false)
    if (isUploading) return
    onFilesSelected(event.dataTransfer.files)
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        if (isUploading) return
        onDraggingChange(true)
      }}
      onDragLeave={(event) => {
        event.preventDefault()
        onDraggingChange(false)
      }}
      onDrop={handleDrop}
      className={cn(
        'relative rounded-2xl border-2 border-dashed p-5 transition-colors',
        dragging
          ? 'border-primary bg-primary/5'
          : 'border-border/70 bg-gradient-to-br from-sky-500/6 via-background to-emerald-500/6 hover:border-muted-foreground/50',
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={UPLOAD_ACCEPT}
        disabled={isUploading}
        className="hidden"
        onChange={(event) => {
          if (event.target.files) onFilesSelected(event.target.files)
        }}
      />

      <div className="space-y-4">
        <UploadDropZoneHeader
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          onBrowse={onBrowse}
        />
        <UploadProgressNotice
          uploadProgress={uploadProgress}
          purpose={purpose}
          lockStatus={lockStatus}
        />
      </div>
    </div>
  )
}

export function ReferenceLibraryUploadPanel({
  fileInputRef,
  purpose,
  lockStatus,
  purposePresets,
  dragging,
  isUploading,
  uploadProgress,
  onBrowse,
  onDraggingChange,
  onFilesSelected,
  onPurposeChange,
  onLockStatusChange,
}: {
  fileInputRef: RefObject<HTMLInputElement | null>
  purpose: string
  lockStatus: AssetLockStatus
  purposePresets: string[]
  dragging: boolean
  isUploading: boolean
  uploadProgress: UploadProgress | null
  onBrowse: () => void
  onDraggingChange: (value: boolean) => void
  onFilesSelected: (files: FileList | File[]) => void
  onPurposeChange: (value: string) => void
  onLockStatusChange: (value: AssetLockStatus) => void
}) {
  return (
    <div className="space-y-3">
      <UploadDefaultsSummary
        purpose={purpose}
        lockStatus={lockStatus}
        purposePresets={purposePresets}
        isUploading={isUploading}
        onPurposeChange={onPurposeChange}
        onLockStatusChange={onLockStatusChange}
      />
      <UploadDropZone
        fileInputRef={fileInputRef}
        dragging={dragging}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
        purpose={purpose}
        lockStatus={lockStatus}
        onBrowse={onBrowse}
        onDraggingChange={onDraggingChange}
        onFilesSelected={onFilesSelected}
      />
    </div>
  )
}
