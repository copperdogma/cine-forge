import { useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import type {
  AssetTargetKind,
  DesignStudyState,
} from '@/lib/api'
import { ReferenceLibraryBrowserPanel } from './ReferenceLibraryBrowserPanel'
import { ReferenceLibraryHeader } from './ReferenceLibraryHeader'
import { ReferenceLibraryPreviewDialog } from './ReferenceLibraryPreviewDialog'
import { ReferenceLibraryUploadPanel } from './ReferenceLibraryUploadPanel'
import { useReferenceLibraryMutations } from './useReferenceLibraryMutations'
import { useReferenceLibraryViewModel } from './useReferenceLibraryViewModel'

interface ReferenceLibrarySectionProps {
  projectId: string
  targetKind: AssetTargetKind
  targetId: string
  title: string
  description: string
  purposePresets: string[]
  activeReferenceHint: string
  designStudyState?: DesignStudyState | null
  designStudyEntityId?: string
}

export function ReferenceLibrarySection({
  projectId,
  targetKind,
  targetId,
  title,
  description,
  purposePresets,
  activeReferenceHint,
  designStudyState = null,
  designStudyEntityId,
}: ReferenceLibrarySectionProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const {
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
  } = useReferenceLibraryViewModel({
    projectId,
    targetKind,
    targetId,
    purposePresets,
    designStudyState,
    designStudyEntityId,
  })
  const {
    handleLockChange,
    isUpdatingLock,
    isUploading,
    openPicker,
    uploadFiles,
    uploadProgress,
  } = useReferenceLibraryMutations({
    projectId,
    targetKind,
    targetId,
    purpose,
    lockStatus,
    fileInputRef,
  })

  return (
    <>
      <Card className="overflow-hidden">
        <ReferenceLibraryHeader
          title={title}
          description={description}
          activeReferenceHint={activeReferenceHint}
          uploadedCount={summary.uploadedCount}
          aiCount={summary.aiCount}
          activeCount={summary.activeCount}
          hasAiItems={summary.hasAiItems}
        />

        <CardContent className="space-y-6 pt-6">
          <ReferenceLibraryUploadPanel
            fileInputRef={fileInputRef}
            purpose={purpose}
            lockStatus={lockStatus}
            purposePresets={purposePresets}
            dragging={dragging}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            onBrowse={openPicker}
            onDraggingChange={setDragging}
            onFilesSelected={(files) => {
              void uploadFiles(files)
            }}
            onPurposeChange={setPurpose}
            onLockStatusChange={setLockStatus}
          />

          <ReferenceLibraryBrowserPanel
            hasAiItems={summary.hasAiItems}
            sourceFilter={sourceFilter}
            typeFilter={typeFilter}
            isLoading={isLoading}
            items={filteredItems}
            onPreview={setPreviewItem}
            onSourceFilterChange={setSourceFilter}
            onTypeFilterChange={setTypeFilter}
          />
        </CardContent>
      </Card>

      <ReferenceLibraryPreviewDialog
        item={previewItem}
        open={previewItem !== null}
        onOpenChange={(open) => {
          if (!open) setPreviewItem(null)
        }}
        onLockChange={(nextLock) => {
          if (previewItem) void handleLockChange(previewItem, nextLock)
        }}
        isUpdatingLock={isUpdatingLock}
      />
    </>
  )
}
