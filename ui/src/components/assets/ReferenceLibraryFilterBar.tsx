import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

import type {
  SourceFilter,
  TypeFilter,
} from './reference-library-model'

export function ReferenceLibraryFilterBar({
  hasAiItems,
  sourceFilter,
  typeFilter,
  onSourceFilterChange,
  onTypeFilterChange,
}: {
  hasAiItems: boolean
  sourceFilter: SourceFilter
  typeFilter: TypeFilter
  onSourceFilterChange: (value: SourceFilter) => void
  onTypeFilterChange: (value: TypeFilter) => void
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        {hasAiItems && (
          <Tabs value={sourceFilter} onValueChange={(value) => onSourceFilterChange(value as SourceFilter)}>
            <TabsList scrollable className="w-full">
              <TabsTrigger value="all">All sources</TabsTrigger>
              <TabsTrigger value="uploaded">Uploaded</TabsTrigger>
              <TabsTrigger value="ai">AI study</TabsTrigger>
            </TabsList>
          </Tabs>
        )}
      </div>

      <Tabs value={typeFilter} onValueChange={(value) => onTypeFilterChange(value as TypeFilter)}>
        <TabsList variant="line" scrollable className="w-full">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="visual">Visual</TabsTrigger>
          <TabsTrigger value="audio">Audio</TabsTrigger>
          <TabsTrigger value="video">Video</TabsTrigger>
          <TabsTrigger value="document">Docs</TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  )
}
