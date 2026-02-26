import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import {
  Box,
  Clapperboard,
  Film,
  FileText,
  Globe,
  History,
  Home,
  Inbox,
  MapPin,
  Package,
  PanelLeftOpen,
  Play,
  Plus,
  Search,
  Settings,
  Sparkles,
  Users,
} from "lucide-react"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import { Badge } from "@/components/ui/badge"
import { useSearch } from "@/lib/hooks"
import {
  formatShortcut,
  getShortcutsByCategory,
  useShortcuts,
} from "@/lib/shortcuts"
import { useNotificationDemo } from "@/lib/notifications"

interface CommandPaletteProps {
  onToggleSidebar?: () => void
}

/**
 * Unified command palette — replaces GlobalSearch, CommandPalette, and KeyboardShortcutsHelp.
 *
 * Triggers: `/` (plain) or `Cmd+K`
 * Empty state: keyboard shortcuts reference
 * With query: fuzzy-matched commands + live entity search from backend
 */
export function CommandPalette({
  onToggleSidebar,
}: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()
  const { fireDemo } = useNotificationDemo()

  // Live entity search from backend (only fires when query is non-empty)
  const { data: searchResults } = useSearch(projectId, query)

  // "/" opens the palette (plain key, no modifier)
  useShortcuts([
    {
      key: "/",
      action: () => setOpen(true),
      label: "Open command palette",
      category: "Actions",
    },
  ])

  // Cmd+K also toggles the palette
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = (callback: () => void) => {
    setOpen(false)
    setQuery("")
    callback()
  }

  const hasQuery = query.length > 0
  const hasSearchResults =
    searchResults &&
    (searchResults.scenes.length > 0 ||
      searchResults.characters.length > 0 ||
      searchResults.locations.length > 0 ||
      searchResults.props.length > 0)

  return (
    <CommandDialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v)
        if (!v) setQuery("")
      }}
    >
      <CommandInput
        placeholder="Type a command or search..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>
          <div className="py-6 text-center text-sm">
            <p className="text-muted-foreground">No results found</p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              Try a different search term
            </p>
          </div>
        </CommandEmpty>

        {/* --- Static commands (always rendered, cmdk filters by text) --- */}

        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => runCommand(() => navigate("/"))}>
            <Film className="h-4 w-4 mr-2" />
            <span className="text-sm">Projects</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => navigate(projectId ? `/${projectId}` : "/"))
            }
          >
            <Home className="h-4 w-4 mr-2" />
            <span className="text-sm">Home</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              ⌘0
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() =>
                navigate(projectId ? `/${projectId}/runs` : "/")
              )
            }
          >
            <History className="h-4 w-4 mr-2" />
            <span className="text-sm">Runs</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              ⌘1
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() =>
                navigate(projectId ? `/${projectId}/artifacts` : "/")
              )
            }
          >
            <Package className="h-4 w-4 mr-2" />
            <span className="text-sm">Artifacts</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              ⌘2
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() =>
                navigate(projectId ? `/${projectId}/inbox` : "/")
              )
            }
          >
            <Inbox className="h-4 w-4 mr-2" />
            <span className="text-sm">Inbox</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              ⌘3
            </kbd>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Actions">
          <CommandItem onSelect={() => runCommand(() => navigate("/new"))}>
            <Plus className="h-4 w-4 mr-2" />
            <span className="text-sm">New Project</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) navigate(`/${projectId}/runs/new`)
              })
            }
            disabled={!projectId}
          >
            <Play className="h-4 w-4 mr-2" />
            <span className="text-sm">Start Run</span>
          </CommandItem>
          {onToggleSidebar && (
            <CommandItem
              onSelect={() => runCommand(() => onToggleSidebar())}
            >
              <PanelLeftOpen className="h-4 w-4 mr-2" />
              <span className="text-sm">Toggle Sidebar</span>
              <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
                ⌘B
              </kbd>
            </CommandItem>
          )}
          <CommandItem onSelect={() => runCommand(() => fireDemo())}>
            <Sparkles className="h-4 w-4 mr-2" />
            <span className="text-sm">Notification Demo</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => navigate("/theme"))}>
            <Settings className="h-4 w-4 mr-2" />
            <span className="text-sm">Theme Showcase</span>
          </CommandItem>
        </CommandGroup>

        {/* Artifact type shortcuts (project-scoped) */}
        {projectId && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Find">
              <CommandItem
                onSelect={() =>
                  runCommand(() =>
                    navigate(`/${projectId}/artifacts?type=screenplay`)
                  )
                }
              >
                <FileText className="h-4 w-4 mr-2" />
                <span className="text-sm">Screenplay</span>
              </CommandItem>
              <CommandItem
                onSelect={() =>
                  runCommand(() =>
                    navigate(`/${projectId}/artifacts?type=entity_graph`)
                  )
                }
              >
                <Search className="h-4 w-4 mr-2" />
                <span className="text-sm">Entity Graph</span>
              </CommandItem>
              <CommandItem
                onSelect={() =>
                  runCommand(() =>
                    navigate(`/${projectId}/artifacts?type=characters`)
                  )
                }
              >
                <Users className="h-4 w-4 mr-2" />
                <span className="text-sm">Characters</span>
              </CommandItem>
              <CommandItem
                onSelect={() =>
                  runCommand(() =>
                    navigate(`/${projectId}/artifacts?type=locations`)
                  )
                }
              >
                <MapPin className="h-4 w-4 mr-2" />
                <span className="text-sm">Locations</span>
              </CommandItem>
              <CommandItem
                onSelect={() =>
                  runCommand(() =>
                    navigate(`/${projectId}/artifacts?type=world_bible`)
                  )
                }
              >
                <Globe className="h-4 w-4 mr-2" />
                <span className="text-sm">World Bible</span>
              </CommandItem>
            </CommandGroup>
          </>
        )}

        {/* --- Dynamic entity search results (only with query + backend results) --- */}

        {hasQuery && hasSearchResults && (
          <>
            <CommandSeparator />

            {searchResults!.scenes.length > 0 && (
              <CommandGroup heading="Scenes">
                {searchResults!.scenes.map((scene) => (
                  <CommandItem
                    key={scene.scene_id}
                    value={`scene ${scene.scene_id} ${scene.heading}`}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId)
                          navigate(`/${projectId}/scenes/${scene.scene_id}`)
                      })
                    }
                  >
                    <Clapperboard className="h-4 w-4 mr-2" />
                    <div className="flex-1 flex items-center gap-2 min-w-0">
                      <span className="text-sm truncate">{scene.heading}</span>
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1 py-0 h-4 shrink-0"
                      >
                        {scene.int_ext}
                      </Badge>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {scene.time_of_day}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {searchResults!.characters.length > 0 && (
              <CommandGroup heading="Characters">
                {searchResults!.characters.map((char) => (
                  <CommandItem
                    key={char.entity_id}
                    value={`character ${char.entity_id} ${char.display_name}`}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId)
                          navigate(`/${projectId}/characters/${char.entity_id}`)
                      })
                    }
                  >
                    <Users className="h-4 w-4 mr-2" />
                    <span className="text-sm font-medium">
                      {char.display_name}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {searchResults!.locations.length > 0 && (
              <CommandGroup heading="Locations">
                {searchResults!.locations.map((loc) => (
                  <CommandItem
                    key={loc.entity_id}
                    value={`location ${loc.entity_id} ${loc.display_name}`}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId)
                          navigate(`/${projectId}/locations/${loc.entity_id}`)
                      })
                    }
                  >
                    <MapPin className="h-4 w-4 mr-2" />
                    <span className="text-sm">{loc.display_name}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {searchResults!.props.length > 0 && (
              <CommandGroup heading="Props">
                {searchResults!.props.map((prop) => (
                  <CommandItem
                    key={prop.entity_id}
                    value={`prop ${prop.entity_id} ${prop.display_name}`}
                    onSelect={() =>
                      runCommand(() => {
                        if (projectId)
                          navigate(`/${projectId}/props/${prop.entity_id}`)
                      })
                    }
                  >
                    <Box className="h-4 w-4 mr-2" />
                    <span className="text-sm">{prop.display_name}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </>
        )}
      </CommandList>

      {/* Footer: shortcuts reference (no query) or hint bar (with query) */}
      {!hasQuery ? (
        <div className="border-t px-4 py-3 max-h-48 overflow-y-auto">
          {Object.entries(getShortcutsByCategory()).map(
            ([category, shortcuts]) => (
              <div key={category} className="mb-2 last:mb-0">
                <p className="text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-wider mb-1">
                  {category}
                </p>
                {shortcuts.map((s) => (
                  <div
                    key={s.label}
                    className="flex items-center justify-between py-0.5"
                  >
                    <span className="text-xs text-muted-foreground">
                      {s.label}
                    </span>
                    <kbd className="text-[10px] font-mono text-muted-foreground/70 bg-muted/40 rounded px-1 py-0.5">
                      {formatShortcut(s)}
                    </kbd>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      ) : (
        <div className="border-t px-3 py-2 text-xs text-muted-foreground">
          <span>
            / to open &middot; Esc to close &middot; &uarr;&darr; to navigate
            &middot; Enter to select
          </span>
        </div>
      )}
    </CommandDialog>
  )
}
