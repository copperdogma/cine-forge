import {
  getAssetFileUrl,
  getDesignStudyImageUrl,
} from '@/lib/api'
import type {
  AssetLockStatus,
  DesignStudyImage,
  DesignStudyState,
  ImageDecision,
  InjectedAsset,
} from '@/lib/api'

export const UPLOAD_ACCEPT =
  '.jpg,.jpeg,.png,.webp,.mp4,.mov,.wav,.mp3,.aac,.m4a,.pdf,.txt,.md'

export const FORMAT_GROUPS = [
  { label: 'Images', value: 'JPG, PNG, WEBP' },
  { label: 'Video', value: 'MP4, MOV' },
  { label: 'Audio', value: 'WAV, MP3, AAC' },
  { label: 'Docs', value: 'PDF, TXT' },
] as const

export const LOCK_LABELS: Record<AssetLockStatus, string> = {
  soft_locked: 'Soft lock',
  hard_locked: 'Hard lock',
  unlocked: 'Unlocked',
}

export type SourceFilter = 'all' | 'uploaded' | 'ai'
export type TypeFilter = 'all' | 'visual' | 'audio' | 'video' | 'document'

export interface UploadProgress {
  current: number
  total: number
  filename: string
}

export type ReferenceItem = {
  id: string
  source: 'uploaded' | 'ai'
  assetType: 'image' | 'audio' | 'video' | 'document' | 'other'
  title: string
  subtitle: string
  detailTitle?: string
  detailDescription?: string
  openUrl: string
  previewUrl?: string
  thumbnailUrl?: string
  active: boolean
  badges: Array<{ label: string; className: string }>
  purpose?: string
  lockStatus?: AssetLockStatus
  injectedAt?: string
  durationSeconds?: number | null
  waveformPoints?: number[]
  model?: string
  guidance?: string | null
  filename: string
  rawAsset?: InjectedAsset
}

export function humanFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatShortDate(value: string | undefined): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function assetTypeLabel(item: Pick<ReferenceItem, 'assetType'>): string {
  if (item.assetType === 'image') return 'Visual'
  if (item.assetType === 'audio') return 'Audio'
  if (item.assetType === 'video') return 'Video'
  if (item.assetType === 'document') return 'Doc'
  return 'File'
}

function modelLabel(model: string | undefined): string | null {
  if (!model) return null
  if (model === 'imagen-4.0-generate-001') return 'Imagen 4'
  if (model === 'gpt-image-1') return 'GPT-Image'
  return model
}

