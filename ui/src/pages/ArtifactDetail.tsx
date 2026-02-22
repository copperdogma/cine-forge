import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  ArrowLeft,
  Clock,
  GitBranch,
  Package,
  Code,
  Edit,
  Save,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  ScriptViewer,
  StructuredDataViewer,
  ProfileViewer,
  SceneViewer,
  BibleViewer,
  EntityGraphViewer,
  StageReviewViewer,
  DefaultViewer,
} from '@/components/ArtifactViewers'
import { ProvenanceBadge } from '@/components/ProvenanceBadge'
import { HealthBadge } from '@/components/HealthBadge'
import { getArtifactMeta } from '@/lib/artifact-meta'
import { useArtifact, useArtifactVersions, useEditArtifact } from '@/lib/hooks'
import { ErrorState } from '@/components/StateViews'

function formatTimestamp(timestamp?: string | number) {
  if (!timestamp) return 'Unknown'
  const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp)
  return date.toLocaleString()
}

function VersionHistorySkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-4 w-32 mb-3" />
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

function ContentSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
      <Separator />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  )
}

export default function ArtifactDetail() {
  const { projectId, artifactType, entityId, version } = useParams()
  const navigate = useNavigate()
  const [showRawJson, setShowRawJson] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [editedJson, setEditedJson] = useState('')
  const [editRationale, setEditRationale] = useState('')

  const versionNum = version ? parseInt(version, 10) : undefined

  // Fetch artifact detail
  const {
    data: artifact,
    isLoading: artifactLoading,
    error: artifactError,
    refetch: refetchArtifact,
  } = useArtifact(projectId, artifactType, entityId, versionNum)

  // Fetch version history
  const {
    data: versions,
    isLoading: versionsLoading,
    error: versionsError,
  } = useArtifactVersions(projectId, artifactType, entityId)

  // Edit artifact mutation
  const editMutation = useEditArtifact()

  const meta = getArtifactMeta(artifactType ?? '')
  const Icon = meta.icon

  // Loading state
  if (artifactLoading || versionsLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header skeleton */}
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-9" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-7 w-64" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Version history sidebar skeleton */}
          <aside className="lg:col-span-1">
            <VersionHistorySkeleton />
          </aside>

          {/* Content skeleton */}
          <main className="lg:col-span-3">
            <Card>
              <CardContent className="p-6">
                <ContentSkeleton />
              </CardContent>
            </Card>
          </main>
        </div>
      </div>
    )
  }

  // Error state
  if (artifactError || versionsError) {
    const error = artifactError || versionsError
    return (
      <div>
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => navigate(`/${projectId}/artifacts`)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to artifacts
          </Button>
        </div>
        <ErrorState
          message={error instanceof Error ? error.message : 'Failed to load artifact'}
          onRetry={refetchArtifact}
        />
      </div>
    )
  }

  // No data
  if (!artifact) {
    return (
      <div>
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => navigate(`/${projectId}/artifacts`)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to artifacts
          </Button>
        </div>
        <ErrorState message="Artifact not found" />
      </div>
    )
  }

  const currentVersion = versions?.find(v => v.version === versionNum)
  const health = currentVersion?.health ?? null

  // Extract a human-friendly display name from the artifact data
  const data = artifact?.payload?.data as Record<string, unknown> | undefined
  const displayName = (
    data?.display_name ??
    data?.name ??
    data?.heading ??
    data?.scene_heading ??
    data?.title
  ) as string | undefined

  function switchVersion(newVersion: number) {
    navigate(`/${projectId}/artifacts/${artifactType}/${entityId}/${newVersion}`)
  }

  function enterEditMode() {
    if (!artifact?.payload?.data) {
      toast.error('No artifact data to edit')
      return
    }
    setEditedJson(JSON.stringify(artifact.payload.data, null, 2))
    setEditRationale('')
    setIsEditMode(true)
  }

  function cancelEdit() {
    setIsEditMode(false)
    setEditedJson('')
    setEditRationale('')
  }

  async function saveEdit() {
    if (!projectId || !artifactType || !entityId) {
      toast.error('Missing required parameters')
      return
    }

    if (!editRationale.trim()) {
      toast.error('Please provide a rationale for this edit')
      return
    }

    let parsedData: Record<string, unknown>
    try {
      parsedData = JSON.parse(editedJson)
    } catch (err) {
      toast.error('Invalid JSON: ' + (err instanceof Error ? err.message : 'Parse error'))
      return
    }

    try {
      const result = await editMutation.mutateAsync({
        projectId,
        artifactType,
        entityId,
        payload: {
          data: parsedData,
          rationale: editRationale,
        },
      })

      toast.success(`Created version ${result.version}`)
      setIsEditMode(false)
      setEditedJson('')
      setEditRationale('')

      // Navigate to the new version
      navigate(`/${projectId}/artifacts/${artifactType}/${entityId}/${result.version}`)
    } catch (err) {
      toast.error('Failed to save edit: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  // Render appropriate viewer based on artifact type
  function renderArtifactContent() {
    if (!artifact?.payload) return null
    const data = artifact.payload.data as Record<string, unknown> | undefined
    if (!data) return null

    // Show raw JSON if toggle is on
    if (showRawJson) {
      return <DefaultViewer data={data} />
    }

    // Route to appropriate viewer
    switch (artifactType) {
      case 'raw_input':
      case 'canonical_script':
        return <ScriptViewer data={data} />

      case 'project_config':
      case 'draft_project_config':
        return <StructuredDataViewer data={data} />

      case 'character_profile':
      case 'character_bible':
        return <ProfileViewer data={data} profileType="character" />

      case 'location_profile':
      case 'location_bible':
        return <ProfileViewer data={data} profileType="location" />

      case 'prop_profile':
      case 'prop_bible':
        return <ProfileViewer data={data} profileType="prop" />

      case 'scene':
        return <SceneViewer data={data} />

      case 'bible_manifest':
        return <BibleViewer data={data} bibleFiles={artifact.bible_files} />

      case 'entity_graph':
        return <EntityGraphViewer data={data} />

      case 'stage_review':
        return <StageReviewViewer data={data} projectId={projectId ?? ''} />

      default:
        return <DefaultViewer data={data} />
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="mb-3">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => navigate(`/${projectId}/artifacts`)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to artifacts
          </Button>
        </div>

        <div className="flex items-start gap-4">
          <div className={cn('rounded-lg bg-card border border-border p-2.5')}>
            <Icon className={cn('h-6 w-6', meta.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold tracking-tight truncate">
                {displayName ?? entityId ?? meta.label}
              </h1>
              <HealthBadge health={health} />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{meta.label}</span>
              {entityId && displayName && (
                <>
                  <span className="text-muted-foreground/50">&middot;</span>
                  <span className="truncate font-mono text-xs">{entityId}</span>
                </>
              )}
              <span className="text-muted-foreground/50">&middot;</span>
              <span className="flex items-center gap-1.5">
                <GitBranch className="h-3.5 w-3.5" />
                v{versionNum}
              </span>
            </div>
          </div>
          {!isEditMode && (
            <Button
              variant="outline"
              size="sm"
              onClick={enterEditMode}
              className="gap-1.5"
            >
              <Edit className="h-3.5 w-3.5" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Version History Sidebar */}
        <aside className="lg:col-span-1 space-y-4">
          <div>
            <h2 className="text-sm font-semibold mb-3 flex items-center gap-1.5">
              <GitBranch className="h-4 w-4" />
              Version History
            </h2>
            {versions && versions.length > 0 ? (
              <div className="space-y-1.5">
                {versions
                  .slice()
                  .sort((a, b) => b.version - a.version)
                  .map(v => (
                    <button
                      key={v.version}
                      aria-label={`Switch to version ${v.version}, health: ${v.health ?? 'unknown'}${v.version === versionNum ? ', currently selected' : ''}`}
                      onClick={() => switchVersion(v.version)}
                      className={cn(
                        'w-full text-left rounded-md border p-2.5 transition-colors',
                        v.version === versionNum
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-accent/50',
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">v{v.version}</span>
                        <HealthBadge health={v.health} />
                      </div>
                      {v.created_at && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {formatTimestamp(v.created_at)}
                        </div>
                      )}
                    </button>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No version history available</p>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main className="lg:col-span-3 space-y-4">
          {/* Metadata Card */}
          <Card>
            <CardHeader className="pb-3">
              <h2 className="text-sm font-semibold">Metadata</h2>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {currentVersion?.producing_module && (
                  <div className="flex items-start gap-2">
                    <Package className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-muted-foreground mb-0.5">Producing Module</p>
                      <p className="font-mono text-xs truncate">{currentVersion.producing_module}</p>
                    </div>
                  </div>
                )}
                {currentVersion?.created_at && (
                  <div className="flex items-start gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-muted-foreground mb-0.5">Created At</p>
                      <p className="text-xs">{formatTimestamp(currentVersion.created_at)}</p>
                    </div>
                  </div>
                )}
              </div>

              {currentVersion?.intent && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Intent</p>
                    <p className="text-xs leading-relaxed">{currentVersion.intent}</p>
                  </div>
                </>
              )}

              <Separator />

              {/* Provenance */}
              <div>
                <p className="text-xs text-muted-foreground mb-2">Provenance</p>
                {(() => {
                  const meta = artifact?.payload?.metadata as Record<string, unknown> | undefined
                  return (
                    <ProvenanceBadge
                      model={
                        (meta?.producing_role as string) ||
                        (meta?.producing_module as string) ||
                        'unknown'
                      }
                      confidence={
                        typeof meta?.confidence === 'number'
                          ? Math.round(meta.confidence * 100)
                          : 0
                      }
                      rationale={
                        (meta?.rationale as string) ||
                        (meta?.intent as string) ||
                        undefined
                      }
                    />
                  )
                })()}
              </div>
            </CardContent>
          </Card>

          {/* Content Card */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <h2 className="text-sm font-semibold">
                {isEditMode ? 'Edit Artifact Data' : 'Content'}
              </h2>
              {!isEditMode && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="gap-1.5"
                >
                  <Code className="h-3.5 w-3.5" />
                  {showRawJson ? 'View Formatted' : 'View Raw JSON'}
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {isEditMode ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Artifact Data (JSON)
                    </label>
                    <Textarea
                      value={editedJson}
                      onChange={(e) => setEditedJson(e.target.value)}
                      className="font-mono text-xs min-h-[400px]"
                      placeholder="Edit the JSON data..."
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Rationale <span className="text-destructive">*</span>
                    </label>
                    <Textarea
                      value={editRationale}
                      onChange={(e) => setEditRationale(e.target.value)}
                      className="text-sm min-h-[80px]"
                      placeholder="Explain why you are making this edit..."
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={saveEdit}
                      disabled={editMutation.isPending}
                      className="gap-1.5"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {editMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={cancelEdit}
                      disabled={editMutation.isPending}
                      className="gap-1.5"
                    >
                      <X className="h-3.5 w-3.5" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                renderArtifactContent()
              )}
            </CardContent>
          </Card>

          {/* Bible Files (if present) */}
          {artifact.bible_files && Object.keys(artifact.bible_files).length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <h2 className="text-sm font-semibold">Bible Files</h2>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(artifact.bible_files).map(([filename, content]) => (
                    <details key={filename} className="group">
                      <summary className="cursor-pointer rounded-md border border-border bg-muted/30 p-2 text-sm font-medium hover:bg-muted/50 transition-colors">
                        <span className="font-mono text-xs">{filename}</span>
                      </summary>
                      <div className="mt-2 rounded-md bg-muted p-3">
                        <pre className="font-mono text-xs text-foreground whitespace-pre-wrap overflow-x-auto">
                          {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                        </pre>
                      </div>
                    </details>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </div>
  )
}
