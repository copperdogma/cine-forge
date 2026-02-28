/**
 * Artifact type display metadata — single source of truth.
 * Keys must match backend artifact_type values.
 * This is the ONLY place artifactMeta should be defined.
 */
import {
  BookOpen,
  Compass,
  Eye,
  FileText,
  Users,
  MapPin,
  Globe,
  Clapperboard,
  Drama,
  MessageSquare,
  Package,
  Scissors,
  Volume2,
} from 'lucide-react'

export const artifactMeta: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  raw_input: { icon: FileText, label: 'Screenplay', color: 'text-blue-400' },
  canonical_script: { icon: FileText, label: 'Canonical Script', color: 'text-blue-300' },
  script_bible: { icon: BookOpen, label: 'Script Bible', color: 'text-indigo-400' },
  project_config: { icon: Package, label: 'Project Config', color: 'text-slate-400' },
  entity_graph: { icon: Globe, label: 'Entity Graph', color: 'text-emerald-400' },
  character_bible: { icon: Users, label: 'Character Bible', color: 'text-amber-400' },
  location_bible: { icon: MapPin, label: 'Location Bible', color: 'text-rose-400' },
  prop_bible: { icon: Package, label: 'Prop Bible', color: 'text-orange-400' },
  bible_manifest: { icon: FileText, label: 'Bible Manifest', color: 'text-teal-400' },
  scene: { icon: Clapperboard, label: 'Scene', color: 'text-violet-400' },
  scene_index: { icon: Clapperboard, label: 'Scene Index', color: 'text-violet-300' },
  continuity_index: { icon: Globe, label: 'Continuity Index', color: 'text-cyan-400' },
  continuity_state: { icon: Globe, label: 'Continuity State', color: 'text-cyan-300' },
  dialogue_analysis: { icon: MessageSquare, label: 'Dialogue Analysis', color: 'text-orange-400' },
  intent_mood: { icon: Compass, label: 'Intent & Mood', color: 'text-purple-400' },
  rhythm_and_flow: { icon: Scissors, label: 'Rhythm & Flow', color: 'text-pink-400' },
  rhythm_and_flow_index: { icon: Scissors, label: 'Rhythm & Flow Index', color: 'text-pink-300' },
  look_and_feel: { icon: Eye, label: 'Look & Feel', color: 'text-sky-400' },
  sound_and_music: { icon: Volume2, label: 'Sound & Music', color: 'text-emerald-400' },
  character_and_performance: { icon: Drama, label: 'Character & Performance', color: 'text-amber-400' },
  story_world: { icon: Globe, label: 'Story World', color: 'text-teal-400' },
}

export function getArtifactMeta(type: string) {
  return artifactMeta[type] ?? { icon: FileText, label: type, color: 'text-muted-foreground' }
}
