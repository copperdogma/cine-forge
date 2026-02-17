import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useEffect, useRef } from 'react';

interface Scene {
  index: number;
  heading: string; // e.g., "INT. LAPD HEADQUARTERS - DAY"
  location: string; // e.g., "LAPD Headquarters"
  intExt: 'INT' | 'EXT' | 'INT/EXT';
  timeOfDay: string; // e.g., "DAY", "NIGHT", "DAWN"
  summary: string; // 1-line summary
}

interface SceneStripProps {
  scenes: Scene[];
  selectedIndex?: number;
  onSelect?: (index: number) => void;
  className?: string;
}

export function SceneStrip({
  scenes,
  selectedIndex,
  onSelect,
  className,
}: SceneStripProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedCardRef = useRef<HTMLButtonElement>(null);

  // Scroll selected card into view when selection changes
  useEffect(() => {
    if (selectedCardRef.current && selectedIndex !== undefined) {
      selectedCardRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center',
      });
    }
  }, [selectedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!onSelect || scenes.length === 0) return;

    const currentIndex = selectedIndex ?? -1;
    let newIndex = currentIndex;

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      newIndex = Math.min(currentIndex + 1, scenes.length - 1);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      newIndex = Math.max(currentIndex - 1, 0);
    }

    if (newIndex !== currentIndex && newIndex >= 0) {
      onSelect(newIndex);
    }
  };

  const getBadgeStyle = (intExt: Scene['intExt']) => {
    switch (intExt) {
      case 'INT':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'EXT':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'INT/EXT':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    }
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full overflow-hidden',
        'before:absolute before:left-0 before:top-0 before:bottom-0 before:w-8 before:bg-gradient-to-r before:from-background before:to-transparent before:z-10 before:pointer-events-none',
        'after:absolute after:right-0 after:top-0 after:bottom-0 after:w-8 after:bg-gradient-to-l after:from-background after:to-transparent after:z-10 after:pointer-events-none',
        className
      )}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <div
        className="flex gap-3 overflow-x-auto px-8 py-4 scrollbar-hide"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
        }}
      >
        {scenes.map((scene) => {
          const isSelected = selectedIndex === scene.index;
          return (
            <button
              key={scene.index}
              ref={isSelected ? selectedCardRef : null}
              onClick={() => onSelect?.(scene.index)}
              className={cn(
                'flex-shrink-0 w-[200px] h-[120px] rounded-lg',
                'bg-card border transition-all duration-200',
                'p-3 flex flex-col gap-2 text-left',
                'focus:outline-none focus:ring-2 focus:ring-primary/50',
                isSelected
                  ? 'border-primary shadow-lg shadow-primary/20'
                  : 'border-border hover:border-muted-foreground/50'
              )}
            >
              {/* Header: Scene number and INT/EXT badge */}
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs text-muted-foreground font-mono">
                  {scene.index}
                </span>
                <Badge
                  variant="outline"
                  className={cn('text-xs px-1.5 py-0', getBadgeStyle(scene.intExt))}
                >
                  {scene.intExt}
                </Badge>
              </div>

              {/* Location */}
              <div className="flex-1 flex flex-col gap-1">
                <h4 className="font-semibold text-sm leading-tight truncate">
                  {scene.location}
                </h4>
                <p className="text-xs text-muted-foreground">{scene.timeOfDay}</p>
              </div>

              {/* Summary */}
              <p className="text-xs text-muted-foreground/80 line-clamp-1">
                {scene.summary}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
