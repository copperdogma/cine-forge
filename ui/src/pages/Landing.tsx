import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Film, Plus, FolderOpen, Clock, Package, Play, AlertCircle, RefreshCw, ChevronDown } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { fetchHealth, fetchChangelog } from '@/lib/api'
import { useRecentProjects, useOpenProject } from '@/lib/hooks'

const INITIAL_SHOW = 5

function timeAgo(epochSeconds: number): string {
  const seconds = Math.floor(Date.now() / 1000 - epochSeconds)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks}w ago`
  const months = Math.floor(days / 30)
  return `${months}mo ago`
}

export default function Landing() {
  const navigate = useNavigate()
  const { data: projects, isLoading, error, refetch } = useRecentProjects()
  const openProject = useOpenProject()
  const [showOpenDialog, setShowOpenDialog] = useState(false)
  const [projectPath, setProjectPath] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [changelogOpen, setChangelogOpen] = useState(false)
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 5 * 60 * 1000,
  })
  const { data: changelogContent } = useQuery({
    queryKey: ['changelog'],
    queryFn: fetchChangelog,
    enabled: changelogOpen,
  })

  const handleOpenExisting = () => {
    setShowOpenDialog(true)
  }

  const handleOpenSubmit = async () => {
    if (!projectPath.trim()) {
      toast.error('Please enter a project path')
      return
    }

    try {
      const project = await openProject.mutateAsync(projectPath.trim())
      toast.success('Project opened successfully')
      setShowOpenDialog(false)
      setProjectPath('')
      navigate(`/${project.project_id}`)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to open project'
      toast.error(message)
    }
  }

  const totalCount = projects?.length ?? 0
  const visibleProjects = showAll ? projects : projects?.slice(0, INITIAL_SHOW)
  const hiddenCount = totalCount - (visibleProjects?.length ?? 0)

  return (
    <div className="flex min-h-screen items-start justify-center p-8 pt-[12vh]">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Film className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">CineForge</h1>
          </div>
          <p className="text-muted-foreground">
            Film reasoning and production pipeline
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-center gap-3">
          <Button onClick={() => navigate('/new')}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
          <Button variant="outline" onClick={handleOpenExisting}>
            <FolderOpen className="h-4 w-4 mr-2" />
            Open Project
          </Button>
        </div>

        {/* Recent projects */}
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Clock className="h-3.5 w-3.5" />
            Recent Projects
          </h2>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <Card key={i}>
                  <CardContent className="flex items-center gap-4 py-3 px-4">
                    <Skeleton className="h-5 w-5 shrink-0" />
                    <div className="min-w-0 flex-1 space-y-2">
                      <Skeleton className="h-4 w-40" />
                      <Skeleton className="h-3 w-64" />
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <Skeleton className="h-6 w-12" />
                      <Skeleton className="h-6 w-12" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <Card className="border-destructive/50">
              <CardContent className="flex items-start gap-4 py-4 px-4">
                <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                <div className="flex-1 space-y-2">
                  <p className="text-sm font-medium text-destructive">
                    Failed to load recent projects
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(error as { hint?: string })?.hint
                      ?? (error instanceof Error ? error.message : 'The backend server may not be running.')}
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => refetch()}
                    className="mt-2"
                  >
                    <RefreshCw className="h-3.5 w-3.5 mr-2" />
                    Retry
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Empty State */}
          {!isLoading && !error && projects && projects.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <Film className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <p className="text-sm font-medium mb-1">No projects yet</p>
                <p className="text-xs text-muted-foreground mb-4">
                  Create your first project to start building your film pipeline
                </p>
                <Button size="sm" onClick={() => navigate('/new')}>
                  <Plus className="h-3.5 w-3.5 mr-2" />
                  Create Project
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Success State — Project List */}
          {!isLoading && !error && visibleProjects && visibleProjects.length > 0 && (
            <div className="space-y-2">
              {visibleProjects.map(project => (
                <Card
                  key={project.project_id}
                  className="cursor-pointer transition-colors hover:bg-accent/50"
                  onClick={() => navigate(`/${project.project_id}`)}
                >
                  <CardContent className="flex items-center gap-4 py-3 px-4">
                    <Film className="h-5 w-5 text-primary shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm truncate">
                        {project.display_name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {project.project_path}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {project.last_modified != null && (
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {timeAgo(project.last_modified)}
                        </span>
                      )}
                      <Badge variant="secondary" className="text-xs gap-1">
                        <Package className="h-3 w-3" />
                        {project.artifact_groups}
                      </Badge>
                      <Badge variant="secondary" className="text-xs gap-1">
                        <Play className="h-3 w-3" />
                        {project.run_count}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Show more / Show less */}
              {totalCount > INITIAL_SHOW && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-muted-foreground"
                  onClick={() => setShowAll(prev => !prev)}
                >
                  <ChevronDown className={`h-4 w-4 mr-2 transition-transform ${showAll ? 'rotate-180' : ''}`} />
                  {showAll
                    ? 'Show less'
                    : `Show ${hiddenCount} more project${hiddenCount === 1 ? '' : 's'}`}
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Version — fixed bottom-left */}
      {healthData?.version && (
        <button
          onClick={() => setChangelogOpen(true)}
          className="fixed bottom-3 left-4 text-[10px] text-muted-foreground/60 hover:text-muted-foreground transition-colors cursor-pointer"
        >
          v{healthData.version}
        </button>
      )}

      {/* Changelog Dialog */}
      <Dialog open={changelogOpen} onOpenChange={setChangelogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Changelog {healthData?.version && `— v${healthData.version}`}</DialogTitle>
          </DialogHeader>
          <div className="prose prose-sm prose-invert max-w-none">
            <ReactMarkdown>{changelogContent ?? 'Loading...'}</ReactMarkdown>
          </div>
        </DialogContent>
      </Dialog>

      {/* Open Project Dialog */}
      <Dialog open={showOpenDialog} onOpenChange={setShowOpenDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Open Project</DialogTitle>
            <DialogDescription>
              Enter the path to an existing CineForge project directory
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-4">
            <Input
              placeholder="/path/to/project"
              value={projectPath}
              onChange={(e) => setProjectPath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && projectPath.trim()) {
                  handleOpenSubmit()
                }
              }}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              The directory should contain an artifacts/ folder
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowOpenDialog(false)
                setProjectPath('')
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleOpenSubmit}
              disabled={!projectPath.trim() || openProject.isPending}
            >
              {openProject.isPending ? 'Opening...' : 'Open Project'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
