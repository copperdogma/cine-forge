import { Users, MapPin, Film, Book, Globe, Package, Clock, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import { useState, Suspense, lazy } from 'react'
import { GlossaryTerm, SectionHelp } from '@/components/GlossaryTerm'

// Lazy load the heavy CodeMirror editor to reduce main bundle size
const ScreenplayEditor = lazy(() => import('@/components/ScreenplayEditor'))

// CollapsibleSection helper component
function CollapsibleSection({
  title,
  icon,
  defaultOpen = true,
  helpQuestion,
  children
}: {
  title: string
  icon?: React.ReactNode
  defaultOpen?: boolean
  /** If set, a small ? icon appears next to the title. Click sends this question to the chat. */
  helpQuestion?: string
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="flex items-center gap-1.5">
        <CollapsibleTrigger className="flex items-center gap-2 text-left group">
          <ChevronRight className={cn('h-3.5 w-3.5 text-muted-foreground transition-transform', open && 'rotate-90')} />
          {icon}
          <span className="text-xs text-muted-foreground font-medium">{title}</span>
        </CollapsibleTrigger>
        {helpQuestion && <SectionHelp question={helpQuestion} />}
      </div>
      <CollapsibleContent className="mt-2">
        {children}
      </CollapsibleContent>
    </Collapsible>
  )
}

// Type guards and helper functions
function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value)
}

function getString(obj: Record<string, unknown>, key: string): string | null {
  const value = obj[key]
  return typeof value === 'string' ? value : null
}

function getNumber(obj: Record<string, unknown>, key: string): number | null {
  const value = obj[key]
  return typeof value === 'number' ? value : null
}

function getArray(obj: Record<string, unknown>, key: string): unknown[] {
  const value = obj[key]
  return isArray(value) ? value : []
}

function getObject(obj: Record<string, unknown>, key: string): Record<string, unknown> | null {
  const value = obj[key]
  return isObject(value) ? value : null
}

// ScriptViewer - for raw_input and canonical_script
export function ScriptViewer({ data }: { data: Record<string, unknown> }) {
  // Try to extract script text from different possible field names
  const scriptText =
    getString(data, 'script_text') ?? getString(data, 'content') ?? getString(data, 'text')

  if (!scriptText) {
    return <DefaultViewer data={data} />
  }

  const title = getString(data, 'title')
  const lineCount = getNumber(data, 'line_count')
  const sceneCount = getNumber(data, 'scene_count')

  return (
    <div className="space-y-4">
      {/* Header info */}
      {(title || lineCount !== null || sceneCount !== null) && (
        <div className="space-y-2">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {(lineCount !== null || sceneCount !== null) && (
            <div className="flex gap-4 text-xs text-muted-foreground">
              {lineCount !== null && (
                <span>
                  {lineCount.toLocaleString()} {lineCount === 1 ? 'line' : 'lines'}
                </span>
              )}
              {sceneCount !== null && (
                <span>
                  {sceneCount} {sceneCount === 1 ? 'scene' : 'scenes'}
                </span>
              )}
            </div>
          )}
          <Separator />
        </div>
      )}

      {/* Script text with CodeMirror screenplay editor */}
      <Suspense fallback={<div className="rounded-md border border-border bg-muted p-4 text-sm text-muted-foreground">Loading editor...</div>}>
        <ScreenplayEditor content={scriptText} readOnly />
      </Suspense>
    </div>
  )
}

