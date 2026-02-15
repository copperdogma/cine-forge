import { useParams, useNavigate } from 'react-router-dom'
import {
  Play,
  Package,
  Inbox,
  History,
  Film,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Calendar,
  ExternalLink,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { SceneStrip } from '@/components/SceneStrip'
import { useProject, useRuns, useArtifactGroups, useScenes } from '@/lib/hooks'
import { cn } from '@/lib/utils'

function getStatusConfig(status: string) {
  switch (status) {
    case 'done':
    case 'skipped_reused':
      return {
        icon: CheckCircle2,
        label: status === 'done' ? 'Done' : 'Reused',
        variant: 'default' as const,
        className: 'bg-green-500/20 text-green-400 border-green-500/30',
      }
    case 'failed':
      return {
        icon: AlertTriangle,
        label: 'Failed',
        variant: 'destructive' as const,
        className: 'bg-red-500/20 text-red-400 border-red-500/30',
      }
    case 'running':
      return {
        icon: Clock,
        label: 'Running',
        variant: 'secondary' as const,
        className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      }
    case 'paused':
      return {
        icon: Clock,
        label: 'Paused',
        variant: 'outline' as const,
        className: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      }
    default:
      return {
        icon: Clock,
        label: 'Pending',
        variant: 'outline' as const,
        className: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
      }
  }
}

function timeAgo(timestamp: number): string {
  const seconds = Math.floor(Date.now() / 1000 - timestamp)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

export default function ProjectHome() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: runs, isLoading: runsLoading } = useRuns(projectId)
  const { data: artifactGroups, isLoading: artifactGroupsLoading } = useArtifactGroups(projectId)
  const { data: scenes, isLoading: scenesLoading } = useScenes(projectId)

  const isLoading = projectLoading || runsLoading || artifactGroupsLoading

  // Derive stats from real data
  const totalRuns = runs?.length ?? 0
  const completedRuns = runs?.filter((r) => r.status === 'done').length ?? 0
  const failedRuns = runs?.filter((r) => r.status === 'failed').length ?? 0
  const totalArtifacts = artifactGroups?.length ?? 0
  const staleArtifacts = artifactGroups?.filter((g) => g.health === 'stale').length ?? 0
  const pendingReviews = staleArtifacts // Approximate with stale artifacts for now
  const pipelineStatus = failedRuns > 0 || staleArtifacts > 0 ? 'degraded' : 'healthy'

  // Sort runs by started_at (most recent first) and take first 5
  const recentRuns = runs
    ? [...runs]
        .sort((a, b) => (b.started_at ?? 0) - (a.started_at ?? 0))
        .slice(0, 5)
    : []

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Film className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">{projectId}</h1>
          </div>
          <p className="text-sm text-muted-foreground">Loading project data...</p>
        </div>
        <Separator />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Project Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <Film className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">
            {project?.display_name ?? projectId}
          </h1>
        </div>
        <p className="text-sm text-muted-foreground">
          ~/Documents/Projects/cine-forge/projects/{projectId}
        </p>
      </div>

      <Separator />

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <History className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRuns}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-green-400">{completedRuns} completed</span>
              {failedRuns > 0 && (
                <>
                  {' · '}
                  <span className="text-red-400">{failedRuns} failed</span>
                </>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Artifacts</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalArtifacts}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {staleArtifacts > 0 ? (
                <>
                  <span className="text-amber-400">{staleArtifacts} stale</span>
                  {' · '}
                  <span className="text-green-400">
                    {totalArtifacts - staleArtifacts} healthy
                  </span>
                </>
              ) : (
                <span className="text-green-400">All healthy</span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Reviews</CardTitle>
            <Inbox className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingReviews}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {pendingReviews > 0 ? 'Requires attention' : 'Inbox clear'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pipeline Status</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {pipelineStatus === 'healthy' ? (
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              )}
              <span className="text-2xl font-bold capitalize">{pipelineStatus}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">All systems operational</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Last 5 pipeline runs</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('runs')}
              className="gap-2"
            >
              View All
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentRuns.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No runs yet. Start your first pipeline run to begin.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentRuns.map((run) => {
                const statusConfig = getStatusConfig(run.status)
                const StatusIcon = statusConfig.icon
                const duration =
                  run.finished_at && run.started_at
                    ? formatDuration(run.finished_at - run.started_at)
                    : null
                return (
                  <div
                    key={run.run_id}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer"
                    onClick={() => navigate(`runs/${run.run_id}`)}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <StatusIcon className={cn('h-4 w-4 shrink-0', statusConfig.className)} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm truncate">{run.run_id}</span>
                          <Badge
                            variant="outline"
                            className={cn('text-xs px-1.5 py-0', statusConfig.className)}
                          >
                            {statusConfig.label}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground shrink-0">
                      {run.started_at && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {timeAgo(run.started_at)}
                        </div>
                      )}
                      {duration && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {duration}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common operations for this project</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => navigate('run')} className="gap-2">
              <Play className="h-4 w-4" />
              Start New Run
            </Button>
            <Button variant="outline" onClick={() => navigate('artifacts')} className="gap-2">
              <Package className="h-4 w-4" />
              View Artifacts
            </Button>
            <Button variant="outline" onClick={() => navigate('inbox')} className="gap-2">
              <Inbox className="h-4 w-4" />
              Check Inbox
              {pendingReviews > 0 && (
                <Badge variant="secondary" className="ml-1 px-1.5 py-0">
                  {pendingReviews}
                </Badge>
              )}
            </Button>
            <Button variant="outline" onClick={() => navigate('runs')} className="gap-2">
              <History className="h-4 w-4" />
              Run History
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Scene Overview (if screenplay data exists) */}
      {scenes && scenes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Scene Overview</CardTitle>
            <CardDescription>
              {scenes.length} scene{scenes.length !== 1 ? 's' : ''} detected in latest screenplay
            </CardDescription>
          </CardHeader>
          <CardContent className="px-0">
            {scenesLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">Loading scenes...</p>
              </div>
            ) : (
              <SceneStrip scenes={scenes} />
            )}
          </CardContent>
        </Card>
      )}

      {/* Artifact Health Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Artifact Health</CardTitle>
            <CardDescription>Current state of all project artifacts</CardDescription>
          </CardHeader>
          <CardContent>
            {totalArtifacts === 0 ? (
              <div className="text-center py-4 text-muted-foreground">
                <p className="text-xs">No artifacts yet. Run a pipeline to generate artifacts.</p>
              </div>
            ) : (
              <div className="space-y-3">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center justify-between cursor-help">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-400" />
                          <span className="text-sm">Healthy</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono text-muted-foreground">
                            {totalArtifacts - staleArtifacts}
                          </span>
                          <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500"
                              style={{
                                width: `${((totalArtifacts - staleArtifacts) / totalArtifacts) * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>These artifacts are up to date and have passed all quality checks.</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                {staleArtifacts > 0 && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center justify-between cursor-help">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-amber-400" />
                            <span className="text-sm">Stale</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-muted-foreground">
                              {staleArtifacts}
                            </span>
                            <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-amber-500"
                                style={{ width: `${(staleArtifacts / totalArtifacts) * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Upstream artifacts have changed. These artifacts need to be regenerated.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline Cost</CardTitle>
            <CardDescription>Aggregate cost tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4 text-muted-foreground">
              <p className="text-xs">
                Cost data available in individual run details.
                <br />
                Aggregate tracking coming soon.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
