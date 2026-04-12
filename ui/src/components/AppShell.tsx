import { NavLink, Outlet, useNavigate, useParams, useLocation, Link } from 'react-router-dom'
import {
  Activity,
  Film,
  History,
  Package,
  Inbox,
  FileText,
  Compass,
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
  Menu,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { RightPanelProvider } from '@/lib/right-panel'
import { useRightPanel } from '@/lib/use-right-panel'
import { CommandPalette } from '@/components/CommandPalette'
import { ProjectSettings } from '@/components/ProjectSettings'
import { ChatPanel } from '@/components/ChatPanel'
import { PipelineBar } from '@/components/PipelineBar'
import { OperationBanner } from '@/components/OperationBanner'
import { ChangelogDialog } from '@/components/ChangelogDialog'
import { useShortcuts } from '@/lib/shortcuts'
import { fetchHealth } from '@/lib/api'
import { useProject, useChatLoader, useArtifactGroups, useRuns, usePipelineGraph } from '@/lib/hooks'
import { useChatStore } from '@/lib/chat-store'
import { useRunProgressChat } from '@/lib/use-run-progress'
import { dropResolvedGenericRunFailureMessages } from '@/lib/run-failure-messages'
import { cn } from '@/lib/utils'
import {
  artifactAttentionItemId,
  errorItemId,
  gateItemId,
  reviewItemId,
  parseReadIds,
  READ_INBOX_KEY,
} from '@/lib/inbox-utils'
import { actionableHealthGroups, gateReviewGroups, reviewableBibleGroups } from '@/lib/health'
import { useIsMobile } from '@/lib/use-mobile'

/** Artifact type → nav route mapping for count badges. */
const NAV_ARTIFACT_TYPES: Record<string, string[]> = {
  scenes: ['scene'],
  characters: ['character_bible'],
  locations: ['location_bible'],
  props: ['prop_bible'],
}

const mainNavBase = [
  { to: '', label: 'Script', icon: FileText, end: true },
  { to: 'intent', label: 'Intent', icon: Compass },
  { to: 'scenes', label: 'Scenes', icon: Clapperboard },
  { to: 'characters', label: 'Characters', icon: Users },
  { to: 'locations', label: 'Locations', icon: MapPin },
  { to: 'props', label: 'Props', icon: Wrench },
  { to: 'inbox', label: 'Inbox', icon: Inbox },
]

/** Animated badge that pops when count increases — teal flash fading over 1.5s.
 *  Uses pulseCount as key to force Badge remount on each increment so the
 *  animation restarts cleanly even on rapid successive count increases. */
function CountBadge({ count }: { count: number }) {
  const prevRef = useRef(count)
  const [pulseCount, setPulseCount] = useState(0)

  useEffect(() => {
    if (count > prevRef.current) {
      // rAF keeps this async (avoids React 19 sync setState-in-effect warning)
      const raf = requestAnimationFrame(() => setPulseCount(n => n + 1))
      return () => cancelAnimationFrame(raf)
    }
    prevRef.current = count
  }, [count])

  // Keep ref current on every change (handles decreases, no animation needed)
  useEffect(() => { prevRef.current = count }, [count])

  if (count === 0) return null

  return (
    <Badge
      key={pulseCount}
      variant="secondary"
      className={cn(
        'ml-auto text-xs px-1.5 py-0 tabular-nums',
        pulseCount > 0 && '[animation:badge-pop_1.5s_ease-out_forwards]',
      )}
    >
      {count}
    </Badge>
  )
}

/** Nav row with whole-row glow when count increases — soft teal fade over 3s.
 *  Uses an absolutely-positioned span with key={glowKey} to restart the animation
 *  on every increment without remounting the NavLink itself. */
function NavItem({
  item,
  count,
  onSelect,
}: {
  item: (typeof mainNavBase)[number]
  count: number
  onSelect?: () => void
}) {
  const prevRef = useRef(count)
  const [glowKey, setGlowKey] = useState(0)

  useEffect(() => {
    if (count > prevRef.current) {
      const raf = requestAnimationFrame(() => setGlowKey(n => n + 1))
      return () => cancelAnimationFrame(raf)
    }
    prevRef.current = count
  }, [count])

  // Keep ref current on every change (handles decreases, no animation needed)
  useEffect(() => { prevRef.current = count }, [count])

  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onSelect}
      className={({ isActive }) =>
        cn(
          'relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors overflow-hidden',
          isActive
            ? 'bg-accent text-accent-foreground'
            : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
        )
      }
    >
      {glowKey > 0 && (
        <span
          key={glowKey}
          aria-hidden
          className="absolute inset-0 [animation:nav-row-glow_3s_ease-out_forwards] pointer-events-none"
        />
      )}
      <item.icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{item.label}</span>
      <CountBadge count={count} />
    </NavLink>
  )
}

