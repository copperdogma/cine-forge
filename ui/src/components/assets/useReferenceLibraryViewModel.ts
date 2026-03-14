import { useMemo, useState } from 'react'

import { useInjectedAssetManifest } from '@/lib/hooks'
import type {
  AssetLockStatus,
  AssetTargetKind,
  DesignStudyState,
} from '@/lib/api'

import {
  buildReferenceItems,
  filterReferenceItems,
  summarizeReferenceItems,
} from './reference-library-model'
import type {
  ReferenceItem,
  SourceFilter,
  TypeFilter,
} from './reference-library-model'

export function useReferenceLibraryViewModel({
  projectId,
  targetKind,
  targetId,
  purposePresets,
  designStudyState,
  designStudyEntityId,
}: {
  projectId: string
  targetKind: AssetTargetKind
  targetId: string
  purposePresets: string[]
  designStudyState?: DesignStudyState | null
  designStudyEntityId?: string
}) {
  const [dragging, setDragging] = useState(false)
  const [purpose, setPurpose] = useState(purposePresets[0] ?? 'reference')
  const [lockStatus, setLockStatus] = useState<AssetLockStatus>('soft_locked')
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [previewItem, setPreviewItem] = useState<ReferenceItem | null>(null)
  const { data: manifest, isLoading } = useInjectedAssetManifest(projectId, targetKind, targetId)

  const items = useMemo(() => buildReferenceItems({
    projectId,
    manifestAssets: manifest?.assets,
    designStudyState,
    designStudyEntityId,
  }), [designStudyEntityId, designStudyState, manifest?.assets, projectId])

  const filteredItems = useMemo(
    () => filterReferenceItems(items, sourceFilter, typeFilter),
    [items, sourceFilter, typeFilter],
  )

  const summary = useMemo(() => summarizeReferenceItems(items), [items])

  return {
    dragging,
    filteredItems,
    isLoading,
    lockStatus,
    previewItem,
    purpose,
    setDragging,
    setLockStatus,
    setPreviewItem,
    setPurpose,
    setSourceFilter,
    setTypeFilter,
    sourceFilter,
    summary,
    typeFilter,
  }
}
