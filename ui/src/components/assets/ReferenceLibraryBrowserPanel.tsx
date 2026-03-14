import { ReferenceLibraryFilterBar } from './ReferenceLibraryFilterBar'
import { ReferenceLibraryGrid } from './ReferenceLibraryGrid'
import type {
  ReferenceItem,
  SourceFilter,
  TypeFilter,
} from './reference-library-model'

export function ReferenceLibraryBrowserPanel({
  hasAiItems,
  sourceFilter,
  typeFilter,
  isLoading,
  items,
  onPreview,
  onSourceFilterChange,
  onTypeFilterChange,
}: {
  hasAiItems: boolean
  sourceFilter: SourceFilter
  typeFilter: TypeFilter
  isLoading: boolean
  items: ReferenceItem[]
  onPreview: (item: ReferenceItem) => void
  onSourceFilterChange: (value: SourceFilter) => void
  onTypeFilterChange: (value: TypeFilter) => void
}) {
  return (
    <div className="space-y-3">
      <ReferenceLibraryFilterBar
        hasAiItems={hasAiItems}
        sourceFilter={sourceFilter}
        typeFilter={typeFilter}
        onSourceFilterChange={onSourceFilterChange}
        onTypeFilterChange={onTypeFilterChange}
      />
      <ReferenceLibraryGrid
        isLoading={isLoading}
        items={items}
        onPreview={onPreview}
      />
    </div>
  )
}
