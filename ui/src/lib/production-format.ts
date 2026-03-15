import type { ProductionFormat } from '@/lib/types'

export const PRODUCTION_FORMAT_OPTIONS: Array<{
  value: ProductionFormat
  label: string
  description: string
}> = [
  {
    value: 'live_action',
    label: 'Live Action',
    description: 'Photoreal performances, real-world materials, and cinematic lens behavior.',
  },
  {
    value: 'animation_2d',
    label: '2D Animation',
    description: 'Hand-drawn linework, stylized shapes, and flat color design.',
  },
  {
    value: 'animation_3d',
    label: '3D Animation',
    description: 'Stylized feature-animation rendering with dimensional lighting and form.',
  },
  {
    value: 'anime',
    label: 'Anime',
    description: 'Crisp linework, cel shading, and expressive stylized character language.',
  },
  {
    value: 'graphic_novel',
    label: 'Graphic Novel',
    description: 'Ink-heavy illustration, bold contrast, and printed-page energy.',
  },
  {
    value: 'concept_art',
    label: 'Concept Art',
    description: 'Painterly exploratory visuals focused on design ideation over final realism.',
  },
]

export function getVisualMediumLabel(value: ProductionFormat): string {
  return PRODUCTION_FORMAT_OPTIONS.find((option) => option.value === value)?.label ?? value
}

export const getProductionFormatLabel = getVisualMediumLabel