function titleCaseLabel(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function compactText(value: string, maxLength = 68): string {
  const normalized = value.replace(/\s+/g, ' ').trim()
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, maxLength - 1).trimEnd()}…`
}

export function compactFilename(filename: string, maxLength = 34): string {
  const normalized = filename.replace(/[_-]+/g, ' ').trim()
  if (normalized.length <= maxLength) return normalized

  const extensionIndex = normalized.lastIndexOf('.')
  const extension = extensionIndex > 0 ? normalized.slice(extensionIndex) : ''
  const stem = extensionIndex > 0 ? normalized.slice(0, extensionIndex) : normalized
  const available = Math.max(8, maxLength - extension.length - 1)
  const headLength = Math.max(10, Math.ceil(available * 0.6))
  const tailLength = Math.max(5, available - headLength)

  if (stem.length <= headLength + tailLength + 1) return normalized
  return `${stem.slice(0, headLength).trimEnd()}…${stem.slice(-tailLength).trimStart()}${extension}`
}

function extractWaveformPoints(asset: InjectedAsset): number[] {
  const raw = asset.extra_metadata?.waveform_points
  if (!Array.isArray(raw)) return []
  return raw
    .filter((point): point is number => typeof point === 'number')
    .slice(0, 64)
}

function latestFavoriteFilename(state: DesignStudyState | null | undefined): string | null {
  if (!state) return null
  const allImages = [...state.rounds].reverse().flatMap(round => [...round.images].reverse())
  return allImages.find(image => image.decision === 'favorite')?.filename ?? null
}

function designStudyDecisionBadge(decision: ImageDecision): { label: string; className: string } {
  switch (decision) {
    case 'selected_final':
      return { label: 'AI Final', className: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' }
    case 'favorite':
      return { label: 'AI Favorite', className: 'bg-amber-500/15 text-amber-200 border-amber-500/30' }
    case 'seed_for_variants':
      return { label: 'AI Seed', className: 'bg-sky-500/15 text-sky-200 border-sky-500/30' }
    case 'rejected':
      return { label: 'Rejected', className: 'bg-destructive/10 text-destructive border-destructive/20' }
    default:
      return { label: 'AI Candidate', className: 'bg-muted text-muted-foreground border-border' }
  }
}

function buildDesignStudyItem(
  projectId: string,
  designStudyEntityId: string,
  image: DesignStudyImage,
  activeAiFilename: string | null,
): ReferenceItem {
  const previewUrl = getDesignStudyImageUrl(projectId, designStudyEntityId, image.filename)
  const badge = designStudyDecisionBadge(image.decision)
  const model = modelLabel(image.model)

  return {
    id: `design-study-${image.filename}`,
    source: 'ai',
    assetType: 'image',
    title: image.guidance?.trim()
      ? compactText(image.guidance)
      : `Round ${image.round_number} study`,
    subtitle: model ? `Round ${image.round_number} · ${model}` : `Round ${image.round_number}`,
    detailTitle: `Round ${image.round_number} · ${image.filename}`,
    detailDescription: image.guidance?.trim()
      ? image.guidance
      : model
        ? `Generated with ${model}`
        : 'AI design study image',
    openUrl: previewUrl,
    previewUrl,
    thumbnailUrl: previewUrl,
    active: activeAiFilename === image.filename,
    badges: [badge],
    model: model ?? undefined,
    guidance: image.guidance,
    filename: image.filename,
  }
}

export function buildReferenceItems({
  projectId,
  manifestAssets,
  designStudyState = null,
  designStudyEntityId,
}: {
  projectId: string
  manifestAssets: InjectedAsset[] | undefined
  designStudyState?: DesignStudyState | null
  designStudyEntityId?: string
}): ReferenceItem[] {
  const activeAiFilename =
    designStudyState?.selected_final_filename ?? latestFavoriteFilename(designStudyState)

  const uploadedItems = (manifestAssets ?? [])
    .map(asset => {
      const fileUrl = getAssetFileUrl(projectId, asset.file_path)
      const thumbnailUrl = asset.thumbnail_path
        ? getAssetFileUrl(projectId, asset.thumbnail_path)
        : asset.asset_type === 'image' ? fileUrl : undefined
      const purposeLabel = titleCaseLabel(asset.purpose)

      return {
        id: asset.asset_id,
        source: 'uploaded' as const,
        assetType: asset.asset_type,
        title: compactFilename(asset.filename, 32),
        subtitle: purposeLabel,
        detailTitle: asset.filename,
        detailDescription: `${purposeLabel} · ${humanFileSize(asset.file_size_bytes)} · ${LOCK_LABELS[asset.lock_status]}`,
        openUrl: fileUrl,
        previewUrl: fileUrl,
        thumbnailUrl,
        active: true,
        badges: [],
        purpose: asset.purpose,
        lockStatus: asset.lock_status,
        injectedAt: asset.injected_at,
        durationSeconds: asset.duration_seconds,
        waveformPoints: extractWaveformPoints(asset),
        filename: asset.filename,
        rawAsset: asset,
      }
    })
    .sort((a, b) => (b.injectedAt ?? '').localeCompare(a.injectedAt ?? ''))

  const aiItems = designStudyState && designStudyEntityId
    ? [...designStudyState.rounds]
        .reverse()
        .flatMap(round =>
          [...round.images].reverse().map(image => buildDesignStudyItem(
            projectId,
            designStudyEntityId,
            image,
            activeAiFilename,
          ))
        )
    : []

  return [...uploadedItems, ...aiItems]
}

export function summarizeReferenceItems(items: ReferenceItem[]) {
  return {
    uploadedCount: items.filter(item => item.source === 'uploaded').length,
    aiCount: items.filter(item => item.source === 'ai').length,
    activeCount: items.filter(item => item.active).length,
    hasAiItems: items.some(item => item.source === 'ai'),
  }
}

export function filterReferenceItems(
  items: ReferenceItem[],
  sourceFilter: SourceFilter,
  typeFilter: TypeFilter,
) {
  return items.filter(item => {
    if (sourceFilter !== 'all' && item.source !== sourceFilter) return false
    if (typeFilter === 'visual') return item.assetType === 'image'
    if (typeFilter === 'audio') return item.assetType === 'audio'
    if (typeFilter === 'video') return item.assetType === 'video'
    if (typeFilter === 'document') return item.assetType === 'document'
    return true
  })
}
