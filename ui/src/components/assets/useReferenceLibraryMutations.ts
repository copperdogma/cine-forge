import type { RefObject } from 'react'
import { useState } from 'react'
import { toast } from 'sonner'

import {
  useInjectAsset,
  useUpdateInjectedAssetLock,
} from '@/lib/hooks'
import type {
  AssetLockStatus,
  AssetTargetKind,
} from '@/lib/api'

import { LOCK_LABELS } from './reference-library-model'
import type {
  ReferenceItem,
  UploadProgress,
} from './reference-library-model'

export function useReferenceLibraryMutations({
  projectId,
  targetKind,
  targetId,
  purpose,
  lockStatus,
  fileInputRef,
}: {
  projectId: string
  targetKind: AssetTargetKind
  targetId: string
  purpose: string
  lockStatus: AssetLockStatus
  fileInputRef: RefObject<HTMLInputElement | null>
}) {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const injectAsset = useInjectAsset(projectId)
  const updateLock = useUpdateInjectedAssetLock(projectId)
  const isUploading = uploadProgress !== null || injectAsset.isPending

  function openPicker() {
    if (isUploading) return
    fileInputRef.current?.click()
  }

  async function uploadFiles(files: FileList | File[]) {
    const next = Array.from(files)
    if (!next.length) return

    let successCount = 0
    const failures: string[] = []
    setUploadProgress({ current: 0, total: next.length, filename: next[0]?.name ?? 'reference' })

    for (const [index, file] of next.entries()) {
      setUploadProgress({ current: index + 1, total: next.length, filename: file.name })
      try {
        await injectAsset.mutateAsync({
          target_kind: targetKind,
          target_id: targetId,
          purpose: purpose.trim() || 'reference',
          lock_status: lockStatus,
          file,
        })
        successCount += 1
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Upload failed'
        failures.push(`${file.name}: ${message}`)
      }
    }

    setUploadProgress(null)
    if (fileInputRef.current) fileInputRef.current.value = ''

    if (successCount > 0) {
      toast.success(
        successCount === 1
          ? `Added ${next[0]?.name ?? 'reference'}`
          : `Added ${successCount} reference files`,
      )
    }
    if (failures.length > 0) {
      toast.error(failures[0])
    }
  }

  async function handleLockChange(item: ReferenceItem, nextLock: AssetLockStatus) {
    if (!item.rawAsset || nextLock === item.lockStatus) return
    try {
      await updateLock.mutateAsync({
        target_kind: targetKind,
        target_id: targetId,
        asset_id: item.rawAsset.asset_id,
        lock_status: nextLock,
        rationale: `Operator updated ${item.filename} from the Reference Library.`,
      })
      toast.success(`Lock updated to ${LOCK_LABELS[nextLock].toLowerCase()}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update lock')
    }
  }

  return {
    handleLockChange,
    isUpdatingLock: updateLock.isPending,
    isUploading,
    openPicker,
    uploadFiles,
    uploadProgress,
  }
}
