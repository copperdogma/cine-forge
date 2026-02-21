import type { EnrichedEntity, Scene } from '../hooks'
import type { ProjectSummary } from '../types'

export type ExportScope = 'everything' | 'scenes' | 'characters' | 'locations' | 'props' | 'single'

export type ExportFormat = 'markdown-clipboard' | 'markdown-file' | 'pdf' | 'one-sheet' | 'call-sheet'

export interface ProjectData {
  summary: ProjectSummary
  scenes: Scene[]
  characters: EnrichedEntity[]
  locations: EnrichedEntity[]
  props: EnrichedEntity[]
}

export interface ExportContext {
  scope: ExportScope
  format: ExportFormat
  singleEntity?: {
    type: 'scene' | 'character' | 'location' | 'prop'
    id: string
  }
}
