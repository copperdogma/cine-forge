import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Wand2, Heart, CheckCircle, XCircle, GitBranch, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  getDesignStudy,
  generateDesignStudy,
  decideDesignStudy,
  getDesignStudyImageUrl,
} from '@/lib/api'
import type {
  DesignStudyState,
  DesignStudyImage,
  DesignStudyEntityType,
  ImageDecision,
} from '@/lib/api'

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

function modelLabel(modelId: string): string {
  return IMAGEN_MODELS.find(m => m.id === modelId)?.label ?? modelId
}

const DECISION_STYLES: Record<ImageDecision, string> = {
  pending: 'border-border',
  selected_final: 'ring-2 ring-emerald-500 shadow-emerald-500/20 shadow-lg',
  favorite: 'ring-2 ring-yellow-400 shadow-yellow-400/20 shadow-lg',
  rejected: 'opacity-35 grayscale',
  seed_for_variants: 'ring-2 ring-blue-400 shadow-blue-400/20 shadow-lg',
}

function ImageCard({
  img,
  index,
  projectId,
  entityId,
  onDecide,
  isDeciding,
}: {
  img: DesignStudyImage
  index: number
  projectId: string
  entityId: string
  onDecide: (filename: string, decision: ImageDecision, guidance?: string) => void
  isDeciding: boolean
}) {
  const [showPrompt, setShowPrompt] = useState(false)
  const [guidanceText, setGuidanceText] = useState('')

  const src = getDesignStudyImageUrl(projectId, entityId, img.filename)

  // Decisions that accept optional guidance notes
  const needsGuidance = img.decision === 'seed_for_variants' || img.decision === 'rejected'

  function handleDecide(decision: ImageDecision) {
    if (img.decision === decision) {
      // Toggle off — reset to pending
      onDecide(img.filename, 'pending')
      setGuidanceText('')
      return
    }
    const guidance = needsGuidance && guidanceText.trim() ? guidanceText.trim() : undefined
    onDecide(img.filename, decision, guidance)
  }

  return (
    <div className={`relative rounded-lg border overflow-hidden bg-card transition-shadow ${DECISION_STYLES[img.decision]}`}>
      {/* Index number */}
      <div className="absolute top-2 right-2 z-10">
        <span className="bg-black/60 text-white text-xs rounded px-1.5 py-0.5 font-mono">
          {index}
        </span>
      </div>

      {/* Decision state badges */}
      {img.decision === 'selected_final' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-emerald-600 text-white text-xs">
            <CheckCircle className="w-3 h-3 mr-1" />
            Final
          </Badge>
        </div>
      )}
      {img.decision === 'favorite' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-yellow-500 text-black text-xs">
            <Heart className="w-3 h-3 mr-1" />
            Favorite
          </Badge>
        </div>
      )}
      {img.decision === 'seed_for_variants' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-blue-500 text-white text-xs">
            <GitBranch className="w-3 h-3 mr-1" />
            Seed
          </Badge>
        </div>
      )}

      {/* Image — cropped preview, click to open full resolution */}
      <a href={src} target="_blank" rel="noopener noreferrer" className="block relative overflow-hidden" style={{ aspectRatio: '3/4' }}>
        <img
          src={src}
          alt={`Design study ${index}`}
          className="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-300"
        />
        <div className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-end justify-end p-2 opacity-0 hover:opacity-100">
          <span className="bg-black/60 text-white text-xs px-2 py-1 rounded">View full</span>
        </div>
      </a>

      <div className="p-3 space-y-2">
        {/* Action buttons */}
        <div className="grid grid-cols-4 gap-1">
          <button
            disabled={isDeciding}
            onClick={() => handleDecide('selected_final')}
            title="Set as visual reference for storyboards and video"
            className={`flex flex-col items-center gap-0.5 py-1.5 rounded text-xs border transition-colors ${
              img.decision === 'selected_final'
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'border-border hover:bg-emerald-600/10 hover:border-emerald-600/50 hover:text-emerald-400'
            }`}
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Final</span>
          </button>
          <button
            disabled={isDeciding}
            onClick={() => handleDecide('favorite')}
            title="Mark as favorite"
            className={`flex flex-col items-center gap-0.5 py-1.5 rounded text-xs border transition-colors ${
              img.decision === 'favorite'
                ? 'bg-yellow-500 text-black border-yellow-500'
                : 'border-border hover:bg-yellow-500/10 hover:border-yellow-500/50 hover:text-yellow-400'
            }`}
          >
            <Heart className="w-3.5 h-3.5" />
            <span>Fav</span>
          </button>
          <button
            disabled={isDeciding}
            onClick={() => handleDecide('seed_for_variants')}
            title="Use as seed for variants"
            className={`flex flex-col items-center gap-0.5 py-1.5 rounded text-xs border transition-colors ${
              img.decision === 'seed_for_variants'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'border-border hover:bg-blue-500/10 hover:border-blue-500/50 hover:text-blue-400'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Seed</span>
          </button>
          <button
            disabled={isDeciding}
            onClick={() => handleDecide('rejected')}
            title="Reject this direction"
            className={`flex flex-col items-center gap-0.5 py-1.5 rounded text-xs border transition-colors ${
              img.decision === 'rejected'
                ? 'bg-destructive text-destructive-foreground border-destructive'
                : 'border-border hover:bg-destructive/10 hover:border-destructive/50 hover:text-destructive'
            }`}
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Reject</span>
          </button>
        </div>

        {/* Guidance input for seed/reject decisions */}
        {(img.decision === 'seed_for_variants' || img.decision === 'rejected') && (
          <Textarea
            placeholder={
              img.decision === 'seed_for_variants'
                ? 'Direction for variants (e.g. "more weathered, older")'
                : 'Reason for rejection (optional)'
            }
            value={img.guidance ?? guidanceText}
            onChange={e => setGuidanceText(e.target.value)}
            onBlur={() => {
              if (guidanceText.trim() && guidanceText !== img.guidance) {
                onDecide(img.filename, img.decision, guidanceText.trim())
              }
            }}
            readOnly={!!img.guidance}
            className="text-xs resize-none h-12"
          />
        )}

        {/* Stored guidance for other decisions */}
        {img.guidance && img.decision !== 'seed_for_variants' && img.decision !== 'rejected' && (
          <p className="text-xs text-muted-foreground italic">"{img.guidance}"</p>
        )}

        <div className="flex items-center justify-between">
          <button
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
            onClick={() => setShowPrompt(v => !v)}
          >
            {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            Details
          </button>
          <span className="text-xs text-muted-foreground/60 font-mono">{modelLabel(img.model)}</span>
        </div>
        {showPrompt && (
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground font-mono bg-muted/50 rounded p-2 whitespace-pre-wrap">
              {img.prompt_used}
            </p>
            <p className="text-xs text-muted-foreground">
              Model: <span className="font-mono">{img.model}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

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
  const [guidance, setGuidance] = useState('')
  const [count, setCount] = useState<1 | 2 | 4 | 8>(1)
  const [model, setModel] = useState(IMAGEN_MODELS[0].id)
  const [showHistory, setShowHistory] = useState(false)
  const [filter, setFilter] = useState<FilterMode>('all')

  const { data: state, isLoading } = useQuery({
    queryKey: ['design-study', projectId, entityId],
    queryFn: () => getDesignStudy(projectId, entityId),
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      generateDesignStudy(projectId, entityId, {
        entity_type: entityType,
        count,
        guidance: guidance.trim() || null,
        model,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['design-study', projectId, entityId], updated)
      setGuidance('')
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
                ? { ...img, decision, ...(g !== undefined ? { guidance: g } : {}) }
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

  const allImages: DesignStudyImage[] = state
    ? [...state.rounds].reverse().flatMap(r => r.images)
    : []

  const latestRoundImages = state?.rounds.length
    ? state.rounds[state.rounds.length - 1].images
    : []

  const historicalImages = allImages.slice(latestRoundImages.length)
  const filteredLatest = filterImages(latestRoundImages, filter)
  const filteredHistory = filterImages(historicalImages, filter)

  function handleDecide(filename: string, decision: ImageDecision, g?: string) {
    decideMutation.mutate({ filename, decision, guidance: g })
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
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            {([1, 2, 4, 8] as const).map(n => (
              <button
                key={n}
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
            <span className="text-xs text-muted-foreground ml-1">image{count !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-1 ml-auto">
            {IMAGEN_MODELS.map(m => (
              <button
                key={m.id}
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
            disabled={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Generating…
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
        <div className="grid grid-cols-2 gap-3">
          {[0, 1].map(i => (
            <div key={i} className="rounded-lg border bg-muted animate-pulse h-48" />
          ))}
        </div>
      )}

      {/* Filter tabs — only when images exist */}
      {allImages.length > 0 && (
        <div className="flex gap-1">
          {(Object.keys(FILTER_LABELS) as FilterMode[]).map(mode => (
            <button
              key={mode}
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
      {filteredLatest.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">Round {state!.rounds.length}</p>
          <div className="grid grid-cols-2 gap-3">
            {filteredLatest.map((img, i) => (
              <ImageCard
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
      )}

      {/* History toggle */}
      {historicalImages.length > 0 && (
        <div className="space-y-2">
          <button
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setShowHistory(v => !v)}
          >
            {showHistory ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showHistory ? 'Hide' : 'Show'} earlier rounds ({historicalImages.length} image{historicalImages.length !== 1 ? 's' : ''})
          </button>
          {showHistory && filteredHistory.length > 0 && (
            <div className="grid grid-cols-2 gap-3">
              {filteredHistory.map((img, i) => (
                <ImageCard
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
          )}
          {showHistory && filteredHistory.length === 0 && (
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
    </div>
  )
}
