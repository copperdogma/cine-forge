import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Wand2, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { DesignStudyImageCard } from '@/components/DesignStudyImageCard'
import { DesignStudySourcesPanel } from '@/components/DesignStudySourcesPanel'
import { ProductionFormatModal } from '@/components/ProductionFormatModal'
import {
  getDesignStudy,
  generateDesignStudy,
  decideDesignStudy,
  updateProjectSettings,
} from '@/lib/api'
import { useProject } from '@/lib/hooks'
import type {
  DesignStudyState,
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
  const [guidance, setGuidance] = useState('')
  const [count, setCount] = useState<1 | 2 | 4 | 8>(1)
  const [model, setModel] = useState(IMAGEN_MODELS[0].id)
  const [showHistory, setShowHistory] = useState(false)
  const [filter, setFilter] = useState<FilterMode>('all')
  const [useSeedVariants, setUseSeedVariants] = useState(true)
  const [formatModalOpen, setFormatModalOpen] = useState(false)

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

  const generateMutation = useMutation({
    mutationFn: () =>
      generateDesignStudy(projectId, entityId, {
        entity_type: entityType,
        count,
        guidance: guidance.trim() || null,
        model,
        seed_image_filename: useSeedVariants ? latestSeedImage?.filename ?? null : null,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['design-study', projectId, entityId], updated)
      setGuidance('')
    },
  })

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
    onSuccess: (_, { filename, decision, guidance: g }) => {
      queryClient.setQueryData(
        ['design-study', projectId, entityId],
        (prev: DesignStudyState | null | undefined) => {
          if (!prev) return prev
          const rounds = prev.rounds.map(r => ({
            ...r,
            images: r.images.map(img =>
              img.filename === filename
                ? {
                    ...img,
                    decision,
                    guidance:
                      decision === 'pending'
                        ? null
                        : g !== undefined
                          ? g
                          : img.guidance,
                  }
                : decision === 'selected_final' && img.decision === 'selected_final'
                  ? { ...img, decision: 'pending' }
                  : img,
            ),
          }))
          const selected_final_filename =
            decision === 'selected_final'
              ? filename
              : prev.selected_final_filename === filename
                ? null
                : prev.selected_final_filename
          return { ...prev, rounds, selected_final_filename }
        },
      )
    },
  })

  const roundsNewestFirst: DesignStudyRound[] = state ? [...state.rounds].reverse() : []
  const latestRound = roundsNewestFirst[0]
  const historicalRounds = roundsNewestFirst.slice(1)
  const allImages: DesignStudyImage[] = roundsNewestFirst.flatMap(r => r.images)
  const latestRoundImages = latestRound?.images ?? []
  const filteredLatest = filterImages(latestRoundImages, filter)
  const filteredHistoricalRounds = historicalRounds
    .map(round => ({
      round,
      images: filterImages(round.images, filter),
    }))
    .filter(({ images }) => images.length > 0)
  const historicalImageCount = historicalRounds.reduce((sum, round) => sum + round.images.length, 0)

  function handleDecide(filename: string, decision: ImageDecision, g?: string) {
    decideMutation.mutate({ filename, decision, guidance: g })
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

      {/* Generate controls */}
      <div className="space-y-2">
        <Textarea
          placeholder="Optional direction — e.g. 'more weathered, older' or 'sunlit, hopeful'"
          value={guidance}
          onChange={e => setGuidance(e.target.value)}
          className="text-sm resize-none h-14"
        />
        {latestSeedImage && (
          <div className="rounded-lg border border-sky-500/20 bg-sky-500/8 px-3 py-2">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-medium text-sky-100">Variant seed available</p>
                <p className="text-xs text-muted-foreground">
                  {latestSeedImage.filename} will guide the next round when seed mode is on.
                  Current support is prompt-guided variation, not direct upload image-conditioning.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setUseSeedVariants(v => !v)}
                className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
                  useSeedVariants
                    ? 'border-sky-400/40 bg-sky-500/20 text-sky-100'
                    : 'border-border bg-background text-muted-foreground hover:bg-muted'
                }`}
              >
                {useSeedVariants ? 'Seed on' : 'Seed off'}
              </button>
            </div>
          </div>
        )}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {([1, 2, 4, 8] as const).map(n => (
              <button
                key={n}
                type="button"
                onClick={() => setCount(n)}
                className={`w-7 h-7 rounded text-xs border transition-colors ${
                  count === n
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background border-border hover:bg-muted text-muted-foreground'
                }`}
              >
                {n}
              </button>
            ))}
            <span className="text-xs text-muted-foreground">image{count !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {IMAGEN_MODELS.map(m => (
              <button
                key={m.id}
                type="button"
                onClick={() => setModel(m.id)}
                title={m.id}
                className={`px-2 h-7 rounded text-xs border transition-colors ${
                  model === m.id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background border-border hover:bg-muted text-muted-foreground'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <Button
            size="sm"
            className="w-full justify-center"
            disabled={generateMutation.isPending || saveFormatMutation.isPending || projectLoading}
            onClick={handleGenerateClick}
          >
            {generateMutation.isPending || saveFormatMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                {saveFormatMutation.isPending ? 'Saving format…' : 'Generating…'}
              </>
            ) : (
              <>
                <Wand2 className="w-3.5 h-3.5 mr-1.5" />
                Generate
              </>
            )}
          </Button>
        </div>
        {generateMutation.isError && (
          <p className="text-xs text-destructive">
            Generation failed: {generateMutation.error instanceof Error ? generateMutation.error.message : 'Unknown error'}
          </p>
        )}
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid gap-3">
          {[0, 1].map(i => (
            <div key={i} className="rounded-lg border bg-muted animate-pulse h-48" />
          ))}
        </div>
      )}

      {/* Filter tabs — only when images exist */}
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

      {/* Latest round images */}
      {latestRound && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">Round {latestRound.round_number}</p>
          <DesignStudySourcesPanel round={latestRound} defaultOpen />
          {filteredLatest.length > 0 ? (
            <div className="grid gap-3">
              {filteredLatest.map((img, i) => (
                <DesignStudyImageCard
                  key={img.filename}
                  img={img}
                  index={i + 1}
                  projectId={projectId}
                  entityId={entityId}
                  onDecide={handleDecide}
                  isDeciding={decideMutation.isPending}
                />
              ))}
            </div>
          ) : (
            <p className="text-xs italic text-muted-foreground">
              No images in the latest round match this filter.
            </p>
          )}
        </div>
      )}

      {/* History toggle */}
      {historicalImageCount > 0 && (
        <div className="space-y-2">
          <button
            type="button"
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setShowHistory(v => !v)}
          >
            {showHistory ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showHistory ? 'Hide' : 'Show'} earlier rounds ({historicalImageCount} image{historicalImageCount !== 1 ? 's' : ''})
          </button>
          {showHistory && filteredHistoricalRounds.length > 0 && (
            <div className="space-y-4">
              {filteredHistoricalRounds.map(({ round, images }) => (
                <div key={round.round_number} className="space-y-2">
                  <p className="text-xs text-muted-foreground">Round {round.round_number}</p>
                  <DesignStudySourcesPanel round={round} />
                  <div className="grid gap-3">
                    {images.map((img, i) => (
                      <DesignStudyImageCard
                        key={img.filename}
                        img={img}
                        index={i + 1}
                        projectId={projectId}
                        entityId={entityId}
                        onDecide={handleDecide}
                        isDeciding={decideMutation.isPending}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
          {showHistory && filteredHistoricalRounds.length === 0 && (
            <p className="text-xs text-muted-foreground italic">No earlier images match this filter.</p>
          )}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !state && !generateMutation.isPending && (
        <p className="text-xs text-muted-foreground text-center py-4">
          No design study yet. Generate the first image above.
        </p>
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
