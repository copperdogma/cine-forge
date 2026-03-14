import {
  AudioLines,
  FileText,
  Film,
  ImageIcon,
} from 'lucide-react'

import { AssetWaveform } from '@/components/assets/AssetWaveform'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

import {
  formatShortDate,
  humanFileSize,
} from './reference-library-model'
import type { ReferenceItem } from './reference-library-model'

function PreviewSurface({
  item,
  onOpen,
}: {
  item: ReferenceItem
  onOpen: () => void
}) {
  if (item.assetType === 'image') {
    return (
      <button
        type="button"
        onClick={onOpen}
        className="group relative block w-full overflow-hidden rounded-xl border border-border/60 bg-muted/20 text-left"
      >
        <div className="aspect-[4/3] overflow-hidden bg-gradient-to-br from-sky-500/10 via-background to-emerald-500/10">
          {item.thumbnailUrl || item.previewUrl ? (
            <img
              src={item.thumbnailUrl ?? item.previewUrl}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <ImageIcon className="h-8 w-8" />
            </div>
          )}
        </div>
      </button>
    )
  }

  if (item.assetType === 'audio') {
    return (
      <button
        type="button"
        onClick={onOpen}
        className="block w-full rounded-xl border border-border/60 bg-gradient-to-br from-emerald-500/10 via-background to-sky-500/10 p-3 text-left"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground/90">
          <AudioLines className="h-4 w-4 text-emerald-300" />
          Audio reference
        </div>
        <AssetWaveform points={item.waveformPoints ?? []} />
      </button>
    )
  }

  if (item.assetType === 'video') {
    return (
      <button
        type="button"
        onClick={onOpen}
        className="block w-full rounded-xl border border-border/60 bg-gradient-to-br from-fuchsia-500/10 via-background to-sky-500/10 p-3 text-left"
      >
        <div className="flex aspect-[4/3] items-center justify-center rounded-lg border border-dashed border-border/60 bg-background/50">
          <div className="text-center">
            <Film className="mx-auto mb-2 h-8 w-8 text-fuchsia-300" />
            <p className="text-sm font-medium">Video reference</p>
            <p className="text-xs text-muted-foreground">Open preview</p>
          </div>
        </div>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={onOpen}
      className="block w-full rounded-xl border border-border/60 bg-gradient-to-br from-amber-500/10 via-background to-orange-500/10 p-3 text-left"
    >
      <div className="flex aspect-[4/3] items-center justify-center rounded-lg border border-dashed border-border/60 bg-background/50">
        <div className="text-center">
          <FileText className="mx-auto mb-2 h-8 w-8 text-amber-200" />
          <p className="text-sm font-medium">Document reference</p>
          <p className="text-xs text-muted-foreground">Open original file</p>
        </div>
      </div>
    </button>
  )
}

export function ReferenceCard({
  item,
  onPreview,
}: {
  item: ReferenceItem
  onPreview: () => void
}) {
  const injectedOn = formatShortDate(item.injectedAt)
  const meta = [
    item.durationSeconds ? `${item.durationSeconds.toFixed(1)}s` : null,
    item.model ?? null,
    item.source === 'uploaded' && item.rawAsset ? humanFileSize(item.rawAsset.file_size_bytes) : null,
    injectedOn,
  ].filter(Boolean)
  const primaryBadge = item.badges[0]

  return (
    <div className={cn(
      'rounded-2xl border border-border/70 bg-card/70 p-3 shadow-sm transition-colors',
      item.source === 'ai' && item.active && 'border-emerald-500/35 bg-emerald-500/5',
    )}>
      <div className="space-y-3">
        <PreviewSurface item={item} onOpen={onPreview} />

        <button type="button" onClick={onPreview} className="block w-full space-y-2 text-left">
          {primaryBadge && (
            <Badge variant="outline" className={cn('h-6 px-2 text-[11px] font-medium', primaryBadge.className)}>
              {primaryBadge.label}
            </Badge>
          )}

          <div>
            <p className="line-clamp-2 text-sm font-medium text-foreground" title={item.detailTitle ?? item.title}>
              {item.title}
            </p>
            <p className="mt-1 line-clamp-1 text-xs leading-relaxed text-muted-foreground" title={item.subtitle}>
              {item.subtitle}
            </p>
          </div>

          {meta.length > 0 && (
            <p className="line-clamp-1 text-[11px] text-muted-foreground">
              {meta.join(' · ')}
            </p>
          )}

          {item.assetType === 'audio' && (
            <p className="text-[11px] text-muted-foreground">
              Open the detail view for playback and waveform preview.
            </p>
          )}
          {item.assetType === 'document' && (
            <p className="text-[11px] text-muted-foreground">
              Open the detail view to inspect the file metadata and launch the original.
            </p>
          )}
          {item.assetType === 'video' && (
            <p className="text-[11px] text-muted-foreground">
              Open the detail view for full playback.
            </p>
          )}
        </button>
      </div>
    </div>
  )
}