const advancedNavItems = [
  { to: 'runs', label: 'Runs', icon: History },
  { to: 'artifacts', label: 'Artifacts', icon: Package },
]

const worldNavItems = [
  { to: 'world/continuity', label: 'Continuity', icon: Activity },
]

type SidebarContentProps = {
  navCounts: Record<string, number>
  worldOpen: boolean
  advancedOpen: boolean
  isOnWorldPage: boolean
  isOnAdvancedPage: boolean
  onWorldOpenChange: (open: boolean) => void
  onAdvancedOpenChange: (open: boolean) => void
  onOpenSettings: () => void
  onNavigate?: () => void
  onOpenChangelog: () => void
  version?: string
}

function SidebarContent({
  navCounts,
  worldOpen,
  advancedOpen,
  isOnWorldPage,
  isOnAdvancedPage,
  onWorldOpenChange,
  onAdvancedOpenChange,
  onOpenSettings,
  onNavigate,
  onOpenChangelog,
  version,
}: SidebarContentProps) {
  return (
    <>
      <Link
        to="/"
        onClick={onNavigate}
        className="flex items-center gap-2 px-4 py-3 hover:bg-accent/50 transition-colors"
      >
        <Film className="h-5 w-5 text-primary shrink-0" />
        <span className="text-sm font-semibold">CineForge</span>
      </Link>

      <Separator />

      <ScrollArea className="flex-1 py-2">
        <nav aria-label="Project navigation" className="flex flex-col gap-0.5 px-2">
          {mainNavBase.map(item => (
            <NavItem
              key={item.to}
              item={item}
              count={navCounts[item.to] ?? 0}
              onSelect={onNavigate}
            />
          ))}

          <Separator className="my-2" />
          <Collapsible open={worldOpen || isOnWorldPage} onOpenChange={onWorldOpenChange}>
            <CollapsibleTrigger className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors w-full cursor-pointer">
              <ChevronDown className={cn(
                'h-3.5 w-3.5 shrink-0 transition-transform duration-200',
                !(worldOpen || isOnWorldPage) && '-rotate-90',
              )} />
              <span className="truncate text-xs uppercase tracking-wider">World</span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="flex flex-col gap-0.5 mt-0.5">
                {worldNavItems.map(item => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onNavigate}
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
              </div>
            </CollapsibleContent>
          </Collapsible>

          <Separator className="my-2" />
          <Collapsible open={advancedOpen || isOnAdvancedPage} onOpenChange={onAdvancedOpenChange}>
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
                    onClick={onNavigate}
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
                  onClick={onOpenSettings}
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

      {version && (
        <button
          onClick={onOpenChangelog}
          className="px-4 py-2 text-[10px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer border-t border-border"
        >
          v{version}
        </button>
      )}
    </>
  )
}

function RightPanelContent({ onClose }: { onClose: () => void }) {
  return (
    <>
      <div className="flex items-center border-b border-border shrink-0 px-4 py-2.5">
        <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
          <MessageSquare className="h-3.5 w-3.5" />
          Chat
        </div>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="icon"
          className="h-11 w-11 cursor-pointer md:h-6 md:w-6"
          onClick={onClose}
          aria-label="Close chat"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <ChatPanel />
    </>
  )
}

function ShellInner({ isMobile }: { isMobile: boolean }) {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [desktopNavOpen, setDesktopNavOpen] = useState(true)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [worldOpen, setWorldOpen] = useState(false)
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
  // Poll at 1.5s during an active run so entity counts tick up as bibles complete (story-072).
  const activeRunId = useChatStore(s => projectId ? s.activeRunId?.[projectId] ?? null : null)
  const projectMessages = useChatStore(
    (s) => (projectId ? s.messages[projectId] : undefined),
  )
  const { data: artifactGroups } = useArtifactGroups(projectId, activeRunId ? 750 : undefined)
  const { data: runs } = useRuns(projectId)

  // Restore activeRunId on page refresh: if there's a running run but no activeRunId,
  // set it so the banner and progress tracking resume.
  useEffect(() => {
    if (!projectId || !runs || activeRunId) return
    const runningRun = runs.find(r => r.status === 'running')
    if (runningRun) {
      useChatStore.getState().setActiveRun(projectId, runningRun.run_id)
    }
  }, [projectId, runs, activeRunId])

  useEffect(() => {
    const currentProjectMessages = projectMessages ?? []
    if (!projectId || !runs || currentProjectMessages.length === 0) return
    const resolvedRunIds = new Set(
      runs
        .filter((run) => run.status === 'done')
        .map((run) => run.run_id),
    )
    if (resolvedRunIds.size === 0) return
    const filtered = dropResolvedGenericRunFailureMessages(currentProjectMessages, resolvedRunIds)
    if (filtered.length !== currentProjectMessages.length) {
      useChatStore.getState().loadMessages(projectId, filtered)
    }
  }, [projectId, projectMessages, runs])

  const { data: pipelineGraph } = usePipelineGraph(projectId, activeRunId)
  const defaultSceneId = useMemo(() => {
    const sceneIds = (artifactGroups ?? [])
      .filter((group) => group.artifact_type === 'scene')
      .map((group) => group.entity_id)
      .filter((entityId): entityId is string => typeof entityId === 'string' && entityId.startsWith('scene_'))
      .sort()
    return sceneIds[0] ?? null
  }, [artifactGroups])

  const navCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    if (artifactGroups) {
      for (const [route, types] of Object.entries(NAV_ARTIFACT_TYPES)) {
        counts[route] = artifactGroups.filter(g => types.includes(g.artifact_type)).length
      }
    }
    // Inbox: match ProjectInbox logic — health attention items + failed runs + v1 bibles needing review
    // Badge shows unread count only, using shared ID builders (story 069)
    const readSet = new Set(parseReadIds(project?.ui_preferences?.[READ_INBOX_KEY]))
    const attentionCount = actionableHealthGroups(artifactGroups).filter(g =>
      !readSet.has(artifactAttentionItemId(g.health, g.artifact_type, g.entity_id))
    ).length ?? 0
    const errorCount = runs?.filter(r =>
      r.status === 'failed' && !readSet.has(errorItemId(r.run_id))
    ).length ?? 0
    const reviewCount = reviewableBibleGroups(artifactGroups).filter(g =>
      !readSet.has(reviewItemId(g.artifact_type, g.entity_id, g.latest_version))
    ).length ?? 0
    const gateReviewCount = gateReviewGroups(artifactGroups).filter(g =>
      !readSet.has(gateItemId(g.entity_id))
    ).length ?? 0
    counts['inbox'] = attentionCount + errorCount + reviewCount + gateReviewCount
    return counts
  }, [artifactGroups, runs, project?.ui_preferences])

  // Scroll main content to top on every route change
  const mainScrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    mainScrollRef.current
      ?.querySelector<HTMLElement>('[data-radix-scroll-area-viewport]')
      ?.scrollTo({ top: 0 })
  }, [location.pathname])

  // Emit activity notes on meaningful navigation (artifact detail, run detail).
  // On initial mount (including refresh), prevPath starts empty so the entity
  // context/activity note is always set for the current URL.
  const prevPath = useRef('')
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
        `Viewing: ${label} (${atype})`,
        `artifacts/${atype}/${entityId}/${artifactMatch[3]}`,
      )
      return
    }

    // Entity detail: /:projectId/characters/:entityId (etc.)
    // Sets the context chip above the chat input rather than posting a timeline message.
    const entityDetailMatch = path.match(new RegExp(`^/${projectId}/(characters|locations|props|scenes)/([^/]+)$`))
    if (entityDetailMatch) {
      const [, section, entityId] = entityDetailMatch
      const entityName = entityId.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      useChatStore.getState().setEntityContext(projectId, { name: entityName, section, entityId })
      return
    }

    // Leaving an entity detail page — clear the context chip
    useChatStore.getState().clearEntityContext(projectId)

    // Entity lists
    if (path.endsWith('/scenes')) { useChatStore.getState().addActivity(projectId, 'Viewing Scene Index', 'scenes'); return }
    if (path.endsWith('/characters')) { useChatStore.getState().addActivity(projectId, 'Reviewing Characters', 'characters'); return }
    if (path.endsWith('/locations')) { useChatStore.getState().addActivity(projectId, 'Reviewing Locations', 'locations'); return }
    if (path.endsWith('/props')) { useChatStore.getState().addActivity(projectId, 'Reviewing Props', 'props'); return }
    if (path.endsWith('/runs')) { useChatStore.getState().addActivity(projectId, 'Reviewing Run History', 'runs'); return }

    // Inbox: /:projectId/inbox
    if (path.endsWith('/inbox')) {
      useChatStore.getState().addActivity(
        projectId,
        `Reviewing Inbox`,
        `inbox`,
      )
      return
    }

    // Run detail: /:projectId/run/:runId
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
    { key: 'b', meta: true, action: () => (isMobile ? setMobileNavOpen(v => !v) : setDesktopNavOpen(v => !v)), label: 'Toggle sidebar' },
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

    if (path.includes('/intent')) return [{ label: 'Intent & Mood' }]
    if (path.includes('/world/continuity')) return [{ label: 'World' }, { label: 'Continuity' }]
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
  // Auto-open world section if we're on a world/* page
  const isOnWorldPage = location.pathname.includes('/world')

  return (
    <div className="fixed inset-0 flex overflow-hidden">
      <CommandPalette
        onToggleSidebar={() => (isMobile ? setMobileNavOpen(v => !v) : setDesktopNavOpen(v => !v))}
      />
      {/* Keyboard-triggered settings dialog */}
      <ProjectSettings
        projectId={projectId ?? ''}
        project={project}
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
      {!isMobile && (
        <aside
          className={cn(
            'flex flex-col border-r border-border bg-sidebar transition-all duration-200 overflow-hidden',
            desktopNavOpen ? 'w-56' : 'w-0',
          )}
        >
          <SidebarContent
            navCounts={navCounts}
            worldOpen={worldOpen}
            advancedOpen={advancedOpen}
            isOnWorldPage={isOnWorldPage}
            isOnAdvancedPage={isOnAdvancedPage}
            onWorldOpenChange={setWorldOpen}
            onAdvancedOpenChange={setAdvancedOpen}
            onOpenSettings={() => setSettingsOpen(true)}
            onOpenChangelog={() => setChangelogOpen(true)}
            version={healthData?.version}
          />
        </aside>
      )}

      <Sheet open={isMobile && mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent
          side="left"
          showCloseButton={false}
          className="w-[18rem] max-w-[calc(100vw-1rem)] p-0"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>Project navigation</SheetTitle>
            <SheetDescription>Browse project routes and open advanced operator tools.</SheetDescription>
          </SheetHeader>
          <div className="flex h-full min-h-0 flex-col bg-sidebar">
            <SidebarContent
              navCounts={navCounts}
              worldOpen={worldOpen}
              advancedOpen={advancedOpen}
              isOnWorldPage={isOnWorldPage}
              isOnAdvancedPage={isOnAdvancedPage}
              onWorldOpenChange={setWorldOpen}
              onAdvancedOpenChange={setAdvancedOpen}
              onOpenSettings={() => {
                setMobileNavOpen(false)
                setSettingsOpen(true)
              }}
              onNavigate={() => setMobileNavOpen(false)}
              onOpenChangelog={() => setChangelogOpen(true)}
              version={healthData?.version}
            />
          </div>
        </SheetContent>
      </Sheet>

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
                className="h-11 w-11 cursor-pointer md:h-8 md:w-8"
                onClick={() => (isMobile ? setMobileNavOpen(v => !v) : setDesktopNavOpen(v => !v))}
                aria-label={isMobile ? 'Open navigation' : (desktopNavOpen ? 'Hide sidebar' : 'Show sidebar')}
              >
                {isMobile ? (
                  <Menu className="h-4 w-4" />
                ) : desktopNavOpen ? (
                  <PanelLeftClose className="h-4 w-4" />
                ) : (
                  <PanelLeftOpen className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {isMobile ? 'Open navigation' : (desktopNavOpen ? 'Hide sidebar' : 'Show sidebar')}
            </TooltipContent>
          </Tooltip>

          {/* Breadcrumbs */}
          {projectId && (
            <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-sm overflow-hidden">
              <Link
                to={`/${projectId}`}
                className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[120px] sm:max-w-[200px]"
              >
                {displayName}
              </Link>
              {breadcrumbs.map((crumb, i) => (
                <span key={i} className="flex min-w-0 items-center gap-1.5 overflow-hidden">
                  <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                  {crumb.path ? (
                    <Link
                      to={crumb.path}
                      className="text-muted-foreground hover:text-foreground transition-colors truncate"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="text-foreground font-medium truncate max-w-[140px] sm:max-w-[300px]">{crumb.label}</span>
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
                className="h-11 w-11 cursor-pointer md:h-8 md:w-8"
                onClick={() => panel.toggle()}
                aria-label={isMobile ? (panel.state.open ? 'Close chat' : 'Open chat') : (panel.state.open ? 'Hide panel' : 'Show panel')}
              >
                {isMobile ? (
                  <MessageSquare className="h-4 w-4" />
                ) : panel.state.open ? (
                  <PanelRightClose className="h-4 w-4" />
                ) : (
                  <PanelRightOpen className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {isMobile ? (panel.state.open ? 'Close chat' : 'Open chat') : (panel.state.open ? 'Hide panel' : 'Show panel')}
            </TooltipContent>
          </Tooltip>
        </header>

        {/* Pipeline Bar */}
        {projectId && pipelineGraph && (
          <PipelineBar
            phases={pipelineGraph.phases}
            nodes={pipelineGraph.nodes}
            projectId={projectId}
            defaultSceneId={defaultSceneId}
          />
        )}

        {/* Operation banner — visible from any page when work is running */}
        {projectId && <OperationBanner projectId={projectId} />}

        {/* Content + optional Right Panel */}
        <div className="flex flex-1 min-h-0">
          {/* Page content */}
          <div ref={mainScrollRef} className="flex-1 min-w-0 overflow-hidden">
          <ScrollArea className="h-full w-full">
            <div className="flex min-h-full w-full min-w-0 flex-col p-4 sm:p-6">
              <Outlet />
            </div>
          </ScrollArea>
          </div>

          {/* Right Panel — Chat + Inspector tabs */}
          {!isMobile && panel.state.open && (
            <aside role="complementary" aria-label="Chat panel" style={{ width: panelWidth }} className="border-l border-border bg-card shrink-0 flex flex-col min-h-0 relative">
              {/* Drag handle */}
              <div
                onMouseDown={handleDragStart}
                className="absolute -left-1 top-0 bottom-0 w-2 cursor-col-resize hover:bg-primary/40 active:bg-primary/60 transition-colors z-10 flex items-center justify-center group"
              >
                <div className="h-8 w-1 rounded-full bg-border group-hover:bg-primary/50 transition-colors" />
              </div>
              <RightPanelContent onClose={() => panel.close()} />
            </aside>
          )}
        </div>
      </main>

      <Sheet
        open={isMobile && panel.state.open}
        onOpenChange={(open) => {
          if (open) {
            panel.openChat()
            return
          }
          panel.close()
        }}
      >
        <SheetContent
          side="right"
          showCloseButton={false}
          className="w-full max-w-none p-0"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>Project chat</SheetTitle>
            <SheetDescription>Chat about the current project without leaving the current route.</SheetDescription>
          </SheetHeader>
          <div className="flex h-full min-h-0 flex-col bg-card">
            <RightPanelContent onClose={() => panel.close()} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}

export default function AppShell() {
  const isMobile = useIsMobile()

  return (
    <RightPanelProvider initialOpen={!isMobile}>
      <ShellInner isMobile={isMobile} />
    </RightPanelProvider>
  )
}
