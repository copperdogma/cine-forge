import { FileText, Users, MapPin, Film, Book, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ArtifactPreviewProps {
  artifactType: string;
  data?: unknown;
}

export default function ArtifactPreview({ artifactType, data }: ArtifactPreviewProps) {
  const content = data;

  // Screenplay formats (raw and normalized)
  if (artifactType === 'screenplay_raw' || artifactType === 'screenplay_normalized') {
    const text = typeof content === 'string' ? content : '';
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <FileText className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Screenplay</span>
        </div>
        <div className="max-h-[600px] overflow-y-auto rounded-md bg-muted p-4">
          <pre className="font-mono text-xs leading-relaxed text-foreground whitespace-pre-wrap">
            {text.split('\n').map((line, i) => {
              // Scene headings: bold and uppercase
              if (line.match(/^(INT\.|EXT\.|INT\/EXT\.)/)) {
                return (
                  <div key={i} className="font-bold uppercase mb-2 mt-4 first:mt-0">
                    {line}
                  </div>
                );
              }
              // Character names: uppercase, likely at start of line after blank line
              if (line === line.toUpperCase() && line.trim() && line.length < 30 && !line.includes('.')) {
                return (
                  <div key={i} className="text-center font-semibold my-1">
                    {line}
                  </div>
                );
              }
              // Parentheticals: subtle
              if (line.trim().startsWith('(') && line.trim().endsWith(')')) {
                return (
                  <div key={i} className="text-muted-foreground pl-12">
                    {line}
                  </div>
                );
              }
              // Regular lines
              return <div key={i}>{line || '\u00A0'}</div>;
            })}
          </pre>
        </div>
      </div>
    );
  }

  // Entity Graph
  if (artifactType === 'entity_graph') {
    const graph = content as { entities: { name: string; type: string; relationship_count: number }[] };
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Users className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Entity Graph</span>
        </div>
        <div className="space-y-1">
          {graph.entities.map((entity, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-md border border-border bg-card p-2 text-xs"
            >
              <div className="flex flex-col gap-0.5">
                <span className="font-medium text-foreground">{entity.name}</span>
                <span className="text-muted-foreground capitalize">{entity.type}</span>
              </div>
              <span className="text-muted-foreground">
                {entity.relationship_count} {entity.relationship_count === 1 ? 'link' : 'links'}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Character Profile
  if (artifactType === 'character_profile') {
    const profile = content as { name: string; description: string; traits: string[]; appearance_count: number };
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Users className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Character Profile</span>
        </div>
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-1">{profile.name}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{profile.description}</p>
          </div>
          <div>
            <h4 className="text-xs font-medium text-foreground mb-1">Key Traits</h4>
            <div className="flex flex-wrap gap-1">
              {profile.traits.map((trait, i) => (
                <span
                  key={i}
                  className="rounded-full bg-muted px-2 py-0.5 text-xs text-foreground"
                >
                  {trait}
                </span>
              ))}
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Appears in {profile.appearance_count} scene{profile.appearance_count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    );
  }

  // Location Profile
  if (artifactType === 'location_profile') {
    const profile = content as { name: string; description: string; scene_count: number };
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <MapPin className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Location Profile</span>
        </div>
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-1">{profile.name}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{profile.description}</p>
          </div>
          <div className="text-xs text-muted-foreground">
            Featured in {profile.scene_count} scene{profile.scene_count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    );
  }

  // Scene Breakdown
  if (artifactType === 'scene_breakdown') {
    const breakdown = content as { scenes: { number: number; heading: string; location: string; time: string }[] };
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Film className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Scene Breakdown</span>
        </div>
        <div className="space-y-1">
          {breakdown.scenes.map((scene) => (
            <div
              key={scene.number}
              className="rounded-md border border-border bg-card p-2 space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-foreground">Scene {scene.number}</span>
                <span className={cn(
                  "rounded px-1.5 py-0.5 text-xs font-medium",
                  scene.heading.startsWith('INT.') ? "bg-blue-500/10 text-blue-400" : "bg-amber-500/10 text-amber-400"
                )}>
                  {scene.heading.startsWith('INT.') ? 'INT' : 'EXT'}
                </span>
              </div>
              <div className="text-xs font-medium text-foreground font-mono uppercase">
                {scene.heading}
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>{scene.location}</span>
                <span>•</span>
                <span>{scene.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // World Bible
  if (artifactType === 'world_bible') {
    const bible = content as { sections: { title: string; content: string }[] };
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Book className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">World Bible</span>
        </div>
        <div className="space-y-3">
          {bible.sections.map((section, i) => (
            <div key={i} className="space-y-1">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-1">
                {section.title}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {section.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Dialogue Analysis
  if (artifactType === 'dialogue_analysis') {
    const analysis = content as { characters: { name: string; line_count: number; key_quote: string }[] };
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <MessageSquare className="h-4 w-4" />
          <span className="text-xs font-medium uppercase">Dialogue Analysis</span>
        </div>
        <div className="space-y-2">
          {analysis.characters.map((char, i) => (
            <div
              key={i}
              className="rounded-md border border-border bg-card p-2 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-foreground">{char.name}</span>
                <span className="text-xs text-muted-foreground">
                  {char.line_count} {char.line_count === 1 ? 'line' : 'lines'}
                </span>
              </div>
              <div className="border-l-2 border-muted pl-2">
                <p className="text-xs italic text-muted-foreground leading-relaxed">
                  "{char.key_quote}"
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default: JSON pretty-print
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-muted-foreground">
        <FileText className="h-4 w-4" />
        <span className="text-xs font-medium uppercase">{artifactType}</span>
      </div>
      <div className="max-h-[600px] overflow-y-auto rounded-md bg-muted p-3">
        <pre className="font-mono text-xs text-foreground whitespace-pre-wrap">
          {JSON.stringify(content, null, 2)}
        </pre>
      </div>
    </div>
  );
}
