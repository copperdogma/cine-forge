// Lightweight film term glossary for hover tooltips.
// The AI provides deeper explanations when clicked — this is just the 1-liner.

export const FILM_GLOSSARY: Record<string, string> = {
  // Scene structure
  'INT': 'Interior — scene takes place indoors',
  'EXT': 'Exterior — scene takes place outdoors',
  'INT/EXT': 'Scene moves between interior and exterior',
  'INT./EXT.': 'Scene moves between interior and exterior',

  // Scene attributes
  'tone & mood': 'The emotional atmosphere and visual feeling of a scene',
  'narrative beats': 'Key story moments or turning points within a scene',
  'narrative beat': 'A key story moment or turning point within a scene',
  'narrative role': 'A character\'s function in the story (protagonist, antagonist, mentor, etc.)',
  'narrative significance': 'How a location or prop serves the story thematically',
  'scene presence': 'Which scenes a character, location, or prop appears in',

  // Character analysis
  'dialogue summary': 'Overview of how a character speaks — patterns, vocabulary, emotional register',
  'inferred traits': 'Character qualities deduced from behavior, dialogue, and actions — not stated explicitly',
  'explicit evidence': 'Direct textual proof from the screenplay supporting an analysis claim',

  // Production
  'provenance': 'Which AI model produced this artifact and how confident it is',
  'entity graph': 'A map of relationships between characters, locations, and props',
  'bible': 'A comprehensive reference document for a character, location, or prop',
  'bible manifest': 'The index of all reference documents generated for a story entity',
  'canonical script': 'The normalized, cleaned version of the screenplay used for analysis',

  // Beat types
  'establishing_shot': 'Opening visual that sets the location, time, and mood',
  'inciting_incident': 'The event that disrupts the status quo and launches the story',
  'rising_action': 'Events that build tension and complicate the central conflict',
  'climax': 'The peak moment of conflict — the turning point',
  'resolution': 'How the story wraps up after the climax',
  'exposition': 'Background information the audience needs to understand the story',
}

/** Dispatch a question to the chat panel. ChatPanel listens for this event. */
export function askChatQuestion(question: string) {
  window.dispatchEvent(
    new CustomEvent('cineforge:ask', { detail: { question } }),
  )
}
