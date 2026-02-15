import { useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import {
  Clapperboard,
  Users,
  MapPin,
  Box,
  Package,
} from "lucide-react"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Badge } from "@/components/ui/badge"
import { useShortcuts } from "@/lib/shortcuts"

// Mock entity types
type Scene = {
  id: string
  heading: string
  location: string
  timeOfDay: string
  intExt: "INT" | "EXT"
}

type Character = {
  id: string
  name: string
  role: string
}

type Location = {
  id: string
  name: string
  intExt: "INT" | "EXT"
  sceneCount: number
}

type Prop = {
  id: string
  name: string
  sceneIds: string[]
}

type ArtifactSearchResult = {
  id: string
  type: string
  entity: string
  version: number
}

// Mock data - Blade Runner-esque sci-fi content
const MOCK_SCENES: Scene[] = [
  {
    id: "scene-001",
    heading: "LAPD HEADQUARTERS - BULLPEN - NIGHT",
    location: "LAPD Headquarters",
    timeOfDay: "NIGHT",
    intExt: "INT",
  },
  {
    id: "scene-002",
    heading: "K'S APARTMENT - LIVING ROOM - DAWN",
    location: "K's Apartment",
    timeOfDay: "DAWN",
    intExt: "INT",
  },
  {
    id: "scene-003",
    heading: "PROTEIN FARM - EXTERIOR - DAY",
    location: "Protein Farm",
    timeOfDay: "DAY",
    intExt: "EXT",
  },
  {
    id: "scene-004",
    heading: "WALLACE CORP - MAIN HALL - DAY",
    location: "Wallace Corp",
    timeOfDay: "DAY",
    intExt: "INT",
  },
  {
    id: "scene-005",
    heading: "LAS VEGAS RUINS - CASINO FLOOR - NIGHT",
    location: "Las Vegas Ruins",
    timeOfDay: "NIGHT",
    intExt: "INT",
  },
  {
    id: "scene-006",
    heading: "SPINNER VEHICLE - COCKPIT - NIGHT",
    location: "Spinner Vehicle",
    timeOfDay: "NIGHT",
    intExt: "INT",
  },
  {
    id: "scene-007",
    heading: "WALLACE CORP - MEMORY ARCHIVE - DAY",
    location: "Wallace Corp",
    timeOfDay: "DAY",
    intExt: "INT",
  },
  {
    id: "scene-008",
    heading: "PROTEIN FARM - GREENHOUSE - DUSK",
    location: "Protein Farm",
    timeOfDay: "DUSK",
    intExt: "INT",
  },
]

const MOCK_CHARACTERS: Character[] = [
  {
    id: "char-001",
    name: "Officer K",
    role: "Blade Runner, LAPD",
  },
  {
    id: "char-002",
    name: "Joi",
    role: "AI Companion",
  },
  {
    id: "char-003",
    name: "Luv",
    role: "Wallace's Enforcer",
  },
  {
    id: "char-004",
    name: "Niander Wallace",
    role: "Replicant Manufacturer",
  },
  {
    id: "char-005",
    name: "Ana Stelline",
    role: "Memory Designer",
  },
  {
    id: "char-006",
    name: "Sapper Morton",
    role: "Rogue Replicant",
  },
]

const MOCK_LOCATIONS: Location[] = [
  {
    id: "loc-001",
    name: "LAPD HQ",
    intExt: "INT",
    sceneCount: 4,
  },
  {
    id: "loc-002",
    name: "Wallace Corp",
    intExt: "INT",
    sceneCount: 6,
  },
  {
    id: "loc-003",
    name: "K's Apartment",
    intExt: "INT",
    sceneCount: 3,
  },
  {
    id: "loc-004",
    name: "Protein Farm",
    intExt: "EXT",
    sceneCount: 5,
  },
  {
    id: "loc-005",
    name: "Las Vegas Ruins",
    intExt: "INT",
    sceneCount: 2,
  },
]

const MOCK_PROPS: Prop[] = [
  {
    id: "prop-001",
    name: "Spinner Vehicle",
    sceneIds: ["scene-006", "scene-001"],
  },
  {
    id: "prop-002",
    name: "Baseline Test Device",
    sceneIds: ["scene-001"],
  },
  {
    id: "prop-003",
    name: "Wooden Horse",
    sceneIds: ["scene-005", "scene-008"],
  },
  {
    id: "prop-004",
    name: "Memory Orb",
    sceneIds: ["scene-007"],
  },
]

const MOCK_ARTIFACTS: ArtifactSearchResult[] = [
  {
    id: "artifact-001",
    type: "screenplay",
    entity: "project",
    version: 3,
  },
  {
    id: "artifact-002",
    type: "entity_graph",
    entity: "project",
    version: 2,
  },
  {
    id: "artifact-003",
    type: "characters",
    entity: "project",
    version: 1,
  },
  {
    id: "artifact-004",
    type: "locations",
    entity: "project",
    version: 1,
  },
  {
    id: "artifact-005",
    type: "world_bible",
    entity: "project",
    version: 2,
  },
]

