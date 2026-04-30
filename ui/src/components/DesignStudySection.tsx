import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { CompositionBar } from '@/components/CompositionBar'
import { ContactSheetRow } from '@/components/ContactSheetRow'
import { ProductionFormatModal } from '@/components/ProductionFormatModal'
import {
  getDesignStudy,
  generateDesignStudy,
  decideDesignStudy,
  updateProjectSettings,
} from '@/lib/api'
import { getDesignStudyRoundStatus, isDesignStudyRoundActive } from '@/lib/design-study-status'
import { useProject } from '@/lib/hooks'
import type {
  DesignStudyImage,
  DesignStudyRound,
  DesignStudyEntityType,
  ImageDecision,
} from '@/lib/api'
import type { ProductionFormat, ProjectSummary } from '@/lib/types'

interface Props {
  projectId: string
  entityId: string
  entityType: DesignStudyEntityType
}

type FilterMode = 'all' | 'selected' | 'favorites' | 'rejected'

const IMAGEN_MODELS: Array<{ id: string; label: string }> = [
  { id: 'imagen-4.0-generate-001', label: 'Imagen 4' },
  { id: 'gpt-image-1', label: 'GPT-Image' },
]

const FILTER_LABELS: Record<FilterMode, string> = {
  all: 'All',
  selected: 'Selected',
  favorites: 'Favorites',
  rejected: 'Rejected',
}

function filterImages(images: DesignStudyImage[], mode: FilterMode): DesignStudyImage[] {
  if (mode === 'all') return images
  if (mode === 'selected') return images.filter(i => i.decision === 'selected_final')
  if (mode === 'favorites') return images.filter(i => i.decision === 'favorite')
  if (mode === 'rejected') return images.filter(i => i.decision === 'rejected')
  return images
}