// StructuredDataViewer - for project_config and draft_project_config
export function StructuredDataViewer({ data }: { data: Record<string, unknown> }) {
  const title = getString(data, 'title')
  const format = getString(data, 'format')
  const genre = getArray(data, 'genre')
  const tone = getArray(data, 'tone')
  const estimatedDuration = getNumber(data, 'estimated_duration_minutes')
  const primaryCharacters = getArray(data, 'primary_characters')
  const supportingCharacters = getArray(data, 'supporting_characters')
  const locationsSummary = getArray(data, 'locations_summary')
  const locationCount = getNumber(data, 'location_count')
  const targetAudience = getString(data, 'target_audience')
  const aspectRatio = getString(data, 'aspect_ratio')
  const productionMode = getString(data, 'production_mode')
  const confirmed = data.confirmed === true

  return (
    <div className="space-y-4">
      {/* Main project info */}
      <div className="space-y-3">
        {title && (
          <div>
            <h3 className="text-lg font-semibold mb-1">{title}</h3>
            {!confirmed && (
              <Badge variant="outline" className="text-xs text-amber-400 border-amber-400/30">
                Draft
              </Badge>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          {format && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Format</p>
              <p className="font-medium capitalize">{format}</p>
            </div>
          )}

          {estimatedDuration !== null && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Est. Duration</p>
              <p className="font-medium">{estimatedDuration} minutes</p>
            </div>
          )}

          {aspectRatio && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Aspect Ratio</p>
              <p className="font-medium font-mono">{aspectRatio}</p>
            </div>
          )}

          {productionMode && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Production Mode</p>
              <p className="font-medium capitalize">{productionMode.replace('_', ' ')}</p>
            </div>
          )}

          {targetAudience && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Target Audience</p>
              <p className="font-medium">{targetAudience}</p>
            </div>
          )}
        </div>
      </div>

      {/* Genre and tone */}
      {(genre.length > 0 || tone.length > 0) && (
        <>
          <Separator />
          <CollapsibleSection title="Genre & Tone">
            <div className="space-y-3">
              {genre.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Genre</p>
                  <div className="flex flex-wrap gap-1.5">
                    {genre.map((g, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {String(g)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {tone.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Tone</p>
                  <div className="flex flex-wrap gap-1.5">
                    {tone.map((t, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {String(t)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Characters */}
      {(primaryCharacters.length > 0 || supportingCharacters.length > 0) && (
        <>
          <Separator />
          <CollapsibleSection title="Characters">
            <div className="space-y-3">
              {primaryCharacters.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Primary Characters</p>
                  <div className="flex flex-wrap gap-1.5">
                    {primaryCharacters.map((char, i) => (
                      <Badge key={i} className="text-xs gap-1">
                        <Users className="h-3 w-3" />
                        {String(char)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {supportingCharacters.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Supporting Characters</p>
                  <div className="flex flex-wrap gap-1.5">
                    {supportingCharacters.map((char, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {String(char)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Locations */}
      {(locationCount !== null || locationsSummary.length > 0) && (
        <>
          <Separator />
          <CollapsibleSection
            title={locationCount !== null ? `Locations (${locationCount})` : 'Locations'}
            icon={<MapPin className="h-4 w-4 text-muted-foreground" />}
          >
            <div className="space-y-2">
              {locationsSummary.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {locationsSummary.map((loc, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {String(loc)}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CollapsibleSection>
        </>
      )}
    </div>
  )
}

// ProfileViewer - for character_profile, location_profile, prop_profile
export function ProfileViewer({
  data,
  profileType,
}: {
  data: Record<string, unknown>
  profileType: 'character' | 'location' | 'prop'
}) {
  const name = getString(data, 'name')
  const description = getString(data, 'description')
  const scenePresence = getArray(data, 'scene_presence')
  const confidence = getNumber(data, 'overall_confidence')

  // Character-specific fields
  const aliases = getArray(data, 'aliases')
  const narrativeRole = getString(data, 'narrative_role')
  const dialogueSummary = getString(data, 'dialogue_summary')
  const explicitEvidence = getArray(data, 'explicit_evidence')
  const inferredTraits = getArray(data, 'inferred_traits')

  // Location-specific fields
  const physicalTraits = getArray(data, 'physical_traits')
  const narrativeSignificance = getString(data, 'narrative_significance')

  const Icon = profileType === 'character' ? Users : profileType === 'location' ? MapPin : Package

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={cn('rounded-lg bg-card border border-border p-2')}>
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          {name && <h3 className="text-lg font-semibold mb-1">{name}</h3>}
          {aliases.length > 0 && (
            <p className="text-xs text-muted-foreground">
              aka {aliases.map((a) => String(a)).join(', ')}
            </p>
          )}
        </div>
        {confidence !== null && (
          <Badge variant="outline" className="text-xs">
            {Math.round(confidence * 100)}% confidence
          </Badge>
        )}
      </div>

      {/* Description */}
      {description && (
        <>
          <Separator />
          <CollapsibleSection title="Description">
            <p className="text-sm leading-relaxed">{description}</p>
          </CollapsibleSection>
        </>
      )}

      {/* Character-specific: Narrative role */}
      {profileType === 'character' && narrativeRole && (
        <>
          <Separator />
          <CollapsibleSection title="Narrative Role" helpQuestion="What does this character's narrative role mean for the story?">
            <Badge className="capitalize">{narrativeRole}</Badge>
          </CollapsibleSection>
        </>
      )}

      {/* Character-specific: Dialogue summary */}
      {profileType === 'character' && dialogueSummary && (
        <>
          <Separator />
          <CollapsibleSection title="Dialogue Summary">
            <p className="text-sm leading-relaxed">{dialogueSummary}</p>
          </CollapsibleSection>
        </>
      )}

      {/* Character-specific: Inferred traits */}
      {profileType === 'character' && inferredTraits.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Inferred Traits" helpQuestion="How are character traits inferred from the screenplay?">
            <div className="space-y-2">
              {inferredTraits.map((traitObj, i) => {
                if (!isObject(traitObj)) return null
                const trait = getString(traitObj, 'trait')
                const value = getString(traitObj, 'value')
                const rationale = getString(traitObj, 'rationale')
                return (
                  <div key={i} className="text-sm">
                    <p className="font-medium">
                      {trait}: <span className="font-normal text-muted-foreground">{value}</span>
                    </p>
                    {rationale && <p className="text-xs text-muted-foreground mt-0.5">{rationale}</p>}
                  </div>
                )
              })}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Location-specific: Physical traits */}
      {profileType === 'location' && physicalTraits.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Physical Traits">
            <div className="flex flex-wrap gap-1.5">
              {physicalTraits.map((trait, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {String(trait)}
                </Badge>
              ))}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Narrative significance (location/prop) */}
      {(profileType === 'location' || profileType === 'prop') && narrativeSignificance && (
        <>
          <Separator />
          <div>
            <p className="text-xs text-muted-foreground mb-2">
              <GlossaryTerm term="narrative significance">Narrative Significance</GlossaryTerm>
            </p>
            <p className="text-sm leading-relaxed">{narrativeSignificance}</p>
          </div>
        </>
      )}

      {/* Scene presence */}
      {scenePresence.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection
            title={`Scene Presence (${scenePresence.length})`}
            icon={<Film className="h-4 w-4 text-muted-foreground" />}
          >
            <div className="flex flex-wrap gap-1">
              {scenePresence.map((scene, i) => (
                <Badge key={i} variant="outline" className="text-xs font-mono">
                  {String(scene)}
                </Badge>
              ))}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Character-specific: Evidence samples */}
      {profileType === 'character' && explicitEvidence.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Evidence (sample)" helpQuestion="What counts as explicit evidence for character analysis?">
            <div className="space-y-2">
              {explicitEvidence.map((evidenceObj, i) => {
                if (!isObject(evidenceObj)) return null
                const trait = getString(evidenceObj, 'trait')
                const quote = getString(evidenceObj, 'quote')
                const sourceScene = getString(evidenceObj, 'source_scene')
                return (
                  <Card key={i}>
                    <CardContent className="p-3 space-y-1">
                      {trait && <p className="text-xs font-medium">{trait}</p>}
                      {quote && (
                        <blockquote className="border-l-2 border-muted pl-2 text-xs italic text-muted-foreground">
                          "{quote}"
                        </blockquote>
                      )}
                      {sourceScene && (
                        <p className="text-xs text-muted-foreground">— {sourceScene}</p>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CollapsibleSection>
        </>
      )}
    </div>
  )
}

// SceneViewer - for scene artifacts
export function SceneViewer({ data }: { data: Record<string, unknown> }) {
  const sceneNumber = getNumber(data, 'scene_number')
  const heading = getString(data, 'heading')
  const location = getString(data, 'location')
  const timeOfDay = getString(data, 'time_of_day')
  const intExt = getString(data, 'int_ext')
  const charactersPresent = getArray(data, 'characters_present')
  const elements = getArray(data, 'elements')
  const toneMood = getString(data, 'tone_mood')
  const narrativeBeats = getArray(data, 'narrative_beats')
  const confidence = getNumber(data, 'confidence')

  return (
    <div className="space-y-4">
      {/* Scene header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {sceneNumber !== null && (
            <Badge className="text-xs">Scene {sceneNumber}</Badge>
          )}
          {intExt && (
            <GlossaryTerm term={intExt}>
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  intExt === 'INT' ? 'text-blue-400 border-blue-400/30' : 'text-amber-400 border-amber-400/30',
                )}
              >
                {intExt}
              </Badge>
            </GlossaryTerm>
          )}
          {confidence !== null && (
            <Badge variant="outline" className="text-xs ml-auto">
              {Math.round(confidence * 100)}% confidence
            </Badge>
          )}
        </div>

        {heading && (
          <h3 className="text-lg font-semibold font-mono uppercase">{heading}</h3>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          {location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="font-medium">{location}</p>
              </div>
            </div>
          )}

          {timeOfDay && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Time of Day</p>
                <p className="font-medium capitalize">{timeOfDay}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Characters present */}
      {charactersPresent.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection
            title="Characters Present"
            icon={<Users className="h-4 w-4 text-muted-foreground" />}
          >
            <div className="flex flex-wrap gap-1.5">
              {charactersPresent.map((char, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {String(char)}
                </Badge>
              ))}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Tone/Mood */}
      {toneMood && (
        <>
          <Separator />
          <CollapsibleSection title="Tone & Mood">
            <p className="text-sm">{toneMood}</p>
          </CollapsibleSection>
        </>
      )}

      {/* Narrative beats */}
      {narrativeBeats.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Narrative Beats" helpQuestion="What are narrative beats and how were they identified in this scene?">
            <div className="space-y-2">
              {narrativeBeats.map((beatObj, i) => {
                if (!isObject(beatObj)) return null
                const beatType = getString(beatObj, 'beat_type')
                const description = getString(beatObj, 'description')
                return (
                  <Card key={i}>
                    <CardContent className="p-3">
                      {beatType && (
                        <GlossaryTerm term={beatType}>
                          <Badge variant="outline" className="text-xs mb-2 capitalize">
                            {beatType.replace('_', ' ')}
                          </Badge>
                        </GlossaryTerm>
                      )}
                      {description && <p className="text-xs">{description}</p>}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CollapsibleSection>
        </>
      )}

      {/* Script elements preview */}
      {elements.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Script Elements">
            <div className="max-h-[600px] overflow-y-auto rounded-md bg-muted p-3 space-y-1">
              {elements.map((elemObj, i) => {
                if (!isObject(elemObj)) return null
                const elementType = getString(elemObj, 'element_type')
                const content = getString(elemObj, 'content')
                if (!content) return null

                const typeClass =
                  elementType === 'scene_heading'
                    ? 'font-bold uppercase'
                    : elementType === 'character'
                      ? 'text-center font-semibold'
                      : elementType === 'dialogue'
                        ? 'pl-4'
                        : elementType === 'parenthetical'
                          ? 'text-muted-foreground pl-8 text-xs'
                          : ''

                return (
                  <div key={i} className={cn('text-xs font-mono', typeClass)}>
                    {content}
                  </div>
                )
              })}
            </div>
          </CollapsibleSection>
        </>
      )}
    </div>
  )
}

// BibleViewer - for bible_manifest
export function BibleViewer({
  data,
  bibleFiles,
}: {
  data: Record<string, unknown>
  bibleFiles?: Record<string, unknown>
}) {
  const entityType = getString(data, 'entity_type')
  const entityId = getString(data, 'entity_id')
  const displayName = getString(data, 'display_name')
  const files = getArray(data, 'files')
  const version = getNumber(data, 'version')

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Book className="h-5 w-5 text-muted-foreground" />
          {displayName && <h3 className="text-lg font-semibold">{displayName}</h3>}
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {entityType && <Badge variant="outline" className="text-xs capitalize">{entityType}</Badge>}
          {entityId && <span className="font-mono">{entityId}</span>}
          {version !== null && <span>Version {version}</span>}
        </div>
      </div>

      {/* Files manifest */}
      {files.length > 0 && (
        <>
          <Separator />
          <div>
            <p className="text-xs text-muted-foreground mb-2">
              {files.length} {files.length === 1 ? 'file' : 'files'} in manifest
            </p>
            <div className="space-y-2">
              {files.map((fileObj, i) => {
                if (!isObject(fileObj)) return null
                const filename = getString(fileObj, 'filename')
                const purpose = getString(fileObj, 'purpose')
                const provenance = getString(fileObj, 'provenance')
                const fileVersion = getNumber(fileObj, 'version')

                return (
                  <Card key={i}>
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium font-mono truncate">{filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {purpose && (
                              <Badge variant="secondary" className="text-xs">
                                {purpose.replace('_', ' ')}
                              </Badge>
                            )}
                            {provenance && (
                              <span className="text-xs text-muted-foreground">
                                {provenance.replace('_', ' ')}
                              </span>
                            )}
                          </div>
                        </div>
                        {fileVersion !== null && (
                          <Badge variant="outline" className="text-xs">
                            v{fileVersion}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        </>
      )}

      {/* Bible files content (if loaded) */}
      {bibleFiles && Object.keys(bibleFiles).length > 0 && (
        <>
          <Separator />
          <div>
            <p className="text-xs text-muted-foreground mb-2">File Contents</p>
            <div className="space-y-2">
              {Object.entries(bibleFiles).map(([filename, content]) => (
                <details key={filename} className="group">
                  <summary className="cursor-pointer rounded-md border border-border bg-muted/30 p-2.5 text-sm font-medium hover:bg-muted/50 transition-colors">
                    <span className="font-mono text-xs">{filename}</span>
                  </summary>
                  <div className="mt-2 rounded-md bg-muted p-3">
                    <pre className="font-mono text-xs text-foreground whitespace-pre-wrap overflow-x-auto max-h-[400px] overflow-y-auto">
                      {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                    </pre>
                  </div>
                </details>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// EntityGraphViewer - for entity_graph
export function EntityGraphViewer({ data }: { data: Record<string, unknown> }) {
  const edges = getArray(data, 'edges')
  const entityCount = getObject(data, 'entity_count')
  const edgeCount = getNumber(data, 'edge_count')
  const confidence = getNumber(data, 'extraction_confidence')

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {entityCount && (
          <Card>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground mb-1">Entities</p>
              <div className="space-y-1">
                {Object.entries(entityCount).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className="capitalize">{type}</span>
                    <Badge variant="secondary" className="text-xs">
                      {String(count)}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {edgeCount !== null && (
          <Card>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground mb-1">Relationships</p>
              <p className="text-2xl font-semibold">{edgeCount}</p>
            </CardContent>
          </Card>
        )}

        {confidence !== null && (
          <Card>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground mb-1">Confidence</p>
              <p className="text-2xl font-semibold">{Math.round(confidence * 100)}%</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edges */}
      {edges.length > 0 && (
        <>
          <Separator />
          <CollapsibleSection title="Relationships" helpQuestion="How is the entity graph constructed and what do these relationships mean?">
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {edges.map((edgeObj, i) => {
                if (!isObject(edgeObj)) return null
                const sourceType = getString(edgeObj, 'source_type')
                const sourceId = getString(edgeObj, 'source_id')
                const targetType = getString(edgeObj, 'target_type')
                const targetId = getString(edgeObj, 'target_id')
                const relationshipType = getString(edgeObj, 'relationship_type')
                const edgeConfidence = getNumber(edgeObj, 'confidence')
                const sceneRefs = getArray(edgeObj, 'scene_refs')

                return (
                  <Card key={i}>
                    <CardContent className="p-3">
                      <div className="flex items-start gap-2 mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 text-sm">
                            <Badge variant="secondary" className="text-xs capitalize">
                              {sourceType}
                            </Badge>
                            <span className="font-medium">{sourceId}</span>
                          </div>
                        </div>
                        <Globe className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 text-sm">
                            <Badge variant="secondary" className="text-xs capitalize">
                              {targetType}
                            </Badge>
                            <span className="font-medium">{targetId}</span>
                          </div>
                        </div>
                      </div>

                      {relationshipType && (
                        <p className="text-xs text-muted-foreground mb-1 text-center">
                          {relationshipType}
                        </p>
                      )}

                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border">
                        {sceneRefs.length > 0 && (
                          <span className="text-xs text-muted-foreground">
                            {sceneRefs.length} {sceneRefs.length === 1 ? 'scene' : 'scenes'}
                          </span>
                        )}
                        {edgeConfidence !== null && (
                          <Badge variant="outline" className="text-xs ml-auto">
                            {Math.round(edgeConfidence * 100)}%
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CollapsibleSection>
        </>
      )}
    </div>
  )
}

// DefaultViewer - fallback for unknown types or raw JSON
export function DefaultViewer({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="max-h-[600px] overflow-y-auto rounded-md bg-muted p-4">
      <pre className="font-mono text-xs text-foreground whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}
