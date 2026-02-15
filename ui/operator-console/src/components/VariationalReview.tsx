import { useState } from "react"
import { Brain, RefreshCw, Check, ThumbsUp, Sparkles } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

interface Variation {
  id: string
  model: string
  confidence: number
  content: string
  highlights?: string[]
}

interface VariationalReviewProps {
  title: string
  artifactType: string
  variations: Variation[]
  selectedId?: string
  onSelect?: (id: string) => void
  onRegenerate?: (id: string) => void
  onApprove?: (id: string, feedback?: string) => void
  className?: string
}

export function VariationalReview({
  title,
  artifactType,
  variations,
  selectedId: controlledSelectedId,
  onSelect,
  onRegenerate,
  onApprove,
  className,
}: VariationalReviewProps) {
  const [internalSelectedId, setInternalSelectedId] = useState<string | undefined>(undefined)
  const [feedback, setFeedback] = useState("")

  // Use controlled value if provided, otherwise use internal state
  const selectedId = controlledSelectedId !== undefined ? controlledSelectedId : internalSelectedId

  const handleSelect = (id: string) => {
    if (onSelect) {
      onSelect(id)
    } else {
      setInternalSelectedId(id)
    }
  }

  const handleApprove = () => {
    if (selectedId && onApprove) {
      onApprove(selectedId, feedback || undefined)
    }
  }

  const getConfidenceBadgeVariant = (confidence: number): "default" | "secondary" | "destructive" => {
    if (confidence >= 80) return "default" // Green
    if (confidence >= 50) return "secondary" // Amber
    return "destructive" // Red
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Artifact Type: <span className="font-mono text-foreground">{artifactType}</span>
        </p>
      </div>

      <Separator />

      {/* Variations Stack */}
      <div className="space-y-4">
        {variations.map((variation) => {
          const isSelected = selectedId === variation.id

          return (
            <div key={variation.id} className="space-y-2">
              <Card
                className={cn(
                  "cursor-pointer transition-all duration-200 hover:shadow-md",
                  isSelected && [
                    "border-primary",
                    "shadow-lg",
                    "ring-2 ring-primary/20",
                  ]
                )}
                onClick={() => handleSelect(variation.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-muted-foreground" />
                      <code className="text-sm font-mono font-medium">
                        {variation.model}
                      </code>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getConfidenceBadgeVariant(variation.confidence)}>
                        {variation.confidence}% confidence
                      </Badge>
                      {isSelected && (
                        <Badge className="bg-primary text-primary-foreground">
                          <Check className="h-3 w-3 mr-1" />
                          Selected
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Content */}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {variation.content}
                  </p>

                  {/* Highlights */}
                  {variation.highlights && variation.highlights.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Key Differences
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {variation.highlights.map((highlight, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs font-normal"
                          >
                            {highlight}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Regenerate Button */}
              {onRegenerate && (
                <div className="flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onRegenerate(variation.id)
                    }}
                    className="gap-1.5"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    Regenerate
                  </Button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <Separator />

      {/* Feedback & Approval */}
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="feedback" className="text-sm font-medium">
            Feedback (optional)
          </label>
          <Textarea
            id="feedback"
            placeholder="Provide feedback on the selected variation or request changes..."
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="min-h-[100px] resize-none"
          />
        </div>

        <div className="flex justify-end">
          <Button
            disabled={!selectedId}
            onClick={handleApprove}
            className="gap-2"
            size="lg"
          >
            <ThumbsUp className="h-4 w-4" />
            Approve Selection
          </Button>
        </div>
      </div>
    </div>
  )
}

// Mock data for demonstration
export const mockVariations: Variation[] = [
  {
    id: "var-1",
    model: "claude-opus-4",
    confidence: 92,
    content: `Rick Deckard is a complex, world-weary protagonist haunted by the ambiguity of his own existence. A former blade runner reluctantly pulled back into service, he embodies the moral exhaustion of enforcing an unjust system while questioning the very nature of humanity and artificial life.

His character arc centers on the gradual erosion of his certainty—initially treating replicants as mere machines to be "retired," he comes to recognize their capacity for emotion, memory, and suffering. This recognition forces him to confront uncomfortable truths about empathy, autonomy, and what it means to be human in a world where the line between natural and artificial has blurred beyond recognition.

Deckard's relationship with Rachael catalyzes his transformation. Her artificial memories feel as real to her as his own do to him, raising the existential question: if synthetic experiences can produce genuine feelings, what makes "real" humanity superior? This relationship becomes both his salvation and his curse, as love for a replicant destined to die young forces him to choose between the system he once served and a fleeting chance at authentic connection.`,
    highlights: [
      "Emphasizes existential ambiguity",
      "Focus on moral exhaustion",
      "Rachael as catalytic relationship",
    ],
  },
  {
    id: "var-2",
    model: "gpt-4o",
    confidence: 85,
    content: `Rick Deckard is a disillusioned detective navigating a decaying Los Angeles in 2019, tasked with hunting down rogue replicants—bioengineered beings virtually indistinguishable from humans. Once a skilled blade runner, Deckard has grown cynical and detached, his sense of purpose eroded by years of morally compromising work.

Throughout the narrative, Deckard undergoes a profound transformation. Initially viewing replicants as dangerous tools to be eliminated, his encounters with them—particularly Roy Batty and Rachael—force him to reckon with their humanity. The replicants' desperate yearning for life and identity mirrors his own spiritual emptiness, creating an unexpected symmetry between hunter and hunted.

His evolving relationship with Rachael serves as the emotional core of his journey. As he falls for her, knowing she is a replicant with implanted memories and a predetermined expiration date, Deckard must confront the arbitrary nature of the distinctions he's built his career upon. The film leaves ambiguous whether Deckard himself might be a replicant—a question that underscores the central theme: the measure of humanity lies not in origin, but in the depth of one's emotional experience.`,
    highlights: [
      "Noir detective framing",
      "Hunter-hunted symmetry",
      "Ambiguous replicant status",
    ],
  },
  {
    id: "var-3",
    model: "claude-sonnet-4",
    confidence: 78,
    content: `Rick Deckard is a burned-out blade runner operating in a dystopian future where the boundaries between human and machine have become dangerously fluid. Hardened by his profession, he approaches his work with cold professionalism, seeing replicants as problems to be solved rather than beings with inner lives.

His character journey is one of reluctant awakening. Each replicant he encounters chips away at his detachment—Leon's desperate violence, Zhora's survival instinct, Pris's childlike vulnerability, and Roy Batty's poetic rage against mortality. These encounters accumulate into a crisis of conscience that Deckard can no longer suppress.

The introduction of Rachael represents the breaking point. Unlike previous models, she doesn't know she's a replicant—her implanted memories are so convincing that she believes herself fully human. Deckard's growing attachment to her forces him to acknowledge that the empathy he's relied upon to distinguish humans from replicants is not a biological marker but a cultivated capacity that replicants can possess in equal or greater measure. His final choice to flee with Rachael is both an act of rebellion against the dehumanizing system he served and an acceptance of a connection that transcends the artificial categories imposed by his world.`,
    highlights: [
      "Reluctant awakening arc",
      "Accumulation of encounters",
      "Empathy as cultivated capacity",
    ],
  },
]
