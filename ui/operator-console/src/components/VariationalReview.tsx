import { useState } from "react"
import { Brain, RefreshCw, Check, ThumbsUp, Sparkles } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

export interface Variation {
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