import { Clapperboard } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, ListSkeleton } from "@/components/StateViews";
import { useScenes } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function ScenesList() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { data: scenes, isLoading } = useScenes(projectId!);

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

      {/* Scenes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenes.map((scene) => (
          <Card
            key={scene.index}
            className="cursor-pointer hover:bg-accent/50 transition-colors"
            onClick={() => navigate(`/${projectId}/scenes/${scene.index}`)}
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
    </div>
  );
}
