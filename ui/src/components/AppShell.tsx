import { NavLink, Outlet, useNavigate, useParams, useLocation, Link } from 'react-router-dom'
import {
  Film,
  History,
  Package,
  Inbox,
  FileText,
  Clapperboard,
  Users,
  MapPin,
  Wrench,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  ChevronRight,
  ChevronDown,
  Settings,
  X,
  MessageSquare,
  Info,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible'
import { RightPanelProvider, useRightPanel, useInspector } from '@/lib/right-panel'
import { CommandPalette } from '@/components/CommandPalette'
import { ProjectSettings } from '@/components/ProjectSettings'
import { ChatPanel } from '@/components/ChatPanel'
import { ChangelogDialog } from '@/components/ChangelogDialog'
import { useShortcuts } from '@/lib/shortcuts'
import { fetchHealth } from '@/lib/api'
import { useProject, useChatLoader, useArtifactGroups, useRuns } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import { useRunProgressChat } from '@/lib/use-run-progress'
import { cn } from '@/lib/utils'

/** Artifact type → nav route mapping for count badges. */
const NAV_ARTIFACT_TYPES: Record<string, string[]> = {
  scenes: ['scene'],
  characters: ['character_bible'],
  locations: ['location_bible'],
  props: ['prop_bible'],
}

const mainNavBase = [
  { to: '', label: 'Script', icon: FileText, end: true },
  { to: 'scenes', label: 'Scenes', icon: Clapperboard },
  { to: 'characters', label: 'Characters', icon: Users },
  { to: 'locations', label: 'Locations', icon: MapPin },
  { to: 'props', label: 'Props', icon: Wrench },
  { to: 'inbox', label: 'Inbox', icon: Inbox },
]

/** Animated badge that pulses when count increases. */
function CountBadge({ count }: { count: number }) {
  const prevRef = useRef(count)
  const [pulse, setPulse] = useState(false)

  useEffect(() => {
    if (count > prevRef.current) {
      const t1 = setTimeout(() => setPulse(true), 0)
      const t2 = setTimeout(() => setPulse(false), 600)
      return () => {
        clearTimeout(t1)
        clearTimeout(t2)
      }
    }
    prevRef.current = count
  }, [count])

  // Also update ref when not pulsing (handles decreases)
  useEffect(() => { prevRef.current = count }, [count])

  if (count === 0) return null

  return (
    <Badge
      variant="secondary"
      className={cn(
        'ml-auto text-xs px-1.5 py-0 tabular-nums transition-transform duration-300',
        pulse && 'animate-pulse scale-110',
      )}
    >
      {count}
    </Badge>
  )
}

const advancedNavItems = [
  { to: 'runs', label: 'Runs', icon: History },
  { to: 'artifacts', label: 'Artifacts', icon: Package },
]

function ShellInner() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [navOpen, setNavOpen] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [changelogOpen, setChangelogOpen] = useState(false)
  const panel = useRightPanel()
  const [panelWidth, setPanelWidth] = useState(380)
  const isDragging = useRef(false)

  const handleDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const newWidth = window.innerWidth - e.clientX
      setPanelWidth(Math.max(280, Math.min(700, newWidth)))
    }
    const handleMouseUp = () => {
      if (!isDragging.current) return
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])
  const inspector = useInspector()
  const { data: project } = useProject(projectId)

  const displayName = project?.display_name ?? projectId?.slice(0, 12) ?? 'Project'

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 5 * 60 * 1000,
  })

  // Load chat from backend JSONL (runs on every page, not just Home)
  useChatLoader(projectId)

  // Track active run progress — adds chat messages as stages complete
  useRunProgressChat(projectId)

  // --- Live nav counts ---
  const { data: artifactGroups } = useArtifactGroups(projectId)
  const { data: runs } = useRuns(projectId)

  const navCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    if (artifactGroups) {
      for (const [route, types] of Object.entries(NAV_ARTIFACT_TYPES)) {
        counts[route] = artifactGroups.filter(g => types.includes(g.artifact_type)).length
      }
    }
    // Inbox: match ProjectInbox logic — stale artifacts + failed runs + v1 bibles needing review
    const BIBLE_TYPES = ['character_bible', 'location_bible', 'prop_bible']
    const staleCount = artifactGroups?.filter(g => g.health === 'stale').length ?? 0
    const errorCount = runs?.filter(r => r.status === 'failed').length ?? 0
    const reviewCount = artifactGroups?.filter(g =>
      BIBLE_TYPES.includes(g.artifact_type) && g.latest_version === 1 && g.health !== 'stale'
    ).length ?? 0
    counts['inbox'] = staleCount + errorCount + reviewCount
    return counts
  }, [artifactGroups, runs])

  // Emit activity notes on meaningful navigation (artifact detail, run detail)
  const prevPath = useRef(location.pathname)
  useEffect(() => {
    if (!projectId || prevPath.current === location.pathname) return
    prevPath.current = location.pathname
    const path = location.pathname

    // Artifact detail: /:projectId/artifacts/:type/:entityId/:version
    const artifactMatch = path.match(new RegExp(`^/${projectId}/artifacts/([^/]+)/([^/]+)/(\\d+)$`))
    if (artifactMatch) {
      const [, atype, entityId] = artifactMatch
      const label = entityId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      useChatStore.getState().addActivity(
        projectId,
        `Viewing: ${label}`,
        `artifacts/${atype}/${entityId}/${artifactMatch[3]}`,
      )
      return
    }

    // Run detail: /:projectId/runs/:runId
    const runMatch = path.match(new RegExp(`^/${projectId}/run/([^/]+)$`))
    if (runMatch) {
      useChatStore.getState().addActivity(
        projectId,
        `Viewing run: ${runMatch[1]}`,
        `run/${runMatch[1]}`,
      )
    }
  }, [location.pathname, projectId])

  // Keyboard shortcuts
  useShortcuts([
    { key: 'b', meta: true, action: () => setNavOpen(v => !v), label: 'Toggle sidebar' },
    { key: 'i', meta: true, action: () => panel.toggle(), label: 'Toggle right panel' },
    { key: '0', meta: true, action: () => navigate(''), label: 'Go to Script' },
    { key: '1', meta: true, action: () => navigate('scenes'), label: 'Go to Scenes' },
    { key: '2', meta: true, action: () => navigate('characters'), label: 'Go to Characters' },
    { key: '3', meta: true, action: () => navigate('locations'), label: 'Go to Locations' },
    { key: '4', meta: true, action: () => navigate('props'), label: 'Go to Props' },
    { key: '5', meta: true, action: () => navigate('inbox'), label: 'Go to Inbox' },
    { key: ',', meta: true, action: () => setSettingsOpen(true), label: 'Open settings' },
  ])

  // Build breadcrumb segments from the current path
  const getBreadcrumbs = (): { label: string; path?: string }[] => {
    const path = location.pathname
    if (!projectId) return []

    // Entity detail: /:projectId/characters/:entityId (etc.)
    const entityDetailMatch = path.match(new RegExp(`^/${projectId}/(characters|locations|props|scenes)/([^/]+)$`))
    if (entityDetailMatch) {
      const [, section, entityId] = entityDetailMatch
      const sectionLabel = section.charAt(0).toUpperCase() + section.slice(1)
      const entityName = entityId.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      return [
        { label: sectionLabel, path: `/${projectId}/${section}` },
        { label: entityName },
      ]
    }

    // Artifact detail: /:projectId/artifacts/:type/:entityId/:version
    const artifactMatch = path.match(new RegExp(`^/${projectId}/artifacts/([^/]+)/([^/]+)/(\\d+)$`))
    if (artifactMatch) {
      const [, artifactType, entityId] = artifactMatch
      const typeLabel = artifactType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
      return [
        { label: 'Artifacts', path: `/${projectId}/artifacts` },
        { label: `${typeLabel} — ${entityId}` },
      ]
    }

    // Run detail: /:projectId/run/:runId
    const runMatch = path.match(new RegExp(`^/${projectId}/run/([^/]+)$`))
    if (runMatch) {
      return [
        { label: 'Runs', path: `/${projectId}/runs` },
        { label: runMatch[1] },
      ]
    }

    if (path.includes('/scenes')) return [{ label: 'Scenes' }]
    if (path.includes('/characters')) return [{ label: 'Characters' }]
    if (path.includes('/locations')) return [{ label: 'Locations' }]
    if (path.includes('/props')) return [{ label: 'Props' }]
    if (path.includes('/runs')) return [{ label: 'Runs' }]
    if (path.includes('/artifacts')) return [{ label: 'Artifacts' }]
    if (path.includes('/inbox')) return [{ label: 'Inbox' }]
    if (path === `/${projectId}`) return [{ label: 'Script' }]
    return []
  }

  const breadcrumbs = getBreadcrumbs()

  // Auto-open advanced section if we're on a runs/artifacts page
  const isOnAdvancedPage = location.pathname.includes('/runs') || location.pathname.includes('/artifacts')

  return (
    <div className="fixed inset-0 flex overflow-hidden">
      <CommandPalette
        onToggleSidebar={() => setNavOpen(v => !v)}
        onToggleInspector={() => panel.toggle()}
      />
      {/* Keyboard-triggered settings dialog */}
      <ProjectSettings
        projectId={projectId ?? ''}
        project={project}
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
      {/* Left Navigator Panel */}
      <aside
        className={cn(
          'flex flex-col border-r border-border bg-sidebar transition-all duration-200 overflow-hidden',
          navOpen ? 'w-56' : 'w-0',
        )}
      >
        {/* App branding — links to project list */}
        <Link
          to="/"
          className="flex items-center gap-2 px-4 py-3 hover:bg-accent/50 transition-colors"
        >
          <Film className="h-5 w-5 text-primary shrink-0" />
          <span className="text-sm font-semibold">CineForge</span>
        </Link>

        <Separator />

        {/* Navigation */}
        <ScrollArea className="flex-1 py-2">
          <nav aria-label="Project navigation" className="flex flex-col gap-0.5 px-2">
            {/* Main entity navigation */}
            {mainNavBase.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                  )
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.label}</span>
                <CountBadge count={navCounts[item.to] ?? 0} />
              </NavLink>
            ))}

            {/* Advanced section */}
            <Separator className="my-2" />
            <Collapsible open={advancedOpen || isOnAdvancedPage} onOpenChange={setAdvancedOpen}>
              <CollapsibleTrigger className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors w-full cursor-pointer">
                <ChevronDown className={cn(
                  'h-3.5 w-3.5 shrink-0 transition-transform duration-200',
                  !(advancedOpen || isOnAdvancedPage) && '-rotate-90',
                )} />
                <span className="truncate text-xs uppercase tracking-wider">Advanced</span>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="flex flex-col gap-0.5 mt-0.5">
                  {advancedNavItems.map(item => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ml-2',
                          isActive
                            ? 'bg-accent text-accent-foreground'
                            : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                        )
                      }
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </NavLink>
                  ))}
                  <button
                    onClick={() => setSettingsOpen(true)}
                    className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors cursor-pointer ml-2"
                  >
                    <Settings className="h-4 w-4 shrink-0" />
                    <span className="truncate">Settings</span>
                  </button>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </nav>
        </ScrollArea>

        {/* Version footer */}
        {healthData?.version && (
          <button
            onClick={() => setChangelogOpen(true)}
            className="px-4 py-2 text-[10px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer border-t border-border"
          >
            v{healthData.version}
          </button>
        )}
      </aside>

      <ChangelogDialog open={changelogOpen} onOpenChange={setChangelogOpen} version={healthData?.version} />

      {/* Center Content Canvas */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-2 border-b border-border px-3 py-2 shrink-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 cursor-pointer"
                onClick={() => setNavOpen(v => !v)}
              >
                {navOpen ? (
                  <PanelLeftClose className="h-4 w-4" />
                ) : (
                  <PanelLeftOpen className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {navOpen ? 'Hide sidebar' : 'Show sidebar'}
            </TooltipContent>
          </Tooltip>

          {/* Breadcrumbs */}
          {projectId && (
            <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm">
              <Link
                to={`/${projectId}`}
                className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[200px]"
              >
                {displayName}
              </Link>
              {breadcrumbs.map((crumb, i) => (
                <span key={i} className="flex items-center gap-1.5">
                  <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                  {crumb.path ? (
                    <Link
                      to={crumb.path}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="text-foreground font-medium truncate max-w-[300px]">{crumb.label}</span>
                  )}
                </span>
              ))}
            </nav>
          )}

          <div className="flex-1" />

          {/* Cmd+K hint */}
          <button
            aria-label="Open command palette"
            className="hidden sm:flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
          >
            <kbd className="pointer-events-none font-mono text-[10px]">⌘K</kbd>
          </button>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 cursor-pointer"
                onClick={() => panel.toggle()}
              >
                {panel.state.open ? (
                  <PanelRightClose className="h-4 w-4" />
                ) : (
                  <PanelRightOpen className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {panel.state.open ? 'Hide panel' : 'Show panel'}
            </TooltipContent>
          </Tooltip>
        </header>

        {/* Content + optional Right Panel */}
        <div className="flex flex-1 min-h-0">
          {/* Page content */}
          <ScrollArea className="flex-1 min-w-0">
            <div className="p-6 flex flex-col min-h-full">
              <Outlet />
            </div>
          </ScrollArea>

          {/* Right Panel — Chat + Inspector tabs */}
          {panel.state.open && (
            <aside role="complementary" aria-label="Chat and inspector panel" style={{ width: panelWidth }} className="border-l border-border bg-card shrink-0 flex flex-col min-h-0 relative">
              {/* Drag handle */}
              <div
                onMouseDown={handleDragStart}
                className="absolute -left-1 top-0 bottom-0 w-2 cursor-col-resize hover:bg-primary/40 active:bg-primary/60 transition-colors z-10 flex items-center justify-center group"
              >
                <div className="h-8 w-1 rounded-full bg-border group-hover:bg-primary/50 transition-colors" />
              </div>
              {/* Tab bar */}
              <div className="flex items-center border-b border-border shrink-0">
                <button
                  onClick={() => panel.setTab('chat')}
                  className={cn(
                    'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer',
                    panel.state.activeTab === 'chat'
                      ? 'text-foreground border-b-2 border-primary'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  Chat
                </button>
                <button
                  onClick={() => panel.setTab('inspector')}
                  className={cn(
                    'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer',
                    panel.state.activeTab === 'inspector'
                      ? 'text-foreground border-b-2 border-primary'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  <Info className="h-3.5 w-3.5" />
                  Inspector
                </button>
                <div className="flex-1" />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 mr-2 cursor-pointer"
                      onClick={() => panel.close()}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="left">Close panel</TooltipContent>
                </Tooltip>
              </div>

              {/* Tab content */}
              {panel.state.activeTab === 'chat' ? (
                <ChatPanel />
              ) : (
                <ScrollArea className="flex-1">
                  <div className="p-4">
                    {inspector.state.content ?? (
                      <p className="text-xs text-muted-foreground">
                        Select an item to inspect its details.
                      </p>
                    )}
                  </div>
                </ScrollArea>
              )}
            </aside>
          )}
        </div>
      </main>
    </div>
  )
}

export default function AppShell() {
  return (
    <RightPanelProvider>
      <ShellInner />
    </RightPanelProvider>
  )
}
