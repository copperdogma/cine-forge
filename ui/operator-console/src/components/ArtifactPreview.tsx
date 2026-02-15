import { FileText, Users, MapPin, Film, Book, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ArtifactPreviewProps {
  artifactType: string;
  data?: unknown;
}

// Mock data for each artifact type
const MOCK_DATA = {
  screenplay_raw: `FADE IN:

INT. COFFEE SHOP - DAY

A small, crowded coffee shop in downtown. Rain streaks the windows. SARAH (28, determined, wearing a worn leather jacket) sits at a corner table, laptop open.

SARAH
(muttering to herself)
This has to work. It has to.

The door CHIMES. MARCUS (32, charismatic, expensive suit) enters, scanning the room. He spots Sarah and approaches.

MARCUS
Sarah Chen?

Sarah looks up, wary.

SARAH
Who's asking?`,

  screenplay_normalized: `FADE IN:

INT. COFFEE SHOP - DAY

A small, crowded coffee shop in downtown. Rain streaks the windows. SARAH (28, determined, wearing a worn leather jacket) sits at a corner table, laptop open.

SARAH
(muttering to herself)
This has to work. It has to.

The door CHIMES. MARCUS (32, charismatic, expensive suit) enters, scanning the room. He spots Sarah and approaches.

MARCUS
Sarah Chen?

Sarah looks up, wary.

SARAH
Who's asking?`,

  entity_graph: {
    entities: [
      { name: 'Sarah Chen', type: 'character', relationship_count: 5 },
      { name: 'Marcus Blake', type: 'character', relationship_count: 4 },
      { name: 'Coffee Shop', type: 'location', relationship_count: 3 },
      { name: 'Downtown District', type: 'location', relationship_count: 2 },
      { name: 'Chen Technologies', type: 'organization', relationship_count: 6 },
    ],
  },

  character_profile: {
    name: 'Sarah Chen',
    description: 'A brilliant software engineer turned whistleblower, Sarah is driven by a sense of justice that borders on obsession. Her technical expertise makes her dangerous to those who underestimated her.',
    traits: ['Determined', 'Tech-savvy', 'Morally rigid', 'Socially awkward', 'Resourceful'],
    appearance_count: 47,
  },

  location_profile: {
    name: 'Coffee Shop',
    description: 'A small, independently-owned coffee shop in the downtown district. Frequented by local artists and remote workers. Known for its strong espresso and free wifi. The owner, Maria, knows most regulars by name.',
    scene_count: 8,
  },

  scene_breakdown: {
    scenes: [
      { number: 1, heading: 'INT. COFFEE SHOP - DAY', location: 'Coffee Shop', time: 'Day' },
      { number: 2, heading: 'EXT. CITY STREET - NIGHT', location: 'Downtown District', time: 'Night' },
      { number: 3, heading: 'INT. SARAH\'S APARTMENT - NIGHT', location: 'Sarah\'s Apartment', time: 'Night' },
      { number: 4, heading: 'INT. CHEN TECHNOLOGIES OFFICE - DAY', location: 'Chen Technologies', time: 'Day' },
      { number: 5, heading: 'EXT. PARKING GARAGE - EVENING', location: 'Parking Garage', time: 'Evening' },
    ],
  },

  world_bible: {
    sections: [
      {
        title: 'Setting Overview',
        content: 'The story takes place in a near-future San Francisco where tech corporations wield unprecedented power. The city is divided between the gleaming corporate towers of the Financial District and the struggling neighborhoods below.',
      },
      {
        title: 'Technology',
        content: 'Advanced AI systems are commonplace, but their development is tightly controlled by a handful of mega-corporations. Quantum encryption is the standard for secure communications, making traditional hacking obsolete.',
      },
      {
        title: 'Social Structure',
        content: 'Society is stratified by access to technology. Tech workers enjoy privileges and protections, while those outside the industry struggle with automation-driven unemployment.',
      },
    ],
  },

  dialogue_analysis: {
    characters: [
      { name: 'Sarah Chen', line_count: 127, key_quote: 'The truth doesn\'t care about your quarterly earnings.' },
      { name: 'Marcus Blake', line_count: 89, key_quote: 'Everyone has a price. You just haven\'t found yours yet.' },
      { name: 'Maria', line_count: 34, key_quote: 'In my shop, everyone gets a second chance.' },
    ],
  },
};

export default function ArtifactPreview({ artifactType, data }: ArtifactPreviewProps) {
  const content = data || MOCK_DATA[artifactType as keyof typeof MOCK_DATA];

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
    const graph = content as typeof MOCK_DATA.entity_graph;
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
    const profile = content as typeof MOCK_DATA.character_profile;
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
    const profile = content as typeof MOCK_DATA.location_profile;
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
    const breakdown = content as typeof MOCK_DATA.scene_breakdown;
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
    const bible = content as typeof MOCK_DATA.world_bible;
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
    const analysis = content as typeof MOCK_DATA.dialogue_analysis;
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
