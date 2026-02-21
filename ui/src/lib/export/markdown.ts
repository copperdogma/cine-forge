import type { EnrichedEntity, Scene } from '../hooks'
import type { ProjectSummary } from '../types'
import { formatEntityName } from '../utils'

// Helpers

function generateHeader(title: string, level: number = 1): string {
  return `${'#'.repeat(level)} ${title}\n\n`
}

function generateMetadata(label: string, value: string | number | null | undefined): string {
  if (value === null || value === undefined) return ''
  return `**${label}:** ${value}\n\n`
}

function generateList(label: string, items: string[] | undefined): string {
  if (!items || items.length === 0) return ''
  let md = `**${label}:**\n`
  for (const item of items) {
    md += `- ${item}\n`
  }
  md += '\n'
  return md
}

// Entity Renderers

export function generateSceneMarkdown(scene: Scene): string {
  let md = generateHeader(scene.heading, 2)
  md += generateMetadata('Location', scene.location)
  md += generateMetadata('Int/Ext', scene.intExt)
  md += generateMetadata('Time', scene.timeOfDay)
  md += generateMetadata('Scene Number', scene.index)
  md += generateMetadata('Summary', scene.summary)
  return md
}

export function generateCharacterMarkdown(character: EnrichedEntity): string {
  let md = generateHeader(formatEntityName(character.entity_id!), 2)
  
  const data = character.data || {}

  if (character.description) {
    md += generateMetadata('Description', character.description)
  }
  
  if (data.narrative_roles) {
    md += generateList('Narrative Roles', data.narrative_roles as string[])
  }

  if (data.dialogue_summary) {
    md += generateMetadata('Dialogue Summary', data.dialogue_summary as string)
  }

  if (data.inferred_traits) {
    md += generateList('Inferred Traits', data.inferred_traits as string[])
  }

  // Evidence is usually a list of strings or objects. Handling strings for now.
  if (data.evidence && Array.isArray(data.evidence)) {
     md += `**Evidence:**\n`;
     (data.evidence as Array<string | { quote?: string }>).forEach((ev) => {
         if (typeof ev === 'string') {
             md += `- ${ev}\n`
         } else if (ev && typeof ev === 'object' && ev.quote) {
             md += `- "${ev.quote}"\n`
         }
     })
     md += '\n'
  }

  md += generateMetadata('Scene Count', character.sceneCount)
  if (character.firstSceneNumber) {
    md += generateMetadata('First Scene', character.firstSceneNumber)
  }

  if (data.scene_presence) {
      md += generateList('Scene Appearances', data.scene_presence as string[])
  }

  return md
}

export function generateLocationMarkdown(location: EnrichedEntity): string {
  let md = generateHeader(formatEntityName(location.entity_id!), 2)
  
  const data = location.data || {}

  if (location.description) {
    md += generateMetadata('Description', location.description)
  }
  
  if (data.narrative_roles) {
    md += generateList('Narrative Roles', data.narrative_roles as string[])
  }

  if (data.inferred_traits) {
    md += generateList('Inferred Traits', data.inferred_traits as string[])
  }

  md += generateMetadata('Scene Count', location.sceneCount)
  
  if (data.scene_presence) {
      md += generateList('Scene Appearances', data.scene_presence as string[])
  }

  return md
}

export function generatePropMarkdown(prop: EnrichedEntity): string {
  let md = generateHeader(formatEntityName(prop.entity_id!), 2)
  const data = prop.data || {}

  if (prop.description) {
    md += generateMetadata('Description', prop.description)
  }
  
  if (data.narrative_roles) {
    md += generateList('Narrative Roles', data.narrative_roles as string[])
  }

  if (data.inferred_traits) {
    md += generateList('Inferred Traits', data.inferred_traits as string[])
  }

  md += generateMetadata('Scene Count', prop.sceneCount)
  
  if (data.scene_presence) {
      md += generateList('Scene Appearances', data.scene_presence as string[])
  }

  return md
}

// Collection Renderers

export function generateScenesMarkdown(scenes: Scene[]): string {
  let md = generateHeader('Scenes', 1)
  for (const scene of scenes) {
    md += generateSceneMarkdown(scene) + '---\n\n'
  }
  return md
}

export function generateCharactersMarkdown(characters: EnrichedEntity[]): string {
  let md = generateHeader('Characters', 1)
  for (const char of characters) {
    md += generateCharacterMarkdown(char) + '---\n\n'
  }
  return md
}

export function generateLocationsMarkdown(locations: EnrichedEntity[]): string {
  let md = generateHeader('Locations', 1)
  for (const loc of locations) {
    md += generateLocationMarkdown(loc) + '---\n\n'
  }
  return md
}

export function generatePropsMarkdown(props: EnrichedEntity[]): string {
  let md = generateHeader('Props', 1)
  for (const prop of props) {
    md += generatePropMarkdown(prop) + '---\n\n'
  }
  return md
}

// Project Renderer

export function generateProjectMarkdown(
  project: ProjectSummary | undefined,
  scenes: Scene[],
  characters: EnrichedEntity[],
  locations: EnrichedEntity[],
  props: EnrichedEntity[]
): string {
  let md = ''
  if (project) {
    md += generateHeader(project.display_name, 1)
    md += generateMetadata('Project ID', project.project_id)
    md += generateMetadata('Total Scenes', scenes.length)
    md += generateMetadata('Characters', characters.length)
    md += generateMetadata('Locations', locations.length)
    md += generateMetadata('Props', props.length)
    md += '---\n\n'
  }

  md += generateScenesMarkdown(scenes)
  md += generateCharactersMarkdown(characters)
  md += generateLocationsMarkdown(locations)
  md += generatePropsMarkdown(props)
  
  return md
}
