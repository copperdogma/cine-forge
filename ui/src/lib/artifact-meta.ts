/**
 * Artifact type display metadata — single source of truth.
 * Keys must match backend artifact_type values.
 * This is the ONLY place artifactMeta should be defined.
 */
import {
  FileText,
  Users,
  MapPin,
  Globe,
  Clapperboard,
  MessageSquare,
  Package,
  Scissors,
} from 'lucide-react'

export const artifactMeta: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  raw_input: { icon: FileText, label: 'Screenplay', color: 'text-blue-400' },
  canonical_script: { icon: FileText, label: 'Canonical Script', color: 'text-blue-300' },
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
  editorial_direction: { icon: Scissors, label: 'Editorial Direction', color: 'text-pink-400' },
  editorial_direction_index: { icon: Scissors, label: 'Editorial Index', color: 'text-pink-300' },
}

export function getArtifactMeta(type: string) {
  return artifactMeta[type] ?? { icon: FileText, label: type, color: 'text-muted-foreground' }
}
