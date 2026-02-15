import { Brain, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface ProvenanceBadgeProps {
  model: string;
  confidence: number;
  rationale?: string;
  className?: string;
}

export function ProvenanceBadge({
  model,
  confidence,
  rationale,
  className,
}: ProvenanceBadgeProps) {
  // Determine confidence level and color
  const confidenceLevel =
    confidence >= 80 ? "high" : confidence >= 50 ? "medium" : "low";

  const confidenceColor = {
    high: "text-green-500 dark:text-green-400",
    medium: "text-amber-500 dark:text-amber-400",
    low: "text-red-500 dark:text-red-400",
  }[confidenceLevel];

  const badgeContent = (
    <Badge variant="secondary" className={cn("gap-1.5", className)}>
      <Brain className="size-3" />
      <span className="font-mono text-[11px]">{model}</span>
      <span className="text-muted-foreground/70">•</span>
      <ShieldCheck className={cn("size-3", confidenceColor)} />
      <span className={cn("font-semibold", confidenceColor)}>
        {confidence}%
      </span>
    </Badge>
  );

  // If no rationale, just show the badge without tooltip
  if (!rationale) {
    return badgeContent;
  }

  // With rationale, wrap in tooltip
  return (
    <Tooltip>
      <TooltipTrigger asChild>{badgeContent}</TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <div className="space-y-1">
          <div className="font-semibold text-xs">Model Rationale</div>
          <div className="text-xs text-muted-foreground leading-relaxed">
            {rationale}
          </div>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
