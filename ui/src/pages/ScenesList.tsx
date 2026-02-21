import { useMemo, useState } from "react";
import { Clapperboard, Share } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, ListSkeleton } from "@/components/StateViews";
import { EntityListControls } from "@/components/EntityListControls";
import { ExportModal } from '@/components/ExportModal'
import { type SortMode, type ViewDensity, type SortDirection } from "@/lib/types";
import { useScenes, useStickyPreference } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function ScenesList() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [isExportOpen, setIsExportOpen] = useState(false);
  const { data: scenes, isLoading } = useScenes(projectId!);
  const [sort, setSort] = useStickyPreference<SortMode>(projectId, 'scenes.sort', 'script-order');
  const [density, setDensity] = useStickyPreference<ViewDensity>(projectId, 'scenes.density', 'medium');
  const [direction, setDirection] = useStickyPreference<SortDirection>(projectId, 'scenes.direction', 'asc');

  const sortedScenes = useMemo(() => {
    if (!scenes) return [];

    const sorted = [...scenes];

    switch (sort) {
      case 'script-order':
        sorted.sort((a, b) => a.index - b.index);
        break;
      case 'alphabetical':
        sorted.sort((a, b) =>
          a.heading.toLowerCase().localeCompare(b.heading.toLowerCase())
        );
        break;
      case 'prominence':
        // Scenes don't have a great prominence metric — use heading length as proxy
        // Fall back to script order for ties
        sorted.sort((a, b) => {
          const lenDiff = b.heading.length - a.heading.length;
          return lenDiff !== 0 ? lenDiff : a.index - b.index;
        });
        break;
    }

    if (direction === 'desc') {
      sorted.reverse();
    }

    return sorted;
  }, [scenes, sort, direction]);

  if (isLoading) {
    return <ListSkeleton />;
  }

  if (!scenes || scenes.length === 0) {
    return (
      <EmptyState
        icon={Clapperboard}
        title="No scenes yet"
        description="Run the pipeline to extract scenes from your screenplay"
      />
    );
  }

  const getIntExtVariant = (
    intExt: string
  ): "default" | "secondary" | "outline" => {
    if (intExt === "INT") return "default"; // blue
    if (intExt === "EXT") return "secondary"; // green
    return "outline"; // amber for INT/EXT
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Clapperboard className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Scenes</h1>
            <Badge variant="secondary" className="ml-2">
              {scenes.length}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            All scenes extracted from your screenplay
          </p>
        </div>
        <Button variant="outline" onClick={() => setIsExportOpen(true)}>
          <Share className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Controls */}
      <EntityListControls
        sort={sort}
        onSortChange={setSort}
        density={density}
        onDensityChange={setDensity}
        direction={direction}
        onDirectionChange={setDirection}
      />

      {/* Scenes List */}
      {density === 'compact' && (
        <div className="space-y-2">
          {sortedScenes.map((scene) => (
            <div
              key={scene.index}
              className="flex items-center gap-3 p-3 rounded-lg border border-border cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => navigate(`/${projectId}/scenes/${scene.entityId}`)}
            >
              <Badge variant="outline">Scene {scene.index}</Badge>
              <span className="font-medium flex-1 truncate">{scene.heading}</span>
              <Badge
                variant={getIntExtVariant(scene.intExt)}
                className={cn(
                  scene.intExt === "INT" && "bg-blue-500/20 text-blue-400",
                  scene.intExt === "EXT" && "bg-green-500/20 text-green-400",
                  scene.intExt === "INT/EXT" && "bg-amber-500/20 text-amber-400"
                )}
              >
                {scene.intExt}
              </Badge>
              {scene.timeOfDay && (
                <span className="text-sm text-muted-foreground">
                  {scene.timeOfDay}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {density === 'medium' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedScenes.map((scene) => (
          <Card
            key={scene.index}
            className="cursor-pointer hover:bg-accent/50 transition-colors"
            onClick={() => navigate(`/${projectId}/scenes/${scene.entityId}`)}
          >
            <CardContent className="p-4 space-y-3">
              {/* Scene Number and INT/EXT badges */}
              <div className="flex items-center gap-2">
                <Badge variant="outline">Scene {scene.index}</Badge>
                <Badge
                  variant={getIntExtVariant(scene.intExt)}
                  className={cn(
                    scene.intExt === "INT" && "bg-blue-500/20 text-blue-400",
                    scene.intExt === "EXT" && "bg-green-500/20 text-green-400",
                    scene.intExt === "INT/EXT" &&
                      "bg-amber-500/20 text-amber-400"
                  )}
                >
                  {scene.intExt}
                </Badge>
              </div>

              {/* Scene Heading */}
              <h3 className="font-semibold text-lg line-clamp-1">
                {scene.heading}
              </h3>

              {/* Time of Day */}
              {scene.timeOfDay && (
                <p className="text-sm text-muted-foreground">
                  {scene.timeOfDay}
                </p>
              )}

              {/* Summary */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                {scene.summary}
              </p>
            </CardContent>
          </Card>
        ))}
        </div>
      )}

      {density === 'large' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sortedScenes.map((scene) => (
            <Card
              key={scene.index}
              className="cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => navigate(`/${projectId}/scenes/${scene.entityId}`)}
            >
              <CardContent className="p-6 space-y-4">
                {/* Scene Number and INT/EXT badges */}
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Scene {scene.index}</Badge>
                  <Badge
                    variant={getIntExtVariant(scene.intExt)}
                    className={cn(
                      scene.intExt === "INT" && "bg-blue-500/20 text-blue-400",
                      scene.intExt === "EXT" && "bg-green-500/20 text-green-400",
                      scene.intExt === "INT/EXT" &&
                        "bg-amber-500/20 text-amber-400"
                    )}
                  >
                    {scene.intExt}
                  </Badge>
                </div>

                {/* Scene Heading */}
                <h3 className="font-semibold text-xl">
                  {scene.heading}
                </h3>

                {/* Time of Day */}
                {scene.timeOfDay && (
                  <p className="text-sm text-muted-foreground">
                    {scene.timeOfDay}
                  </p>
                )}

                {/* Summary (full, not clamped) */}
                <p className="text-sm text-muted-foreground">
                  {scene.summary}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId!}
        defaultScope="scenes"
      />
    </div>
  );
}
