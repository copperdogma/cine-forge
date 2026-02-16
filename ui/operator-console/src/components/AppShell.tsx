import { NavLink, Outlet, useNavigate, useParams, useLocation, Link } from 'react-router-dom'
import {
  Film,
  Play,
  History,
  Package,
  Inbox,
  Home,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  ChevronDown,
  ChevronRight,
  Settings,
  X,
  MessageSquare,
  Info,
} from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { RightPanelProvider, useRightPanel, useInspector } from '@/lib/right-panel'
import { CommandPalette } from '@/components/CommandPalette'
import { GlobalSearch } from '@/components/GlobalSearch'
import { ProjectSettings } from '@/components/ProjectSettings'
import { ChatPanel } from '@/components/ChatPanel'
import { useShortcuts } from '@/lib/shortcuts'
import { useProject } from '@/lib/hooks'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '', label: 'Home', icon: Home, end: true },
  { to: 'run', label: 'Pipeline', icon: Play },
  { to: 'runs', label: 'Runs', icon: History },
  { to: 'artifacts', label: 'Artifacts', icon: Package },
  { to: 'inbox', label: 'Inbox', icon: Inbox, badge: 0 },
]

function ShellInner() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [navOpen, setNavOpen] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const panel = useRightPanel()
  const inspector = useInspector()
  const { data: project } = useProject(projectId)

  const displayName = project?.display_name ?? projectId?.slice(0, 12) ?? 'Project'

  // Keyboard shortcuts
  useShortcuts([
    { key: 'b', meta: true, action: () => setNavOpen(v => !v), label: 'Toggle sidebar' },
    { key: 'i', meta: true, action: () => panel.toggle(), label: 'Toggle right panel' },
    { key: '0', meta: true, action: () => navigate(''), label: 'Go to Home' },
    { key: '1', meta: true, action: () => navigate('run'), label: 'Go to Pipeline' },
    { key: '2', meta: true, action: () => navigate('runs'), label: 'Go to Runs' },
    { key: '3', meta: true, action: () => navigate('artifacts'), label: 'Go to Artifacts' },
    { key: '4', meta: true, action: () => navigate('inbox'), label: 'Go to Inbox' },
    { key: ',', meta: true, action: () => setSettingsOpen(true), label: 'Open settings' },
    { key: 'Escape', action: () => { if (panel.state.open) panel.close() }, label: 'Close right panel' },
  ])

  // Determine current page from pathname (check longer paths first)
  const getCurrentPage = () => {
    const path = location.pathname
    if (path.includes('/runs')) return 'Runs'
    if (path.includes('/run')) return 'Pipeline'
    if (path.includes('/artifacts')) return 'Artifacts'
    if (path.includes('/inbox')) return 'Inbox'
    if (path === `/${projectId}`) return 'Home'
    return null
  }

  const currentPage = getCurrentPage()

  return (
    <div className="flex h-screen overflow-hidden">
      <CommandPalette
        onToggleSidebar={() => setNavOpen(v => !v)}
        onToggleInspector={() => panel.toggle()}
      />
      <GlobalSearch />
      {/* Keyboard-triggered settings dialog */}
      <ProjectSettings
        projectId={projectId ?? ''}
        projectName={displayName}
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
      {/* Left Navigator Panel */}
      <aside
        className={cn(
          'flex flex-col border-r border-border bg-sidebar transition-all duration-200',
          navOpen ? 'w-56' : 'w-0 overflow-hidden',
        )}
      >
        {/* Project header */}
        <div className="flex items-center gap-2 px-4 py-3">
          <Film className="h-5 w-5 text-primary shrink-0" />
          <div className="min-w-0 flex-1">
            <ProjectSettings
              projectId={projectId ?? ''}
              projectName={displayName}
            >
              <button
                aria-label={`Project ${displayName} settings`}
                className="flex items-center gap-1 text-sm font-semibold truncate hover:text-primary transition-colors cursor-pointer"
              >
                <span className="truncate">{displayName}</span>
                <ChevronDown className="h-3.5 w-3.5 shrink-0 opacity-60" />
              </button>
            </ProjectSettings>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <ProjectSettings
                projectId={projectId ?? ''}
                projectName={displayName}
              >
                <button
                  aria-label="Open project settings"
                  className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                >
                  <Settings className="h-3.5 w-3.5" />
                </button>
              </ProjectSettings>
            </TooltipTrigger>
            <TooltipContent side="right">Project settings</TooltipContent>
          </Tooltip>
        </div>

        <Separator />

        {/* Navigation */}
        <ScrollArea className="flex-1 py-2">
          <nav aria-label="Project navigation" className="flex flex-col gap-0.5 px-2">
            {navItems.map(item => (
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
                {item.badge != null && item.badge > 0 && (
                  <Badge variant="secondary" className="ml-auto text-xs px-1.5 py-0">
                    {item.badge}
                  </Badge>
                )}
              </NavLink>
            ))}
          </nav>
        </ScrollArea>

        {/* Footer — home link */}
        <Separator />
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              aria-label="Go to all projects"
              className="flex items-center gap-2 px-4 py-3 text-xs text-muted-foreground hover:text-primary transition-colors text-left cursor-pointer w-full"
              onClick={() => navigate('/')}
            >
              <Film className="h-3.5 w-3.5 shrink-0" />
              CineForge
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">All projects</TooltipContent>
        </Tooltip>
      </aside>

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
              {currentPage && (
                <>
                  <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                  <span className="text-foreground font-medium">{currentPage}</span>
                </>
              )}
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
          <ScrollArea className="flex-1">
            <div className="p-6">
              <Outlet />
            </div>
          </ScrollArea>

          {/* Right Panel — Chat + Inspector tabs */}
          {panel.state.open && (
            <aside role="complementary" aria-label="Chat and inspector panel" className="w-80 border-l border-border bg-card shrink-0 flex flex-col min-h-0">
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