export function GlobalSearch() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()

  // Register the "/" shortcut
  useShortcuts([
    {
      key: "/",
      action: () => setOpen(true),
      label: "Global search",
      category: "Actions",
    },
  ])

  // Filter results based on query
  const filteredScenes = useMemo(() => {
    if (!query) return MOCK_SCENES.slice(0, 5) // Show first 5 by default
    const lowerQuery = query.toLowerCase()
    return MOCK_SCENES.filter(
      (scene) =>
        scene.heading.toLowerCase().includes(lowerQuery) ||
        scene.location.toLowerCase().includes(lowerQuery) ||
        scene.timeOfDay.toLowerCase().includes(lowerQuery)
    )
  }, [query])

  const filteredCharacters = useMemo(() => {
    if (!query) return MOCK_CHARACTERS.slice(0, 5)
    const lowerQuery = query.toLowerCase()
    return MOCK_CHARACTERS.filter(
      (char) =>
        char.name.toLowerCase().includes(lowerQuery) ||
        char.role.toLowerCase().includes(lowerQuery)
    )
  }, [query])

  const filteredLocations = useMemo(() => {
    if (!query) return MOCK_LOCATIONS.slice(0, 5)
    const lowerQuery = query.toLowerCase()
    return MOCK_LOCATIONS.filter((loc) =>
      loc.name.toLowerCase().includes(lowerQuery)
    )
  }, [query])

  const filteredProps = useMemo(() => {
    if (!query) return MOCK_PROPS.slice(0, 4)
    const lowerQuery = query.toLowerCase()
    return MOCK_PROPS.filter((prop) =>
      prop.name.toLowerCase().includes(lowerQuery)
    )
  }, [query])

  const filteredArtifacts = useMemo(() => {
    if (!query) return []
    const lowerQuery = query.toLowerCase()
    return MOCK_ARTIFACTS.filter(
      (artifact) =>
        artifact.type.toLowerCase().includes(lowerQuery) ||
        artifact.entity.toLowerCase().includes(lowerQuery)
    )
  }, [query])

  const hasResults =
    filteredScenes.length > 0 ||
    filteredCharacters.length > 0 ||
    filteredLocations.length > 0 ||
    filteredProps.length > 0 ||
    filteredArtifacts.length > 0

  const runCommand = (callback: () => void) => {
    setOpen(false)
    setQuery("")
    callback()
  }

  return (
    <CommandDialog
      open={open}
      onOpenChange={(newOpen) => {
        setOpen(newOpen)
        if (!newOpen) {
          setQuery("")
        }
      }}
      title="Global Search"
      description="Search for scenes, characters, locations, props, and artifacts"
    >
      <CommandInput
        placeholder="Search scenes, characters, locations, props..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>
          <div className="py-6 text-center text-sm">
            <p className="text-muted-foreground">No results found.</p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              Try a different search term.
            </p>
          </div>
        </CommandEmpty>

        {hasResults && (
          <>
            {filteredScenes.length > 0 && (
              <CommandGroup heading="Scenes">
                {filteredScenes.map((scene) => (
                  <CommandItem
                    key={scene.id}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId) {
                          navigate(`/${projectId}/scenes/${scene.id}`)
                        }
                      })
                    }
                  >
                    <Clapperboard className="h-4 w-4 mr-2" />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm">{scene.heading}</span>
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1 py-0 h-4"
                      >
                        {scene.intExt}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {scene.timeOfDay}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {filteredCharacters.length > 0 && (
              <CommandGroup heading="Characters">
                {filteredCharacters.map((char) => (
                  <CommandItem
                    key={char.id}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId) {
                          navigate(`/${projectId}/characters/${char.id}`)
                        }
                      })
                    }
                  >
                    <Users className="h-4 w-4 mr-2" />
                    <div className="flex-1">
                      <span className="text-sm font-medium">{char.name}</span>
                      <span className="text-xs text-muted-foreground ml-2">
                        {char.role}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {filteredLocations.length > 0 && (
              <CommandGroup heading="Locations">
                {filteredLocations.map((loc) => (
                  <CommandItem
                    key={loc.id}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId) {
                          navigate(`/${projectId}/locations/${loc.id}`)
                        }
                      })
                    }
                  >
                    <MapPin className="h-4 w-4 mr-2" />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm">{loc.name}</span>
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1 py-0 h-4"
                      >
                        {loc.intExt}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {loc.sceneCount} scenes
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {filteredProps.length > 0 && (
              <CommandGroup heading="Props">
                {filteredProps.map((prop) => (
                  <CommandItem
                    key={prop.id}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId) {
                          navigate(`/${projectId}/props/${prop.id}`)
                        }
                      })
                    }
                  >
                    <Box className="h-4 w-4 mr-2" />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm">{prop.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {prop.sceneIds.length} scenes
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {filteredArtifacts.length > 0 && (
              <CommandGroup heading="Artifacts">
                {filteredArtifacts.map((artifact) => (
                  <CommandItem
                    key={artifact.id}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId) {
                          navigate(
                            `/${projectId}/artifacts/${artifact.type}/${artifact.entity}/v${artifact.version}`
                          )
                        }
                      })
                    }
                  >
                    <Package className="h-4 w-4 mr-2" />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm">{artifact.type}</span>
                      <span className="text-xs text-muted-foreground">
                        {artifact.entity} • v{artifact.version}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </>
        )}
      </CommandList>

      <div className="border-t px-3 py-2 text-xs text-muted-foreground">
        <span>/ to search • Esc to close • ↑↓ to navigate • Enter to select</span>
      </div>
    </CommandDialog>
  )
}