export function DesignStudySection({ projectId, entityId, entityType }: Props) {
  const queryClient = useQueryClient()
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const [directive, setDirective] = useState('')
  const [positiveRefs, setPositiveRefs] = useState<string[]>([])
  const [negativeRefs, setNegativeRefs] = useState<string[]>([])
  const [count, setCount] = useState<1 | 2 | 4 | 8>(1)
  const [model, setModel] = useState(IMAGEN_MODELS[0].id)
  const [filter, setFilter] = useState<FilterMode>('all')
  const [useSeedVariants, setUseSeedVariants] = useState(true)
  const [formatModalOpen, setFormatModalOpen] = useState(false)
  const [expandedRoundNumber, setExpandedRoundNumber] = useState<number | null>(null)

  const { data: state, isLoading } = useQuery({
    queryKey: ['design-study', projectId, entityId],
    queryFn: () => getDesignStudy(projectId, entityId),
  })

  const latestSeedImage = state
    ? [...state.rounds]
        .reverse()
        .flatMap(r => [...r.images].reverse())
        .find(img => img.decision === 'seed_for_variants')
    : undefined
  const roundsNewestFirst: DesignStudyRound[] = state ? [...state.rounds].reverse() : []
  const hasGeneratingRound = roundsNewestFirst.some(isDesignStudyRoundActive)
  const latestRound = roundsNewestFirst[0]
  const activeRoundNumber =
    expandedRoundNumber !== null
    && roundsNewestFirst.some(round => round.round_number === expandedRoundNumber)
      ? expandedRoundNumber
      : latestRound?.round_number ?? null
  const allImages: DesignStudyImage[] = roundsNewestFirst.flatMap(round => round.images)
  const imageByFilename = new Map(allImages.map(image => [image.filename, image]))
  const positiveRefChips = positiveRefs.map(filename => ({
    filename,
    label: formatCompositionRefLabel(imageByFilename.get(filename), filename),
  }))
  const negativeRefChips = negativeRefs.map(filename => ({
    filename,
    label: formatCompositionRefLabel(imageByFilename.get(filename), filename),
  }))

  const generateMutation = useMutation({
    mutationFn: () =>
      generateDesignStudy(projectId, entityId, {
        entity_type: entityType,
        count,
        directive: directive.trim() || null,
        positive_refs: positiveRefs,
        negative_refs: negativeRefs,
        model,
        seed_image_filename: useSeedVariants ? latestSeedImage?.filename ?? null : null,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['design-study', projectId, entityId], updated)
      setDirective('')
      setPositiveRefs([])
      setNegativeRefs([])
      setExpandedRoundNumber(updated.rounds[updated.rounds.length - 1]?.round_number ?? null)
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: ['design-study', projectId, entityId] })
    },
  })

  useEffect(() => {
    if (!generateMutation.isPending && !hasGeneratingRound) {
      return undefined
    }
    const interval = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ['design-study', projectId, entityId] })
    }, 1500)
    return () => window.clearInterval(interval)
  }, [entityId, generateMutation.isPending, hasGeneratingRound, projectId, queryClient])

  const saveFormatMutation = useMutation({
    mutationFn: (format: ProductionFormat) =>
      updateProjectSettings(projectId, { production_format: format }),
    onSuccess: (updatedProject) => {
      queryClient.setQueryData<ProjectSummary>(['projects', projectId], updatedProject)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to save visual medium'
      toast.error(message)
    },
  })

  const decideMutation = useMutation({
    mutationFn: ({ filename, decision, guidance: g }: { filename: string; decision: ImageDecision; guidance?: string }) =>
      decideDesignStudy(projectId, entityId, { filename, decision, guidance: g ?? null }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['design-study', projectId, entityId] }),
        queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'preferences', 'profile'] }),
      ])
    },
  })

  function handleDecide(filename: string, decision: ImageDecision, g?: string) {
    decideMutation.mutate({ filename, decision, guidance: g })
  }

  function handleComposeRef(filename: string, polarity: 'positive' | 'negative') {
    if (polarity === 'positive') {
      setPositiveRefs(current =>
        current.includes(filename)
          ? current.filter(value => value !== filename)
          : [...current, filename],
      )
      setNegativeRefs(current => current.filter(value => value !== filename))
      return
    }
    setNegativeRefs(current =>
      current.includes(filename)
        ? current.filter(value => value !== filename)
        : [...current, filename],
    )
    setPositiveRefs(current => current.filter(value => value !== filename))
  }

  function handleRemoveRef(filename: string, polarity: 'positive' | 'negative') {
    if (polarity === 'positive') {
      setPositiveRefs(current => current.filter(value => value !== filename))
      return
    }
    setNegativeRefs(current => current.filter(value => value !== filename))
  }

  function handleRegenerateFromRound(round: DesignStudyRound) {
    setExpandedRoundNumber(round.round_number)
    setDirective(round.directive ?? '')
    setPositiveRefs([])
    setNegativeRefs([])
    setModel(IMAGEN_MODELS.some(option => option.id === round.model) ? round.model : IMAGEN_MODELS[0].id)
    setCount(isImageCount(round.count) ? round.count : 1)
    setUseSeedVariants(false)
  }

  async function handleFormatSelect(format: ProductionFormat) {
    try {
      await saveFormatMutation.mutateAsync(format)
      setFormatModalOpen(false)
      generateMutation.mutate()
    } catch {
      // Error surfaced through mutation state; keep modal open for retry.
    }
  }

  function handleGenerateClick() {
    if (!project?.production_format) {
      setFormatModalOpen(true)
      return
    }
    generateMutation.mutate()
  }

  const generationLabel = saveFormatMutation.isPending ? 'Saving format…' : 'Generating…'
  const generationError = generateMutation.isError
    ? generateMutation.error instanceof Error
      ? `Generation failed: ${generateMutation.error.message}`
      : 'Generation failed: Unknown error'
    : null
  const visibleRounds = roundsNewestFirst.filter(round => {
    if (getDesignStudyRoundStatus(round) !== 'completed') {
      return true
    }
    if (round.round_number === activeRoundNumber) {
      return true
    }
    return filterImages(round.images, filter).length > 0
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-sm">Design Study</h3>
          <p className="text-xs text-muted-foreground">
            Generate concept art for this {entityType}
          </p>
        </div>
        {state && allImages.length > 0 && (
          <Badge variant="outline" className="text-xs">
            {allImages.length} image{allImages.length !== 1 ? 's' : ''}
          </Badge>
        )}
      </div>

      {isLoading && (
        <div className="grid gap-3">
          {[0, 1].map(i => (
            <div key={i} className="rounded-lg border bg-muted animate-pulse h-48" />
          ))}
        </div>
      )}

      {allImages.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {(Object.keys(FILTER_LABELS) as FilterMode[]).map(mode => (
            <button
              key={mode}
              type="button"
              onClick={() => setFilter(mode)}
              className={`px-2.5 py-1 rounded text-xs border transition-colors ${
                filter === mode
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background border-border hover:bg-muted text-muted-foreground'
              }`}
            >
              {FILTER_LABELS[mode]}
            </button>
          ))}
        </div>
      )}

      {!isLoading && visibleRounds.length > 0 && (
        <div className="space-y-4">
          {visibleRounds.map(round => {
            const expanded = round.round_number === activeRoundNumber
            return (
              <div key={round.round_number} className="space-y-3">
                <ContactSheetRow
                  round={round}
                  images={filterImages(round.images, filter)}
                  projectId={projectId}
                  entityId={entityId}
                  expanded={expanded}
                  isLatest={round.round_number === latestRound?.round_number}
                  isDeciding={decideMutation.isPending}
                  positiveRefs={positiveRefs}
                  negativeRefs={negativeRefs}
                  onExpand={() => setExpandedRoundNumber(round.round_number)}
                  onRegenerateFromHere={handleRegenerateFromRound}
                  onDecide={handleDecide}
                  onComposeRef={handleComposeRef}
                />
                {expanded && (
                  <CompositionBar
                    directive={directive}
                    positiveRefs={positiveRefChips}
                    negativeRefs={negativeRefChips}
                    count={count}
                    model={model}
                    models={IMAGEN_MODELS}
                    canGenerate={!projectLoading && !saveFormatMutation.isPending}
                    isGenerating={generateMutation.isPending || saveFormatMutation.isPending}
                    generationLabel={generationLabel}
                    errorMessage={generationError}
                    sticky={getDesignStudyRoundStatus(round) !== 'failed'}
                    latestSeedFilename={latestSeedImage?.filename ?? null}
                    useSeedVariants={useSeedVariants}
                    onDirectiveChange={setDirective}
                    onCountChange={setCount}
                    onModelChange={setModel}
                    onRemoveRef={handleRemoveRef}
                    onToggleSeedVariants={() => setUseSeedVariants(value => !value)}
                    onGenerate={handleGenerateClick}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}

      {!isLoading && !state && (
        <div className="space-y-3">
          <p className="py-1 text-center text-xs text-muted-foreground">
            No design study yet. Generate the first image to start the contact-sheet loop.
          </p>
          <CompositionBar
            directive={directive}
            positiveRefs={positiveRefChips}
            negativeRefs={negativeRefChips}
            count={count}
            model={model}
            models={IMAGEN_MODELS}
            canGenerate={!projectLoading && !saveFormatMutation.isPending}
            isGenerating={generateMutation.isPending || saveFormatMutation.isPending}
            generationLabel={generationLabel}
            errorMessage={generationError}
            latestSeedFilename={null}
            useSeedVariants={false}
            onDirectiveChange={setDirective}
            onCountChange={setCount}
            onModelChange={setModel}
            onRemoveRef={handleRemoveRef}
            onToggleSeedVariants={() => undefined}
            onGenerate={handleGenerateClick}
          />
        </div>
      )}

      <ProductionFormatModal
        open={formatModalOpen}
        onOpenChange={setFormatModalOpen}
        selectedFormat={project?.production_format ?? null}
        pending={saveFormatMutation.isPending}
        title="Choose a visual medium before generating"
        description="This one project-wide choice sets the base visual medium for image generation. You can refine it later from Intent & Mood."
        onSelect={handleFormatSelect}
        onSkip={() => {
          setFormatModalOpen(false)
          generateMutation.mutate()
        }}
      />
    </div>
  )
}

function formatCompositionRefLabel(
  image: DesignStudyImage | undefined,
  filename: string,
): string {
  if (!image) {
    return filename
  }
  return `R${image.round_number} · ${filename}`
}

function isImageCount(value: number): value is 1 | 2 | 4 | 8 {
  return value === 1 || value === 2 || value === 4 || value === 8
}
