import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'
import AppShell from '@/components/AppShell'
import Landing from '@/pages/Landing'
import NewProject from '@/pages/NewProject'
import ProjectHome from '@/pages/ProjectHome'
import ProjectRun from '@/pages/ProjectRun'
import ProjectRuns from '@/pages/ProjectRuns'
import RunDetail from '@/pages/RunDetail'
import ProjectArtifacts from '@/pages/ProjectArtifacts'
import ArtifactDetail from '@/pages/ArtifactDetail'
import ProjectInbox from '@/pages/ProjectInbox'
import ThemeShowcase from '@/pages/ThemeShowcase'
import { KeyboardShortcutsHelp } from '@/components/KeyboardShortcutsHelp'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5_000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <div className="dark min-h-screen bg-background text-foreground">
            <Routes>
              {/* Full-screen routes (no shell) */}
              <Route path="/" element={<Landing />} />
              <Route path="/new" element={<NewProject />} />
              <Route path="/theme" element={<ThemeShowcase />} />

              {/* Project-scoped routes (wrapped in AppShell) */}
              <Route path="/:projectId" element={<AppShell />}>
                <Route index element={<ProjectHome />} />
                <Route path="run" element={<ProjectRun />} />
                <Route path="run/:runId" element={<ProjectRun />} />
                <Route path="runs" element={<ProjectRuns />} />
                <Route path="runs/:runId" element={<RunDetail />} />
                <Route path="artifacts" element={<ProjectArtifacts />} />
                <Route path="artifacts/:artifactType/:entityId/:version" element={<ArtifactDetail />} />
                <Route path="inbox" element={<ProjectInbox />} />
              </Route>
            </Routes>
          </div>
          <Toaster richColors position="bottom-right" />
          <KeyboardShortcutsHelp />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  )
}
