import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import {
  Film,
  Globe,
  History,
  Inbox,
  MapPin,
  Package,
  PanelLeftOpen,
  PanelRightOpen,
  Play,
  Plus,
  Search,
  Settings,
  FileText,
  Users,
  HelpCircle,
  Sparkles,
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
import { formatShortcut } from "@/lib/shortcuts"
import { useNotificationDemo } from "@/lib/notifications"

interface CommandPaletteProps {
  onToggleSidebar?: () => void
  onToggleInspector?: () => void
}

export function CommandPalette({
  onToggleSidebar,
  onToggleInspector,
}: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()
  const { fireDemo } = useNotificationDemo()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = (callback: () => void) => {
    setOpen(false)
    callback()
  }

  // Helper to dispatch keyboard shortcut
  const dispatchShortcut = (key: string, options: { meta?: boolean; ctrl?: boolean; shift?: boolean; alt?: boolean } = {}) => {
    const event = new KeyboardEvent('keydown', {
      key,
      metaKey: options.meta,
      ctrlKey: options.ctrl,
      shiftKey: options.shift,
      altKey: options.alt,
      bubbles: true,
      cancelable: true,
    })
    window.dispatchEvent(event)
  }

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>
          <div className="py-6 text-center text-sm">
            <p className="text-muted-foreground">No results found</p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              Try a different search term
            </p>
          </div>
        </CommandEmpty>

        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => runCommand(() => navigate("/"))}>
            <Film className="h-4 w-4 mr-2" />
            <span className="text-sm">Landing Page</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => navigate(projectId ? `/${projectId}` : "/"))
            }
          >
            <Play className="h-4 w-4 mr-2" />
            <span className="text-sm">Pipeline</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              {formatShortcut({ key: '1', meta: true, label: 'Go to Pipeline', category: 'Navigation' })}
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => navigate(projectId ? `/${projectId}/runs` : "/"))
            }
          >
            <History className="h-4 w-4 mr-2" />
            <span className="text-sm">Runs</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              {formatShortcut({ key: '2', meta: true, label: 'Go to Runs', category: 'Navigation' })}
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
              {formatShortcut({ key: '3', meta: true, label: 'Go to Artifacts', category: 'Navigation' })}
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
              {formatShortcut({ key: '4', meta: true, label: 'Go to Inbox', category: 'Navigation' })}
            </kbd>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => navigate("/theme"))}>
            <Settings className="h-4 w-4 mr-2" />
            <span className="text-sm">Theme Showcase</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Actions">
          <CommandItem onSelect={() => runCommand(() => navigate("/new"))}>
            <Plus className="h-4 w-4 mr-2" />
            <span className="text-sm">New Project</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              {formatShortcut({ key: 'n', meta: true, label: 'New run', category: 'Actions' })}
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/runs/new`)
                }
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
                {formatShortcut({ key: 'b', meta: true, label: 'Toggle sidebar', category: 'UI Controls' })}
              </kbd>
            </CommandItem>
          )}
          {onToggleInspector && (
            <CommandItem
              onSelect={() => runCommand(() => onToggleInspector())}
            >
              <PanelRightOpen className="h-4 w-4 mr-2" />
              <span className="text-sm">Toggle Inspector</span>
              <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
                {formatShortcut({ key: 'i', meta: true, label: 'Toggle inspector', category: 'UI Controls' })}
              </kbd>
            </CommandItem>
          )}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Artifacts">
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/artifacts?type=screenplay`)
                }
              })
            }
            disabled={!projectId}
          >
            <FileText className="h-4 w-4 mr-2" />
            <span className="text-sm">Find Screenplay</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/artifacts?type=entity_graph`)
                }
              })
            }
            disabled={!projectId}
          >
            <Search className="h-4 w-4 mr-2" />
            <span className="text-sm">Find Entity Graph</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/artifacts?type=characters`)
                }
              })
            }
            disabled={!projectId}
          >
            <Users className="h-4 w-4 mr-2" />
            <span className="text-sm">Find Characters</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/artifacts?type=locations`)
                }
              })
            }
            disabled={!projectId}
          >
            <MapPin className="h-4 w-4 mr-2" />
            <span className="text-sm">Find Locations</span>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(() => {
                if (projectId) {
                  navigate(`/${projectId}/artifacts?type=world_bible`)
                }
              })
            }
            disabled={!projectId}
          >
            <Globe className="h-4 w-4 mr-2" />
            <span className="text-sm">Find World Bible</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Demo">
          <CommandItem onSelect={() => runCommand(() => fireDemo())}>
            <Sparkles className="h-4 w-4 mr-2" />
            <span className="text-sm">Run notification demo</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Help">
          <CommandItem
            onSelect={() =>
              runCommand(() => dispatchShortcut('?', { shift: true, meta: true }))
            }
          >
            <HelpCircle className="h-4 w-4 mr-2" />
            <span className="text-sm">Keyboard Shortcuts</span>
            <kbd className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 rounded px-1">
              ⌘?
            </kbd>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
