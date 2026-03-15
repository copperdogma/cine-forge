import { useState } from 'react'
import {
  Heart,
  CheckCircle,
  XCircle,
  GitBranch,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { getDesignStudyImageUrl } from '@/lib/api'
import type { DesignStudyImage, ImageDecision } from '@/lib/api'

const IMAGEN_MODELS: Array<{ id: string; label: string }> = [
  { id: 'imagen-4.0-generate-001', label: 'Imagen 4' },
  { id: 'gpt-image-1', label: 'GPT-Image' },
]

const DECISION_STYLES: Record<ImageDecision, string> = {
  pending: 'border-border',
  selected_final: 'ring-2 ring-emerald-500 shadow-emerald-500/20 shadow-lg',
  favorite: 'ring-2 ring-yellow-400 shadow-yellow-400/20 shadow-lg',
  rejected: 'opacity-35 grayscale',
  seed_for_variants: 'ring-2 ring-blue-400 shadow-blue-400/20 shadow-lg',
}

function modelLabel(modelId: string): string {
  return IMAGEN_MODELS.find(m => m.id === modelId)?.label ?? modelId
}

interface Props {
  img: DesignStudyImage
  index: number
  projectId: string
  entityId: string
  onDecide: (filename: string, decision: ImageDecision, guidance?: string) => void
  isDeciding: boolean
}

export function DesignStudyImageCard({
  img,
  index,
  projectId,
  entityId,
  onDecide,
  isDeciding,
}: Props) {
  const [showPrompt, setShowPrompt] = useState(false)
  const [guidanceText, setGuidanceText] = useState('')

  const src = getDesignStudyImageUrl(projectId, entityId, img.filename)

  function handleDecide(decision: ImageDecision) {
    if (img.decision === decision) {
      onDecide(img.filename, 'pending')
      setGuidanceText('')
      return
    }
    const guidance =
      (decision === 'seed_for_variants' || decision === 'rejected') && guidanceText.trim()
        ? guidanceText.trim()
        : undefined
    onDecide(img.filename, decision, guidance)
  }

  return (
    <div
      className={`relative overflow-hidden rounded-lg border bg-card transition-shadow ${DECISION_STYLES[img.decision]}`}
    >
      <div className="absolute top-2 right-2 z-10">
        <span className="rounded bg-black/60 px-1.5 py-0.5 font-mono text-xs text-white">
          {index}
        </span>
      </div>

      {img.decision === 'selected_final' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-emerald-600 text-xs text-white">
            <CheckCircle className="mr-1 h-3 w-3" />
            Final
          </Badge>
        </div>
      )}
      {img.decision === 'favorite' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-yellow-500 text-xs text-black">
            <Heart className="mr-1 h-3 w-3" />
            Favorite
          </Badge>
        </div>
      )}
      {img.decision === 'seed_for_variants' && (
        <div className="absolute top-2 left-2 z-10">
          <Badge className="bg-blue-500 text-xs text-white">
            <GitBranch className="mr-1 h-3 w-3" />
            Seed
          </Badge>
        </div>
      )}

      <a
        href={src}
        target="_blank"
        rel="noopener noreferrer"
        className="relative block overflow-hidden"
        style={{ aspectRatio: '3 / 4' }}
      >
        <img
          src={src}
          alt={`Design study ${index}`}
          className="h-full w-full object-cover object-top transition-transform duration-300 hover:scale-105"
        />
        <div className="absolute inset-0 flex items-end justify-end bg-black/0 p-2 opacity-0 transition-colors hover:bg-black/10 hover:opacity-100">
          <span className="rounded bg-black/60 px-2 py-1 text-xs text-white">View full</span>
        </div>
      </a>

      <div className="space-y-2 p-3">
        <div className="grid grid-cols-4 gap-1">
          <button
            type="button"
            disabled={isDeciding}
            onClick={() => handleDecide('selected_final')}
            title="Set as visual reference for storyboards and video"
            className={`flex flex-col items-center gap-0.5 rounded border py-1.5 text-xs transition-colors ${
              img.decision === 'selected_final'
                ? 'border-emerald-600 bg-emerald-600 text-white'
                : 'border-border hover:border-emerald-600/50 hover:bg-emerald-600/10 hover:text-emerald-400'
            }`}
          >
            <CheckCircle className="h-3.5 w-3.5" />
            <span>Final</span>
          </button>
          <button
            type="button"
            disabled={isDeciding}
            onClick={() => handleDecide('favorite')}
            title="Mark as favorite"
            className={`flex flex-col items-center gap-0.5 rounded border py-1.5 text-xs transition-colors ${
              img.decision === 'favorite'
                ? 'border-yellow-500 bg-yellow-500 text-black'
                : 'border-border hover:border-yellow-500/50 hover:bg-yellow-500/10 hover:text-yellow-400'
            }`}
          >
            <Heart className="h-3.5 w-3.5" />
            <span>Fav</span>
          </button>
          <button
            type="button"
            disabled={isDeciding}
            onClick={() => handleDecide('seed_for_variants')}
            title="Use as seed for variants"
            className={`flex flex-col items-center gap-0.5 rounded border py-1.5 text-xs transition-colors ${
              img.decision === 'seed_for_variants'
                ? 'border-blue-500 bg-blue-500 text-white'
                : 'border-border hover:border-blue-500/50 hover:bg-blue-500/10 hover:text-blue-400'
            }`}
          >
            <GitBranch className="h-3.5 w-3.5" />
            <span>Seed</span>
          </button>
          <button
            type="button"
            disabled={isDeciding}
            onClick={() => handleDecide('rejected')}
            title="Reject this direction"
            className={`flex flex-col items-center gap-0.5 rounded border py-1.5 text-xs transition-colors ${
              img.decision === 'rejected'
                ? 'border-destructive bg-destructive text-destructive-foreground'
                : 'border-border hover:border-destructive/50 hover:bg-destructive/10 hover:text-destructive'
            }`}
          >
            <XCircle className="h-3.5 w-3.5" />
            <span>Reject</span>
          </button>
        </div>

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
            className="h-12 resize-none text-xs"
          />
        )}

        {img.guidance && img.decision !== 'seed_for_variants' && img.decision !== 'rejected' && (
          <p className="text-xs italic text-muted-foreground">"{img.guidance}"</p>
        )}

        <div className="flex items-center justify-between">
          <button
            type="button"
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setShowPrompt(v => !v)}
          >
            {showPrompt ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            Details
          </button>
          <span className="font-mono text-xs text-muted-foreground/60">
            {modelLabel(img.model)}
          </span>
        </div>
        {showPrompt && (
          <div className="space-y-1.5">
            <p className="whitespace-pre-wrap rounded bg-muted/50 p-2 font-mono text-xs text-muted-foreground">
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
